"""invest-dashboard — st.navigation hub.

Switched from auto-discovery of app/pages/* to explicit st.Page registration
so we can group children under a Healthcare section. Ticker Drill stays at
top level (not nested) — it's domain-agnostic.

Layout:
    Home
    Ticker Drill
    ── Healthcare ──
        CMSI Coverage
        Overview
        Sector Heatmap
        Strategy Picks
        Valuation Scanner

The `url_path` arguments preserve the slugs created by the prior
auto-discovery layout so existing deep-links (e.g. /Ticker_Drill?ticker=LLY)
continue to work after the redeploy.
"""

from __future__ import annotations

import streamlit as st

# --- Top-level pages ---
home = st.Page(
    "home.py",
    title="Home",
    url_path="",
    default=True,
)
ticker_drill = st.Page(
    "pages/6_🔍_Ticker_Drill.py",
    title="Ticker Drill",
    url_path="Ticker_Drill",
)

# --- Healthcare children ---
cmsi_coverage = st.Page(
    "pages/1_💎_CMSI_Coverage.py",
    title="CMSI Coverage",
    url_path="CMSI_Coverage",
)
healthcare_overview = st.Page(
    "pages/2_🏥_Healthcare.py",
    title="Overview",
    url_path="Healthcare",
)
sector_heatmap = st.Page(
    "pages/3_🔥_Sector_Heatmap.py",
    title="Sector Heatmap",
    url_path="Sector_Heatmap",
)
strategy_picks = st.Page(
    "pages/4_🧬_Strategy_Picks.py",
    title="Strategy Picks",
    url_path="Strategy_Picks",
)
valuation_scanner = st.Page(
    "pages/5_💰_Valuation_Scanner.py",
    title="Valuation Scanner",
    url_path="Valuation_Scanner",
)

pg = st.navigation(
    {
        "": [home, ticker_drill],
        "Healthcare": [
            cmsi_coverage,
            healthcare_overview,
            sector_heatmap,
            strategy_picks,
            valuation_scanner,
        ],
    }
)
pg.run()
