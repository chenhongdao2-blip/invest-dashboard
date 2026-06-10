"""Universe 行情列表表 (按领域/地区/行业筛选) + CSV 下载 —— 可复用渲染单元。

从原独立的 Market Data 页抽出，供合并后的「行情 / 个股」页在**列表模式**渲染
(个股详情 = 详情模式)。Industry-agnostic：拉全 universe，filter 让它随新 domain
扩展仍好用。新增「行业/子行业」筛选 (sector multiselect) —— 原 Market Data 只有
领域/地区两档。
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, i18n, theme, ui
from lib import format as fmt


@st.cache_data(ttl=300)
def _ticker_roster() -> pd.DataFrame:
    """一行一票 (sectors 用 GROUP_CONCAT 拼成 csv)。"""
    return db.query(
        """SELECT ticker,
                  MAX(name_cn) AS name_cn, MAX(name_en) AS name_en,
                  MAX(domain)  AS domain,
                  GROUP_CONCAT(DISTINCT sector) AS sectors,
                  MAX(region)  AS region
           FROM universe_member
           GROUP BY ticker
           ORDER BY ticker"""
    )


@st.cache_data(ttl=300)
def _security_master_csv() -> bytes:
    """原始 universe_member (每条 membership 行) → CSV bytes。"""
    df = db.query(
        "SELECT domain, sector, ticker, name_cn, name_en, region, note "
        "FROM universe_member ORDER BY domain, sector, ticker"
    )
    return df.to_csv(index=False).encode("utf-8-sig")


def _fmt_sectors(sec_csv: str) -> str:
    # _coverage 标记排前 (易筛/排序)，真实 sector 在后 → "覆盖 / 生物科技"
    parts = [s for s in (sec_csv or "").split(",") if s]
    parts.sort(key=lambda s: (s != "_coverage", s))
    return " / ".join(i18n.sector_name(s) for s in parts)


def render_quote_list(prefer_cn: bool, *, key_prefix: str = "qt") -> None:
    """全 universe 行情表 (FT 精排) + 领域/地区/行业筛选 + 下载。列表模式调用。

    行内「详情 ↗」深链点击 → **新标签**打开个股详情 (/Ticker_Drill?ticker=X)。
    WHY 新标签而非同标签：同标签点行需原生 st.dataframe，但其 glide-grid canvas 被
    OS 暗色模式穿透变黑底 (CSS 够不到) —— 这正是全站用 FT iframe 表的原因。iframe
    沙箱又禁 target=_top，故唯一可行的点击跳转是 target=_blank 新标签。
    key_prefix 让同函数多处实例化时 widget key 不撞。
    """
    roster = _ticker_roster()

    # ── 筛选: 领域 / 地区 / 行业(子行业) ──
    domains = sorted(d for d in roster["domain"].dropna().unique())
    regions = sorted(r for r in roster["region"].dropna().unique())
    sectors = sorted({
        s for csv in roster["sectors"].dropna()
        for s in csv.split(",") if s and s != "_coverage"
    })
    c1, c2, c3 = st.columns(3)
    sel_domains = c1.multiselect(
        i18n.t("market.filters.domain"), options=domains, default=domains,
        format_func=i18n.domain_name, key=f"{key_prefix}_dom")
    sel_regions = c2.multiselect(
        i18n.t("market.filters.region"), options=regions, default=regions,
        key=f"{key_prefix}_reg")
    sel_sectors = c3.multiselect(
        i18n.t("market.filters.sector"), options=sectors, default=[],
        format_func=i18n.sector_name, key=f"{key_prefix}_sec",
        help=i18n.t("market.filters.sector_help"))

    filt = roster.copy()
    if sel_domains:
        filt = filt[filt["domain"].isin(sel_domains)]
    if sel_regions:
        filt = filt[filt["region"].isin(sel_regions)]
    if sel_sectors:
        want = set(sel_sectors)
        filt = filt[filt["sectors"].fillna("").apply(
            lambda csv: bool(want & {s for s in csv.split(",") if s}))]

    if filt.empty:
        st.warning(i18n.t("market.empty"))
        return

    all_t = tuple(filt["ticker"].tolist())
    closes = db.get_close_series_usd(all_t)
    rets = db.compute_returns(closes)
    mults = db.latest_multiples(all_t)
    name_map = db.ticker_to_name(prefer_cn=prefer_cn)

    disp = pd.DataFrame(index=filt["ticker"])
    disp.index.name = "Ticker"
    disp["Name"] = [name_map.get(t, t) for t in disp.index]
    disp["Sector"] = [
        _fmt_sectors(sec)
        for sec in filt.set_index("ticker")["sectors"].reindex(disp.index).fillna("")
    ]
    disp["Region"] = filt.set_index("ticker")["region"].reindex(disp.index).values

    def _c(src: pd.DataFrame, col: str):
        return src[col].reindex(disp.index) if (not src.empty and col in src.columns) else pd.NA

    disp["Last"] = _c(rets, "last")
    disp["1D %"] = _c(rets, "1d_%")
    disp["5D %"] = _c(rets, "5d_%")
    disp["YTD %"] = _c(rets, "ytd_%")
    disp["Trail P/E"] = _c(mults, "trailing_pe")
    disp["Fwd P/E"] = _c(mults, "forward_pe")
    disp["Mcap USD ($B)"] = _c(mults, "market_cap_usd") / 1e9
    disp = disp.sort_values("Mcap USD ($B)", ascending=False, na_position="last")
    raw_order = list(disp.index)                     # 原始 ticker(按市值序) — 行选择映射
    disp.index = [fmt.fmt_ticker_bbg(t) for t in disp.index]
    disp.index.name = "Ticker"

    # ── 指标 + 下载 ──
    m1, m2, _ = st.columns([1, 1, 4])
    m1.metric(i18n.t("market.metric.universe"), f"{len(roster)}")
    m2.metric(i18n.t("market.metric.shown"), f"{len(disp)}")

    d1, d2, _ = st.columns([1.4, 1.6, 3])
    d1.download_button(
        i18n.t("market.dl.quotes"),
        data=disp.reset_index().to_csv(index=False).encode("utf-8-sig"),
        file_name=f"market_data_{db.latest_snapshot_date() or 'latest'}.csv",
        mime="text/csv", width="stretch", key=f"{key_prefix}_dlq")
    d2.download_button(
        i18n.t("market.dl.master"), data=_security_master_csv(),
        file_name="security_master.csv", mime="text/csv",
        help=i18n.t("market.dl.master_help"), width="stretch", key=f"{key_prefix}_dlm")

    # ── 表 (FT 精排 iframe 表; 行内「详情 ↗」点击 → 新标签开个股详情) ──
    nav_col = "_open"
    disp[nav_col] = [f"/Ticker_Drill?ticker={t}" for t in raw_order]   # 下载之后才加 → CSV 不含 URL
    theme.section_header(i18n.t("market.section.table"))
    st.caption(i18n.t("market.click_hint"))
    ui.render_html_table(
        disp,
        pct_cols=["1D %", "5D %", "YTD %"],
        mult_cols=["Trail P/E", "Fwd P/E"],
        money_b_cols=["Mcap USD ($B)"],
        price_cols=["Last"],
        text_cols=["Name", "Sector", "Region"],
        nav_cols=[nav_col],
        nav_label="详情 ↗" if prefer_cn else "Open ↗",
        height=560,
        column_labels={
            **i18n.common_cols(),
            "Sector": i18n.t("market.col.sector"),
            "Region": i18n.t("market.col.region"),
            nav_col: "详情" if prefer_cn else "Detail",
        },
        index_label=i18n.t("common.col.ticker"),
    )

    with st.expander(i18n.t("market.onboarding.title")):
        st.markdown(i18n.t("market.onboarding.body"))
