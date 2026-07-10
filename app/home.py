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
from lib import heatmap_treemap
from lib import market_hub_tiles
from lib import market_hub_tables
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
        st.caption(i18n.t("home.panel.empty"))
        return
    # v3: one ECharts Treemap (面积=市值 / 颜色=涨跌) per domain — replaces the bento.
    _h = 600 if len(domains) > 1 else 720
    for i, _d in enumerate(domains):
        _doc, _hh = heatmap_treemap.render_treemap_html(
            _d, window_label=win, as_of=latest, prefer_cn=prefer_cn, height=_h,
            show_header=(i == 0))
        st.iframe(_doc, height=_hh)
    st.caption(
        (f"子行业按中位涨跌排名分配席位 · 青绿涨/红跌（港美股惯例，与 A 股相反）· 截至 {latest}"
         if prefer_cn else
         f"Slots by sub-sector median-return rank · teal up / red down (HK/US convention) · as of {latest}")
    )
    # 点热力图里看到的股 → 这里选代码 → K 线弹窗(cream 终端,不离开本页 / 不跳新页)。
    from lib import candlestick_terminal as cterm
    _hm_tickers = sorted(db.all_tickers())
    if _hm_tickers:
        cterm.kline_picker(_hm_tickers, db.ticker_to_name(prefer_cn=prefer_cn),
                           prefer_cn=prefer_cn, key="home_hm_kline")


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


# --- 1. Market Overview — [09] index tiles (sparkline + 52w range, real EOD data) ---
# HUB1 masthead(wave-2 行情中枢设计头排):红条 + 30px 标题 + mono kicker + EOD 状态块。
# 呼吸点复用 theme._CSS 的 .cmsi-live-dot 动画;文案语义改真(EOD,非实时)。
_zh_hub = i18n.get_lang() == "zh"
st.markdown(
    f"""<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:20px;
border-bottom:2px solid {theme.INK};padding-bottom:14px;margin:4px 0 14px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <span style="width:5px;height:44px;background:{theme.CMSI_RED};border-radius:1px;flex:none;"></span>
    <div>
      <div style="font-family:{theme.FONT_DISPLAY};font-size:30px;line-height:34px;font-weight:700;letter-spacing:-0.01em;color:{theme.INK};">{"行情中枢" if _zh_hub else "Market Hub"}</div>
      <div style="font-family:{theme.FONT_MONO};font-size:11px;letter-spacing:.08em;color:{theme.INK_3};margin-top:5px;">CMSI · MARKET HUB · {"四大指数总览" if _zh_hub else "BROAD MARKET OVERVIEW"}</div>
    </div>
  </div>
  <div style="text-align:right;flex:none;">
    <div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;">
      <span class="cmsi-live-dot" style="width:8px;height:8px;border-radius:50%;background:{theme.UP};display:inline-block;"></span>
      <span style="font-family:{theme.FONT_MONO};font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:{theme.UP};font-weight:600;">{"EOD · 收盘" if _zh_hub else "EOD · CLOSE"}</span>
    </div>
    <div style="font-family:{theme.FONT_MONO};font-size:11px;color:{theme.INK_3};margin-top:5px;">{f'EOD {latest} · 取数 {fetch_utc[:16] if fetch_utc else "—"} HKT' if _zh_hub else f'EOD {latest} · fetch {fetch_utc[:16] if fetch_utc else "—"} HKT'}</div>
  </div>
</div>""",
    unsafe_allow_html=True,
)
_bm_present = [s for s in _panels["broad_market"] if s in bench_df.index]
if not _bm_present:
    theme.section_header(i18n.t("home.panel.broad_market"))
    st.caption(i18n.t("home.panel.empty"))
