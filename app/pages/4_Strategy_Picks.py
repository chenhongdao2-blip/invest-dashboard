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
import re

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
from lib import picks_table

st.set_page_config(
    page_title="Strategy Picks · invest-dashboard",
    page_icon="🧬",
    layout="wide",
)

# Language: seed once + render the top-bar switch BEFORE any t() call so the
# whole page renders in one language per run (cccg ship-gate #3).
i18n.init_lang()

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
    top_n = min(int(cfg.get("top_n", 20)), len(picks))
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
    """IPO overview card from load_ipo — day-1 returns as percentage points.

    day1_ret in CSV is a decimal (3.84 = +384%); ×100 applied here before
    computing median/hi/lo so banner _ipo_card renders the correct scale
    (e.g. +384.0%, not +3.8%).  The banner formats values with :.1f% only —
    no second ×100 transform on that side.
    """
    df = strat.load_ipo()
    if df.empty:
        return None
    d1 = (pd.to_numeric(df[df["status"] == "listed"]["day1_ret"], errors="coerce").dropna()
          * 100)  # decimal → pct-pts (3.84 → 384.0)
    if d1.empty or float(d1.max()) <= 0:   # bar widths divide by hi; guard non-positive
        return None
    return {
        "kind": "ipo", "name": i18n.t("strategy.name.ipo"), "tag": "六因子 v6.7",
        "n": len(df), "listed": int((df["status"] == "listed").sum()),
        "median": float(d1.median()), "hi": float(d1.max()), "lo": float(d1.min()),  # unit: pct-pts
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
# BANR4:dek 按设计包样式(14px/1.65/#4a4a4a/max-880),i18n 文案的 markdown 粗体转 <b> 墨色
_pitch_html = re.sub(
    r"\*\*(.+?)\*\*", r'<b style="color:#1a1a1a;">\1</b>', i18n.t("strategy.pitch")
).replace("\n\n", "<br><br>")
st.markdown(
    f'<p style="font-size:14px;line-height:1.65;color:#4a4a4a;max-width:880px;'
    f'margin:16px 0 0;">{_pitch_html}</p>',
    unsafe_allow_html=True,
)
if _ov_cards:
    sb.overview_strip(_ov_cards)


# ── Method-card config per strategy book ─────────────────────────────────────

_BIOTECH_DIMS = [
    {"name": "管线",   "pct": 40, "color": "#c8102e", "fg": "#fff1e5"},
    {"name": "催化事件", "pct": 25, "color": "#0d7680", "fg": "#fff1e5"},
    {"name": "并购",   "pct": 20, "color": "#1a1a1a", "fg": "#fff1e5"},
    {"name": "财务",   "pct": 10, "color": "#E0A458", "fg": "#1a1a1a"},
    {"name": "风险",   "pct":  5, "color": "#b8ab99", "fg": "#1a1a1a"},
]
_HD_DIMS = [
    {"name": "公司治理", "pct": 55, "color": "#c8102e", "fg": "#fff1e5"},
    {"name": "财务质量", "pct": 25, "color": "#0d7680", "fg": "#fff1e5"},
    {"name": "行业护城河", "pct": 20, "color": "#1a1a1a", "fg": "#fff1e5"},
]


def _build_method_cfg(strat_id: str, prefer_cn: bool) -> dict:
    """Return a picks_table.render_methodology() m-dict for the given strategy."""
    is_biotech = strat_id in ("v4_biotech", "v5_biotech", "v6_biotech")
    dims = _BIOTECH_DIMS if is_biotech else _HD_DIMS

    version_chip = {
        "v4_biotech": "v4 · 2026-04",
        "v5_biotech": "v5 · 2026-05",
        "v6_biotech": "v6 · 2026-07",
        "hk_hd":   "v1 · 2026-03",
        "hk_hd_v2": "v2 · 2026-06",
        "hk_hd_v3": "v3 · 2026-07",
    }.get(strat_id, strat_id)
    universe_chip = "US Biotech" if is_biotech else "HK High-Div"

    # Fetch methodology body text from i18n (existing keys, not new ones)
    method_key = {
        "v4_biotech": "strategy.v4.method",
        "v5_biotech": "strategy.v5.method",
        "v6_biotech": "strategy.v5.method",
        "hk_hd":    "strategy.hd.method",
        "hk_hd_v2": "strategy.hd.v2.method",
        "hk_hd_v3": "strategy.hd.v3.method",
    }.get(strat_id, "strategy.hd.method")
    raw_md = i18n.t(method_key)
    # Convert lightweight markdown to inline HTML (bold, newlines → <br>)
    import re as _re
    summary_html = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", raw_md)
    summary_html = summary_html.replace("\n\n", "<br><br>").replace("\n", "<br>")

    return {
        "tag":          version_chip,
        "chip":         universe_chip,
        "dims":         dims,
        "summary_html": summary_html,
    }


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

    # --- Methodology glass card (picks_table house design) ---
    _is_biotech = strat_id in ("v4_biotech", "v5_biotech", "v6_biotech")
    _prefer_cn = i18n.get_lang() == "zh"
    _method_cfg = _build_method_cfg(strat_id, _prefer_cn)
    with st.expander(i18n.t("strategy.method_expander"), expanded=True):
        _mdoc, _mh = picks_table.render_methodology(_method_cfg, prefer_cn=_prefer_cn)
        st.iframe(_mdoc, height=_mh)

    # --- Top-N selection (scoring model: portfolio = top 20 by score rank) ---
    n_total = len(picks)
    top_n = min(int(cfg.get("top_n", 20)), n_total)
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
    # Fetch from the earlier of (pick_date - 55 days) and Jan 1 of current year so
    # that YTD is computable for all strategy books regardless of pick_date.
    _jan1 = f"{pd.Timestamp.now().year}-01-01"
    _pre55 = (pd.Timestamp(pick_date) - pd.Timedelta(days=55)).date().isoformat()
    earliest = min(_jan1, _pre55)
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
                currency=cfg.get("currency"),
                initial_capital=cfg.get("initial_capital"),
                cap_label=i18n.t("strategy.hero.initial_capital"),
                nav_label=i18n.t("strategy.hero.current_nav"),
                gain_label=i18n.t("strategy.hero.nav_gain"),
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
        picks_closes[t].dropna().tail(20).tolist()
        if t in picks_closes.columns else []
        for t in perf.index
    ]
    perf.index = [fmt.fmt_ticker_bbg(t) for t in perf.index]

    # --- Build picks_table payload ---
    # Determine currency prefix per book
    _ccy = "$" if _is_biotech else "HK$"

    # perf.index is now BBG-formatted tickers (renamed above); build the reverse
    # map (bbg → yf_sym) BEFORE the loop so we can look up picks_closes columns.
    # Also build a forward map (yf_sym → bbg) for the tick field.
    _bbg_to_yf: dict[str, str] = {}
    for _orig_yf in picks["yf_sym"].dropna().unique():
        _b = fmt.fmt_ticker_bbg(str(_orig_yf))
        _bbg_to_yf[_b] = str(_orig_yf)

    # Compute YTD returns from picks_closes (which now fetches from Jan 1).
    # db.compute_returns handles the per-ticker YTD anchor correctly.
    import importlib as _il
    _db = _il.import_module("lib.db")
    _ytd_map: dict[str, float | None] = {}
    if not picks_closes.empty:
        _ret_df = _db.compute_returns(picks_closes)
        for _col in _ret_df.index:
            _v = _ret_df.loc[_col, "ytd_%"] if "ytd_%" in _ret_df.columns else float("nan")
            _ytd_map[str(_col)] = float(_v) if pd.notna(_v) else None

    def _pv(row: "pd.Series", col: str) -> "float | None":
        v = row.get(col, None)
        return float(v) if pd.notna(v) else None  # type: ignore[arg-type]

    _payload_rows: list[dict] = []
    for _bbg_sym, _row in perf.iterrows():
        _bbg_sym = str(_bbg_sym)
        # Resolve yf_sym for picks_closes column lookup
        _orig_yf = _bbg_to_yf.get(_bbg_sym, _bbg_sym)

        # name: from meta join; fallback to ticker
        _name = str(_row.get("name", _bbg_sym)) if pd.notna(_row.get("name", None)) else _bbg_sym
        # score: float or None
        _score_raw = _row.get("score", None)
        _score = float(_score_raw) if pd.notna(_score_raw) else None  # type: ignore[arg-type]
        # price
        _price_raw = _row.get("Last", None)
        _price = float(_price_raw) if pd.notna(_price_raw) else None  # type: ignore[arg-type]
        # spark: already computed as 20-day list of floats (or [])
        _spark = _row.get("spark", []) or []

        # since: for same-day books (e.g. v6 entered today), since==0.0 is
        # uninformative — fall back to the 1D return so the column shows real moves.
        _since_raw = _pv(_row, "Since %")
        if _since_raw == 0.0:
            _since_raw = _pv(_row, "1D %")

        # YTD: use compute_returns result keyed by yf_sym (picks_closes columns)
        _ytd = _ytd_map.get(_orig_yf)

        _payload_rows.append({
            "rank":  int(_row["rank"]) if "rank" in _row and pd.notna(_row["rank"]) else 0,
            "tick":  _bbg_sym,
            "name":  _name,
            "score": _score,
            "price": _price,
            "ccy":   _ccy,
            "spark": _spark,
            "d1":    _pv(_row, "1D %"),
            "d5":    _pv(_row, "5D %"),
            "m1":    _pv(_row, "30D %"),   # 30D as "1月" proxy
            "ytd":   _ytd,
            "since": _since_raw,
        })

    # Sort by rank
    _payload_rows.sort(key=lambda r: (r["rank"] == 0, r["rank"]))

    # i18n labels for holdings table (inline — new picks.tbl.* keys not yet in locales)
    _prefer_cn2 = i18n.get_lang() == "zh"
    if _prefer_cn2:
        _tbl_labels = {
            "col_rank":  "名次",
            "col_tick":  "代码",
            "col_name":  "名称",
            "col_score": "评分",
            "col_price": "现价",
            "col_d1":    "1日",
            "col_d5":    "5日",
            "col_m1":    "1月",
            "col_ytd":   "年初至今",
            "col_since": "建仓来",
            "col_spark": "走势",
            "nm_label":  "NM",
            "footnote":  "含息复权总回报（yfinance auto_adjust=True）· 建仓来=入选日至今 · 年初至今=当年首个交易日至今",
            "brand":     "CMSI",
        }
    else:
        _tbl_labels = {
            "col_rank":  "Rank",
            "col_tick":  "Ticker",
            "col_name":  "Name",
            "col_score": "Score",
            "col_price": "Price",
            "col_d1":    "1D",
            "col_d5":    "5D",
            "col_m1":    "1M",
            "col_ytd":   "YTD",
            "col_since": "Since",
            "col_spark": "Trend",
            "nm_label":  "NM",
            "footnote":  "Total return incl. dividends (yfinance auto_adjust=True) · Since = pick date to today · YTD = first trading day of current year to today",
            "brand":     "CMSI",
        }

    def _render_picks_table(rows: list[dict], height: int = 560) -> None:
        _doc, _h = picks_table.render_holdings(rows, _tbl_labels, height=height)
        st.iframe(_doc, height=_h)

    # Top-N holdings (the actual portfolio) shown by default; full ranked universe in expander.
    holdings_title_key = ("strategy.holdings.title_weighted" if weights is not None
                          else "strategy.holdings.title")
    st.markdown(f"##### {i18n.t(holdings_title_key)}")
    _render_picks_table(_payload_rows[:top_n], height=560)
    if asof:
        theme.provenance(i18n.t("common.provenance", src="yfinance", asof=asof))
    if len(_payload_rows) > top_n:
        with st.expander(i18n.t("strategy.holdings.all", n=len(_payload_rows)),
                         expanded=True):
            _render_picks_table(_payload_rows, height=620)


