"""AI · SEC Company Facts — KPI cards + fact browser + concept time-series + comp export.

Mirror of `8_📋_SEC_Facts.py` scoped to AI-domain US-listed names (domain='ai').
US AI tickers auto-enter the SEC pool via jobs/fetch_sec_facts.py; until that fetch
lands this page is empty-data safe (empty pool → info prompt; un-fetched ticker →
the standard "not cached yet" warning).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n
from lib import sec_facts as sf
from lib import charts

st.set_page_config(
    page_title="AI SEC Facts · invest-dashboard",
    page_icon="📋",
    layout="wide",
)


def _fmt_val(v, unit: str) -> str:
    """Unit-aware value format (shared by KPI cards and comp-table preview)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    unit = unit or ""
    if "shares" in unit and "/" in unit:        # USD/shares → EPS (per-share)
        return f"${v:,.2f}"
    if unit == "USD" or unit.startswith("USD"):
        return fmt.fmt_money_b(v)
    if "shares" in unit:                        # raw share counts
        return fmt.fmt_money_b(v).lstrip("$")
    return f"{v:,.2f}"


def _fmt_kpi(fact: dict | None) -> str:
    """Format a KPI fact value by unit kind."""
    if fact is None or fact.get("value") is None:
        return "—"
    return _fmt_val(fact["value"], fact.get("unit") or "")


# ── sidebar + lang ──
i18n.init_lang()
with st.sidebar:
    ui.sidebar_search(key_prefix="ai_sec")
i18n.render_lang_toggle()
theme.page_header(i18n.t("ai.sec.title"))
st.caption(i18n.t("ai.sec.caption"))

# AI-domain US-listed pool only (US AI names auto-enter the SEC fetch pool)
pool = sf.us_pool()
pool = pool[pool["domain"] == "ai"].copy()
us_tickers = pool["ticker"].tolist()
prefer_cn = i18n.get_lang() == "zh"
name_map = db.ticker_to_name(prefer_cn=prefer_cn)

if not us_tickers:
    st.caption(i18n.t("sec.pick_prompt"))
    st.stop()

# ── ticker selection (US AI pool only) + deep-link ──
if "global_ticker" not in st.session_state:
    st.session_state.global_ticker = ""
url_ticker = st.query_params.get("ticker", "")
if isinstance(url_ticker, list):
    url_ticker = url_ticker[0] if url_ticker else ""
if url_ticker and url_ticker in us_tickers:
    st.session_state.global_ticker = url_ticker

default_idx = 0
cur = st.session_state.global_ticker
options = [""] + us_tickers
if cur in us_tickers:
    default_idx = options.index(cur)

pick = st.selectbox(
    i18n.t("sec.choose"),
    options=options,
    index=default_idx,
    format_func=lambda t: "" if t == "" else f"{name_map.get(t, t)} · {fmt.fmt_ticker_bbg(t)}",
    key="ai_sec_pick",
)
if pick:
    st.session_state.global_ticker = pick
ticker = st.session_state.global_ticker

if not ticker:
    st.caption(i18n.t("sec.pick_prompt"))
    st.stop()

if ticker not in us_tickers:
    st.warning(i18n.t("sec.warn.non_us", ticker=ticker))
    st.stop()

status = sf.company_status(ticker)
sec_status = (status or {}).get("sec_status")
if status is None or not sec_status:
    st.warning(i18n.t("sec.warn.not_fetched", ticker=ticker))
    st.stop()
if sec_status in ("not_mapped", "no_xbrl"):
    st.warning(i18n.t("sec.warn.no_xbrl", ticker=ticker))
    st.stop()
if sec_status == "failed":
    st.warning(i18n.t("sec.warn.not_fetched", ticker=ticker))
    st.stop()

# ── freshness badges ──
badges = [
    i18n.t("sec.badge.taxonomy", tax=status.get("taxonomy_primary") or "—"),
    i18n.t("sec.badge.latest_filed", filed=status.get("latest_filed") or "—"),
    i18n.t("sec.badge.fetched", fetched=(status.get("fetched_at") or "—")[:10]),
]
st.caption(" · ".join(badges))

