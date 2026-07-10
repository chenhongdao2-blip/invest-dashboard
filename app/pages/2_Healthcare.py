"""Healthcare domain overview — 7 sub-sectors summary."""

from __future__ import annotations

import re as _re

import pandas as pd
import streamlit as st
from pathlib import Path

from lib import benchmarks as bm
from lib import charts
from lib import db
from lib import format as fmt
from lib import hc_overview as hco
from lib import hc_exports as hcx
from lib import fund_13f as f13
from lib import fund_13f_matrix as f13m
from lib import ui
from lib import theme
from lib import i18n
from lib import rs_panel
from lib import sector_overview as so


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

# Per-section staleness thresholds (days) — mirror .claude/hooks/hc-staleness.mjs so the
# in-app ⚠ and the SessionStart reminder agree. These sources (iFind / local xlsx /
# hand-curated annuals) can't auto-refresh on Cloud, so the badge guarantees stale data
# never silently reads as live. See docs/healthcare-data-pipeline.md.
from datetime import date as _date
_STALE_DAYS = {"rs": 35, "hshci": 45, "pos": 135, "hc": 300, "jp": 7, "f13": 140}


def _stale_note(latest_iso, key: str) -> None:
    """Render a ⚠ if this section's latest data date is past its cadence threshold."""
    if not latest_iso:
        return
    try:
        d = _date.fromisoformat(str(latest_iso)[:10])
    except ValueError:
        return
    age = (_date.today() - d).days
    if age > _STALE_DAYS.get(key, 10**9):
        st.warning(i18n.t("hc.stale.warn", days=age, asof=str(latest_iso)[:10]))


cfg = db.load_domain_cfg(str(DOMAIN_CFG))
i18n.init_lang()
i18n.render_lang_toggle()
theme.page_header(i18n.t("hc.title"))
st.caption(cfg.get("description", "").strip())
prefer_cn = i18n.get_lang() == "zh"
theme.page_radial_wash(1240)

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

# --- Domain benchmark snapshot — [10] sector_overview (sparkline + 发散色阶 + 相对标普条) ---
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    _present = [s for s in focus if s in bench_df.index]
    _cs = bm.close_series()
    _gspc_ytd = bench_df.loc["^GSPC", "ytd_%"] if "^GSPC" in bench_df.index else None
    _pmap = {"1日": "1d_%", "5日": "5d_%", "1月": "1m_%", "3月": "3m_%", "YTD": "ytd_%"}
    _rows = []
    for _s in _present:
        _r = bench_df.loc[_s]
        _ser = _cs.get(_s)
        _spark = ([float(v) for v in _ser.dropna().sort_index().tail(30).tolist()]
                  if _ser is not None else [])
        _ytd = _r["ytd_%"]
        _rel = (float(_ytd) - float(_gspc_ytd)
                if (_gspc_ytd is not None and not pd.isna(_ytd) and not pd.isna(_gspc_ytd)) else None)
        _rows.append({
            "tk": _s,
            "name": i18n.bench_name(_s, _r["name"]),
            "periods": {lbl: (None if pd.isna(_r[col]) else float(_r[col])) for lbl, col in _pmap.items()},
            "rel_sp": _rel,
            "spark": _spark,
        })
    _asof = db.latest_snapshot_date()
    _src = (f"来源 Yahoo Finance cron EOD · 截至 {_asof} · 仅供参考"
            if i18n.get_lang() == "zh"
            else f"Source: Yahoo Finance cron EOD · as of {_asof} · for reference")
    so.masthead(
        title=i18n.t("hc.section.benchmark"),
        chip="HEALTHCARE",
        subtitle="基准 ETF 分档表现 · 30 日趋势 · 相对标普超额",
        asof=_asof,
        source=_src,
        prefer_cn=prefer_cn,
    )
    so.benchmark_table(_rows, source=_src)

st.divider()

# --- Relative performance: 3 paired index comparisons (Jonah) ----------------
# HSHCI vs HSI/HSTECH · NBI vs Nasdaq · S&P HC vs S&P. Source series baked by
# jobs/build_hc_overview_data.py (HK = iFind, US = yfinance) — cloud can't fetch live.
theme.section_header(i18n.t("hc.rs.section"), meta=i18n.t("hc.rs.section_meta"))
_idx = hco.load_index_comparison()
if _idx.empty:
    st.caption(i18n.t("hc.rs.empty"))