def render_hd_versions() -> None:
    """HK 高股息 tab = version group: v3 (current, default) / v2 (history) / v1
    (history, frozen curve keeps running) / 3-gen compare. One tab, four views —
    v1/v2 histories are never truncated; v3 is a NEW book from 2026-07-07 (三代演进)."""
    opts = [
        i18n.t("strategy.hd.version.v3"),
        i18n.t("strategy.hd.version.v2"),
        i18n.t("strategy.hd.version.v1"),
        i18n.t("strategy.hd.version.compare"),
    ]
    choice = st.segmented_control(
        i18n.t("strategy.hd.version.toggle"), opts, default=opts[0],
        key="hd_version",
    ) or opts[0]
    if choice == opts[1]:
        render_strategy("hk_hd_v2")
    elif choice == opts[2]:
        st.caption(i18n.t("strategy.hd.version.v1_note"))
        render_strategy("hk_hd")
    elif choice == opts[3]:
        render_hd_compare()
    else:
        render_strategy("hk_hd_v3")


def _chain_nav(
    curves: list[pd.Series], capital: float = 1_000_000.0
) -> tuple[pd.Series, list[str]]:
    """Chain per-version normalized curves (each rebased to 100 at its OWN inception)
    into ONE real account NAV that follows the rebalances.

    Semantics: capital is invested in the FIRST version at its inception; at each
    later version's first trading day the whole book is rolled into that version —
    the prior segment's terminal account value becomes the next segment's starting
    capital. So the account value on day t inside version k's holding window is:

        acct(t) = running_capital_k × (curve_k(t) / curve_k(start_k))

    Each version's segment runs [its inception, next version's inception) except the
    last, which runs to its final observation. Empty curves are skipped (biotech v6
    before its data lands), so the chain degrades to whatever versions exist.

    Returns (account_nav_series, boundary_iso_dates) where boundary dates are the
    handover days (each later version's first trading day) for rebalance markers.
    """
    live = [c for c in curves if c is not None and not c.empty]
    if not live:
        return pd.Series(dtype=float), []
    # order by first trading day (chronological); each already starts at 100.
    live = sorted(live, key=lambda s: s.index[0])
    starts = [s.index[0] for s in live]
    segments: list[pd.Series] = []
    boundaries: list[str] = []
    running = float(capital)
    for i, cur in enumerate(live):
        # this segment ends the day before the next version starts (exclusive), or
        # runs to the end for the last version.
        end = starts[i + 1] if i + 1 < len(live) else None
        seg = cur if end is None else cur[cur.index < end]
        if seg.empty:
            # a version fully superseded before it logged a trading day — skip but
            # still advance running capital using its (single) first point ratio.
            continue
        base = float(seg.iloc[0])           # = 100 by construction, but read it live
        acct = running * (seg / base)       # scale this version's shape onto the book
        segments.append(acct)
        running = float(acct.iloc[-1])       # terminal value → next segment's capital
        if i > 0:
            boundaries.append(starts[i].date().isoformat())
    if not segments:
        return pd.Series(dtype=float), []
    account = pd.concat(segments)
    account = account[~account.index.duplicated(keep="last")].sort_index()
    return account, boundaries


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
    v3 = strat.load_hd_v3()
    if v1.empty or v2.empty or v3.empty:
        st.warning("Need hd_picks.csv + hd_picks_v2.csv + hd_picks_v3.csv — check data/external/")
        return
    cfg1 = strat.STRATEGIES["hk_hd"]
    cfg2 = strat.STRATEGIES["hk_hd_v2"]
    cfg3 = strat.STRATEGIES["hk_hd_v3"]
    bench_sym = cfg1["benchmark"]
    bench2_sym = cfg1.get("benchmark2")

    v1_book = v1.sort_values("rank").head(20)
    v2_book = v2.sort_values("rank")
    v3_book = v3.sort_values("rank")
    v1_syms = v1_book["yf_sym"].dropna().tolist()
    v2_syms = v2_book["yf_sym"].dropna().tolist()
    v3_syms = v3_book["yf_sym"].dropna().tolist()

    # --- Prices: one fetch covering all three books + benchmarks, from v1 inception ---
    all_syms = tuple(dict.fromkeys(
        v1_syms + v2_syms + v3_syms + [s for s in (bench_sym, bench2_sym) if s]))
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
    # v3 curve: published weights + 12% cash from 2026-07-07 (current book)
    w3 = v3_book.set_index("yf_sym")[cfg3["weight_col"]].astype(float) / 100.0
    _, port_v3, _, _ = strat.compute_strategy_returns(
        closes[[c for c in v3_syms if c in closes.columns]],
        cfg3["pick_date"], portfolio_syms=v3_syms,
        weights=w3, cash_pct=cfg3["cash_pct"],
    )
    def _cmp_norm(sym: str | None) -> pd.Series:
        if not sym or sym not in closes.columns:
            return pd.Series(dtype=float)
        b = closes[sym].dropna()
        b = b[b.index >= pd.Timestamp(cfg1["pick_date"])]
        return (b / b.iloc[0]) * 100 if not b.empty else pd.Series(dtype=float)

    bench_norm = _cmp_norm(bench_sym)
    bench2_norm = _cmp_norm(bench2_sym)

    # ── Assemble the FT-cream 三代对比 tearsheet (single self-contained iframe) ──
    ccy = cfg1.get("currency", "HKD")
    capital = float(cfg1.get("initial_capital", 1_000_000))

    def _pct(series) -> str:
        return f"{series.iloc[-1] - 100:+.2f}%" if not series.empty else "—"

    # 4 KPI cards — v1 teal, v2 amber, v3 red (current), primary bench ink.
    cards = [
        {"label": i18n.t("strategy.hd.compare.metric.v1"),
         "sub": f"等权建仓 · {cfg1['pick_date']}", "value": _pct(port_v1), "color": theme.UP},
        {"label": i18n.t("strategy.hd.compare.metric.v2"),
         "sub": f"评分定权 · {cfg2['pick_date']}", "value": _pct(port_v2), "color": "#E0A458"},
        {"label": i18n.t("strategy.hd.compare.metric.v3"),
         "sub": f"Wind 单源 · {cfg3['pick_date']}", "value": _pct(port_v3), "color": theme.CMSI_RED},
        {"label": i18n.t("strategy.metric.benchmark_ret", sym=bench_sym),
         "sub": f"买入持有 · 锚定 {cfg1['pick_date']}", "value": _pct(bench_norm), "color": theme.INK},
    ]

    # Chained account (v1→v2→v3 rebalances) — real book, prior terminal seeds next.
    account, boundaries = _chain_nav([port_v1, port_v2, port_v3], capital)
    cur_nav = float(account.iloc[-1]) if not account.empty else capital
    cum = (cur_nav / capital - 1.0) * 100.0
    bench_cum = float(bench_norm.iloc[-1] - 100.0) if not bench_norm.empty else 0.0
    alpha = cum - bench_cum
    gain = cur_nav - capital

    _idx = pd.DatetimeIndex([])
    for _s in (bench_norm, bench2_norm, port_v1, port_v2, port_v3, account):
        if not _s.empty:
            _idx = _idx.union(_s.index)
    _idx = _idx.sort_values()
    dates = [d.date().isoformat() for d in _idx]

    def _al(s):
        if s is None or s.empty:
            return [None] * len(_idx)
        r = s.reindex(_idx)
        return [None if pd.isna(v) else round(float(v), 2) for v in r.values]

    acct_norm = account / float(account.iloc[0]) * 100.0 if not account.empty else account

    # independent overlay lines (v1 teal / v2 amber / v3 red / benchmarks muted)
    cmp_lines = []
    if not bench_norm.empty:
        cmp_lines.append({"name": i18n.t("strategy.chart.line.benchmark",
                                         sym=bench_sym, name=cfg1["benchmark_name"]),
                          "values": _al(bench_norm), "color": theme.INK_3,
                          "dash": "dashed", "width": 1.5})
    if not bench2_norm.empty:
        cmp_lines.append({"name": i18n.t("strategy.chart.line.benchmark",
                                         sym=bench2_sym, name=cfg1.get("benchmark2_name", "")),
                          "values": _al(bench2_norm), "color": "#4a6fa5",
                          "dash": "dotted", "width": 1.5})
    if not port_v1.empty:
        cmp_lines.append({"name": i18n.t("strategy.hd.compare.v1_line"),
                          "values": _al(port_v1), "color": theme.UP,
                          "dash": "solid", "width": 1.8})
    if not port_v2.empty:
        cmp_lines.append({"name": i18n.t("strategy.hd.compare.v2_line"),
                          "values": _al(port_v2), "color": "#E0A458",
                          "dash": "solid", "width": 1.8})
    if not port_v3.empty:
        cmp_lines.append({"name": i18n.t("strategy.hd.compare.v3_line"),
                          "values": _al(port_v3), "color": theme.CMSI_RED,
                          "dash": "solid", "width": 2.4})

    _reb_lab = i18n.t("strategy.chain.rebal_marker")
    chain_markers = [{"date": b, "label": f"{_reb_lab} → v{2 + i}"}
                     for i, b in enumerate(boundaries)]

    n_v1, n_v2, n_v3 = len(v1_book), len(v2_book), len(v3_book)
    days_held = (_idx[-1] - _idx[0]).days if len(_idx) else 0
    kpi_tiles = [
        {"label": "建仓日", "value": cfg1["pick_date"], "sub": "等权建仓 v1"},
        {"label": "已执行换仓", "value": f"{len(boundaries)} 次",
         "sub": (f"{boundaries[-1]} → v3" if boundaries else "—")},
        {"label": "当前版本", "value": "v3 · 07-07",
         "sub": "Wind 单源评分定权", "color": theme.CMSI_RED},
        {"label": "持仓数", "value": f"{n_v1} → {n_v2} → {n_v3}", "sub": "v1→v2→v3"},
        {"label": "持有天数", "value": f"{days_held} 天",
         "sub": f"{cfg1['pick_date']} → {(_idx[-1].date().isoformat() if len(_idx) else '')}"},
        {"label": "基准", "value": bench_sym, "sub": cfg1["benchmark_name"]},
    ]

    as_of = _idx[-1].date().isoformat() if len(_idx) else cfg1["pick_date"]
    strategy_hero.render_gen_compare(
        dates=dates, chain_curve=_al(acct_norm), bench_curve=_al(bench_norm),
        cmp_lines=cmp_lines, chain_markers=chain_markers,
        nav_str=f"{ccy} {cur_nav:,.0f}",
        cum_str=f"{'+' if cum >= 0 else ''}{cum:.2f}%",
        alpha_str=f"{'+' if alpha >= 0 else ''}{alpha:.2f}pp",
        gain_str=f"{'+' if gain >= 0 else '-'}{ccy} {abs(gain):,.0f}",
        bench_cum_str=f"{bench_cum:+.2f}%",
        cards=cards, kpi_tiles=kpi_tiles,
        chain_start=cfg1["pick_date"], currency=ccy, capital_str=f"{capital:,.0f}",
        v6_pending="",
        method_note=i18n.t("strategy.chain.note", cur=ccy, cap=f"{capital:,.0f}"),
        indep_title=i18n.t("strategy.chain.independent_section_title"),
        indep_badge="",
        indep_note=i18n.t("strategy.hd.compare.note"),
        chain_bench_name=i18n.t("strategy.chart.line.benchmark",
                                sym=bench_sym, name=cfg1["benchmark_name"]),
        chain_acct_name=i18n.t("strategy.chain.acct_line"),
        source=f"yfinance · 含息复权 · 截至 {as_of} · 真实累计收益,非回测美化",
    )

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


