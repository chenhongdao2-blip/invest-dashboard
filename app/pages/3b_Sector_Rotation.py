"""板块轮动 · 相对轮动图 (RRG) — A股申万 + 美股GICS 双单市场.

「市场内部注意力地图」：把板块的相对强弱×动量投影到四象限，回答"这个板块的强是否
已被资金定价、走到顺时针哪一步"。与 Sector Heatmap (横截面强弱) 互补。

定位 (周期 agent 研判)：RRG 是正交的"内部时间维度"测量仪，不是择时信号。核心带两条
护栏防误用——①周期级别水印 (lib.regime) ②拥挤度叠加 (lib.crowding)。详见 lib/rrg.py。

数据：A股 = sw_industry_daily (iFind 周线 seed)；美股 = benchmarks_daily (yfinance cron)。
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, i18n, theme, ui
from lib import rrg, crowding, regime

st.set_page_config(page_title="Sector Rotation · invest-dashboard", page_icon="🧭", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()

theme.page_header(i18n.t("rot.title"))
st.caption(i18n.t("rot.caption"))

with st.sidebar:
    ui.sidebar_search(key_prefix="rotation")
    st.divider()
    st.subheader(i18n.t("rot.ctrl.header"))
    tail = st.slider(i18n.t("rot.ctrl.tail"), 4, 12, rrg.TAIL_DEFAULT, 1,
                     help=i18n.t("rot.ctrl.tail_help"))
    thr = st.slider(i18n.t("rot.ctrl.thr"), 1.0, 3.0, crowding.OVERHEAT_Z, 0.1,
                    help=i18n.t("rot.ctrl.thr_help"))

# US GICS sector ETF → 中文名
_US_CN = {
    "XLK": "信息技术", "XLF": "金融", "XLE": "能源", "XLB": "材料", "XLI": "工业",
    "XLY": "可选消费", "XLP": "必需消费", "XLC": "通信服务", "XLU": "公用事业",
    "XLRE": "房地产", "XLV": "医疗保健",
}
_US_EN = {k: v for k, v in {
    "XLK": "Info Tech", "XLF": "Financials", "XLE": "Energy", "XLB": "Materials",
    "XLI": "Industrials", "XLY": "Cons. Disc.", "XLP": "Cons. Staples",
    "XLC": "Comm. Svcs", "XLU": "Utilities", "XLRE": "Real Estate", "XLV": "Health Care",
}.items()}


# HK 恒生综合行业 中文名 → 英文短名
_HK_EN = {
    "金融": "Financials", "地产建筑": "Property", "资讯科技": "Info Tech",
    "医疗保健": "Health Care", "非必需消费": "Cons. Disc.", "必需消费": "Cons. Staples",
    "能源": "Energy", "电讯": "Telecom", "公用事业": "Utilities", "工业": "Industrials",
    "原材料": "Materials",
}


def _sw_frames(market: str, bench_ticker: str) -> dict:
    """从 sw_industry_daily 按 market 取 {sectors, turns, bench}。"""
    df = db.query(
        "SELECT ticker, name_cn, date, close, turnover_rate "
        "FROM sw_industry_daily WHERE market = ? ORDER BY date", [market]
    )
    if df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    out = {"sectors": {}, "turns": {}, "bench": None}
    for tk, g in df.groupby("ticker"):
        g = g.set_index("date").sort_index()
        if tk == bench_ticker:
            out["bench"] = g["close"]
            continue
        name = g["name_cn"].iloc[0]
        out["sectors"][name] = g["close"]
        out["turns"][name] = g["turnover_rate"]
    return out


@st.cache_data(ttl=1800)
def _ashare_frames() -> dict:
    return _sw_frames("a_share", "000300.SH")


@st.cache_data(ttl=1800)
def _hk_frames() -> dict:
    return _sw_frames("hk", "HSI.GI")


@st.cache_data(ttl=1800)
def _us_frames() -> dict:
    tks = list(_US_CN) + ["^GSPC"]
    q = "SELECT ticker, date, close FROM benchmarks_daily WHERE ticker IN (%s) ORDER BY date" % ",".join("?" * len(tks))
    df = db.query(q, tks)
    if df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    out = {"closes": {}, "bench": None}
    for tk, g in df.groupby("ticker"):
        s = g.set_index("date").sort_index()["close"]
        if tk == "^GSPC":
            out["bench"] = s
        else:
            out["closes"][tk] = s
    return out


def _render_market(market: str, prefer_cn: bool) -> None:
    if market in ("a_share", "hk"):
        fr = _ashare_frames() if market == "a_share" else _hk_frames()
        empty_key = "rot.empty.a" if market == "a_share" else "rot.empty.hk"
        if not fr or fr.get("bench") is None or not fr["sectors"]:
            st.warning(i18n.t(empty_key))
            return
        sectors, turns = fr["sectors"], fr["turns"]
        if market == "hk" and not prefer_cn:           # 港股板块切英文名
            sectors = {_HK_EN.get(k, k): v for k, v in sectors.items()}
            turns = {_HK_EN.get(k, k): v for k, v in turns.items()}
        bench = fr["bench"]
        points = rrg.compute_rrg(sectors, bench, tail=tail)
        meta = {}
        for p in points:
            cz = crowding.turnover_z(turns.get(p.label))
            meta[p.label] = {"overheated": crowding.is_overheated(p.quadrant, cz, thr=thr), "cz": cz}
        if market == "a_share":
            mkt_label = "A股 · 申万/中证行业" if prefer_cn else "A-share · SW/CSI sectors"
        else:
            mkt_label = "港股 · 恒生综合行业" if prefer_cn else "HK · HS sectors"
    else:
        fr = _us_frames()
        if not fr or fr.get("bench") is None or not fr["closes"]:
            st.warning(i18n.t("rot.empty.us"))
            return
        name_map = _US_CN if prefer_cn else _US_EN
        sectors = {name_map[tk]: s for tk, s in fr["closes"].items()}
        bench = fr["bench"]
        points = rrg.compute_rrg(sectors, bench, tail=tail)
        # 美股 crowding = 价格拉伸 z (close-only 代理；真换手/breadth 留 v2)
        rev = {name_map[tk]: tk for tk in fr["closes"]}
        meta = {}
        for p in points:
            cz = crowding.extension_z(fr["closes"][rev[p.label]], sma_win=200, z_win=252)
            meta[p.label] = {"overheated": crowding.is_overheated(p.quadrant, cz, thr=thr), "cz": cz}
        mkt_label = "美股 · GICS" if prefer_cn else "US · GICS"

    reg = regime.regime_banner(market, bench, prefer_cn=prefer_cn)
    as_of = bench.dropna().index.max()
    as_of = as_of.date().isoformat() if as_of is not None else None
    doc, h = rrg.render_rrg_html(points, meta, prefer_cn=prefer_cn,
                                 market_label=mkt_label, regime=reg, as_of=as_of, tail=tail)
    st.iframe(doc, height=h)


prefer_cn = i18n.get_lang() == "zh"
tab_a, tab_hk, tab_us = st.tabs([i18n.t("rot.tab.a"), i18n.t("rot.tab.hk"), i18n.t("rot.tab.us")])
with tab_a:
    _render_market("a_share", prefer_cn)
    st.caption(i18n.t("rot.note.a"))
with tab_hk:
    _render_market("hk", prefer_cn)
    st.caption(i18n.t("rot.note.hk"))
with tab_us:
    _render_market("us", prefer_cn)
    st.caption(i18n.t("rot.note.us"))

with st.expander(i18n.t("rot.onboard.title")):
    st.markdown(i18n.t("rot.onboard.body"))
