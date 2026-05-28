"""invest-dashboard — Home page.

Audit fixes:
- M7: pre-format strings + Styler color-only
- M10: name_cn priority
- B4: global ticker search in sidebar (stub for D6 Ticker Drill)
- n2: Bloomberg ticker style display
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Unified sidebar search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="home")

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


def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
    """Sort-bug-safe: numeric DataFrame + column_config + Styler color (delegates to ui)."""
    text_cols = [c for c in df.columns if c not in pct_cols and (num_cols is None or c not in num_cols)]
    extra_formats = {c: "%.2f" for c in (num_cols or []) if c in df.columns}
    ui.render_styled_table(
        df,
        pct_cols=pct_cols,
        text_cols=text_cols,
        extra_formats=extra_formats,
        height=360,
    )


# --- Benchmarks ---
st.subheader("📐 Benchmarks")
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    show = bench_df[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]].rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    })
    _render_pct_table(show, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])
else:
    st.warning("Benchmark fetch failed (yfinance live, check network).")

st.divider()

# --- Top movers ---
st.subheader("🏆 Today's Top Movers (across all 7 healthcare sectors)")
gainers, losers = db.top_movers(n=10)
if gainers.empty:
    st.info("No price data — run `jobs/fetch_eod.py --backfill-days 180`.")
else:
    rename_map = {"name": "Name", "last": "Last",
                  "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %"}

    movers_col1, movers_col2 = st.columns(2)
    with movers_col1:
        st.markdown("##### 🟢 Top 10 Gainers")
        g = gainers.rename(columns=rename_map)
        # n2: rewrite index to Bloomberg style
        g.index = [fmt.fmt_ticker_bbg(t) for t in g.index]
        _render_pct_table(g, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])

    with movers_col2:
        st.markdown("##### 🔴 Top 10 Drags")
        l = losers.rename(columns=rename_map)
        l.index = [fmt.fmt_ticker_bbg(t) for t in l.index]
        _render_pct_table(l, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])

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
    "Repo: [github.com/chenhongdao2-blip/invest-dashboard](https://github.com/chenhongdao2-blip/invest-dashboard) · "
    "Data: SQLite committed in repo · "
    "Auto-update: GitHub Actions cron (22:30 UTC US + 09:00 UTC HK)"
)
