"""Benchmark index data.

Primary source: benchmarks_daily in snapshots.db (cron-fetched on a US runner).
Live yfinance is a FALLBACK only — live calls from Streamlit Cloud get rate-limited
by Yahoo (esp. ^HSI), which is why the cron-cached DB is preferred.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import db

# ---------------------------------------------------------------------------
# _META: canonical source of truth for all benchmark symbols.
# Each entry: {"name": <EN display name>}
# ---------------------------------------------------------------------------
_META: dict[str, dict] = {
    # ---- Healthcare --------------------------------------------------------
    "XLV":          {"name": "Health Care Select Sector"},
    "XBI":          {"name": "S&P Biotech"},
    "XPH":          {"name": "S&P Pharmaceuticals"},
    "IXJ":          {"name": "iShares Global Healthcare"},
    "IHF":          {"name": "US Healthcare Providers"},
    "IHI":          {"name": "US Medical Devices"},
    "^SP500-352020":{"name": "S&P 500 Pharmaceuticals"},   # US large-cap MNC pharma
    "IGV":          {"name": "Tech-Software (SaaS)"},       # health-tech RS benchmark
    "XHS":          {"name": "Health Care Services"},       # hospital_care RS benchmark
    # ---- HK / China healthcare benchmarks (native currency) ---------------
    "HSHCI.HK":     {"name": "Hang Seng Healthcare"},
    "512170.SS":    {"name": "CSI Healthcare (A-share)"},
    # ---- Broad market ------------------------------------------------------
    "^HSI":         {"name": "Hang Seng Index"},
    "^GSPC":        {"name": "S&P 500"},
    "^NDX":         {"name": "Nasdaq 100"},
    # ---- S&P 500 GICS sector ETFs (10 non-healthcare) ---------------------
    "XLK":          {"name": "Information Technology"},
    "XLF":          {"name": "Financials"},
    "XLE":          {"name": "Energy"},
    "XLB":          {"name": "Materials"},
    "XLI":          {"name": "Industrials"},
    "XLY":          {"name": "Consumer Discretionary"},
    "XLP":          {"name": "Consumer Staples"},
    "XLC":          {"name": "Communication Services"},
    "XLU":          {"name": "Utilities"},
    "XLRE":         {"name": "Real Estate"},
    # ---- AI / semiconductor supply-chain (cross-market; LLM Wiki, ai-researcher reviewed) ----
    "^SOX":         {"name": "PHLX Semiconductor"},
    "SMH":          {"name": "VanEck Semiconductor"},
    "AIQ":          {"name": "Global X AI & Tech"},
    "2644.T":       {"name": "Global X Japan Semiconductor"},
    "091160.KS":    {"name": "KODEX Korea Semiconductor"},
    "442580.KS":    {"name": "PLUS Global HBM Semiconductor"},
    "512480.SS":    {"name": "CSI Semiconductor"},
    "515880.SS":    {"name": "CSI Telecom (Optical/CPO)"},
    "159819.SZ":    {"name": "CSI Artificial Intelligence"},
    "588200.SS":    {"name": "STAR Market Chip"},
    "3191.HK":      {"name": "Global X China Semiconductor"},
}

# Derived flat dict — keeps all historic callers (Ticker Drill _route_benchmarks /
# BENCHMARKS.get etc.) working without any change.
BENCHMARKS: dict[str, str] = {k: v["name"] for k, v in _META.items()}

# ---------------------------------------------------------------------------
# PANELS — ordered groups used by the benchmark table page.
# ("ai", [...]) is reserved as a future placeholder (commented out).
# ---------------------------------------------------------------------------
PANELS = [
    ("broad_market",  ["^GSPC", "^NDX", "^HSI"]),
    ("sp500_sector",  ["XLK", "XLC", "XLY", "XLF", "XLV", "XLI", "XLP", "XLE", "XLU", "XLB", "XLRE", "^GSPC"]),
    ("healthcare",    ["XLV", "XBI", "XPH", "^SP500-352020", "IHI", "IHF", "XHS", "IGV", "IXJ", "HSHCI.HK", "512170.SS"]),
    # AI / semiconductor supply-chain — cross-market headline set (ai-researcher reviewed:
    # US semi anchor + AI theme, JP/KR semi + HBM, A-share semi/optical/AI/STAR, HK China semi).
    ("ai",            ["^SOX", "SMH", "AIQ", "2644.T", "091160.KS", "442580.KS",
                       "512480.SS", "515880.SS", "159819.SZ", "588200.SS", "3191.HK"]),
]


def _returns_row(t: str, ser: pd.Series | None, today: date) -> dict:
    """Compute the display row (last + 1d/5d/1m/3m/ytd %) from a close series."""
    if ser is None:
        return {"ticker": t, "name": BENCHMARKS[t]}
    ser = ser.dropna().sort_index()
    if ser.empty:
        return {"ticker": t, "name": BENCHMARKS[t]}
    last = float(ser.iloc[-1])

    def ret(n: int) -> float | None:
        if len(ser) <= n:
            return None
        prev = ser.iloc[-n - 1]
        if pd.isna(prev) or prev == 0:
            return None
        return float((ser.iloc[-1] / prev - 1) * 100)

    # YTD: anchor to data-driven year (not today.year) so cross-year DB rows work
    yr = ser.index.max().year
    ytd_ser = ser[ser.index >= pd.Timestamp(f"{yr}-01-01")]
    ytd: float | None = None
    if not ytd_ser.empty:
        ytd = float((ser.iloc[-1] / ytd_ser.iloc[0] - 1) * 100)

    return {
        "ticker": t, "name": BENCHMARKS[t], "last": last,
        "1d_%": ret(1), "5d_%": ret(5), "1m_%": ret(21),
        "3m_%": ret(63),
        "ytd_%": ytd,
    }


@st.cache_data(ttl=1800)
def _series_from_db() -> dict[str, pd.Series]:
    """{ticker: close series} from cron-cached benchmarks_daily (empty if not populated)."""
    df = db.query("SELECT ticker, date, close FROM benchmarks_daily ORDER BY date")
    if df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    return {t: g.set_index("date")["close"] for t, g in df.groupby("ticker")}


@st.cache_data(ttl=1800, show_spinner="Fetching benchmarks (live fallback)…")
def _series_live() -> dict[str, pd.Series]:
    """Live yfinance fallback (used only when benchmarks_daily is empty)."""
    today = date.today()
    start = (today - timedelta(days=200)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    try:
        d = yf.download(list(BENCHMARKS), start=start, end=end,
                        auto_adjust=True, progress=False, threads=True, group_by="ticker")
    except Exception:
        return {}
    out: dict[str, pd.Series] = {}
    for t in BENCHMARKS:
        try:
            if isinstance(d.columns, pd.MultiIndex):
                out[t] = d[t]["Close"] if t in d.columns.get_level_values(0) else pd.Series(dtype=float)
            else:
                out[t] = d["Close"]
        except Exception:
            out[t] = pd.Series(dtype=float)
    return out


@st.cache_data(ttl=1800)
def close_series() -> dict[str, pd.Series]:
    """Public accessor: {benchmark symbol: close series}. Cron-cached DB first,
    live yfinance fallback only if the DB is empty. Used by the Ticker Drill
    relative-strength chart."""
    return _series_from_db() or _series_live()


@st.cache_data(ttl=1800)
def fetch_benchmarks() -> pd.DataFrame:
    """Tidy DataFrame: index=ticker, columns=[name, last, 1d, 5d, 1m, 3m, ytd].
    Reads cron-cached DB first; falls back to live yfinance only if the DB is empty."""
    today = date.today()
    series = _series_from_db()
    if not series:
        series = _series_live()
    rows = [_returns_row(t, series.get(t), today) for t in BENCHMARKS]
    return pd.DataFrame(rows).set_index("ticker")
