"""CMSI Coverage — 28 ticker cover list with full multiples + cross-sector tags.

D5 implementation:
- Region tabs (HK / US / CN-A)
- Per region: full table with multiples + return windows + cross-sector membership
- Defaults: name_cn first, mcap desc (M10 audit)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n
from lib import model_view


def _reco_label(v) -> str:
    """yfinance recommendationMean 1.0-5.0 → label."""
    if v is None or pd.isna(v):
        return "—"
    if v < 1.5:
        return "Strong Buy"
    if v < 2.5:
        return "Buy"
    if v < 3.5:
        return "Hold"
    if v < 4.5:
        return "Sell"
    return "Strong Sell"

st.set_page_config(
    page_title="CMSI Coverage · invest-dashboard",
    page_icon="💎",
    layout="wide",
)

# --- Sidebar global search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="cmsi")

i18n.init_lang()
i18n.render_lang_toggle()

theme.page_header(i18n.t("cov.title"))
st.caption(i18n.t("cov.caption", date=(db.latest_snapshot_date() or "—")))


# --- Load CMSI Coverage tickers ---
cmsi = db.sector_tickers("healthcare", "_coverage")
if cmsi.empty:
    st.warning("No CMSI coverage data — check config/universes/cmsi_coverage_hc.yml")
    st.stop()

tickers = tuple(cmsi["ticker"].tolist())

# --- Compute returns + multiples for all CMSI tickers ---
closes = db.get_close_series_usd(tickers)
rets = db.compute_returns(closes)
mults = db.latest_multiples(tickers)

# --- Find cross-sector membership ---
# Query all sectors each ticker belongs to (excluding _coverage)
@st.cache_data(ttl=300)
def cross_membership(tickers: tuple[str, ...]) -> dict[str, list[str]]:
    # param must NOT start with '_' — underscore-prefixed args are excluded from
    # the Streamlit cache key, so different ticker tuples would collide.
    placeholders = ",".join("?" * len(tickers))
    df = db.query(
        f"SELECT ticker, sector FROM universe_member "
        f"WHERE ticker IN ({placeholders}) AND sector != '_coverage' "
        f"ORDER BY ticker, sector",
        tuple(tickers),
    )
    out: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        out.setdefault(row["ticker"], []).append(row["sector"])
    return out


cross = cross_membership(tickers)

# --- Merge into display DataFrame ---
merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
merged["name_cn"] = cmsi.set_index("ticker")["name_cn"]
merged["name_en"] = cmsi.set_index("ticker")["name_en"]
merged["region"] = cmsi.set_index("ticker")["region"]
merged["BBG"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]
if not mults.empty:
    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
              "ev_ebitda", "ev_sales", "fcf_yield", "pb",
              # m8 audit additions
              "last_price", "last_price_usd", "target_price_mean",
              "recommendation_mean", "n_analysts"]:
        if c in mults.columns:
            merged[c] = mults[c]

# m8 audit: compute TP upside % from analyst consensus
if "target_price_mean" in merged.columns and "last_price" in merged.columns:
    merged["tp_upside_%"] = (
        (merged["target_price_mean"] - merged["last_price"])
        / merged["last_price"] * 100
    )
else:
    merged["tp_upside_%"] = pd.NA

# m8 audit: alpha vs HSI (港股 sell-side daily 必看)
@st.cache_data(ttl=600)
def _hsi_ytd() -> float | None:
    bench_df = bm.fetch_benchmarks()
    if bench_df.empty or "^HSI" not in bench_df.index:
        return None
    v = bench_df.loc["^HSI", "ytd_%"]
    return float(v) if pd.notna(v) else None


hsi_ytd = _hsi_ytd()
if hsi_ytd is not None:
    merged["vs_hsi_ytd"] = merged["ytd_%"] - hsi_ytd
else:
    merged["vs_hsi_ytd"] = pd.NA

# Cross-sector tags: convert to icons
def _cross_tag(ticker: str) -> str:
    sectors = cross.get(ticker, [])
    if not sectors:
        return ""
    # 简短 emoji mapping
    icons = {
        "biotech": "BIO", "pharma": "PHAR", "hc_ai": "AI",
        "medtech": "MED", "hospital_care": "HOSP",
        "managed_care": "MC", "cxo": "CXO",
    }
    return " ".join(icons.get(s, f"[{s}]") for s in sectors)


merged["Cross-Sector"] = [_cross_tag(t) for t in merged.index]

# --- Default sort: mcap desc (M10 audit) ---
merged = merged.sort_values("market_cap_usd", ascending=False, na_position="last")

# --- Region tabs ---
regions = ["HK", "US", "CN", "All"]
tabs = st.tabs([f"{r} ({sum(merged['region']==r) if r != 'All' else len(merged)})" for r in regions])


def render_region(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No tickers in this region.")
        return

    # BUGFIX: Build NUMERIC DataFrame (not pre-formatted strings) so column sort
    # works correctly. Streamlit column_config handles display format; Styler.apply
    # still works for background_gradient on the numeric values.
    # Note: BBG column dropped — duplicates the ticker index. Name column uses
    # name_cn first, falls back to name_en, then ticker.
    disp = pd.DataFrame(index=df.index)
    # Click-through to the analyst-model one-pager (Model Drill). Only covered
    # names that actually have an extracted model get the 📊 link; others blank.
    _mdl_col = "模型" if i18n.get_lang() == "zh" else "Model"
    disp[_mdl_col] = [f"/Model_Drill?ticker={t}" if model_view.has_model(t) else ""
                      for t in df.index]
    disp["Name"] = df["name_cn"].fillna(df["name_en"]).fillna(df.index.to_series())
    disp["Mcap USD ($B)"] = df["market_cap_usd"] / 1e9              # numeric, B
    disp["YTD %"] = df["ytd_%"]
    disp["1M %"] = df["1m_%"]
    disp["5D %"] = df["5d_%"]
    disp["1D %"] = df["1d_%"]
    disp["vs HSI YTD"] = df["vs_hsi_ytd"]
    disp["Trail P/E"] = df["trailing_pe"]
    disp["Fwd P/E"] = df["forward_pe"]
    disp["EV/EBITDA"] = df["ev_ebitda"]
    # FCF Yld stored as decimal (0.025); pre-multiply by 100 so column_config
    # "%+.2f%%" displays "+2.50%". Streamlit's NumberColumn format string does
    # not implement printf's %%-as-percent-multiplier shorthand.
    disp["FCF Yld"] = df["fcf_yield"] * 100
    disp["P/B"] = df["pb"]
    # TP Upside % / Reco / N analysts / Cross columns removed per user request
    # (analyst TP/Reco are LOW-reliability yfinance consensus; Cross was clutter).
    disp.index.name = "Ticker"

    # Stage 2: render as FT-editorial HTML table (iframe) instead of st.dataframe.
    # Solves the glide-data-grid canvas dark-mode penetration (black cells), and
    # gives click-sort + tabular-nums + <th title> tooltips with full CSS control.
    # Column kinds map onto render_html_table; coloring is text-only (染字不染底).
    # FCF Yld is already ×100 (pct units) above, so it goes in pct_cols.
    ui.render_html_table(
        disp,
        money_b_cols=["Mcap USD ($B)"],
        pct_cols=["YTD %", "1M %", "5D %", "1D %", "vs HSI YTD"],
        pct2_cols=["FCF Yld"],
        mult_cols=["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"],
        text_cols=["Name"],
        nav_cols=[_mdl_col],
        nav_label="📊",
        height=620,
        column_labels={
            **i18n.common_cols(),
            "vs HSI YTD": i18n.t("cov.col.vs_hsi"),
        },
        index_label=i18n.t("common.col.ticker"),
    )


for tab, region in zip(tabs, regions):
    with tab:
        if region == "All":
            render_region(merged)
        else:
            render_region(merged[merged["region"] == region])

# --- Onboarding ---
with st.expander(i18n.t("cov.onboarding.title")):
    st.markdown(i18n.t("cov.onboarding.body"))

st.divider()
st.caption(i18n.t("cov.caption.tags"))
st.caption(i18n.t("cov.caption.source", n=len(merged)))
