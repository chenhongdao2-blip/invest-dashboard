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


# ── 个股下沉 (drill) — 美股子板块成分股 vs 等权合成板块指数 ──────────────────
# 项目子板块 slug → 双语展示名 (universe_member.sector 是 slug)
_DOMAIN_CN = {"ai": "AI/科技", "healthcare": "医疗保健", "software": "软件"}
_DOMAIN_EN = {"ai": "AI/Tech", "healthcare": "Healthcare", "software": "Software"}
_SECTOR_CN = {
    "ai_server": "AI服务器", "ai_chip": "AI芯片", "ai_interconnect": "互联/光模块",
    "ai_equip": "半导体设备", "ai_foundry": "晶圆代工", "ai_memory": "存储",
    "biotech": "生物科技", "cxo": "CXO", "pharma": "大药企", "hc_ai": "医疗AI",
    "hospital_care": "医院/医疗服务", "managed_care": "管理式医疗", "medtech": "医疗器械",
    "saas_comps": "SaaS",
}
_SECTOR_EN = {
    "ai_server": "AI Servers", "ai_chip": "AI Chips", "ai_interconnect": "Interconnect/Optics",
    "ai_equip": "Semicap", "ai_foundry": "Foundry", "ai_memory": "Memory",
    "biotech": "Biotech", "cxo": "CXO", "pharma": "Pharma", "hc_ai": "Health AI",
    "hospital_care": "Hospital/Care", "managed_care": "Managed Care", "medtech": "MedTech",
    "saas_comps": "SaaS",
}


@st.cache_data(ttl=1800)
def _us_drill_sectors() -> pd.DataFrame:
    """美股可下沉的项目子板块 (region=US, ≥4 只有价成分; 排除 _coverage 桶)。"""
    return db.query(
        "SELECT u.domain, u.sector, COUNT(DISTINCT u.ticker) AS n "
        "FROM universe_member u "
        "JOIN (SELECT DISTINCT ticker FROM prices_daily WHERE currency='USD') p "
        "  ON p.ticker = u.ticker "
        "WHERE u.region = 'US' AND u.sector <> '_coverage' "
        "GROUP BY u.domain, u.sector HAVING n >= 4 "
        "ORDER BY u.domain, n DESC"
    )


@st.cache_data(ttl=1800)
def _us_drill_frames(domain: str, sector: str) -> dict:
    """{closes(wide,close), adv(20d 成交额)} — 某美股子板块成分股。"""
    members = db.sector_tickers(domain, sector)
    members = members[members["region"] == "US"]
    tks = tuple(members["ticker"])
    if not tks:
        return {}
    closes = db.get_close_series(tks)
    if closes.empty:
        return {}
    ph = ",".join("?" * len(tks))
    adv = db.query(
        f"SELECT ticker, AVG(dv) AS adv FROM ("
        f"  SELECT ticker, close * volume AS dv, "
        f"  ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) AS rn "
        f"  FROM prices_daily WHERE ticker IN ({ph}) AND volume IS NOT NULL"
        f") WHERE rn <= 20 GROUP BY ticker",
        tks,
    )
    return {"closes": closes, "adv": dict(zip(adv["ticker"], adv["adv"]))}