def render_biotech_versions() -> None:
    """US biotech tab = version group: v6 (current, default) / v5 (history) / v4
    (history, frozen curve keeps running) / 3-gen compare. One tab, four views —
    mirrors render_hd_versions. v4/v5 are equal-weight books (no weight_col); v6 is
    a NEW book from 2026-07-08 whose picks data is added separately (graceful
    placeholder until v6_picks.csv lands)."""
    opts = [
        i18n.t("strategy.biotech.version.v6"),
        i18n.t("strategy.biotech.version.v5"),
        i18n.t("strategy.biotech.version.v4"),
        i18n.t("strategy.biotech.version.compare"),
    ]
    choice = st.segmented_control(
        i18n.t("strategy.biotech.version.toggle"), opts, default=opts[0],
        key="biotech_version",
    ) or opts[0]
    if choice == opts[1]:
        render_strategy("v5_biotech")
    elif choice == opts[2]:
        st.caption(i18n.t("strategy.biotech.version.v4_note"))
        render_strategy("v4_biotech")
    elif choice == opts[3]:
        render_biotech_compare()
    else:
        # v6 current — graceful placeholder until its picks data is inserted.
        if strat.load_v6().empty:
            st.info(i18n.t("strategy.biotech.version.v6_pending"))
        else:
            render_strategy("v6_biotech")


def render_biotech_compare() -> None:
    """v4 / v5 / v6 overlay — each curve indexed to 100 at its OWN inception
    (independent books, NOT a chained NAV); benchmark (XBI) anchored at v4
    inception. Mirrors render_hd_compare but equal-weight + single benchmark, and
    tolerates v6 being empty (drops that line until its data lands)."""
    v4 = strat.load_v4()
    v5 = strat.load_v5()
    v6 = strat.load_v6()
    if v4.empty or v5.empty:
        st.warning("Need v4_picks.csv + v5_picks.csv — check data/external/")
        return
    cfg4 = strat.STRATEGIES["v4_biotech"]
    cfg5 = strat.STRATEGIES["v5_biotech"]
    cfg6 = strat.STRATEGIES["v6_biotech"]
    bench_sym = cfg4["benchmark"]

    def _book_syms(df: pd.DataFrame) -> list[str]:
        d = df.sort_values("rank") if "rank" in df.columns else df
        return d.head(20)["yf_sym"].dropna().tolist()

    v4_syms = _book_syms(v4)
    v5_syms = _book_syms(v5)
    v6_syms = _book_syms(v6) if not v6.empty else []

    all_syms = tuple(dict.fromkeys(v4_syms + v5_syms + v6_syms + [bench_sym]))
    earliest = (pd.Timestamp(cfg4["pick_date"]) - pd.Timedelta(days=10)).date().isoformat()
    closes = strat.fetch_picks_closes(all_syms, start=earliest,
                                      _ovr_mtime=strat._delisted_mtime())
    if closes.empty:
        st.error("Live price fetch failed. Check network/yfinance.")
        return

    def _curve(syms: list[str], pick_date: str) -> pd.Series:
        cols = [c for c in syms if c in closes.columns]
        if not cols:
            return pd.Series(dtype=float)
        _, port, _, _ = strat.compute_strategy_returns(
            closes[cols], pick_date, portfolio_syms=syms)
        return port

    port_v4 = _curve(v4_syms, cfg4["pick_date"])
    port_v5 = _curve(v5_syms, cfg5["pick_date"])
    port_v6 = _curve(v6_syms, cfg6["pick_date"]) if v6_syms else pd.Series(dtype=float)

    def _cmp_norm(sym: str | None) -> pd.Series:
        if not sym or sym not in closes.columns:
            return pd.Series(dtype=float)
        b = closes[sym].dropna()
        b = b[b.index >= pd.Timestamp(cfg4["pick_date"])]
        return (b / b.iloc[0]) * 100 if not b.empty else pd.Series(dtype=float)

    bench_norm = _cmp_norm(bench_sym)

    # ── Assemble the FT-cream 三代对比 tearsheet (single self-contained iframe) ──
    ccy = cfg4.get("currency", "USD")
    capital = float(cfg4.get("initial_capital", 1_000_000))

    def _pct(series) -> str:
        return f"{series.iloc[-1] - 100:+.2f}%" if not series.empty else "—"

    # 4 KPI cards — v4/v5 teal, v6 red (待录入 until data lands), XBI ink.
    cards = [
        {"label": i18n.t("strategy.biotech.compare.metric.v4"),
         "sub": "春季建仓 · 2026-04-22", "value": _pct(port_v4), "color": theme.UP},
        {"label": i18n.t("strategy.biotech.compare.metric.v5"),
         "sub": "夏季调仓 · 2026-05-15", "value": _pct(port_v5), "color": "#E0A458"},
        {"label": i18n.t("strategy.biotech.compare.metric.v6"),
         "sub": "7月调仓 · 2026-07-08",
         "value": _pct(port_v6), "color": theme.CMSI_RED,
         "pending": port_v6.empty},
        {"label": i18n.t("strategy.metric.benchmark_ret", sym=bench_sym),
         "sub": "买入持有 · 锚定 v4 建仓日", "value": _pct(bench_norm), "color": theme.INK},
    ]

    # Chained account (v4→v5→v6 rebalances) — real book, prior terminal seeds next.
    account, boundaries = _chain_nav([port_v4, port_v5, port_v6], capital)
    cur_nav = float(account.iloc[-1]) if not account.empty else capital
    cum = (cur_nav / capital - 1.0) * 100.0
    bench_cum = float(bench_norm.iloc[-1] - 100.0) if not bench_norm.empty else 0.0
    alpha = cum - bench_cum
    gain = cur_nav - capital

    # Common x-axis across chained + all independent curves (so a late-start line
    # begins exactly at its inception via None gaps).
    _idx = pd.DatetimeIndex([])
    for _s in (bench_norm, port_v4, port_v5, port_v6, account):
        if not _s.empty:
            _idx = _idx.union(_s.index)
    _idx = _idx.sort_values()
    dates = [d.date().isoformat() for d in _idx]

    def _al(s):
        if s is None or s.empty:
            return [None] * len(_idx)
        r = s.reindex(_idx)
        return [None if pd.isna(v) else round(float(v), 2) for v in r.values]

    acct_norm = account / float(account.iloc[0]) * 100.0 if not account.empty else account

    # independent overlay lines (v4 teal / v5 amber / v6 red / XBI grey-dash)
    cmp_lines = []
    if not bench_norm.empty:
        cmp_lines.append({"name": i18n.t("strategy.chart.line.benchmark",
                                         sym=bench_sym, name=cfg4["benchmark_name"]),
                          "values": _al(bench_norm), "color": theme.INK_3,
                          "dash": "dashed", "width": 1.5})
    if not port_v4.empty:
        cmp_lines.append({"name": i18n.t("strategy.biotech.compare.v4_line"),
                          "values": _al(port_v4), "color": theme.UP,
                          "dash": "solid", "width": 1.8})
    if not port_v5.empty:
        cmp_lines.append({"name": i18n.t("strategy.biotech.compare.v5_line"),
                          "values": _al(port_v5), "color": "#E0A458",
                          "dash": "solid", "width": 2.0})
    if not port_v6.empty:
        cmp_lines.append({"name": i18n.t("strategy.biotech.compare.v6_line"),
                          "values": _al(port_v6), "color": theme.CMSI_RED,
                          "dash": "solid", "width": 2.4})

    # rebalance markers on the chained chart (label each handover with its version)
    _reb_lab = i18n.t("strategy.chain.rebal_marker")
    chain_markers = [{"date": b, "label": f"{_reb_lab} → v{5 + i}"}
                     for i, b in enumerate(boundaries)]

    # 6 bottom KPI tiles
    n_v4 = len(strat.load_v4()) if not v4.empty else 0
    n_v5 = len(strat.load_v5()) if not v5.empty else 0
    days_held = (_idx[-1] - _idx[0]).days if len(_idx) else 0
    reb_done = len(boundaries)
    kpi_tiles = [
        {"label": "建仓日", "value": cfg4["pick_date"], "sub": "春季建仓 v4"},
        {"label": "已执行换仓", "value": f"{reb_done} 次",
         "sub": (f"{boundaries[-1]} → v5" if boundaries else "—")},
        {"label": "待执行", "value": ("v6 · 07-08" if port_v6.empty else "—"),
         "sub": ("选股确认中 · 待录入" if port_v6.empty else "已建仓"),
         "color": (theme.CMSI_RED if port_v6.empty else theme.INK)},
        {"label": "持仓数", "value": f"{n_v4} → {n_v5}", "sub": "v4 → v5 · 等权"},
        {"label": "持有天数", "value": f"{days_held} 天",
         "sub": f"{cfg4['pick_date']} → {(_idx[-1].date().isoformat() if len(_idx) else '')}"},
        {"label": "基准", "value": bench_sym, "sub": cfg4["benchmark_name"]},
    ]

    as_of = _idx[-1].date().isoformat() if len(_idx) else cfg4["pick_date"]
    strategy_hero.render_gen_compare(
        dates=dates, chain_curve=_al(acct_norm), bench_curve=_al(bench_norm),
        cmp_lines=cmp_lines, chain_markers=chain_markers,
        nav_str=f"{ccy} {cur_nav:,.0f}",
        cum_str=f"{'+' if cum >= 0 else ''}{cum:.2f}%",
        alpha_str=f"{'+' if alpha >= 0 else ''}{alpha:.2f}pp",
        gain_str=f"{'+' if gain >= 0 else '-'}{ccy} {abs(gain):,.0f}",
        bench_cum_str=f"{bench_cum:+.2f}%",
        cards=cards, kpi_tiles=kpi_tiles,
        chain_start=cfg4["pick_date"], currency=ccy, capital_str=f"{capital:,.0f}",
        v6_pending=(i18n.t("strategy.biotech.version.v6_pending") if port_v6.empty else ""),
        method_note=i18n.t("strategy.chain.note", cur=ccy, cap=f"{capital:,.0f}"),
        indep_title=i18n.t("strategy.chain.independent_section_title"),
        indep_badge=("v6 · 7月调仓 · 待录入" if port_v6.empty else ""),
        indep_note=i18n.t("strategy.biotech.compare.note"),
        chain_bench_name=i18n.t("strategy.chart.line.benchmark",
                                sym=bench_sym, name=cfg4["benchmark_name"]),
        chain_acct_name=i18n.t("strategy.chain.acct_line"),
        source=f"yfinance · 含息复权 · 截至 {as_of} · 真实累计收益,非回测美化",
    )


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
        elif sid == "v4_biotech":
            render_biotech_versions()
        else:
            render_strategy(sid)
with strategy_tabs[-1]:
    render_ipo_strategy()

st.divider()
st.caption(i18n.t("strategy.method.equal_weight"))
st.caption(i18n.t("strategy.method.total_return"))
st.caption(i18n.t("strategy.method.source"))
