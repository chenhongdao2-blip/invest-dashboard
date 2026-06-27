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

import math

import numpy as np
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
    bench2_sym = cfg.get("benchmark2")
    bench2_name = cfg.get("benchmark2_name", "")
    disp_name = i18n.t(f"strategy.name.{strat_id}")

    # --- Methodology (sourced; biotech vs high-dividend) ---
    method_key = {
        "v4_biotech": "strategy.v4.method",
        "v5_biotech": "strategy.v5.method",
        "hk_hd": "strategy.hd.method",
        "hk_hd_v2": "strategy.hd.v2.method",
    }.get(strat_id, "strategy.hd.method")
    with st.expander(i18n.t("strategy.method_expander")):
        st.markdown(i18n.t(method_key))

    # --- Top-N selection (scoring model: portfolio = top 20 by score rank) ---
    n_total = len(picks)
    top_n = min(20, n_total)
    picks_ranked = picks.sort_values("rank") if "rank" in picks.columns else picks
    top_syms = picks_ranked.head(top_n)["yf_sym"].dropna().tolist()

    # --- Weighted book (HD v2): published weights + idle-cash sleeve ---
    weight_col = cfg.get("weight_col")
    cash_pct = float(cfg.get("cash_pct", 0.0))
    weights = None
    if weight_col and weight_col in picks.columns:
        weights = picks.set_index("yf_sym")[weight_col].astype(float) / 100.0

    # --- Header metrics (KPI cards — house style, replaces st.metric) ---
    days_since = (pd.Timestamp.now().normalize() - pd.Timestamp(pick_date)).days
    holdings_foot = (
        i18n.t("strategy.metric.holdings_foot_weighted", cash=cash_pct)
        if weights is not None
        else i18n.t("strategy.metric.holdings_foot", n=n_total)
    )
    theme.kpi_strip([
        theme.kpi_metric(i18n.t("strategy.metric.pick_date"), str(pick_date)),
        theme.kpi_metric(i18n.t("strategy.metric.n_picks"), str(top_n),
                         foot=holdings_foot),
        theme.kpi_metric(i18n.t("strategy.metric.days_since"), str(days_since)),
        theme.kpi_metric(i18n.t("strategy.metric.benchmark"), bench_sym,
                         foot=bench_name),
    ])

    # --- Fetch prices ---
    yf_syms = tuple(picks["yf_sym"].dropna().unique().tolist())
    # 55 calendar days ≈ 30+ trading days of pre-inception history so the
    # trailing 15D/30D columns have data even on a freshly built book (v2).
    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=55)).date().isoformat()
    bench_syms = tuple(s for s in (bench_sym, bench2_sym) if s)
    closes = strat.fetch_picks_closes(yf_syms + bench_syms, start=earliest,
                                      _ovr_mtime=strat._delisted_mtime())

    if closes.empty:
        st.error("Live price fetch failed. Check network/yfinance.")
        return

    bench_close = closes[bench_sym] if bench_sym in closes.columns else pd.Series(dtype=float)
    bench2_close = (closes[bench2_sym]
                    if bench2_sym and bench2_sym in closes.columns
                    else pd.Series(dtype=float))
    picks_closes = closes.drop(columns=list(bench_syms), errors="ignore")

    # --- Compute returns (single source: buy&hold + monthly rebalance) ---
    normed, portfolio, portfolio_rebal, perf = strat.compute_strategy_returns(
        picks_closes, pick_date, portfolio_syms=top_syms,
        weights=weights, cash_pct=cash_pct,
    )

    # Benchmark norm to 100 at pick_date anchor
    def _bench_norm(close: pd.Series) -> pd.Series:
        if close.empty:
            return pd.Series(dtype=float)
        sub = close[close.index >= pd.Timestamp(pick_date)].dropna()
        return (sub / sub.iloc[0]) * 100 if not sub.empty else pd.Series(dtype=float)

    bench_norm = _bench_norm(bench_close)
    bench2_norm = _bench_norm(bench2_close)

    # --- Summary metrics (KPI cards — house style, replaces st.metric) ---
    asof = (picks_closes.index[-1].date().isoformat()
            if not picks_closes.empty else "")
    if not portfolio.empty:
        port_last = portfolio.iloc[-1] - 100
        rebal_last = (portfolio_rebal.iloc[-1] - 100) if not portfolio_rebal.empty else None
        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
        alpha = (port_last - bench_last) if bench_last is not None else None

        def _dir(x) -> str:
            return "up" if x is not None and x > 0 else (
                "down" if x is not None and x < 0 else "flat")

        def _gly(x) -> str:
            return "▲" if x is not None and x > 0 else (
                "▼" if x is not None and x < 0 else "·")

        cards = [theme.kpi_metric(
            i18n.t("strategy.metric.port_bh"), f"{port_last:+.2f}%",
            delta_abs=_gly(port_last), direction=_dir(port_last),
        )]
        if show_rebal and rebal_last is not None:
            delta_bp = (rebal_last - port_last) * 100  # pp diff → basis points
            cards.append(theme.kpi_metric(
                i18n.t("strategy.metric.port_rebal"), f"{rebal_last:+.2f}%",
                delta_pct=i18n.t("strategy.metric.delta_vs_bh", bp=delta_bp),
                direction="flat",
            ))
        cards.append(theme.kpi_metric(
            i18n.t("strategy.metric.benchmark_ret", sym=bench_sym),
            f"{bench_last:+.2f}%" if bench_last is not None else "—",
            delta_abs=_gly(bench_last), direction=_dir(bench_last),
        ))
        if not bench2_norm.empty:
            b2_last = bench2_norm.iloc[-1] - 100
            cards.append(theme.kpi_metric(
                i18n.t("strategy.metric.benchmark_ret", sym=bench2_sym),
                f"{b2_last:+.2f}%",
                delta_abs=_gly(b2_last), direction=_dir(b2_last),
            ))
        delta_word = (
            i18n.t("strategy.delta.outperform") if alpha and alpha > 0
            else i18n.t("strategy.delta.underperform") if alpha
            else i18n.t("strategy.delta.tied")
        )
        cards.append(theme.kpi_metric(
            i18n.t("strategy.metric.alpha"),
            f"{alpha:+.2f}pp" if alpha is not None else "—",
            delta_abs=delta_word, direction=_dir(alpha),
        ))
        theme.kpi_strip(cards)
        # 口径声明: auto_adjust=True → "Close" 是复权总回报(含息); 组合与基准同口径
        # (lib/strategy.py fetch_picks_closes)。高息股除息日股价机械下跌已被复权抵消。
        st.caption(i18n.t("strategy.metric.totalreturn_note"))
        if weights is not None:
            st.caption(i18n.t("strategy.hd.v2.cash_note", cash=cash_pct))

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
        if not bench2_norm.empty:
            fig.add_trace(go.Scatter(
                x=bench2_norm.index, y=bench2_norm.values,
                mode="lines",
                name=i18n.t("strategy.chart.line.benchmark", sym=bench2_sym, name=bench2_name),
                line=dict(width=1.5, color="#4a6fa5", dash="dot"),
            ))
        # theme=None: keep our PLOTLY_LAYOUT authoritative (cream bg + INK text).
        st.plotly_chart(fig, width="stretch", theme=None)
        if asof:
            theme.provenance(i18n.t("common.provenance", src="yfinance", asof=asof))

    # --- Top/Worst ranking tables ---
    if perf.empty:
        st.warning("No per-ticker performance data.")
        return

    # --- Ranked holdings table (scoring model → sort by SCORE RANK, not return) ---
    # HD v2 extras (weight/bucket/runrate) join automatically when present.
    meta_cols = [c for c in ["rank", "name", "score", "weight_pct", "bucket",
                             "runrate_pct"] if c in picks.columns]
    meta = picks.set_index("yf_sym")[meta_cols]
    perf = perf.join(meta, how="left")
    if "weight_pct" in perf.columns and "Since %" in perf.columns:
        # Contribution to basket NAV since inception = build weight × since-entry
        # return; cash buffer contributes 0 (conservative cash=0% convention), so
        # the column sums to ≈ the buy & hold curve's since-inception return.
        perf["contrib_pct"] = perf["weight_pct"] / 100.0 * perf["Since %"]
    if "rank" in perf.columns:
        perf = perf.sort_values("rank", na_position="last")
    if "bucket" in perf.columns:
        perf["bucket"] = perf["bucket"].map(
            lambda b: i18n.t(f"strategy.hd.bucket.{b}") if isinstance(b, str) else b)
    # 30-trading-day sparkline closes per ticker (fetch window is 55 calendar
    # days, so even a fresh book has a full pre-inception window).
    perf["spark"] = [
        picks_closes[t].dropna().tail(30).tolist()
        if t in picks_closes.columns else []
        for t in perf.index
    ]
    perf.index = [fmt.fmt_ticker_bbg(t) for t in perf.index]

    disp = perf.rename(columns={
        "rank": "Rank", "name": "Name", "score": "Score",
        "weight_pct": "Weight", "bucket": "Bucket", "runrate_pct": "Yield",
        "contrib_pct": "Contrib", "spark": "Spark",
    })
    front_cols = ["Rank", "Name", "Score", "Weight", "Bucket", "Yield",
                  "Last", "Spark", "1D %", "5D %", "15D %", "30D %",
                  "Since %", "Contrib"]
    disp = disp[[c for c in front_cols if c in disp.columns]]

    pct_cols_avail = [c for c in ["1D %", "5D %", "15D %", "30D %", "Since %", "Contrib"]
                      if c in disp.columns]
    extra_fmt = {}
    for c, f in (("Last", "%.2f"), ("Score", "%.2f"),
                 ("Weight", "%.2f"), ("Yield", "%.2f")):
        if c in disp.columns:
            extra_fmt[c] = f
    col_labels = {
        "Rank": i18n.t("strategy.col.rank"),
        "Name": i18n.t("strategy.col.name"),
        "Score": i18n.t("strategy.col.score"),
        "Weight": i18n.t("strategy.col.weight"),
        "Bucket": i18n.t("strategy.col.bucket"),
        "Yield": i18n.t("strategy.col.runrate"),
        "Last": i18n.t("strategy.col.last"),
        "Spark": i18n.t("strategy.col.spark"),
        "Since %": i18n.t("strategy.col.since"),
        "Contrib": i18n.t("strategy.col.contrib"),
    }

    def _render_perf(slice_df: pd.DataFrame, height: int = 560) -> None:
        ui.render_html_table(
            slice_df,
            int_cols=[c for c in ["Rank"] if c in slice_df.columns],
            pct_cols=[c for c in pct_cols_avail if c in slice_df.columns],
            text_cols=[c for c in ["Name", "Bucket"] if c in slice_df.columns],
            spark_cols=[c for c in ["Spark"] if c in slice_df.columns],
            bar_cols=[c for c in ["Weight", "Contrib"] if c in slice_df.columns],
            extra_formats=extra_fmt,
            column_labels=col_labels,
            index_label=i18n.t("strategy.col.ticker"),
            height=height,
        )

    # Top-N holdings (the actual portfolio) shown by default; full ranked universe in expander.
    holdings_title_key = ("strategy.holdings.title_weighted" if weights is not None
                          else "strategy.holdings.title")
    st.markdown(f"##### {i18n.t(holdings_title_key)}")
    _render_perf(disp.head(top_n), height=560)
    if asof:
        theme.provenance(i18n.t("common.provenance", src="yfinance", asof=asof))
    if len(disp) > top_n:
        with st.expander(i18n.t("strategy.holdings.all", n=len(disp))):
            _render_perf(disp, height=620)


