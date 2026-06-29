"""invest-dashboard — st.navigation hub.

Switched from auto-discovery of app/pages/* to explicit st.Page registration
so we can group children under a Healthcare section. Ticker Drill stays at
top level (not nested) — it's domain-agnostic.

Layout:
    Home
    Ticker Drill
    Strategy Picks          # top-level: spans biotech + HK high-dividend, not HC-only
    ── Healthcare ──
        CMSI Coverage
        Overview
        Sector Heatmap
        Valuation Scanner
    ── AI 人工智能 ──
        Coverage
        Overview
        Sector Heatmap
        Valuation Scanner
        SEC Facts

The `url_path` arguments preserve the slugs created by the prior
auto-discovery layout so existing deep-links (e.g. /Ticker_Drill?ticker=LLY)
continue to work after the redeploy.
"""

from __future__ import annotations

import streamlit as st

from lib import i18n

# Seed language once at the app entry so every page (deep-linked or via nav)
# shares one st.session_state["lang"] — avoids half-translated pages (cccg gate #3).
i18n.init_lang()

# --- Top-level pages ---
# Nav labels are bilingual (EN 中文) by user request — shown verbatim regardless
# of the in-page language toggle. url_path kept stable so deep-links still work.
home = st.Page(
    "home.py",
    title="Market Hub 行情中枢",
    url_path="",
    default=True,
)
ticker_drill = st.Page(
    "pages/6_Ticker_Drill.py",
    title="Market & Stocks 行情 / 个股",   # 合并: 列表(全市场行情表)+详情(个股下钻) 同页
    url_path="Ticker_Drill",               # url 不变 → ?ticker= 深链照常进详情模式
)
# (Market Data 已并入 Ticker Drill 的列表模式; 表逻辑搬到 lib/quote_table.py)
model_drill = st.Page(
    "pages/model_drill.py",
    title="Model Drill 分析师模型",
    url_path="Model_Drill",
)
sector_rotation = st.Page(
    "pages/3b_Sector_Rotation.py",
    title="Sector Rotation 板块轮动",
    url_path="Sector_Rotation_RRG",
)

# --- Healthcare children ---
cmsi_coverage = st.Page(
    "pages/1_CMSI_Coverage.py",
    title="CMSI Coverage 覆盖名单",
    url_path="CMSI_Coverage",
)
healthcare_overview = st.Page(
    "pages/2_Healthcare.py",
    title="HC Overview 总览",
    url_path="Healthcare",
)
sector_heatmap = st.Page(
    "pages/3_Sector_Heatmap.py",
    title="HC Heatmap 板块热力图",
    url_path="Sector_Heatmap",
)
strategy_picks = st.Page(
    "pages/4_Strategy_Picks.py",
    title="Strategy Picks 策略表现",
    url_path="Strategy_Picks",
)
valuation_scanner = st.Page(
    "pages/5_Valuation_Scanner.py",
    title="HC Valuation 估值扫描器",
    url_path="Valuation_Scanner",
)
sec_facts = st.Page(
    "pages/8_SEC_Facts.py",
    title="HC SEC Facts 财报数据",
    url_path="SEC_Facts",
)
hc_capital = st.Page(
    "pages/9_HC_Capital_Markets.py",
    title="HC Capital Markets 投融资",
    url_path="HC_Capital_Markets",
)
# --- ETF 专栏 (own top-level section; ETFs are first-class instruments like stocks) ---
etf_overview = st.Page(
    "pages/e1_etf_overview.py",
    title="ETF Overview 总览/表现",
    url_path="ETF_Overview",
)
etf_heatmap = st.Page(
    "pages/e2_etf_heatmap.py",
    title="ETF Heatmap 热力图",
    url_path="ETF_Heatmap",
)
etf_rotation = st.Page(
    "pages/e3_etf_rotation.py",
    title="ETF Rotation 动能轮动",
    url_path="ETF_Rotation",
)

# --- AI children ---
ai_coverage = st.Page(
    "pages/a1_ai_coverage.py",
    title="Universe 全景标的",
    url_path="AI_Coverage",
)
ai_overview = st.Page(
    "pages/a2_ai_overview.py",
    title="AI Overview 算力总览",
    url_path="AI_Overview",
)
ai_heatmap = st.Page(
    "pages/a3_ai_heatmap.py",
    title="AI Heatmap 算力热力图",
    url_path="AI_Sector_Heatmap",
)
ai_valuation = st.Page(
    "pages/a4_ai_valuation.py",
    title="AI Valuation 算力估值",
    url_path="AI_Valuation_Scanner",
)
ai_sec = st.Page(
    "pages/a5_ai_sec.py",
    title="AI SEC Facts 算力财报",
    url_path="AI_SEC_Facts",
)

pg = st.navigation(
    {
        # 核心：AI Agent 选股·策略表现 = 平台主张，单独置顶成 section (与其余分隔)。
        "⭐ 核心策略": [strategy_picks],
        "Global 全局": [home, ticker_drill, model_drill, sector_rotation],
        "Healthcare 医疗健康": [
            cmsi_coverage,
            healthcare_overview,
            sector_heatmap,
            valuation_scanner,
            sec_facts,
            hc_capital,
        ],
        "AI 人工智能": [
            ai_coverage,
            ai_overview,
            ai_heatmap,
            ai_valuation,
            ai_sec,
        ],
        "ETF 专栏": [
            etf_overview,
            etf_heatmap,
            etf_rotation,
        ],
    },
    # Force all sections fully expanded. Default behavior collapses overflow
    # into a "View N more" button once total nav items exceed the height the
    # sidebar leaves for the nav (we have 14 pages + sidebar search/probe), which
    # was hiding the last 4 AI pages behind "View 4 more". expanded=True pins them open.
    expanded=True,
)
pg.run()
