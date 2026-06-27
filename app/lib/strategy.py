"""Strategy picks data layer — reads from data/external/.

Strategies tracked:
- v4 biotech (2026-04-22, 27 picks, XBI benchmark) — CSV
- v5 biotech (2026-05-15, 40 picks, XBI benchmark) — CSV (derived from picks.db)
- HK 高股息 v1 (2026-03-20, 34 picks equal-weight, 3466.HK benchmark) — CSV
- HK 高股息 v2 (2026-06-11, 20 picks score-weighted + 12% cash, 3466.HK) — CSV
  (standard build, George sign-off 2026-06-11; canonical source:
  portfolio-engine/high_div_screen standard-build output. v1 history is frozen
  and never edited — v2 is a NEW book starting 2026-06-11, not a restatement.)

B1 audit fix: picks.db not committed (contains thesis/conviction IP).
Sync via `scripts/sync_ledger.sh` to regenerate v5_picks.csv from local ic-foundry.

Prices fetched live via yfinance, cached 1 hour.
"""

from __future__ import annotations

import time
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
HD_V2_CSV = DATA_EXT / "hd_picks_v2.csv"
IPO_CSV = DATA_EXT / "ipo_picks.csv"
IPO_INTRADAY_CSV = DATA_EXT / "ipo_day1_intraday.csv"
# Acquired / delisted picks: yfinance purges their history, so a live fetch returns
# nothing and the book silently drops the name (+ "possibly delisted" warning). This
# map pins each to its cash-out value (held as cash from delist_date), so the book
# accounts an acquired pick at the deal price instead of losing it. Analyst-editable.
DELISTED_CSV = DATA_EXT / "delisted_overrides.csv"


@st.cache_data(ttl=3600)
def _delisted_overrides() -> dict[str, float]:
    """{yf_sym: final_cash_price} for acquired/delisted picks. Empty if file absent."""
    if not DELISTED_CSV.exists():
        return {}
    d = pd.read_csv(DELISTED_CSV)
    fp = pd.to_numeric(d["final_price"], errors="coerce")
    return {str(s): float(p) for s, p in zip(d["yf_sym"], fp)
            if pd.notna(s) and pd.notna(p)}


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
def load_hd_v2() -> pd.DataFrame:
    """HD v2 standard build (2026-06-11). Public fields only (rank/score/weight/
    bucket/runrate) — B1 audit convention, no thesis/conviction columns.
    weight_pct = absolute book weight, Σ=88.01; the other ~12% is idle cash by
    design (not an error). bucket: rate=利率溢价桶 / nonrate=非利率桶."""
    if not HD_V2_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_V2_CSV)


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
    # HD benchmarks (George 2026-06-12): primary 3466.HK Hang Seng High
    # Dividend 30 ETF (was 3110.HK), plus ^HSI as a broad-market reference
    # overlay — both versions, so the v1/v2 curves stay comparable.
    "hk_hd": {
        "name": "💰 HK 高股息 v1",
        "emoji": "💰",
        "loader": load_hd,
        "pick_date": "2026-03-20",
        "benchmark": "3466.HK",
        "benchmark_name": "恒生高股息30",
        "benchmark2": "^HSI",
        "benchmark2_name": "恒生指数",
    },
    "hk_hd_v2": {
        "name": "💰 HK 高股息 v2",
        "emoji": "💰",
        "loader": load_hd_v2,
        "pick_date": "2026-06-11",
        "benchmark": "3466.HK",
        "benchmark_name": "恒生高股息30",
        "benchmark2": "^HSI",
        "benchmark2_name": "恒生指数",
        # score-weighted book: weight_pct column = absolute %, plus idle cash.
        "weight_col": "weight_pct",
        "cash_pct": 12.0,
        # page renders this INSIDE the hk_hd tab (version toggle), not as its
        # own tab — see HD_VERSION_GROUP filter in 4_Strategy_Picks.py.
        "version_of": "hk_hd",
    },
}


@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
    """Wide-format close DataFrame for picks. Live yfinance, cached 1h.

    yfinance occasionally fails a whole burst of symbols in one batch
    ("possibly delisted" on clearly-listed names = rate-limit artifact, seen
    2026-06-11 with 12/21 HK names incl. the benchmark). A partial frame
    would be CACHED for 1h and silently shrink the book, so missing symbols
    get one re-download after a short pause; if still missing, the page is
    warned rather than left silently degraded.
    """
    if not yf_syms:
        return pd.DataFrame()
    end = (date.today() + timedelta(days=1)).isoformat()

    def _download(syms: tuple[str, ...]) -> dict[str, pd.Series]:
        try:
            d = yf.download(
                list(syms), start=start, end=end,
                auto_adjust=True, progress=False, threads=True, group_by="ticker",
            )
        except Exception as e:
            st.warning(f"Live fetch failed: {e}")
            return {}
        if d.empty:
            return {}
        if len(syms) == 1:
            sym = syms[0]
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.droplevel(1)
            if "Close" in d.columns:
                ser = d["Close"].dropna()
                if not ser.empty:
                    return {sym: ser}
            return {}
        out: dict[str, pd.Series] = {}
        for sym in syms:
            try:
                if sym in d.columns.get_level_values(0):
                    ser = d[sym]["Close"].dropna()
                    if not ser.empty:
                        out[sym] = ser
            except Exception:
                pass
        return out

    out = _download(tuple(yf_syms))
    missing = tuple(s for s in yf_syms if s not in out)
    if missing:
        time.sleep(2)  # rate-limit pause before the retry batch
        out.update(_download(missing))

    # Acquired/delisted picks (yfinance returns nothing): pin to cash-out value, a
    # flat series from `start` to today, so the book holds them as cash at the deal
    # price instead of dropping them + warning. Done BEFORE the missing-warning so a
    # known cash-out is never flagged as a fetch failure.
    overrides = _delisted_overrides()
    flat_idx = pd.bdate_range(start=start, end=date.today())
    for sym in yf_syms:
        if sym in overrides and len(flat_idx):
            out[sym] = pd.Series(overrides[sym], index=flat_idx, name=sym)

    still = [s for s in yf_syms if s not in out]
    if still:
        st.warning(f"Price fetch incomplete after retry: {', '.join(still)}")
    if not out:
        return pd.DataFrame()
    return pd.DataFrame(out).sort_index()


def compute_strategy_returns(
    closes: pd.DataFrame, pick_date: str, rebalance_freq: str = "M",
    portfolio_syms: list[str] | tuple[str, ...] | None = None,
    weights: pd.Series | None = None, cash_pct: float = 0.0,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Compute since-inception cumulative return (indexed=100) + TWO portfolio
    curves (equal-weight by default) + per-window returns table.

    Weighted mode (HD v2): pass `weights` (pd.Series indexed by yf_sym, DECIMAL
    fractions, e.g. 0.0641) + `cash_pct` (12.0 = 12% idle cash, 0 return).
    Curves switch to pm.weighted_* (buy & hold drift + reset-to-target monthly);
    `weights=None` keeps the original equal-weight path — v1/v4/v5 unchanged.

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
    if weights is not None:
        cash_w = float(cash_pct) / 100.0
        portfolio = pm.weighted_buy_hold_portfolio(normed, weights, cash_weight=cash_w)
        portfolio_rebalanced = pm.weighted_rebalanced_portfolio(
            sub, weights, cash_weight=cash_w, freq=rebalance_freq)
    else:
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
