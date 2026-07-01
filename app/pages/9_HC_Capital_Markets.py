"""Healthcare · Capital Markets 投融资 — Pharma MNC M&A + BD/licensing (deal-level).

Two co-equal domains, split into tabs so "M&A is M&A, BD is BD":
- **M&A** (control transfer): the acquisition history of global pharma/biotech buyers
  (original 13-MNC basket + 2026 expansion: Gilead/Biogen/UCB/Merck KGaA…). 2026-YTD at
  the top. M&A is web/deal-tracker sourced — PharmCube carries no corporate M&A.
- **BD** (license / option / collaboration — NO control transfer): the
  bd_deals.csv canonical set, given its own insight layer (KPI strip + MNC-buyer league + by-TA +
  depth-of-reach by phase + timeline + filter table). Hengrui-BMS $15.2B is BD, not M&A.

CRITICAL: the two are never mixed in one scroll. BD value is milestone-CONTINGENT — the
headline total is an announced ceiling, never realized cash (Σ upfront ≪ Σ total). The
MNC dry-powder balance-sheet table (SEC XBRL) sits below both tabs — firepower for both.
NO sell-side rating surfaced.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import charts
from lib import funding
from lib import i18n
from lib import ipo_tracker
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

ma = deals[deals["deal_type"] == "M&A"].copy()        # true acquisitions only
mnc_bd = deals[deals["deal_type"] == "BD"].copy()      # 39-row BD subset — M&A-tab YTD count card only

BD_ACCENT = theme.SECTOR_PALETTE[3]   # "#4a6fa5" muted slate-blue — BD value bars (NOT teal/red)
IPO_ACCENT = theme.SECTOR_PALETTE[2]  # IPO break-rate bars (distinct from M&A/BD)

# ── Column labels ──────────────────────────────────────────────────────────
c_tgt = i18n.t("mnc_ma.col.target")
c_yr = i18n.t("mnc_ma.col.year")
c_sz = i18n.t("mnc_ma.col.size")
c_ta = i18n.t("mnc_ma.col.ta")
c_basis = i18n.t("mnc_ma.col.basis")

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
bd_struct = i18n.t("capital.bd.col.structure")
_STRUCT_LABEL = {
    "License-out": i18n.t("capital.bd.struct.licenseout"),
    "Co-Co": i18n.t("capital.bd.struct.coco"),
    "NewCo": i18n.t("capital.bd.struct.newco"),
}


def _kpi(label: str, value: str, sub: str, vcls: str = "") -> str:
    return (
        '<div class="cmsi-kpi">'
        f'<div class="cmsi-kpi-head"><span class="cmsi-kpi-label ipo">{label}</span></div>'
        f'<div class="cmsi-kpi-num {vcls}">{value}</div>'
        f'<div class="cmsi-kpi-foot ink">{sub}</div>'
        '</div>'
    )


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


def _bd_table(df: pd.DataFrame, height: int) -> None:
    """BD deal table: index = licensor(授权方); cols = asset / licensee / source ↗ /
    canonical TA / canonical phase / upfront / milestone / total (USD bn) / date.
    Mirrors _deal_table_b3 but for BD's licensor→asset→licensee economics."""
    disp = pd.DataFrame({
        bd_struct: [_STRUCT_LABEL.get(str(s), str(s)) for s in df["structure"]],
        bd_ast: df["asset"].astype(str),
        bd_lee: df["licensee"].astype(str),
        bd_src: df["source_url"].astype(str),
        bd_ta: [i18n.ta_name(x) for x in df["ta_canon"]],
        bd_pha: df["phase_canon"].astype(str),
        bd_up: df["upfront_musd"] / 1000.0,
        bd_ms: df["milestone_musd"] / 1000.0,
        bd_tot: df["total_musd"] / 1000.0,
        bd_dt: df["date"].astype(str),
    })
    disp.index = df["licensor"].astype(str)
    disp.index.name = bd_lor
    ui.render_html_table(
        disp, extra_formats={bd_up: "%.2f", bd_ms: "%.2f", bd_tot: "%.2f"},
        text_cols=[bd_struct, bd_lee, bd_ast, bd_ta, bd_pha], right_text_cols=[bd_dt], link_cols=[bd_src],
        index_label=bd_lor, height=height,
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


# ══ Page header + taxonomy callout (above the tabs) ════════════════════════
theme.page_header(i18n.t("capital.page.title"),
                  meta=i18n.t("mnc_ma.page.asof", asof=meta.get("as_of", "")))
st.caption(i18n.t("mnc_ma.intro"))
theme.md_note("来源 · 口径" if i18n.get_lang() == "zh" else "Source · basis", i18n.t("mnc_ma.source_note", source=meta.get("source", "")))
theme.md_note("释义 · M&A vs BD" if i18n.get_lang() == "zh" else "Definitions · M&A vs BD", i18n.t("capital.def"))

tab_ma, tab_bd, tab_ipo = st.tabs([i18n.t("capital.tab.ma"), i18n.t("capital.tab.bd"), i18n.t("capital.tab.ipo")])


# ══════════════════════════════ M&A TAB ═══════════════════════════════════
with tab_ma:
    # ── 2026 YTD M&A ──
    theme.section_header(i18n.t("mnc_ma.section.ytd"), meta=i18n.t("mnc_ma.section.ytd_meta"))
    ma26 = ma[ma["year"] == 2026].sort_values("deal_size_mn", ascending=False)
    bd26 = mnc_bd[mnc_bd["year"] == 2026]
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

    # ── Lifetime M&A (true acquisitions only) ──
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

    # ── 资金流 Sankey:收购方 × 治疗领域(bold 新 viz — 一图看钱流向哪个 TA)──
    from lib import deal_sankey
    _zh = i18n.get_lang() == "zh"
    _topN = by_co.head(12)
    _agg = (ma[ma["ticker"].isin(set(_topN["ticker"]))]
            .groupby(["ticker", "ta_group"], as_index=False)["deal_size_mn"].sum())
    _agg["bn"] = _agg["deal_size_mn"] / 1000.0
    _agg = _agg[_agg["bn"] >= 2.0]                       # 去 <$2B 细碎链路,保持可读
    if not _agg.empty:
        _acq = [tk for tk in _topN["ticker"].tolist() if tk in set(_agg["ticker"])]
        _tas = list(_agg.groupby("ta_group")["bn"].sum().sort_values(ascending=False).index)
        _nodes = ([{"name": tk, "side": "L"} for tk in _acq]
                  + [{"name": i18n.ta_name(ta), "side": "R"} for ta in _tas])
        _links = [{"source": r["ticker"], "target": i18n.ta_name(r["ta_group"]), "value": r["bn"]}
                  for _, r in _agg.iterrows()]
        theme.section_header("资金流 · 收购方 × 治疗领域" if _zh else "Capital Flow · Acquirer × TA",
                             meta=("连线宽 = 累计交易额" if _zh else "link width = cumulative deal value"))
        deal_sankey.render(
            _nodes, _links,
            title=("M&A 资金流向" if _zh else "M&A capital flow"),
            source=(f"来源 web / deal-tracker · M&A 累计交易额(USD bn)· 头部 {len(_acq)} 收购方 · 链路 ≥ $2B"
                    if _zh else
                    f"Source: web / deal-tracker · cumulative M&A value (USD bn) · top {len(_acq)} acquirers · links ≥ $2B"),
            prefer_cn=_zh,
        )

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


# ══════════════════════════════ BD TAB ════════════════════════════════════
with tab_bd:
    bd = funding.load_bd_enriched()       # 99-row canonical BD set (NEVER union mnc_ma BD rows)
    k = funding.bd_kpis(bd)

    # ── 2026 YTD BD ──
    theme.section_header(i18n.t("capital.bd.section.ytd"), meta=i18n.t("capital.bd.section.ytd_meta"))
    bd26v = bd[(bd["year"] == 2026) & bd["value_ok"]]
    bd26_all = bd[bd["year"] == 2026]
    ytd_total_bn = bd26v["total_musd"].sum() / 1000.0
    ytd_upfront_bn = bd26v["upfront_musd"].sum() / 1000.0
    bd_cards = [
        _kpi(i18n.t("capital.bd.ytd.total"), f"${ytd_total_bn:,.1f}B",
             i18n.t("capital.bd.ytd.total_foot", n=len(bd26_all))),
        _kpi(i18n.t("capital.bd.ytd.upfront"), f"${ytd_upfront_bn:,.1f}B",
             i18n.t("capital.bd.ytd.upfront_foot")),
        _kpi(i18n.t("capital.bd.ytd.count"), f"{len(bd26_all)}",
             i18n.t("capital.bd.ytd.count_foot", y=k["n_2025"])),
    ]
    if len(bd26v):
        big = bd26v.nlargest(1, "total_musd").iloc[0]
        bd_cards.append(_kpi(i18n.t("capital.bd.ytd.biggest"), f"${big['total_musd'] / 1000:,.1f}B",
                             i18n.t("capital.bd.ytd.biggest_foot", lor=str(big["licensor"]), lee=str(big["licensee"]))))
    theme.kpi_strip(bd_cards)
    st.caption(i18n.t("capital.bd.contingent"))
    if not bd26_all.empty:
        _bd_table(bd26_all.sort_values("total_musd", ascending=False),
                  height=min(820, 80 + 36 * len(bd26_all)))

    # ── BD League (full 2025–2026) — the risk-sharing + China-out economics ──
    theme.section_header(i18n.t("capital.bd.section.league"), meta=i18n.t("capital.bd.section.league_meta"))
    league_cards = [
        _kpi(i18n.t("capital.bd.kpi.total"), f"${k['total_bn']:,.1f}B",
             i18n.t("capital.bd.kpi.total_foot", u=k["upfront_bn"], m=k["milestone_bn"])),
    ]
    if k["med_upfront_pct"] is not None:
        league_cards.append(_kpi(i18n.t("capital.bd.kpi.upfront_ratio"), f"{k['med_upfront_pct']:.1f}%",
                                 i18n.t("capital.bd.kpi.upfront_ratio_foot")))
    if k["china_pct"] is not None:
        league_cards.append(_kpi(i18n.t("capital.bd.kpi.china"), f"{k['china_pct']:.1f}%",
                                 i18n.t("capital.bd.kpi.china_foot", b=k["china_bn"])))
    if k["top_mnc"] is not None:
        league_cards.append(_kpi(i18n.t("capital.bd.kpi.topmnc"), f"{k['top_mnc']['licensee']}",
                                 i18n.t("capital.bd.kpi.topmnc_foot", name=k["top_mnc"]["licensee"], n=int(k["top_mnc"]["n"]))))
    theme.kpi_strip(league_cards)

    # Chart 1 — MNC buyer league (by DEAL COUNT; value is milestone-inflated)
    theme.section_header(i18n.t("capital.bd.section.bylicensee"), meta=i18n.t("capital.bd.section.bylicensee_meta"))
    by_lee = funding.bd_by_licensee(bd, top=12)
    st.plotly_chart(charts.ranked_hbar(by_lee["licensee"].tolist(), by_lee["n"].tolist(),
                    title=i18n.t("capital.bd.chart.licensee"), xlabel=i18n.t("capital.bd.unit.deals"),
                    color=BD_ACCENT, value_fmt="%d"),
                    width="stretch", theme=None)
    st.caption(i18n.t("capital.bd.note.league"))

    # Chart 2 — by canonical TA (value; same axis taxonomy as the M&A by-TA chart)
    theme.section_header(i18n.t("capital.bd.section.byta"), meta=i18n.t("capital.bd.section.byta_meta"))
    by_ta_bd = funding.bd_by_ta(bd)
    st.plotly_chart(charts.ranked_hbar([i18n.ta_name(t) for t in by_ta_bd["ta_canon"]], by_ta_bd["total_bn"].tolist(),
                    title=i18n.t("capital.bd.chart.ta"), xlabel=i18n.t("capital.unit.bn"), color=BD_ACCENT),
                    width="stretch", theme=None)

    # Chart 3 — depth-of-reach by phase (COUNT, ordered Preclinical→Approved; M&A can't show this)
    theme.section_header(i18n.t("capital.bd.section.byphase"), meta=i18n.t("capital.bd.section.byphase_meta"))
    by_ph = funding.bd_by_phase(bd)
    st.plotly_chart(charts.ranked_hbar(by_ph["phase_canon"].tolist(), by_ph["n"].tolist(),
                    title=i18n.t("capital.bd.chart.phase"), xlabel=i18n.t("capital.bd.unit.deals"),
                    color=BD_ACCENT, value_fmt="%d"),
                    width="stretch", theme=None)

    # Chart 4 — 2025→2026 timeline (COUNT; 2026 is partial)
    theme.section_header(i18n.t("capital.bd.section.byyear"))
    by_yr_bd = funding.bd_by_year(bd)
    st.plotly_chart(charts.year_bar(by_yr_bd["year"].tolist(), by_yr_bd["n"].tolist(),
                    title=i18n.t("capital.bd.chart.year"), ylabel=i18n.t("capital.bd.unit.deals"),
                    color=BD_ACCENT, dtick=1, value_hover_fmt=",.0f"),
                    width="stretch", theme=None)
    st.caption(i18n.t("capital.bd.note.year"))

    # Chart 5 — by out-licensing STRUCTURE (License-out / Co-Co / NewCo) — the模式升级 view
    theme.section_header(i18n.t("capital.bd.section.bystructure"), meta=i18n.t("capital.bd.section.bystructure_meta"))
    by_st = funding.bd_by_structure(bd)
    _st_lbl = [_STRUCT_LABEL.get(s, s) for s in by_st["structure"]]
    st.plotly_chart(charts.ranked_hbar(_st_lbl, by_st["n"].tolist(),
                    title=i18n.t("capital.bd.chart.structure"), xlabel=i18n.t("capital.bd.unit.deals"),
                    color=BD_ACCENT, value_fmt="%d"),
                    width="stretch", theme=None)
    st.caption(i18n.t("capital.bd.note.structure",
                      lo=int(by_st.set_index("structure").loc["License-out", "n"]),
                      coco=int(by_st.set_index("structure").loc["Co-Co", "n"]),
                      newco=int(by_st.set_index("structure").loc["NewCo", "n"])))

    # ── TOP 20 + dual-filter detail table ──
    theme.section_header(i18n.t("capital.bd.section.top"))
    _bd_table(bd.sort_values("total_musd", ascending=False).head(20), height=760)

    theme.section_header(i18n.t("capital.bd.section.table"))
    _all = i18n.t("capital.bd.filter.all")
    _fc1, _fc2, _fc3 = st.columns(3)
    with _fc1:
        _lee_opts = [_all] + sorted(bd["licensee"].dropna().astype(str).unique().tolist())
        _pick_lee = st.selectbox(i18n.t("capital.bd.filter.licensee"), _lee_opts, key="bd_flt_lee")
    with _fc2:
        _lor_opts = [_all] + sorted(bd["licensor"].dropna().astype(str).unique().tolist())
        _pick_lor = st.selectbox(i18n.t("capital.bd.filter.licensor"), _lor_opts, key="bd_flt_lor")
    with _fc3:
        _st_opts = [_all] + funding.BD_STRUCTURE_ORDER
        _pick_st = st.selectbox(i18n.t("capital.bd.filter.structure"), _st_opts, key="bd_flt_st",
                                format_func=lambda s: _STRUCT_LABEL.get(s, s) if s != _all else _all)
    _bsub = bd.copy()
    if _pick_lee != _all:
        _bsub = _bsub[_bsub["licensee"].astype(str) == _pick_lee]
    if _pick_lor != _all:
        _bsub = _bsub[_bsub["licensor"].astype(str) == _pick_lor]
    if _pick_st != _all:
        _bsub = _bsub[_bsub["structure"].astype(str) == _pick_st]
    _bd_table(_bsub.sort_values("total_musd", ascending=False), height=620)


# ══════════════════════════════ IPO TAB ═══════════════════════════════════
with tab_ipo:
    ipo = ipo_tracker.load_hk_ipo_tracker()
    im = ipo_tracker.hk_ipo_meta()
    if ipo.empty:
        st.caption(i18n.t("capital.ipo.empty"))
    else:
        st.caption(i18n.t("capital.ipo.asof", asof=im.get("as_of", "")))
        clean = ipo_tracker.clean_view(ipo)
        broke_n = int((clean["broke"] == True).sum())  # noqa: E712
        broke_d = int(clean["broke"].notna().sum())
        n_big = int(ipo["mktcap_tier"].isin(["大市值", "中市值"]).sum())
        med = clean["ret_pct"].median()
        cards = [
            _kpi(i18n.t("capital.ipo.kpi.total"), f"{len(ipo)}",
                 i18n.t("capital.ipo.kpi.total_foot", w=int(im.get("n_with_offer", 0)),
                        s=int(im.get("n_suspended", 0)))),
            _kpi(i18n.t("capital.ipo.kpi.broke"), f"{broke_n / broke_d * 100:.0f}%" if broke_d else "—",
                 i18n.t("capital.ipo.kpi.broke_foot", n=broke_n, d=broke_d,
                        fn=im.get("break_rate_full", "—"))),
            _kpi(i18n.t("capital.ipo.kpi.big"), f"{n_big}", i18n.t("capital.ipo.kpi.big_foot")),
        ]
        if not clean.empty and clean["ret_pct"].notna().any():
            top = clean.loc[clean["ret_pct"].idxmax()]
            cards.append(_kpi(i18n.t("capital.ipo.kpi.top"), f"{top['ret_pct']:+.0f}%",
                              i18n.t("capital.ipo.kpi.top_foot", name=str(top["name_cn"]))))
        cards.append(_kpi(i18n.t("capital.ipo.kpi.median"), f"{med:+.0f}%" if pd.notna(med) else "—",
                          i18n.t("capital.ipo.kpi.median_foot", n=len(clean))))
        theme.kpi_strip(cards)
        st.caption(i18n.t("capital.ipo.methodology"))

        # Chart 1 (the conclusion) — 破发率 × 市值分层 (monotonic)
        theme.section_header(i18n.t("capital.ipo.section.bymkt"), meta=i18n.t("capital.ipo.section.bymkt_meta"))
        brm = ipo_tracker.break_rate_by(ipo, "mktcap_tier", ["大市值", "中市值", "小市值"])
        brm = brm[brm["n"] > 0]
        st.plotly_chart(charts.ranked_hbar(
            [f"{b} (n={n})" for b, n in zip(brm["bucket"], brm["n"])], brm["rate_pct"].tolist(),
            title=i18n.t("capital.ipo.chart.bymkt"), xlabel=i18n.t("capital.ipo.unit.break"),
            color=IPO_ACCENT, value_fmt="%.0f%%"), width="stretch", theme=None)
        st.caption(i18n.t("capital.ipo.note.bymkt"))

        # Chart 2 — 涨幅 × 市值散点 (excl. no-offer + suspended frozen prices)
        theme.section_header(i18n.t("capital.ipo.section.scatter"), meta=i18n.t("capital.ipo.section.scatter_meta"))
        st.plotly_chart(charts.scatter_returns(
            ipo[(~ipo["no_offer"]) & (~ipo["suspended"])], title=i18n.t("capital.ipo.chart.scatter")),
            width="stretch", theme=None)

        # Chart 3 — 破发率 × 流动性 (secondary; noisy, descriptive only)
        theme.section_header(i18n.t("capital.ipo.section.byliq"), meta=i18n.t("capital.ipo.section.byliq_meta"))
        brl = ipo_tracker.break_rate_by(ipo, "liquidity_tier", [">$20M", "$10-20M", "<$10M"])
        brl = brl[brl["n"] > 0]
        st.plotly_chart(charts.ranked_hbar(
            [f"{b} (n={n})" for b, n in zip(brl["bucket"], brl["n"])], brl["rate_pct"].tolist(),
            title=i18n.t("capital.ipo.chart.byliq"), xlabel=i18n.t("capital.ipo.unit.break"),
            color=theme.INK_3, value_fmt="%.0f%%"), width="stretch", theme=None)
        st.caption(i18n.t("capital.ipo.note.byliq"))

        # Full roster — filterable
        theme.section_header(i18n.t("capital.ipo.section.table"))
        _iall = i18n.t("capital.ipo.filter.all")
        _above, _below = i18n.t("capital.ipo.filter.above"), i18n.t("capital.ipo.filter.below")
        _ai = i18n.t("capital.ipo.filter.ai")
        _g1, _g2, _g3 = st.columns(3)
        with _g1:
            _pick_mkt = st.selectbox(i18n.t("capital.ipo.filter.mkt"),
                                     [_iall, "大市值", "中市值", "小市值"], key="ipo_flt_mkt")
        with _g2:
            _pick_w = st.selectbox(i18n.t("capital.ipo.filter.water"), [_iall, _above, _below], key="ipo_flt_w")
        with _g3:
            _pick_tag = st.selectbox(i18n.t("capital.ipo.filter.tag"), [_iall, "18A", _ai], key="ipo_flt_tag")
        _isub = ipo.copy()
        if _pick_mkt != _iall:
            _isub = _isub[_isub["mktcap_tier"] == _pick_mkt]
        if _pick_w == _above:
            _isub = _isub[_isub["broke"] == False]   # noqa: E712
        elif _pick_w == _below:
            _isub = _isub[_isub["broke"] == True]     # noqa: E712
        if _pick_tag == "18A":
            _isub = _isub[_isub["is_18a"] == True]    # noqa: E712
        elif _pick_tag == _ai:
            _isub = _isub[_isub["is_ai_pharma"] == True]  # noqa: E712

        ic = {k: i18n.t(f"capital.ipo.col.{k}") for k in
              ("name", "date", "offer", "close", "ret", "mktcap", "mkttier", "turnover", "liqtier", "broke", "flag")}

        def _flag(r) -> str:
            if r["suspended"]:
                return "停牌"
            if r["no_offer"]:
                return "介绍上市"
            if r["is_ai_pharma"]:
                return "AI"
            return "18A" if r["is_18a"] else ""

        disp = pd.DataFrame({
            ic["date"]: _isub["ipo_date"].astype(str),
            ic["offer"]: _isub["offer_price_hkd"],
            ic["close"]: _isub["close"],
            ic["ret"]: _isub["ret_pct"],
            ic["mktcap"]: _isub["cur_mktcap_yi"],
            ic["mkttier"]: _isub["mktcap_tier"].fillna("—"),
            ic["turnover"]: _isub["avg_turnover_usdm"],
            ic["liqtier"]: _isub["liquidity_tier"].fillna("—"),
            ic["broke"]: _isub["broke"].map({True: "破发", False: "水上"}).fillna("—"),
            ic["flag"]: [_flag(r) for _, r in _isub.iterrows()],
        })
        disp.index = _isub["name_cn"].astype(str)
        disp.index.name = ic["name"]
        ui.render_html_table(
            disp, price_cols=[ic["offer"], ic["close"]],
            extra_formats={ic["ret"]: "%+.0f%%", ic["mktcap"]: "%.0f", ic["turnover"]: "%.1f"},
            text_cols=[ic["mkttier"], ic["liqtier"], ic["flag"]],
            status_cols={ic["broke"]: {"水上": "up", "破发": "down"}},
            right_text_cols=[ic["date"]], index_label=ic["name"],
            height=min(1100, 80 + 30 * len(disp)))


# ══ MNC dry-powder (SEC XBRL — who can fund the next wave, M&A or BD) ═══════
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
theme.md_note("免责声明" if i18n.get_lang() == "zh" else "Disclaimer", i18n.t("mnc_ma.disclaimer"))
