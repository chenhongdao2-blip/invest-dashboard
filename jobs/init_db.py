"""Initialize SQLite schema for invest-dashboard.

Idempotent — safe to run multiple times.

Usage:
    python jobs/init_db.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

SCHEMA = """
-- Daily prices (auto-grown by fetch_eod.py)
-- Local-currency close + USD-converted close (M1 audit fix)
CREATE TABLE IF NOT EXISTS prices_daily (
    ticker        TEXT NOT NULL,
    date          TEXT NOT NULL,        -- YYYY-MM-DD
    open          REAL,
    high          REAL,
    low           REAL,
    close         REAL,                  -- local ccy
    adj_close     REAL,                  -- local ccy
    volume        INTEGER,
    currency      TEXT,                  -- USD / HKD / JPY / KRW / EUR / CNY / GBP / CHF
    close_usd     REAL,                  -- M1: USD-converted close
    adj_close_usd REAL,                  -- M1: USD-converted adj_close
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices_daily(date);

-- Multiple snapshot 时序 (core value: 自累积 → 90d 后可做 Z-score)
CREATE TABLE IF NOT EXISTS multiples_daily (
    ticker            TEXT NOT NULL,
    date              TEXT NOT NULL,
    market_cap_usd    REAL,
    mcap_tier         TEXT,                -- M11: mega/large/mid/small/micro
    trailing_pe       REAL,
    forward_pe        REAL,
    trailing_eps      REAL,
    forward_eps       REAL,
    ev_ebitda         REAL,
    ev_sales          REAL,
    fcf_yield         REAL,
    peg               REAL,
    pb                REAL,
    ytd_return        REAL,
    last_price        REAL,                -- local ccy
    last_price_usd    REAL,                -- M1: USD-converted last price
    currency          TEXT,                -- 来自 yfinance.info
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_mult_date ON multiples_daily(date);

-- Universe membership (many-to-many for cross-sector tickers like ISRG / HCA)
CREATE TABLE IF NOT EXISTS universe_member (
    domain    TEXT NOT NULL,
    sector    TEXT NOT NULL,
    ticker    TEXT NOT NULL,
    name_cn   TEXT,
    name_en   TEXT,
    region    TEXT,
    note      TEXT,
    PRIMARY KEY (domain, sector, ticker)
);
CREATE INDEX IF NOT EXISTS idx_um_ticker ON universe_member(ticker);
CREATE INDEX IF NOT EXISTS idx_um_domain_sector ON universe_member(domain, sector);

-- Meta key/value
CREATE TABLE IF NOT EXISTS meta (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT
);
"""


def _safe_alter(conn: sqlite3.Connection, sql: str) -> None:
    """ALTER TABLE ADD COLUMN — ignore 'duplicate column name' errors."""
    try:
        conn.execute(sql)
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        # m8 audit: idempotent column adds for existing DBs (no destructive migration)
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN target_price_mean REAL")
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN recommendation_mean REAL")
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN n_analysts INTEGER")
        conn.commit()
        # Sanity log
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall()]
        print(f"[init_db] DB at: {DB_PATH}")
        print(f"[init_db] Tables: {tables}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
