"""One-off exporter: SQLite time-series tables → the partitioned Parquet store.

Reads `data/snapshots.db` and writes `data/parquet/<table>/<partition>.parquet` for
prices_daily, multiples_daily, benchmarks_daily and sw_industry_daily. SQLite is
untouched — this is a copy, and during the dual-write week SQLite remains the
source of truth (see docs/storage-migration.md).

Idempotent in the strong sense: re-running writes byte-identical files, because
each partition is rendered whole from the SQLite rows and the writer is
deterministic. `git status` after a second run is clean. Verify with --verify.

Usage:
    python jobs/migrate_sqlite_to_parquet.py                # export everything
    python jobs/migrate_sqlite_to_parquet.py --table prices_daily
    python jobs/migrate_sqlite_to_parquet.py --verify       # re-export, assert bytes unchanged
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import parquet_store as ps  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"

TABLES = ["prices_daily", "multiples_daily", "benchmarks_daily", "sw_industry_daily"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--table", action="append", default=None,
                   help="Export only this table (repeatable). Default: all four.")
    p.add_argument("--verify", action="store_true",
                   help="Hash every partition before and after re-export; "
                        "exit non-zero if any byte changed.")
    p.add_argument("--db", type=Path, default=DB_PATH)
    return p.parse_args()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(tables: list[str]) -> dict[str, str]:
    return {str(p): _sha(p) for t in tables for p in ps.partitions(t)}


def export_table(conn: sqlite3.Connection, table: str) -> tuple[int, int, int]:
    """Render every partition of `table` from SQLite. → (rows, files, bytes)."""
    spec = ps.TABLES[table]
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)  # noqa: S608 — fixed table list
    if df.empty:
        print(f"[migrate] {table}: 0 rows in SQLite — nothing to export")
        return 0, 0, 0

    keys = df[spec.part_column].map(lambda v: ps.partition_key(table, v))
    rows = files = nbytes = 0
    for key, chunk in df.groupby(keys, sort=True):
        path = ps.write_partition(table, key, chunk)
        rows += len(chunk)
        files += 1
        nbytes += path.stat().st_size
    print(f"[migrate] {table}: {rows:>7,} rows → {files:>3} files, "
          f"{nbytes / 1024 / 1024:6.2f} MB")

    # A partition that exists on disk but no longer in SQLite is not deleted — say so
    # rather than silently leaving a stale file that read_table would still pick up.
    live = {ps.partition_path(table, k).name for k in keys.unique()}
    stale = [p.name for p in ps.partitions(table) if p.name not in live]
    if stale:
        print(f"[migrate] {table}: WARNING {len(stale)} partition(s) on disk with no "
              f"SQLite rows: {stale} — delete by hand if the rows really are gone")
    return rows, files, nbytes


def main() -> None:
    args = parse_args()
    if not args.db.exists():
        raise SystemExit(f"DB not found at {args.db}")
    tables = args.table or TABLES
    for t in tables:
        if t not in ps.TABLES:
            raise SystemExit(f"unknown table {t!r}; known: {TABLES}")

    before = _hashes(tables) if args.verify else {}

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    try:
        tot_rows = tot_files = tot_bytes = 0
        for t in tables:
            r, f, b = export_table(conn, t)
            tot_rows += r
            tot_files += f
            tot_bytes += b
    finally:
        conn.close()

    print(f"[migrate] TOTAL: {tot_rows:,} rows, {tot_files} files, "
          f"{tot_bytes / 1024 / 1024:.2f} MB at {ps.root()}")

    if args.verify:
        after = _hashes(tables)
        changed = sorted(
            k for k in set(before) | set(after) if before.get(k) != after.get(k)
        )
        if changed:
            print(f"[migrate] VERIFY FAILED — {len(changed)} partition(s) changed bytes:")
            for k in changed[:20]:
                print(f"          {k}")
            raise SystemExit(1)
        print(f"[migrate] VERIFY OK — {len(after)} partitions byte-identical on re-export")


if __name__ == "__main__":
    main()
