"""SQLite read helpers for Streamlit pages."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"


def connect() -> sqlite3.Connection:
    """Read-only connection."""
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def query(sql: str, params: tuple | list | dict | None = None) -> pd.DataFrame:
    conn = connect()
    try:
        return pd.read_sql_query(sql, conn, params=params or ())
    finally:
        conn.close()


# ---------- metadata ----------
@st.cache_data(ttl=300)
def latest_snapshot_date() -> str | None:
    df = query("SELECT MAX(date) AS d FROM multiples_daily")
    return df["d"].iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def last_fetch_utc() -> str | None:
    df = query("SELECT value FROM meta WHERE key = 'last_fetch_utc'")
    return df["value"].iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def universe_summary() -> pd.DataFrame:
    return query(
        "SELECT domain, sector, COUNT(*) AS n FROM universe_member "
        "WHERE sector != '_coverage' GROUP BY domain, sector ORDER BY domain, sector"
    )


# ---------- universe ----------
@st.cache_data(ttl=300)
def all_tickers() -> list[str]:
    return query("SELECT DISTINCT ticker FROM universe_member")["ticker"].tolist()


@st.cache_data(ttl=300)
def sector_tickers(domain: str, sector: str) -> pd.DataFrame:
    return query(
        "SELECT ticker, name_cn, name_en, region "
        "FROM universe_member WHERE domain = ? AND sector = ? "
        "ORDER BY ticker",
        (domain, sector),
    )


@st.cache_data(ttl=300)
def ticker_to_name() -> dict[str, str]:
    """Use English name if available, else Chinese, else ticker."""
    df = query(
        "SELECT ticker, "
        "  COALESCE(name_en, name_cn, ticker) AS display_name "
        "FROM universe_member GROUP BY ticker"
    )
    return dict(zip(df["ticker"], df["display_name"]))


# ---------- prices & returns ----------
@st.cache_data(ttl=300)
def get_close_series(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Wide-format close prices: index=date, columns=ticker. Tuple for cache."""
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"SELECT ticker, date, close FROM prices_daily "
        f"WHERE ticker IN ({placeholders}) ORDER BY date",
        tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="ticker", values="close").sort_index()


def compute_returns(closes: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker return windows. Each ticker uses its OWN last valid close —
    avoids ragged-tail bug across markets (JP closes earlier than US).
    Output index=ticker, columns=[last, 1d_%, 5d_%, 1m_%, ytd_%, 60d_%]."""
    if closes.empty:
        return pd.DataFrame()

    closes = closes.sort_index()
    out: dict[str, dict[str, float | None]] = {}

    NAN = float("nan")
    for ticker in closes.columns:
        ser = closes[ticker].dropna()
        if ser.empty:
            out[ticker] = {k: NAN for k in ("last", "1d_%", "5d_%", "1m_%", "ytd_%", "60d_%")}
            continue

        last = float(ser.iloc[-1])

        def ret_back(n: int) -> float:
            if len(ser) <= n:
                return NAN
            prev = ser.iloc[-n - 1]
            if pd.isna(prev) or prev == 0:
                return NAN
            return float((ser.iloc[-1] / prev - 1) * 100)

        # YTD: first close in current year (use each ticker's own anchor)
        year = ser.index.max().year
        this_year = ser[ser.index >= pd.Timestamp(f"{year}-01-01")]
        if not this_year.empty and this_year.iloc[0] != 0:
            ytd = float((ser.iloc[-1] / this_year.iloc[0] - 1) * 100)
        else:
            ytd = NAN

        out[ticker] = {
            "last": last,
            "1d_%": ret_back(1),
            "5d_%": ret_back(5),
            "1m_%": ret_back(21),
            "ytd_%": ytd,
            "60d_%": ret_back(60),
        }

    return pd.DataFrame.from_dict(out, orient="index")


# ---------- multiples ----------
@st.cache_data(ttl=300)
def latest_multiples(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Latest multiples_daily snapshot per ticker."""
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"""
        SELECT m.* FROM multiples_daily m
        INNER JOIN (
          SELECT ticker, MAX(date) AS max_date
          FROM multiples_daily
          WHERE ticker IN ({placeholders})
          GROUP BY ticker
        ) latest
        ON m.ticker = latest.ticker AND m.date = latest.max_date
        """,
        tuple(tickers),
    )
    if df.empty:
        return df
    return df.set_index("ticker")


# ---------- top movers ----------
@st.cache_data(ttl=300)
def top_movers(n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Top n gainers and losers by 1-day return across all universe tickers."""
    tickers = tuple(all_tickers())
    closes = get_close_series(tickers)
    rets = compute_returns(closes)
    if rets.empty:
        return pd.DataFrame(), pd.DataFrame()
    name_map = ticker_to_name()
    rets["name"] = rets.index.map(name_map)
    rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
    gainers = rets.sort_values("1d_%", ascending=False).head(n)
    losers = rets.sort_values("1d_%", ascending=True).head(n)
    return gainers, losers
