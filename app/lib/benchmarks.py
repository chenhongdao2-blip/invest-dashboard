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

BENCHMARKS = {
    "XLV":   "Health Care Select Sector",
    "XBI":   "S&P Biotech",
    "XPH":   "S&P Pharmaceuticals",
    "IXJ":   "iShares Global Healthcare",
    "IHF":   "US Healthcare Providers",
    "IHI":   "US Medical Devices",
    "^HSI":  "Hang Seng Index",
    "^GSPC": "S&P 500",
    "^SP500-352020": "S&P 500 Pharmaceuticals",   # US large-cap MNC pharma (vs XPH equal-weight)
    "^NDX": "Nasdaq 100",                          # tech 大盘 anchor for hc_ai / health-tech names
    "IGV": "Tech-Software (SaaS)",                 # US software/SaaS — health-tech (Veeva…) RS benchmark
    "XHS": "Health Care Services",                 # US hospital/facility operators — hospital_care RS benchmark
    # HK / China healthcare benchmarks — native currency (HKD / CNY). HSHCI is
    # iFind-seeded (not on yfinance); 512170 is yfinance-fetched. See
    # jobs/fetch_cn_benchmarks.py.
    "HSHCI.HK":  "Hang Seng Healthcare",
    "512170.SS": "CSI Healthcare (A-share)",
}


def _returns_row(t: str, ser: pd.Series | None, today: date) -> dict:
    """Compute the display row (last + 1d/5d/1m/ytd %) from a close series."""
    if ser is None:
        return {"ticker": t, "name": BENCHMARKS[t]}
    ser = ser.dropna().sort_index()
    if ser.empty:
        return {"ticker": t, "name": BENCHMARKS[t]}
    last = float(ser.iloc[-1])

    def ret(n: int) -> float | None:
        if len(ser) < n + 1:
            return None
        return float((ser.iloc[-1] / ser.iloc[-n - 1] - 1) * 100)

    ytd = None
    ytd_ser = ser[ser.index >= pd.Timestamp(f"{today.year}-01-01")]
    if not ytd_ser.empty:
        ytd = float((ser.iloc[-1] / ytd_ser.iloc[0] - 1) * 100)
    return {
        "ticker": t, "name": BENCHMARKS[t], "last": last,
        "1d_%": ret(1), "5d_%": ret(5), "1m_%": ret(21), "ytd_%": ytd,
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
    """Tidy DataFrame: index=ticker, columns=[name, last, 1d, 5d, 1m, ytd].
    Reads cron-cached DB first; falls back to live yfinance only if the DB is empty."""
    today = date.today()
    series = _series_from_db()
    if not series:
        series = _series_live()
    rows = [_returns_row(t, series.get(t), today) for t in BENCHMARKS]
    return pd.DataFrame(rows).set_index("ticker")