else:
    # 52w range micro-bar + ~30d sparkline from the DB-backed close series (real, not MOCK).
    _bm_series = bm.close_series()

    def _range52(sym: str, last) -> tuple | None:
        """Real trailing-52-week (lo_str, hi_str, pos) from the close series; None
        if no series, last missing, or the window spans <~330d (never mislabel a
        short window as '52W' — anti-slop 数字非编造)."""
        ser = _bm_series.get(sym)
        if ser is None or last is None or pd.isna(last):
            return None
        ser = ser.dropna().sort_index()
        if ser.empty:
            return None
        win = ser[ser.index >= ser.index.max() - pd.Timedelta(days=365)]
        if win.empty or (win.index.max() - win.index.min()).days < 330:
            return None
        lo, hi = float(win.min()), float(win.max())
        if hi <= lo:
            return None
        _f = lambda v: f"{v:,.2f}" if v < 1000 else f"{v:,.0f}"
        return (_f(lo), _f(hi), (float(last) - lo) / (hi - lo))

    def _spark(sym: str) -> list[float]:
        """近 ~30 个收盘点(real)给 sparkline;不足 2 点则空(瓦片不画线)。"""
        ser = _bm_series.get(sym)
        if ser is None:
            return []
        ser = ser.dropna().sort_index()
        return [float(v) for v in ser.tail(30).tolist()]

    _tiles = []
    for sym in _bm_present:
        row = bench_df.loc[sym]
        last = row["last"]
        r52 = _range52(sym, last)
        _tiles.append({
            "name": i18n.bench_name(sym, row["name"]),
            "value": f"{last:,.2f}" if not pd.isna(last) else "—",
            "value_raw": None if pd.isna(last) else float(last),  # enables count-up
            "chg_pct": None if pd.isna(row["1d_%"]) else float(row["1d_%"]),
            "lo": r52[0] if r52 else None,
            "hi": r52[1] if r52 else None,
            "pos": r52[2] if r52 else None,
            "m1": None if pd.isna(row["1m_%"]) else float(row["1m_%"]),
            "ytd": None if pd.isna(row["ytd_%"]) else float(row["ytd_%"]),
            "spark": _spark(sym),
        })
    _doc, _h = market_hub_tiles.render_index_tiles(
        _tiles, as_of=latest, prefer_cn=(i18n.get_lang() == "zh"))
    st.iframe(_doc, height=_h)

# --- 1b. Single-stock heatmap v2 (ranked bento grid, Healthcare + AI) — sits under the
#     KPI strip, high on the page. Size = market cap, color = selectable-window
#     return (teal up / red down), grouped by healthcare sub-sector. ---
_render_stock_heatmap()

# --- 2+3. Market Hub iframe — S&P 500 GICS sectors + HC benchmarks + 涨跌榜 ---
# Three blocks in one self-contained iframe (client-side sort, no Streamlit rerun).
# Replaces the old sp500_sector expander + healthcare benchmark/movers expanders.
_prefer_cn = i18n.get_lang() == "zh"

# SP rows: 11 GICS SPDR ETFs (exclude ^GSPC; it becomes sp_ref)
_GICS_ZH = {
    "XLK": "信息技术", "XLC": "通信服务", "XLY": "非必需消费",
    "XLF": "金融", "XLV": "医疗健康", "XLI": "工业",
    "XLP": "必需消费", "XLE": "能源", "XLU": "公用事业",
    "XLB": "材料", "XLRE": "房地产",
}
_GICS_EN = {
    "XLK": "Technology", "XLC": "Comm. Services", "XLY": "Cons. Discretionary",
    "XLF": "Financials", "XLV": "Health Care", "XLI": "Industrials",
    "XLP": "Cons. Staples", "XLE": "Energy", "XLU": "Utilities",
    "XLB": "Materials", "XLRE": "Real Estate",
}
_gics_names = _GICS_ZH if _prefer_cn else _GICS_EN

