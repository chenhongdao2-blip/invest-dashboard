"""AI / 存储: history, technical paths, cash, policy and research evidence."""
import streamlit as st

from lib import i18n, storage_research_panel, ui

with st.sidebar:
    ui.sidebar_search(key_prefix="ai_storage")
i18n.init_lang()
i18n.render_lang_toggle()
storage_research_panel.render()