def _render_drill(prefer_cn: bool) -> None:
    secs = _us_drill_sectors()
    if secs.empty:
        st.warning(i18n.t("rot.drill.empty"))
        return
    dom_lbl = _DOMAIN_CN if prefer_cn else _DOMAIN_EN
    sec_lbl = _SECTOR_CN if prefer_cn else _SECTOR_EN
    domains = list(dict.fromkeys(secs["domain"]))

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c1:
        dom = st.selectbox(i18n.t("rot.drill.domain"), domains,
                           format_func=lambda d: dom_lbl.get(d, d), key="drill_dom")
    sub = secs[secs["domain"] == dom].reset_index(drop=True)
    with c2:
        sector = st.selectbox(
            i18n.t("rot.drill.sector"), list(sub["sector"]),
            format_func=lambda s: f"{sec_lbl.get(s, s)} "
            f"({int(sub.loc[sub['sector'] == s, 'n'].iloc[0])})",
            key="drill_sec")
    with c3:
        top_n = st.slider(i18n.t("rot.drill.topn"), 6, 20, 12, 1,
                          help=i18n.t("rot.drill.topn_help"), key="drill_topn")

    fr = _us_drill_frames(dom, sector)
    if not fr or fr["closes"].empty:
        st.warning(i18n.t("rot.drill.empty"))
        return
    closes = fr["closes"]
    # 过滤历史不足的成分：prices_daily 里晚加入采集的票可能只有几天数据，喂进
    # compute_rrg 会退化成 100/100 占位点、堆在 Leading 角误导。compute_rrg 需
    # ≥ w_r+2≈22 周 ≈ ~110 交易日；取 120 留余量。合成指数也只用合格成分，避免
    # breadth 在中途跳变 (满史 3 只 + 新票 22 只会让合成指数失真)。
    MIN_DAYS = 120
    counts = closes.count()
    qualified = [t for t in closes.columns if counts.get(t, 0) >= MIN_DAYS]
    n_total = len(closes.columns)
    n_short = n_total - len(qualified)
    if len(qualified) < 3:
        st.warning(i18n.t("rot.drill.empty"))
        return
    closes_q = closes[qualified]
    composite = rrg.equal_weight_composite(closes_q)        # 合格成分 → 一致 breadth 合成指数
    if composite.empty:
        st.warning(i18n.t("rot.drill.empty"))
        return

    # 按 20d 成交额(流动性) top-N 截断绘制；label = ticker (短、不重叠、双语通用)
    ranked = sorted(qualified, key=lambda t: fr["adv"].get(t, 0.0), reverse=True)
    shown = ranked[:top_n]
    sectors = {t: closes_q[t] for t in shown}
    points = rrg.compute_rrg(sectors, composite, tail=tail)

    # 个股拥挤度 = 价格拉伸 z；prices_daily 仅 ~9 月 → 短窗 (50日均线/120日 z)
    meta = {}
    for p in points:
        cz = crowding.extension_z(closes_q[p.label], sma_win=50, z_win=120)
        meta[p.label] = {"overheated": crowding.is_overheated(p.quadrant, cz, thr=thr), "cz": cz}

    sec_name = sec_lbl.get(sector, sector)
    mkt_label = (f"美股下沉 · {sec_name}" if prefer_cn else f"US drill · {sec_name}")
    reg = regime.regime_banner("us_drill", composite, prefer_cn=prefer_cn)   # 合成指数 auto 兜底
    as_of = composite.dropna().index.max()
    as_of = as_of.date().isoformat() if as_of is not None else None
    doc, h = rrg.render_rrg_html(points, meta, prefer_cn=prefer_cn,
                                 market_label=mkt_label, regime=reg, as_of=as_of, tail=tail)
    st.iframe(doc, height=h)
    notes = []
    if len(shown) < len(qualified):
        notes.append(i18n.t("rot.drill.trunc").format(shown=len(shown), total=len(qualified)))
    if n_short:
        notes.append(i18n.t("rot.drill.short").format(n=n_short))
    if notes:
        st.caption("  ·  ".join(notes))


# ── 跨市场 USD 同框 (tab 4) — A/港/美板块统一换 USD vs MSCI World + 护栏③汇率剥离 ──
_MKT_COLOR = {"a_share": "#5b6ee1", "hk": "#e6a23c", "us": "#16a085"}   # 按市场配色 (非强弱)
_MKT_TAG = {"a_share": "A", "hk": "HK", "us": "US"}
_MKT_NAME_CN = {"a_share": "A股", "hk": "港股", "us": "美股"}
_MKT_NAME_EN = {"a_share": "A-share", "hk": "HK", "us": "US"}