def render_hd_versions() -> None:
    """HK 高股息 tab = version group: v2 (current, default) / v1 (history,
    frozen curve keeps running) / v1-vs-v2 compare. One tab, three views —
    v1 history is never truncated; v2 is a NEW book from 2026-06-11."""
    opts = [
        i18n.t("strategy.hd.version.v2"),
        i18n.t("strategy.hd.version.v1"),
        i18n.t("strategy.hd.version.compare"),
    ]
    choice = st.segmented_control(
        i18n.t("strategy.hd.version.toggle"), opts, default=opts[0],
        key="hd_version",
    ) or opts[0]
    if choice == opts[1]:
        st.caption(i18n.t("strategy.hd.version.v1_note"))
        render_strategy("hk_hd")
    elif choice == opts[2]:
        render_hd_compare()
    else:
        render_strategy("hk_hd_v2")


def render_hd_compare() -> None:
    """v1 vs v2 overlay + rebalance diff.

    Overlay: each curve indexed to 100 at its OWN inception (independent books,
    NOT a chained NAV); benchmark anchored at v1 inception. Diff is computed
    from the two CSVs (never hand-filled), against the v1 TOP-20 NAV book —
    the equal-weight portfolio the page has been tracking — not the 34-name
    scored universe.
    """
    v1 = strat.load_hd()
    v2 = strat.load_hd_v2()
    if v1.empty or v2.empty:
        st.warning("Need both hd_picks.csv and hd_picks_v2.csv — check data/external/")
        return
    cfg1 = strat.STRATEGIES["hk_hd"]
    cfg2 = strat.STRATEGIES["hk_hd_v2"]
    bench_sym = cfg1["benchmark"]
    bench2_sym = cfg1.get("benchmark2")

    v1_book = v1.sort_values("rank").head(20)
    v2_book = v2.sort_values("rank")
    v1_syms = v1_book["yf_sym"].dropna().tolist()
    v2_syms = v2_book["yf_sym"].dropna().tolist()

    # --- Prices: one fetch covering both books + benchmarks, from v1 inception ---
    all_syms = tuple(dict.fromkeys(
        v1_syms + v2_syms + [s for s in (bench_sym, bench2_sym) if s]))
    earliest = (pd.Timestamp(cfg1["pick_date"]) - pd.Timedelta(days=10)).date().isoformat()
    closes = strat.fetch_picks_closes(all_syms, start=earliest,
                                      _ovr_mtime=strat._delisted_mtime())
    if closes.empty:
        st.error("Live price fetch failed. Check network/yfinance.")
        return

    # v1 curve: equal-weight top-20 from 2026-03-20 (existing semantics, untouched)
    _, port_v1, _, _ = strat.compute_strategy_returns(
        closes[[c for c in v1_syms if c in closes.columns]],
        cfg1["pick_date"], portfolio_syms=v1_syms,
    )
    # v2 curve: published weights + 12% cash from 2026-06-11
    w2 = v2_book.set_index("yf_sym")[cfg2["weight_col"]].astype(float) / 100.0
    _, port_v2, _, _ = strat.compute_strategy_returns(
        closes[[c for c in v2_syms if c in closes.columns]],
        cfg2["pick_date"], portfolio_syms=v2_syms,
        weights=w2, cash_pct=cfg2["cash_pct"],
    )
    def _cmp_norm(sym: str | None) -> pd.Series:
        if not sym or sym not in closes.columns:
            return pd.Series(dtype=float)
        b = closes[sym].dropna()
        b = b[b.index >= pd.Timestamp(cfg1["pick_date"])]
        return (b / b.iloc[0]) * 100 if not b.empty else pd.Series(dtype=float)

    bench_norm = _cmp_norm(bench_sym)
    bench2_norm = _cmp_norm(bench2_sym)

    # --- Summary metrics (as-of latest close) ---
    mc = st.columns(4 if not bench2_norm.empty else 3)
    if not port_v1.empty:
        mc[0].metric(i18n.t("strategy.hd.compare.metric.v1"),
                     f"{port_v1.iloc[-1] - 100:+.2f}%",
                     help=f"inception {cfg1['pick_date']}")
    if not port_v2.empty:
        mc[1].metric(i18n.t("strategy.hd.compare.metric.v2"),
                     f"{port_v2.iloc[-1] - 100:+.2f}%",
                     help=f"inception {cfg2['pick_date']}")
    if not bench_norm.empty:
        mc[2].metric(i18n.t("strategy.metric.benchmark_ret", sym=bench_sym),
                     f"{bench_norm.iloc[-1] - 100:+.2f}%",
                     help=f"anchor {cfg1['pick_date']}")
    if not bench2_norm.empty:
        mc[3].metric(i18n.t("strategy.metric.benchmark_ret", sym=bench2_sym),
                     f"{bench2_norm.iloc[-1] - 100:+.2f}%",
                     help=f"anchor {cfg1['pick_date']}")

    # --- Overlay chart: v1 + v2 + benchmark, v2 inception marked ---
    fig = go.Figure()
    if not bench_norm.empty:
        fig.add_trace(go.Scatter(
            x=bench_norm.index, y=bench_norm.values, mode="lines",
            name=i18n.t("strategy.chart.line.benchmark",
                        sym=bench_sym, name=cfg1["benchmark_name"]),
            line=dict(width=1.5, color="#8a8580", dash="dash"),
        ))
    if not bench2_norm.empty:
        fig.add_trace(go.Scatter(
            x=bench2_norm.index, y=bench2_norm.values, mode="lines",
            name=i18n.t("strategy.chart.line.benchmark",
                        sym=bench2_sym, name=cfg1.get("benchmark2_name", "")),
            line=dict(width=1.5, color="#4a6fa5", dash="dot"),
        ))
    if not port_v1.empty:
        fig.add_trace(go.Scatter(
            x=port_v1.index, y=port_v1.values, mode="lines",
            name=i18n.t("strategy.hd.compare.v1_line"),
            line=dict(width=1.5, color=charts.SECONDARY),
        ))
    if not port_v2.empty:
        fig.add_trace(go.Scatter(
            x=port_v2.index, y=port_v2.values, mode="lines",
            name=i18n.t("strategy.hd.compare.v2_line"),
            line=dict(width=2.0, color=charts.PRIMARY),
        ))
    fig.add_vline(x=pd.Timestamp(cfg2["pick_date"]), line_width=1,
                  line_dash="dot", line_color="#8a8580")
    fig.add_annotation(x=pd.Timestamp(cfg2["pick_date"]), y=1.02, yref="paper",
                       text=i18n.t("strategy.hd.compare.rebal_label"),
                       showarrow=False, font=dict(size=11, color="#4a4a4a"))
    fig.update_layout(
        title=i18n.t("strategy.hd.compare.title"),
        yaxis_title=i18n.t("strategy.chart.y"),
        height=450,
    )
    st.plotly_chart(theme.style_plotly(fig), width="stretch", theme=None)
    st.caption(i18n.t("strategy.hd.compare.note"))

    # --- Rebalance diff: kept / added / removed, computed from the two CSVs ---
    theme.section_header(i18n.t("strategy.hd.diff.title"))
    v1_set = set(v1_book["ticker"])
    v2_set = set(v2_book["ticker"])
    v1_names = v1_book.set_index("ticker")
    v2_names = v2_book.set_index("ticker")
    EQ_W = 100.0 / len(v1_book)  # v1 equal weight per name (top-20 book → 5%)

    kept_tk = [t for t in v2_book["ticker"] if t in v1_set]      # v2 rank order
    added_tk = [t for t in v2_book["ticker"] if t not in v1_set]  # v2 rank order
    removed_tk = [t for t in v1_book["ticker"] if t not in v2_set]  # v1 rank order

    col_name = i18n.t("strategy.col.name")
    col_v1w = i18n.t("strategy.hd.diff.col.v1w")
    col_v2w = i18n.t("strategy.hd.diff.col.v2w")
    col_bucket = i18n.t("strategy.col.bucket")
    col_sector = i18n.t("strategy.hd.diff.col.sector")

    def _bucket_lab(t: str) -> str:
        b = v2_names.loc[t, "bucket"]
        return i18n.t(f"strategy.hd.bucket.{b}") if isinstance(b, str) else "—"

    kept_df = pd.DataFrame({
        col_name: [v2_names.loc[t, "name"] for t in kept_tk],
        col_v1w: [f"{EQ_W:.1f}" for _ in kept_tk],
        col_v2w: [f"{v2_names.loc[t, 'weight_pct']:.2f}" for t in kept_tk],
        col_bucket: [_bucket_lab(t) for t in kept_tk],
    }, index=kept_tk)
    added_df = pd.DataFrame({
        col_name: [v2_names.loc[t, "name"] for t in added_tk],
        col_v2w: [f"{v2_names.loc[t, 'weight_pct']:.2f}" for t in added_tk],
        col_bucket: [_bucket_lab(t) for t in added_tk],
    }, index=added_tk)
    removed_df = pd.DataFrame({
        col_name: [v1_names.loc[t, "name"] for t in removed_tk],
        col_v1w: [f"{EQ_W:.1f}" for _ in removed_tk],
        col_sector: [v1_names.loc[t, "sector"] for t in removed_tk],
    }, index=removed_tk)

    d1, d2, d3 = st.columns(3)
    _tk_lbl = i18n.t("strategy.col.ticker")
    with d1:
        st.markdown(f"##### {i18n.t('strategy.hd.diff.kept', n=len(kept_tk))}")
        ui.render_html_table(kept_df, text_cols=list(kept_df.columns),
                             index_label=_tk_lbl, height=520)
    with d2:
        st.markdown(f"##### {i18n.t('strategy.hd.diff.added', n=len(added_tk))}")
        ui.render_html_table(added_df, text_cols=list(added_df.columns),
                             index_label=_tk_lbl, height=520)
    with d3:
        st.markdown(f"##### {i18n.t('strategy.hd.diff.removed', n=len(removed_tk))}")
        ui.render_html_table(removed_df, text_cols=list(removed_df.columns),
                             index_label=_tk_lbl, height=520)
    st.caption(i18n.t("strategy.hd.diff.note"))


