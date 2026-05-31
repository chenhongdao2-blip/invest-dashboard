"""Market Data — full-universe quote table (all domains) + downloads.

One-page market scan across the ENTIRE universe (not healthcare-only): latest
price, 1D/5D/YTD returns, trailing/forward P/E, market cap. Two CSV exports:
the current (filtered) quote table, and the raw security master (universe_member).

Industry-agnostic: pulls every ticker regardless of domain, with domain/region
filters so it stays useful as new domains (AI, etc.) are added.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(
    page_title="Market Data · invest-dashboard",
    page_icon="📊",
    layout="wide",
)


# ── per-ticker roster (one row/ticker; sectors concatenated) ──
@st.cache_data(ttl=300)
def ticker_roster() -> pd.DataFrame:
    return db.query(
        """SELECT ticker,
                  MAX(name_cn) AS name_cn, MAX(name_en) AS name_en,
                  MAX(domain)  AS domain,
                  GROUP_CONCAT(DISTINCT sector) AS sectors,
                  MAX(region)  AS region
           FROM universe_member
           GROUP BY ticker
           ORDER BY ticker"""
    )


@st.cache_data(ttl=300)
def security_master_csv() -> bytes:
    """Raw universe_member (every membership row, all columns) → CSV bytes."""
    df = db.query(
        "SELECT domain, sector, ticker, name_cn, name_en, region, note "
        "FROM universe_member ORDER BY domain, sector, ticker"
    )
    return df.to_csv(index=False).encode("utf-8-sig")


# ── sidebar ──
i18n.init_lang()
with st.sidebar:
    ui.sidebar_search(key_prefix="market")

roster = ticker_roster()

with st.sidebar:
    st.divider()
    domains = sorted(d for d in roster["domain"].dropna().unique())
    regions = sorted(r for r in roster["region"].dropna().unique())
    sel_domains = st.multiselect(
        i18n.t("market.filters.domain"), options=domains, default=domains,
        format_func=i18n.domain_name, key="mkt_domains",
    )
    sel_regions = st.multiselect(
        i18n.t("market.filters.region"), options=regions, default=regions,
        key="mkt_regions",
    )

# ── header ──
i18n.render_lang_toggle()
theme.page_header(i18n.t("market.title"))
st.caption(i18n.t("market.caption", n=len(roster), date=(db.latest_snapshot_date() or "—")))

filt = roster.copy()
if sel_domains:
    filt = filt[filt["domain"].isin(sel_domains)]
if sel_regions:
    filt = filt[filt["region"].isin(sel_regions)]

all_t = tuple(filt["ticker"].tolist())
if not all_t:
    st.warning("No tickers match the current filters.")
    st.stop()

# ── data ──
closes = db.get_close_series_usd(all_t)
rets = db.compute_returns(closes)
mults = db.latest_multiples(all_t)
prefer_cn = i18n.get_lang() == "zh"
name_map = db.ticker_to_name(prefer_cn=prefer_cn)

# ── assemble numeric display frame (render_html_table formats it) ──
# Build on the RAW ticker index so the rets/mults joins line up; the index is
# relabelled to Bloomberg format just before render (no separate BBG column — it
# duplicated the ticker for US names like LLY/LLY).
disp = pd.DataFrame(index=filt["ticker"])
disp.index.name = "Ticker"
disp["Name"] = [name_map.get(t, t) for t in disp.index]
def _fmt_sectors(sec_csv: str) -> str:
    # _coverage marker first (easier to filter/sort on), real sectors after → "覆盖 / 生物科技"
    parts = [s for s in (sec_csv or "").split(",") if s]
    parts.sort(key=lambda s: (s != "_coverage", s))
    return " / ".join(i18n.sector_name(s) for s in parts)


disp["Sector"] = [
    _fmt_sectors(sec)
    for sec in filt.set_index("ticker")["sectors"].reindex(disp.index).fillna("")
]
disp["Region"] = filt.set_index("ticker")["region"].reindex(disp.index).values


def _col(src: pd.DataFrame, col: str):
    return src[col].reindex(disp.index) if (not src.empty and col in src.columns) else pd.NA


disp["Last"] = _col(rets, "last")
disp["1D %"] = _col(rets, "1d_%")
disp["5D %"] = _col(rets, "5d_%")
disp["YTD %"] = _col(rets, "ytd_%")
disp["Trail P/E"] = _col(mults, "trailing_pe")
disp["Fwd P/E"] = _col(mults, "forward_pe")
disp["Mcap USD ($B)"] = _col(mults, "market_cap_usd") / 1e9

disp = disp.sort_values("Mcap USD ($B)", ascending=False, na_position="last")
# relabel index to Bloomberg style for display (e.g. 2269.HK → "2269 HK")
disp.index = [fmt.fmt_ticker_bbg(t) for t in disp.index]
disp.index.name = "Ticker"

# ── metrics + downloads ──
m1, m2, _ = st.columns([1, 1, 4])
m1.metric(i18n.t("market.metric.universe"), f"{len(roster)}")
m2.metric(i18n.t("market.metric.shown"), f"{len(disp)}")

d1, d2, _ = st.columns([1.4, 1.6, 3])
d1.download_button(
    i18n.t("market.dl.quotes"),
    data=disp.reset_index().to_csv(index=False).encode("utf-8-sig"),
    file_name=f"market_data_{db.latest_snapshot_date() or 'latest'}.csv",
    mime="text/csv",
    width="stretch",
)
d2.download_button(
    i18n.t("market.dl.master"),
    data=security_master_csv(),
    file_name="security_master.csv",
    mime="text/csv",
    help=i18n.t("market.dl.master_help"),
    width="stretch",
)

# ── table ──
theme.section_header(i18n.t("market.section.table"))
ui.render_html_table(
    disp,
    pct_cols=["1D %", "5D %", "YTD %"],
    mult_cols=["Trail P/E", "Fwd P/E"],
    money_b_cols=["Mcap USD ($B)"],
    price_cols=["Last"],
    text_cols=["Name", "Sector", "Region"],
    height=620,
    column_labels={
        **i18n.common_cols(),
        "Sector": i18n.t("market.col.sector"),
        "Region": i18n.t("market.col.region"),
    },
    index_label=i18n.t("common.col.ticker"),
)

with st.expander(i18n.t("market.onboarding.title")):
    st.markdown(i18n.t("market.onboarding.body"))
