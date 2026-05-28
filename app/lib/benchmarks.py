"""Live benchmark data via yfinance (cached 30 min).

Benchmarks are NOT in our SQLite universe — fetched on demand.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import yfinance as yf

BENCHMARKS = {
    "XLV":   "Health Care Select Sector",
    "XBI":   "S&P Biotech",
    "XPH":   "S&P Pharmaceuticals",
    "IXJ":   "iShares Global Healthcare",
    "IHF":   "US Healthcare Providers",
    "IHI":   "US Medical Devices",
    "^HSI":  "Hang Seng Index",
    "^GSPC": "S&P 500",
}


@st.cache_data(ttl=1800, show_spinner="Fetching benchmarks…")
def fetch_benchmarks() -> pd.DataFrame:
    """Return a tidy DataFrame: index=ticker, columns=[name, last, 1d, 5d, 1m, ytd]."""
    tickers = list(BENCHMARKS.keys())
    today = date.today()
    start = (today - timedelta(days=180)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    try:
        d = yf.download(
            tickers, start=start, end=end,
            auto_adjust=True, progress=False, threads=True, group_by="ticker",
        )
    except Exception as e:
        return pd.DataFrame()

    rows = []
    for t in tickers:
        try:
            if t in d.columns.get_level_values(0):
                ser = d[t]["Close"].dropna().sort_index()
            else:
                ser = pd.Series(dtype=float)
            if ser.empty:
                rows.append({"ticker": t, "name": BENCHMARKS[t]})
                continue
            last = float(ser.iloc[-1])

            def ret(n: int) -> float | None:
                if len(ser) < n + 1:
                    return None
                return float((ser.iloc[-1] / ser.iloc[-n - 1] - 1) * 100)

            # YTD
            ytd = None
            this_year_start = pd.Timestamp(f"{today.year}-01-01")
            ytd_ser = ser[ser.index >= this_year_start]
            if not ytd_ser.empty:
                ytd = float((ser.iloc[-1] / ytd_ser.iloc[0] - 1) * 100)

            rows.append({
                "ticker": t,
                "name": BENCHMARKS[t],
                "last": last,
                "1d_%": ret(1),
                "5d_%": ret(5),
                "1m_%": ret(21),
                "ytd_%": ytd,
            })
        except Exception:
            rows.append({"ticker": t, "name": BENCHMARKS[t]})

    df = pd.DataFrame(rows).set_index("ticker")
    return df
