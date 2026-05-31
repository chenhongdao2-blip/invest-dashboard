"""Theme preview app — sidebar picker for 3 candidate styles.

Run:
    streamlit run demos/theme_preview/app.py --server.port 8502

Visit:
    http://localhost:8502

Notes:
- This is a standalone demo. It does NOT touch the real app under app/.
- Data is mocked; the goal is pure visual / typographic comparison.
- After picking a theme, we'll port that theme dict into app/lib/theme.py
  and apply it across the real pages.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from themes import THEMES

st.set_page_config(
    page_title="Theme Preview · invest-dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar: theme picker ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Theme picker")
    choice = st.radio(
        "Pick a style",
        options=list(THEMES.keys()),
        format_func=lambda k: f"{k} · {THEMES[k]['name']}",
        index=0,
        label_visibility="collapsed",
    )
    theme = THEMES[choice]
    st.caption(theme["tagline"])
    swatch_html = " ".join(
        f'<span style="display:inline-block;width:22px;height:22px;background:{c};'
        f'border-radius:4px;margin-right:4px;border:1px solid rgba(255,255,255,0.1)"></span>'
        for c in theme["swatches"]
    )
    st.markdown(swatch_html, unsafe_allow_html=True)
    st.markdown("---")
    st.caption(
        "Switch themes via radio above. Backgrounds, fonts, tables, KPI strip, "
        "and Plotly chart will re-render with the selected theme."
    )

# ── Inject the chosen theme's CSS ────────────────────────────────────────
st.markdown(f"<style>{theme['css']}</style>", unsafe_allow_html=True)

# ── Mock data (mirrors the shape of the real home page) ──────────────────
benchmarks = pd.DataFrame([
    {"Name": "Hang Seng Index",   "Last": 18420.13, "1D %": -0.42, "5D %":  1.20, "1M %":  3.15, "YTD %":  8.42},
    {"Name": "HSCEI (H-shares)",  "Last":  6582.04, "1D %": -0.28, "5D %":  1.55, "1M %":  4.20, "YTD %": 10.18},
    {"Name": "S&P 500",           "Last":  5328.10, "1D %":  0.31, "5D %":  0.85, "1M %":  2.40, "YTD %": 11.05},
    {"Name": "NASDAQ Composite",  "Last": 16920.80, "1D %":  0.52, "5D %":  1.20, "1M %":  3.65, "YTD %": 12.80},
    {"Name": "XBI (US Biotech)",  "Last":    92.45, "1D %": -1.15, "5D %": -2.40, "1M %": -0.85, "YTD %": -4.20},
])

gainers = pd.DataFrame([
    {"Ticker": "WUXI.HK",  "Name": "WuXi Biologics",   "Sector": "Biotech CRO",  "Last": 22.40, "1D %":  6.15},
    {"Ticker": "1801.HK",  "Name": "Innovent Biologic","Sector": "Innovative Rx","Last": 48.90, "1D %":  4.82},
    {"Ticker": "2269.HK",  "Name": "WuXi Bio",          "Sector": "Biotech CRO",  "Last": 21.80, "1D %":  4.10},
    {"Ticker": "BNTX",     "Name": "BioNTech",          "Sector": "mRNA",         "Last":102.15, "1D %":  3.95},
    {"Ticker": "1093.HK",  "Name": "CSPC Pharma",       "Sector": "Generics",     "Last":  6.45, "1D %":  3.20},
])

drags = pd.DataFrame([
    {"Ticker": "MRNA",    "Name": "Moderna",          "Sector": "mRNA",          "Last":108.42, "1D %": -5.20},
    {"Ticker": "BGNE",    "Name": "BeiGene",          "Sector": "Innovative Rx", "Last":175.80, "1D %": -3.85},
    {"Ticker": "3692.HK", "Name": "Hansoh Pharma",    "Sector": "Innovative Rx", "Last": 18.90, "1D %": -3.10},
    {"Ticker": "1801.HK", "Name": "Sino Biopharm",    "Sector": "Generics",      "Last":  3.18, "1D %": -2.65},
    {"Ticker": "VRTX",    "Name": "Vertex Pharma",    "Sector": "Specialty Rx",  "Last":462.30, "1D %": -2.20},
])


def render_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
    """Render df as themed HTML table — full CSS control over bg / fonts / colors.

    st.dataframe is canvas-rendered so CSS can't reach its internals. HTML tables
    give us 100% theme control.
    """
    num_cols = num_cols or []
    up, down = theme["accent_up"], theme["accent_down"]

    def fmt_cell(col: str, val) -> str:
        if pd.isna(val):
            return '<td class="num">—</td>'
        if col in pct_cols:
            color = up if val >= 0 else down
            sign = theme["up_symbol"] if val >= 0 else theme["down_symbol"]
            return f'<td class="num" style="color:{color};font-weight:500">{sign} {val:+.2f}%</td>'
        if col in num_cols:
            return f'<td class="num">{val:,.2f}</td>'
        return f"<td>{val}</td>"

    head_cells = "".join(
        f'<th class="num">{c}</th>' if (c in pct_cols or c in num_cols) else f"<th>{c}</th>"
        for c in df.columns
    )
    body_rows = "".join(
        "<tr>" + "".join(fmt_cell(c, row[c]) for c in df.columns) + "</tr>"
        for _, row in df.iterrows()
    )
    html = (
        f'<div class="themed-table-wrap"><table class="themed-table">'
        f"<thead><tr>{head_cells}</tr></thead>"
        f"<tbody>{body_rows}</tbody>"
        f"</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ── Page content ─────────────────────────────────────────────────────────
st.title("Multi-Domain Investment Dashboard")
st.caption(
    f"Sell-side healthcare coverage  ·  Theme preview: **{choice} · {theme['name']}**  ·  "
    "v1 mock data  ·  switch theme from sidebar"
)

# KPI strip
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest snapshot", "2026-05-28")
c2.metric("Last fetch (UTC)", "2026-05-28 14:32")
c3.metric("Universe tickers", "247", delta="+3 this week")
c4.metric("Coverage memos", "31", delta="+2")

st.divider()

# Benchmarks
st.header("Benchmarks")
st.caption("Major indices and sector ETFs · live yfinance pull")
render_table(benchmarks, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])

# Top movers
st.header("Today's Top Movers")
st.caption("Across all 7 healthcare sectors · ranked by 1-day return")

col_l, col_r = st.columns(2)
with col_l:
    st.subheader(f"{theme['up_symbol']}  Top 5 Gainers")
    render_table(gainers, pct_cols=["1D %"], num_cols=["Last"])
with col_r:
    st.subheader(f"{theme['down_symbol']}  Top 5 Drags")
    render_table(drags, pct_cols=["1D %"], num_cols=["Last"])

st.divider()

# Chart
st.header("XBI · 60-day price")
st.caption("US biotech sector ETF · normalized")

rng = np.random.default_rng(7)
days = pd.date_range(end=pd.Timestamp.today(), periods=60, freq="B")
price = 100 + np.cumsum(rng.normal(0, 1.4, len(days)))
ma20 = pd.Series(price).rolling(20).mean()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=days, y=price, name="XBI", mode="lines",
    line=dict(width=2.2),
))
fig.add_trace(go.Scatter(
    x=days, y=ma20, name="MA(20)", mode="lines",
    line=dict(width=1.4, dash="dot"),
))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(orientation="h", y=1.08, x=0),
    **theme["plotly_template"],
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    f"This is a standalone preview. Pick a theme, then I'll port `{choice}` "
    "into `app/lib/theme.py` and apply it to the real pages."
)
