"""Shared Streamlit UI components."""

from __future__ import annotations

import html as _html
import math

import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt
from lib import theme
from lib import i18n

# Shared column tooltips — single source of truth for cross-page consistency.
# Reference these via render_styled_table(column_help=COLUMN_HELP) or splice
# into manual column_config dicts.
COLUMN_HELP = {
    "Fwd P/E": (
        "yfinance.info.forwardPE — Next-12-Month rolling consensus forward EPS "
        "(LSEG / Refinitiv source). 与 Yahoo Finance 网页 \"預測市盈率\" "
        "(下一财年 fiscal-year EPS 口径) 数字可能差 5-10%。"
        "Cross-check 请用 Bloomberg / FactSet / 卖方研报。"
    ),
    "Trail P/E": (
        "yfinance.info.trailingPE — Trailing 12-Month GAAP EPS。"
        "Biotech 烧钱期标的可能 NULL / 负值。"
    ),
    "EV/EBITDA": (
        "yfinance.info.enterpriseToEbitda — TTM EBITDA basis。"
        "Biotech / SaaS 早期标的若 EBITDA 为负，倍数无意义。"
    ),
    "EV/Sales": (
        "yfinance.info.enterpriseToRevenue — TTM Revenue basis。"
        "高增长 biotech / hc_ai 看此指标比 P/E 更有意义。"
    ),
    "FCF Yld": (
        "Free Cash Flow Yield = FCF / Market Cap (TTM)。"
        "yfinance.info.freeCashflow / marketCap。"
        "用 USD-converted market cap 计算。"
    ),
    "P/B": (
        "yfinance.info.priceToBook — Latest reported book value basis。"
        "金融 / asset-light 公司参考价值有限。"
    ),
    "TP Upside %": (
        "(targetMeanPrice - currentPrice) / currentPrice × 100%。"
        "yfinance.info.targetMeanPrice — consensus 12M target price mean across "
        "covering analysts。Yahoo aggregator，与 Bloomberg/Wind broker basket 不同。"
    ),
    "Reco": (
        "yfinance.info.recommendationMean: 1=Strong Buy, 2=Buy, 3=Hold, 4=Sell, 5=Strong Sell。"
        "标签按 1.5/2.5/3.5/4.5 阈值切档。"
    ),
    "N analysts": (
        "yfinance.info.numberOfAnalystOpinions — 当前覆盖该标的的卖方分析师数。"
        "<5 时 consensus 不稳健。"
    ),
    "vs HSI YTD": (
        "YTD return - HSI YTD return (pp)。港股 sell-side 早会必看指标。"
    ),
    "Mcap USD ($B)": (
        "Market cap converted to USD via daily FX (yfinance Currency. 港股 HKD/USD, "
        "JP JPY/USD, KR KRW/USD, CN CNY/USD)。"
    ),
}


def sidebar_search(key_prefix: str = ""):
    """Global theme-CSS injection hook (kept on every page).

    The sidebar ticker-search UI (🔍 查找标的 subheader + jump-to dropdown) was
    removed per user request — the top navigation + the dedicated Ticker Drill
    page already cover lookup, so the duplicate sidebar search was redundant.
    Function name/signature kept so the existing per-page call sites stay valid
    and CSS still injects with 100% page coverage. `key_prefix` is now unused.
    Ticker Drill still resolves its own selection via its local selectbox + the
    `?ticker=` URL param; `global_ticker` is initialised here for safety.
    """
    theme.inject_css()
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = ""


def onboarding_expander(page_name: str, markdown_text: str):
    """Consistent onboarding expander across pages."""
    with st.expander(f"How to read this {page_name}"):
        st.markdown(markdown_text)


# ---------- Sort-bug-safe table renderer (extracted from CMSI Coverage) ----------

