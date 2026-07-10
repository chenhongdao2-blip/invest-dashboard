"""AI Sector Heatmap — cross-section multiples + returns, design-source card.

2026-07-10 reskin: the st.tabs + Styler table is replaced by lib/heat_table.py,
mirroring the healthcare page (3_Sector_Heatmap.py) for the AI domain.
Data layer unchanged: db.get_close_series_usd (M1 USD returns) +
db.latest_multiples (yfinance static + fwd multiples snapshot).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from lib import db
from lib import heat_table
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(page_title="AI Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "ai.yml"

cfg = db.load_domain_cfg(str(DOMAIN_CFG))

i18n.init_lang()
i18n.render_lang_toggle()

theme.page_header(i18n.t("ai.heat.title"), meta="AI SECTOR HEATMAP")
st.caption(i18n.t("heat.caption"))
theme.page_radial_wash(1300)
prefer_cn = i18n.get_lang() == "zh"

# --- Sidebar global search + min-mcap filter (server-side; sort is in-table) ---
with st.sidebar:
    ui.sidebar_search(key_prefix="ai_heat")
    st.divider()
    st.subheader(i18n.t("heat.filter.header"))
    min_mcap_b = st.slider(
        i18n.t("heat.filter.min_mcap"), 0.0, 50.0, 0.0, 0.5,
        help=i18n.t("heat.filter.min_mcap_help")
    )


def _sector_rows(sec_id: str, name_map: dict) -> list[dict]:
    """One sector's cross-section rows for heat_table (mcap $B, returns %, multiples,
    fcf_yield fraction → %). Missing values stay None → NM in-table."""
    uni = db.sector_tickers("ai", sec_id)
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        return []
    rets = db.compute_returns(db.get_close_series_usd(tickers))
    mults = db.latest_multiples(tickers)
    rows = []
    for tk in tickers:
        r = rets.loc[tk] if (not rets.empty and tk in rets.index) else pd.Series(dtype=float)
        m = mults.loc[tk] if (not mults.empty and tk in mults.index) else pd.Series(dtype=float)
        mcap = m.get("market_cap_usd")
        mcap_b = (float(mcap) / 1e9) if pd.notna(mcap) else None
        if min_mcap_b > 0 and (mcap_b is None or mcap_b < min_mcap_b):
            continue
        fcf = m.get("fcf_yield")
        rows.append({
            "t": tk, "n": name_map.get(tk, tk), "mcap": mcap_b,
            "ytd": r.get("ytd_%"), "m1": r.get("1m_%"),
            "d5": r.get("5d_%"), "d1": r.get("1d_%"),
            "peS": m.get("trailing_pe"), "peF": m.get("forward_pe"),
            "evE": m.get("ev_ebitda"), "evS": m.get("ev_sales"),
            "fcf": (float(fcf) * 100.0) if pd.notna(fcf) else None,
        })
    return rows


_name_map = db.ticker_to_name(prefer_cn=prefer_cn)
_sectors = []
for sec in cfg["sectors"]:
    _rows = _sector_rows(sec["id"], _name_map)
    if _rows:
        _sectors.append({"id": sec["id"], "name": i18n.sector_name(sec["id"]),
                         "bench": sec.get("benchmark", "—"), "rows": _rows})

if not _sectors:
    st.warning(i18n.t("heat.empty"))
else:
    _labels = {
        "cover": i18n.t("heat.tbl.cover"), "mcap_total": i18n.t("heat.tbl.mcap_total"),
        "ytd_med": i18n.t("heat.tbl.ytd_med"), "breadth": i18n.t("heat.tbl.breadth"),
        "up": i18n.t("heat.tbl.up"), "dn": i18n.t("heat.tbl.dn"),
        "unit_names": i18n.t("heat.tbl.unit_names"), "median": i18n.t("heat.tbl.median"),
        "grp_ret": i18n.t("heat.tbl.grp_ret"), "grp_val": i18n.t("heat.tbl.grp_val"),
        "grp_cf": i18n.t("heat.tbl.grp_cf"),
        "footnote": i18n.t("heat.tbl.footnote", date=(db.latest_snapshot_date() or "—")),
        "footnote_dyn": i18n.t("heat.tbl.footnote_dyn"),
        "brand": "CMSI · AI SECTOR HEATMAP",
        # 板块汇总（zip4 设计）：section 头 + 8 列表头
        "sum_title": i18n.t("heat.tbl.sum.title"),
        "sum_sub": i18n.t("heat.tbl.sum.sub", n=sum(len(s["rows"]) for s in _sectors)),
        "sum_right": "EQUAL-WEIGHT AVG",
        "heat_title": i18n.t("heat.tbl.heat.title"),
        "heat_sub": i18n.t("heat.tbl.heat.sub"),
        "sum_cols": {
            "sector": i18n.t("heat.tbl.sum.col.sector"), "n": i18n.t("heat.tbl.sum.col.n"),
            "d1": i18n.t("heat.tbl.col.d1"), "d5": i18n.t("heat.tbl.col.d5"),
            "m1": i18n.t("heat.tbl.col.m1"), "ytd": i18n.t("heat.tbl.col.ytd"),
            "dist": i18n.t("heat.tbl.sum.col.dist"), "bench": i18n.t("heat.tbl.sum.col.bench"),
        },
        "cols": {
            "t": i18n.t("heat.tbl.col.t"), "n": i18n.t("heat.tbl.col.n"),
            "mcap": i18n.t("heat.tbl.col.mcap"), "ytd": i18n.t("heat.tbl.col.ytd"),
            "m1": i18n.t("heat.tbl.col.m1"), "d5": i18n.t("heat.tbl.col.d5"),
            "d1": i18n.t("heat.tbl.col.d1"), "peS": i18n.t("heat.tbl.col.peS"),
            "peF": i18n.t("heat.tbl.col.peF"), "evE": "EV/EBITDA", "evS": "EV/S",
            "fcf": i18n.t("heat.tbl.col.fcf"),
        },
    }
    _doc, _h = heat_table.render_heat_table(_sectors, labels=_labels, height=920)
    st.iframe(_doc, height=_h)
    st.caption(i18n.t("heat.tbl.filter_note"))

# --- Onboarding ---
with st.expander(i18n.t("heat.onboarding.title"), expanded=True):
    st.markdown(i18n.t("heat.tbl.onboarding.body"))
