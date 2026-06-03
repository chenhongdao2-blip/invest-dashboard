"""Healthcare domain overview — 7 sub-sectors summary."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path

from lib import benchmarks as bm
from lib import charts
from lib import db
from lib import format as fmt
from lib import hc_overview as hco
from lib import hc_exports as hcx
from lib import ui
from lib import theme
from lib import i18n


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
        height=360,
        heatmap=True,
        column_labels=column_labels,
    )

st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")

# --- Sidebar global search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="hc_overview")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


cfg = db.load_domain_cfg(str(DOMAIN_CFG))
i18n.init_lang()
i18n.render_lang_toggle()
theme.page_header(i18n.t("hc.title"))
st.caption(cfg.get("description", "").strip())

# --- 7 sector aggregate summary ---
theme.section_header(i18n.t("hc.section.summary"), meta=i18n.t("hc.section.summary_meta"))

rows = []
all_returns_by_sector: dict[str, pd.DataFrame] = {}
for sec in cfg["sectors"]:
    uni = db.sector_tickers("healthcare", sec["id"])
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        continue
    closes = db.get_close_series_usd(tickers)   # M1 audit: USD-converted
    rets = db.compute_returns(closes)
    if rets.empty:
        continue
    all_returns_by_sector[sec["id"]] = rets
    rows.append({
        "Sector": i18n.sector_name(sec["id"]),
        "Tickers": len(tickers),
        "1D % avg": rets["1d_%"].mean(),
        "5D % avg": rets["5d_%"].mean(),
        "1M % avg": rets["1m_%"].mean(),
        "YTD % avg": rets["ytd_%"].mean(),
        "Benchmark": sec.get("benchmark", "—"),
    })

if not rows:
    st.warning(i18n.t("hc.summary.empty"))
else:
    summary = pd.DataFrame(rows).set_index("Sector")
    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    _render_pct_table(
        summary,
        pct_cols=pct_cols,
        column_labels={
            "Sector": i18n.t("hc.col.sector"),
            "Tickers": i18n.t("hc.col.tickers"),
            "Benchmark": i18n.t("hc.col.benchmark"),
            "1D % avg": i18n.t("hc.col.1d_avg"),
            "5D % avg": i18n.t("hc.col.5d_avg"),
            "1M % avg": i18n.t("hc.col.1m_avg"),
            "YTD % avg": i18n.t("hc.col.ytd_avg"),
        },
    )

st.divider()

# --- Domain benchmark snapshot ---
theme.section_header(i18n.t("hc.section.benchmark"), meta=i18n.t("hc.section.benchmark_meta"))
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    sub = sub.rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "3m_%": "3M %", "ytd_%": "YTD %",
    })
    sub["Name"] = [i18n.bench_name(s, n) for s, n in zip(sub.index, sub["Name"])]
    _render_pct_table(
        sub,
        pct_cols=["1D %", "5D %", "1M %", "3M %", "YTD %"],
        num_cols=["Last"],
        column_labels=i18n.common_cols(),
    )

st.divider()

# --- Relative performance: 3 paired index comparisons (Jonah) ----------------
# HSHCI vs HSI/HSTECH · NBI vs Nasdaq · S&P HC vs S&P. Source series baked by
# jobs/build_hc_overview_data.py (HK = iFind, US = yfinance) — cloud can't fetch live.
theme.section_header(i18n.t("hc.rs.section"), meta=i18n.t("hc.rs.section_meta"))
_idx = hco.load_index_comparison()
if _idx.empty:
    st.info(i18n.t("hc.rs.empty"))
else:
    _cn = i18n.get_lang() == "zh"
    _asof = _idx["date"].max().date().isoformat()
    _PANEL_TITLE = {"hk": "hc.rs.hk.title", "nbi": "hc.rs.nbi.title", "sphc": "hc.rs.sphc.title"}

    def _render_rs_panel(panel_id: str, *, height: int = 360) -> None:
        cfg = next((h, p) for pid, h, p in hco.PANELS if pid == panel_id)
        hero_id, peer_ids = cfg
        ser = hco.panel_series(_idx, panel_id)
        if hero_id not in ser:
            return
        hero_nm = hco.series_name(_idx, hero_id, prefer_cn=_cn)
        peers = {hco.series_name(_idx, p, prefer_cn=_cn): ser[p] for p in peer_ids if p in ser}
        fig, meta = charts.index_compare_chart(
            ser[hero_id], peers, hero_name=hero_nm, height=height,
            title=i18n.t(_PANEL_TITLE[panel_id]), ylabel=i18n.t("hc.rs.ylabel"),
        )
        if fig is None:
            return
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})
        # Scannable FT-style spread: "<peer> ±N.Npp" (vs hero, since anchor). −0.0 → 0.0.
        parts = [f"{pn} {(pp if abs(pp) >= 0.05 else 0.0):+.1f}pp" for pn, pp in meta["spreads"].items()]
        st.caption(i18n.t("hc.rs.caption", anchor=meta["anchor"], detail=" / ".join(parts),
                          src="iFind · yfinance", asof=_asof))

    _render_rs_panel("hk")                          # headline: 3-line HK comparison, full width
    _c1, _c2 = st.columns(2)
    with _c1:
        _render_rs_panel("nbi", height=260)         # supporting pair: shorter (visual hierarchy)
    with _c2:
        _render_rs_panel("sphc", height=260)
    theme.eyebrow(i18n.t("hc.read.eyebrow"))         # cross-market read (biotech-researcher Agent)
    st.markdown(i18n.t("hc.rs.read"))
    st.download_button(
        i18n.t("hc.dl.xlsx"), data=hcx.relative_bytes(),
        file_name="HC_相对表现_relative_performance.xlsx",
        mime=_XLSX_MIME, key="dl_hc_relative",
    )

st.divider()

# --- Institutional positioning: offshore China funds OW/UW on healthcare ------
# Audited fund-positioning xlsx → china_fund_hc_positioning.csv. Diverging bar uses
# the LOCKED teal=OW / red=UW convention; caption spells it out (positioning, not return).
theme.section_header(i18n.t("hc.pos.section"), meta=i18n.t("hc.pos.section_meta"))
_pos = hco.load_fund_positioning()
if _pos.empty:
    st.info(i18n.t("hc.pos.empty"))
else:
    _v = hco.positioning_verdict(_pos)
    _v["aum_pp"] = f"{_v.get('aum_wt_dev', 0.0) * 100:+.1f}"   # dynamic — never hardcode the tilt
    st.markdown(i18n.t("hc.pos.verdict", **_v))                # counts headline — always valid
    if _v.get("data_available"):                               # directional tilt only when real AUM backs it
        st.markdown(i18n.t("hc.pos.verdict_tilt", **_v))

    _cn = i18n.get_lang() == "zh"
    _chart_col, _tbl_col = st.columns([5, 6])
    with _chart_col:
        _have = _pos.dropna(subset=["deviation_2026"]).copy()
        fig_pos = charts.positioning_diverging_bar(
            _have["fund"].tolist(), _have["deviation_2026"].tolist(),
            title=i18n.t("hc.pos.chart.title"), xlabel=i18n.t("hc.pos.chart.xlabel"),
        )
        st.plotly_chart(fig_pos, width="stretch", theme=None, config={"displayModeBar": False})
        st.caption(i18n.t("hc.pos.legend"))

    with _tbl_col:
        _stance_key = {"OW": "hc.pos.stance.OW", "UW": "hc.pos.stance.UW",
                       "Neutral": "hc.pos.stance.Neutral", "Slightly OW": "hc.pos.stance.SlightlyOW",
                       "N/A": "hc.pos.stance.NA"}
        c_fund, c_aum = i18n.t("hc.pos.col.fund"), i18n.t("hc.pos.col.aum")
        c_fhc, c_bhc = i18n.t("hc.pos.col.fund_hc"), i18n.t("hc.pos.col.bm_hc")
        c_dev, c_st, c_chg = i18n.t("hc.pos.col.dev"), i18n.t("hc.pos.col.stance"), i18n.t("hc.pos.col.chg")

        def _wpct(x) -> str:
            return "—" if pd.isna(x) else f"{x * 100:.1f}%"

        # House FT-editorial HTML table (NOT st.dataframe — DESIGN.md §5.1: glide-grid
        # bleeds OS dark-mode). dev/chg as pct_decimal → sign-colored = OW-teal / UW-red.
        _disp = pd.DataFrame({
            c_fund: _pos["fund"],
            c_aum: _pos["aum_2026"],
            c_fhc: _pos["fund_hc_w"].map(_wpct),
            c_bhc: _pos["bm_hc_w"].map(_wpct),
            c_dev: _pos["deviation_2026"],
            c_st: _pos["ow_uw_2026"].map(
                lambda s: i18n.t(_stance_key.get(str(s).strip(), "hc.pos.stance.Neutral"))),
            c_chg: _pos["change_dev"],
        })
        ui.render_styled_table(
            _disp,
            pct_decimal_cols=[c_dev, c_chg],
            text_cols=[c_fund, c_aum, c_fhc, c_bhc, c_st],
            hide_index=True,
            height=460,
        )

    theme.eyebrow(i18n.t("hc.read.eyebrow"))   # institutional-flow read (financial-strategist Agent)
    st.markdown(i18n.t("hc.pos.read"))
    st.caption(i18n.t("hc.pos.note_ai"))
    _src = hco.positioning_source()
    if _src:
        st.caption(i18n.t("hc.pos.source") + _src)
    st.download_button(
        i18n.t("hc.dl.xlsx"), data=hcx.positioning_bytes(),
        file_name="HC_机构持仓_fund_positioning.xlsx",
        mime=_XLSX_MIME, key="dl_hc_positioning",
    )

st.divider()

# --- Headcount change: China innovative-pharma hirers vs cutters --------------
# 12 names' FY2024→FY2025 GROUP headcount, baked by jobs/cn_pharma_headcount_2025.py
# from 年报业绩公告 / ESG / iFind (cloud can't fetch live). Diverging bar uses the
# LOCKED teal=扩招 / red=收缩 convention; caption spells it out (headcount, not return).
theme.section_header(i18n.t("hc.hc.section"), meta=i18n.t("hc.hc.section_meta"))
_hc = hco.load_headcount()
if _hc.empty:
    st.info(i18n.t("hc.hc.empty"))
else:
    _cn = i18n.get_lang() == "zh"
    _hv = hco.headcount_verdict(_hc)
    # narrated extremes: pick the lang-appropriate company name (verdict returns both)
    _hv["top_hire_name"] = _hv["top_hire_name_cn"] if _cn else _hv["top_hire_name_en"]
    _hv["top_cut_name"] = _hv["top_cut_name_cn"] if _cn else _hv["top_cut_name_en"]
    st.markdown(i18n.t("hc.hc.verdict", **_hv))

    _name_col = "name_cn" if _cn else "name_en"
    _chart_col, _tbl_col = st.columns([5, 6])
    with _chart_col:
        fig_hc = charts.headcount_diverging_bar(
            _hc[_name_col].tolist(), _hc["delta"].tolist(),
            title=i18n.t("hc.hc.chart.title"), xlabel=i18n.t("hc.hc.chart.xlabel"),
        )
        st.plotly_chart(fig_hc, width="stretch", theme=None, config={"displayModeBar": False})
        st.caption(i18n.t("hc.hc.legend"))

    with _tbl_col:
        c_co, c_tk = i18n.t("hc.hc.col.company"), i18n.t("hc.hc.col.ticker")
        c_a, c_b = i18n.t("hc.hc.col.fy24"), i18n.t("hc.hc.col.fy25")
        c_d, c_p = i18n.t("hc.hc.col.delta"), i18n.t("hc.hc.col.pct")
        _disp = pd.DataFrame({
            c_co: _hc[_name_col],
            c_tk: _hc["ticker"],
            c_a: _hc["fy2024"],
            c_b: _hc["fy2025"],
            c_d: _hc["delta"],
            c_p: _hc["pct"],
        })
        ui.render_styled_table(
            _disp,
            int_cols=[c_a, c_b, c_d],
            pct_decimal_cols=[c_p],
            text_cols=[c_co, c_tk],
            hide_index=True,
            height=460,
        )

    theme.eyebrow(i18n.t("hc.read.eyebrow"))
    st.markdown(i18n.t("hc.hc.read"))
    st.caption(i18n.t("hc.hc.source"))
    st.download_button(
        i18n.t("hc.dl.xlsx"), data=hcx.headcount_bytes(),
        file_name="HC_员工人数变化_headcount_2025.xlsx",
        mime=_XLSX_MIME, key="dl_hc_headcount",
    )

st.divider()

# --- Per-sector top 3 movers / drags ---
theme.section_header(i18n.t("hc.section.movers"))

name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
for sec in cfg["sectors"]:
    rets = all_returns_by_sector.get(sec["id"])
    if rets is None or rets.empty:
        continue
    with st.expander(f"**{i18n.sector_name(sec['id'])}**  ({len(rets)} tickers)"):
        rets = rets.copy()
        rets["name"] = rets.index.map(name_map)
        rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
        rets.index.name = "Ticker"

        rename_map = {"name": "Name", "last": "Last",
                      "1d_%": "1D %", "5d_%": "5D %",
                      "1m_%": "1M %", "ytd_%": "YTD %"}
        c1, c2 = st.columns(2)
        gainers = rets.sort_values("1d_%", ascending=False).head(3).rename(columns=rename_map)
        drags = rets.sort_values("1d_%", ascending=True).head(3).rename(columns=rename_map)
        # n2: Bloomberg ticker style
        gainers.index = [fmt.fmt_ticker_bbg(t) for t in gainers.index]
        drags.index = [fmt.fmt_ticker_bbg(t) for t in drags.index]
        with c1:
            st.markdown(f"**{i18n.t('hc.movers.gainers')}**")
            _render_pct_table(
                gainers,
                pct_cols=["1D %", "5D %", "1M %", "YTD %"],
                num_cols=["Last"],
                column_labels=i18n.common_cols(),
            )
        with c2:
            st.markdown(f"**{i18n.t('hc.movers.drags')}**")
            _render_pct_table(
                drags,
                pct_cols=["1D %", "5D %", "1M %", "YTD %"],
                num_cols=["Last"],
                column_labels=i18n.common_cols(),
            )

# --- Onboarding ---
with st.expander(i18n.t("hc.onboarding.title")):
    st.markdown(i18n.t("hc.onboarding.body"))
