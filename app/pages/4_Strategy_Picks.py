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
import streamlit as st

from lib import db  # noqa: F401  (kept for parity with other pages / future use)
from lib import format as fmt
from lib import strategy as strat
from lib import ui
from lib import theme
from lib import i18n
from lib import strategy_hero
from lib import strategy_banner as sb
from lib import ipo_stage

st.set_page_config(
    page_title="Strategy Picks · invest-dashboard",
    page_icon="🧬",
    layout="wide",
)

# Language: seed once + render the top-bar switch BEFORE any t() call so the
# whole page renders in one language per run (cccg ship-gate #3).
i18n.init_lang()
# [08] 语言切换:banner 的 中/EN 描边分段 = ?lang= 真链接(替代顶部实心红钮,不留两个语言钮)。
_qp_lang = st.query_params.get("lang")
if _qp_lang in ("zh", "en") and _qp_lang != st.session_state.get("lang"):
    st.session_state["lang"] = _qp_lang
    st.rerun()

# Sidebar global search + chart settings
with st.sidebar:
    ui.sidebar_search(key_prefix="strategy")
    # (Chart-settings toggles removed — the Tearsheet Hero replaced the Plotly chart
    #  and its show-individual / show-rebalanced controls.)

# ── Strategy-banner overview cards (computed eagerly at page top; cached) ──────
def _overview_curve_card(strat_id: str) -> dict | None:
    """One overview card (mini sparkline + cum/α) for a curve strategy. Same compute
    path as render_strategy (@st.cache_data, so the per-tab call hits cache). None if
    no data / no benchmark overlap (no fabrication)."""
    cfg = strat.STRATEGIES.get(strat_id)
    if not cfg:
        return None
    picks = cfg["loader"]()
    if picks.empty:
        return None
    pick_date, bench_sym = cfg["pick_date"], cfg["benchmark"]
    top_n = min(20, len(picks))
    pr = picks.sort_values("rank") if "rank" in picks.columns else picks
    top_syms = pr.head(top_n)["yf_sym"].dropna().tolist()
    wc = cfg.get("weight_col")
    cash_pct = float(cfg.get("cash_pct", 0.0))
    weights = None
    if wc and wc in picks.columns:
        weights = picks.set_index("yf_sym")[wc].astype(float) / 100.0
    yf_syms = tuple(picks["yf_sym"].dropna().unique().tolist())
    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=55)).date().isoformat()
    closes = strat.fetch_picks_closes(yf_syms + (bench_sym,), start=earliest,
                                      _ovr_mtime=strat._delisted_mtime())
    if closes.empty or bench_sym not in closes.columns:
        return None
    bench_close = closes[bench_sym]
    normed, portfolio, _, _ = strat.compute_strategy_returns(
        closes.drop(columns=[bench_sym], errors="ignore"), pick_date,
        portfolio_syms=top_syms, weights=weights, cash_pct=cash_pct)
    if portfolio.empty:
        return None
    sub = bench_close[bench_close.index >= pd.Timestamp(pick_date)].dropna()
    if sub.empty:
        return None
    bench_norm = (sub / sub.iloc[0]) * 100
    b_al = (bench_norm.reindex(bench_norm.index.union(portfolio.index))
            .ffill().reindex(portfolio.index).bfill())
    if not pd.notna(b_al.iloc[-1]):
        return None

    def _ds(series, n=44):
        vals = series.values
        if len(vals) <= n:
            return [round(float(v), 2) for v in vals]
        idx = np.linspace(0, len(vals) - 1, n).round().astype(int)
        return [round(float(vals[i]), 2) for i in idx]

    cum = float(portfolio.iloc[-1] - 100)
    bret = float(b_al.iloc[-1] - 100)
    return {
        "name": i18n.t(f"strategy.name.{strat_id}"),
        "bench_code": bench_sym, "pick_date": str(pick_date), "n_picks": top_n,
        "cum_ret": cum, "bench_ret": bret, "alpha": cum - bret,
        "wins": int((normed.iloc[-1] > 100).sum()), "total": int(normed.shape[1]),
        "hold_days": (pd.Timestamp.now().normalize() - pd.Timestamp(pick_date)).days,
        "curve": (_ds(portfolio), _ds(b_al)),
        "win_list": (normed.iloc[-1] > 100).tolist(),
        "_as_of": portfolio.index[-1].date().isoformat(),
    }


