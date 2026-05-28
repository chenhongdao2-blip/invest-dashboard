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

from lib import db
from lib import format as fmt

st.set_page_config(
    page_title="CMSI Coverage · invest-dashboard",
    page_icon="💎",
    layout="wide",
)

# --- Sidebar global search ---
with st.sidebar:
    st.subheader("🔍 Find ticker")
    pick = st.selectbox(
        "Jump to ticker drill",
        options=[""] + sorted(db.all_tickers()),
        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
        key="cmsi_search",
    )
    if pick:
        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")

st.title("💎 CMSI Healthcare Coverage")
st.caption("28 ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: " + (db.latest_snapshot_date() or "—"))


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
def cross_membership(_tickers: tuple[str, ...]) -> dict[str, list[str]]:
    placeholders = ",".join("?" * len(_tickers))
    df = db.query(
        f"SELECT ticker, sector FROM universe_member "
        f"WHERE ticker IN ({placeholders}) AND sector != '_coverage' "
        f"ORDER BY ticker, sector",
        tuple(_tickers),
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
              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
        if c in mults.columns:
            merged[c] = mults[c]

# Cross-sector tags: convert to icons
def _cross_tag(ticker: str) -> str:
    sectors = cross.get(ticker, [])
    if not sectors:
        return ""
    # 简短 emoji mapping
    icons = {
        "biotech": "🧬", "pharma": "💊", "hc_ai": "🤖",
        "medtech": "⚕️", "hospital_care": "🏥",
        "managed_care": "🩺", "cxo": "🧪",
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

    # Build display string DataFrame (M7 audit pattern)
    disp = pd.DataFrame(index=df.index)
    disp["BBG"] = df["BBG"]
    disp["Name (CN)"] = df["name_cn"].fillna("—")
    disp["Name (EN)"] = df["name_en"].fillna("—")
    disp["Region"] = df["region"]
    disp["Tier"] = df.get("mcap_tier", pd.Series(index=df.index)).fillna("—")
    disp["Cross"] = df["Cross-Sector"]
    disp["Mcap USD"] = df["market_cap_usd"].apply(fmt.fmt_money_b)
    disp["YTD %"] = df["ytd_%"].apply(fmt.fmt_pct)
    disp["1M %"] = df["1m_%"].apply(fmt.fmt_pct)
    disp["5D %"] = df["5d_%"].apply(fmt.fmt_pct)
    disp["1D %"] = df["1d_%"].apply(fmt.fmt_pct)
    disp["Trail P/E"] = df["trailing_pe"].apply(fmt.fmt_ratio)
    disp["Fwd P/E"] = df["forward_pe"].apply(fmt.fmt_ratio)
    disp["EV/EBITDA"] = df["ev_ebitda"].apply(fmt.fmt_ratio)
    disp["FCF Yld"] = df["fcf_yield"].apply(fmt.fmt_pct_decimal)
    disp["P/B"] = df["pb"].apply(fmt.fmt_ratio)
    disp.index.name = "Ticker"

    pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
    mult_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"]

    styler = disp.style
    for col in pct_cols:
        num = df["ytd_%" if "YTD" in col else ("1m_%" if "1M" in col else ("5d_%" if "5D" in col else "1d_%"))]
        styler = styler.apply(
            lambda _s, n=num: fmt.background_gradient_diverging(n),
            subset=[col],
        )
    for col in mult_cols:
        num_field = {"Trail P/E": "trailing_pe", "Fwd P/E": "forward_pe",
                     "EV/EBITDA": "ev_ebitda", "P/B": "pb"}[col]
        styler = styler.apply(
            lambda _s, n=df[num_field]: fmt.background_gradient_low_good(n),
            subset=[col],
        )
    styler = styler.apply(
        lambda _s: fmt.background_gradient_low_good(df["fcf_yield"], low_color="#dc2626", high_color="#16a34a"),
        subset=["FCF Yld"],
    )

    st.dataframe(styler, use_container_width=True, height=560)


for tab, region in zip(tabs, regions):
    with tab:
        if region == "All":
            render_region(merged)
        else:
            render_region(merged[merged["region"] == region])

st.divider()
st.caption(
    "🧬 = Biotech · 💊 = Pharma · 🤖 = HC+AI · ⚕️ = Medtech · 🏥 = Hospital Care · 🩺 = Managed Care · 🧪 = CXO. "
    "Cross-sector tags 表示 ticker 同时存在于其他 sector universe（dedup 自动）。"
)
st.caption(
    f"📊 Cover list source: `config/universes/cmsi_coverage_hc.yml` ({len(merged)} tickers). "
    "默认按 market cap 降序，名字优先中文 (M10 audit)。"
)
