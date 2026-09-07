"""Valuation Scanner — find outlier candidates with cheap multiples + positive momentum.

D5 implementation:
- Filters: sector multi-select, min mcap, P/E percentile, YTD return range
- Output: candidate list with sector-relative P/E rank + Z-score (if enough data)
- Multi-criteria: combine cheap-on-multiple + recovering-momentum signal
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n
from lib import section_header
from lib import valuation

st.set_page_config(
    page_title="Valuation Scanner · invest-dashboard",
    page_icon="💰",
    layout="wide",
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"

cfg = db.load_domain_cfg(str(DOMAIN_CFG))
sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
all_sector_ids = [s[0] for s in sector_options]

# --- Sidebar global search + Filters ---
i18n.init_lang()  # seed lang before sidebar uses t()/sector_name (Codex MINOR)
with st.sidebar:
    ui.sidebar_search(key_prefix="scanner")
    st.divider()
    
    st.subheader(i18n.t("scan.presets.header"))
    c1, c2 = st.columns(2)
    if c1.button(i18n.t("scan.presets.deep_value"), width="stretch"):
        st.session_state["scan_pe_pct"] = 15
        st.session_state["scan_mcap"] = 5.0
        st.session_state["scan_ytd"] = (-100, 20)
        st.session_state["scan_5d"] = -30
    if c2.button(i18n.t("scan.presets.recovery"), width="stretch"):
        st.session_state["scan_pe_pct"] = 30
        st.session_state["scan_mcap"] = 2.0
        st.session_state["scan_ytd"] = (-100, 0)
        st.session_state["scan_5d"] = 5
    if st.button(i18n.t("scan.presets.reset"), width="stretch"):
        for k in ["scan_pe_pct", "scan_mcap", "scan_ytd", "scan_5d", "scan_sectors"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    st.divider()
    st.subheader(i18n.t("scan.filters.header"))

    selected_sectors = st.multiselect(
        i18n.t("scan.filters.sector"),
        options=all_sector_ids,
        default=all_sector_ids,
        format_func=lambda x: i18n.sector_name(x),
        key="scan_sectors"
    )

    min_mcap_b = st.slider(
        i18n.t("scan.filters.min_mcap"), 0.0, 50.0, 1.5, 0.5, key="scan_mcap",
        help="M11 audit: default $1.5B 适合 HK biotech 中小盘 + US 中盘。原 $5B 默认过滤掉 90% HK 18A。"
    )
    pct_threshold = st.slider(
        i18n.t("scan.filters.pe_pct"),
        0, 100, 25,
        help=i18n.t("scan.filters.pe_pct_help"),
        key="scan_pe_pct"
    )
    pe_metric = st.selectbox(i18n.t("scan.filters.pe_metric"), ["forward_pe", "trailing_pe"], index=0)
    ytd_range = st.slider(i18n.t("scan.filters.ytd_range"), -100, 200, (-50, 100), 5, key="scan_ytd")
    ytd_min, ytd_max = ytd_range
    min_5d = st.slider(i18n.t("scan.filters.min_5d"), -30, 30, -10, 1, key="scan_5d")


# --- Build candidate universe ---
i18n.init_lang()
i18n.render_lang_toggle()
section_header.cover(i18n.t("scan.title"), "CMSI · VALUATION SCANNER",
                     rail=section_header.RAIL_HC, prefer_cn=i18n.get_lang() == "zh")
st.caption(i18n.t("scan.caption", date=(db.latest_snapshot_date() or "—")))

if not selected_sectors:
    st.warning(i18n.t("scan.warn.no_sector"))
    st.stop()

# Collect all tickers across selected sectors
all_tickers_by_sec: dict[str, list[str]] = {}
_MF = db.market_frame("healthcare")
for sid in selected_sectors:
    tlist = _MF.members.get(sid, ())
    for t in tlist:
        all_tickers_by_sec.setdefault(t, []).append(sid)

all_t = tuple(all_tickers_by_sec.keys())
if not all_t:
    st.warning("No tickers in selected sectors.")
    st.stop()

# Returns + multiples
rets = db.returns_for(all_t, _MF.as_of, "usd", "healthcare")
mults = _MF.multiples.loc[_MF.multiples.index.intersection(all_t)]
name_map = db.ticker_to_name(prefer_cn=True)

# Merge
merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(all_t))
if not mults.empty:
    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
        if c in mults.columns:
            merged[c] = mults[c]

# Sector-internal P/E percentile — single definition in lib.valuation (audit C3:
# the page-local copies took `_`-prefixed args, which Streamlit EXCLUDES from the
# cache key, so switching sectors served the previous sector's percentiles).
pe_pct, sec_n_elig, sec_n_excl = valuation.sector_pe_percentile(
    mults, all_tickers_by_sec, pe_metric)
merged["pe_percentile"] = pe_pct

# m2/m3 audit: surface small-N + negative-excluded caveats
small_n_secs = {s: n for s, n in sec_n_elig.items() if n < 6 and n > 0}
total_neg_excl = sum(sec_n_excl.values())
if small_n_secs or total_neg_excl > 0:
    caveats = []
    if small_n_secs:
        caveats.append(
            "**Small-N sectors** (percentile coarse): "
            + ", ".join(f"{s} (N={n})" for s, n in small_n_secs.items())
        )
    if total_neg_excl > 0:
        caveats.append(
            f"**{total_neg_excl} tickers excluded from P/E percentile** "
            "(negative or null trailing/forward EPS — biotech 烧钱期标的 / one-time charge)"
        )
    st.caption(" · ".join(caveats))

# Apply filters
candidates = merged.copy()
candidates = candidates[candidates["market_cap_usd"] >= min_mcap_b * 1e9]
candidates = candidates[candidates["pe_percentile"] <= pct_threshold]
candidates = candidates[candidates["pe_percentile"].notna()]
candidates = candidates[(candidates["ytd_%"] >= ytd_min) & (candidates["ytd_%"] <= ytd_max)]
candidates = candidates[candidates["5d_%"] >= min_5d]

# Sort by P/E percentile ascending (cheapest first)
candidates = candidates.sort_values("pe_percentile", ascending=True)

# --- Result summary ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(i18n.t("scan.metric.universe"), f"{len(all_t)}")
col2.metric(i18n.t("scan.metric.candidates"), f"{len(candidates)}")
col3.metric(i18n.t("scan.metric.median_mcap"),
            f"${candidates['market_cap_usd'].median()/1e9:.1f}B" if not candidates.empty else "—")
col4.metric(i18n.t("scan.metric.median_ytd"), fmt.fmt_pct(candidates['ytd_%'].median()) if not candidates.empty else "—")

if candidates.empty:
    st.warning(i18n.t("scan.warn.no_candidates"))
    st.stop()

# Build NUMERIC display DataFrame (sort-bug fix).
pe_label = pe_metric.replace("_", " ").title()
disp = pd.DataFrame(index=candidates.index)
disp["BBG"] = [fmt.fmt_ticker_bbg(t) for t in disp.index]
disp["Name"] = [name_map.get(t, t) for t in disp.index]
disp["Mcap USD ($B)"] = candidates["market_cap_usd"] / 1e9
disp[pe_label] = candidates[pe_metric]
disp["Sector P/E %ile"] = candidates["pe_percentile"]
disp["YTD %"] = candidates["ytd_%"]
disp["1M %"] = candidates["1m_%"]
disp["5D %"] = candidates["5d_%"]
disp["EV/EBITDA"] = candidates["ev_ebitda"]
disp["FCF Yld"] = candidates["fcf_yield"]
disp.index.name = "Ticker"

ui.render_html_table(
    disp,
    pct_cols=["YTD %", "1M %", "5D %"],
    pct_decimal_cols=["FCF Yld"],
    mult_cols=[pe_label, "EV/EBITDA", "Sector P/E %ile"],
    money_b_cols=["Mcap USD ($B)"],
    text_cols=["BBG", "Name"],
    extra_formats={"Sector P/E %ile": "%.0f%%"},
    height=560,
    column_labels={**i18n.common_cols(), "Sector P/E %ile": i18n.t("scan.col.pe_pctile")},
    index_label=i18n.t("common.col.ticker"),
)

# --- Interpretation hints ---
with st.expander(i18n.t("scan.onboarding.title")):
    st.markdown(i18n.t("scan.onboarding.body"))

st.divider()
st.caption(i18n.t("scan.caption.method", date=(db.latest_snapshot_date() or "—")))
