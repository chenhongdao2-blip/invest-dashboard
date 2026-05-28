"""Shared Streamlit UI components."""

from __future__ import annotations

import streamlit as st
from lib import db
from lib import format as fmt

def sidebar_search(key_prefix: str = ""):
    """Unified sidebar ticker search with session state persistence."""
    st.subheader("🔍 Find ticker")
    
    # Initialize session state if not present
    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = ""

    all_t = sorted(db.all_tickers())
    
    # We use a temporary key for the selectbox and then sync with session_state
    # to avoid the "Duplicate Key" or "Value not in options" issues during page switches.
    current_index = 0
    if st.session_state.global_ticker in all_t:
        current_index = all_t.index(st.session_state.global_ticker) + 1

    pick = st.selectbox(
        "Jump to ticker drill",
        options=[""] + all_t,
        index=current_index,
        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
        key=f"{key_prefix}_search_box",
    )
    
    if pick != st.session_state.global_ticker:
        st.session_state.global_ticker = pick
        # st.rerun() # Optional: force immediate update if needed

    if st.session_state.global_ticker:
        st.info(f"📍 **{fmt.fmt_ticker_bbg(st.session_state.global_ticker)}** — Ticker Drill (D6) coming soon.")

def onboarding_expander(page_name: str, markdown_text: str):
    """Consistent onboarding expander across pages."""
    with st.expander(f"📖 How to read this {page_name}"):
        st.markdown(markdown_text)
