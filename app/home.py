"""Home — landing page rendered by the st.navigation hub.

The hub (streamlit_app.py) handles page registration + grouping. This file
just renders the Home dashboard content. Keep its set_page_config so that
when this page is active the browser tab title / icon match.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import charts
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n
from lib import heatmap as hm
from lib import freshness

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Unified sidebar search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="home")
    freshness.render_freshness_panel()

# --- Language ---
i18n.init_lang()
i18n.render_lang_toggle()

# --- Data ---
latest = db.latest_snapshot_date()
fetch_utc = db.last_fetch_utc()

# --- Header (with meta: snapshot date + fetch time) ---
theme.page_header(
    i18n.t("home.title"),
    meta=f"{latest} · {fetch_utc[:16] if fetch_utc else '—'}",
)

# Home-only CSS: make the domain expanders (S&P sectors / Healthcare / AI) read as
# editorial section headers (red bar + 21px + ink top rule) while staying click-to-
# collapse. Injected here (NOT in the global theme) so other pages' expanders
# (Ticker Drill onboarding etc.) keep the compact default look.
st.markdown(
    f"""<style>
    [data-testid="stExpander"] {{
      border: none !important; border-top: 1px solid {theme.INK} !important;
      border-radius: 0 !important; background: transparent !important; margin-top: 1.6rem !important;
    }}
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] details > div:first-child {{
      background: transparent !important; border: none !important;
    }}
    [data-testid="stExpander"] summary {{
      padding: 10px 0 6px 0 !important; background: transparent !important;
    }}
    /* The expander LABEL lives in a nested <p> with its own font-size, so styling
       `summary` alone leaves it small (~14px). Target the <p> directly to match
       .cmsi-section .ttl (21px) so the collapsible headers look like section headers. */
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] summary span:not([data-testid="stIconMaterial"]):not([class*="material"]) {{
      font-size: 21px !important; line-height: 27px !important; font-weight: 600 !important;
      color: {theme.INK} !important; letter-spacing: -0.01em !important; margin: 0 !important;
    }}
    [data-testid="stExpander"] summary:hover p,
    [data-testid="stExpander"] summary:hover {{
      background: transparent !important; color: {theme.CMSI_RED} !important;
    }}
    [data-testid="stExpander"] summary::before {{
      content: ''; display: inline-block; width: 4px; height: 18px;
      background: {theme.CMSI_RED}; margin-right: 10px; vertical-align: -2px;
    }}
    </style>""",
    unsafe_allow_html=True,
)


def _render_pct_table(
    df: pd.DataFrame,
    pct_cols: list[str],
    num_cols: list[str] | None = None,
    column_labels: dict | None = None,
) -> None:
    """Sort-bug-safe: numeric DataFrame + column_config + Styler color (delegates to ui)."""
    text_cols = [c for c in df.columns if c not in pct_cols and (num_cols is None or c not in num_cols)]
    extra_formats = {c: "%.2f" for c in (num_cols or []) if c in df.columns}
    ui.render_styled_table(
        df,
        pct_cols=pct_cols,
        text_cols=text_cols,
        extra_formats=extra_formats,
        column_labels=column_labels,
        height=360,
        heatmap=True,
    )


def _render_movers(domain: str) -> None:
    """Gainers/drags side-by-side for ONE domain (e.g. 'healthcare' / 'ai'), so each
    benchmark category shows its own movers. Empty domain (no tickers yet, e.g. AI) →
    a 'coming soon' caption instead of empty tables."""
    gainers, losers = db.top_movers(n=10, domain=domain)
    if gainers.empty:
        st.caption(i18n.t("home.panel.empty"))
        return
    rename_map = {"name": "Name", "last": "Last",
                  "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %"}
    c1, c2 = st.columns(2)
    with c1:
        theme.subsection(i18n.t("home.movers.gainers"))
        g = gainers.rename(columns=rename_map)
        g.index = [fmt.fmt_ticker_bbg(t) for t in g.index]
        _render_pct_table(g, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"], column_labels=i18n.common_cols())
    with c2:
        theme.subsection(i18n.t("home.movers.drags"))
        l = losers.rename(columns=rename_map)
        l.index = [fmt.fmt_ticker_bbg(t) for t in l.index]
        _render_pct_table(l, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"], column_labels=i18n.common_cols())


# ---- Single-stock heatmap v2 — ranked bento grid (Healthcare + AI) ----
# Data assembly + self-contained HTML render live in lib/heatmap.py
# (build_domain_bento / render_bento_html). Replaces the v1 go.Treemap
# (area = |return|, which let one outlier eat the canvas) per the 2026-06-01
# design-team + 4-way /cccg review. Sub-sectors are ranked by MEDIAN member
# return; the best book gets the most tile "slots" (declutters cold books).
# Window/domain toggles are Streamlit segmented_controls (Python re-runs); the
# board is server-rendered HTML in an iframe (st.markdown strips <script>,
# st.dataframe is a dark canvas — same reason ui.render_html_table uses iframes).
def _render_stock_heatmap() -> None:
    prefer_cn = i18n.get_lang() == "zh"
    theme.section_header("个股热力图" if prefer_cn else "Single-Stock Heatmap")

    cw = st.columns([1, 1.5])
    with cw[0]:
        win = st.segmented_control(
            "时间窗口" if prefer_cn else "Window",
            ["1D", "5D", "1M"], default="1D",
            key="hc_heatmap_window", label_visibility="collapsed",
        ) or "1D"
    all_lbl = "全部" if prefer_cn else "All"
    dom_map = {
        all_lbl: ["healthcare", "ai"],
        ("医疗" if prefer_cn else "Healthcare"): ["healthcare"],
        "AI": ["ai"],
    }
    with cw[1]:
        dom_choice = st.segmented_control(
            "范围" if prefer_cn else "Domain",
            list(dom_map.keys()), default=all_lbl,
            key="hc_heatmap_domain", label_visibility="collapsed",
        ) or all_lbl

    window_col = hm.WIN_TO_COL.get(win, "1d_%")
    domains = []
    for did in dom_map.get(dom_choice, ["healthcare", "ai"]):
        d = hm.build_domain_bento(did, window_col, prefer_cn)
        if d and d["sectors"]:
            domains.append(d)
    if not domains:
        st.info(i18n.t("home.panel.empty"))
        return
    doc, h = hm.render_bento_html(domains, prefer_cn=prefer_cn, window_label=win, as_of=latest)
    st.iframe(doc, height=h)
    st.caption(
        (f"子行业按中位涨跌排名分配席位 · 青绿涨/红跌（港美股惯例，与 A 股相反）· 截至 {latest}"
         if prefer_cn else
         f"Slots by sub-sector median-return rank · teal up / red down (HK/US convention) · as of {latest}")
    )


# ---- Benchmark data (cron-cached, read-only) ----
bench_df = bm.fetch_benchmarks()
gspc_ytd = bench_df.loc["^GSPC", "ytd_%"] if "^GSPC" in bench_df.index else None
_panels = dict(bm.PANELS)


def _render_benchmark_table(panel_id: str, syms: list[str]) -> None:
    """One benchmark panel → FT-editorial HTML table (vs-SPX column; ^GSPC reference
    row for the sector hero). Empty panel → 'coming soon' caption."""
    present = [s for s in syms if s in bench_df.index]
    if not present:
        st.caption(i18n.t("home.panel.empty"))
        return
    sub = bench_df.reindex(present).copy()
    sub["vs_spx_pp"] = (sub["ytd_%"] - gspc_ytd) if gspc_ytd is not None else pd.NA
    if panel_id == "sp500_sector" and "^GSPC" in sub.index:
        sub.loc["^GSPC", "vs_spx_pp"] = pd.NA
    sub["Name"] = [i18n.bench_name(s, n) for s, n in zip(sub.index, sub["name"])]
    show = sub[["Name", "1d_%", "5d_%", "1m_%", "3m_%", "ytd_%", "vs_spx_pp"]].rename(columns={
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "3m_%": "3M %",
        "ytd_%": "YTD %", "vs_spx_pp": "vs SPX",
    })
    ui.render_html_table(
        show,
        pct_cols=["1D %", "5D %", "1M %", "3M %", "YTD %", "vs SPX"],
        text_cols=["Name"],
        column_labels=i18n.common_cols(),
        heatmap=True,
        ref_rows=({"^GSPC"} if panel_id == "sp500_sector" else None),
        height=(520 if panel_id == "sp500_sector" else 360),
    )
    st.caption(
        f"来源 Yahoo Finance cron EOD · 截至 {latest} · 仅供参考"
        if i18n.get_lang() == "zh"
        else f"Source: Yahoo Finance cron EOD · as of {latest} · reference only"
    )


# --- 1. Market Overview — KPI cards (^GSPC / ^NDX / ^HSI) ---
theme.section_header(i18n.t("home.panel.broad_market"))
_bm_present = [s for s in _panels["broad_market"] if s in bench_df.index]
if not _bm_present:
    st.caption(i18n.t("home.panel.empty"))
else:
    cards = []
    for sym in _bm_present:
        row = bench_df.loc[sym]
        d1 = row["1d_%"]
        direction = "flat" if pd.isna(d1) else ("up" if d1 > 0 else "down" if d1 < 0 else "flat")
        delta_pct = f"{d1:+.2f}%" if not pd.isna(d1) else None
        m1, ytd = row["1m_%"], row["ytd_%"]
        foot_parts = []
        if not pd.isna(m1):
            foot_parts.append(f"1M {m1:+.1f}%")
        if not pd.isna(ytd):
            foot_parts.append(f"YTD {ytd:+.1f}%")
        foot = " · ".join(foot_parts) if foot_parts else None
        last = row["last"]
        cards.append(theme.kpi_metric(
            label=i18n.bench_name(sym, row["name"]),
            value=f"{last:,.2f}" if not pd.isna(last) else "—",
            delta_pct=delta_pct, foot=foot, direction=direction,
        ))
    theme.kpi_strip(cards)

# --- 1b. Single-stock heatmap v2 (ranked bento grid, Healthcare + AI) — sits under the
#     KPI strip, high on the page. Size = market cap, color = selectable-window
#     return (teal up / red down), grouped by healthcare sub-sector. ---
_render_stock_heatmap()

# --- 2. S&P 500 sectors (hero) — collapsible (expanded by default) ---
with st.expander(i18n.t("home.panel.sp500_sector"), expanded=True):
    st.caption(i18n.t("home.panel.sp500_caption"))
    _render_benchmark_table("sp500_sector", _panels["sp500_sector"])

# --- 3. Healthcare domain — collapsible (expanded); benchmark + movers UNIFIED under
#     one domain header. Inner blocks use subsection() (no dividing INK rule), so the
#     HC benchmark and its movers read as ONE healthcare block. ---
with st.expander(i18n.domain_name("healthcare"), expanded=True):
    theme.subsection(i18n.t("home.sub.benchmarks"))
    _render_benchmark_table("healthcare", _panels["healthcare"])
    theme.subsection(i18n.t("home.section.movers"))
    _render_movers("healthcare")

# --- 4. AI domain — collapsible (collapsed by default). Benchmark table populated from
#     the cross-market AI/semi set (LLM Wiki); movers stub until an AI stock universe
#     lands. Future domains follow this same collapsible-card pattern. ---
with st.expander(i18n.domain_name("ai"), expanded=False):
    _ai_syms = _panels.get("ai", [])
    if _ai_syms:
        theme.subsection(i18n.t("home.sub.benchmarks"))
        _render_benchmark_table("ai", _ai_syms)
        theme.subsection(i18n.t("home.section.movers"))
        _render_movers("ai")
    else:
        st.caption(i18n.t("home.panel.empty"))

# --- Footer ---
st.caption(i18n.t("home.caveat.data"))
