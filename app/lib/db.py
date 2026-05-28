"""SQLite read helpers for Streamlit pages."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"


def connect() -> sqlite3.Connection:
    """Read-only connection (uri mode)."""
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def query(sql: str, params: tuple | dict | None = None) -> pd.DataFrame:
    """Run a SQL query and return a DataFrame."""
    conn = connect()
    try:
        return pd.read_sql_query(sql, conn, params=params or ())
    finally:
        conn.close()


def universe_summary() -> pd.DataFrame:
    return query(
        "SELECT domain, sector, COUNT(*) AS n FROM universe_member "
        "GROUP BY domain, sector ORDER BY domain, sector"
    )


def latest_snapshot_date() -> str | None:
    df = query("SELECT MAX(date) AS d FROM multiples_daily")
    return df["d"].iloc[0] if not df.empty else None


def sector_tickers(domain: str, sector: str) -> pd.DataFrame:
    return query(
        "SELECT ticker, name_cn, name_en, region FROM universe_member "
        "WHERE domain = ? AND sector = ? ORDER BY ticker",
        (domain, sector),
    )