@st.cache_data(ttl=1800)
def _xmkt_raw() -> dict:
    """跨市场原始序列: 各市场板块本币 close + FX(CNY=X/HKD=X) + URTH(MSCI World, USD)。"""
    out: dict = {"sectors": {}, "fx": {}, "urth": None}
    sw = db.query(
        "SELECT market, ticker, name_cn, date, close FROM sw_industry_daily "
        "WHERE market IN ('a_share','hk') ORDER BY date"
    )
    if not sw.empty:
        sw["date"] = pd.to_datetime(sw["date"])
        bench_tk = {"a_share": "000300.SH", "hk": "HSI.GI"}
        for (mkt, tk), g in sw.groupby(["market", "ticker"]):
            if tk == bench_tk.get(mkt):
                continue
            g = g.set_index("date").sort_index()
            out["sectors"].setdefault(mkt, {})[g["name_cn"].iloc[0]] = g["close"]
    extra = list(_US_CN) + ["URTH", "CNY=X", "HKD=X"]
    q = ("SELECT ticker, date, close FROM benchmarks_daily WHERE ticker IN (%s) ORDER BY date"
         % ",".join("?" * len(extra)))
    bm = db.query(q, extra)
    if not bm.empty:
        bm["date"] = pd.to_datetime(bm["date"])
        for tk, g in bm.groupby("ticker"):
            s = g.set_index("date").sort_index()["close"]
            if tk == "URTH":
                out["urth"] = s
            elif tk in ("CNY=X", "HKD=X"):
                out["fx"][tk] = s
            elif tk in _US_CN:
                out["sectors"].setdefault("us", {})[_US_CN[tk]] = s
    return out


def _xmkt_fx_note(raw: dict, sel: list[str], prefer_cn: bool) -> str:
    """期内 (trailing ~52 周) 本币 vs USD 变动摘要 (护栏③ 量化: + = 本币贬值压低板块 USD 表现)。"""
    pairs = {"a_share": ("CNY=X", "USDCNY"), "hk": ("HKD=X", "USDHKD")}
    parts = []
    for m in sel:
        if m not in pairs:
            continue
        tk, disp = pairs[m]
        s = raw["fx"].get(tk)
        if s is None or s.dropna().empty:
            continue
        s = s.dropna().sort_index()
        win = s[s.index >= s.index.max() - pd.Timedelta(days=364)]
        if len(win) < 2:
            continue
        chg = (float(win.iloc[-1]) / float(win.iloc[0]) - 1) * 100
        parts.append(f"{disp} {chg:+.1f}%")
    if not parts:
        return ""
    lead = "期内汇率（本币/USD）：" if prefer_cn else "FX over window (local/USD): "
    tail_txt = ("　·　+ = 本币贬值 → 压低该市场板块的 USD 相对表现（护栏③：USD 面板含此效应，剥离面板已扣除）"
                if prefer_cn else
                "　·　+ = local depreciation → drags that market's sectors in USD (guardrail ③: USD panel includes it, stripped panel removes it)")
    return lead + "　".join(parts) + tail_txt


