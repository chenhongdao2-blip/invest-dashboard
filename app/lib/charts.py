"""Plotly chart helpers."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


PLOT_TEMPLATE = "plotly_dark"
PRIMARY = "#22c55e"
SECONDARY = "#06b6d4"
BENCH_LINE = "#a78bfa"
GRID = "#334155"


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
            line=dict(width=2),
        ))
    if benchmark is not None and not benchmark.empty:
        fig.add_trace(go.Scatter(
            x=benchmark.index, y=benchmark.values,
            mode="lines", name=benchmark_name or "Benchmark",
            line=dict(width=1.5, color=BENCH_LINE, dash="dot"),
        ))
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=title,
        yaxis_title=ylabel,
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0),
    )
    return fig


def cumulative_return_chart(
    closes: pd.DataFrame,
    title: str = "",
    pick_date: str | None = None,
) -> go.Figure:
    """Index series to pick_date (or first date) = 100.
    Each ticker shown as a translucent line, plus equal-weighted portfolio in bold.
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
    for col in norm.columns:
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm[col],
            mode="lines", name=col,
            line=dict(width=1), opacity=0.35,
            showlegend=False, hoverinfo="x+y+name",
        ))
    fig.add_trace(go.Scatter(
        x=portfolio.index, y=portfolio.values,
        mode="lines", name="Equal-weight portfolio",
        line=dict(width=3, color=PRIMARY),
    ))
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=title,
        yaxis_title="Indexed (start=100)",
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig
