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

    # --- KPI strip (house cmsi-kpi cards — black sub-text + cream bg, replaces
    # the native st.metric whose label/delta render grey). 命中率口径 = 全 17
    # 只已上市的首日收涨率 (n_up/n_listed), 不再用推荐档 10/11 子样本. ---
    n_total, n_listed, n_pending = len(picks), len(listed), len(pending)
    med_ret = listed["ret_pct"].median()
    lo_ret = listed["ret_pct"].min()
    top_row = listed.loc[listed["ret_pct"].idxmax()]
    n_up = int((listed["ret_pct"] > 0).sum())          # 首日收涨数 (全 listed)
    win_rate = (n_up / n_listed * 100) if n_listed else float("nan")

    def _ipo_kpi(label: str, value: str, sub: str, vcls: str = "") -> str:
        return (
            '<div class="cmsi-kpi">'
            f'<div class="cmsi-kpi-head"><span class="cmsi-kpi-label ipo">{label}</span></div>'
            f'<div class="cmsi-kpi-num {vcls}">{value}</div>'
            f'<div class="cmsi-kpi-foot ink">{sub}</div>'
            '</div>'
        )

    # Value colours are semantic: 样本数 neutral ink; 最高首日 deep-teal (hero);
    # 中位首日 / 收涨率 teal (positive). Eyebrow labels carry the CMSI red accent.
    theme.kpi_strip([
        _ipo_kpi(i18n.t("strategy.ipo.kpi.sample"), str(n_total),
                 i18n.t("strategy.ipo.kpi.sample_delta", listed=n_listed, pending=n_pending)),
        _ipo_kpi(i18n.t("strategy.ipo.kpi.max"), f"{top_row['ret_pct']:+.0f}%",
                 i18n.t("strategy.ipo.kpi.max_delta", name=str(top_row["name_cn"])),
                 vcls="up-deep"),
        _ipo_kpi(i18n.t("strategy.ipo.kpi.med"), f"{med_ret:+.1f}%",
                 i18n.t("strategy.ipo.kpi.med_delta", lo=lo_ret, hi=top_row["ret_pct"]), vcls="up"),
        _ipo_kpi(i18n.t("strategy.ipo.kpi.hitrate"), f"{win_rate:.1f}%",
                 i18n.t("strategy.ipo.kpi.hitrate_delta", up=n_up, n=n_listed), vcls="up"),
    ])

    # KPI note (4-way review): surface the strategy-actionable cut (≥6.0 推荐档)
    # alongside the full-sample win-rate, and flag the right-tail mean distortion.
    rec = listed[listed["score"] >= 6.0]
    rec_up, rec_n = int((rec["ret_pct"] > 0).sum()), len(rec)
    st.caption(i18n.t("strategy.ipo.kpi.note",
                      rec_up=rec_up, rec_n=rec_n, up=n_up, n=n_listed,
                      median=med_ret))

    # --- Score × day-1 scatter (core trend; honest Spearman ρ annotation) ---
    theme.section_header(i18n.t("strategy.ipo.scatter.title", n=n_listed))
    rho = _spearman_rho(listed["score"], listed["ret_pct"])
    pval = _spearman_pval(rho, n_listed)
    p_str = f"{pval:.2f}" if math.isfinite(pval) else "n/a"
    rho_text = i18n.t("strategy.ipo.scatter.rho", rho=rho, p=p_str)

    def _hover(r) -> str:
        return i18n.t("strategy.ipo.scatter.hover",
                      name=str(r["name"]), code=str(r["code"]),
                      score=float(r["score"]), ret=float(r["ret_pct"]),
                      tier=i18n.ipo_tier(str(r["tier"])))

    sc = listed.rename(columns={"name_cn": "name"})
    fig_sc = charts.ipo_score_scatter(
        sc, score_col="score", ret_col="ret_pct", tier_col="tier",
        name_col="name", code_col="code", rho_text=rho_text,
        title=i18n.t("strategy.ipo.scatter.title", n=n_listed),
        x_label=i18n.t("strategy.ipo.scatter.x"),
        y_label=i18n.t("strategy.ipo.scatter.y"),
        trend_label=i18n.t("strategy.ipo.scatter.trend"),
        tier_label_fn=lambda tt: i18n.ipo_tier(str(tt)),
        hover_fn=_hover,
    )
    st.plotly_chart(fig_sc, width="stretch", theme=None)
    st.caption(i18n.t("strategy.ipo.scatter.caption"))

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
_ts_ids = list(strat.STRATEGIES.keys())
_tab_labels = [i18n.t(f"strategy.name.{sid}") for sid in _ts_ids]
_tab_labels.append(i18n.t("strategy.name.ipo"))
strategy_tabs = st.tabs(_tab_labels)
for tab, sid in zip(strategy_tabs[:-1], _ts_ids):
    with tab:
        render_strategy(sid)
with strategy_tabs[-1]:
    render_ipo_strategy()

st.divider()
st.caption(i18n.t("strategy.method.equal_weight"))
st.caption(i18n.t("strategy.method.total_return"))
st.caption(i18n.t("strategy.method.source"))