# period basis toggle
period = st.segmented_control(
    i18n.t("sec.period.label"),
    options=["annual", "quarterly"],
    format_func=lambda p: i18n.t(f"sec.period.{p}"),
    default="annual",
    key="ai_sec_period",
)
period = period or "annual"

# domain for this ticker (drives which KPI overlay shows)
domain = pool.set_index("ticker")["domain"].get(ticker)

# ══════════════════════════════════════════════════════════════════════════
# ① KPI cards (domain-aware) + auditable source trace
# ══════════════════════════════════════════════════════════════════════════
theme.section_header(i18n.t("sec.section.kpi"))
kpis = sf.kpis_for_domain(domain)
label_field = "label_cn" if prefer_cn else "label_en"
facts: dict[str, dict | None] = {k["kpi_key"]: sf.pick_kpi_fact(ticker, k["kpi_key"], period) for k in kpis}

cards = []
for k in kpis:
    f = facts[k["kpi_key"]]
    foot = ""
    if f:
        foot = f"{f['form']} · {f.get('fp') or ''} {f.get('end_date') or ''}".strip()
        if f.get("is_fallback"):
            foot += f" · {i18n.t('sec.kpi.fallback')}"
    cards.append(theme.kpi_metric(k[label_field], _fmt_kpi(f), foot=foot or None))

# render in rows of 4
for i in range(0, len(cards), 4):
    theme.kpi_strip(cards[i:i + 4])

# auditable "why this value" trace
with st.expander("ⓘ " + i18n.t("sec.kpi.trace", concept="…", form="", fy="", fp="", end="", filed="", accn="").split("：")[0].split(":")[0]):
    trace_rows = []
    for k in kpis:
        f = facts[k["kpi_key"]]
        if not f:
            continue
        trace_rows.append({
            i18n.t("sec.section.kpi"): k[label_field],
            i18n.t("sec.col.concept"): f"{f['taxonomy']}:{f['concept']}",
            i18n.t("sec.col.form"): f["form"],
            i18n.t("sec.col.end"): f["end_date"],
            i18n.t("sec.col.filed"): f["filed"],
            "accession": f["accession"],
        })
    if trace_rows:
        _tdf = pd.DataFrame(trace_rows).set_index(i18n.t("sec.section.kpi"))
        ui.render_html_table(
            _tdf,
            text_cols=list(_tdf.columns),
            index_label=i18n.t("sec.section.kpi"),
            height=360,
        )

# ── Financial statements summary (三大报表摘要 · built from XBRL facts) ──
from lib import sec_statements
sec_statements.statements_section(
    ticker, status.get("taxonomy_primary") or "us-gaap", prefer_cn, freq=period, domain=domain
)

# ══════════════════════════════════════════════════════════════════════════
# ③ concept time-series (QoQ / YoY)
# ══════════════════════════════════════════════════════════════════════════
theme.section_header(i18n.t("sec.section.timeseries"))
all_df = sf.all_facts(ticker)

ts_opts: list[tuple[str, str, str]] = []
if not all_df.empty:
    grp = (
        all_df[all_df["value"].notna()]
        .groupby(["taxonomy", "concept", "unit"])["end_date"].nunique()
    )
    for (tax, concept, unit), n in grp.items():
        if n >= 2:
            ts_opts.append((tax, concept, unit))
    # curated/common concepts (those with a 中文名) first, long-tail raw tags after;
    # within each group keep primary-taxonomy ahead, then alphabetical by concept.
    ts_opts.sort(key=lambda x: (not bool(sf.concept_cn(x[1])), x[0] != (status.get("taxonomy_primary") or ""), x[1]))