def render_styled_table(
    df: pd.DataFrame,
    *,
    pct_cols: list[str] | None = None,
    pct_decimal_cols: list[str] | None = None,
    mult_cols: list[str] | None = None,
    money_b_cols: list[str] | None = None,
    int_cols: list[str] | None = None,
    text_cols: list[str] | None = None,
    column_widths: dict[str, str] | None = None,
    extra_formats: dict[str, str] | None = None,
    column_help: dict[str, str] | None = None,
    column_labels: dict[str, str] | None = None,
    index_label: str | None = None,
    height: int = 500,
    hide_index: bool = False,
    heatmap: bool = False,
    ref_rows: set | None = None,
) -> None:
    """DEPRECATED shim → render_html_table (kept so existing call sites work).

    Previously rendered a pandas Styler via st.dataframe (glide-data-grid CANVAS):
    CSS could not reach the cells and OS dark-mode penetrated → black tables, and
    Styler.background_gradient filled whole cells (violating DESIGN.md 染字不染底).
    Now delegates to the FT-editorial HTML table. `column_widths` is ignored
    (HTML auto-sizes). Pass heatmap=True for the optional ≤12% tinted heatmap.
    """
    render_html_table(
        df,
        pct_cols=pct_cols,
        pct_decimal_cols=pct_decimal_cols,
        mult_cols=mult_cols,
        money_b_cols=money_b_cols,
        int_cols=int_cols,
        text_cols=text_cols,
        extra_formats=extra_formats,
        column_help=column_help,
        column_labels=column_labels,
        index_label=index_label,
        height=height,
        hide_index=hide_index,
        heatmap=heatmap,
        ref_rows=ref_rows,
    )


# ---------- FT-editorial HTML table (Stage 2 — solves dataframe canvas dark) ----------

