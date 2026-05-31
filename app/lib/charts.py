"""Plotly chart helpers."""

from __future__ import annotations

import re

import pandas as pd
import plotly.graph_objects as go

from lib import theme

PLOT_TEMPLATE = "plotly_white"      # legacy; theme.style_plotly applies the real look
PRIMARY = theme.UP                  # portfolio / primary series — FT teal #0d7680
SECONDARY = theme.SECTOR_PALETTE[1]
BENCH_LINE = theme.INK_3            # benchmark — muted grey, dashed
GRID = theme.PAPER_RULE

# Strip emoji from chart titles: DESIGN.md bans emoji, and emoji glyphs render
# with inconsistent baseline/width in Plotly SVG (cccg-2 finding).
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF\uFE0F\u200D]+"
)


def _clean_title(t: str | None) -> str:
    return _EMOJI_RE.sub("", t).strip() if t else (t or "")


def price_line_chart(
    df: pd.DataFrame,
    title: str = "",
    ylabel: str = "Close",
    benchmark: pd.Series | None = None,
    benchmark_name: str = "",
) -> go.Figure:
    """Single-series price line.
    df: wide DataFrame with date index, one (or more) ticker columns.
    """
    fig = go.Figure()
    for col in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col],
            mode="lines", name=col,
            line=dict(width=1.5),
        ))
    if benchmark is not None and not benchmark.empty:
        fig.add_trace(go.Scatter(
            x=benchmark.index, y=benchmark.values,
            mode="lines", name=benchmark_name or "Benchmark",
            line=dict(width=1.5, color=BENCH_LINE, dash="dot"),
        ))
    fig.update_layout(
        title=_clean_title(title),
        yaxis_title=ylabel,
        height=380,
    )
    return theme.style_plotly(fig)


def _rgba(hex_color: str, a: float) -> str:
    """'#rrggbb' → 'rgba(r,g,b,a)' (for soft fills under a same-color line)."""
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        r, g, b = 74, 74, 74
    return f"rgba({r},{g},{b},{a:.3f})"