_sp_etfs = [s for s in _panels["sp500_sector"] if s != "^GSPC"]
_sp_rows = []
for _sym in _sp_etfs:
    if _sym not in bench_df.index:
        continue
    _row = bench_df.loc[_sym]
    _rel = (float(_row["ytd_%"]) - float(gspc_ytd)) if (gspc_ytd is not None and not pd.isna(_row["ytd_%"]) and not pd.isna(gspc_ytd)) else None
    _sp_rows.append([
        _sym,
        _gics_names.get(_sym, _row["name"]),
        None if pd.isna(_row["1d_%"]) else float(_row["1d_%"]),
        None if pd.isna(_row["5d_%"]) else float(_row["5d_%"]),
        None if pd.isna(_row["1m_%"]) else float(_row["1m_%"]),
        None if pd.isna(_row["3m_%"]) else float(_row["3m_%"]),
        None if pd.isna(_row["ytd_%"]) else float(_row["ytd_%"]),
        _rel,
    ])

_sp_ref = None
if "^GSPC" in bench_df.index:
    _gr = bench_df.loc["^GSPC"]
    _sp_ref = [
        "^GSPC",
        "标普 500 指数" if _prefer_cn else "S&P 500 Index",
        None if pd.isna(_gr["1d_%"]) else float(_gr["1d_%"]),
        None if pd.isna(_gr["5d_%"]) else float(_gr["5d_%"]),
        None if pd.isna(_gr["1m_%"]) else float(_gr["1m_%"]),
        None if pd.isna(_gr["3m_%"]) else float(_gr["3m_%"]),
        None if pd.isna(_gr["ytd_%"]) else float(_gr["ytd_%"]),
        None,
    ]

# HC rows: design's 9 HC ETFs (exclude A/HK indices — not in iframe design)
_HC_ORDER = ["XLV", "XBI", "XPH", "^SP500-352020", "IHI", "IHF", "XHS", "IGV", "IXJ"]
_hc_rows = []
for _sym in _HC_ORDER:
    if _sym not in bench_df.index:
        continue
    _row = bench_df.loc[_sym]
    _rel = (float(_row["ytd_%"]) - float(gspc_ytd)) if (gspc_ytd is not None and not pd.isna(_row["ytd_%"]) and not pd.isna(gspc_ytd)) else None
    _hc_rows.append([
        _sym,
        i18n.bench_name(_sym, _row["name"]),
        None if pd.isna(_row["1d_%"]) else float(_row["1d_%"]),
        None if pd.isna(_row["5d_%"]) else float(_row["5d_%"]),
        None if pd.isna(_row["1m_%"]) else float(_row["1m_%"]),
        None if pd.isna(_row["3m_%"]) else float(_row["3m_%"]),
        None if pd.isna(_row["ytd_%"]) else float(_row["ytd_%"]),
        _rel,
    ])

# Movers: top_movers returns (gainers, losers) with index=ticker, cols=[name,last,1d_%,5d_%,1m_%,ytd_%]
_hub_gainers_df, _hub_losers_df = db.top_movers(n=10, domain="healthcare")


def _mover_rows(df: pd.DataFrame) -> list:
    out = []
    for _tk, _r in df.iterrows():
        _mkt = ("HK" if str(_tk).endswith(".HK") else "JP" if str(_tk).endswith(".T") else "KR" if (str(_tk).endswith(".KS") or str(_tk).endswith(".KQ")) else "CN" if (str(_tk).endswith(".SS") or str(_tk).endswith(".SZ")) else "US")
        out.append([
            str(_tk),
            _mkt,
            str(_r.get("name", _tk)),
            None if pd.isna(_r.get("last", float("nan"))) else float(_r["last"]),
            None if pd.isna(_r.get("1d_%", float("nan"))) else float(_r["1d_%"]),
            None if pd.isna(_r.get("5d_%", float("nan"))) else float(_r["5d_%"]),
            None if pd.isna(_r.get("1m_%", float("nan"))) else float(_r["1m_%"]),
        ])
    return out