def _overview_ipo_card() -> dict | None:
    """IPO overview card from load_ipo — REAL day-1 returns (the demo's +12.4%/+384%
    were illustrative mock; this shows the actual median/hi/lo)."""
    df = strat.load_ipo()
    if df.empty:
        return None
    d1 = pd.to_numeric(df[df["status"] == "listed"]["day1_ret"], errors="coerce").dropna()
    if d1.empty or float(d1.max()) <= 0:   # bar widths divide by hi; guard non-positive
        return None
    return {
        "kind": "ipo", "name": i18n.t("strategy.name.ipo"), "tag": "六因子 v6.7",
        "n": len(df), "listed": int((df["status"] == "listed").sum()),
        "median": float(d1.median()), "hi": float(d1.max()), "lo": float(d1.min()),
    }


# wave-2: radial wash for glass card backdrops (BANR1)
theme.page_radial_wash(1240)

# ── Opening banner: LIVE title + 3-strategy overview strip + dual-track ────────
_ov_cards = [c for c in (_overview_curve_card("v5_biotech"),
                         _overview_curve_card("hk_hd"),
                         _overview_ipo_card()) if c]
sb.live_title(i18n.t("strategy.page.title"),
              as_of=next((c.get("_as_of") for c in _ov_cards if c.get("_as_of")), None),
              lang=("中" if i18n.get_lang() == "zh" else "EN"))