else:
    _cn = i18n.get_lang() == "zh"
    _asof = _idx["date"].max().date().isoformat()
    st.caption(i18n.t("hc.rs.win.meta"))   # REBASED 说明行；窗口控件在每张卡片右上角

    _PANEL_TITLE = {"hk": "hc.rs.hk.title", "msci": "hc.rs.msci.title",
                    "nbi": "hc.rs.nbi.title", "sphc": "hc.rs.sphc.title",
                    "ai_bio": "hc.rs.aibio.title"}
    # Design-source card chrome (相对表现 区间筛选 美化.dc.html): per-panel accent
    # top-bar + numbered kicker + chart px height. Cross-sector colouring is
    # series_id-keyed: biotech family (XBI) = CMSI-red so it isn't mistaken for
    # broad market; AI hardware (^SOX) = teal solid, visually apart from red biotech.
    _P_CHROME = {"hk":     (theme.CMSI_RED, 340, "hc.rs.kicker.hk"),
                 "msci":   (theme.INK,      300, "hc.rs.kicker.msci"),
                 "nbi":    (theme.INK,      260, "hc.rs.kicker.nbi"),
                 "sphc":   (theme.INK,      260, "hc.rs.kicker.sphc"),
                 "ai_bio": (theme.UP,       300, "hc.rs.kicker.aibio")}
    _P_STYLE = {"HSI.HK":    {"dash": [6, 4]},
                "HSTECH.HK": {"dash": [2, 3]},
                "XBI":       {"color": theme.CMSI_RED, "dash": [6, 4], "width": 1.5},
                "^SOX":      {"color": theme.UP, "dash": "solid", "width": 1.8}}

    def _rs_series(ser: dict, sid: str, *, hero: bool) -> dict:
        """One series payload for rs_panel (design line styles, hero = red solid)."""
        s = ser[sid].dropna()
        sty = _P_STYLE.get(sid, {})
        return {"name": hco.series_name(_idx, sid, prefer_cn=_cn),
                "dates": [d.date().isoformat() for d in s.index],
                "closes": [float(v) for v in s.values],
                "color": theme.CMSI_RED if hero else sty.get("color", "#8f8a84"),
                "dash": "solid" if hero else sty.get("dash", [6, 4]),
                "width": 2.2 if hero else sty.get("width", 1.4),
                "hero": hero}

    def _render_rs_panel(panel_id: str, *, src: str = "iFind · yfinance") -> None:
        hero_id, peer_ids = next((h, p) for pid, h, p in hco.PANELS if pid == panel_id)
        ser = hco.panel_series(_idx, panel_id)
        if hero_id not in ser:
            return
        accent, chart_h, kicker_key = _P_CHROME[panel_id]
        _series = ([_rs_series(ser, p, hero=False) for p in peer_ids if p in ser]
                   + [_rs_series(ser, hero_id, hero=True)])
        doc, h = rs_panel.render_panel({
            "pid": panel_id, "kicker": i18n.t(kicker_key),
            "title": i18n.t(_PANEL_TITLE[panel_id]), "accent": accent,
            "chart_h": chart_h, "src": src, "asof": _asof, "series": _series,
        }, prefer_cn=_cn)
        st.iframe(doc, height=h)

    _render_rs_panel("hk")                          # headline: 3-line HK comparison, full width

    # MSCI 口径（ETF 代理）— 与 HK 口径并列的「全中国医疗 beta vs 全中国宽基」。KURE/MCHI 是
    # ETF 市价(USD·含息)，非 MSCI 指数本体(免费源/iFind 都拿不到)，故 title + caption 双重标注
    # 「ETF 代理」。之后的 note 讲清两个医疗指数的成分与区别。
    if "KURE" in hco.panel_series(_idx, "msci"):
        _render_rs_panel("msci", src=i18n.t("hc.rs.msci.src"))
        # 释义 · GLOSSARY 结构化对照卡（zip4 设计，替换旧 md_note 长段落）
        _gdoc, _gh = rs_panel.render_hc_glossary({k: i18n.t(f"hc.rs.gl.{k}") for k in (
            "eyebrow", "title", "sub_right", "comp_label", "feat_label", "how_label",
            "note_right", "badge1", "name1", "tag1", "chip1a", "chip1b", "comp1", "feat1",
            "badge2", "name2", "tag2", "chip2a", "chip2b", "comp2", "feat2", "how1", "how2",
        )}, height=350)
        st.iframe(_gdoc, height=_gh)

    _c1, _c2 = st.columns(2)
    with _c1:
        # nbi carries 3 lines: ^NBI (red hero) · XBI (red dashed = biotech family) ·
        # Nasdaq (grey = broad market). XBI styled red so it doesn't read as "broad market".
        _render_rs_panel("nbi")
    with _c2:
        _render_rs_panel("sphc")

    # Cross-sector theme: biotech (NBI + XBI, red family) vs AI hardware (^SOX, teal).
    # Full-width below the supporting pair — the "rotation between the two hottest themes"
    # read. Hero = NBI (red), XBI red-dashed, ^SOX teal solid so the sectors separate.
    if "^SOX" in hco.panel_series(_idx, "ai_bio"):
        _render_rs_panel("ai_bio")
        # ink 释义卡（墨底 cream 字——与白玻璃图表卡分层；markdown 粗体 → <b>）
        _note_html = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", i18n.t("hc.rs.aibio.note"))
        _ndoc, _nh = rs_panel.render_ink_note(
            "释义 · 怎么读这张图" if _cn else "HOW TO READ THIS CHART",
            _note_html, height=250)
        st.iframe(_ndoc, height=_nh)
    st.caption(i18n.t("hc.rs.footnote"))   # 口径脚注（设计稿底部：pp 徽章 + 窗口语义）

    # HSHCI full-cycle context (calendar time, absolute level): −70% → 翻倍 → 回调.
    # Milestones (start/trough/recovery-peak/now) computed from data — never hardcoded.
    # Card format = rs_panel family (George 2026-07-10: 跟上面的 format 一样).
    _hist = hco.load_hshci_history()
    if not _hist.empty:
        _hd = _hist.sort_values("date").reset_index(drop=True)
        _itr = int(_hd["close"].idxmin())
        _ipk = int(_hd["close"].iloc[_itr:].idxmax())
        _inow = len(_hd) - 1
        _ms = hco.hshci_milestones(_hd)

        def _ann(i: int, text: str, pos: str) -> dict:
            return {"d": _hd["date"].iloc[i].date().isoformat(),
                    "v": float(_hd["close"].iloc[i]), "t": text, "pos": pos}

        _anns = [
            _ann(0, i18n.t("hc.rs.hshci.ann.start", c=float(_hd["close"].iloc[0])), "right"),
            _ann(_itr, i18n.t("hc.rs.hshci.ann.trough", c=float(_hd["close"].iloc[_itr]),
                              p=_ms["trough"]["pct_start"]), "bottom"),
            _ann(_ipk, i18n.t("hc.rs.hshci.ann.peak", c=float(_hd["close"].iloc[_ipk]),
                              p=_ms["peak"]["pct_trough"]), "left"),
            _ann(_inow, i18n.t("hc.rs.hshci.ann.now", c=float(_hd["close"].iloc[_inow]),
                               p=_ms["now"]["pct_peak"]), "top"),
        ]
        _hist_asof0 = str(_hd["asof"].iloc[0]) if "asof" in _hd.columns else _hd["date"].max().date().isoformat()
        _dochist, _hhist = rs_panel.render_history_panel({
            "kicker": i18n.t("hc.rs.hshci.kicker"), "title": i18n.t("hc.rs.hshci.title"),
            "chip": i18n.t("hc.rs.hshci.chip"), "accent": theme.CMSI_RED, "chart_h": 340,
            "src": i18n.t("hc.rs.hshci.src"), "asof": _hist_asof0, "name": "HSHCI",
            "dates": [d.date().isoformat() for d in _hd["date"]],
            "closes": [float(v) for v in _hd["close"]],
            "anns": _anns,
            "chips": [
                {"k": i18n.t("hc.rs.hshci.vs_peak"), "v": f"{_ms['now']['pct_peak']:+.1%}",
                 "neg": _ms["now"]["pct_peak"] < 0},
                {"k": i18n.t("hc.rs.hshci.vs_start"), "v": f"{_ms['now']['pct_start']:+.1%}",
                 "neg": _ms["now"]["pct_start"] < 0},
            ],
        }, prefer_cn=_cn)
        st.iframe(_dochist, height=_hhist)
        _hist_asof = str(_hd["asof"].iloc[0]) if "asof" in _hd.columns else _hd["date"].max().date().isoformat()
        st.caption(i18n.t(
            "hc.rs.hshci.caption",
            start_d=_ms["start"]["date"], start_c=_ms["start"]["close"],
            trough_d=_ms["trough"]["date"], trough_c=_ms["trough"]["close"], trough_pct=_ms["trough"]["pct_start"],
            peak_d=_ms["peak"]["date"], peak_c=_ms["peak"]["close"], peak_pct=_ms["peak"]["pct_trough"],
            now_d=_ms["now"]["date"], now_c=_ms["now"]["close"],
            now_peak=_ms["now"]["pct_peak"], now_start=_ms["now"]["pct_start"], asof=_hist_asof,
        ))
        _stale_note(_hist_asof, "hshci")

    theme.eyebrow(i18n.t("hc.read.eyebrow"))         # cross-market read (biotech-researcher Agent)
    st.markdown(i18n.t("hc.rs.read"))
    st.download_button(
        i18n.t("hc.dl.xlsx"), data=hcx.relative_bytes(),
        file_name="HC_相对表现_relative_performance.xlsx",
        mime=_XLSX_MIME, key="dl_hc_relative",
    )
    _stale_note(_asof, "rs")   # _asof = 相对表现指数序列最新日期

