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
from lib import ui
from lib import theme

st.set_page_config(
    page_title="Strategy Picks · invest-dashboard",
    page_icon="🧬",
    layout="wide",
)

# Sidebar global search
with st.sidebar:
    ui.sidebar_search(key_prefix="strategy")
    st.divider()
    st.subheader("Chart Settings")
    show_lines = st.checkbox("Show individual ticker lines", value=False, help="Display translucent lines for every ticker in the portfolio.")

theme.page_header("06 / 07", "Strategy Picks Performance")
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
    c1.metric("Pick date", pick_date)
    c2.metric("# picks", n_picks)
    c3.metric("Days since", days_since)
    c4.metric("Benchmark", bench_sym)

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
            "Portfolio since-inception",
            f"{port_last:+.2f}%",
            delta=None,
        )
        c2.metric(
            f"Benchmark ({bench_sym})",
            f"{bench_last:+.2f}%" if bench_last is not None else "—",
            delta=None,
        )
        c3.metric(
            "Alpha (pp)",
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
            show_individual=show_lines,
        )
        # Add benchmark overlay
        import plotly.graph_objects as go
        if not bench_norm.empty:
            fig.add_trace(go.Scatter(
                x=bench_norm.index, y=bench_norm.values,
                mode="lines", name=f"{bench_sym} ({bench_name})",
                line=dict(width=1.5, color="#8a8580", dash="dash"),
            ))
        # theme=None: do NOT let Streamlit re-theme the figure — our PLOTLY_LAYOUT
        # (cream bg + INK title/legend) is authoritative; theme="streamlit" washed
        # the title/legend text to a faint color on cream.
        st.plotly_chart(fig, width="stretch", theme=None)

    # --- Top/Worst ranking table ---
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

    pct_cols_avail = [c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"]
                      if c in perf_display.columns]
    text_cols_avail = [c for c in ["Name"] if c in perf_display.columns]
    extra_fmt = {}
    if "Last" in perf_display.columns:
        extra_fmt["Last"] = "%.2f"
    if "Pick Score" in perf_display.columns:
        extra_fmt["Pick Score"] = "%.2f"

    def _render_perf(slice_df: pd.DataFrame, height: int = 280) -> None:
        ui.render_styled_table(
            slice_df,
            pct_cols=pct_cols_avail,
            text_cols=text_cols_avail,
            extra_formats=extra_fmt,
            height=height,
        )

    c_top, c_bot = st.columns(2)
    with c_top:
        st.markdown(f"##### Top {min(5, len(perf_display))} (since-inception)")
        _render_perf(perf_display.head(5))
    with c_bot:
        st.markdown(f"##### Worst {min(5, len(perf_display))} (since-inception)")
        _render_perf(perf_display.tail(5).iloc[::-1])

    # --- Full table (expandable) ---
    with st.expander(f"All {len(perf_display)} picks (sorted by since-inception)"):
        _render_perf(perf_display, height=500)


# --- Onboarding expander ---
ui.onboarding_expander("Strategy Page", """
**Cumulative Return Chart**: 
- **Portfolio (Equal-weight)**: 每只票在 Pick Date 初始权重相同，展示其后的复合回报（Indexed=100）。
- **Benchmark**: 比较基准（如 XBI 或 3110.HK）的同步表现。
- **10th–90th %ile Range**: 阴影区域展示了组合内 80% 标的的表现分布。如果阴影很宽，说明个股分化巨大。
- **Individual Lines**: 可在侧边栏开启，查看每只具体股票的轨迹。

**Metrics**:
- **Alpha (pp)**: 组合回报减去基准回报的百分点差。
- **Pick Score**: 如果来自 catalyst-monitor，显示其当时的量化评分。

**Sorting**:
- **Top 5**: 累计回报最高的 5 只票。
- **Worst 5**: 累计回报最低的 5 只票（Worst first）。
""")


# --- M8 audit: tabs > dropdown ---
strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
    with tab:
        render_strategy(sid)

st.divider()
st.caption(
    "**Methodology**: Equal-weight portfolio cumulative return from pick date. "
    "All prices via yfinance (auto-adjusted for splits/dividends). "
    "Benchmark: XBI for biotech, 3110.HK for HK 高股息."
)
st.caption(
    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
)
