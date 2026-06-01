"""Strategy picks data layer — reads from data/external/.

Strategies tracked:
- v4 biotech (2026-04-22, 27 picks, XBI benchmark) — CSV
- v5 biotech (2026-05-15, 40 picks, XBI benchmark) — CSV (derived from picks.db)
- HK 高股息 (2026-03-20, 34 picks, 3110.HK benchmark) — CSV

B1 audit fix: picks.db not committed (contains thesis/conviction IP).
Sync via `scripts/sync_ledger.sh` to regenerate v5_picks.csv from local ic-foundry.

Prices fetched live via yfinance, cached 1 hour.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import portfolio_math as pm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_EXT = REPO_ROOT / "data" / "external"

V4_CSV = DATA_EXT / "v4_picks.csv"
V5_CSV = DATA_EXT / "v5_picks.csv"
HD_CSV = DATA_EXT / "hd_picks.csv"
IPO_CSV = DATA_EXT / "ipo_picks.csv"
IPO_INTRADAY_CSV = DATA_EXT / "ipo_day1_intraday.csv"


@st.cache_data(ttl=900)
def load_v4() -> pd.DataFrame:
    if not V4_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V4_CSV)


@st.cache_data(ttl=900)
def load_v5() -> pd.DataFrame:
    """v5 biotech: from CSV (derived from ic-foundry catalyst-monitor picks)."""
    if not V5_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V5_CSV)


@st.cache_data(ttl=900)
def load_hd() -> pd.DataFrame:
    if not HD_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_CSV)


@st.cache_data(ttl=900)
def load_ipo() -> pd.DataFrame:
    """HK IPO 打新 backtest — STATIC cross-section snapshot (18 rows).

    NOT a time-series strategy: this reads the frozen ipo_picks.csv only and is
    NEVER routed through compute_strategy_returns / yfinance. `code` kept as str
    so leading-zero HK codes (e.g. 0901) don't get coerced to int. `day1_ret` is
    a DECIMAL (3.84 = +384%); ×100 happens at the render layer.
    """
    if not IPO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(IPO_CSV, dtype={"code": str})


@st.cache_data(ttl=900)
def load_ipo_intraday() -> pd.DataFrame:
    """Listing-day 5-min intraday closes for the IPO backtest (17 listed names).

    Columns: code(str) / time(datetime) / close(float). `time` parsed once here;
    used for the post-open intraday-path small-multiples. Missing file → empty DF
    so the page degrades gracefully instead of crashing.
    """
    if not IPO_INTRADAY_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(IPO_INTRADAY_CSV, dtype={"code": str})
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    return df


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
    closes: pd.DataFrame, pick_date: str, rebalance_freq: str = "M",
    portfolio_syms: list[str] | tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Compute since-inception cumulative return (indexed=100) + TWO equal-weight
    portfolio curves + per-window returns table.

    The strategy is a SCORING model: rank by score, build the portfolio from the
    **Top 20** by rank (equal-weight headline; `portfolio_syms` = those 20 yf
    symbols). The portfolio curves (`normed` / `portfolio` / `portfolio_rebalanced`)
    are computed ONLY on `portfolio_syms`; the per-ticker `perf` table is computed
    on ALL columns of `closes` (so the page can show the full ranked universe in an
    expander). If `portfolio_syms` is None the portfolio uses every column.

    Dual-track: buy & hold (shipped curve) + monthly-rebalanced (reproducible-
    strategy curve). Both computed once here — `charts.py` consumes the series.

    Returns: (normed, portfolio, portfolio_rebalanced, perf_table)
    """
    _empty4 = (pd.DataFrame(), pd.Series(dtype=float),
               pd.Series(dtype=float), pd.DataFrame())
    if closes.empty:
        return _empty4
    closes = closes.sort_index()
    anchor_ts = pd.Timestamp(pick_date)
    sub_all = closes[closes.index >= anchor_ts]
    if sub_all.empty:
        return _empty4
    # M2 audit fix: forward-fill missing closes (trading halts) before normalization
    # so portfolio weight per ticker stays constant; avoid bias toward currently-trading subset
    sub_all = sub_all.ffill()
    # Portfolio = Top-N subset (by rank, passed as portfolio_syms); fall back to all.
    if portfolio_syms:
        port_cols = [c for c in portfolio_syms if c in sub_all.columns]
        sub = sub_all[port_cols] if port_cols else sub_all
    else:
        sub = sub_all
    # Single-source math (lib.portfolio_math — pure, unit-tested in tests/test_strategy.py)
    normed = pm.normalize(sub)
    portfolio = pm.buy_hold_portfolio(normed)
    portfolio_rebalanced = pm.rebalanced_portfolio(sub, freq=rebalance_freq)

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
    return normed, portfolio, portfolio_rebalanced, perf
