"""Sector Heatmap — multiples + returns per sector with color gradient.

Audit fixes applied:
- M7: pre-format string DataFrame for display; Styler computes background from numeric.
- M8: st.tabs instead of dropdown (analyst can piano-key through 7 sectors).
- M10: default sort by market cap desc; name_cn priority (中文卖方习惯).
- M1: use USD-converted close series for fair cross-region return comparison.
- M11: mcap_tier shown as badge; sidebar min-mcap filter.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from lib import db
from lib import format as fmt

st.set_page_config(page_title="Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"


@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)


cfg = load_domain_cfg()

st.title("🔥 Sector Heatmap")
st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")

# --- Sidebar filter (M11 audit) ---
with st.sidebar:
    st.subheader("Filter")
    min_mcap_b = st.slider(
        "Min market cap (USD B)", 0.0, 50.0, 0.0, 0.5,
        help="过滤掉小市值标的避免均值扭曲（GLM audit M11: 4587.T $904M 拉低 biotech 均值）"
    )
    sort_col = st.selectbox(
        "Sort by",
        ["Mcap USD", "YTD %", "1M %", "Trail P/E", "Fwd P/E"],
        index=0,
        help="默认按市值降序（M10 audit: 中文卖方习惯）"
    )


def render_sector(sec: dict) -> None:
    uni = db.sector_tickers("healthcare", sec["id"])
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        st.warning(f"No tickers in sector {sec['name']}")
        return

    # M1: use USD-converted close series
    closes = db.get_close_series_usd(tickers)
    rets = db.compute_returns(closes)
    mults = db.latest_multiples(tickers)
    name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
    region_map = uni.set_index("ticker")["region"].to_dict()

    # --- Merge numeric DataFrame (for gradient calc) ---
    merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    if not mults.empty:
        for col in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
                    "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
            if col in mults.columns:
                merged[col] = mults[col]
    merged["Name"] = pd.Series(name_map).reindex(merged.index)
    merged["Region"] = pd.Series(region_map).reindex(merged.index)
    merged["Ticker_bbg"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]   # n2 audit

    # M11 audit: filter by min_mcap (in B)
    if min_mcap_b > 0:
        mcap_filter = merged["market_cap_usd"] >= (min_mcap_b * 1e9)
        merged = merged[mcap_filter]

    # M10 audit: default sort by market cap desc
    sort_map = {
        "Mcap USD": "market_cap_usd",
        "YTD %": "ytd_%",
        "1M %": "1m_%",
        "Trail P/E": "trailing_pe",
        "Fwd P/E": "forward_pe",
    }
    sort_field = sort_map.get(sort_col, "market_cap_usd")
    ascending = "P/E" in sort_col   # cheaper first for P/E
    if sort_field in merged.columns:
        merged = merged.sort_values(sort_field, ascending=ascending, na_position="last")

    if merged.empty:
        st.info(f"No tickers in {sec['name']} after min-mcap filter (>= ${min_mcap_b:.1f}B)")
        return

    # --- Build STRING display DataFrame (M7 audit) ---
    display_str = pd.DataFrame(index=merged.index)
    display_str["BBG"] = merged["Ticker_bbg"]
    display_str["Name"] = merged["Name"].fillna(merged.index.to_series())
    display_str["Tier"] = merged.get("mcap_tier", pd.Series(index=merged.index)).fillna("—")
    display_str["Mcap USD"] = merged["market_cap_usd"].apply(fmt.fmt_money_b)
    display_str["YTD %"] = merged["ytd_%"].apply(fmt.fmt_pct)
    display_str["1M %"] = merged["1m_%"].apply(fmt.fmt_pct)
    display_str["5D %"] = merged["5d_%"].apply(fmt.fmt_pct)
    display_str["1D %"] = merged["1d_%"].apply(fmt.fmt_pct)
    display_str["Trail P/E"] = merged["trailing_pe"].apply(fmt.fmt_ratio)
    display_str["Fwd P/E"] = merged["forward_pe"].apply(fmt.fmt_ratio)
    display_str["EV/EBITDA"] = merged["ev_ebitda"].apply(fmt.fmt_ratio)
    display_str["EV/Sales"] = merged["ev_sales"].apply(fmt.fmt_ratio)
    display_str["FCF Yld"] = merged["fcf_yield"].apply(fmt.fmt_pct_decimal)
    display_str["P/B"] = merged["pb"].apply(fmt.fmt_ratio)
    display_str.index.name = "Ticker"

    # --- Apply colors via Styler using NUMERIC values from `merged` ---
    pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
    low_good_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "P/B"]
    high_good_cols = ["FCF Yld"]

    pct_num_map = {"YTD %": "ytd_%", "1M %": "1m_%", "5D %": "5d_%", "1D %": "1d_%"}
    mult_num_map = {"Trail P/E": "trailing_pe", "Fwd P/E": "forward_pe",
                    "EV/EBITDA": "ev_ebitda", "EV/Sales": "ev_sales", "P/B": "pb",
                    "FCF Yld": "fcf_yield"}

    styler = display_str.style
    for col in pct_cols:
        num_series = merged[pct_num_map[col]]
        styler = styler.apply(
            lambda _s, n=num_series: fmt.background_gradient_diverging(n),
            subset=[col],
        )
    for col in low_good_cols:
        num_series = merged[mult_num_map[col]]
        styler = styler.apply(
            lambda _s, n=num_series: fmt.background_gradient_low_good(n),
            subset=[col],
        )
    for col in high_good_cols:
        num_series = merged[mult_num_map[col]]
        styler = styler.apply(
            lambda _s, n=num_series: fmt.background_gradient_low_good(
                n, low_color="#dc2626", high_color="#16a34a"
            ),
            subset=[col],
        )

    st.dataframe(styler, use_container_width=True, height=540)

    # --- Sector aggregates (M11 audit: by cap_tier optional) ---
    with st.expander(f"📊 {sec['name']} aggregates (mean / median / weighted)"):
        agg_rows: dict[str, dict] = {}
        for label, num_col in pct_num_map.items():
            s = merged[num_col].dropna()
            agg_rows[label] = {
                "Mean": fmt.fmt_pct(s.mean() if not s.empty else None),
                "Median": fmt.fmt_pct(s.median() if not s.empty else None),
                "Min": fmt.fmt_pct(s.min() if not s.empty else None),
                "Max": fmt.fmt_pct(s.max() if not s.empty else None),
            }
        for label, num_col in mult_num_map.items():
            s = merged[num_col].dropna()
            fmt_fn = fmt.fmt_pct_decimal if label == "FCF Yld" else fmt.fmt_ratio
            agg_rows[label] = {
                "Mean": fmt_fn(s.mean() if not s.empty else None),
                "Median": fmt_fn(s.median() if not s.empty else None),
                "Min": fmt_fn(s.min() if not s.empty else None),
                "Max": fmt_fn(s.max() if not s.empty else None),
            }
        st.dataframe(pd.DataFrame.from_dict(agg_rows, orient="index"),
                     use_container_width=True)


# --- M8 audit: render tabs for piano-key navigation ---
sector_tabs = st.tabs([f"{sec['name']} ({len(db.sector_tickers('healthcare', sec['id']))})"
                       for sec in cfg["sectors"]])

for tab, sec in zip(sector_tabs, cfg["sectors"]):
    with tab:
        render_sector(sec)

st.divider()
st.caption(
    "🎨 **Color legend**: Returns 绿涨红跌. Multiples (P/E, EV/EBITDA) 绿低红高 (cheap=green). "
    "FCF Yield 绿高红低. "
    "Ticker shown in **Bloomberg style** (2269 HK / 4587 JP / 300760 CH). "
    f"Latest data: **{db.latest_snapshot_date()}**"
)
st.caption(
    "Sort/filter via sidebar. Min market cap filter is useful when small-cap stocks "
    "distort sector means (e.g., 4587 JP $904M vs GILD $166B)."
)