if ts_opts:
    default_ts = 0
    for i, (_, c, _) in enumerate(ts_opts):
        if "Revenue" in c:
            default_ts = i
            break

    def _ts_label(i: int) -> str:
        tax, concept, unit = ts_opts[i]
        cn = sf.concept_cn(concept) if prefer_cn else ""
        prefix = f"{cn} · " if cn else ""
        return f"{prefix}{tax}:{concept} ({unit})"

    sel = st.selectbox(
        i18n.t("sec.ts.pick"),
        options=range(len(ts_opts)),
        index=default_ts,
        format_func=_ts_label,
        key="ai_sec_ts_concept",
    )
    tax, concept, unit = ts_opts[sel]
    ts = sf.concept_timeseries(ticker, tax, concept, unit, freq=period)
    if ts.empty:
        st.caption(i18n.t("sec.ts.empty"))
    else:
        # readable axis: scale USD / share counts to bn/mn (raw values are huge)
        scale, scale_lbl = 1.0, unit
        _mx = ts["value"].abs().max()
        if unit == "USD":
            if _mx >= 1e9:
                scale, scale_lbl = 1e9, "USD (bn)"
            elif _mx >= 1e6:
                scale, scale_lbl = 1e6, "USD (mn)"
        elif "shares" in (unit or "") and "/" not in (unit or ""):
            if _mx >= 1e9:
                scale, scale_lbl = 1e9, "Shares (bn)"
            elif _mx >= 1e6:
                scale, scale_lbl = 1e6, "Shares (mn)"
        _disp = (sf.concept_cn(concept) if prefer_cn else "") or concept
        plot_df = (
            ts.set_index(pd.to_datetime(ts["end_date"]))[["value"]] / scale
        ).rename(columns={"value": _disp})
        fig = charts.price_line_chart(plot_df, title=f"{_disp} ({unit})", ylabel=scale_lbl)
        fig.update_layout(showlegend=False)   # single series → drop redundant legend
        st.plotly_chart(fig, width="stretch", theme=None)
        ui.render_concept_table(
            ts,
            value_formatter=lambda v: _fmt_val(v, unit),
            labels={
                "end_date": i18n.t("sec.col.end"),
                "fy": i18n.t("sec.col.fy"),
                "fp": i18n.t("sec.col.fp"),
                "value": i18n.t("sec.col.value"),
                "yoy": i18n.t("sec.ts.yoy"),
                "qoq": i18n.t("sec.ts.qoq"),
            },
        )
else:
    st.caption(i18n.t("sec.ts.empty"))

# ══════════════════════════════════════════════════════════════════════════
# ③ full fact browser
# ══════════════════════════════════════════════════════════════════════════
theme.section_header(i18n.t("sec.section.browser"))
_raw_title = "展开全量 XBRL 字段（搜索 / 筛选 / 导出）" if prefer_cn else "Expand raw XBRL fields (search / filter / export)"
with st.expander(_raw_title, expanded=False):
    if all_df.empty:
        st.caption(i18n.t("sec.ts.empty"))
    else:
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        q = fc1.text_input(i18n.t("sec.browser.search"), key="ai_sec_browse_q")
        form_opts = ["(all)"] + sorted(x for x in all_df["form"].dropna().unique())
        tax_opts = ["(all)"] + sorted(all_df["taxonomy"].dropna().unique())
        sel_form = fc2.selectbox(i18n.t("sec.browser.form"), form_opts, key="ai_sec_browse_form")
        sel_tax = fc3.selectbox(i18n.t("sec.browser.taxonomy"), tax_opts, key="ai_sec_browse_tax")

        view = all_df.copy()
        if q:
            ql = q.lower()
            mask = view["concept"].str.lower().str.contains(ql, na=False) | view["label"].str.lower().str.contains(ql, na=False)
            view = view[mask]
        if sel_form != "(all)":
            view = view[view["form"] == sel_form]
        if sel_tax != "(all)":
            view = view[view["taxonomy"] == sel_tax]

        st.caption(i18n.t("sec.browser.shown", shown=len(view), total=len(all_df)))

        disp = view.rename(columns={
            "concept": "Concept", "taxonomy": "Taxonomy", "unit": "Unit", "value": "Value",
            "start_date": "Start", "end_date": "End", "form": "Form", "fy": "FY", "filed": "Filed",
        })[["Concept", "Taxonomy", "Unit", "Value", "Start", "End", "Form", "FY", "Filed"]].copy()
        if prefer_cn:
            disp.insert(1, "ConceptCN", disp["Concept"].map(sf.concept_cn))
        disp = disp.sort_values(["Filed", "Concept"], ascending=[False, True]).reset_index(drop=True)

        st.download_button(
            i18n.t("sec.browser.dl"),
            data=disp.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"sec_facts_{ticker}.csv",
            mime="text/csv",
        )
        col_cfg = {
            "Concept": i18n.t("sec.col.concept"), "Taxonomy": i18n.t("sec.col.taxonomy"),
            "Unit": i18n.t("sec.col.unit"), "Value": i18n.t("sec.col.value"),
            "Start": i18n.t("sec.col.start"), "End": i18n.t("sec.col.end"),
            "Form": i18n.t("sec.col.form"), "FY": i18n.t("sec.col.fy"), "Filed": i18n.t("sec.col.filed"),
        }
        if prefer_cn:
            col_cfg["ConceptCN"] = i18n.t("sec.col.concept_cn")
        rdf = disp.head(500).copy()
        rdf["Value"] = [_fmt_val(v, u) for v, u in zip(rdf["Value"], rdf["Unit"])]
        if "FY" in rdf.columns:
            rdf["FY"] = [str(int(x)) if pd.notna(x) else "—" for x in rdf["FY"]]
        rdf = rdf.set_index("Concept")
        ui.render_html_table(
            rdf,
            right_text_cols=["Value"],
            text_cols=[c for c in rdf.columns if c != "Value"],
            column_labels=col_cfg,
            index_label=i18n.t("sec.col.concept"),
            height=560,
        )

