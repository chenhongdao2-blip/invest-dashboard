"""Strategy picks data layer — reads from data/external/.

Strategies tracked:
- v4 biotech (2026-04-22, 27 picks, XBI benchmark) — CSV
- v5 biotech (2026-05-15, 40 picks, XBI benchmark)   — picks.db (catalyst-monitor)
- HK 高股息 (2026-03-20, 34 picks, 3110.HK benchmark) — CSV

Prices fetched live via yfinance, cached 1 hour.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_EXT = REPO_ROOT / "data" / "external"

PICKS_DB = DATA_EXT / "picks.db"
V4_CSV = DATA_EXT / "v4_picks.csv"
HD_CSV = DATA_EXT / "hd_picks.csv"


@st.cache_data(ttl=900)
def load_v4() -> pd.DataFrame:
    if not V4_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V4_CSV)


@st.cache_data(ttl=900)
def load_v5() -> pd.DataFrame:
    """v5 biotech: from picks.db, source_skill='catalyst-monitor'."""
    if not PICKS_DB.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(f"file:{PICKS_DB}?mode=ro", uri=True)
    try:
        df = pd.read_sql(
            "SELECT ticker, MAX(price_at_decision) AS price_at_decision, "
            "MIN(date_added) AS pick_date "
            "FROM picks_v2 WHERE source_skill='catalyst-monitor' GROUP BY ticker",
            conn,
        )
    finally:
        conn.close()
    df["name"] = df["ticker"]
    df["score"] = None
    df["benchmark"] = "XBI"
    df["yf_sym"] = df["ticker"]
    df["pick_date"] = "2026-05-15"
    return df[["ticker", "name", "score", "pick_date", "benchmark", "yf_sym", "price_at_decision"]]


@st.cache_data(ttl=900)
def load_hd() -> pd.DataFrame:
    if not HD_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_CSV)


STRATEGIES = {
    "v4_biotech": {
        "name": "🧬 v4 biotech",
        "emoji": "🧬",
        "loader": load_v4,
        "pick_date": "2026-04-22",
        "benchmark": "XBI",
        "benchmark_name": "SPDR S&P Biotech",
    },
    "v5_biotech": {
        "name": "🧬 v5 biotech",
        "emoji": "🧬",
        "loader": load_v5,
        "pick_date": "2026-05-15",
        "benchmark": "XBI",
        "benchmark_name": "SPDR S&P Biotech",
    },
    "hk_hd": {
        "name": "💰 HK 高股息",
        "emoji": "💰",
        "loader": load_hd,
        "pick_date": "2026-03-20",
        "benchmark": "3110.HK",
        "benchmark_name": "Premia 沪深港高股息低波动",
    },
}


@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
    """Wide-format close DataFrame for picks. Live yfinance, cached 1h."""
    if not yf_syms:
        return pd.DataFrame()
    end = (date.today() + timedelta(days=1)).isoformat()
    try:
        d = yf.download(
            list(yf_syms), start=start, end=end,
            auto_adjust=True, progress=False, threads=True, group_by="ticker",
        )
    except Exception as e:
        st.warning(f"Live fetch failed: {e}")
        return pd.DataFrame()
    if d.empty:
        return pd.DataFrame()

    if len(yf_syms) == 1:
        sym = yf_syms[0]
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.droplevel(1)
        if "Close" in d.columns:
            return pd.DataFrame({sym: d["Close"]}).dropna(how="all")
        return pd.DataFrame()

    out = {}
    for sym in yf_syms:
        try:
            if sym in d.columns.get_level_values(0):
                out[sym] = d[sym]["Close"].dropna()
        except Exception:
            pass
    return pd.DataFrame(out).sort_index()


def compute_strategy_returns(
    closes: pd.DataFrame, pick_date: str
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Compute since-inception cumulative return (indexed=100) for each ticker
    + equal-weight portfolio + per-window returns table.

    Returns:
      - normed: wide DataFrame indexed=100 from pick_date
      - portfolio: equal-weight portfolio cumulative (Series)
      - perf_table: per-ticker returns for windows
    """
    if closes.empty:
        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
    closes = closes.sort_index()
    anchor_ts = pd.Timestamp(pick_date)
    sub = closes[closes.index >= anchor_ts]
    if sub.empty:
        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
    base = sub.iloc[0]
    normed = (sub / base) * 100
    # Equal-weight portfolio: mean across tickers each day
    portfolio = normed.mean(axis=1, skipna=True)

    # Per-window returns
    rows = []
    NAN = float("nan")
    for ticker in closes.columns:
        ser = closes[ticker].dropna()
        if ser.empty:
            continue
        last = float(ser.iloc[-1])
        after_pick = ser[ser.index >= anchor_ts]
        since = float((last / after_pick.iloc[0] - 1) * 100) if not after_pick.empty else NAN

        def ret_back(n: int) -> float:
            if len(ser) <= n:
                return NAN
            prev = ser.iloc[-n - 1]
            if pd.isna(prev) or prev == 0:
                return NAN
            return float((last / prev - 1) * 100)

        rows.append({
            "Ticker": ticker,
            "Last": last,
            "1D %": ret_back(1),
            "5D %": ret_back(5),
            "15D %": ret_back(15),
            "30D %": ret_back(30),
            "Since %": since,
        })
    perf = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
    return normed, portfolio, perf
