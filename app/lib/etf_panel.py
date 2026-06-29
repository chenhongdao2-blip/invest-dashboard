"""ETF panel loader — reader for the Healthcare · ETF 专栏 page.

Pure reader over the three baked artifacts (see jobs/build_etf_panel.py):
    data/external/etf_hc_universe.csv   # 1 row / ETF: profile + perf windows
    data/external/etf_hc_holdings.csv   # long: 1 row / holding (rank/symbol/name/weight_pct)
    data/external/etf_hc_meta.json      # as_of + source + per-ETF weight coverage

Mirrors lib/ipo_tracker.py: the deployed app cannot call the etf-data MCP, so a build
job bakes the data and this loader just reads it. Every function is empty/{}-safe on a
missing file (the page degrades to a notice, never crashes).

Holdings shape (from upstream): each ETF has a weighted head (~top 25; `rank`/`weight_pct`
populated) and a symbol-only tail (`rank`/`name`/`weight_pct` are NaN). The tail is the
"+N more constituents" set. An unknown weight is NaN — NEVER 0 (zero would lie).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Module-level path constants (monkeypatchable in tests).
UNIVERSE_CSV = REPO_ROOT / "data" / "external" / "etf_hc_universe.csv"
HOLDINGS_CSV = REPO_ROOT / "data" / "external" / "etf_hc_holdings.csv"
META_JSON = REPO_ROOT / "data" / "external" / "etf_hc_meta.json"

UNIVERSE_COLS = [
    "domain", "sub_sector", "ticker", "name", "aum", "expense_ratio",
    "price", "year_high", "year_low",
    "ret_1m", "ret_3m", "ret_ytd", "ret_1y", "ret_3y", "ret_5y",
    "vol", "max_dd",
]
HOLDINGS_COLS = ["etf_ticker", "rank", "symbol", "name", "weight_pct"]


@st.cache_data(ttl=600)
def _read_csv(path_str: str, _mtime: float, columns: tuple[str, ...]) -> pd.DataFrame:
    """Cached CSV read keyed on (path, mtime) so a re-bake busts the cache instead of
    serving stale data for the TTL. `columns` only seeds the empty-frame shape."""
    return pd.read_csv(path_str)


def load_etf_universe() -> pd.DataFrame:
    """One row per ETF. Empty DataFrame (with expected columns) if the file is absent.

    The existence check reads the *current* module-level UNIVERSE_CSV each call (so it
    is monkeypatchable and reacts to a rebuild); only the file read itself is cached."""
    p = UNIVERSE_CSV
    if not p.exists():
        return pd.DataFrame(columns=UNIVERSE_COLS)
    return _read_csv(str(p), p.stat().st_mtime, tuple(UNIVERSE_COLS))


def load_etf_holdings() -> pd.DataFrame:
    """Long holdings table. Empty DataFrame (with expected columns) if the file is absent.

    `rank` and `weight_pct` stay nullable floats — tail rows keep NaN (unknown ≠ zero)."""
    p = HOLDINGS_CSV
    if not p.exists():
        return pd.DataFrame(columns=HOLDINGS_COLS)
    return _read_csv(str(p), p.stat().st_mtime, tuple(HOLDINGS_COLS))


def holdings_for(
    holdings_df: pd.DataFrame, etf_ticker: str
) -> tuple[pd.DataFrame, list[str]]:
    """Split one ETF's holdings into (weighted_df, tail_symbols).

    weighted_df : rows with a non-null `rank`, sorted by rank ascending — the named,
                  weighted top holdings (all `weight_pct` non-null).
    tail_symbols: the symbol-only tail (rows with null `rank`) as a list[str].
    """
    if holdings_df is None or holdings_df.empty or "etf_ticker" not in holdings_df.columns:
        return pd.DataFrame(columns=HOLDINGS_COLS), []
    sub = holdings_df[holdings_df["etf_ticker"] == etf_ticker]
    if sub.empty:
        return pd.DataFrame(columns=HOLDINGS_COLS), []
    weighted = (
        sub[sub["rank"].notna()]
        .sort_values("rank")
        .reset_index(drop=True)
    )
    tail = (
        sub[sub["rank"].isna()]["symbol"]
        .dropna()
        .astype(str)
        .tolist()
    )
    return weighted, tail


@st.cache_data(ttl=600)
def _read_meta(path_str: str, _mtime: float) -> dict:
    try:
        return json.loads(Path(path_str).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def etf_meta() -> dict:
    """Metadata dict (as_of / source / weight coverage). Empty dict if the file is absent."""
    p = META_JSON
    if not p.exists():
        return {}
    return _read_meta(str(p), p.stat().st_mtime)
