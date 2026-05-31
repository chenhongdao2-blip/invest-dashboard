"""Strategy Picks — v4/v5 biotech + HK 高股息 since-inception perf vs benchmark.

Phase 1 (bilingual + dual-track rebalance):
- Top-bar 中文/EN toggle (lib.i18n); all visible copy via t(); CN copy GLM-finalised.
- Two equal-weight curves: buy & hold (solid) + monthly rebalance (dashed, optional).
  Both computed once in strategy.compute_strategy_returns (single source) — charts
  consumes the series, never recomputes (cccg ship-gate #2).
- Per-strategy methodology expander sourced from CMS HK whitepapers (no placeholders).
- Data: data/external/picks.db (v5) + v4_picks.csv + hd_picks.csv; prices live via yfinance.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db  # noqa: F401  (kept for parity with other pages / future use)
from lib import format as fmt
from lib import strategy as strat
from lib import charts
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(
    page_title="Strategy Picks · invest-dashboard",
    page_icon="🧬",
    layout="wide",
)

# Language: seed once + render the top-bar switch BEFORE any t() call so the
# whole page renders in one language per run (cccg ship-gate #3).
i18n.init_lang()
i18n.render_lang_toggle()

# Sidebar global search + chart settings
with st.sidebar:
    ui.sidebar_search(key_prefix="strategy")
    st.divider()
    st.subheader(i18n.t("strategy.sidebar.chart_settings"))
    show_lines = st.checkbox(
        i18n.t("strategy.sidebar.show_individual"), value=False,
        help=i18n.t("strategy.sidebar.show_individual_help"),
    )
    show_rebal = st.checkbox(
        i18n.t("strategy.sidebar.show_rebalanced"), value=False,
        help=i18n.t("strategy.sidebar.show_rebalanced_help"),
    )

theme.page_header(i18n.t("strategy.page.title"))
st.caption(i18n.t("strategy.page.caption"))
st.markdown(i18n.t("strategy.pitch"))


def render_strategy(strat_id: str) -> None:
    cfg = strat.STRATEGIES[strat_id]
    picks = cfg["loader"]()
    if picks.empty:
        st.warning(f"No picks for {cfg['name']} — check data/external/")
        return

    pick_date = cfg["pick_date"]
    bench_sym = cfg["benchmark"]
    bench_name = cfg["benchmark_name"]
    disp_name = i18n.t(f"strategy.name.{strat_id}")

    # --- Methodology (sourced; biotech vs high-dividend) ---
    method_key = {
        "v4_biotech": "strategy.v4.method",
        "v5_biotech": "strategy.v5.method",
        "hk_hd": "strategy.hd.method",
    }.get(strat_id, "strategy.hd.method")
    with st.expander(i18n.t("strategy.method_expander")):
        st.markdown(i18n.t(method_key))

    # --- Top-N selection (scoring model: portfolio = top 20 by score rank) ---
    n_total = len(picks)
    top_n = min(20, n_total)
    picks_ranked = picks.sort_values("rank") if "rank" in picks.columns else picks
    top_syms = picks_ranked.head(top_n)["yf_sym"].dropna().tolist()

    # --- Header metrics ---
    days_since = (pd.Timestamp.now().normalize() - pd.Timestamp(pick_date)).days
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(i18n.t("strategy.metric.pick_date"), pick_date)
    c2.metric(i18n.t("strategy.metric.n_picks"), top_n,
              help=i18n.t("strategy.metric.holdings_help", n=n_total))
    c3.metric(i18n.t("strategy.metric.days_since"), days_since)
    c4.metric(i18n.t("strategy.metric.benchmark"), bench_sym)

    # --- Fetch prices ---
    yf_syms = tuple(picks["yf_sym"].dropna().unique().tolist())
    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=10)).date().isoformat()
    closes = strat.fetch_picks_closes(yf_syms + (bench_sym,), start=earliest)

    if closes.empty:
        st.error("Live price fetch failed. Check network/yfinance.")
        return

    bench_close = closes[bench_sym] if bench_sym in closes.columns else pd.Series(dtype=float)
    picks_closes = closes.drop(columns=[bench_sym], errors="ignore")

    # --- Compute returns (single source: buy&hold + monthly rebalance) ---
    normed, portfolio, portfolio_rebal, perf = strat.compute_strategy_returns(
        picks_closes, pick_date, portfolio_syms=top_syms
    )

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
        rebal_last = (portfolio_rebal.iloc[-1] - 100) if not portfolio_rebal.empty else None
        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
        alpha = (port_last - bench_last) if bench_last is not None else None

        show_rebal_metric = show_rebal and rebal_last is not None
        mcols = st.columns(4 if show_rebal_metric else 3)
        i = 0
        mcols[i].metric(i18n.t("strategy.metric.port_bh"), f"{port_last:+.2f}%")
        i += 1
        if show_rebal_metric:
            delta_bp = (rebal_last - port_last) * 100  # pp diff → basis points
            mcols[i].metric(
                i18n.t("strategy.metric.port_rebal"), f"{rebal_last:+.2f}%",
                delta=i18n.t("strategy.metric.delta_vs_bh", bp=delta_bp),
                delta_color="off",
            )
            i += 1
        mcols[i].metric(
            i18n.t("strategy.metric.benchmark_ret", sym=bench_sym),
            f"{bench_last:+.2f}%" if bench_last is not None else "—",
        )
        i += 1
        if i < len(mcols):
            delta_word = (
                i18n.t("strategy.delta.outperform") if alpha and alpha > 0
                else i18n.t("strategy.delta.underperform") if alpha
                else i18n.t("strategy.delta.tied")
            )
            mcols[i].metric(
                i18n.t("strategy.metric.alpha"),
                f"{alpha:+.2f}pp" if alpha is not None else "—",
                delta=delta_word,
                delta_color="normal" if alpha and alpha > 0 else "inverse" if alpha else "off",
            )

    # --- Cumulative return chart (consumes precomputed series) ---
    if not portfolio.empty:
        labels = {
            "portfolio": i18n.t("strategy.chart.line.portfolio"),
            "rebalanced": i18n.t("strategy.chart.line.rebalanced"),
            "band": i18n.t("strategy.chart.line.band"),
            "y": i18n.t("strategy.chart.y"),
        }
        fig = charts.cumulative_return_chart(
            normed, portfolio,
            portfolio_rebalanced=portfolio_rebal,
            title=i18n.t("strategy.chart.title", name=disp_name, date=pick_date),
            show_individual=show_lines,
            show_rebalanced=show_rebal,
            labels=labels,
        )
        # Benchmark overlay
        if not bench_norm.empty:
            fig.add_trace(go.Scatter(
                x=bench_norm.index, y=bench_norm.values,
                mode="lines",
                name=i18n.t("strategy.chart.line.benchmark", sym=bench_sym, name=bench_name),
                line=dict(width=1.5, color="#8a8580", dash="dash"),
            ))
        # theme=None: keep our PLOTLY_LAYOUT authoritative (cream bg + INK text).
        st.plotly_chart(fig, width="stretch", theme=None)

    # --- Top/Worst ranking tables ---
    if perf.empty:
        st.warning("No per-ticker performance data.")
        return

    # --- Ranked holdings table (scoring model → sort by SCORE RANK, not return) ---
    meta_cols = [c for c in ["rank", "name", "score"] if c in picks.columns]
    meta = picks.set_index("yf_sym")[meta_cols]
    perf = perf.join(meta, how="left")
    if "rank" in perf.columns:
        perf = perf.sort_values("rank", na_position="last")
    perf.index = [fmt.fmt_ticker_bbg(t) for t in perf.index]

    disp = perf.rename(columns={"rank": "Rank", "name": "Name", "score": "Score"})
    front_cols = ["Rank", "Name", "Score", "Last", "1D %", "5D %", "15D %", "30D %", "Since %"]
    disp = disp[[c for c in front_cols if c in disp.columns]]

    pct_cols_avail = [c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in disp.columns]
    extra_fmt = {}
    if "Last" in disp.columns:
        extra_fmt["Last"] = "%.2f"
    if "Score" in disp.columns:
        extra_fmt["Score"] = "%.2f"
    col_labels = {
        "Rank": i18n.t("strategy.col.rank"),
        "Name": i18n.t("strategy.col.name"),
        "Score": i18n.t("strategy.col.score"),
        "Last": i18n.t("strategy.col.last"),
        "Since %": i18n.t("strategy.col.since"),
    }

    def _render_perf(slice_df: pd.DataFrame, height: int = 560) -> None:
        ui.render_html_table(
            slice_df,
            int_cols=[c for c in ["Rank"] if c in slice_df.columns],
            pct_cols=[c for c in pct_cols_avail if c in slice_df.columns],
            text_cols=[c for c in ["Name"] if c in slice_df.columns],
            extra_formats=extra_fmt,
            column_labels=col_labels,
            index_label=i18n.t("strategy.col.ticker"),
            height=height,
        )

    # Top-N holdings (the actual portfolio) shown by default; full ranked universe in expander.
    st.markdown(f"##### {i18n.t('strategy.holdings.title')}")
    _render_perf(disp.head(top_n), height=560)
    if len(disp) > top_n:
        with st.expander(i18n.t("strategy.holdings.all", n=len(disp))):
            _render_perf(disp, height=620)


# --- Onboarding expander (i18n) ---
with st.expander(i18n.t("strategy.onboarding.title")):
    st.markdown(i18n.t("strategy.onboarding.body"))

# --- Tabs: one per strategy ---
strategy_tabs = st.tabs([
    i18n.t(f"strategy.name.{sid}") for sid in strat.STRATEGIES
])
for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
    with tab:
        render_strategy(sid)

st.divider()
st.caption(i18n.t("strategy.method.equal_weight"))
st.caption(i18n.t("strategy.method.total_return"))
st.caption(i18n.t("strategy.method.source"))
