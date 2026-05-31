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

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Unified sidebar search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="home")

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


# ---- Healthcare stock heatmap (finviz-style treemap) ----
# Candidate market-cap columns in multiples_daily (defensive: schema name varies
# across snapshots). First present, positive value wins.
_MCAP_CANDIDATES = (
    "market_cap_usd", "mcap_usd", "marketcap_usd",
    "market_cap", "marketcap", "mktcap_usd", "mktcap",
)


@st.cache_data(ttl=300)
def _healthcare_sectors() -> list[str]:
    """Healthcare sub-sectors from the universe (skips '_coverage' pseudo-sector)."""
    df = db.query(
        "SELECT DISTINCT sector FROM universe_member "
        "WHERE domain = 'healthcare' AND sector != '_coverage' ORDER BY sector"
    )
    return df["sector"].tolist()


def _build_heatmap_df(window_col: str) -> tuple[pd.DataFrame, str]:
    """Assemble per-stock heatmap rows for ALL healthcare sub-sectors.

    Returns (df, mcap_col_used). df is indexed by ticker with columns
    [sector, name, ret_pct, mcap]. Rows with no/≤0 market cap are dropped.
    """
    sectors = _healthcare_sectors()
    frames: list[pd.DataFrame] = []
    for sec in sectors:
        members = db.sector_tickers("healthcare", sec)
        if members.empty:
            continue
        sub = members[["ticker"]].copy()
        sub["sector"] = sec
        frames.append(sub)
    if not frames:
        return pd.DataFrame(), ""
    base = pd.concat(frames, ignore_index=True).drop_duplicates("ticker")
    tickers = tuple(base["ticker"].tolist())
    if not tickers:
        return pd.DataFrame(), ""

    # Returns over the selected window.
    closes = db.get_close_series_usd(tickers)
    rets = db.compute_returns(closes)
    if rets.empty or window_col not in rets.columns:
        return pd.DataFrame(), ""

    # Latest multiples → market cap (pick first present candidate column).
    mult = db.latest_multiples(tickers)
    mcap_col = ""
    for cand in _MCAP_CANDIDATES:
        if not mult.empty and cand in mult.columns:
            mcap_col = cand
            break
    if not mcap_col:
        return pd.DataFrame(), ""

    prefer_cn = i18n.get_lang() == "zh"
    names = db.ticker_to_name(prefer_cn=prefer_cn)

    base = base.set_index("ticker")
    base["name"] = [names.get(t, t) for t in base.index]
    base["ret_pct"] = rets[window_col].reindex(base.index)
    base["mcap"] = pd.to_numeric(mult[mcap_col].reindex(base.index), errors="coerce")
    # tile SIZE = |return| (George: big movers big, mega-caps small). Keep names
    # that have a return (mcap kept for hover only); floor |ret| so a near-flat
    # name still shows a small tile instead of vanishing.
    base = base[base["ret_pct"].notna()]
    base["abs_ret"] = base["ret_pct"].abs().clip(lower=0.05)
    return base, mcap_col


def _render_healthcare_heatmap() -> None:
    """Finviz-style treemap of healthcare single stocks: size=mcap, color=window
    return (teal up / red down), grouped by sub-sector. Window switch via
    st.segmented_control (1D / 5D / 1M)."""
    prefer_cn = i18n.get_lang() == "zh"
    theme.section_header(
        "医疗个股热力图" if prefer_cn else "Healthcare Stock Heatmap"
    )
    win_options = ["1D", "5D", "1M"]
    win = st.segmented_control(
        i18n.t("home.section.movers") if False else ("时间窗口" if prefer_cn else "Window"),
        win_options,
        default="1D",
        key="hc_heatmap_window",
        label_visibility="collapsed",
    ) or "1D"
    win_to_col = {"1D": "1d_%", "5D": "5d_%", "1M": "1m_%"}
    window_col = win_to_col.get(win, "1d_%")

    hdf, mcap_col = _build_heatmap_df(window_col)
    if hdf.empty:
        st.info(i18n.t("home.panel.empty"))
        return
    fig = charts.treemap_heatmap(
        hdf,
        size_col="abs_ret",
        color_col="ret_pct",
        group_col="sector",
        label_col="name",
        title=("医疗个股热力图 · " if prefer_cn else "Healthcare Heatmap · ") + win,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        (f"瓦片面积 = 涨跌幅绝对值（动得越大块越大）· 颜色 = {win} 涨跌 · 青涨/红跌 · 截至 {latest}"
         if prefer_cn else
         f"Tile size = |{win} return| (bigger move = bigger tile) · color = {win} return · teal up / red down · as of {latest}")
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
    st.caption(f"来源 Yahoo Finance cron EOD · 截至 {latest} · 仅供参考")


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

# --- 1b. Healthcare stock heatmap (finviz-style treemap) — sits directly under the
#     KPI strip, high on the page. Size = market cap, color = selectable-window
#     return (teal up / red down), grouped by healthcare sub-sector. ---
_render_healthcare_heatmap()

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
