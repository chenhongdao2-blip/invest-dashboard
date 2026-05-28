"""Strategy Picks — v4/v5 biotech + HK 高股息 since-inception perf vs benchmark.

D4 implementation:
- 3 tabs (one per strategy)
- For each: cumulative return chart (portfolio vs benchmark) + per-pick ranking table
- Data: data/external/picks.db (v5) + data/external/v4_picks.csv + data/external/hd_picks.csv
- Price fetch: yfinance live, cached 1h (picks tickers not in main universe by design)
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt
from lib import strategy as strat
from lib import charts

st.set_page_config(
    page_title="Strategy Picks · invest-dashboard",
    page_icon="🧬",
    layout="wide",
)

# Sidebar global search (B4 audit, on every page)
with st.sidebar:
    st.subheader("🔍 Find ticker")
    pick = st.selectbox(
        "Jump to ticker drill",
        options=[""] + sorted(db.all_tickers()),
        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
        key="strategy_search",
    )
    if pick:
        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")

st.title("🧬 Strategy Picks Performance")
st.caption(
    "v4 / v5 biotech + HK 高股息 since-inception cumulative returns vs benchmark. "
    "Data source: ic-foundry ledger.db + scoring Excel, picks fetched live via yfinance."
)


def render_strategy(strat_id: str) -> None:
    cfg = strat.STRATEGIES[strat_id]
    picks = cfg["loader"]()
    if picks.empty:
        st.warning(f"No picks for {cfg['name']} — check data/external/")
        return

    pick_date = cfg["pick_date"]
    bench_sym = cfg["benchmark"]
    bench_name = cfg["benchmark_name"]

    # --- Header metrics ---
    n_picks = len(picks)
    days_since = (pd.Timestamp.now().normalize() - pd.Timestamp(pick_date)).days
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Pick date", pick_date)
    c2.metric("📊 # picks", n_picks)
    c3.metric("📆 Days since", days_since)
    c4.metric("📐 Benchmark", bench_sym)

    # --- Fetch prices ---
    yf_syms = tuple(picks["yf_sym"].dropna().unique().tolist())
    # Fetch from pick_date - 10 days for benchmark anchor
    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=10)).date().isoformat()
    closes = strat.fetch_picks_closes(yf_syms + (bench_sym,), start=earliest)

    if closes.empty:
        st.error("Live price fetch failed. Check network/yfinance.")
        return

    # Separate benchmark
    bench_close = closes[bench_sym] if bench_sym in closes.columns else pd.Series(dtype=float)
    picks_closes = closes.drop(columns=[bench_sym], errors="ignore")

    # --- Compute returns ---
    normed, portfolio, perf = strat.compute_strategy_returns(picks_closes, pick_date)

    # Benchmark norm to 100 at pick_date anchor
    bench_norm = pd.Series(dtype=float)
    if not bench_close.empty:
        anchor_ts = pd.Timestamp(pick_date)
        bench_sub = bench_close[bench_close.index >= anchor_ts].dropna()
        if not bench_sub.empty:
            bench_norm = (bench_sub / bench_sub.iloc[0]) * 100

    # --- Summary metrics ---
    if not portfolio.empty:
        port_last = portfolio.iloc[-1] - 100
        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
        alpha = (port_last - bench_last) if bench_last is not None else None
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "📈 Portfolio since-inception",
            f"{port_last:+.2f}%",
            delta=None,
        )
        c2.metric(
            f"📐 Benchmark ({bench_sym})",
            f"{bench_last:+.2f}%" if bench_last is not None else "—",
            delta=None,
        )
        c3.metric(
            "🎯 Alpha (pp)",
            f"{alpha:+.2f}pp" if alpha is not None else "—",
            delta=f"{'outperform' if alpha and alpha > 0 else 'underperform' if alpha else 'tied'}",
            delta_color="normal" if alpha and alpha > 0 else "inverse" if alpha else "off",
        )

    # --- Cumulative return chart ---
    if not portfolio.empty:
        # Build a 2-column DataFrame: portfolio + benchmark
        chart_df = pd.DataFrame({"Portfolio (equal-weight)": portfolio})
        if not bench_norm.empty:
            chart_df[f"{bench_sym} (benchmark)"] = bench_norm
        chart_df = chart_df.dropna(how="all")

        fig = charts.cumulative_return_chart(
            picks_closes[picks_closes.index >= pd.Timestamp(pick_date)],
            title=f"{cfg['name']} — Indexed return since {pick_date}",
            pick_date=pick_date,
        )
        # Add benchmark overlay
        import plotly.graph_objects as go
        if not bench_norm.empty:
            fig.add_trace(go.Scatter(
                x=bench_norm.index, y=bench_norm.values,
                mode="lines", name=f"{bench_sym} ({bench_name})",
                line=dict(width=3, color="#a78bfa", dash="dash"),
            ))
        st.plotly_chart(fig, use_container_width=True)

    # --- Top/Bottom ranking table ---
    if perf.empty:
        st.warning("No per-ticker performance data.")
        return

    # Merge in name + score from picks
    picks_meta = picks.set_index("yf_sym")[["name"]] if "yf_sym" in picks.columns else pd.DataFrame()
    if "score" in picks.columns and not picks.empty:
        picks_meta["Pick Score"] = picks.set_index("yf_sym")["score"]
    perf = perf.join(picks_meta, how="left")

    perf_sorted = perf.sort_values("Since %", ascending=False, na_position="last")
    perf_sorted.index = [fmt.fmt_ticker_bbg(t) for t in perf_sorted.index]

    # Re-order columns
    front_cols = ["name", "Pick Score", "Last", "1D %", "5D %", "15D %", "30D %", "Since %"]
    cols_to_show = [c for c in front_cols if c in perf_sorted.columns]
    perf_display = perf_sorted[cols_to_show].rename(columns={"name": "Name"})

    c_top, c_bot = st.columns(2)
    with c_top:
        st.markdown(f"##### 🟢 Top {min(5, len(perf_display))} (since-inception)")
        top5 = perf_display.head(5)
        styler = (
            top5.style
            .format({
                "Last": fmt.fmt_num,
                "Pick Score": "{:.2f}",
                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
            }, na_rep="—")
            .apply(fmt.style_pct_column,
                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in top5.columns])
        )
        st.dataframe(styler, use_container_width=True)
    with c_bot:
        st.markdown(f"##### 🔴 Bottom {min(5, len(perf_display))} (since-inception)")
        bot5 = perf_display.tail(5).iloc[::-1]
        styler = (
            bot5.style
            .format({
                "Last": fmt.fmt_num,
                "Pick Score": "{:.2f}",
                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
            }, na_rep="—")
            .apply(fmt.style_pct_column,
                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in bot5.columns])
        )
        st.dataframe(styler, use_container_width=True)

    # --- Full table (expandable) ---
    with st.expander(f"📋 All {len(perf_display)} picks (sorted by since-inception)"):
        styler = (
            perf_display.style
            .format({
                "Last": fmt.fmt_num,
                "Pick Score": "{:.2f}",
                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
            }, na_rep="—")
            .apply(fmt.style_pct_column,
                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in perf_display.columns])
        )
        st.dataframe(styler, use_container_width=True, height=500)


# --- M8 audit: tabs > dropdown ---
strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
    with tab:
        render_strategy(sid)

st.divider()
st.caption(
    "📊 **Methodology**: Equal-weight portfolio cumulative return from pick date. "
    "All prices via yfinance (auto-adjusted for splits/dividends). "
    "Benchmark: XBI for biotech, 3110.HK for HK 高股息."
)
st.caption(
    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
)