# ══════════════════════════════════════════════════════════════════════════
# ④ comp-table export (multi-ticker × KPI)
# ══════════════════════════════════════════════════════════════════════════
theme.section_header(i18n.t("sec.section.comp"))
ok_pool = pool[pool["sec_status"] == "ok"]["ticker"].tolist()
comp_tickers = st.multiselect(
    i18n.t("sec.comp.pick_tickers"),
    options=ok_pool,
    default=[ticker] if ticker in ok_pool else [],
    format_func=lambda t: f"{name_map.get(t, t)} · {fmt.fmt_ticker_bbg(t)}",
    key="ai_sec_comp_tickers",
)
all_kpi_keys = [k["kpi_key"] for k in sf.kpis_for_domain(domain)]
kpi_labels = {k["kpi_key"]: k[label_field] for k in sf.kpis_for_domain(domain)}
default_kpis = [k for k in ("revenue", "net_income", "eps_diluted", "rnd", "cash") if k in all_kpi_keys]
comp_kpis = st.multiselect(
    i18n.t("sec.comp.pick_kpis"),
    options=all_kpi_keys,
    default=default_kpis,
    format_func=lambda k: kpi_labels.get(k, k),
    key="ai_sec_comp_kpis",
)
st.caption(i18n.t("sec.comp.hint"))

if comp_tickers and comp_kpis:
    comp = sf.comp_table(comp_tickers, comp_kpis, lang=i18n.get_lang())
    comp.insert(1, "Name", [name_map.get(t, t) for t in comp["Ticker"]])
    st.download_button(
        i18n.t("sec.comp.dl"),
        data=comp.to_csv(index=False).encode("utf-8-sig"),
        file_name="sec_comp_table.csv",
        mime="text/csv",
    )
    unit_by_label = {k[label_field]: (k["unit_hint"] or "USD") for k in sf.kpis_for_domain(domain)}
    prev = comp.copy()
    for c in prev.columns:
        if c not in ("Ticker", "Name", "FY End"):
            u = unit_by_label.get(c, "USD")
            prev[c] = prev[c].map(lambda v, _u=u: _fmt_val(v, _u))
    rprev = prev.set_index("Ticker")
    _val_cols = [c for c in rprev.columns if c not in ("Name", "FY End")]
    ui.render_html_table(
        rprev,
        right_text_cols=_val_cols,
        text_cols=[c for c in ("Name", "FY End") if c in rprev.columns],
        index_label="Ticker",
        height=480,
    )

with st.expander(i18n.t("sec.onboarding.title")):
    st.markdown(i18n.t("sec.onboarding.body"))
