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
