"""AI Universe — full AI supply-chain universe (no CMSI cover list for AI yet).

Adapted from `1_💎_CMSI_Coverage.py`: AI has no coverage list in ai.yml, so this
page surfaces the ENTIRE AI universe (domain='ai', ~135 names) grouped by the 6
supply-chain layers, with region tabs. `vs HSI` (HK-centric) is replaced by
`vs ^SOX YTD` (the AI-domain primary benchmark). Empty-data safe: missing prices/
multiples render as "—" and an empty universe shows a warning.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(
    page_title="AI Universe · invest-dashboard",
    page_icon="💎",
    layout="wide",
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "ai.yml"


cfg = db.load_domain_cfg(str(DOMAIN_CFG))

# --- Sidebar global search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="ai_cov")

i18n.init_lang()
i18n.render_lang_toggle()

theme.page_header(i18n.t("ai.cov.title"))
st.caption(i18n.t("ai.cov.caption", date=(db.latest_snapshot_date() or "—")))


# --- Load the full AI universe across all 6 sectors ---
frames = []
for sec in cfg["sectors"]:
    uni = db.sector_tickers("ai", sec["id"])
    if uni.empty:
        continue
    uni = uni.copy()
    uni["sector"] = sec["id"]
    frames.append(uni)

if not frames:
    st.warning("No AI universe data — check config/universes/ai_*.yml backfill.")
    st.stop()

uni_all = pd.concat(frames, ignore_index=True)
# a ticker can appear in multiple layers — keep first sector membership for display,
# but collect ALL layer tags for the Layers column.
sector_tags: dict[str, list[str]] = {}
for _, r in uni_all.iterrows():
    sector_tags.setdefault(r["ticker"], []).append(r["sector"])
uni_dedup = uni_all.drop_duplicates(subset="ticker", keep="first").set_index("ticker")

tickers = tuple(uni_dedup.index.tolist())

# --- Compute returns + multiples ---
closes = db.get_close_series_usd(tickers)
rets = db.compute_returns(closes)
mults = db.latest_multiples(tickers)

# --- Merge into display DataFrame ---
merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
merged["name_cn"] = uni_dedup["name_cn"]
merged["name_en"] = uni_dedup["name_en"]
merged["region"] = uni_dedup["region"]
for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
          "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    if not mults.empty and c in mults.columns:
        merged[c] = mults[c]
    elif c not in merged.columns:
        merged[c] = pd.NA   # empty-data safe: column always present

# vs ^SOX YTD (AI-domain primary benchmark, replaces HSI on the HC coverage page)
@st.cache_data(ttl=600)
def _sox_ytd() -> float | None:
    bench_df = bm.fetch_benchmarks()
    if bench_df.empty or "^SOX" not in bench_df.index:
        return None
    v = bench_df.loc["^SOX", "ytd_%"]
    return float(v) if pd.notna(v) else None


sox_ytd = _sox_ytd()
if sox_ytd is not None and "ytd_%" in merged.columns:
    merged["vs_sox_ytd"] = merged["ytd_%"] - sox_ytd
else:
    merged["vs_sox_ytd"] = pd.NA

# Supply-chain layer tags (icons)
_LAYER_ICONS = {
    "ai_equip": "EQP", "ai_chip": "CHIP", "ai_memory": "MEM",
    "ai_foundry": "FAB", "ai_interconnect": "INTC", "ai_server": "SRV",
}


def _layer_tag(ticker: str) -> str:
    return " ".join(_LAYER_ICONS.get(s, f"[{s}]") for s in sector_tags.get(ticker, []))


merged["Layers"] = [_layer_tag(t) for t in merged.index]

# --- Default sort: mcap desc ---
if "market_cap_usd" in merged.columns:
    merged = merged.sort_values("market_cap_usd", ascending=False, na_position="last")


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """Safe column accessor: missing column (data not yet fetched) → all-NaN."""
    if name in df.columns:
        return df[name]
    return pd.Series([pd.NA] * len(df), index=df.index)


def render_region(df: pd.DataFrame) -> None:
    if df.empty:
        st.caption("No tickers in this region.")
        return

    disp = pd.DataFrame(index=df.index)
    disp["Name"] = df["name_cn"].fillna(df["name_en"]).fillna(df.index.to_series())
    disp["Layers"] = df["Layers"]
    disp["Mcap USD ($B)"] = _col(df, "market_cap_usd") / 1e9
    disp["YTD %"] = _col(df, "ytd_%")
    disp["1M %"] = _col(df, "1m_%")
    disp["5D %"] = _col(df, "5d_%")
    disp["1D %"] = _col(df, "1d_%")
    disp["vs SOX YTD"] = _col(df, "vs_sox_ytd")
    disp["Trail P/E"] = _col(df, "trailing_pe")
    disp["Fwd P/E"] = _col(df, "forward_pe")
    disp["EV/EBITDA"] = _col(df, "ev_ebitda")
    # FCF Yld stored as decimal; ×100 so pct2 column shows "+2.50%".
    fcf = _col(df, "fcf_yield")
    disp["FCF Yld"] = fcf * 100 if fcf.notna().any() else fcf
    disp["P/B"] = _col(df, "pb")
    disp.index.name = "Ticker"

    ui.render_html_table(
        disp,
        money_b_cols=["Mcap USD ($B)"],
        pct_cols=["YTD %", "1M %", "5D %", "1D %", "vs SOX YTD"],
        pct2_cols=["FCF Yld"],
        mult_cols=["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"],
        text_cols=["Name", "Layers"],
        height=620,
        column_labels={
            **i18n.common_cols(),
            "vs SOX YTD": i18n.t("ai.cov.col.vs_sox"),
        },
        index_label=i18n.t("common.col.ticker"),
    )


# --- Region tabs (AI markets: US / JP / KR / CN + All) ---
regions = ["US", "JP", "KR", "CN", "All"]
tabs = st.tabs([f"{r} ({sum(merged['region'] == r) if r != 'All' else len(merged)})" for r in regions])

for tab, region in zip(tabs, regions):
    with tab:
        if region == "All":
            render_region(merged)
        else:
            render_region(merged[merged["region"] == region])

# --- Onboarding ---
with st.expander(i18n.t("ai.cov.onboarding.title")):
    st.markdown(i18n.t("ai.cov.onboarding.body"))

st.divider()
st.caption(i18n.t("ai.cov.caption.source", n=len(merged)))