st.divider()

# --- Japan Healthcare: 区域 universe（hc_japan.yml, 40 支 iFind 自选清单）--------
# regions key 不进 7-sector taxonomy；价格走 prices_daily EOD cron（JPY→USD 已转，
# M1 口径）。专栏指数 = 40 支等权；TOPIX 用 1305.T ETF 代理（yfinance 无 ^TPX；
# 1306.T 因 2026-03-30 拆股 Yahoo 未复权弃用）。
theme.section_header(i18n.t("hc.jp.section"), meta=i18n.t("hc.jp.section_meta"))
_jp = hco.jp_universe()
_jp_closes = db.get_close_series_usd(tuple(_jp["ticker"])) if not _jp.empty else pd.DataFrame()
if _jp.empty or _jp_closes.empty:
    st.caption(i18n.t("hc.jp.empty"))
else:
    _cn = i18n.get_lang() == "zh"
    _jp_asof = _jp_closes.index.max().date().isoformat()
    _jp_rets = db.compute_returns(_jp_closes)
    # merge keeps the yml row order (subsector blocks, mcap-desc within block)
    _jpm = _jp.merge(_jp_rets, left_on="ticker", right_index=True, how="inner")

    # ① subsector summary (equal-weight averages, USD)
    _sub_rows = []
    for _s in hco.JP_SUBSECTOR_ORDER:
        _grp = _jpm[_jpm["subsector"] == _s]
        if _grp.empty:
            continue
        _sub_rows.append({
            "Subsector": i18n.t(f"hc.jp.sub.{_s}"),
            "Tickers": len(_grp),
            "1D % avg": _grp["1d_%"].mean(),
            "5D % avg": _grp["5d_%"].mean(),
            "1M % avg": _grp["1m_%"].mean(),
            "YTD % avg": _grp["ytd_%"].mean(),
        })
    if _sub_rows:
        _render_pct_table(
            pd.DataFrame(_sub_rows).set_index("Subsector"),
            pct_cols=["1D % avg", "5D % avg", "1M % avg", "YTD % avg"],
            column_labels={
                "Subsector": i18n.t("hc.jp.col.subsector"),
                "Tickers": i18n.t("hc.col.tickers"),
                "1D % avg": i18n.t("hc.col.1d_avg"),
                "5D % avg": i18n.t("hc.col.5d_avg"),
                "1M % avg": i18n.t("hc.col.1m_avg"),
                "YTD % avg": i18n.t("hc.col.ytd_avg"),
            },
        )

    # ② composite vs TOPIX vs Nikkei — same FT framing as the rs panels above
    _comp = hco.jp_composite(
        _jp_closes, weights=_jp.set_index("ticker")["mcap_bn_jpy"]
        if "mcap_bn_jpy" in _jp.columns else None)
    _jpb = hco.jp_benchmarks_usd()
    if _comp is not None and _jpb:
        # Same design-source card as the 相对表现 panels — per-chart 5D/1M/6M/全程
        # control lives in the card's own header (client-side, re-anchors in window).
        def _jp_series(name: str, s, *, hero: bool, dash="solid") -> dict:
            s = s.dropna()
            return {"name": name,
                    "dates": [pd.Timestamp(d).date().isoformat() for d in s.index],
                    "closes": [float(v) for v in s.values],
                    "color": theme.CMSI_RED if hero else "#8f8a84",
                    "dash": "solid" if hero else dash,
                    "width": 2.2 if hero else 1.4, "hero": hero}

        _jser = []
        if "1305.T" in _jpb:
            _jser.append(_jp_series(i18n.t("hc.jp.bench.topix"), _jpb["1305.T"],
                                    hero=False, dash=[6, 4]))
        if "^N225" in _jpb:
            _jser.append(_jp_series(i18n.t("hc.jp.bench.n225"), _jpb["^N225"],
                                    hero=False, dash=[2, 3]))
        _jser.append(_jp_series(i18n.t("hc.jp.hero"), _comp, hero=True))
        _docjp, _hjp = rs_panel.render_panel({
            "pid": "jp", "kicker": i18n.t("hc.jp.kicker"),
            "title": i18n.t("hc.jp.chart.title"), "accent": theme.INK,
            "chart_h": 300, "src": "yfinance EOD cron", "asof": _jp_asof,
            "series": _jser,
        }, prefer_cn=_cn)
        st.iframe(_docjp, height=_hjp)
        st.caption(i18n.t("hc.jp.caption", asof=_jp_asof))

    # ③ full 40-name detail (expander keeps the section weight equal to its peers)
    with st.expander(i18n.t("hc.jp.detail"), expanded=True):   # George: section 不折叠
        _name_col = "name_cn" if _cn else "name_en"
        _dispjp = pd.DataFrame({
            "Name": _jpm[_name_col],
            "Subsector": _jpm["subsector"].map(lambda s: i18n.t(f"hc.jp.sub.{s}")),
            "Last": _jpm["last"],
            "1D %": _jpm["1d_%"],
            "5D %": _jpm["5d_%"],
            "1M %": _jpm["1m_%"],
            "YTD %": _jpm["ytd_%"],
        })
        _dispjp.index = [fmt.fmt_ticker_bbg(t) for t in _jpm["ticker"]]
        _render_pct_table(
            _dispjp,
            pct_cols=["1D %", "5D %", "1M %", "YTD %"],
            num_cols=["Last"],
            column_labels={**i18n.common_cols(),
                           "Subsector": i18n.t("hc.jp.col.subsector")},
        )

    theme.eyebrow(i18n.t("hc.read.eyebrow"))   # pricing-currency layering read
    st.markdown(i18n.t("hc.jp.read"))
    st.caption(i18n.t("hc.jp.note_delisted"))
    st.download_button(
        i18n.t("hc.dl.xlsx"), data=hcx.japan_bytes(),
        file_name="HC_日本医药_japan_healthcare.xlsx",
        mime=_XLSX_MIME, key="dl_hc_japan",
    )
    _stale_note(_jp_asof, "jp")