def _spearman_rho(x: pd.Series, y: pd.Series) -> float:
    """Spearman rank correlation = Pearson on ranks (no scipy dependency)."""
    rx, ry = x.rank(), y.rank()
    if len(rx) < 2 or rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def _spearman_pval(rho: float, n: int) -> float:
    """Two-sided p-value for Spearman ρ via the normal approximation.

    z = ρ·√(n−1) is asymptotically standard-normal under H0 (ρ=0). Computed
    here (rather than scipy) so the displayed p stays in sync with the live ρ
    when the CSV is edited. Small-n caveat is carried in the surrounding copy.
    """
    if not math.isfinite(rho) or n < 3:
        return float("nan")
    z = abs(rho) * math.sqrt(n - 1)
    # two-sided tail of the standard normal: erfc(|z|/√2)
    return float(math.erfc(z / math.sqrt(2.0)))


def render_ipo_strategy() -> None:
    """HK IPO 打新 backtest — STATIC cross-section snapshot.

    Structurally different from the 3 time-series strategies: reads ONLY the two
    frozen CSVs (ipo_picks / ipo_day1_intraday), never yfinance /
    compute_strategy_returns. Day-1 figures are frozen on the listing date.
    """
    picks = strat.load_ipo()
    if picks.empty:
        st.warning("No IPO picks — check data/external/ipo_picks.csv")
        return

    st.markdown(i18n.t("strategy.ipo.tab.intro"))

    # day1_ret is a DECIMAL (3.84 = +384%) → ×100 once here for the whole tab.
    picks = picks.copy()
    picks["ret_pct"] = picks["day1_ret"] * 100  # NaN for pending
    listed = picks[picks["status"] == "listed"].copy()
    pending = picks[picks["status"] != "listed"].copy()

    # --- Methodology expander (six-factor; NOT biotech clinical/FDA) ---
    with st.expander(i18n.t("strategy.ipo.method_expander")):
        st.markdown(i18n.t("strategy.ipo.method"))

    # Defensive: the CSV is hand-edited & frozen. If it ever holds only pending
    # rows, the KPI/scatter/intraday blocks (which assume ≥1 listed name) would
    # crash on idxmax/mean. Render the pending table only and bail early.
    if listed.empty:
        st.info(i18n.t("strategy.ipo.caveat"))
        _render_ipo_table(picks)
        st.caption(i18n.t("strategy.ipo.source"))
        return

    # --- KPI strip: 3 dead-simple single numbers (规模 + 上行 + 下行). The
    # "does a higher score actually do better?" question is answered by the
    # by-tier staircase TABLE below — not by cramming a contrast into a card
    # (contrast cards read as cryptic; user feedback 2026-06). ---
    n_total, n_listed, n_pending = len(picks), len(listed), len(pending)
    top_row = listed.loc[listed["ret_pct"].idxmax()]
    worst_row = listed.loc[listed["ret_pct"].idxmin()]

    def _ipo_kpi(label: str, value: str, sub: str, vcls: str = "") -> str:
        return (
            '<div class="cmsi-kpi">'
            f'<div class="cmsi-kpi-head"><span class="cmsi-kpi-label ipo">{label}</span></div>'
            f'<div class="cmsi-kpi-num {vcls}">{value}</div>'
            f'<div class="cmsi-kpi-foot ink">{sub}</div>'
            '</div>'
        )

    theme.kpi_strip([
        _ipo_kpi(i18n.t("strategy.ipo.kpi.sample"), str(n_total),
                 i18n.t("strategy.ipo.kpi.sample_delta", listed=n_listed, pending=n_pending)),
        _ipo_kpi(i18n.t("strategy.ipo.kpi.max"), f"{top_row['ret_pct']:+.0f}%",
                 i18n.t("strategy.ipo.kpi.max_delta", name=str(top_row["name_cn"])),
                 vcls="up-deep"),
        _ipo_kpi(i18n.t("strategy.ipo.kpi.worst"), f"{worst_row['ret_pct']:+.1f}%",
                 i18n.t("strategy.ipo.kpi.worst_delta", name=str(worst_row["name_cn"]))),
    ])

    # --- By-tier staircase: does a higher 申购档 actually perform better? Read it
    # top-to-bottom. The data shows the model nails the EXTREMES (重点+ best / 不申购
    # broke) but the middle tiers barely separate — honest, no clever single metric. ---
    theme.section_header(i18n.t("strategy.ipo.tier.title"))
    prefer_cn = i18n.get_lang() == "zh"
    c_n = i18n.t("strategy.ipo.tier.col.n")
    c_med = i18n.t("strategy.ipo.tier.col.med")
    c_win = i18n.t("strategy.ipo.tier.col.win")
    c_brk = i18n.t("strategy.ipo.tier.col.brk")
    _trows: dict[str, dict] = {}
    for _t in ["重点申购+", "重点申购", "推荐申购", "谨慎申购", "不申购"]:
        g = listed[listed["tier"] == _t]
        if g.empty:
            continue
        _up = int((g["ret_pct"] > 0).sum())
        _trows[_t if prefer_cn else i18n.ipo_tier(_t)] = {
            c_n: str(len(g)),
            c_med: f"{g['ret_pct'].median():+.0f}%",
            c_win: f"{_up}/{len(g)}",
            c_brk: str(int((g["ret_pct"] < 0).sum())),
        }
    if _trows:
        ui.render_html_table(
            pd.DataFrame.from_dict(_trows, orient="index"),
            text_cols=[c_n, c_med, c_win, c_brk], column_help={},
            index_label=i18n.t("strategy.ipo.tier.col.tier"), height=260,
        )
    st.caption(i18n.t("strategy.ipo.tier.note"))

    # --- Listing-day intraday small-multiples (open bar = 100, post-open path) ---
    theme.section_header(i18n.t("strategy.ipo.intraday.title"))
    intra = strat.load_ipo_intraday()
    if not intra.empty:
        # order by score desc so high-tier shapes read first
        order = listed.sort_values("score", ascending=False)
        paths = []
        for _, r in order.iterrows():
            code = str(r["code"])
            g = intra[intra["code"] == code].sort_values("time")
            g = g[g["close"].notna()]
            if g.empty:
                continue
            closes = g["close"].astype(float)
            last = float(closes.iloc[-1])
            if last == 0:
                continue
            d1 = float(r["day1_ret"])  # decimal, e.g. 3.84 = +384%
            # Plot as "% vs 发行价" at each 5-min bar. offer = last/(1+d1), so the
            # path terminates EXACTLY at the labelled day-1 return (d1*100) — fixes
            # the title/line mismatch from the old open-bar=100 normalisation.
            pct = (closes * (1.0 + d1) / last - 1.0) * 100.0
            up = bool(d1 >= 0)  # colour by FULL day-1 sign (= mini-title sign)
            hover = [
                i18n.t("strategy.ipo.intraday.hover",
                       time=t.strftime("%H:%M"), path=float(v))
                for t, v in zip(g["time"], pct)
            ]
            paths.append({
                "title": i18n.t("strategy.ipo.intraday.mini_title",
                                name=str(r["name_cn"]), ret=float(r["ret_pct"])),
                "y": pct.tolist(), "up": up, "hover": hover,
            })
        if paths:
            fig_intra = charts.ipo_intraday_facets(
                paths, ncols=4,
                title=i18n.t("strategy.ipo.intraday.title"),
                use_hover=True,
            )
            st.plotly_chart(fig_intra, width="stretch", theme=None)
    st.caption(i18n.t("strategy.ipo.intraday.caption"))

    # --- Dual leaderboard (by score / by day-1 return); pending row kept ---
    _render_ipo_table(picks)

    # --- Caveat + source ---
    st.info(i18n.t("strategy.ipo.caveat"))
    st.caption(i18n.t("strategy.ipo.source"))


