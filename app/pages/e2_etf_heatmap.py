"""ETF 专栏 · 热力图 — the same ranked-bento heatmap the stock pages use, scoped to
domain='etf'. One industry → one basket: all healthcare ETFs render as a SINGLE 医药
block (single_block=True), each ETF a tile colored teal-up / red-down (locked
convention), rather than six thin sub-sector blocks.

Pure reuse of lib.heatmap.build_domain_bento + render_bento_html (same as home.py),
with the 1D/5D/1M window segmented-control.
"""
from __future__ import annotations

import streamlit as st

from lib import db
from lib import heatmap as hm
from lib import i18n
from lib import theme
from lib import ui

st.set_page_config(page_title="ETF Heatmap · invest-dashboard", page_icon="🔥", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()
with st.sidebar:
    ui.sidebar_search(key_prefix="etf_heat")

prefer_cn = i18n.get_lang() == "zh"

theme.page_header(i18n.t("etf.heat.title"))
latest = db.latest_snapshot_date() or "—"
st.caption(i18n.t("etf.heat.caption", date=latest))

win = st.segmented_control(
    i18n.t("etf.heat.window"),
    options=["1D", "5D", "1M"],
    default="1M",
    key="etf_heatmap_window",
    label_visibility="collapsed",
)
window_col = hm.WIN_TO_COL.get(win or "1M", "1m_%")

# One industry → one basket: all healthcare ETFs collapse into a single block
# (George: 一个行业一个栏目 · 医药一篮就好), rather than 6 sub-sector blocks.
bento = hm.build_domain_bento(
    "etf", window_col, prefer_cn,
    single_block=True,
    single_cn="医药", single_en="Healthcare",
)
if bento is None or not bento.get("sectors"):
    st.warning(i18n.t("etf.empty"))
    st.stop()

doc, h = hm.render_bento_html([bento], prefer_cn=prefer_cn, window_label=(win or "1M"), as_of=latest)
st.iframe(doc, height=h)
