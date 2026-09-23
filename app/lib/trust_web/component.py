"""One Streamlit Components v2 renderer for the private trust board."""
from __future__ import annotations

from pathlib import Path
import streamlit as st

_ASSETS = Path(__file__).resolve().parents[2] / "static" / "trust_web"
board = st.components.v2.component(
    "cmsi_trust_research_board",
    css=(_ASSETS / "board.css").read_text(),
    js=(_ASSETS / "board.js").read_text(),
    isolate_styles=True,
)
