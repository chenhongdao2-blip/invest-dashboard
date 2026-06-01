"""Healthcare · Capital Markets 投融资 — Pharma MNC M&A (deal-level).

Centerpiece: the M&A history of 13 global pharma MNCs from the MNCs basket xlsx
(mnc-deal-scanner skill). 2026-YTD M&A is surfaced at the top. CRITICAL: M&A
(true acquisition / change of control) is kept SEPARATE from BD (license / option
/ collaboration — no change of control). The Hengrui-BMS $15.2B is BD, not M&A.
Complemented by the MNC dry-powder balance-sheet table (SEC XBRL).

Data (copied into repo): data/external/mnc_ma_deals.csv (+ meta) carries a
deal_type column {M&A | BD}. NO sell-side rating surfaced.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import charts
from lib import funding
from lib import i18n
from lib import theme
from lib import ui

st.set_page_config(page_title="Capital Markets · invest-dashboard", page_icon="💰", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()
with st.sidebar:
    ui.sidebar_search(key_prefix="hc_capital")

# ── Load + split M&A vs BD ─────────────────────────────────────────────────
deals = funding.load_mnc_deals()
meta = funding.mnc_ma_meta()
mnc_bs = funding.load_mnc()

ma = deals[deals["deal_type"] == "M&A"].copy()       # true acquisitions only
bd = deals[deals["deal_type"] == "BD"].copy()         # license / option / collaboration

theme.page_header(i18n.t("capital.page.title"),
                  meta=i18n.t("mnc_ma.page.asof", asof=meta.get("as_of", "")))
st.caption(i18n.t("mnc_ma.intro"))
st.info(i18n.t("mnc_ma.source_note", source=meta.get("source", "")))


def _kpi(label: str, value: str, sub: str, vcls: str = "") -> str:
    return (
        '<div class="cmsi-kpi">'
        f'<div class="cmsi-kpi-head"><span class="cmsi-kpi-label ipo">{label}</span></div>'
        f'<div class="cmsi-kpi-num {vcls}">{value}</div>'
        f'<div class="cmsi-kpi-foot ink">{sub}</div>'
        '</div>'
    )


c_tgt = i18n.t("mnc_ma.col.target")
c_yr = i18n.t("mnc_ma.col.year")
c_sz = i18n.t("mnc_ma.col.size")
c_ta = i18n.t("mnc_ma.col.ta")
c_basis = i18n.t("mnc_ma.col.basis")


def _ym(d, y) -> str:
    """ISO date -> 'YYYY-MM'; fall back to the year when no month is on file."""
    s = str(d)
    return s[:7] if len(s) >= 7 and s[:4].isdigit() and s[4] == "-" else str(int(y))


def _deal_table(df: pd.DataFrame, height: int) -> None:
    disp = pd.DataFrame({
        c_tgt: df["target"].astype(str),
        c_yr: [_ym(d, y) for d, y in zip(df["date"], df["year"])],   # YYYY-MM
        c_sz: df["deal_size_mn"] / 1000.0,                            # USD bn
        c_ta: [i18n.ta_name(t) for t in df["ta_group"]],             # bilingual on zh
        c_basis: [i18n.t(f"mnc_ma.basis.{b}") for b in df["size_basis"]],
    })
    disp.index = df["ticker"].astype(str)
    disp.index.name = i18n.t("mnc_ma.col.ticker")
    ui.render_html_table(
        disp, extra_formats={c_sz: "%.2f"},
        text_cols=[c_tgt, c_ta, c_basis], right_text_cols=[c_yr],
        index_label=i18n.t("mnc_ma.col.ticker"), height=height,
    )


def _deal_table_b3(df: pd.DataFrame, height: int) -> None:
    """2026 deals with the B3 three-part economics: total / upfront / milestone (USD bn)."""
    col_t = i18n.t("mnc_ma.col.total")
    col_u = i18n.t("mnc_ma.col.upfront")
    col_m = i18n.t("mnc_ma.col.milestone")
    col_s = i18n.t("mnc_ma.col.src")
    disp = pd.DataFrame({
        c_tgt: df["target"].astype(str),
        col_s: df["source_url"].astype(str),                # 来源 — right after the company
        c_yr: [_ym(d, y) for d, y in zip(df["date"], df["year"])],
        col_t: df["deal_size_mn"] / 1000.0,
        col_u: df["upfront_musd"] / 1000.0,
        col_m: df["milestone_musd"] / 1000.0,
        c_ta: [i18n.ta_name(t) for t in df["ta_group"]],
    })
    disp.index = df["ticker"].astype(str)
    disp.index.name = i18n.t("mnc_ma.col.ticker")
    ui.render_html_table(
        disp, extra_formats={col_t: "%.2f", col_u: "%.2f", col_m: "%.2f"},
        text_cols=[c_tgt, c_ta], right_text_cols=[c_yr], link_cols=[col_s],
        index_label=i18n.t("mnc_ma.col.ticker"), height=height,
    )


def _source_links(df: pd.DataFrame) -> None:
    """Clickable per-deal source links (render_html_table can't hold <a>, so list below)."""
    links = []
    for _, r in df.iterrows():
        url = str(r.get("source_url", "") or "")
        if url.startswith("http"):
            name = str(r["target"]).split("(")[0].split("—")[0].strip()[:18]
            links.append(f"[{r['ticker']}·{name}]({url})")
    if links:
        st.caption(i18n.t("mnc_ma.ytd.sources"))
        st.markdown(" · ".join(links))


# ══ 2026 YTD M&A (TOP) ════════════════════════════════════════════════════
theme.section_header(i18n.t("mnc_ma.section.ytd"), meta=i18n.t("mnc_ma.section.ytd_meta"))

ma26 = ma[ma["year"] == 2026].sort_values("deal_size_mn", ascending=False)
bd26 = bd[bd["year"] == 2026]
ma26_total_bn = ma26["deal_size_mn"].sum() / 1000.0
cards = [
    _kpi(i18n.t("mnc_ma.ytd.total"), f"${ma26_total_bn:,.1f}B",
         i18n.t("mnc_ma.ytd.total_foot", n=len(ma26)), vcls="up-deep"),
    _kpi(i18n.t("mnc_ma.ytd.count"), f"{len(ma26)}",
         i18n.t("mnc_ma.ytd.count_foot", value=ma26_total_bn)),
]
if not ma26.empty:
    big26 = ma26.iloc[0]
    cards.append(_kpi(i18n.t("mnc_ma.ytd.biggest"), f"${big26['deal_size_mn'] / 1000:,.2f}B",
                      i18n.t("mnc_ma.ytd.biggest_foot", acq=big26["ticker"], tgt=big26["target"]), vcls="up"))
cards.append(_kpi(i18n.t("mnc_ma.ytd.bd_count"), f"{len(bd26)}",
                  i18n.t("mnc_ma.ytd.bd_foot"), vcls="up"))
theme.kpi_strip(cards)

if not ma26.empty:
    _deal_table_b3(ma26, height=min(820, 80 + 36 * len(ma26)))


# ══ Lifetime M&A (true acquisitions only) ═════════════════════════════════
ma_total_bn = meta["ma_total_mn"] / 1000.0
by_co = funding.mnc_by_company(ma)
by_ta = funding.mnc_by_ta(ma)
by_yr = funding.mnc_by_year(ma)
top_co = by_co.iloc[0]
biggest = funding.mnc_top_deals(ma, 1).iloc[0]
n_actual = int((ma["size_basis"] == "Actual").sum())
n_est = int((ma["size_basis"] == "Estimated").sum())

theme.section_header(i18n.t("mnc_ma.section.league"),
                     meta=i18n.t("mnc_ma.section.league_meta") + " " + i18n.t("mnc_ma.ma_only"))
theme.kpi_strip([
    _kpi(i18n.t("mnc_ma.kpi.total"), f"${ma_total_bn / 1000:,.2f}T",
         i18n.t("mnc_ma.kpi.total_foot", n=meta["n_ma"], ymin=meta["year_min"], ymax=meta["year_max"]), vcls="up-deep"),
    _kpi(i18n.t("mnc_ma.kpi.deals"), f"{meta['n_ma']:,}",
         i18n.t("mnc_ma.kpi.deals_foot", actual=n_actual, est=n_est)),
    _kpi(i18n.t("mnc_ma.kpi.top"), f"${top_co['total_bn']:,.0f}B",
         i18n.t("mnc_ma.kpi.top_foot", company=top_co["company"], n=int(top_co["n"])), vcls="up"),
    _kpi(i18n.t("mnc_ma.kpi.biggest"), f"${biggest['deal_size_mn'] / 1000:,.1f}B",
         i18n.t("mnc_ma.kpi.biggest_foot", acq=biggest["ticker"], tgt=biggest["target"], year=int(biggest["year"])), vcls="up-deep"),
])
st.plotly_chart(charts.ranked_hbar(by_co["company"].tolist(), by_co["total_bn"].tolist(),
                title=i18n.t("mnc_ma.chart.by_company"), xlabel=i18n.t("capital.unit.bn")),
                width="stretch", theme=None)

theme.section_header(i18n.t("mnc_ma.section.ta"), meta=i18n.t("mnc_ma.section.ta_meta"))
st.plotly_chart(charts.ranked_hbar([i18n.ta_name(t) for t in by_ta["ta_group"]], by_ta["total_bn"].tolist(),
                title=i18n.t("mnc_ma.chart.by_ta"), xlabel=i18n.t("capital.unit.bn"), color=theme.UP_DEEP),
                width="stretch", theme=None)

theme.section_header(i18n.t("mnc_ma.section.timeline"), meta=i18n.t("mnc_ma.section.timeline_meta"))
st.plotly_chart(charts.year_bar(by_yr["year"].tolist(), by_yr["total_bn"].tolist(),
                title=i18n.t("mnc_ma.chart.by_year"), ylabel=i18n.t("capital.unit.bn")),
                width="stretch", theme=None)

theme.section_header(i18n.t("mnc_ma.section.top"))
_deal_table(funding.mnc_top_deals(ma, 20), height=760)

theme.section_header(i18n.t("mnc_ma.section.table"), meta=i18n.t("mnc_ma.section.table_meta"))
_co_opts = [i18n.t("mnc_ma.filter.all")] + by_co["ticker"].tolist()
_pick = st.selectbox(i18n.t("mnc_ma.filter.company"), _co_opts, key="mnc_ma_co")
_sub = ma if _pick == i18n.t("mnc_ma.filter.all") else ma[ma["ticker"] == _pick]
_deal_table(_sub.sort_values("deal_size_mn", ascending=False), height=620)


# ══ BD / partnerships — report format (licensor→licensee, upfront/milestone/total) ══
theme.section_header(i18n.t("mnc_ma.section.bd"), meta=i18n.t("mnc_ma.section.bd_meta"))
bd_rpt = funding.load_bd_report().sort_values("total_musd", ascending=False)
bd_lor = i18n.t("mnc_ma.bd.col.licensor")
bd_lee = i18n.t("mnc_ma.bd.col.licensee")
bd_ast = i18n.t("mnc_ma.bd.col.asset")
bd_pha = i18n.t("mnc_ma.bd.col.phase")
bd_ta = i18n.t("mnc_ma.col.ta")
bd_up = i18n.t("mnc_ma.col.upfront")
bd_ms = i18n.t("mnc_ma.col.milestone")
bd_tot = i18n.t("mnc_ma.col.total")
bd_dt = i18n.t("mnc_ma.bd.col.date")
bd_src = i18n.t("mnc_ma.col.src")
bd_disp = pd.DataFrame({
    bd_ast: bd_rpt["asset"].astype(str),       # 药物/技术 — between 授权方(index) and 被授权方
    bd_lee: bd_rpt["licensee"].astype(str),
    bd_src: bd_rpt["source_url"].astype(str),  # 来源 — right after the company
    bd_ta: bd_rpt["ta"].astype(str),
    bd_pha: bd_rpt["phase"].astype(str),
    bd_up: bd_rpt["upfront_musd"] / 1000.0,
    bd_ms: bd_rpt["milestone_musd"] / 1000.0,
    bd_tot: bd_rpt["total_musd"] / 1000.0,
    bd_dt: bd_rpt["date"].astype(str),
})
bd_disp.index = bd_rpt["licensor"].astype(str)
bd_disp.index.name = bd_lor
ui.render_html_table(
    bd_disp,
    extra_formats={bd_up: "%.2f", bd_ms: "%.2f", bd_tot: "%.2f"},
    text_cols=[bd_lee, bd_ast, bd_ta, bd_pha],
    right_text_cols=[bd_dt], link_cols=[bd_src],
    index_label=bd_lor,
    height=820,
)


# ══ MNC dry-powder (SEC XBRL — who can fund the next wave) ═════════════════
theme.section_header(i18n.t("capital.section.mnc"), meta=i18n.t("capital.section.mnc_meta"))
c_company = i18n.t("capital.mnc.col.company")
c_cash = i18n.t("capital.mnc.col.cash")
c_debt = i18n.t("capital.mnc.col.debt")
c_net = i18n.t("capital.mnc.col.net")
c_form = i18n.t("capital.mnc.col.form")
c_date = i18n.t("capital.mnc.col.date")
mnc_disp = pd.DataFrame({
    c_company: mnc_bs["name"].astype(str),
    c_cash: mnc_bs["cash_bn"], c_debt: mnc_bs["debt_total_bn"], c_net: mnc_bs["net_cash_bn"],
    c_form: mnc_bs["filing_form"].astype(str), c_date: mnc_bs["filing_date"].astype(str),
})
mnc_disp.index = mnc_bs["ticker"].astype(str)
mnc_disp.index.name = "Ticker"
mnc_disp = mnc_disp.sort_values(c_net, ascending=False, na_position="last")
ui.render_html_table(mnc_disp, money_b_cols=[c_cash, c_debt, c_net], text_cols=[c_company],
                     right_text_cols=[c_form, c_date], index_label="Ticker", height=720)
st.caption(i18n.t("capital.mnc.note"))


# ══ Sources — clickable MNC IR newsrooms ══════════════════════════════════
theme.section_header(i18n.t("mnc_ma.section.sources"))
st.caption(i18n.t("mnc_ma.sources_note"))
_name_by_tkr = dict(zip(by_co["ticker"], by_co["company"]))
_links = [
    f"[{_name_by_tkr.get(tkr, tkr)} ({tkr})]({url})"
    for tkr, url in funding.MNC_IR_URL.items()
]
st.markdown(" · ".join(_links))

st.divider()
st.info(i18n.t("mnc_ma.disclaimer"))