st.divider()

# --- Institutional positioning: offshore China funds OW/UW on healthcare ------
# Audited fund-positioning xlsx → china_fund_hc_positioning.csv. Diverging bar uses
# the LOCKED teal=OW / red=UW convention; caption spells it out (positioning, not return).
theme.section_header(i18n.t("hc.pos.section"), meta=i18n.t("hc.pos.section_meta"))
_pos = hco.load_fund_positioning()
if _pos.empty:
    st.caption(i18n.t("hc.pos.empty"))
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
    _pos_asof = _pos["data_date"].dropna().astype(str).str[:10].max() if "data_date" in _pos.columns else None
    _stale_note(_pos_asof, "pos")

st.divider()

# --- US HC-dedicated funds 13F: consensus holdings + QoQ moves ----------------
# US-institutional counterpart of the China-fund OW/UW block above. SEC EDGAR
# 13F-HR (public — real fund names, no anon), baked by jobs/fetch_13f_hc_funds.py.
# LOCKED teal=加仓/新建 / red=减仓/清仓 convention; caption spells out it's
# POSITIONING as of the report date (13F lags up to 45 days), not a daily move.
theme.section_header(i18n.t("hc.f13.section"), meta=i18n.t("hc.f13.section_meta"))
_f13 = f13.load_13f()
_f13v = f13.verdict(_f13)
if not _f13v:
    st.caption(i18n.t("hc.f13.empty"))
else:
    st.markdown(i18n.t(
        "hc.f13.verdict",
        n_funds=_f13v["n_funds"], period=_f13v["period"],
        aum=f"{_f13v['total_aum_bn']:.0f}",
        top=_f13v["top_label"], top_n=_f13v["top_n_funds"],
        hot=_f13v["hot_label"], hot_n=_f13v["hot_n_new"],
    ))

    c_name = i18n.t("hc.f13.col.name")
    c_nf, c_val = i18n.t("hc.f13.col.n_funds"), i18n.t("hc.f13.col.value")
    c_new, c_add, c_trim = i18n.t("hc.f13.col.new"), i18n.t("hc.f13.col.add"), i18n.t("hc.f13.col.trim")
    c_funds = i18n.t("hc.f13.col.funds")
    c_spark, c_sq = i18n.t("hc.f13.col.spark"), i18n.t("hc.f13.col.since_qend")

    # Block A — FactSet-style holder × company matrix (replaces the flat consensus
    # table): rows = funds ranked by combined value across the shown names, columns
    # = top-15 consensus holdings with 6M mini-spark + since-Q-end in the header.
    # Cell = that fund's position ($M), TEXT colored by its own QoQ move (teal
    # NEW/ADD, red TRIM, ink UNCH) — house 染字不染底, one dimension over FactSet.
    st.markdown(i18n.t("hc.f13.consensus_h"))
    f13m.render_matrix(
        _f13, top_n=15, prefer_cn=(i18n.get_lang() == "zh"),
        labels={
            "holder": i18n.t("hc.f13.mx.holder"), "total": i18n.t("hc.f13.mx.total"),
            "legend_new": i18n.t("hc.f13.qoq.NEW"), "legend_add": i18n.t("hc.f13.qoq.ADD"),
            "legend_trim": i18n.t("hc.f13.qoq.TRIM"), "legend_unch": i18n.t("hc.f13.mx.unch"),
        },
    )
    st.caption(i18n.t("hc.f13.consensus_note"))

    # Block B — QoQ highlights: hottest new buys / most-crowded exits.
    _buys, _exits = f13.top_new_buys(_f13), f13.top_exits(_f13)
    _bcol, _ecol = st.columns(2)
    with _bcol:
        st.markdown(i18n.t("hc.f13.newbuys_h"))
        if _buys.empty:
            st.caption(i18n.t("hc.f13.none"))
        else:
            _buys = f13.attach_prices(_buys, _f13)
            _buys["total_value"] = _buys["total_value"] / 1e9   # → USD billions
            _b = _buys.head(10).rename(columns={
                "label": c_name, "n_new": c_new, "n_funds": c_nf,
                "total_value": c_val, "funds": c_funds,
                "spark": c_spark, "since_qend_pct": c_sq,
            })[[c_name, c_new, c_nf, c_val, c_spark, c_sq]]
            ui.render_html_table(
                _b, text_cols=[c_name],
                int_cols=[c_new, c_nf], money_b_cols=[c_val],
                spark_cols=[c_spark], pct_decimal_cols=[c_sq],
                hide_index=True, height=420)
    with _ecol:
        st.markdown(i18n.t("hc.f13.exits_h"))
        if _exits.empty:
            st.caption(i18n.t("hc.f13.none"))
        else:
            c_ex = i18n.t("hc.f13.col.n_exits")
            _exits = f13.attach_prices(_exits, _f13)
            _e = _exits.head(10).rename(columns={
                "label": c_name, "n_exits": c_ex, "funds": c_funds,
                "spark": c_spark, "since_qend_pct": c_sq,
            })[[c_name, c_ex, c_spark, c_sq]]
            ui.render_html_table(
                _e, text_cols=[c_name],
                int_cols=[c_ex], spark_cols=[c_spark], pct_decimal_cols=[c_sq],
                hide_index=True, height=420)
    st.caption(i18n.t("hc.f13.legend"))
    _pas = f13.prices_as_of(_f13)
    if _pas:
        st.caption(i18n.t("hc.f13.prices_note", asof=_pas, period=_f13v["period"]))

    # Block C — per-fund top holdings + that fund's QoQ tags.
    st.markdown(i18n.t("hc.f13.perfund_h"))
    _qoq_key = {"NEW": "hc.f13.qoq.NEW", "ADD": "hc.f13.qoq.ADD",
                "TRIM": "hc.f13.qoq.TRIM", "UNCH": "hc.f13.qoq.UNCH"}
    c_w, c_qoq, c_chg = i18n.t("hc.f13.col.weight"), i18n.t("hc.f13.col.qoq"), i18n.t("hc.f13.col.chg")
    for _f in f13.funds_ok(_f13):
        _stale = " ⚠️" if _f.get("status") == "stale" else ""
        _hdr = f"{_f['name']} · ${(_f.get('total_value') or 0)/1e9:.1f}bn · " \
               f"{_f.get('n_positions', 0)} {i18n.t('hc.f13.positions')} · {_f.get('period', '—')}{_stale}"
        with st.expander(_hdr):
            _snap = f13.fund_snapshot(_f)
            if _snap.empty:
                st.caption(i18n.t("hc.f13.none"))
                continue
            _snap["qoq"] = _snap["qoq"].map(lambda s: i18n.t(_qoq_key.get(str(s), "hc.f13.qoq.UNCH")))
            _snap["value"] = _snap["value"] / 1e9   # → USD billions
            _sdisp = _snap.rename(columns={
                "label": c_name, "weight": c_w, "value": c_val,
                "qoq": c_qoq, "shares_chg_pct": c_chg})[[c_name, c_w, c_val, c_qoq, c_chg]]
            ui.render_html_table(
                _sdisp, text_cols=[c_name], status_cols={
                    c_qoq: {i18n.t("hc.f13.qoq.NEW"): "up", i18n.t("hc.f13.qoq.ADD"): "up",
                            i18n.t("hc.f13.qoq.TRIM"): "down", i18n.t("hc.f13.qoq.UNCH"): ""}},
                pct_decimal_cols=[c_w, c_chg], money_b_cols=[c_val],
                hide_index=True, height=min(560, 60 + 36 * len(_sdisp)))

    theme.eyebrow(i18n.t("hc.read.eyebrow"))
    st.markdown(i18n.t("hc.f13.read"))
    st.caption(i18n.t("hc.f13.source"))
    _f13_asof = _f13.get("latest_period")
    _stale_note(_f13_asof, "f13")

st.divider()

# --- Headcount change: China innovative-pharma hirers vs cutters --------------
# 12 names' FY2024→FY2025 GROUP headcount, baked by jobs/cn_pharma_headcount_2025.py
# from 年报业绩公告 / ESG / iFind (cloud can't fetch live). Diverging bar uses the
# LOCKED teal=扩招 / red=收缩 convention; caption spells it out (headcount, not return).
theme.section_header(i18n.t("hc.hc.section"), meta=i18n.t("hc.hc.section_meta"))
_hc = hco.load_headcount()
if _hc.empty:
    st.caption(i18n.t("hc.hc.empty"))
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
    _hc_asof = str(_hc["asof"].iloc[0]) if "asof" in _hc.columns and len(_hc) else None
    _stale_note(_hc_asof, "hc")

st.divider()

# --- Movers — [10] sector_overview: domain-wide top-10 gainers / losers (行内动量条) ---
_name_map = db.ticker_to_name(prefer_cn=(i18n.get_lang() == "zh"))
_all_rets = [df for df in all_returns_by_sector.values() if df is not None and not df.empty]
if _all_rets:
    _combined = pd.concat(_all_rets)
    _combined = _combined[~_combined.index.duplicated(keep="first")]   # 跨子行业去重(一票只算一次)
    _combined = _combined[pd.notna(_combined["1d_%"])]

    def _mv_rows(_df: pd.DataFrame) -> list[dict]:
        return [{"tk": fmt.fmt_ticker_bbg(_tk),
                 "name": _name_map.get(_tk, _tk),
                 "last": (0.0 if pd.isna(_row["last"]) else float(_row["last"])),
                 "d1": float(_row["1d_%"])}
                for _tk, _row in _df.iterrows()]

    _gainers = _mv_rows(_combined.sort_values("1d_%", ascending=False).head(10))
    _losers = _mv_rows(_combined.sort_values("1d_%", ascending=True).head(10))
    so.movers(gainers=_gainers, losers=_losers,
              window=("1 日" if prefer_cn else "1D"), prefer_cn=prefer_cn)

# --- Onboarding ---
with st.expander(i18n.t("hc.onboarding.title"), expanded=True):   # George: section 不折叠
    st.markdown(i18n.t("hc.onboarding.body"))