def _cmsi_table_css() -> str:
    """Inline CSS for the .cov HTML table. Self-contained (runs in iframe, so it
    does NOT inherit the page theme — every token must be inlined here)."""
    t = theme
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0; background: {t.PAPER}; color: {t.INK};
      font-family: {t.FONT_STACK}; font-size: 13px;
      font-feature-settings: 'tnum','ss01','cv11'; -webkit-font-smoothing: antialiased;
    }}
    .tbl-wrap {{ overflow: auto; background: {t.PAPER}; border: 1px solid {t.PAPER_EDGE}; }}
    table.cov {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    table.cov thead th {{
      background: {t.PAPER_BAND}; color: {t.CMSI_RED};
      font-size: 10px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600;
      padding: 9px 8px; text-align: right; border-bottom: 1px solid {t.CMSI_RED};
      white-space: nowrap; cursor: pointer; user-select: none;
      position: sticky; top: 0; z-index: 2;
    }}
    table.cov thead th.l {{ text-align: left; }}
    table.cov thead th .arr {{
      display: inline-block; width: 8px; color: {t.CMSI_RED}; margin-left: 3px;
      font-size: 9px;
    }}
    table.cov tbody td {{
      padding: 0 8px; height: 36px; text-align: right;
      font-variant-numeric: tabular-nums lining-nums;
      border-bottom: 1px solid {t.PAPER_RULE}; white-space: nowrap; color: {t.INK_2};
    }}
    table.cov tbody td.l {{ text-align: left; }}
    table.cov tbody tr:hover td {{ background: {t.PAPER_BAND}; }}
    table.cov td.tk {{
      font-family: {t.FONT_MONO}; font-weight: 700; color: {t.INK}; font-size: 12px;
      letter-spacing: .04em; text-align: left;
      position: sticky; left: 0; background: {t.PAPER};
      border-right: 1px solid {t.PAPER_EDGE}; z-index: 1;
    }}
    table.cov tr:hover td.tk {{ background: {t.PAPER_BAND}; }}
    table.cov thead th.tk {{
      position: sticky; left: 0; z-index: 3;
      border-right: 1px solid {t.PAPER_EDGE}; background: {t.PAPER_BAND};
    }}
    table.cov td.nm {{ color: {t.INK}; font-weight: 500; text-align: left; }}
    table.cov td.strong {{ color: {t.INK}; font-weight: 500; }}
    .up {{ color: {t.UP}; font-weight: 600; }}
    .down {{ color: {t.DOWN}; font-weight: 600; }}
    .flat {{ color: {t.INK_3}; }}
    a.srclink {{ color: {t.CMSI_RED}; text-decoration: none; font-weight: 700; font-size: 14px; }}
    a.srclink:hover {{ text-decoration: underline; }}
    .nm-muted {{ color: {t.INK_3}; }}
    .gly {{ display: inline-block; width: 8px; text-align: center; margin-right: 1px;
            font-size: 8px; vertical-align: 1px; }}
    table.cov tr.ref-row td {{ border-top: 2px solid {t.PAPER_EDGE}; font-style: italic; color: {t.INK_3}; }}
    """


# Vanilla JS: 3-state header click-sort (asc → desc → original). Sorts on the
# raw numeric in each cell's data-v attribute (never the formatted text), so
# '+12.4%' and '$1.2B' sort numerically. NaN/'—' rows sink to the bottom.
# Plain string (NOT an f-string) — JS template-literal ${...} must survive.
_CMSI_TABLE_JS = """
const tbl = document.getElementById('cov');
const tb = tbl.tBodies[0];
const orig = Array.from(tb.rows);
let curIdx = null, state = 0;           // 0 none, 1 asc, 2 desc
function paint(rows){ rows.forEach(r => tb.appendChild(r)); }
tbl.querySelectorAll('thead th').forEach((th, idx) => {
  if (th.dataset.sortable === '0') return;
  th.addEventListener('click', () => {
    if (curIdx === idx) state = (state + 1) % 3; else { curIdx = idx; state = 1; }
    tbl.querySelectorAll('thead th .arr').forEach(a => a.textContent = '');
    if (state === 0) { curIdx = null; paint(orig); return; }
    const arr = th.querySelector('.arr');
    if (arr) arr.textContent = state === 1 ? '\\u25B2' : '\\u25BC';
    const type = th.dataset.type;
    const sorted = [...orig].sort((ra, rb) => {
      let va = ra.cells[idx].dataset.v, vb = rb.cells[idx].dataset.v;
      let na = (va === '' || va == null), nb = (vb === '' || vb == null);
      let c;
      if (type === 'n') {
        const fa = parseFloat(va), fb = parseFloat(vb);
        na = na || Number.isNaN(fa); nb = nb || Number.isNaN(fb);
        if (na && nb) return 0; if (na) return 1; if (nb) return -1;
        c = fa - fb;
      } else {
        if (na && nb) return 0; if (na) return 1; if (nb) return -1;
        c = String(va).localeCompare(String(vb));
      }
      return state === 1 ? c : -c;
    });
    paint(sorted);
  });
});
"""


def _na(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, float) and pd.isna(v)) or v is pd.NA


def render_html_table(
    df: pd.DataFrame,
    *,
    pct_cols: list[str] | None = None,
    pct2_cols: list[str] | None = None,
    pct_decimal_cols: list[str] | None = None,
    mult_cols: list[str] | None = None,
    money_b_cols: list[str] | None = None,
    int_cols: list[str] | None = None,
    price_cols: list[str] | None = None,
    text_cols: list[str] | None = None,
    right_text_cols: list[str] | None = None,
    link_cols: list[str] | None = None,
    extra_formats: dict[str, str] | None = None,
    column_help: dict[str, str] | None = None,
    column_labels: dict[str, str] | None = None,
    height: int = 600,
    hide_index: bool = False,
    index_label: str | None = None,
    heatmap: bool = False,
    ref_rows: set | None = None,
) -> None:
    """Render `df` as an FT-editorial HTML table inside an iframe (components.html).

    Why an iframe and not st.markdown: st.dataframe is a glide-data-grid CANVAS —
    CSS can't reach the cells and OS dark-mode penetrates → black table. st.markdown
    strips <script>, killing click-sort. components.html runs a self-contained HTML
    doc in an iframe: full CSS control + working vanilla-JS sort + zero canvas.

    Signature mirrors render_styled_table so call sites migrate with minimal change.
    Coloring follows DESIGN.md: percentages color the TEXT (up=teal/down=red), never
    the cell background. Numbers are right-aligned tabular-nums; text is left.

    Column kinds (a column may appear in exactly one list):
      pct_cols          values already in pct units (12.4 → "+12.4%"), sign-colored
      pct_decimal_cols  values in decimal (0.025 → "+2.5%"), sign-colored
      mult_cols         ratio "14.2x"; NaN/≤0 → "NM" (muted)
      money_b_cols      value already in USD billions → "$18.2B" (ink-strong)
      int_cols          integer "%d"
      price_cols        comma price "%,.2f"
      text_cols         left-aligned text (escaped)
    The DataFrame index becomes the sticky first column (mono). Pass hide_index=True
    to drop it. `column_help` → <th title="…"> tooltip (defaults to COLUMN_HELP).
    `column_labels` overrides a column's header text.
    """
    pct_cols = set(pct_cols or [])
    pct2_cols = set(pct2_cols or [])
    pct_decimal_cols = set(pct_decimal_cols or [])
    mult_cols = set(mult_cols or [])
    money_b_cols = set(money_b_cols or [])
    int_cols = set(int_cols or [])
    price_cols = set(price_cols or [])
    text_cols = set(text_cols or [])
    right_text_cols = set(right_text_cols or [])
    link_cols = set(link_cols or [])
    extra_formats = extra_formats or {}
    column_help = COLUMN_HELP if column_help is None else column_help
    column_labels = column_labels or {}

    cols = list(df.columns)

    def _heat(pct_val) -> str:
        """≤12% tint bg for heatmap mode (DESIGN.md §4.2 / §0.4). pct_val in
        percent units; teal=up, red=down, layered UNDER the text color."""
        if not heatmap or _na(pct_val):
            return ""
        a = min(abs(pct_val) / 20.0, 1.0) * 0.12
        if pct_val > 0:
            return f"background:rgba(13,118,128,{a:.3f});"
        if pct_val < 0:
            return f"background:rgba(204,0,0,{a:.3f});"
        return ""

    def _pct_cell(v, decimals=1):
        if _na(v):
            return '<span class="flat">—</span>', "", ""
        cls = "up" if v > 0 else ("down" if v < 0 else "flat")
        gly = "▲" if v > 0 else ("▼" if v < 0 else "·")
        sign = "+" if v > 0 else ("" if v < 0 else "")
        inner = (f'<span class="{cls}"><span class="gly">{gly}</span>'
                 f'{sign}{v:.{decimals}f}%</span>')
        return inner, float(v), _heat(v)

    def _cell(col, v):
        """Return (inner_html, sort_value, td_class, sortable_type, bg_style)."""
        # extra_formats wins over kind lists — matches the old column_config
        # precedence (e.g. Valuation 'Sector P/E %ile' is in BOTH mult_cols and
        # extra_formats, and the printf format must win).
        if col in link_cols:
            # value is a URL → clickable ↗ opening in a new tab (works inside the iframe)
            s = "" if _na(v) else str(v)
            if s.startswith("http"):
                return (f'<a class="srclink" href="{_html.escape(s)}" target="_blank" '
                        f'rel="noopener">↗</a>', "1", "", "s", "")
            return '<span class="flat">—</span>', "", "", "s", ""
        if col in right_text_cols:
            # value already formatted by caller (unit-aware) — right-align + ink-strong
            s = '<span class="flat">—</span>' if _na(v) else _html.escape(str(v))
            return s, ("" if _na(v) else str(v).lower()), "strong", "s", ""
        if col in text_cols:
            s = "" if _na(v) else _html.escape(str(v))
            return s, ("" if _na(v) else str(v).lower()), "l nm", "s", ""
        if col in extra_formats:
            if _na(v):
                return '<span class="flat">—</span>', "", "", "n", ""
            try:
                return _html.escape(extra_formats[col] % v), float(v), "", "n", ""
            except (TypeError, ValueError):
                return _html.escape(str(v)), str(v).lower(), "l", "s", ""
        if col in money_b_cols:
            if _na(v):
                return '<span class="flat">—</span>', "", "strong", "n", ""
            return f"${v:,.1f}B", float(v), "strong", "n", ""
        if col in pct_cols:
            inner, sv, bg = _pct_cell(v, 1)
            return inner, sv, "", "n", bg
        if col in pct2_cols:
            inner, sv, bg = _pct_cell(v, 2)
            return inner, sv, "", "n", bg
        if col in pct_decimal_cols:
            inner, sv, bg = _pct_cell(v * 100 if not _na(v) else v, 2)
            return inner, sv, "", "n", bg
        if col in mult_cols:
            if _na(v) or v <= 0:
                return '<span class="nm-muted">NM</span>', "", "", "n", ""
            return f"{v:.1f}x", float(v), "", "n", ""
        if col in int_cols:
            if _na(v):
                return '<span class="flat">—</span>', "", "", "n", ""
            return f"{int(round(v))}", float(v), "", "n", ""
        if col in price_cols:
            if _na(v):
                return '<span class="flat">—</span>', "", "", "n", ""
            return f"{v:,.2f}", float(v), "", "n", ""
        # default: numeric → 2dp, else text
        if isinstance(v, (int, float)) and not _na(v):
            return f"{v:,.2f}", float(v), "", "n", ""
        s = "" if _na(v) else _html.escape(str(v))
        return s, ("" if _na(v) else str(v).lower()), "l", "s", ""

    # ---- header row ----
    th_parts = []
    if not hide_index:
        idx_lbl = _html.escape(index_label or (df.index.name or "Ticker"))
        th_parts.append(
            f'<th class="l tk" data-type="s"><span class="lbl">{idx_lbl}</span>'
            f'<span class="arr"></span></th>'
        )
    for col in cols:
        # infer sort type + alignment from kind (sample first non-null value)
        sample = df[col].dropna().iloc[0] if df[col].notna().any() else None
        _, _, td_cls, stype, _ = _cell(col, sample)
        align = "l" if "l" in td_cls.split() else ""
        label = _html.escape(column_labels.get(col, str(col)))
        help_txt = column_help.get(col, "")
        title = f' title="{_html.escape(help_txt)}"' if help_txt else ""
        th_parts.append(
            f'<th class="{align}" data-type="{stype}"{title}>'
            f'<span class="lbl">{label}</span><span class="arr"></span></th>'
        )
    thead = "<tr>" + "".join(th_parts) + "</tr>"

    # ---- body rows ----
    tr_parts = []
    for idx, row in df.iterrows():
        tds = []
        if not hide_index:
            idx_disp = _html.escape(str(idx))
            tds.append(f'<td class="tk" data-v="{_html.escape(str(idx).lower())}">{idx_disp}</td>')
        for col in cols:
            inner, sv, td_cls, _, bg = _cell(col, row[col])
            sv_attr = _html.escape(str(sv)) if sv != "" else ""
            cls_attr = f' class="{td_cls}"' if td_cls else ""
            style_attr = f' style="{bg}"' if bg else ""
            tds.append(f'<td{cls_attr}{style_attr} data-v="{sv_attr}">{inner}</td>')
        tr_cls = ' class="ref-row"' if (ref_rows is not None and idx in ref_rows) else ""
        tr_parts.append(f"<tr{tr_cls}>" + "".join(tds) + "</tr>")
    tbody = "".join(tr_parts)

    nrows = len(df)
    content_h = 44 + nrows * 36 + 4
    iframe_h = min(content_h, height)
    wrap_h = iframe_h - 2

    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_cmsi_table_css()}"
        f".tbl-wrap{{max-height:{wrap_h}px;}}</style></head><body>"
        f'<div class="tbl-wrap"><table class="cov" id="cov">'
        f"<thead>{thead}</thead><tbody>{tbody}</tbody></table></div>"
        f"<script>{_CMSI_TABLE_JS}</script>"
        "</body></html>"
    )
    # st.iframe (Streamlit 1.58+) auto-detects HTML-string content and renders it
    # via srcdoc — keeps <script> alive (unlike st.html / st.markdown which strip
    # it). Replaces st.components.v1.html, removed after 2026-06-01.
    st.iframe(doc, height=iframe_h)


def render_concept_table(
    ts: pd.DataFrame,
    *,
    value_formatter,
    labels: dict[str, str] | None = None,
    max_rows: int = 12,
) -> None:
    """SEC concept time-series → house editorial HTML table (warm, not dark).

    `ts` is sec_facts.concept_timeseries output: columns
    [end_date, value, fy, fp, form, unit, yoy(, qoq)] with yoy/qoq already in
    percent units. `value_formatter(v) -> str` renders each value unit-aware
    (pass the page's `_fmt_val` bound to the concept unit, so the table matches
    the KPI cards). yoy/qoq stay numeric so they get teal-up / red-down coloring.
    `labels` keys: end_date, fy, fp, value, yoy, qoq.
    """
    if ts is None or ts.empty:
        return
    labels = labels or {}
    t = ts.sort_values("end_date", ascending=False).head(max_rows).copy()

    fy_l = labels.get("fy", "FY")
    fp_l = labels.get("fp", "FP")
    val_l = labels.get("value", "Value")

    disp = pd.DataFrame(index=t["end_date"].astype(str))
    disp[fy_l] = [str(int(x)) if pd.notna(x) else "—" for x in t["fy"]]
    disp[fp_l] = t["fp"].fillna("—").astype(str).to_numpy()
    disp[val_l] = [value_formatter(v) for v in t["value"]]

    pct_label_cols: list[str] = []
    if "yoy" in t.columns:
        yoy_l = labels.get("yoy", "YoY %")
        disp[yoy_l] = t["yoy"].to_numpy()
        pct_label_cols.append(yoy_l)
    if "qoq" in t.columns:
        qoq_l = labels.get("qoq", "QoQ %")
        disp[qoq_l] = t["qoq"].to_numpy()
        pct_label_cols.append(qoq_l)

    disp.index.name = labels.get("end_date", "End")
    render_html_table(
        disp,
        pct_cols=pct_label_cols,
        text_cols=[fp_l, fy_l],
        right_text_cols=[val_l],
        index_label=labels.get("end_date", "End"),
    )
