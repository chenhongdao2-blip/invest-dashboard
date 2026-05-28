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
import yaml

from lib import db
from lib import format as fmt
from lib import ui

st.set_page_config(
    page_title="Valuation Scanner · invest-dashboard",
    page_icon="💰",
    layout="wide",
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"

@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)

cfg = load_domain_cfg()
sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
all_sector_ids = [s[0] for s in sector_options]

# --- Sidebar global search + Filters ---
with st.sidebar:
    ui.sidebar_search(key_prefix="scanner")
    st.divider()
    
    st.subheader("🎯 Presets")
    c1, c2 = st.columns(2)
    if c1.button("💎 Deep Value", use_container_width=True):
        st.session_state["scan_pe_pct"] = 15
        st.session_state["scan_mcap"] = 5.0
        st.session_state["scan_ytd"] = (-100, 20)
        st.session_state["scan_5d"] = -30
    if c2.button("🚀 Recovery", use_container_width=True):
        st.session_state["scan_pe_pct"] = 30
        st.session_state["scan_mcap"] = 2.0
        st.session_state["scan_ytd"] = (-100, 0)
        st.session_state["scan_5d"] = 5
    if st.button("🔄 Reset all filters", use_container_width=True):
        for k in ["scan_pe_pct", "scan_mcap", "scan_ytd", "scan_5d", "scan_sectors"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    st.divider()
    st.subheader("📊 Filters")

    selected_sectors = st.multiselect(
        "Sector",
        options=all_sector_ids,
        default=all_sector_ids,
        format_func=lambda x: next(s[1] for s in sector_options if s[0] == x),
        key="scan_sectors"
    )

    min_mcap_b = st.slider(
        "Min market cap (USD B)", 0.0, 50.0, 1.5, 0.5, key="scan_mcap",
        help="M11 audit: default $1.5B 适合 HK biotech 中小盘 + US 中盘。原 $5B 默认过滤掉 90% HK 18A。"
    )
    pct_threshold = st.slider(
        "P/E percentile threshold",
        0, 100, 25,
        help="只显示 fwd P/E 在板块内分位 ≤ 此阈值的候选",
        key="scan_pe_pct"
    )
    pe_metric = st.selectbox("P/E metric", ["forward_pe", "trailing_pe"], index=0)
    ytd_range = st.slider("YTD return range (%)", -100, 200, (-50, 100), 5, key="scan_ytd")
    ytd_min, ytd_max = ytd_range
    min_5d = st.slider("Min 5D return (%)", -30, 30, -10, 1, key="scan_5d")


# --- Build candidate universe ---
st.title("💰 Valuation Scanner")
st.caption(
    "Cross-sectional scan — find cheap-on-multiple stocks with positive recent momentum. "
    "Sector-internal P/E percentile + YTD/5D filter. Latest: " + (db.latest_snapshot_date() or "—")
)

if not selected_sectors:
    st.warning("Select at least 1 sector in sidebar.")
    st.stop()

# Collect all tickers across selected sectors
all_tickers_by_sec: dict[str, list[str]] = {}
for sid in selected_sectors:
    tlist = db.sector_tickers("healthcare", sid)["ticker"].tolist()
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
if not mults.empty:
    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
        if c in mults.columns:
            merged[c] = mults[c]

# Sector-internal P/E percentile
# For each ticker, compute its P/E rank within its first sector
@st.cache_data(ttl=300)
def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str):
    """For each ticker, rank P/E within its sector (excluding NaN and negative).
    Returns (percentile [0,100] where 0 = cheapest, per-sector eligible-N dict,
    per-sector neg/missing-N dict)."""
    result: dict[str, float] = {}
    sector_n_eligible: dict[str, int] = {}
    sector_n_excluded: dict[str, int] = {}
    # Group tickers by sector
    sector_tickers: dict[str, list[str]] = {}
    for t, secs in _sector_map.items():
        for s in secs:
            sector_tickers.setdefault(s, []).append(t)

    for sec, t_list in sector_tickers.items():
        in_sec_all = _mults_df.loc[_mults_df.index.intersection(t_list), pe_col]
        # exclude non-positive (neg earnings) for percentile calc
        in_sec = in_sec_all[in_sec_all > 0].dropna()
        sector_n_eligible[sec] = len(in_sec)
        sector_n_excluded[sec] = len(t_list) - len(in_sec)
        if in_sec.empty:
            continue
        ranks = in_sec.rank(pct=True) * 100
        for t in t_list:
            if t in ranks.index:
                # Keep min percentile across sectors (cheapest sector ranking wins)
                if t not in result or ranks[t] < result[t]:
                    result[t] = float(ranks[t])
    return pd.Series(result, name="pe_percentile"), sector_n_eligible, sector_n_excluded


pe_pct, sec_n_elig, sec_n_excl = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
merged["pe_percentile"] = pe_pct

