"""AI Valuation Scanner — cheap multiples + positive momentum across the AI supply chain.

Mirror of `5_💰_Valuation_Scanner.py` with domain='ai', reading config/domains/ai.yml.
Empty-data safe: if no multiples are cached yet, the candidate set is empty and the
page shows the standard "no candidates" warning rather than crashing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(
    page_title="AI Valuation Scanner · invest-dashboard",
    page_icon="💰",
    layout="wide",
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "ai.yml"


@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)


cfg = load_domain_cfg()
sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
all_sector_ids = [s[0] for s in sector_options]

# --- Sidebar global search + Filters ---
i18n.init_lang()  # seed lang before sidebar uses t()/sector_name
with st.sidebar:
    ui.sidebar_search(key_prefix="ai_val")
    st.divider()

    st.subheader(i18n.t("scan.presets.header"))
    c1, c2 = st.columns(2)
    if c1.button(i18n.t("scan.presets.deep_value"), width="stretch"):
        st.session_state["ai_scan_pe_pct"] = 15
        st.session_state["ai_scan_mcap"] = 5.0
        st.session_state["ai_scan_ytd"] = (-100, 20)
        st.session_state["ai_scan_5d"] = -30
    if c2.button(i18n.t("scan.presets.recovery"), width="stretch"):
        st.session_state["ai_scan_pe_pct"] = 30
        st.session_state["ai_scan_mcap"] = 2.0
        st.session_state["ai_scan_ytd"] = (-100, 0)
        st.session_state["ai_scan_5d"] = 5
    if st.button(i18n.t("scan.presets.reset"), width="stretch"):
        for k in ["ai_scan_pe_pct", "ai_scan_mcap", "ai_scan_ytd", "ai_scan_5d", "ai_scan_sectors"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    st.divider()
    st.subheader(i18n.t("scan.filters.header"))

    selected_sectors = st.multiselect(
        i18n.t("scan.filters.sector"),
        options=all_sector_ids,
        default=all_sector_ids,
        format_func=lambda x: i18n.sector_name(x),
        key="ai_scan_sectors"
    )

    min_mcap_b = st.slider(
        i18n.t("scan.filters.min_mcap"), 0.0, 50.0, 1.5, 0.5, key="ai_scan_mcap",
    )
    pct_threshold = st.slider(
        i18n.t("scan.filters.pe_pct"),
        0, 100, 25,
        help=i18n.t("scan.filters.pe_pct_help"),
        key="ai_scan_pe_pct"
    )
    pe_metric = st.selectbox(i18n.t("scan.filters.pe_metric"), ["forward_pe", "trailing_pe"], index=0)
    ytd_range = st.slider(i18n.t("scan.filters.ytd_range"), -100, 200, (-50, 100), 5, key="ai_scan_ytd")
    ytd_min, ytd_max = ytd_range
    min_5d = st.slider(i18n.t("scan.filters.min_5d"), -30, 30, -10, 1, key="ai_scan_5d")


# --- Build candidate universe ---
i18n.render_lang_toggle()
theme.page_header(i18n.t("ai.scan.title"))
st.caption(i18n.t("scan.caption", date=(db.latest_snapshot_date() or "—")))

if not selected_sectors:
    st.warning(i18n.t("scan.warn.no_sector"))
    st.stop()

# Collect all tickers across selected sectors
all_tickers_by_sec: dict[str, list[str]] = {}
for sid in selected_sectors:
    tlist = db.sector_tickers("ai", sid)["ticker"].tolist()
    for t in tlist:
        all_tickers_by_sec.setdefault(t, []).append(sid)

all_t = tuple(all_tickers_by_sec.keys())
if not all_t:
    st.warning("No tickers in selected sectors.")
    st.stop()

# Returns + multiples
closes = db.get_close_series_usd(all_t)
rets = db.compute_returns(closes)
mults = db.latest_multiples(all_t)
name_map = db.ticker_to_name(prefer_cn=True)

# Merge
merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(all_t))
for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
          "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    if not mults.empty and c in mults.columns:
        merged[c] = mults[c]
    elif c not in merged.columns:
        merged[c] = pd.NA   # empty-data safe: column always present
# Return columns are NOT guaranteed when `rets` is empty (fresh AI load before EOD
# backfill) — guard them too so the YTD/5D filters below never KeyError (cccg/Codex MAJOR).
for c in ["1d_%", "5d_%", "1m_%", "ytd_%"]:
    if c not in merged.columns:
        merged[c] = pd.NA


# Sector-internal P/E percentile
@st.cache_data(ttl=300)
def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str):
    """For each ticker, rank P/E within its sector (excluding NaN and negative).
    Returns (percentile [0,100] where 0 = cheapest, per-sector eligible-N dict,
    per-sector neg/missing-N dict)."""
    result: dict[str, float] = {}
    sector_n_eligible: dict[str, int] = {}
    sector_n_excluded: dict[str, int] = {}
    if _mults_df.empty or pe_col not in _mults_df.columns:
        return pd.Series(dtype=float, name="pe_percentile"), sector_n_eligible, sector_n_excluded
    sector_tickers: dict[str, list[str]] = {}
    for t, secs in _sector_map.items():
        for s in secs:
            sector_tickers.setdefault(s, []).append(t)

    for sec, t_list in sector_tickers.items():
        in_sec_all = _mults_df.loc[_mults_df.index.intersection(t_list), pe_col]
        in_sec = in_sec_all[in_sec_all > 0].dropna()
        sector_n_eligible[sec] = len(in_sec)
        sector_n_excluded[sec] = len(t_list) - len(in_sec)
        if in_sec.empty:
            continue
        ranks = in_sec.rank(pct=True) * 100
        for t in t_list:
            if t in ranks.index:
                if t not in result or ranks[t] < result[t]:
                    result[t] = float(ranks[t])
    return pd.Series(result, name="pe_percentile"), sector_n_eligible, sector_n_excluded


pe_pct, sec_n_elig, sec_n_excl = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
merged["pe_percentile"] = pe_pct

# surface small-N + negative-excluded caveats
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
            "(negative or null trailing/forward EPS)"
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
if "pe_percentile" in candidates.columns and not candidates.empty:
    candidates = candidates.sort_values("pe_percentile", ascending=True)

# --- Result summary ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(i18n.t("scan.metric.universe"), f"{len(all_t)}")
col2.metric(i18n.t("scan.metric.candidates"), f"{len(candidates)}")
col3.metric(i18n.t("scan.metric.median_mcap"),
            f"${candidates['market_cap_usd'].median()/1e9:.1f}B" if not candidates.empty else "—")
col4.metric(i18n.t("scan.metric.median_ytd"),
            fmt.fmt_pct(candidates['ytd_%'].median()) if not candidates.empty else "—")

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

ui.render_styled_table(
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
