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


def cumulative_return_chart(
    closes: pd.DataFrame,
    title: str = "",
    pick_date: str | None = None,
    show_individual: bool = False,
) -> go.Figure:
    """Index series to pick_date (or first date) = 100.
    Shows equal-weighted portfolio in bold, plus a 10-90th percentile shaded band
    for dispersion. Individual lines optional.
    """
    if closes.empty:
        return go.Figure()
    closes = closes.sort_index()
    if pick_date:
        anchor_ts = pd.Timestamp(pick_date)
        closes = closes[closes.index >= anchor_ts]
        if closes.empty:
            return go.Figure()

    base = closes.iloc[0]
    norm = (closes / base) * 100
    portfolio = norm.mean(axis=1)

    fig = go.Figure()

    # --- Dispersion Band (10th - 90th percentile) ---
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
        name="10th–90th %ile Range",
    ))

    # --- Individual Lines (Optional) ---
    if show_individual:
        for col in norm.columns:
            fig.add_trace(go.Scatter(
                x=norm.index, y=norm[col],
                mode="lines", name=col,
                line=dict(width=1), opacity=0.25,
                showlegend=False, hoverinfo="x+y+name",
            ))

    # --- Portfolio Line ---
    fig.add_trace(go.Scatter(
        x=portfolio.index, y=portfolio.values,
        mode="lines", name="Equal-weight Portfolio",
        line=dict(width=1.5, color=PRIMARY),
    ))

    fig.update_layout(
        title=_clean_title(title),
        yaxis_title="Indexed (start=100)",
        height=450,
    )
    return theme.style_plotly(fig)
