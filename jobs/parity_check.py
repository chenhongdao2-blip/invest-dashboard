"""SQLite vs Parquet parity gate for the dual-write week.

Runs in the three data workflows AFTER the fetch and BEFORE the commit, so a
divergence fails the run loudly instead of being committed and discovered later
(audit §8.1 — the whole class of "green manifest over dead data" bugs).

Three checks per table, in the order a divergence is cheapest to read:

1. **row counts** — the coarse signal; says "something is wrong" in one number.
2. **anti-join on the primary key, both directions** — says WHICH rows. A row in
   SQLite but not Parquet means a dual-write did not fire; the reverse means the
   Parquet store kept something SQLite dropped.
3. **value equality, column by column** — says which FIELD drifted for rows that
   exist on both sides. Exact equality, not a tolerance: these are copies of the
   same numbers, so any drift at all is a finding.

Plus a duplicate-PK scan on the Parquet side, which is the failure mode a broken
merge in `upsert_rows` would produce and which the anti-joins alone would miss.

On the comparison itself: the Parquet side is read through the same schema
coercion the writer applies, the SQLite side is read raw. So a coercion that LOST
information on write (a float truncated into an Int64 column, say) still surfaces
here as a value mismatch against the raw SQLite value. What this cannot see is a
coercion that is symmetric and lossless in both directions — which is the
definition of one that does not matter.

Exit code 0 = every table matches. Non-zero = at least one did not, with a summary.

`PARQUET_DUAL_WRITE=0` short-circuits the whole check to a SKIP and exit 0: that flag
is the rollback lever, and with the shadow write off the two stores are SUPPOSED to
drift apart. See `main()`.

Usage:
    python jobs/parity_check.py                      # all four tables
    python jobs/parity_check.py --table prices_daily
    python jobs/parity_check.py --max-samples 20
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import parquet_store as ps  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"
TABLES = ["prices_daily", "multiples_daily", "benchmarks_daily", "sw_industry_daily"]

_NUMERIC = {"float64", "Int64"}
_SEP = "\x1f"          # PK joiner: a byte that cannot occur in a ticker or a date


def _show(key: str) -> str:
    return key.replace(_SEP, " | ")


def _val(v) -> str:
    """Readable scalar for a diff line (bare numbers, not numpy reprs)."""
    if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
        return "NULL"
    return f"{float(v):.10g}" if isinstance(v, (int, float, np.number)) else repr(v)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--table", action="append", default=None,
                   help="Check only this table (repeatable). Default: all four.")
    p.add_argument("--db", type=Path, default=DB_PATH)
    p.add_argument("--max-samples", type=int, default=5,
                   help="Sample keys / values printed per failing check.")
    return p.parse_args()


def _num(s: pd.Series) -> np.ndarray:
    return pd.to_numeric(s, errors="coerce").astype("Float64").to_numpy(
        dtype="float64", na_value=np.nan)


def _txt(s: pd.Series) -> np.ndarray:
    """Object array with a single sentinel for every flavour of null."""
    out = s.astype(object).to_numpy(copy=True)
    for i, v in enumerate(out):
        if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
            out[i] = None
    return out


def _mismatches(a: pd.Series, b: pd.Series, numeric: bool) -> np.ndarray:
    """Boolean mask of positions where `a` and `b` disagree. NULL == NULL."""
    if numeric:
        av, bv = _num(a), _num(b)
        both_nan = np.isnan(av) & np.isnan(bv)
        return ~(both_nan | (av == bv))
    av, bv = _txt(a), _txt(b)
    return np.array([x != y for x, y in zip(av, bv)], dtype=bool)


def check_table(conn: sqlite3.Connection, table: str, max_samples: int) -> list[str]:
    """Compare one table. Returns a list of problem lines (empty = parity)."""
    spec = ps.TABLES[table]
    pk = list(spec.pk or [])
    problems: list[str] = []

    sq = pd.read_sql_query(f"SELECT * FROM {table}", conn)  # noqa: S608 — fixed list
    pqd = ps.read_table(table)

    # ── 1. row counts ────────────────────────────────────────────────────
    if len(sq) != len(pqd):
        problems.append(f"row count: sqlite={len(sq):,} parquet={len(pqd):,} "
                        f"(delta {len(pqd) - len(sq):+,})")

    # ── duplicate PK on the parquet side (a broken merge in upsert_rows) ─
    dup = pqd.duplicated(subset=pk, keep=False)
    if dup.any():
        sample = pqd.loc[dup, pk].head(max_samples).to_dict("records")
        problems.append(f"parquet has {int(dup.sum()):,} rows on duplicated PKs, e.g. {sample}")

    # ── 2. anti-join on the PK, both directions ──────────────────────────
    sq_keys = sq[pk].astype(str).agg(_SEP.join, axis=1) if len(sq) else pd.Series(dtype=str)
    pq_keys = pqd[pk].astype(str).agg(_SEP.join, axis=1) if len(pqd) else pd.Series(dtype=str)
    only_sq = set(sq_keys) - set(pq_keys)
    only_pq = set(pq_keys) - set(sq_keys)
    if only_sq:
        problems.append(f"{len(only_sq):,} PK(s) in SQLite but NOT in Parquet "
                        f"(a dual-write did not fire), e.g. "
                        f"{[_show(k) for k in sorted(only_sq)[:max_samples]]}")
    if only_pq:
        problems.append(f"{len(only_pq):,} PK(s) in Parquet but NOT in SQLite "
                        f"(Parquet kept a row SQLite dropped), e.g. "
                        f"{[_show(k) for k in sorted(only_pq)[:max_samples]]}")

    # ── 3. value equality on the intersection ────────────────────────────
    common = sorted(set(sq_keys) & set(pq_keys))
    if common:
        a = sq.assign(_k=sq_keys).set_index("_k").loc[common]
        b = pqd.assign(_k=pq_keys).set_index("_k").loc[common]
        for col, dt in spec.dtypes.items():
            if col not in sq.columns:
                problems.append(f"column {col!r} declared in the parquet schema but "
                                f"absent from the SQLite table")
                continue
            bad = _mismatches(a[col], b[col], numeric=dt in _NUMERIC)
            if bad.any():
                idx = np.flatnonzero(bad)[:max_samples]
                sample = [f"{_show(common[i])}: sqlite={_val(a[col].iloc[i])} "
                          f"parquet={_val(b[col].iloc[i])}" for i in idx]
                problems.append(f"column {col!r}: {int(bad.sum()):,}/{len(common):,} "
                                f"values differ, e.g. {sample}")
    return problems


def main() -> None:
    args = parse_args()

    # The rollback lever must not break the thing it exists to rescue. This gate runs
    # BEFORE "Commit data" in all three workflows, so with `PARQUET_DUAL_WRITE=0` — the
    # documented rollback (docs/storage-migration.md § Rollback) — the Parquet store
    # freezes while SQLite keeps moving, and every table diverges by design within a
    # day. Failing on that would stop the whole data pipeline on the exact path taken
    # to get OUT of trouble. Nothing reads Parquet yet, so there is nothing to protect
    # here once the shadow write is off.
    if not ps.dual_write_enabled():
        print("[parity] SKIP — dual write disabled (PARQUET_DUAL_WRITE=0)")
        return

    if not args.db.exists():
        raise SystemExit(f"DB not found at {args.db}")
    tables = args.table or TABLES
    for t in tables:
        if t not in ps.TABLES:
            raise SystemExit(f"unknown table {t!r}; known: {TABLES}")

    print(f"[parity] sqlite={args.db}")
    print(f"[parity] parquet={ps.root()}")
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    failed: dict[str, list[str]] = {}
    try:
        for t in tables:
            problems = check_table(conn, t, args.max_samples)
            n_sq = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # noqa: S608
            n_pq = len(ps.read_table(t))
            if problems:
                failed[t] = problems
                print(f"[parity] {t:<18} MISMATCH  sqlite={n_sq:,} parquet={n_pq:,}")
                for p in problems:
                    print(f"[parity]   • {p}")
            else:
                print(f"[parity] {t:<18} OK        {n_sq:,} rows match on "
                      f"{len(ps.TABLES[t].dtypes)} columns")
    finally:
        conn.close()

    if failed:
        print(f"[parity] FAIL — {len(failed)}/{len(tables)} table(s) diverged: "
              f"{', '.join(sorted(failed))}")
        raise SystemExit(1)
    print(f"[parity] PASS — {len(tables)} table(s) identical across both stores")


if __name__ == "__main__":
    main()