_hub_payload = {
    "sp_rows": _sp_rows,
    "sp_ref":  _sp_ref,
    "hc_rows": _hc_rows,
    "gainers": _mover_rows(_hub_gainers_df),
    "losers":  _mover_rows(_hub_losers_df),
    "as_of":   latest or "",
}
_hub_labels = {
    "hub.tbl.sp.title":      i18n.t("hub.tbl.sp.title"),
    "hub.tbl.sp.sub":        i18n.t("hub.tbl.sp.sub"),
    "hub.tbl.sp.right":      "GICS SPDR ETF",
    "hub.tbl.hc.title":      i18n.t("hub.tbl.hc.title"),
    "hub.tbl.hc.sub":        i18n.t("hub.tbl.hc.sub"),
    "hub.tbl.hc.right":      "HC BENCHMARK",
    "hub.tbl.movers.title":  i18n.t("hub.tbl.movers.title"),
    "hub.tbl.movers.sub":    i18n.t("hub.tbl.movers.sub"),
    "hub.tbl.movers.right":  "HEALTHCARE UNIVERSE",
    "hub.tbl.grp.ret":       "回报 RETURNS %" if _prefer_cn else "RETURNS %",
    "hub.tbl.grp.rel":       "相对标普 · YTD 超额 PP" if _prefer_cn else "vs S&P 500 · YTD excess PP",
    "hub.tbl.col.tick":      "代码" if _prefer_cn else "Ticker",
    "hub.tbl.col.name":      "名称" if _prefer_cn else "Name",
    "hub.tbl.col.d1":        "1日" if _prefer_cn else "1D",
    "hub.tbl.col.d5":        "5日" if _prefer_cn else "5D",
    "hub.tbl.col.m1":        "1月" if _prefer_cn else "1M",
    "hub.tbl.col.m3":        "3月" if _prefer_cn else "3M",
    "hub.tbl.col.ytd":       "年初至今" if _prefer_cn else "YTD",
    "hub.tbl.col.rel":       "相对PP" if _prefer_cn else "vs SPX",
    "hub.tbl.col.dist":      "分布" if _prefer_cn else "Dist.",
    "hub.tbl.movers.gainers": "涨幅前 10" if _prefer_cn else "Top 10 Gainers",
    "hub.tbl.movers.losers":  "跌幅前 10" if _prefer_cn else "Top 10 Losers",
    "hub.tbl.movers.col.rank":  "#",
    "hub.tbl.movers.col.price": "最新价" if _prefer_cn else "Price",
    "hub.tbl.footnote": (
        "回报数据来源 Yahoo Finance cron EOD · 相对 PP = 标的 YTD − 标普 500 YTD · "
        f"截至 {latest} · 仅供参考"
        if _prefer_cn else
        f"Returns: Yahoo Finance cron EOD · Relative PP = ticker YTD − S&P 500 YTD · "
        f"as of {latest} · reference only"
    ),
    "hub.tbl.brand": "CMSI · MARKET HUB",
}
_hub_doc, _hub_h = market_hub_tables.render_market_hub(_hub_payload, _hub_labels)
st.iframe(_hub_doc, height=_hub_h)

