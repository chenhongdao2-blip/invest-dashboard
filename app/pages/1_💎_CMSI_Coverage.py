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
    # disp["Name (EN)"] = df["name_en"].fillna("—") # Cull redundant name
    # disp["Region"] = df["region"] # Redundant in tabs
    # disp["Tier"] = df.get("mcap_tier", pd.Series(index=df.index)).fillna("—")
    disp["Mcap USD"] = df["market_cap_usd"].apply(fmt.fmt_money_b)
    disp["YTD %"] = df["ytd_%"].apply(fmt.fmt_pct)
    disp["1M %"] = df["1m_%"].apply(fmt.fmt_pct)
    disp["5D %"] = df["5d_%"].apply(fmt.fmt_pct)
    disp["1D %"] = df["1d_%"].apply(fmt.fmt_pct)
    disp["vs HSI YTD"] = df["vs_hsi_ytd"].apply(fmt.fmt_pct)        # m8 audit
    disp["Trail P/E"] = df["trailing_pe"].apply(fmt.fmt_ratio)
    disp["Fwd P/E"] = df["forward_pe"].apply(fmt.fmt_ratio)
    disp["EV/EBITDA"] = df["ev_ebitda"].apply(fmt.fmt_ratio)
    disp["FCF Yld"] = df["fcf_yield"].apply(fmt.fmt_pct_decimal)
    disp["P/B"] = df["pb"].apply(fmt.fmt_ratio)
    # m8 audit: sell-side consensus columns
    disp["TP Upside"] = df["tp_upside_%"].apply(fmt.fmt_pct)
    disp["Reco"] = df["recommendation_mean"].apply(_reco_label)
    disp["N analysts"] = df["n_analysts"].apply(
        lambda v: str(int(v)) if pd.notna(v) else "—"
    )
    disp["Cross"] = df["Cross-Sector"]
    disp.index.name = "Ticker"

    pct_cols = ["YTD %", "1M %", "5D %", "1D %", "vs HSI YTD", "TP Upside"]
    mult_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"]

    styler = disp.style
    pct_num_map = {
        "YTD %": "ytd_%", "1M %": "1m_%", "5D %": "5d_%", "1D %": "1d_%",
        "vs HSI YTD": "vs_hsi_ytd", "TP Upside": "tp_upside_%",
    }
    for col in pct_cols:
        num = df[pct_num_map[col]]
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

# --- Onboarding ---
ui.onboarding_expander("Coverage Page", """
**Official Coverage List**: 招商证券 (CMSI) Healthcare 覆盖名单，包含港股、美股及 A 股。

**Columns**:
- **Cross**: 跨板块标签。如果一个标的同时属于多个 Sector Universe（如信达属于 Biotech + Pharma），此处会显示对应 emoji。
- **Mcap USD**: 统一换算为美元的市值，方便跨地域比较。
- **Fwd P/E**: yfinance 提供的 12M forward P/E。
- **FCF Yield**: 自由现金流收益率。越高通常代表现金流越稳健。

**Sorting**: 默认按市值 (Mcap) 降序排列。
""")

st.divider()
st.caption(
    "🧬 = Biotech · 💊 = Pharma · 🤖 = HC+AI · ⚕️ = Medtech · 🏥 = Hospital Care · 🩺 = Managed Care · 🧪 = CXO. "
    "Cross-sector tags 表示 ticker 同时存在于其他 sector universe（dedup 自动）。"
)
st.caption(
    f"📊 Cover list source: `config/universes/cmsi_coverage_hc.yml` ({len(merged)} tickers). "
    "默认按 market cap 降序，名字优先中文 (M10 audit)。"
)
