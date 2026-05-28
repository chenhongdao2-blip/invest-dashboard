"""Sector Heatmap — multiples + returns per sector with color gradient."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yaml
from pathlib import Path

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

# --- Sector picker ---
sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
default_idx = next((i for i, s in enumerate(sector_options) if s[0] == "biotech"), 0)
selected = st.selectbox(
    "Pick sector",
    options=[s[0] for s in sector_options],
    format_func=lambda x: next(s[1] for s in sector_options if s[0] == x),
    index=default_idx,
)

# --- Load ---
uni = db.sector_tickers("healthcare", selected)
tickers = tuple(uni["ticker"].tolist())
if not tickers:
    st.warning("No tickers in this sector — check config/universes/")
    st.stop()

closes = db.get_close_series(tickers)
rets = db.compute_returns(closes)
mults = db.latest_multiples(tickers)
name_map = db.ticker_to_name()

# Merge: returns + multiples
merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
merged["Name"] = pd.Series(name_map).reindex(merged.index)
merged = merged.join(mults[["market_cap_usd", "trailing_pe", "forward_pe",
                             "ev_ebitda", "ev_sales", "fcf_yield", "pb"]],
                     how="left")

# Region annotation
region_map = uni.set_index("ticker")["region"].to_dict()
merged["Region"] = pd.Series(region_map).reindex(merged.index)

# Reorder columns
display = merged[["Name", "Region", "market_cap_usd",
                  "ytd_%", "1m_%", "5d_%", "1d_%",
                  "trailing_pe", "forward_pe", "ev_ebitda", "ev_sales",
                  "fcf_yield", "pb"]].copy()
display.columns = ["Name", "Region", "Mcap USD",
                    "YTD %", "1M %", "5D %", "1D %",
                    "Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales",
                    "FCF Yld", "P/B"]
display.index.name = "Ticker"

# Sort by YTD desc by default
display = display.sort_values("YTD %", ascending=False, na_position="last")

# --- Heatmap styling ---
pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
low_good_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "P/B"]
high_good_cols = ["FCF Yld"]

styler = display.style.format({
    "Mcap USD": fmt.fmt_money_b,
    "YTD %": fmt.fmt_pct,
    "1M %": fmt.fmt_pct,
    "5D %": fmt.fmt_pct,
    "1D %": fmt.fmt_pct,
    "Trail P/E": fmt.fmt_ratio,
    "Fwd P/E": fmt.fmt_ratio,
    "EV/EBITDA": fmt.fmt_ratio,
    "EV/Sales": fmt.fmt_ratio,
    "FCF Yld": fmt.fmt_pct_decimal,
    "P/B": fmt.fmt_ratio,
}, na_rep="—")

# Color gradient for return columns
styler = styler.apply(fmt.background_gradient_diverging, subset=pct_cols)

# Lower-is-better for multiples (P/E etc.)
for col in low_good_cols:
    styler = styler.apply(fmt.background_gradient_low_good, subset=[col])

# Higher-is-better for FCF Yield (reverse colors)
for col in high_good_cols:
    styler = styler.apply(
        lambda s: fmt.background_gradient_low_good(s, low_color="#dc2626", high_color="#16a34a"),
        subset=[col],
    )

st.dataframe(styler, use_container_width=True, height=600)

# --- Sector aggregates ---
st.subheader("📊 Sector aggregates")

agg_rows = {}
for col in ["YTD %", "1M %", "5D %", "1D %", "Trail P/E", "Fwd P/E",
            "EV/EBITDA", "EV/Sales", "FCF Yld", "P/B"]:
    s = display[col]
    s_clean = s.dropna()
    agg_rows[col] = {
        "Mean": s_clean.mean() if not s_clean.empty else None,
        "Median": s_clean.median() if not s_clean.empty else None,
        "Min": s_clean.min() if not s_clean.empty else None,
        "Max": s_clean.max() if not s_clean.empty else None,
    }
# Mkt-cap weighted average for multiples
mcap_w = display["Mcap USD"].fillna(0)
if mcap_w.sum() > 0:
    weights = mcap_w / mcap_w.sum()
    for col in ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "FCF Yld", "P/B"]:
        valid = display[col].notna()
        if valid.any():
            w = weights[valid] / weights[valid].sum()
            wm = (display.loc[valid, col] * w).sum()
            agg_rows[col]["Wgt avg"] = wm

agg = pd.DataFrame(agg_rows).T
agg = agg[["Mean", "Median", "Min", "Max"] + (["Wgt avg"] if "Wgt avg" in agg.columns else [])]

def _fmt_cell(col_label: str, v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if "%" in col_label:
        return f"{v:+.2f}%"
    if col_label in ["FCF Yld"]:
        return f"{v * 100:+.2f}%"
    return f"{v:.1f}x"

# Build fresh string DataFrame to avoid pandas 2.x dtype coercion error
agg_str = {
    idx: {col: _fmt_cell(idx, agg.at[idx, col]) for col in agg.columns}
    for idx in agg.index
}
agg_fmt = pd.DataFrame.from_dict(agg_str, orient="index")

st.dataframe(agg_fmt, use_container_width=True)

# --- caveats ---
st.caption(
    "🎨 **Color legend**: Returns (YTD/1M/5D/1D) green=up, red=down. "
    "Multiples (P/E, EV/EBITDA): green=lower=cheaper, red=higher=expensive. "
    "FCF Yield: green=higher=better."
)
st.caption(
    f"Sector: **{next(s['name'] for s in cfg['sectors'] if s['id'] == selected)}** "
    f"({len(display)} tickers) · Latest data: {db.latest_snapshot_date()}"
)
