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
    title="Ticker Drill 个股详情",
    url_path="Ticker_Drill",
)
market_data = st.Page(
    "pages/7_Market_Data.py",
    title="Market Data 行情总表",
    url_path="Market_Data",
)

# --- Healthcare children ---
cmsi_coverage = st.Page(
    "pages/1_CMSI_Coverage.py",
    title="CMSI Coverage 覆盖名单",
    url_path="CMSI_Coverage",
)
healthcare_overview = st.Page(
    "pages/2_Healthcare.py",
    title="Overview 总览",
    url_path="Healthcare",
)
sector_heatmap = st.Page(
    "pages/3_Sector_Heatmap.py",
    title="Sector Heatmap 板块热力图",
    url_path="Sector_Heatmap",
)
strategy_picks = st.Page(
    "pages/4_Strategy_Picks.py",
    title="Strategy Picks 策略表现",
    url_path="Strategy_Picks",
)
valuation_scanner = st.Page(
    "pages/5_Valuation_Scanner.py",
    title="Valuation Scanner 估值扫描器",
    url_path="Valuation_Scanner",
)
sec_facts = st.Page(
    "pages/8_SEC_Facts.py",
    title="SEC Company Facts 财报数据",
    url_path="SEC_Facts",
)

# --- AI children ---
ai_coverage = st.Page(
    "pages/a1_ai_coverage.py",
    title="Universe 全景标的",
    url_path="AI_Coverage",
)
ai_overview = st.Page(
    "pages/a2_ai_overview.py",
    title="Overview 总览",
    url_path="AI_Overview",
)
ai_heatmap = st.Page(
    "pages/a3_ai_heatmap.py",
    title="Sector Heatmap 板块热力图",
    url_path="AI_Sector_Heatmap",
)
ai_valuation = st.Page(
    "pages/a4_ai_valuation.py",
    title="Valuation Scanner 估值扫描器",
    url_path="AI_Valuation_Scanner",
)
ai_sec = st.Page(
    "pages/a5_ai_sec.py",
    title="SEC Company Facts 财报数据",
    url_path="AI_SEC_Facts",
)

pg = st.navigation(
    {
        "Global 全局": [home, ticker_drill, market_data, strategy_picks],
        "Healthcare 医疗健康": [
            cmsi_coverage,
            healthcare_overview,
            sector_heatmap,
            valuation_scanner,
            sec_facts,
        ],
        "AI 人工智能": [
            ai_coverage,
            ai_overview,
            ai_heatmap,
            ai_valuation,
            ai_sec,
        ],
    }
)
pg.run()
