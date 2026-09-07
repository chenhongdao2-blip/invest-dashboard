"""companyfacts gzip blob → per-ticker Parquet, projected to the concepts the app uses.

`sec_company.payload_gzip` is 40.25 MB over 311 rows and git rewrites all of it
whenever any one company files (audit §6). The app reads only 90 of the ~784
concepts a payload carries (jobs/sec_concepts.py), so the projection is ~12× smaller
AND per-ticker — the weekly SEC job then rewrites the handful of companies that
actually filed, not the whole blob.

Audit §8.2 called for a `sec_fact` SQLite table of "a few hundred KB". Both halves
of that need correcting, and design B.2 measures why: the projected facts are
millions of rows, and as a SQLite table they occupy **58 MB — worse than today's
40 MB blob**. Parquet, per ticker, is the representation that pays.

**The row construction below is a verbatim copy of `_load_facts` in
app/lib/sec_facts.py, with one added `if concept not in KEEP: continue`.** That is
deliberate, and the duplication is the point: the output must be substitutable for
what `_load_facts` returns today so the read shim in a later PR is a drop-in.
tests/test_sec_fact_normalize.py pins the equivalence against the real function for
three tickers, so the copy cannot drift unnoticed.

What this does NOT do, deliberately:
  • It does not dedupe. Design B.2 measured a 2.0× collapse on
    (taxonomy, concept, unit, start_date, end_date) keeping MAX(filed), which would
    halve the store. But `_dedupe_by_end_date` and `_rank` in app/lib/sec_facts.py
    are STABLE sorts, so rows tying on all their keys resolve by input order —
    deduping here would change which fact the app displays, in exactly the cases
    audit C2 shows are already subtle (the FY row and the 91-day Q4 row share an
    end_date). Correctness first; the store is ~12 MB either way and the concept
    projection already bought the 12×.
  • It does not touch `payload_gzip`. The read side still parses it; dropping the
    blob is the last step of the cutover, not this one.

Usage:
    python jobs/normalize_sec_facts.py               # every sec_status='ok' ticker
    python jobs/normalize_sec_facts.py --ticker LLY
    python jobs/normalize_sec_facts.py --limit 5
"""

from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import parquet_store as ps, sec_concepts  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"

# app/lib/sec_facts.py `_FACT_COLS`, verbatim — name AND order.
FACT_COLS = list(ps.TABLES["sec_fact"].dtypes)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", type=str, default="", help="Normalize a single ticker.")
    p.add_argument("--limit", type=int, default=0, help="Process only first N tickers.")
    p.add_argument("--db", type=Path, default=DB_PATH)
    return p.parse_args()


def facts_frame(payload: bytes, keep: frozenset[str]) -> pd.DataFrame:
    """gzip'd companyfacts JSON → the `_FACT_COLS` frame, projected to `keep`."""
    try:
        cf = json.loads(gzip.decompress(payload))
    except (OSError, ValueError, TypeError):
        return pd.DataFrame(columns=FACT_COLS)
    return frame_from_companyfacts(cf, keep)


def frame_from_companyfacts(cf: dict, keep: frozenset[str]) -> pd.DataFrame:
    """Parsed companyfacts dict → the `_FACT_COLS` frame, projected to `keep`.

    Mirrors app/lib/sec_facts.py `_load_facts` exactly apart from the projection.
    Takes the parsed object so jobs/fetch_sec_facts.py can reuse the payload it
    just downloaded instead of re-compressing and re-parsing it.
    """
    rows: list[tuple] = []
    for taxonomy, concepts in (cf.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            if concept not in keep:          # ← the only departure from _load_facts
                continue
            label = cdata.get("label")
            for unit, items in (cdata.get("units") or {}).items():
                for it in items:
                    end = it.get("end")
                    if not end:
                        continue
                    start = it.get("start") or ""
                    val = it.get("val")
                    is_num = isinstance(val, (int, float))
                    rows.append((
                        taxonomy, concept, label, unit,
                        float(val) if is_num else None,
                        None if is_num else (None if val is None else str(val)),
                        start, end, 0 if start else 1,
                        it.get("fy"), it.get("fp"), it.get("form"),
                        it.get("filed"), it.get("accn", ""), it.get("frame", "") or "",
                    ))
    if not rows:
        return pd.DataFrame(columns=FACT_COLS)
    return pd.DataFrame(rows, columns=FACT_COLS)


def normalize_ticker(conn: sqlite3.Connection, ticker: str,
                     keep: frozenset[str]) -> tuple[int, int]:
    """Write one ticker's projected facts. → (rows, bytes); (0, 0) if nothing usable."""
    row = conn.execute(
        "SELECT payload_gzip FROM sec_company WHERE ticker = ? AND sec_status = 'ok'",
        (ticker,),
    ).fetchone()
    if not row or row[0] is None:
        return 0, 0
    df = facts_frame(row[0], keep)
    if df.empty:
        return 0, 0
    return len(df), write_ticker(ticker, df)


def write_ticker(ticker: str, df: pd.DataFrame) -> int:
    """Write one ticker's file. → bytes on disk."""
    return ps.write_partition("sec_fact", ticker, df).stat().st_size


def main() -> None:
    args = parse_args()
    if not args.db.exists():
        raise SystemExit(f"DB not found at {args.db}")

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    try:
        keep = sec_concepts.used_concepts(args.db)
        print(f"[sec-norm] keeping {len(keep)} concepts "
              f"(sec_kpi_map ∪ sec_statements row tags)")

        if args.ticker:
            tickers = [args.ticker.upper()]
        else:
            tickers = [r[0] for r in conn.execute(
                "SELECT ticker FROM sec_company WHERE sec_status = 'ok' "
                "AND payload_gzip IS NOT NULL ORDER BY ticker")]
            if args.limit > 0:
                tickers = tickers[:args.limit]
        print(f"[sec-norm] tickers with a payload: {len(tickers)}")

        n_files = tot_rows = tot_bytes = 0
        empty: list[str] = []
        for i, t in enumerate(tickers, 1):
            rows, nbytes = normalize_ticker(conn, t, keep)
            if rows == 0:
                empty.append(t)
                continue
            n_files += 1
            tot_rows += rows
            tot_bytes += nbytes
            if i % 50 == 0 or i == len(tickers):
                print(f"[sec-norm] {i}/{len(tickers)} … {n_files} files, "
                      f"{tot_rows:,} rows, {tot_bytes / 1024 / 1024:.2f} MB")
    finally:
        conn.close()

    if empty:
        print(f"[sec-norm] {len(empty)} ticker(s) produced no rows for the kept "
              f"concepts: {empty[:20]}")
    if n_files:
        sizes = sorted(p.stat().st_size for p in ps.partitions("sec_fact"))
        med = sizes[len(sizes) // 2] / 1024
        print(f"[sec-norm] done. {n_files} files, {tot_rows:,} rows, "
              f"{tot_bytes / 1024 / 1024:.2f} MB "
              f"(median {med:.1f} KB, max {sizes[-1] / 1024:.1f} KB per file) "
              f"at {ps.root() / 'sec_fact'}")


if __name__ == "__main__":
    main()
