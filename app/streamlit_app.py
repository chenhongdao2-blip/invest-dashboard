"""invest-dashboard — Home page.

Streamlit multi-page entry. Full Home content (top movers / benchmarks)
implemented D3.
"""

from __future__ import annotations

import streamlit as st

from lib import db

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Multi-Domain Investment Dashboard")
st.caption("Sell-side healthcare coverage · v1 · data via yfinance")

latest = db.latest_snapshot_date()
if latest:
    st.info(f"📅 Latest data: **{latest}** (UTC)")
else:
    st.warning("⚠️ No snapshot yet. Run `jobs/fetch_eod.py --backfill-days 30` locally.")

# --- Universe summary ---
st.subheader("🌐 Universe Coverage")
uni = db.universe_summary()
if uni.empty:
    st.warning("Empty universe_member. Run `jobs/load_universe.py`.")
else:
    st.dataframe(uni, use_container_width=True, hide_index=True)

# --- Navigation hint ---
st.markdown("""
### 📑 Pages

- **🏥 Healthcare** — 7 sub-sectors overview
- **🔥 Sector Heatmap** — Multiple + return heatmap per sector
- **💎 CMSI Coverage** — Your own coverage list
- **🧬 Strategy Picks** — v4 / v5 biotech / HK 高股息
- **💰 Valuation Scanner** — Outlier candidates
- **🔍 Ticker Drill** — Individual security detail

Use the left sidebar to navigate.
""")

st.divider()
st.caption(
    "⚠️ Valuation multiples are from yfinance (trailing + 12M forward). "
    "Multi-year forward (25E / 26E / 27E) requires Bloomberg / FactSet and is not in scope."
)