st.markdown(i18n.t("strategy.pitch"))
if _ov_cards:
    sb.overview_strip(_ov_cards)


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
    # (Header KPI strip removed per user — the Tearsheet Hero's bottom KPI row carries
    #  选股日 / 持仓数 / 持有天数 / 基准 + 胜率 / MDD / 夏普.)

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

    # --- Tearsheet Hero (showpiece headline; consumes the precomputed curves) ---
    # mdd/sharpe/win computed here (portfolio_math has no risk metrics). Bench curve
    # aligned via UNION index then ffill (a plain reindex(portfolio.index) would DROP
    # bench values on bench-only trading days → cross-market benchmarks misalign).
    # Gated on ≥10 days history + a real (non-degenerate) sharpe + a non-NaN bench
    # tail, so we never display a fabricated 0.0 sharpe / 0 win count (audit MEDIUM
    # B1/B2); below the gate the summary strip + chart below still render.
    if (not portfolio.empty and not bench_norm.empty
            and not normed.empty and len(portfolio) >= 10):
        _b_aligned = (bench_norm.reindex(bench_norm.index.union(portfolio.index))
                      .ffill().reindex(portfolio.index).bfill())
        _rets = portfolio.pct_change().dropna()
        if pd.notna(_b_aligned.iloc[-1]) and len(_rets) > 1 and _rets.std() > 0:
            _cum = float(portfolio.iloc[-1] - 100.0)
            _bret = float(_b_aligned.iloc[-1] - 100.0)
            strategy_hero.render(
                strat_name=disp_name,
                strat_dates=[d.date().isoformat() for d in portfolio.index],
                strat_curve=portfolio.values,
                bench_name=bench_name, bench_curve=_b_aligned.values,
                cum_ret=_cum, bench_ret=_bret, alpha_pp=_cum - _bret,
                pick_date=str(pick_date), n_hold=top_n, pool=n_total, days=days_since,
                wins=int((normed.iloc[-1] > 100.0).sum()), n_total=int(normed.shape[1]),
                mdd=float((portfolio / portfolio.cummax() - 1.0).min() * 100.0),
                sharpe=float(_rets.mean() / _rets.std()) * (252 ** 0.5),
                bench_code=bench_sym, bench_sub=bench_name,
                as_of=portfolio.index[-1].date().isoformat(),
                source=f"yfinance · 含息复权 total return · 基准 {bench_sym}",
            )

    # --- Summary metrics (KPI cards — house style, replaces st.metric) ---
    asof = (picks_closes.index[-1].date().isoformat()
            if not picks_closes.empty else "")
    if not portfolio.empty:
        # (Summary KPI strip 组合/基准/超额 removed per user — the Tearsheet Hero above
        #  already carries cum / benchmark / alpha + mdd / sharpe / win. Keep only the
        #  provenance captions: total-return basis + the v2 idle-cash note.)
        # 口径声明: auto_adjust=True → "Close" 是复权总回报(含息); 组合与基准同口径
        # (lib/strategy.py fetch_picks_closes)。高息股除息日股价机械下跌已被复权抵消。
        st.caption(i18n.t("strategy.metric.totalreturn_note"))
        if weights is not None:
            st.caption(i18n.t("strategy.hd.v2.cash_note", cash=cash_pct))

    # (The Plotly cumulative-return chart + the header/summary KPI strips were removed
    #  per user — the Tearsheet Hero above is now the single net-value curve and carries
    #  all the headline metrics.)

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

    # --- Overlay chart: v1 + v2 + benchmarks (ECharts, Hero-aligned) ---
    # Common date axis = union of all four series (so v2's later-start line begins
    # exactly at its inception via None gaps). v2 = CMSI red (the "current" book,
    # prominent like the Hero strategy line); v1 = teal; benchmarks muted dash/dot.
    _all_idx = pd.DatetimeIndex([])
    for _s in (bench_norm, bench2_norm, port_v1, port_v2):
        if not _s.empty:
            _all_idx = _all_idx.union(_s.index)
    _all_idx = _all_idx.sort_values()

    def _aligned(s):
        r = s.reindex(_all_idx)
        return [None if pd.isna(v) else round(float(v), 2) for v in r.values]

    _lines = []
    if not bench_norm.empty:
        _lines.append({"name": i18n.t("strategy.chart.line.benchmark",
                                      sym=bench_sym, name=cfg1["benchmark_name"]),
                       "values": _aligned(bench_norm), "color": theme.INK_3,
                       "dash": "dashed", "width": 1.5})
    if not bench2_norm.empty:
        _lines.append({"name": i18n.t("strategy.chart.line.benchmark",
                                      sym=bench2_sym, name=cfg1.get("benchmark2_name", "")),
                       "values": _aligned(bench2_norm), "color": "#4a6fa5",
                       "dash": "dotted", "width": 1.5})
    if not port_v1.empty:
        _lines.append({"name": i18n.t("strategy.hd.compare.v1_line"),
                       "values": _aligned(port_v1), "color": theme.UP,
                       "dash": "solid", "width": 1.8})
    if not port_v2.empty:
        _lines.append({"name": i18n.t("strategy.hd.compare.v2_line"),
                       "values": _aligned(port_v2), "color": theme.CMSI_RED,
                       "dash": "solid", "width": 2.4})

    if _lines and len(_all_idx):
        # marker = v2's actual first trading day (guarantees it matches a real x
        # category even if the nominal pick_date is a weekend/holiday).
        _marker = port_v2.index[0].date().isoformat() if not port_v2.empty else None
        strategy_hero.render_compare_chart(
            dates=[d.date().isoformat() for d in _all_idx], lines=_lines,
            marker_date=_marker, marker_label=i18n.t("strategy.hd.compare.rebal_label"),
            title=i18n.t("strategy.hd.compare.title"),
            source=f"yfinance · 含息复权 · 截至 {_all_idx[-1].date().isoformat()}",
        )
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
    """HK IPO 打新 1a — newspaper-precision reskin (wave-2).

    Delegates to ipo_stage.render() which emits one self-contained st.iframe.
    Data pipeline: strat.load_ipo() + strat.load_ipo_intraday() — unchanged.
    """
    picks    = strat.load_ipo()
    intraday = strat.load_ipo_intraday()
    prefer_cn = st.session_state.get("lang", "zh") != "en"
    as_of = picks["list_date"].dropna().max() if "list_date" in picks.columns else "2026-07-03"
    ipo_stage.render(picks, intraday, prefer_cn=prefer_cn, as_of=str(as_of))



# --- Dual-track guide cards (replaces the old 如何阅读 expander) ---
sb.dual_track(
    [
        ("01", "催化剂驱动",
         "围绕生物科技的临床读出、FDA / NMPA 审批节点、财报与公司治理事件,捕捉事件前后的"
         "价值重估。前三个标签页 = 自选股日起的<b>真实累计收益 vs 基准</b>。"),
        ("02", "新股打新多维评分",
         "以六因子模型(流通盘稀缺度、基石阵容、板块景气、认购倍数、估值、基本面)为港股新股"
         "打分分档,<b>量化首日申购胜率</b>。末标签页为静态截面后测。"),
    ],
    footer="两条线共用同一套<b>数据纪律</b>:数字标来源与时效、卖方一致预期与自有观点分离、"
           "结论可操作。后续将扩展至更多行业 domain。",
)

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
