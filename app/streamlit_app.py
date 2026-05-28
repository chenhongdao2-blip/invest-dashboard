"""invest-dashboard — Home page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import db
from lib import format as fmt

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Header ---
st.title("📊 Multi-Domain Investment Dashboard")
st.caption(
    "Sell-side healthcare coverage · v1 (P0) · data via yfinance · "
    "build: `streamlit_app.py` · plan: `~/.claude/plans/modular-toasting-spindle.md`"
)

latest = db.latest_snapshot_date()
fetch_utc = db.last_fetch_utc()
col1, col2, col3 = st.columns([2, 2, 3])
col1.metric("📅 Latest snapshot", latest or "—")
col2.metric("🕒 Last fetch (UTC)", fetch_utc[:16] if fetch_utc else "—")
n_tickers = len(db.all_tickers())
col3.metric("🌐 Universe tickers", f"{n_tickers}")

st.divider()

# --- Benchmarks ---
st.subheader("📐 Benchmarks")
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    show = bench_df.copy()
    # Build a display DataFrame with formatted strings + bg gradient on raw values
    display_cols = ["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]
    show = show[display_cols].rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    })
    styler = (
        show.style
        .format({
            "Last": fmt.fmt_num,
            "1D %": fmt.fmt_pct,
            "5D %": fmt.fmt_pct,
            "1M %": fmt.fmt_pct,
            "YTD %": fmt.fmt_pct,
        }, na_rep="—")
        .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    )
    st.dataframe(styler, use_container_width=True)
else:
    st.warning("Benchmark fetch failed (yfinance live, check network).")

st.divider()

# --- Top movers ---
st.subheader("🏆 Today's Top Movers (across all 7 healthcare sectors)")
gainers, losers = db.top_movers(n=10)
if gainers.empty:
    st.info("No price data — run `jobs/fetch_eod.py --backfill-days 30`.")
else:
    movers_col1, movers_col2 = st.columns(2)
    pct_cols = ["1d_%", "5d_%", "1m_%", "ytd_%"]
    rename_map = {"name": "Name", "last": "Last",
                  "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %"}

    with movers_col1:
        st.markdown("##### 🟢 Top 10 Gainers")
        g = gainers.rename(columns=rename_map)
        styler = (
            g.style
            .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
                     "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
                    na_rep="—")
            .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
        )
        st.dataframe(styler, use_container_width=True)

    with movers_col2:
        st.markdown("##### 🔴 Top 10 Drags")
        l = losers.rename(columns=rename_map)
        styler = (
            l.style
            .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
                     "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
                    na_rep="—")
            .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
        )
        st.dataframe(styler, use_container_width=True)

st.divider()

# --- Universe ---
st.subheader("🌐 Universe Coverage")
uni = db.universe_summary()
if not uni.empty:
    st.dataframe(uni.rename(columns={"domain": "Domain", "sector": "Sector", "n": "Tickers"}),
                 use_container_width=True, hide_index=True)
else:
    st.warning("universe_member empty — run `jobs/load_universe.py`")

# --- Footer ---
st.divider()
st.caption(
    "⚠️ **Data caveat**: valuation multiples are from **yfinance** "
    "(trailing P/E + 12M forward P/E). Multi-year forward (25E / 26E / 27E) "
    "requires Bloomberg / FactSet and is **not in scope**. "
    "Use this dashboard for quick visual scan; refer to your manual Excel comp tables for precise consensus."
)
st.caption(
    f"Repo: [github.com/chenhongdao2-blip/invest-dashboard](https://github.com/chenhongdao2-blip/invest-dashboard) · "
    f"Data: SQLite committed in repo · "
    f"Auto-update: GitHub Actions cron (22:30 UTC US + 09:00 UTC HK)"
)
