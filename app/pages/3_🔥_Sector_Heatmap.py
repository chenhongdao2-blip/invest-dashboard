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
from lib import ui
from lib import theme

st.set_page_config(page_title="Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"


@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)


cfg = load_domain_cfg()

theme.page_header("05 / 07", "Sector Heatmap")
st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")

# --- Sidebar global search + filter ---
with st.sidebar:
    ui.sidebar_search(key_prefix="heatmap")
    st.divider()
    st.subheader("Filter")
    min_mcap_b = st.slider(
        "Min market cap (USD B)", 0.0, 50.0, 0.0, 0.5,
        help="过滤掉小市值标的避免均值扭曲"
    )
    sort_col = st.selectbox(
        "Sort by",
        ["Mcap USD", "YTD %", "1M %", "Trail P/E", "Fwd P/E"],
        index=0,
        help="默认按市值降序"
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

    # --- Build NUMERIC display DataFrame (sort-bug fix) ---
    # Sort bug fix: keep numeric, let column_config render the format, so the
    # Streamlit header click sorts numerically instead of lexicographically.
    # Note: BBG column dropped — duplicates the ticker index. Keep ticker as the
    # row identifier, surface Name (CN > EN > ticker) as the human-readable column.
    disp = pd.DataFrame(index=merged.index)
    disp["Name"] = merged["Name"].fillna(merged.index.to_series())
    disp["Mcap USD ($B)"] = merged["market_cap_usd"] / 1e9
    disp["YTD %"] = merged["ytd_%"]
    disp["1M %"] = merged["1m_%"]
    disp["5D %"] = merged["5d_%"]
    disp["1D %"] = merged["1d_%"]
    disp["Trail P/E"] = merged["trailing_pe"]
    disp["Fwd P/E"] = merged["forward_pe"]
    disp["EV/EBITDA"] = merged["ev_ebitda"]
    disp["EV/Sales"] = merged["ev_sales"]
    disp["FCF Yld"] = merged["fcf_yield"]
    disp["P/B"] = merged["pb"]
    disp.index.name = "Ticker"

    ui.render_styled_table(
        disp,
        pct_cols=["YTD %", "1M %", "5D %", "1D %"],
        pct_decimal_cols=["FCF Yld"],
        mult_cols=["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "P/B"],
        money_b_cols=["Mcap USD ($B)"],
        text_cols=["Name"],
        column_widths={"Name": "medium"},
        height=540,
    )

    pct_num_map = {"YTD %": "ytd_%", "1M %": "1m_%", "5D %": "5d_%", "1D %": "1d_%"}
    mult_num_map = {"Trail P/E": "trailing_pe", "Fwd P/E": "forward_pe",
                    "EV/EBITDA": "ev_ebitda", "EV/Sales": "ev_sales", "P/B": "pb",
                    "FCF Yld": "fcf_yield"}

    # --- Sector aggregates (M11 audit: by cap_tier optional) ---
    with st.expander(f"{sec['name']} aggregates (mean / median / weighted)"):
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
        _agg = pd.DataFrame.from_dict(agg_rows, orient="index")
        ui.render_html_table(
            _agg,
            text_cols=list(_agg.columns),
            column_help={},
            index_label="Metric",
            height=460,
        )


# --- M8 audit: render tabs for piano-key navigation ---
sector_tabs = st.tabs([f"{sec['name']} ({len(db.sector_tickers('healthcare', sec['id']))})"
                       for sec in cfg["sectors"]])

for tab, sec in zip(sector_tabs, cfg["sectors"]):
    with tab:
        render_sector(sec)

st.divider()
st.caption(
    "**Color legend**: Returns 绿涨红跌. Multiples (P/E, EV/EBITDA) 绿低红高 (cheap=green). "
    "FCF Yield 绿高红低. "
    "Ticker shown in **Bloomberg style** (2269 HK / 4587 JP / 300760 CH). "
    f"Latest data: **{db.latest_snapshot_date()}**"
)
st.caption(
    "Sort/filter via sidebar. Min market cap filter is useful when small-cap stocks "
    "distort sector means (e.g., 4587 JP $904M vs GILD $166B)."
)

# --- Onboarding ---
ui.onboarding_expander("Sector Heatmap", """
**Multiples & Returns**: 
- **Color Legend**: 收益率（YTD/1M等）绿涨红跌；估值倍数（P/E, EV/EBITDA）绿低红高（代表便宜）；FCF Yield 绿高红低。
- **Tabs**: 通过上方选项卡快速切换 7 个不同的细分板块。

**Filters**:
- **Min Market Cap**: 过滤掉极小市值的标的（如某些市值不到 B 的 Biotech），避免它们极端的估值拉低或拉高板块整体均值。

**Aggregates**:
- 展开下方的 "Sector aggregates" 可以看到该板块所有标的的平均值 (Mean) 和中位数 (Median)。
""")
