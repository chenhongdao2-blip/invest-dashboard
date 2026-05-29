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
    title="Home 首页",
    url_path="",
    default=True,
)
ticker_drill = st.Page(
    "pages/6_🔍_Ticker_Drill.py",
    title="Ticker Drill 个股详情",
    url_path="Ticker_Drill",
)

# --- Healthcare children ---
cmsi_coverage = st.Page(
    "pages/1_💎_CMSI_Coverage.py",
    title="CMSI Coverage 覆盖名单",
    url_path="CMSI_Coverage",
)
healthcare_overview = st.Page(
    "pages/2_🏥_Healthcare.py",
    title="Overview 总览",
    url_path="Healthcare",
)
sector_heatmap = st.Page(
    "pages/3_🔥_Sector_Heatmap.py",
    title="Sector Heatmap 板块热力图",
    url_path="Sector_Heatmap",
)
strategy_picks = st.Page(
    "pages/4_🧬_Strategy_Picks.py",
    title="Strategy Picks 策略表现",
    url_path="Strategy_Picks",
)
valuation_scanner = st.Page(
    "pages/5_💰_Valuation_Scanner.py",
    title="Valuation Scanner 估值扫描器",
    url_path="Valuation_Scanner",
)

pg = st.navigation(
    {
        "": [home, ticker_drill, strategy_picks],
        "Healthcare 医疗健康": [
            cmsi_coverage,
            healthcare_overview,
            sector_heatmap,
            valuation_scanner,
        ],
    }
)
pg.run()
