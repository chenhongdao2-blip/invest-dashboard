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
        fillcolor="rgba(34, 197, 94, 0.15)",  # Translucent green
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
        line=dict(width=3, color=PRIMARY),
    ))

    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=title,
        yaxis_title="Indexed (start=100)",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
