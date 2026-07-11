"""Market Data — 已并入「行情 / 个股」(pages/6_Ticker_Drill.py 的列表模式)。

保留为 lib.quote_table 的薄壳，单独打开仍能渲染全 universe 行情表；但**已不在侧栏
nav**（st.navigation 只注册合并后的页面）。表逻辑统一在 lib/quote_table.py，避免重复。
"""
from __future__ import annotations

import streamlit as st

from lib import i18n, quote_table, theme, ui
from lib import section_header

st.set_page_config(
    page_title="Market Data · invest-dashboard",
    page_icon="📊",
    layout="wide",
)

i18n.init_lang()
with st.sidebar:
    ui.sidebar_search(key_prefix="market")

i18n.render_lang_toggle()
section_header.cover(i18n.t("market.title"), "CMSI · MARKET DATA",
                     rail=section_header.RAIL_GLOBAL, prefer_cn=i18n.get_lang() == "zh")
quote_table.render_quote_list(prefer_cn=i18n.get_lang() == "zh", key_prefix="market")
