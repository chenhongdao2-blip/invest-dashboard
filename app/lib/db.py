"""SQLite read helpers for Streamlit pages."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"


@st.cache_data(ttl=600)
def load_domain_cfg(cfg_path: str) -> dict:
    """Load a domain YAML config (e.g. config/domains/{healthcare,ai}.yml).

    cfg_path is a HASHED argument, so each domain gets a DISTINCT cache entry.
    This is load-bearing: Streamlit keys @st.cache_data by
    (func.__module__, func.__qualname__, source_text) ONLY — module globals are
    invisible to the key. Pages are all exec'd under module "__main__", so the
    previous per-page `def load_domain_cfg()` (no args, identical body, differing
    only by a module-global DOMAIN_CFG) collapsed into ONE shared bucket across
    every page. Whichever page loaded first won for the whole TTL, and siblings
    silently got the wrong domain's sectors. Keying on the path fixes it by
    construction; centralizing here removes the duplicated def that bred the bug.
    """
    with open(cfg_path) as f:
        return yaml.safe_load(f)


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
def ticker_to_name(prefer_cn: bool = True) -> dict[str, str]:
    """Resolve display name. M10 audit fix: default to Chinese first (中文卖方 习惯).

    Set prefer_cn=False to fall back to English-first."""
    if prefer_cn:
        col_expr = "COALESCE(name_cn, name_en, ticker)"
    else:
        col_expr = "COALESCE(name_en, name_cn, ticker)"
    df = query(
        f"SELECT ticker, {col_expr} AS display_name "
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

        # Split / bad-tick guard: a single-day DROP beyond this is almost never a
        # real return — it's an un-back-adjusted forward split (yfinance sometimes
        # MISSES the split entirely, e.g. 5801.T / 3110.T 2026-06 ~1:10, so the DB
        # mixes pre- and post-split closes) or a bad tick. Any window spanning such
        # a drop is suppressed (NaN) so the heatmap drops the tile rather than
        # printing a fake -90%. DOWNWARD-only + 0.75 by design: real biotech
        # catalysts pop UP big (e.g. 2565.HK +66% on 2026-05-18, no split — must
        # NOT be suppressed), and genuine one-day crashes rarely exceed -75%
        # (2617.HK -60% real distress stays), while forward-split jumps are -80/-90%.
        SPLIT_GUARD = 0.75

        def ret_back(n: int) -> float:
            if len(ser) <= n:
                return NAN
            seg = ser.iloc[-n - 1:]
            if (seg.pct_change() < -SPLIT_GUARD).any():
                return NAN  # window crosses a split/bad-tick down-discontinuity
            prev = seg.iloc[0]
            if pd.isna(prev) or prev == 0:
                return NAN
            return float((ser.iloc[-1] / prev - 1) * 100)

        # YTD: first close in current year (use each ticker's own anchor)
        year = ser.index.max().year
        this_year = ser[ser.index >= pd.Timestamp(f"{year}-01-01")]
        if (not this_year.empty and this_year.iloc[0] != 0
                and not (this_year.pct_change() < -SPLIT_GUARD).any()):
            ytd = float((ser.iloc[-1] / this_year.iloc[0] - 1) * 100)
        else:
            ytd = NAN

        out[ticker] = {
            "last": last,
            "1d_%": ret_back(1),
            "5d_%": ret_back(5),
            "1m_%": ret_back(21),
            "3m_%": ret_back(63),    # M14 audit: 3-month
            "6m_%": ret_back(126),   # M14 audit: 6-month
            "ytd_%": ytd,
            "60d_%": ret_back(60),
        }

    return pd.DataFrame.from_dict(out, orient="index")


# ---------- multiples ----------
@st.cache_data(ttl=300)
def latest_multiples(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Latest multiples_daily snapshot per ticker. Includes M1 close_usd + M11 mcap_tier."""
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