def mini_trend_chart(
    series: pd.Series,
    *,
    title: str = "",
    color: str | None = None,
    ylabel: str = "USD bn",
) -> go.Figure:
    """Compact single-metric trend (SEC financials: Revenue / R&D / Cash …).

    series: index=period-end date, values in display units (e.g. USD billions).
    Smooth spline line over a soft gradient fill, small period markers, and an
    emphasised last point — a clean sell-side sparkline. Height 220, designed to
    sit in a 3-column st.columns grid. FT-editorial via theme.style_plotly.
    """
    fig = go.Figure()
    if series is None or series.dropna().empty:
        return theme.style_plotly(fig)
    c = color or theme.INK_2
    s = series.dropna()
    # Area fill (soft, same-hue) under a smoothed spline line.
    fig.add_trace(go.Scatter(
        x=s.index, y=s.values, mode="lines",
        line=dict(width=2.2, color=c, shape="spline", smoothing=0.6),
        fill="tozeroy", fillcolor=_rgba(c, 0.10), showlegend=False,
        hovertemplate="%{x|%Y-%m}<br>%{y:.2f}<extra></extra>",
    ))
    # Small markers at the real (annual) data points so the spline stays honest.
    fig.add_trace(go.Scatter(
        x=s.index, y=s.values, mode="markers",
        marker=dict(size=4, color=c), showlegend=False, hoverinfo="skip",
    ))
    # Emphasised last point (ring) — the latest reported value.
    fig.add_trace(go.Scatter(
        x=[s.index[-1]], y=[s.values[-1]], mode="markers",
        marker=dict(size=8, color=c, line=dict(width=2, color=theme.PAPER)),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_layout(
        title=_clean_title(title), yaxis_title=ylabel, height=220,
        margin=dict(l=52, r=18, t=52, b=28),
        xaxis=dict(showgrid=False),   # declutter — keep only horizontal gridlines
    )
    return theme.style_plotly(fig)


def relative_strength_chart(
    stock: pd.Series,
    benchmarks: dict[str, pd.Series],
    *,
    stock_name: str,
    title: str = "",
    ylabel: str = "Rebased (start=100)",
) -> tuple[go.Figure | None, str | None]:
    """Rebased=100 relative strength: a single stock vs sector benchmark(s).

    G3 (Codex /cccg): all series are INNER-JOINED on common trading days and
    rebased to 100 at the FIRST COMMON date — never each series' own first day.
    benchmarks_daily starts ~2 months later than prices_daily, so rebasing the
    stock from its own earlier start would show that start-date gap as spurious
    alpha. The anchor is therefore the latest common start.

    Series are distinguished by line STYLE not color (DESIGN.md §4): the stock is
    a solid CMSI-red 1.8px line; benchmarks are muted-grey dashed/dotted 1.3px.

    Returns (figure, anchor_date_iso). Figure is None when there is too little
    common history (<5 points) — the caller should fall back to the absolute
    price line.
    """
    if stock is None or stock.dropna().empty or not benchmarks:
        return None, None
    frame: dict[str, pd.Series] = {stock_name: stock.dropna()}
    for sym, ser in benchmarks.items():
        if ser is not None and not ser.dropna().empty:
            frame[sym] = ser.dropna()
    wide = pd.DataFrame(frame).dropna()          # inner-join → common trading days
    if len(wide) < 5 or wide.shape[1] < 2:
        return None, None
    rebased = wide.divide(wide.iloc[0]) * 100.0   # anchor = first common date
    anchor_iso = wide.index[0].date().isoformat()

    fig = go.Figure()
    # Benchmarks first (drawn under), muted grey, distinguished by dash pattern.
    dash_cycle = ["dash", "dot", "dashdot"]
    bench_cols = [c for c in rebased.columns if c != stock_name]
    for i, col in enumerate(bench_cols):
        fig.add_trace(go.Scatter(
            x=rebased.index, y=rebased[col], mode="lines", name=col,
            line=dict(width=1.3, color=theme.INK_3, dash=dash_cycle[i % len(dash_cycle)]),
        ))
    # Stock on top — solid CMSI-red emphasis.
    fig.add_trace(go.Scatter(
        x=rebased.index, y=rebased[stock_name], mode="lines", name=stock_name,
        line=dict(width=1.8, color=theme.CMSI_RED),
    ))
    fig.update_layout(title=_clean_title(title), yaxis_title=ylabel, height=380)
    # Baseline at 100 — the rebase anchor reference.
    fig.add_hline(y=100, line=dict(width=1, color=theme.INK_3, dash="dash"), opacity=0.4)
    return theme.style_plotly(fig), anchor_iso


def _diverging_color(pct: float, *, cap: float = 12.0) -> str:
    """Map a signed % return to a diverging teal(up)/red(down) hex, centered at 0.

    Saturation ramps linearly to `cap` (±%) then clamps — keeps the heatmap
    readable instead of letting one outlier dominate the scale. 0% → near-neutral
    paper-band so flat tiles don't shout. Colors: theme.UP teal / theme.DOWN red
    (project LOCKED convention: teal up / red down).
    """
    if pct is None or pd.isna(pct):
        return theme.PAPER_BAND
    mag = min(abs(float(pct)) / cap, 1.0)            # 0..1 saturation
    # Blend from a neutral cream band toward the full up/down hue.
    n_r, n_g, n_b = 0xf2, 0xdf, 0xce                 # PAPER_BAND neutral anchor
    if pct >= 0:
        t_r, t_g, t_b = 0x0d, 0x76, 0x80            # theme.UP teal
    else:
        t_r, t_g, t_b = 0xcc, 0x00, 0x00            # theme.DOWN red
    r = round(n_r + (t_r - n_r) * mag)
    g = round(n_g + (t_g - n_g) * mag)
    b = round(n_b + (t_b - n_b) * mag)
    return f"#{r:02x}{g:02x}{b:02x}"


def treemap_heatmap(
    df: pd.DataFrame,
    *,
    size_col: str,
    color_col: str,
    group_col: str,
    label_col: str,
    title: str = "",
    cap: float = 12.0,
) -> go.Figure:
    """Finviz-style treemap: tiles sized by `size_col` (market cap), colored by
    `color_col` (signed % return, diverging teal/red centered at 0), grouped by
    `group_col` (sub-sector). `label_col` is the display name shown on each tile.

    Expected df columns (one row per stock):
      - index or a column holding the ticker (we read it from df.index)
      - size_col   : positive market cap (rows with NaN/≤0 are dropped by caller)
      - color_col  : signed % return for the selected window
      - group_col  : sub-sector bucket (treemap parent)
      - label_col  : display name (中文 when prefer_cn)

    Returns a go.Figure on the cream PAPER background. Caller is responsible for
    the empty-data st.info fallback (we still return a valid empty figure if df
    is empty so callers never crash).
    """
    fig = go.Figure()
    if df is None or df.empty:
        return theme.style_plotly(fig)

    work = df.copy()
    # Per-tile color from the signed return (diverging, capped).
    colors = [_diverging_color(v, cap=cap) for v in work[color_col]]

    # Tile text: ticker + signed % on two lines; hover adds name + mcap.
    tickers = [str(t) for t in work.index]

    def _fmt_pct(v) -> str:
        return "—" if (v is None or pd.isna(v)) else f"{float(v):+.1f}%"

    def _fmt_mcap(v) -> str:
        # Real market cap (USD) for the hover. size_col is now |return| (abs_ret),
        # so mcap must come from its own 'mcap' column — never from `sizes`.
        if v is None or pd.isna(v):
            return "—"
        v = float(v)
        if v >= 1e12:
            return f"${v / 1e12:.1f}T"
        if v >= 1e9:
            return f"${v / 1e9:.1f}B"
        if v >= 1e6:
            return f"${v / 1e6:.1f}M"
        return f"${v:,.0f}"

    labels = list(work[label_col].astype(str))
    groups = list(work[group_col].astype(str))
    sizes = [float(x) for x in work[size_col]]
    texts = [f"{tk}<br>{_fmt_pct(v)}" for tk, v in zip(tickers, work[color_col])]

    # Build a flat go.Treemap with a synthetic root → group → leaf hierarchy.
    # ids must be unique; labels can repeat. Leaf id = ticker, parent = group.
    root_id = "ALL"
    seen_groups: list[str] = []
    for g in groups:
        if g not in seen_groups:
            seen_groups.append(g)

    ids = [root_id] + [f"grp::{g}" for g in seen_groups] + tickers
    parents = [""] + [root_id for _ in seen_groups] + [f"grp::{g}" for g in groups]
    node_labels = [_clean_title(title) or "ALL"] + list(seen_groups) + texts
    node_values = [0.0] + [0.0 for _ in seen_groups] + sizes  # branchvalues=remainder→leaves sum up
    node_colors = [theme.PAPER] + [theme.PAPER_DEEP for _ in seen_groups] + colors
    # Hover only for leaves; carry name + pct + REAL mcap via customdata.
    # 3rd field = market cap (USD) from work['mcap'] when present — NOT the
    # tile size (size_col is now |return|, so reusing `sizes` would mislabel
    # |return| as mcap). Missing/NaN mcap → "—".
    if "mcap" in work.columns:
        mcap_strs = [_fmt_mcap(m) for m in work["mcap"]]
    else:
        mcap_strs = ["—" for _ in tickers]
    customdata = (
        [["", "", ""]]
        + [[g, "", ""] for g in seen_groups]
        + [[lab, _fmt_pct(v), mc] for lab, v, mc in zip(labels, work[color_col], mcap_strs)]
    )

    fig.add_trace(go.Treemap(
        ids=ids,
        labels=node_labels,
        parents=parents,
        values=node_values,
        branchvalues="remainder",
        marker=dict(colors=node_colors, line=dict(width=1, color=theme.PAPER)),
        text=None,
        textposition="middle center",
        textfont=dict(size=12, color=theme.INK, family=theme.FONT_STACK),
        customdata=customdata,
        hovertemplate="%{customdata[0]}<br>%{customdata[1]} · mcap %{customdata[2]}<extra></extra>",
        tiling=dict(pad=2),
        sort=True,
        pathbar=dict(visible=False),
    ))
    fig.update_layout(
        title=_clean_title(title),
        height=460,
        margin=dict(l=8, r=8, t=56, b=8),
    )
    fig = theme.style_plotly(fig)
    # Treemap has no x/y axes — strip the FT grid/axis layout style would add.
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False, hovermode="closest",
    )
    return fig


def cumulative_return_chart(
    normed: pd.DataFrame,
    portfolio: pd.Series,
    *,
    title: str = "",
    portfolio_rebalanced: pd.Series | None = None,
    show_individual: bool = False,
    show_rebalanced: bool = False,
    labels: dict | None = None,
) -> go.Figure:
    """Plot precomputed since-inception curves (indexed=100).

    Ship-gate #2: this function does NOT recompute portfolio math — it consumes
    series already produced by `strategy.compute_strategy_returns` (single
    source). `normed` is the per-ticker indexed wide frame, used ONLY for the
    dispersion band + optional individual lines.

    - portfolio: equal-weight buy & hold (solid, primary) — always shown.
    - portfolio_rebalanced: equal-weight periodic rebalance (dashed) — shown when
      `show_rebalanced` and the series is non-empty.
    - labels: i18n line names; keys 'portfolio' / 'rebalanced' / 'band' / 'y'.
      Defaults to English so the chart stays i18n-agnostic.
    """
    if portfolio is None or portfolio.empty:
        return go.Figure()
    lab = {
        "portfolio": "Portfolio (buy & hold)",
        "rebalanced": "Portfolio (monthly rebalance)",
        "band": "10th–90th %ile range",
        "y": "Indexed (start=100)",
        **(labels or {}),
    }

    fig = go.Figure()

    # --- Dispersion Band (10th - 90th percentile) — display only ---
    if normed is not None and not normed.empty and normed.shape[1] >= 2:
        norm = normed.sort_index()
        p10 = norm.quantile(0.1, axis=1)
        p90 = norm.quantile(0.9, axis=1)
        fig.add_trace(go.Scatter(
            x=p90.index.tolist() + p90.index[::-1].tolist(),
            y=p90.values.tolist() + p10.values[::-1].tolist(),
            fill="toself",
            fillcolor="rgba(13, 118, 128, 0.12)",  # FT teal tint ≤12% (DESIGN.md)
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name=lab["band"],
        ))
        # --- Individual Lines (Optional) ---
        if show_individual:
            for col in norm.columns:
                fig.add_trace(go.Scatter(
                    x=norm.index, y=norm[col],
                    mode="lines", name=str(col),
                    line=dict(width=1), opacity=0.25,
                    showlegend=False, hoverinfo="x+y+name",
                ))

    # --- Rebalanced Line (dashed) — drawn under the buy&hold solid ---
    if show_rebalanced and portfolio_rebalanced is not None and not portfolio_rebalanced.empty:
        fig.add_trace(go.Scatter(
            x=portfolio_rebalanced.index, y=portfolio_rebalanced.values,
            mode="lines", name=lab["rebalanced"],
            line=dict(width=1.5, color=SECONDARY, dash="dash"),
        ))

    # --- Portfolio Line (buy & hold, solid primary) ---
    fig.add_trace(go.Scatter(
        x=portfolio.index, y=portfolio.values,
        mode="lines", name=lab["portfolio"],
        line=dict(width=1.5, color=PRIMARY),
    ))

    fig.update_layout(
        title=_clean_title(title),
        yaxis_title=lab["y"],
        height=450,
    )
    return theme.style_plotly(fig)