def _render_xmkt(prefer_cn: bool) -> None:
    raw = _xmkt_raw()
    if raw.get("urth") is None or not raw.get("sectors"):
        st.warning(i18n.t("rot.xmkt.empty"))
        return
    mkt_name = _MKT_NAME_CN if prefer_cn else _MKT_NAME_EN
    avail = [m for m in ("a_share", "hk", "us") if raw["sectors"].get(m)]

    c1, c2 = st.columns([2.2, 1])
    with c1:
        sel = st.multiselect(i18n.t("rot.xmkt.markets"), avail, default=avail,
                             format_func=lambda m: mkt_name[m], key="xmkt_mkts")
    with c2:
        per_n = st.slider(i18n.t("rot.xmkt.pern"), 4, 10, 6, 1,
                          help=i18n.t("rot.xmkt.pern_help"), key="xmkt_pern")
    if not sel:
        st.info(i18n.t("rot.xmkt.pick"))
        return

    fx_for = {"a_share": raw["fx"].get("CNY=X"), "hk": raw["fx"].get("HKD=X"), "us": None}
    urth = raw["urth"]
    live, frozen, mkt_of = {}, {}, {}
    for m in sel:
        tag = _MKT_TAG[m]
        for name, s_local in raw["sectors"][m].items():
            usd_live = rrg.usd_convert(s_local, fx_for[m], freeze=False)
            if usd_live.empty:
                continue
            lbl = f"{tag}·{name}"
            live[lbl] = usd_live
            frozen[lbl] = rrg.usd_convert(s_local, fx_for[m], freeze=True)
            mkt_of[lbl] = m
    if not live:
        st.warning(i18n.t("rot.xmkt.empty"))
        return

    pts_live_all = rrg.compute_rrg(live, urth, tail=tail)
    # 每市场按偏离度 (|RSR-100|+|RSM-100|) 取 top-N，避免 53 个板块挤爆画布
    bymkt: dict[str, list] = {}
    for p in pts_live_all:
        bymkt.setdefault(mkt_of[p.label], []).append(p)
    keep = set()
    for m, ps in bymkt.items():
        ps.sort(key=lambda p: abs(p.rs_ratio - 100) + abs(p.rs_momentum - 100), reverse=True)
        keep.update(p.label for p in ps[:per_n])
    pts_live = [p for p in pts_live_all if p.label in keep]
    pts_frz = rrg.compute_rrg({l: frozen[l] for l in keep if l in frozen}, urth, tail=tail)

    colors = {l: _MKT_COLOR[mkt_of[l]] for l in keep}
    glegend = [(mkt_name[m], _MKT_COLOR[m]) for m in sel]
    reg = regime.regime_banner("world", urth, prefer_cn=prefer_cn)
    as_of = urth.dropna().index.max()
    as_of = as_of.date().isoformat() if as_of is not None else None

    fxnote = _xmkt_fx_note(raw, sel, prefer_cn)
    if fxnote:
        st.caption("💱 " + fxnote)

    lab_usd = "跨市场 · USD 同框（含汇率）" if prefer_cn else "Cross-market · USD (incl. FX)"
    lab_frz = "跨市场 · 汇率剥离（板块本币驱动）" if prefer_cn else "Cross-market · FX-stripped (local-driven)"
    doc1, h1 = rrg.render_rrg_html(pts_live, {}, prefer_cn=prefer_cn, market_label=lab_usd,
                                   regime=reg, as_of=as_of, tail=tail,
                                   point_colors=colors, group_legend=glegend)
    st.iframe(doc1, height=h1)
    st.caption(i18n.t("rot.xmkt.panel_frozen"))
    doc2, h2 = rrg.render_rrg_html(pts_frz, {}, prefer_cn=prefer_cn, market_label=lab_frz,
                                   regime=None, as_of=as_of, tail=tail,
                                   point_colors=colors, group_legend=glegend)
    st.iframe(doc2, height=h2)


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
tab_a, tab_hk, tab_us, tab_drill, tab_xmkt = st.tabs(
    [i18n.t("rot.tab.a"), i18n.t("rot.tab.hk"), i18n.t("rot.tab.us"),
     i18n.t("rot.tab.drill"), i18n.t("rot.tab.xmkt")])
with tab_a:
    _render_market("a_share", prefer_cn)
    st.caption(i18n.t("rot.note.a"))
with tab_hk:
    _render_market("hk", prefer_cn)
    st.caption(i18n.t("rot.note.hk"))
with tab_us:
    _render_market("us", prefer_cn)
    st.caption(i18n.t("rot.note.us"))
with tab_drill:
    _render_drill(prefer_cn)
    st.caption(i18n.t("rot.note.drill"))
with tab_xmkt:
    _render_xmkt(prefer_cn)
    st.caption(i18n.t("rot.note.xmkt"))

with st.expander(i18n.t("rot.onboard.title")):
    st.markdown(i18n.t("rot.onboard.body"))
