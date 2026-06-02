"""Loaders for the Healthcare page's institutional-positioning + relative-performance
section. Reads the two committed CSVs baked by jobs/build_hc_overview_data.py
(cloud can't fetch iFind/yfinance live), so the page stays self-contained.

- hc_index_comparison.csv      : rebased-comparison source series (3 panels)
- china_fund_hc_positioning.csv: 12 funds' HC over/underweight vs benchmark
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_EXT = REPO_ROOT / "data" / "external"
IDX_PATH = _EXT / "hc_index_comparison.csv"
# Fund positioning: the FULL file (real fund names) is gitignored / local-only; the
# committed file is ANONYMISED (Fund 1–12) and is the only one that reaches Cloud.
# The loaders prefer the full file when it exists, else fall back to the public one —
# so local shows real names, Cloud shows Fund 1–12, with no per-environment branching.
POS_PATH_FULL = _EXT / "china_fund_hc_positioning_full.csv"
POS_PATH = _EXT / "china_fund_hc_positioning.csv"
POS_SRC_PATH_FULL = _EXT / "china_fund_hc_positioning_source_full.txt"
POS_SRC_PATH = _EXT / "china_fund_hc_positioning_source.txt"

# Panel layout: (panel_id, hero_series_id, [peer_series_ids]).
PANELS = [
    ("hk",   "HSHCI.HK",  ["HSI.HK", "HSTECH.HK"]),
    ("nbi",  "^NBI",      ["^IXIC"]),
    ("sphc", "^SP500-35", ["^GSPC"]),
]


@st.cache_data(ttl=3600)
def load_index_comparison() -> pd.DataFrame:
    """date-indexed long frame: date, series_id, name_en, name_cn, panel, close, source."""
    if not IDX_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(IDX_PATH, parse_dates=["date"])
    return df


def panel_series(df: pd.DataFrame, panel: str) -> dict[str, pd.Series]:
    """{series_id: close series indexed by date} for one panel."""
    sub = df[df["panel"] == panel]
    return {sid: g.set_index("date")["close"].sort_index() for sid, g in sub.groupby("series_id")}


def series_name(df: pd.DataFrame, series_id: str, *, prefer_cn: bool) -> str:
    row = df[df["series_id"] == series_id]
    if row.empty:
        return series_id
    return str(row.iloc[0]["name_cn" if prefer_cn else "name_en"])


@st.cache_data(ttl=3600)
def load_fund_positioning() -> pd.DataFrame:
    path = POS_PATH_FULL if POS_PATH_FULL.exists() else POS_PATH   # local real names → else anon
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # The builder writes the literal sentinel "N/A" into ow_uw_2026 for the one fund
    # that discloses no HC weight. pandas' DEFAULT na_values
    # includes "N/A", so read_csv silently coerces that token to float NaN — which
    # then (1) makes positioning_verdict's `== "N/A"` branch dead code (the fund is
    # dropped from the count, so the tally no longer sums to the universe), and
    # (2) makes the page's str(s).strip() stance lookup miss every key and fall
    # through to the Neutral fallback (mislabelling an undisclosed fund "中性").
    # Restore the sentinel at the loader boundary so the undisclosed fund is both
    # counted as N/A and routed to the dedicated NA stance key.
    if "ow_uw_2026" in df.columns:
        df["ow_uw_2026"] = df["ow_uw_2026"].where(df["ow_uw_2026"].notna(), "N/A")
    return df


@st.cache_data(ttl=3600)
def positioning_source() -> str:
    path = POS_SRC_PATH_FULL if POS_SRC_PATH_FULL.exists() else POS_SRC_PATH
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def positioning_verdict(df: pd.DataFrame) -> dict:
    """Counts + AUM-weighted tilt sign. AUM weighting parses the '3.3bn'/'995mn' strings.

    Returns {n_ow, n_uw, n_neu, n_na, aum_wt_dev, tilt} where tilt ∈ {OW, UW, ~flat}.
    aum_wt_dev is the AUM-weighted mean of deviation_2026 over funds WITH data — the
    "real money" tilt that the headline verdict rests on.
    """
    if df.empty:
        return {}
    ow_uw = df["ow_uw_2026"].astype(str)
    # contains() on BOTH OW and UW (symmetric): "Slightly OW"/"Slightly UW" must each
    # land in their lean. Exact =="UW" silently dropped "Slightly UW" while n_ow's
    # contains() caught "Slightly OW" — an asymmetry that understated the underweight
    # tally and broke the {n_ow}/{n_uw}/{n_neu}/{n_na} partition of the universe.
    n_ow = ow_uw.str.contains("OW", na=False).sum()
    n_uw = ow_uw.str.contains("UW", na=False).sum()
    n_neu = ow_uw.str.contains("Neutral", na=False).sum()
    n_na = (ow_uw == "N/A").sum()

    have = df.dropna(subset=["deviation_2026"]).copy()
    have["_aum"] = have["aum_2026"].map(_parse_aum)
    have = have.dropna(subset=["_aum"])

    counts = {"n_ow": int(n_ow), "n_uw": int(n_uw), "n_neu": int(n_neu), "n_na": int(n_na)}

    # No fund has BOTH a parseable AUM and a non-NaN deviation → zero real-money
    # signal. Emit an explicit no-data sentinel instead of a silent NaN: omit the
    # aum_wt_dev key entirely (so the caller's `.get("aum_wt_dev", 0.0)` default
    # fires and never formats a NaN into a finite-looking "+X.Xpp"), and refuse to
    # advertise a "~flat" tilt that no money backs. `data_available` lets the
    # caller branch on the no-data case explicitly.
    denom = float(have["_aum"].sum()) if not have.empty else 0.0
    if have.empty or denom <= 0:
        # No parseable AUM behind any non-NaN deviation (empty) OR a zero / non-positive
        # AUM denominator → no real-money signal. Same no-data sentinel as the empty
        # case: OMIT aum_wt_dev (so the caller's .get(...,0.0) default fires and never
        # formats a NaN into a finite-looking "+X.Xpp"), and refuse a "~flat" tilt that
        # zero money backs. A non-empty `have` whose AUMs all parse to 0.0 lands here too.
        return {**counts, "data_available": False, "tilt": "n/a"}

    aum_wt_dev = float((have["deviation_2026"] * have["_aum"]).sum() / denom)
    tilt = "OW" if aum_wt_dev > 0.002 else "UW" if aum_wt_dev < -0.002 else "~flat"
    return {**counts, "data_available": True, "aum_wt_dev": aum_wt_dev, "tilt": tilt}


def _parse_aum(s) -> float | None:
    """'3.3bn' → 3300, '995mn' → 995, '2,609mn' → 2609 (USD mn). None if unparseable."""
    if s is None:
        return None
    t = str(s).strip().lower().replace(",", "").replace("~", "").replace("usd", "").strip()
    try:
        if t.endswith("bn"):
            return float(t[:-2]) * 1000.0
        if t.endswith("mn"):
            return float(t[:-2])
        return float(t)
    except ValueError:
        return None
