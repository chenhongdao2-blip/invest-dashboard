"""Fetch EOD price + multiple snapshot for all tickers in universe_member.

This is a D1 SKELETON — full pattern (crib from strategy-weekly/weekly_perf.py:74-102)
will be implemented D2.

Usage:
    python jobs/fetch_eod.py                       # today's EOD
    python jobs/fetch_eod.py --backfill-days 30    # 30-day historical backfill
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--backfill-days", type=int, default=0,
                   help="Days of historical price to backfill (0 = today only).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print actions, don't write to DB.")
    return p.parse_args()


def get_tickers(conn: sqlite3.Connection) -> list[str]:
    """All unique tickers across universe_member."""
    cur = conn.execute("SELECT DISTINCT ticker FROM universe_member")
    return [row[0] for row in cur.fetchall()]


def main() -> None:
    args = parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Run init_db.py first.")

    conn = sqlite3.connect(DB_PATH)
    tickers = get_tickers(conn)
    print(f"[fetch_eod] {len(tickers)} unique tickers in universe")
    print(f"[fetch_eod] backfill_days={args.backfill_days}, dry_run={args.dry_run}")

    if not tickers:
        print("[fetch_eod] No tickers — load_universe.py first.")
        return

    # TODO D2: implement yfinance batch download.
    # Pattern reference: /Users/gcc/strategy-weekly/weekly_perf.py lines 74-102
    #   - yf.download(tickers, period=..., group_by='ticker')
    #   - yf.Ticker(t).info for multiples (trailing_pe, forward_pe, etc.)
    # Handle:
    #   - HK / JP / KR ticker formatting (already in YAML as 0123.HK / 4587.T / 207940.KS)
    #   - Currency normalize to USD for market_cap
    #   - Retry / backoff on rate limit
    #   - Batch in groups of 50

    print("[fetch_eod] SKELETON — implementation pending D2")
    conn.close()


if __name__ == "__main__":
    main()
