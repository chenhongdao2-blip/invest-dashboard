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

    # BUGFIX: Build NUMERIC DataFrame (not pre-formatted strings) so column sort
    # works correctly. Streamlit column_config handles display format; Styler.apply
    # still works for background_gradient on the numeric values.
    disp = pd.DataFrame(index=df.index)
    disp["BBG"] = df["BBG"]
    disp["Name (CN)"] = df["name_cn"].fillna("")
    disp["Mcap USD ($B)"] = df["market_cap_usd"] / 1e9              # numeric, B
    disp["YTD %"] = df["ytd_%"]
    disp["1M %"] = df["1m_%"]
    disp["5D %"] = df["5d_%"]
    disp["1D %"] = df["1d_%"]
    disp["vs HSI YTD"] = df["vs_hsi_ytd"]
    disp["Trail P/E"] = df["trailing_pe"]
    disp["Fwd P/E"] = df["forward_pe"]
    disp["EV/EBITDA"] = df["ev_ebitda"]
    disp["FCF Yld"] = df["fcf_yield"]                               # decimal e.g. 0.025
    disp["P/B"] = df["pb"]
    disp["TP Upside %"] = df["tp_upside_%"]                         # m8
    disp["Reco"] = df["recommendation_mean"].apply(_reco_label)
    disp["N analysts"] = df["n_analysts"]                           # int
    disp["Cross"] = df["Cross-Sector"]
    disp.index.name = "Ticker"

    # Background gradient via Styler (works on numeric)
    pct_cols = ["YTD %", "1M %", "5D %", "1D %", "vs HSI YTD", "TP Upside %"]
    mult_low_good = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"]

    styler = disp.style
    for col in pct_cols:
        styler = styler.apply(
            lambda s: fmt.background_gradient_diverging(s),
            subset=[col],
        )
    for col in mult_low_good:
        styler = styler.apply(
            lambda s: fmt.background_gradient_low_good(s),
            subset=[col],
        )
    styler = styler.apply(
        lambda s: fmt.background_gradient_low_good(s, low_color="#dc2626", high_color="#16a34a"),
        subset=["FCF Yld"],
    )

    # column_config: display format (preserves numeric sort)
    col_cfg = {
        "Mcap USD ($B)": st.column_config.NumberColumn(format="$%.1fB"),
        "YTD %": st.column_config.NumberColumn(format="%+.2f%%"),
        "1M %": st.column_config.NumberColumn(format="%+.2f%%"),
        "5D %": st.column_config.NumberColumn(format="%+.2f%%"),
        "1D %": st.column_config.NumberColumn(format="%+.2f%%"),
        "vs HSI YTD": st.column_config.NumberColumn(format="%+.2f%%"),
        "Trail P/E": st.column_config.NumberColumn(format="%.1fx"),
        "Fwd P/E": st.column_config.NumberColumn(format="%.1fx"),
        "EV/EBITDA": st.column_config.NumberColumn(format="%.1fx"),
        "FCF Yld": st.column_config.NumberColumn(format="%+.2%"),    # 0.025 → +2.5%
        "P/B": st.column_config.NumberColumn(format="%.1fx"),
        "TP Upside %": st.column_config.NumberColumn(format="%+.1f%%"),
        "N analysts": st.column_config.NumberColumn(format="%d"),
    }

    # 17 columns require narrow widths to fit Streamlit canvas at 1050px viewport.
    # Sort works because dataframe is numeric (not pre-formatted strings).
    col_cfg = {
        "BBG": st.column_config.TextColumn(width="small"),
        "Name (CN)": st.column_config.TextColumn(width="small"),
        "Mcap USD ($B)": st.column_config.NumberColumn(format="$%.1fB", width="small"),
        "YTD %": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "1M %": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "5D %": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "1D %": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "vs HSI YTD": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "Trail P/E": st.column_config.NumberColumn(format="%.1fx", width="small"),
        "Fwd P/E": st.column_config.NumberColumn(format="%.1fx", width="small"),
        "EV/EBITDA": st.column_config.NumberColumn(format="%.1fx", width="small"),
        "FCF Yld": st.column_config.NumberColumn(format="%+.2%", width="small"),
        "P/B": st.column_config.NumberColumn(format="%.1fx", width="small"),
        "TP Upside %": st.column_config.NumberColumn(format="%+.1f%%", width="small"),
        "Reco": st.column_config.TextColumn(width="small"),
        "N analysts": st.column_config.NumberColumn(format="%d", width="small"),
        "Cross": st.column_config.TextColumn(width="small"),
    }
    st.dataframe(styler, use_container_width=True, height=560, column_config=col_cfg)


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