# m2/m3 audit: surface small-N + negative-excluded caveats
small_n_secs = {s: n for s, n in sec_n_elig.items() if n < 6 and n > 0}
total_neg_excl = sum(sec_n_excl.values())
if small_n_secs or total_neg_excl > 0:
    caveats = []
    if small_n_secs:
        caveats.append(
            "⚠️ **Small-N sectors** (percentile coarse): "
            + ", ".join(f"{s} (N={n})" for s, n in small_n_secs.items())
        )
    if total_neg_excl > 0:
        caveats.append(
            f"ℹ️ **{total_neg_excl} tickers excluded from P/E percentile** "
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
col1.metric("🌐 Universe scanned", f"{len(all_t)}")
col2.metric("✅ Candidates", f"{len(candidates)}")
col3.metric("📐 Median Mcap (USD B)",
            f"${candidates['market_cap_usd'].median()/1e9:.1f}B" if not candidates.empty else "—")
col4.metric("📈 Median YTD", fmt.fmt_pct(candidates['ytd_%'].median()) if not candidates.empty else "—")

if candidates.empty:
    st.warning(
        "🤷 No candidates match filters. Loosen criteria (lower min mcap / higher P/E threshold / widen YTD range)."
    )
    st.stop()

# Build display
disp = pd.DataFrame(index=candidates.index)
disp["BBG"] = [fmt.fmt_ticker_bbg(t) for t in disp.index]
disp["Name"] = [name_map.get(t, t) for t in disp.index]
# disp["Sectors"] = [", ".join(all_tickers_by_sec.get(t, [])) for t in disp.index] # Cull to save space
# disp["Tier"] = candidates.get("mcap_tier", pd.Series(index=candidates.index)).fillna("—")
disp["Mcap USD"] = candidates["market_cap_usd"].apply(fmt.fmt_money_b)
disp[f"{pe_metric.replace('_', ' ').title()}"] = candidates[pe_metric].apply(fmt.fmt_ratio)
disp["Sector P/E %ile"] = candidates["pe_percentile"].apply(lambda v: f"{v:.0f}%" if pd.notna(v) else "—")
disp["YTD %"] = candidates["ytd_%"].apply(fmt.fmt_pct)
disp["1M %"] = candidates["1m_%"].apply(fmt.fmt_pct)
disp["5D %"] = candidates["5d_%"].apply(fmt.fmt_pct)
disp["EV/EBITDA"] = candidates["ev_ebitda"].apply(fmt.fmt_ratio)
disp["FCF Yld"] = candidates["fcf_yield"].apply(fmt.fmt_pct_decimal)
disp.index.name = "Ticker"

# Color gradients
styler = disp.style
# ... (rest of style logic)
for col, num in [("YTD %", candidates["ytd_%"]), ("1M %", candidates["1m_%"]),
                 ("5D %", candidates["5d_%"])]:
    styler = styler.apply(
        lambda _s, n=num: fmt.background_gradient_diverging(n),
        subset=[col],
    )
# Lower better
styler = styler.apply(
    lambda _s: fmt.background_gradient_low_good(candidates[pe_metric]),
    subset=[f"{pe_metric.replace('_', ' ').title()}"],
)
styler = styler.apply(
    lambda _s: fmt.background_gradient_low_good(candidates["ev_ebitda"]),
    subset=["EV/EBITDA"],
)
# Higher better
styler = styler.apply(
    lambda _s: fmt.background_gradient_low_good(
        candidates["fcf_yield"], low_color="#dc2626", high_color="#16a34a"
    ),
    subset=["FCF Yld"],
)
# Sector P/E percentile column — low percentile = cheap = green
styler = styler.apply(
    lambda _s: fmt.background_gradient_low_good(candidates["pe_percentile"]),
    subset=["Sector P/E %ile"],
)

st.dataframe(styler, use_container_width=True, height=560)

# --- Interpretation hints ---
ui.onboarding_expander("Valuation Scanner", """
**Sector P/E %ile**：当前股票的 forward (or trailing) P/E 在所属板块内的分位。
- `0%-25%` = cheapest quartile within sector
- 一般 sell-side framework: 看 cheap multiple + 正面 momentum 一起 → 可能 re-rating 候选

**YTD %**: 年至今总回报。负 YTD + 低 P/E 可能是 "fallen angel" 候选。
正 YTD + 低 P/E 可能是 "value with momentum"。

**5D %**: 最近 5 个交易日 momentum。Filter 默认 ≥ -10% 排除崩盘中候选。

**EV/EBITDA**: complementary multiple，避免单看 P/E 误判（EPS 被一次性项目影响）。

**FCF Yield**: free cash flow / market cap. 高 = 现金生成能力强 = 好。

**Presets**:
- **Deep Value**: 寻找板块内极低估 (15%ile) 的大市值标的。
- **Recovery**: 寻找已经开始从底部回升 (5D % > 5%) 的低估标的。
""")

st.divider()
st.caption(
    "🎯 **Methodology**: Cross-sectional within selected sectors. Negative P/E excluded from percentile rank. "
    "Latest snapshot: " + (db.latest_snapshot_date() or "—") + ". "
    "Sector membership: many-to-many (ISRG ∈ hc_ai + medtech 等)."
)