def _render_ipo_table(picks: pd.DataFrame) -> None:
    """Dual leaderboard table (sort by score / by day-1 return).

    pending rows are kept (day-1 reads 待上市/Pending) but are NOT given a
    numeric rank — only listed names are ranked; pending shows "—" for rank.
    `picks` must already carry the ×100 `ret_pct` column.
    """
    sort_opts = [i18n.t("strategy.ipo.rank.by_score"),
                 i18n.t("strategy.ipo.rank.by_ret")]
    choice = st.segmented_control(
        i18n.t("strategy.ipo.rank.toggle"), sort_opts, default=sort_opts[0],
        key="ipo_rank_sort",
    ) or sort_opts[0]
    by_ret = (choice == sort_opts[1])

    # Build display frame. pending kept in the table; day-1 shows 待上市/Pending.
    tbl = picks.copy()
    if by_ret:
        # listed sorted by ret desc; pending pinned to bottom
        listed_sorted = tbl[tbl["status"] == "listed"].sort_values(
            "ret_pct", ascending=False)
        pend_sorted = tbl[tbl["status"] != "listed"]
        tbl = pd.concat([listed_sorted, pend_sorted])
    else:
        tbl = tbl.sort_values("score", ascending=False)
    tbl = tbl.reset_index(drop=True)
    # Rank only listed names; pending isn't ranked (it hasn't traded yet) → "—".
    is_listed = (tbl["status"] == "listed").to_numpy()
    ranks: list[str] = []
    _r = 0
    for listed_flag in is_listed:
        if listed_flag:
            _r += 1
            ranks.append(str(_r))
        else:
            ranks.append("—")
    tbl.insert(0, "rank", ranks)

    # day1 column: numeric pct for listed, text "待上市(date)" for pending.
    # render_html_table needs one kind per column → use a text column with the
    # signed-% string we format ourselves (keeps teal/red via inline span? no —
    # ui colors pct_cols only). Keep day-1 as a pct col for listed; pending uses
    # NaN → "—". The pending status is conveyed in a separate 状态 note column.
    disp = pd.DataFrame({
        i18n.t("strategy.ipo.col.code"): tbl["code"].astype(str),
        i18n.t("strategy.ipo.col.name"): tbl["name_cn"].astype(str),
        i18n.t("strategy.ipo.col.score"): tbl["score"].astype(float),
        i18n.t("strategy.ipo.col.tier"): [i18n.ipo_tier(str(x)) for x in tbl["tier"]],
        i18n.t("strategy.ipo.col.sub_sector"): tbl["sub_sector"].astype(str),
        i18n.t("strategy.ipo.col.day1_ret"): tbl["ret_pct"].to_numpy(),
        i18n.t("strategy.ipo.col.source"): tbl["source"].astype(str),
    })
    disp.index = tbl["rank"].to_numpy()
    disp.index.name = i18n.t("strategy.ipo.col.rank")

    # Pending rows: replace day-1 cell (NaN) so it reads 待上市(date), not "—".
    name_lbl = i18n.t("strategy.ipo.col.name")
    day1_lbl = i18n.t("strategy.ipo.col.day1_ret")
    for i, (_, r) in enumerate(tbl.iterrows()):
        if r["status"] != "listed":
            disp.iloc[i, disp.columns.get_loc(name_lbl)] = (
                f"{r['name_cn']} · "
                + i18n.t("strategy.ipo.rank.pending", date=str(r["list_date"]))
            )

    ui.render_html_table(
        disp,
        pct_cols=[day1_lbl],
        text_cols=[name_lbl,
                   i18n.t("strategy.ipo.col.tier"),
                   i18n.t("strategy.ipo.col.sub_sector"),
                   i18n.t("strategy.ipo.col.source")],
        extra_formats={i18n.t("strategy.ipo.col.score"): "%.2f"},
        right_text_cols=[i18n.t("strategy.ipo.col.code")],
        index_label=i18n.t("strategy.ipo.col.rank"),
        height=720,
    )


# --- Onboarding expander (i18n) ---
with st.expander(i18n.t("strategy.onboarding.title")):
    st.markdown(i18n.t("strategy.onboarding.body"))

# --- Tabs: 3 time-series strategies + 1 independent static IPO backtest ---
# Strategies with "version_of" render INSIDE their group's tab (version toggle),
# not as their own tab — hk_hd_v2 lives in the hk_hd tab.
_ts_ids = [k for k, c in strat.STRATEGIES.items() if not c.get("version_of")]
_tab_labels = [i18n.t(f"strategy.name.{sid}") for sid in _ts_ids]
_tab_labels.append(i18n.t("strategy.name.ipo"))
strategy_tabs = st.tabs(_tab_labels)
for tab, sid in zip(strategy_tabs[:-1], _ts_ids):
    with tab:
        if sid == "hk_hd":
            render_hd_versions()
        else:
            render_strategy(sid)
with strategy_tabs[-1]:
    render_ipo_strategy()

st.divider()
st.caption(i18n.t("strategy.method.equal_weight"))
st.caption(i18n.t("strategy.method.total_return"))
st.caption(i18n.t("strategy.method.source"))