@st.cache_data(ttl=300)
def rule_of_40_comps(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Rule-of-40 valuation-matrix inputs for a software comp set (Model Drill ③).

    Joins the latest multiples_daily.ev_sales (Y axis) with company_profile's
    revenueGrowth + freeCashflow/totalRevenue (X axis = Rule of 40 = revenue
    growth % + FCF margin %). Everything comes from the daily snapshot, so the
    matrix tracks the current market — re-run jobs/fetch_eod to refresh. Rows
    missing any input (or with non-positive revenue) are dropped. Returns a frame
    indexed by ticker with name_cn / name_en / ev_sales / rev_growth / fcf_margin /
    rule40 (the last three already in PERCENT points)."""
    if not tickers:
        return pd.DataFrame()
    ph = ",".join("?" * len(tickers))
    df = query(
        f"""
        SELECT u.ticker,
               MIN(u.name_cn) AS name_cn, MIN(u.name_en) AS name_en,
               m.ev_sales, p.revenueGrowth, p.totalRevenue, p.freeCashflow
        FROM universe_member u
        INNER JOIN (
          SELECT ticker, MAX(date) AS d FROM multiples_daily
          WHERE ticker IN ({ph}) GROUP BY ticker
        ) lm ON lm.ticker = u.ticker
        INNER JOIN multiples_daily m ON m.ticker = u.ticker AND m.date = lm.d
        LEFT JOIN company_profile p ON p.ticker = u.ticker
        WHERE u.ticker IN ({ph})
        GROUP BY u.ticker, m.ev_sales, p.revenueGrowth, p.totalRevenue, p.freeCashflow
        """,
        tuple(tickers) + tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df = df.dropna(subset=["ev_sales", "revenueGrowth", "totalRevenue", "freeCashflow"])
    df = df[df["totalRevenue"] > 0]
    if df.empty:
        return df
    df["rev_growth"] = df["revenueGrowth"] * 100.0
    df["fcf_margin"] = df["freeCashflow"] / df["totalRevenue"] * 100.0
    df["rule40"] = df["rev_growth"] + df["fcf_margin"]
    return df.set_index("ticker")[["name_cn", "name_en", "ev_sales",
                                   "rev_growth", "fcf_margin", "rule40"]]


@st.cache_data(ttl=300)
def adv_20d(ticker: str) -> float | None:
    """20-trading-day average daily turnover (close × volume) in the stock's LOCAL
    currency — a liquidity gauge (small-cap HK/A names can be hard to build/exit).
    Returns None when no volume is on file. Reads the committed snapshots.db only
    (works offline; no live call)."""
    df = query(
        "SELECT close, volume FROM prices_daily WHERE ticker = ? "
        "ORDER BY date DESC LIMIT 20",
        (ticker,),
    )
    if df.empty or df["volume"].isna().all():
        return None
    turn = (df["close"] * df["volume"]).dropna()
    return float(turn.mean()) if not turn.empty else None


@st.cache_data(ttl=300)
def get_close_series_usd(tickers: tuple[str, ...]) -> pd.DataFrame:
    """M1 audit fix: USD-converted close series (so cross-region returns are comparable).

    Falls back to local close × FX if close_usd is null (legacy rows pre-M1 fix).
    """
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"SELECT ticker, date, COALESCE(close_usd, close) AS close_usd "
        f"FROM prices_daily WHERE ticker IN ({placeholders}) ORDER BY date",
        tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="ticker", values="close_usd").sort_index()


# ---------- top movers ----------
@st.cache_data(ttl=300)
def top_movers(n: int = 10, domain: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Top n gainers and losers by 1-day return across universe tickers, optionally
    scoped to a single `domain` (e.g. 'healthcare' / 'ai') so each home-page benchmark
    category can show its OWN movers (HC movers under HC, AI movers under AI)."""
    if domain:
        tickers = tuple(
            query("SELECT DISTINCT ticker FROM universe_member WHERE domain = ?",
                  (domain,))["ticker"].tolist()
        )
    else:
        tickers = tuple(all_tickers())
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()
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
