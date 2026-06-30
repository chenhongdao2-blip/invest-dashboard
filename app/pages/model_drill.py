"""Model Drill — analyst-model financial visualization + LLM Wiki, one company per page.

Deep-linked: /Model_Drill?ticker=VEEV (click-through from CMSI Coverage etc.).
Reads data/models/<TICKER>.json (produced by jobs/extract_model.py). Model data
SHIPS to public Cloud ("上云透明", George 2026-06-02) — the analyst view is the
product. When a ticker has no extract, has_model() is False and the page degrades
gracefully to a pointer at Ticker Drill / SEC Facts.

Three honesty tiers run through the page (design doc 2026-06-01):
  GAAP 申报 (HIGH) · 分析师 model view (MEDIUM) · forecast (FYxxE, never bare).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import charts
from lib import db
from lib import i18n
from lib import model_view
from lib import theme
from lib import ui
from lib import wiki

st.set_page_config(page_title="Model Drill · invest-dashboard", page_icon="📊", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()
prefer_cn = i18n.get_lang() == "zh"

# sidebar_search() injects the house CSS (cream/FT theme + cmsi-kpi cards) — every
# page must call it or the page falls back to Streamlit's default dark canvas.
with st.sidebar:
    ui.sidebar_search(key_prefix="model_drill")

theme.page_header(i18n.t("model.title"))
st.caption(i18n.t("model.intro"))

# ── ticker resolution: query_params → global_ticker → selectbox ──
avail = model_view.available_models()
if "global_ticker" not in st.session_state:
    st.session_state.global_ticker = ""
qp = st.query_params.get("ticker", "")
if isinstance(qp, list):
    qp = qp[0] if qp else ""
if qp:
    st.session_state.global_ticker = qp

if not avail:
    # No model extracts on disk (e.g. public Cloud) — degrade, don't crash.
    st.caption(i18n.t("model.none_any"))
    st.stop()

cur = st.session_state.global_ticker
default_idx = avail.index(cur) if cur in avail else 0
ticker = st.selectbox(i18n.t("model.pick"), avail, index=default_idx, key="model_pick")
st.session_state.global_ticker = ticker

m = model_view.load_model(ticker)
if m is None:
    st.warning(i18n.t("model.no_model", ticker=ticker))
    st.markdown(f"[{i18n.t('model.fallback_link')}](/Ticker_Drill?ticker={ticker})")
    st.stop()

meta = m["meta"]
periods = m["periods"]
dcf = m.get("dcf")
wp = wiki.find_wiki(ticker)


def _card(label: str, value: str, sub: str, vcls: str = "") -> str:
    return ('<div class="cmsi-kpi">'
            f'<div class="cmsi-kpi-head"><span class="cmsi-kpi-label ipo">{label}</span></div>'
            f'<div class="cmsi-kpi-num {vcls}">{value}</div>'
            f'<div class="cmsi-kpi-foot ink">{sub}</div></div>')


# ── header: company + model provenance + DCF cards ──
st.markdown(f"### {meta.get('company', ticker)} · `{ticker}`")
st.caption(i18n.t("model.as_of", ver=meta.get("model_version", "—"), src=meta.get("source", "")))
if meta.get("public"):
    st.caption(i18n.t("model.public_desensitized"))

if dcf and dcf.get("target_price") and dcf.get("current_price"):
    tp = dcf["target_price"]
    # 现价 = latest close from the price DB, NOT the model's frozen price (which is
    # struck at model-build time and goes stale — George 2026-06-01). Falls back to
    # the model reference price + model date only when the ticker has no price
    # history on file (e.g. some HK names not in the universe).
    ref_price = dcf["current_price"]
    live, asof = None, None
    _cs = db.get_close_series((ticker,))
    if not _cs.empty and ticker in _cs.columns:
        _ser = _cs[ticker].dropna()
        if not _ser.empty:
            live = float(_ser.iloc[-1])
            asof = _ser.index[-1].date().isoformat()
    pr = live if live is not None else ref_price
    price_sub = (i18n.t("model.as_of_date", d=asof) if asof
                 else meta.get("model_version", ""))
    up = (tp / pr - 1) * 100 if pr else float("nan")
    theme.kpi_strip([
        _card(i18n.t("model.tp"), f"${tp:,.0f}",
              i18n.t("model.dcf_sub", wacc=f"{dcf.get('wacc', 0):.1%}",
                     tg=f"{dcf.get('terminal_growth', 0):.1%}"), "up-deep"),
        _card(i18n.t("model.price"), f"${pr:,.2f}", price_sub),
        _card(i18n.t("model.upside"), f"{up:+.0f}%", i18n.t("model.upside_sub"),
              "up" if up >= 0 else ""),
    ])
    # the model's base-case reference price (where the DCF upside was originally
    # struck) — kept as provenance now that 现价 shows the live close.
    if live is not None and abs(ref_price - live) > 1e-9:
        st.caption(i18n.t("model.model_ref", p=f"${ref_price:,.0f}",
                          ver=meta.get("model_version", "")))

# wiki rating/TP — demoted to a hairline meta strip (the full thesis lives on
# Ticker Drill; this page is the numbers, so the house view is just an anchor).
if wp and (wp.rating or wp.tp):
    _meta_items = []
    if wp.rating:
        _meta_items.append((i18n.t("model.rating"), wp.rating))
    if wp.tp:
        _meta_items.append((i18n.t("model.wiki_tp"), wp.tp))
    theme.memo_meta_bar(_meta_items)

# ── period-frequency toggle (annual ↔ quarterly) — drives ①②③ only ──
# Quarterly is code-to-code from the analyst model's quarterly columns (segment
# splits + forecast that SEC GAAP can't give). DCF/EV/Rule-of-40 stay annual.
_periods_q = m.get("periods_q") or []
_quarterly = False
if _periods_q:
    _opts = [i18n.t("model.freq_year"), i18n.t("model.freq_quarter")]
    _sel = st.segmented_control(i18n.t("model.freq"), _opts, default=_opts[0],
                                key="model_freq")
    _quarterly = (_sel == _opts[1])

if _quarterly:
    axis = _periods_q
    _fe = next((i for i, p in enumerate(axis) if p["actual_est"] == "E"), len(axis))
    line_ax = axis[max(0, _fe - 12):_fe + 8]                 # ②③ window (~20 q)
    _rev_src = axis[max(0, _fe - 8):_fe + 6]                 # ① window (~14 q)
else:
    axis = periods
    line_ax = periods                                        # ②③ full annual (unchanged)
    _fe = next((i for i, p in enumerate(periods) if p["actual_est"] == "E"), len(periods))
    _rev_src = periods[max(0, _fe - 4):_fe + 2]              # ① 4 actual + 2 forecast
_rev_window = [p["label"] for p in _rev_src]

# ── ① Revenue breakdown ──
theme.section_header(i18n.t("model.sec.revenue"))
st.plotly_chart(charts.model_revenue_chart(m["revenue_breakdown"], axis,
                                            prefer_cn=prefer_cn, window=_rev_window),
                width="stretch", theme=None)
st.caption(i18n.t("model.revenue_cap"))

# ── ② Margins + GAAP→non-GAAP bridge ──
theme.section_header(i18n.t("model.sec.margin"))
_want = {("gross_margin", "gaap"), ("operating_margin", "gaap"),
         ("operating_margin", "non_gaap"), ("net_margin", "non_gaap")}
_msel = [mg for mg in m["margins"] if (mg["metric"], mg["basis"]) in _want]
st.plotly_chart(charts.model_margin_chart(_msel, line_ax, prefer_cn=prefer_cn),
                width="stretch", theme=None)
st.caption(i18n.t("model.margin_cap"))
if m.get("gaap_bridge"):
    with st.expander(i18n.t("model.bridge_expand")):
        st.plotly_chart(charts.model_bridge_chart(m["gaap_bridge"], prefer_cn=prefer_cn),
                        width="stretch", theme=None)

# ── ③ Forecast + DCF ──
# EPS line only (revenue already lives in ① — no redundant revenue bar here).
theme.section_header(i18n.t("model.sec.forecast"))
st.plotly_chart(charts.model_forecast_chart(m["forecast"], line_ax, prefer_cn=prefer_cn,
                                            bar_line=None),
                width="stretch", theme=None)
if dcf:
    # EV value-map FIRST (where value comes from — echoes ①'s R&D%).
    evb = dcf.get("ev_breakdown") or []
    if evb:
        st.caption(i18n.t("model.ev_title"))
        for col, e in zip(st.columns(len(evb)), evb):
            npv = e.get("npv") or 0   # stored in USD millions → show in billions
            col.metric(e["segment"], f"${npv / 1000:,.1f}B",
                       f"{(e.get('pct') or 0):.0%}", delta_color="off")
    note = dcf.get("scenario_note_cn")
    if note:
        with st.expander(i18n.t("model.scenario")):
            st.markdown(note)

# ── ⑤ Analyst ratios — the divisions / multiples / forecasts SEC GAAP can't give.
# Annual is the source of truth; in 季度 mode we keep it simple (spec §GROUPED
# TABLES v1): always show the annual table, add a note, and show quarterly columns
# only for 口径-safe (freq="q") metrics. No per-cell greying.
_ratios = m.get("ratios")
if _ratios and _ratios.get("groups"):

    def _ratio_axis():
        """Last 3 annual periods (FY n-2 · n-1 · nE) ending at the first forecast."""
        _fe_a = next((i for i, p in enumerate(periods) if p["actual_est"] == "E"),
                     len(periods))
        return periods[max(0, _fe_a - 2):_fe_a + 1]

    def _fmt_ratio(v, fmt: str) -> str:
        if v is None or (isinstance(v, float) and v != v):
            return "—"
        if fmt == "mult":
            return f"{v:.1f}x"
        if fmt == "pct":
            return f"{v * 100:.1f}%"
        if fmt == "days":
            return f"{v:.0f}{'天' if prefer_cn else 'd'}"
        if fmt == "ps":
            return f"${v:.2f}"
        if fmt == "ratio":
            return f"{v:.2f}x"
        if fmt == "int":
            return f"{int(round(v)):,}"
        if fmt == "bn":
            return f"${v / 1000:.2f}B"
        return f"{v:.2f}"

    def _mname(mt) -> str:
        return mt["cn"] if prefer_cn else mt["en"]

    # last 3-4 quarters ending at the first forecast quarter (for q-safe metrics).
    def _q_axis():
        if not _periods_q:
            return []
        _feq = next((i for i, p in enumerate(_periods_q) if p["actual_est"] == "E"),
                    len(_periods_q))
        return _periods_q[max(0, _feq - 3):_feq + 1]

    theme.section_header(i18n.t("model.sec.ratios"))
    st.caption(f"**{i18n.t('model.ratios_tag')}** · {i18n.t('model.ratios_cap')}")

    # ── 6 hero cards: latest ACTUAL annual big number + FY(n-2)→(n-1)→(n)E path ──
    _ann = _ratio_axis()
    _ann_lbls = [p["label"] for p in _ann]
    _by_key = {mt["key"]: mt for g in _ratios["groups"] for mt in g["metrics"]}
    # latest ACTUAL annual label (last non-E in the full annual axis).
    _last_actual = next((p["label"] for p in reversed(periods)
                         if p["actual_est"] == "A"), _ann_lbls[-1] if _ann_lbls else None)
    _hero = ["adj_pe", "ev_sales", "op_margin_ng", "fcf_margin", "roic", "billings_growth"]
    _cards = []
    for hk in _hero:
        mt = _by_key.get(hk)
        if not mt:
            continue
        vals = mt["values"]
        big = _fmt_ratio(vals.get(_last_actual), mt["fmt"]) if _last_actual else "—"
        # mini path: strip the unit suffix so "59→43→43x" reads cleanly.
        path_raw = [_fmt_ratio(vals.get(l), mt["fmt"]) for l in _ann_lbls]
        suf = ""
        for s in ("x", "%", "天", "d", "B"):
            if path_raw and path_raw[-1].endswith(s):
                suf = s
                break
        nums = []
        for s in path_raw:
            if s == "—":
                nums.append("—")
            else:
                t_ = s
                for s2 in ("x", "%", "天", "d", "B", "$"):
                    t_ = t_.replace(s2, "")
                nums.append(t_.strip())
        sub = "→".join(nums) + suf
        _cards.append(_card(_mname(mt), big, sub, "up-deep"))
    if _cards:
        theme.kpi_strip(_cards)

    # ── grouped tables (one per group) ──
    _gtitle = {"valuation": "model.ratios.g.valuation",
               "profitability": "model.ratios.g.profitability",
               "efficiency": "model.ratios.g.efficiency",
               "cash": "model.ratios.g.cash",
               "operational": "model.ratios.g.operational"}
    _metric_col = i18n.t("model.ratios_metric_col")
    if _quarterly:
        st.caption(i18n.t("model.ratios_q_note"))
    for g in _ratios["groups"]:
        gt = i18n.t(_gtitle.get(g["key"], "")) or (g["cn"] if prefer_cn else g["en"])
        st.markdown(f"**{gt}**")
        if _quarterly and _q_axis():
            # q-safe subset only, quarterly columns
            qax = _q_axis()
            qlbls = [p["label"] for p in qax]
            rows = {}
            qmetrics = [mt for mt in g["metrics"] if mt.get("freq") == "q"]
            if not qmetrics:
                st.caption(i18n.t("model.ratios_annual_only"))
                continue
            for mt in qmetrics:
                rows[_mname(mt)] = [_fmt_ratio(mt["values"].get(l), mt["fmt"]) for l in qlbls]
            df = pd.DataFrame.from_dict(rows, orient="index", columns=qlbls)
            df.index.name = _metric_col
            ui.render_html_table(df, right_text_cols=qlbls, index_label=_metric_col,
                                 height=60 + len(df) * 36)
        else:
            rows = {}
            for mt in g["metrics"]:
                rows[_mname(mt)] = [_fmt_ratio(mt["values"].get(l), mt["fmt"]) for l in _ann_lbls]
            df = pd.DataFrame.from_dict(rows, orient="index", columns=_ann_lbls)
            df.index.name = _metric_col
            ui.render_html_table(df, right_text_cols=_ann_lbls, index_label=_metric_col,
                                 height=60 + len(df) * 36)

# ── Rule-of-40 valuation matrix (replaces the WACC×TG sensitivity grid; George
# 2026-06-01). Software/SaaS comp cloud (EV/Sales vs growth+FCF margin) read live
# from the daily snapshot → dynamic. Highlights the current ticker if it's a comp.
_comps = tuple(db.sector_tickers("software", "saas_comps")["ticker"].tolist())
if _comps:
    theme.section_header(i18n.t("model.sec.r40"))
    _r40 = db.rule_of_40_comps(_comps)
    if _r40.empty:
        st.caption(i18n.t("model.r40_none"))
    else:
        st.plotly_chart(
            charts.rule_of_40_scatter(_r40, highlight=ticker, prefer_cn=prefer_cn),
            width="stretch", theme=None)
        st.caption(i18n.t("model.r40_cap", n=len(_r40),
                          d=db.latest_snapshot_date() or "—"))

# ── LLM Wiki thesis intentionally NOT shown here (George 2026-06-01): the full
# research view lives on Ticker Drill (个股详情); duplicating it bloated this page.
# Model Drill = the numbers; the header keeps only a compact rating/TP chip above.
# A link to the thesis page lives in the footer below.

st.divider()
st.caption(i18n.t("model.disclaimer", src=meta.get("source_file", "")))
st.markdown(f"[{i18n.t('model.see_thesis')}](/Ticker_Drill?ticker={ticker})")