# --- 4. AI domain — hub-style glass table (expanded by default). Benchmark table
#     populated from the cross-market AI/semi set (LLM Wiki); movers stub until an AI
#     stock universe lands. Future domains follow this same pattern. ---
with st.expander(i18n.domain_name("ai"), expanded=True):
    _ai_syms = _panels.get("ai", [])
    if _ai_syms:
        _ai_present = [s for s in _ai_syms if s in bench_df.index]
        _ai_rows = []
        for _sym in _ai_present:
            _row = bench_df.loc[_sym]
            _rel = (float(_row["ytd_%"]) - float(gspc_ytd)) if (
                gspc_ytd is not None
                and not pd.isna(_row["ytd_%"])
                and not pd.isna(gspc_ytd)
            ) else None
            _ai_rows.append([
                _sym,
                i18n.bench_name(_sym, _row["name"]),
                None if pd.isna(_row["1d_%"]) else float(_row["1d_%"]),
                None if pd.isna(_row["5d_%"]) else float(_row["5d_%"]),
                None if pd.isna(_row["1m_%"]) else float(_row["1m_%"]),
                None if pd.isna(_row["3m_%"]) else float(_row["3m_%"]),
                None if pd.isna(_row["ytd_%"]) else float(_row["ytd_%"]),
                _rel,
            ])
        _ai_labels = {
            "bench.title":       "基准 / AI · BENCHMARKS" if _prefer_cn else "基准 / AI · BENCHMARKS",
            "bench.sub":         "半导体 · AI主题 · 跨市场" if _prefer_cn else "Semis · AI Theme · Cross-Market",
            "bench.right":       "AI BENCHMARK",
            "bench.as_of":       latest or "",
            "hub.tbl.grp.ret":   "回报 RETURNS %" if _prefer_cn else "RETURNS %",
            "hub.tbl.grp.rel":   "相对标普 · YTD 超额 PP" if _prefer_cn else "vs S&P 500 · YTD excess PP",
            "hub.tbl.col.tick":  "代码" if _prefer_cn else "Ticker",
            "hub.tbl.col.name":  "名称" if _prefer_cn else "Name",
            "hub.tbl.col.d1":    "1日" if _prefer_cn else "1D",
            "hub.tbl.col.d5":    "5日" if _prefer_cn else "5D",
            "hub.tbl.col.m1":    "1月" if _prefer_cn else "1M",
            "hub.tbl.col.m3":    "3月" if _prefer_cn else "3M",
            "hub.tbl.col.ytd":   "年初至今" if _prefer_cn else "YTD",
            "hub.tbl.col.rel":   "相对PP" if _prefer_cn else "vs SPX",
            "hub.tbl.col.dist":  "分布" if _prefer_cn else "Dist.",
            "hub.tbl.footnote": (
                "回报数据来源 Yahoo Finance cron EOD · 相对 PP = 标的 YTD − 标普 500 YTD · "
                f"截至 {latest} · 仅供参考"
                if _prefer_cn else
                f"Returns: Yahoo Finance cron EOD · Relative PP = ticker YTD − S&P 500 YTD · "
                f"as of {latest} · reference only"
            ),
            "hub.tbl.brand": "CMSI · MARKET HUB",
        }
        if _ai_rows:
            _ai_doc, _ai_h = market_hub_tables.render_bench_block(_ai_rows, _ai_labels)
            st.iframe(_ai_doc, height=_ai_h)
        else:
            st.caption(i18n.t("home.panel.empty"))
        # AI 涨跌榜 — 与 hub 同款双 glass 卡（旧 _render_movers 表格样式退役）
        _ai_g, _ai_l = db.top_movers(n=10, domain="ai")
        if not _ai_g.empty:
            _mv_labels = {
                "hub.tbl.movers.title": "涨跌榜 · 1 日" if _prefer_cn else "Top Movers · 1D",
                "hub.tbl.movers.sub": ("AI 覆盖池 · 按 1 日涨跌排序 · 价格为当地币种"
                                        if _prefer_cn else
                                        "AI coverage pool · ranked by 1D move · local currency"),
                "hub.tbl.movers.right": "AI UNIVERSE",
                "hub.tbl.movers.gainers": "涨幅前 10" if _prefer_cn else "Top 10 Gainers",
                "hub.tbl.movers.losers": "跌幅前 10" if _prefer_cn else "Top 10 Losers",
                "hub.tbl.movers.col.rank": "#",
                "hub.tbl.movers.col.price": "最新价" if _prefer_cn else "Price",
                "hub.tbl.col.tick": "代码" if _prefer_cn else "Ticker",
                "hub.tbl.col.name": "名称" if _prefer_cn else "Name",
                "hub.tbl.col.d1": "1日" if _prefer_cn else "1D",
                "hub.tbl.col.d5": "5日" if _prefer_cn else "5D",
                "hub.tbl.col.m1": "1月" if _prefer_cn else "1M",
            }
            _mv_doc, _mv_h = market_hub_tables.render_movers_block(
                _mover_rows(_ai_g), _mover_rows(_ai_l), _mv_labels)
            st.iframe(_mv_doc, height=_mv_h)
    else:
        st.caption(i18n.t("home.panel.empty"))

# --- Footer ---
st.caption(i18n.t("home.caveat.data"))
