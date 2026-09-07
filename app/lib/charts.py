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


# ── HK IPO 打新 backtest charts (static cross-section; teal up / red down) ──

# Tier → discrete marker color (4 tiers, semantics consistent with the site).
_IPO_TIER_COLORS = {
    "重点申购+": theme.UP_DEEP,    # 深 teal
    "推荐申购": theme.UP,          # teal
    "谨慎申购": "#a07a2c",         # amber (FT muted)
    "不申购": theme.INK_3,         # grey
}


# 市值分层 → marker color (HK HC IPO tracker). 大=anchor red (恒瑞 outlier),
# 中=teal (winners cohort), 小=grey (the 破发 cluster).
_IPO_MKT_TIER_COLORS = {
    "大市值": theme.CMSI_RED,
    "中市值": theme.UP,
    "小市值": theme.INK_3,
}


def scatter_returns(
    df: pd.DataFrame,
    *,
    mktcap_col: str = "cur_mktcap_yi",
    ret_col: str = "ret_pct",
    tier_col: str = "mktcap_tier",
    name_col: str = "name_cn",
    title: str = "",
    x_label: str = "现市值 (亿 HKD, log)",
    y_label: str = "自发行价涨幅 %",
) -> go.Figure:
    """Return-since-offer vs current market cap, colored by 市值分层; y=0 dotted = 破发线.

    Renders the 'larger-cap = stays above water' story: 小市值 dots cluster below the line,
    中/大市值 above. Log x-axis (恒瑞 is a 3700亿 outlier vs a sub-100亿 long tail)."""
    fig = go.Figure()
    d = df.dropna(subset=[mktcap_col, ret_col])
    if d.empty:
        return theme.style_plotly(fig)
    for tier, color in _IPO_MKT_TIER_COLORS.items():
        sub = d[d[tier_col] == tier]
        if sub.empty:
            continue
        txt = [f"{n}<br>{tier} · 市值 {mc:,.0f}亿<br>涨幅 {r:+.0f}%"
               for n, mc, r in zip(sub[name_col], sub[mktcap_col], sub[ret_col])]
        fig.add_trace(go.Scatter(
            x=sub[mktcap_col], y=sub[ret_col], mode="markers", name=tier,
            marker=dict(size=11, color=color, line=dict(width=0.8, color="white"), opacity=0.9),
            text=txt, hovertemplate="%{text}<extra></extra>",
        ))
    fig.add_hline(y=0, line=dict(width=1.2, color=theme.INK_2, dash="dot"))
    fig.update_layout(title=_clean_title(title), height=420)
    fig = theme.style_plotly(fig)
    fig.update_layout(
        xaxis=dict(title=dict(text=x_label, font=dict(size=12, color=theme.INK_2)),
                   type="log", tickfont=dict(size=11, color=theme.INK_2)),
        yaxis=dict(title=dict(text=y_label, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11, color=theme.INK_2)),
        margin=dict(l=8, r=24, t=70, b=44),
    )
    return fig


def ranked_hbar(
    labels: list,
    values: list,
    *,
    title: str = "",
    xlabel: str = "USD bn",
    color: str | None = None,
    value_fmt: str = "$%.0fB",
    height: int | None = None,
) -> go.Figure:
    """Horizontal ranked bar (league table) — e.g. M&A $ per MNC, or per TA.

    Highest at the TOP. Bars are teal (gross magnitudes; up/down convention N/A).
    Value labels printed at the bar end. Height auto-scales to bar count.
    """
    fig = go.Figure()
    if not labels:
        return theme.style_plotly(fig)
    c = color or theme.UP
    # Plotly draws the first category at the bottom; reverse so largest is on top.
    labs = list(labels)[::-1]
    vals = list(values)[::-1]
    texts = [value_fmt % v for v in vals]
    fig.add_trace(go.Bar(
        x=vals, y=labs, orientation="h",
        marker_color=c, marker_line_width=0,
        text=texts, textposition="outside",
        textfont=dict(size=11, color=theme.INK_2),
        hovertemplate="%{y}<br>%{x:,.1f} " + xlabel + "<extra></extra>",
    ))
    h = height or max(220, 26 * len(labs) + 80)
    fig.update_layout(title=_clean_title(title), height=h, showlegend=False)
    fig = theme.style_plotly(fig)
    fig.update_layout(
        xaxis=dict(title=dict(text=xlabel, font=dict(size=12, color=theme.INK_2)),
                   tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2)),
        yaxis=dict(tickfont=dict(size=12, color=theme.INK), showgrid=False),
        margin=dict(l=8, r=64, t=64, b=40),
    )
    return fig


def year_bar(
    years: list,
    values: list,
    *,
    title: str = "",
    ylabel: str = "USD bn",
    color: str | None = None,
    dtick: int = 5,
    value_hover_fmt: str = ",.1f",
) -> go.Figure:
    """Vertical bars by year — M&A deal value per year (shows the deal waves).

    dtick: x-axis tick spacing in years. Default 5 fits the long M&A timeline
    (1986-2026); pass dtick=1 for a short 2-3 year series (e.g. BD 2025-2026) so
    every year gets a tick. value_hover_fmt lets a count series drop the decimals.
    """
    fig = go.Figure()
    if not years:
        return theme.style_plotly(fig)
    fig.add_trace(go.Bar(
        x=list(years), y=list(values),
        marker_color=color or theme.UP, marker_line_width=0,
        hovertemplate="%{x}<br>%{y:" + value_hover_fmt + "} " + ylabel + "<extra></extra>",
    ))
    fig.update_layout(title=_clean_title(title), height=320, showlegend=False)
    fig = theme.style_plotly(fig)
    fig.update_layout(
        yaxis=dict(title=dict(text=ylabel, font=dict(size=12, color=theme.INK_2)),
                   tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2)),
        xaxis=dict(tickfont=dict(size=10, color=theme.INK_2), dtick=dtick),
    )
    return fig


def positioning_diverging_bar(
    labels: list,
    deviations: list,           # signed FRACTION: -0.038 → −3.8pp underweight
    *,
    title: str = "",
    xlabel: str = "Deviation from benchmark (pp)",
    height: int | None = None,
) -> go.Figure:
    """Diverging horizontal bars — fund healthcare over/underweight vs its own BM.

    x = deviation in PERCENTAGE POINTS (fund HC weight − benchmark HC weight).
    Color is the LOCKED project convention: overweight (>0) → teal (theme.UP),
    underweight (<0) → red (theme.DOWN). NOTE this is a *positioning* tilt, not a
    price return — the page caption must spell out "teal = 超配 / red = 低配" so the
    A-share red-is-up reflex doesn't misread it. Sorted most-OW at top. A vertical
    zero line marks the benchmark weight. Funds with no disclosure (NaN) are
    expected to be dropped by the caller.
    """
    fig = go.Figure()
    if not labels:
        return theme.style_plotly(fig)
    order = sorted(range(len(labels)),
                   key=lambda k: (deviations[k] if deviations[k] is not None else 0.0))
    labs = [labels[k] for k in order]
    pp = [round((deviations[k] or 0.0) * 100, 1) for k in order]
    colors = [theme.UP if v >= 0 else theme.DOWN for v in pp]
    texts = [(f"+{v:.1f}" if v > 0 else f"{v:.1f}") for v in pp]
    fig.add_trace(go.Bar(
        x=pp, y=labs, orientation="h",
        marker_color=colors, marker_line_width=0,
        text=texts, textposition="outside",
        textfont=dict(size=11, color=theme.INK_2),
        hovertemplate="%{y}<br>%{x:+.1f} pp vs benchmark<extra></extra>",
    ))
    h = height or max(240, 30 * len(labs) + 90)
    fig.update_layout(title=_clean_title(title), height=h, showlegend=False)
    fig = theme.style_plotly(fig)
    fig.add_vline(x=0, line=dict(width=1.2, color=theme.INK_2), opacity=0.7)
    fig.update_layout(
        xaxis=dict(title=dict(text=xlabel, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), zeroline=False),
        yaxis=dict(tickfont=dict(size=12, color=theme.INK), showgrid=False, automargin=True),
        margin=dict(l=8, r=60, t=64, b=44),
    )
    return fig


def headcount_diverging_bar(
    labels: list,
    deltas: list,               # signed integer: +1843 hire / −2944 cut (people)
    *,
    title: str = "",
    xlabel: str = "Headcount change (FY2024 → FY2025)",
    height: int | None = None,
) -> go.Figure:
    """Diverging horizontal bars — net headcount change per company (扩招 vs 收缩).

    x = signed COUNT of people (FY2025 − FY2024). Color follows the LOCKED project
    convention: net hire (>0) → teal (theme.UP), net cut (<0) → red (theme.DOWN).
    NOTE this is an operating-posture signal, not a price return — the page caption
    must spell out "teal = 扩招 / red = 收缩" so the A-share red-is-up reflex doesn't
    misread it. Sorted biggest hirer at top; a vertical zero line marks no change.
    """
    fig = go.Figure()
    if not labels:
        return theme.style_plotly(fig)
    order = sorted(range(len(labels)),
                   key=lambda k: (deltas[k] if deltas[k] is not None else 0))
    labs = [labels[k] for k in order]
    vals = [int(deltas[k] or 0) for k in order]
    colors = [theme.UP if v >= 0 else theme.DOWN for v in vals]
    texts = [(f"+{v:,}" if v > 0 else f"{v:,}") for v in vals]
    fig.add_trace(go.Bar(
        x=vals, y=labs, orientation="h",
        marker_color=colors, marker_line_width=0,
        text=texts, textposition="outside",
        textfont=dict(size=11, color=theme.INK_2),
        hovertemplate="%{y}<br>%{x:+,} 人<extra></extra>",
    ))
    h = height or max(240, 30 * len(labs) + 90)
    fig.update_layout(title=_clean_title(title), height=h, showlegend=False)
    fig = theme.style_plotly(fig)
    fig.add_vline(x=0, line=dict(width=1.2, color=theme.INK_2), opacity=0.7)
    fig.update_layout(
        xaxis=dict(title=dict(text=xlabel, font=dict(size=12, color=theme.INK_2)),
                   tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2), zeroline=False),
        yaxis=dict(tickfont=dict(size=12, color=theme.INK), showgrid=False, automargin=True),
        margin=dict(l=8, r=64, t=64, b=44),
    )
    return fig


# ── Analyst-model views (Model Drill page) ──────────────────────────────────
# All take `periods` = [{"label","actual_est"}] so the actual→forecast boundary
# renders uniformly: actuals solid/opaque, forecast semi-transparent, with a
# dotted "Forecast →" divider at the first "E" column.

def _fc_boundary(periods):
    return next((i for i, p in enumerate(periods) if p.get("actual_est") == "E"), None)


def _fc_opacity(periods):
    return [1.0 if p.get("actual_est") == "A" else 0.45 for p in periods]


def _add_forecast_divider(fig, periods, prefer_cn, label=True):
    fe = _fc_boundary(periods)
    if fe is None or fe <= 0:   # all-forecast window → no actual region to divide
        return
    fig.add_vline(x=fe - 0.5, line=dict(width=1.2, color=theme.INK_3, dash="dot"))
    if label:
        fig.add_annotation(x=fe - 0.5, y=1.0, yref="paper", showarrow=False,
                           text=("预测 →" if prefer_cn else "Forecast →"),
                           font=dict(size=10, color=theme.INK_3), xanchor="left", yshift=2)


_REV_LIGHT_TEAL = "#7fb0b3"   # non-dominant segment (mono-teal palette, George 2026-06-01)


def model_revenue_chart(breakdown, periods, *, prefer_cn=True, window=None):
    """Revenue 2×2 in ONE stacked bar, all on ONE teal hue (George 2026-06-01 —
    the prior 2nd hue, amber then slate, clashed on cream): segment by DEPTH
    (dominant-by-revenue → deep teal, others → light teal, data-driven — never
    hardcode a name), basis by PATTERN (subscription = solid, professional
    services = diagonal hatch over the same fill, NOT a 0.5α shade — α blurred the
    four blocks together). Per-period top label = "{lead} NN%" (e.g. "R&D 53%"),
    the lead segment's %-of-revenue, so the bare number isn't ambiguous. Values
    shown in USD **billions**. `window` = period labels to show (default last ~6
    incl. 2 forecast; the full 16y would crowd 64 blocks)."""
    ps = [p for p in periods if p["label"] in set(window)] if window else periods
    labels = [p["label"] for p in ps]
    op = _fc_opacity(ps)
    # dominant segment by total revenue over the WHOLE series (not the shown window)
    # → the lead segment's deep-teal stays stable when the annual/quarterly toggle
    # or window changes (cccg-Gemini: a window-local dominance could flip the hue).
    seg_tot = {}
    for s in breakdown:
        seg_tot[s["segment"]] = seg_tot.get(s["segment"], 0.0) + sum(
            (v or 0) for v in s["values"].values())
    ranked = sorted(seg_tot, key=lambda s: -seg_tot[s])
    dominant = ranked[0] if ranked else None
    # mono-teal: lead = deep teal, every other segment = light teal. Segment read
    # by depth, basis by hatch (below) — one cool family, no clashing 2nd hue.
    hue = {dominant: theme.UP}
    for s in ranked[1:]:
        hue[s] = _REV_LIGHT_TEAL

    def _val_bn(s, l):
        v = s["values"].get(l)
        return v / 1000.0 if v is not None else None   # USD millions → billions

    # stack: non-dominant (bottom) → dominant (top); within a segment, services below subscription
    order = sorted(breakdown, key=lambda s: (s["segment"] == dominant,
                                             s["basis"] == "subscription"))
    fig = go.Figure()
    for s in order:
        name = (s.get("label_cn") if prefer_cn else s.get("label_en")) or s.get("key", "")
        seg_hue = hue.get(s["segment"], theme.INK_3)
        is_sub = s["basis"] == "subscription"
        # services = same fill + cream diagonal hatch; subscription = solid fill.
        pattern = dict(shape="" if is_sub else "/",
                       fgcolor=theme.PAPER, size=7, solidity=0.32)
        fig.add_trace(go.Bar(
            x=labels, y=[_val_bn(s, l) for l in labels], name=name, legendgroup=s["segment"],
            marker=dict(color=seg_hue, opacity=op, line=dict(width=0), pattern=pattern),
            hovertemplate="%{x} · " + str(name) + " $%{y:,.2f}B<extra></extra>"))
    # lead-segment %-of-total annotation per period — labelled with the segment
    # name ("R&D 53%") so the number's meaning is explicit (George 2026-06-01).
    for l in labels:
        tot = sum((s["values"].get(l) or 0) for s in breakdown)
        dom = sum((s["values"].get(l) or 0) for s in breakdown if s["segment"] == dominant)
        if tot:
            fig.add_annotation(x=l, y=tot / 1000.0, yshift=11, showarrow=False,
                               text=f"{dominant} {dom / tot * 100:.0f}%",
                               font=dict(size=10, color=theme.UP_DEEP, family=theme.FONT_MONO))
    fig.update_layout(barmode="stack", height=400,
                      legend=dict(orientation="h", y=1.13, x=0),
                      yaxis_title=("收入 ($B)" if prefer_cn else "Revenue ($B)"))
    _add_forecast_divider(fig, ps, prefer_cn)
    return theme.style_plotly(fig)


def model_margin_chart(margins, periods, *, prefer_cn=True):
    """Margin lines; GAAP = muted grey dashed, non-GAAP = solid coloured. Caller
    chooses which margins to pass (keep it to ~4 for legibility)."""
    labels = [p["label"] for p in periods]
    pal = {"gross_margin": theme.UP_TINT, "operating_margin": theme.UP,
           "net_margin": theme.SECTOR_PALETTE[2]}
    fig = go.Figure()
    for mg in margins:
        is_gaap = mg["basis"] == "gaap"
        nm = (mg.get("metric_cn") if prefer_cn else mg.get("metric_en")) or mg["metric"]
        y = [mg["values"].get(l) for l in labels]
        color = theme.INK_3 if is_gaap else pal.get(mg["metric"], theme.UP)
        fig.add_trace(go.Scatter(
            x=labels, y=y, mode="lines", name=nm,
            line=dict(width=1.5 if is_gaap else 2.2, color=color,
                      dash="dash" if is_gaap else "solid"),
            hovertemplate="%{x} · " + nm + " %{y:.1%}<extra></extra>"))
    fig.update_layout(height=360, yaxis=dict(tickformat=".0%"),
                      legend=dict(orientation="h", y=1.14, x=0),
                      yaxis_title=("利润率" if prefer_cn else "Margin"))
    _add_forecast_divider(fig, periods, prefer_cn, label=False)
    return theme.style_plotly(fig)


def model_bridge_chart(bridge, *, prefer_cn=True):
    """GAAP→Non-GAAP waterfall (one reported quarter). Neutral grey steps —
    accounting add-backs are NOT market up/down, so no teal/red."""
    items = bridge["items"]
    names = [it["item"] if prefer_cn else it.get("item_en", it["item"]) for it in items]
    vals = [it["value"] for it in items]
    measure = ["absolute"] + ["relative"] * (len(items) - 2) + ["total"]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measure, x=names, y=vals,
        text=[f"{v:+.0f}" if m == "relative" else f"{v:.0f}" for v, m in zip(vals, measure)],
        textposition="outside", textfont=dict(family=theme.FONT_MONO, size=11),
        connector=dict(line=dict(color=theme.PAPER_RULE)),
        increasing=dict(marker=dict(color=theme.INK_3)),
        decreasing=dict(marker=dict(color=theme.INK_3)),
        totals=dict(marker=dict(color=theme.UP)),
    ))
    per = bridge.get("period", "")
    fig.update_layout(height=340,
                      yaxis_title=("营业利润 ($M)" if prefer_cn else "Operating Income ($M)"),
                      title=_clean_title(f"{per} " + ("GAAP → 非GAAP 桥" if prefer_cn else "GAAP → Non-GAAP Bridge")))
    return theme.style_plotly(fig)


def model_forecast_chart(forecast, periods, *, prefer_cn=True,
                         bar_line="revenue", overlay_line="eps_nongaap"):
    """Forecast lines. With a bar_line: revenue bars (actual/forecast opacity) + the
    overlay line on a 2nd axis. With bar_line=None: the overlay line ALONE on the
    primary axis (post-polish default — revenue already lives in the ① chart, so a
    2nd revenue bar here would be redundant)."""
    labels = [p["label"] for p in periods]
    op = _fc_opacity(periods)
    byk = {f["line"]: f for f in forecast}
    bar = byk.get(bar_line)
    line = byk.get(overlay_line)
    fig = go.Figure()
    if bar:
        nm = bar["line_cn"] if prefer_cn else bar["line_en"]
        fig.add_trace(go.Bar(x=labels, y=[bar["values"].get(l) for l in labels], name=nm,
                             marker=dict(color=theme.UP, opacity=op),
                             hovertemplate="%{x} · " + nm + " $%{y:,.0f}M<extra></extra>"))
    if line:
        nm = line["line_cn"] if prefer_cn else line["line_en"]
        fig.add_trace(go.Scatter(x=labels, y=[line["values"].get(l) for l in labels], name=nm,
                                 mode="lines+markers", yaxis=("y2" if bar else "y"),
                                 line=dict(width=2.2, color=theme.CMSI_RED), marker=dict(size=6),
                                 hovertemplate="%{x} · " + nm + " $%{y:.2f}<extra></extra>"))
    layout = dict(height=360, legend=dict(orientation="h", y=1.1, x=0))
    if bar:
        layout["yaxis"] = dict(title=("收入 ($M)" if prefer_cn else "Revenue ($M)"))
        layout["yaxis2"] = dict(title="EPS ($)", overlaying="y", side="right", showgrid=False)
    else:
        layout["yaxis"] = dict(title=("每股收益 (非GAAP, $)" if prefer_cn else "EPS (non-GAAP, $)"))
    fig.update_layout(**layout)
    _add_forecast_divider(fig, periods, prefer_cn)
    return theme.style_plotly(fig)


def rule_of_40_scatter(df, *, highlight=None, prefer_cn=True, title="",
                       x_label=None, y_label=None):
    """Rule-of-40 valuation matrix (replaces the WACC×TG sensitivity in ③): X =
    revenue growth + FCF margin (%), Y = EV/Sales (x) on a LOG axis. Software/SaaS
    comps plot as hollow teal circles labelled by ticker (the sell-side comp-cloud
    idiom); `highlight` (e.g. VEEV) is a filled CMSI-red point with a bold label.

    De-crowding (George 2026-06-01): EV/Sales spans 1–70x and most comps sit in the
    3–12x band, which a linear axis crushes together. A LOG y-axis stretches that
    band apart and lets premium names (PLTR ~70x) sit naturally at the top — no cap
    / outlier-pin needed. Dashed mean lines anchor both axes; a dotted Rule-of-40 =
    40 line (the SaaS '优秀线') with a faint shade marks the >40 zone. All inputs are
    live snapshot data, so positions move with the market — re-run fetch_eod."""
    fig = go.Figure()
    if df is None or df.empty:
        return theme.style_plotly(fig)
    work = df[df["ev_sales"] > 0].copy()   # log axis needs strictly positive y
    if work.empty:
        return theme.style_plotly(fig)
    avg_y = float(work["ev_sales"].mean())
    avg_x = float(work["rule40"].mean())
    x_lo, x_hi = float(work["rule40"].min()), float(work["rule40"].max())
    y_hi = float(work["ev_sales"].max())
    import math
    hl = highlight if (highlight and highlight in work.index) else None

    def _hover(idx, row):
        nm = (row["name_cn"] if prefer_cn else row["name_en"]) or idx
        g, f = ("增速", "FCF margin") if prefer_cn else ("growth", "FCF margin")
        return (f"<b>{idx}</b> {nm}<br>Rule of 40 {row['rule40']:.1f}% "
                f"({g} {row['rev_growth']:.1f}% + {f} {row['fcf_margin']:.1f}%)"
                f"<br>EV/Sales {row['ev_sales']:.1f}x")

    # faint shade of the > 40 "优秀区间"
    fig.add_vrect(x0=40, x1=x_hi + 15, fillcolor=theme.UP, opacity=0.04, line_width=0)

    peers = work.drop(index=hl) if hl else work
    # peers — hollow teal circles + ticker label
    fig.add_trace(go.Scatter(
        x=peers["rule40"], y=peers["ev_sales"], mode="markers+text",
        text=list(peers.index), textposition="top center",
        textfont=dict(size=11, color=theme.INK_2, family=theme.FONT_STACK),
        marker=dict(size=12, color="rgba(0,0,0,0)", line=dict(width=1.6, color=theme.UP)),
        customdata=[_hover(i, r) for i, r in peers.iterrows()],
        hovertemplate="%{customdata}<extra></extra>", showlegend=False))
    # highlight — filled CMSI-red, bold label
    if hl:
        r = work.loc[hl]
        fig.add_trace(go.Scatter(
            x=[r["rule40"]], y=[r["ev_sales"]], mode="markers+text",
            text=[f"<b>{hl}</b>"], textposition="top center",
            textfont=dict(size=14, color=theme.CMSI_RED, family=theme.FONT_STACK),
            marker=dict(size=16, color=theme.CMSI_RED, symbol="circle",
                        line=dict(width=1.5, color=theme.PAPER)),
            customdata=[_hover(hl, r)],
            hovertemplate="%{customdata}<extra></extra>", showlegend=False))

    # mean lines (both axes) + Rule-of-40 = 40 reference
    fig.add_hline(y=avg_y, line=dict(width=1, color=theme.INK_3, dash="dash"), opacity=0.6)
    fig.add_vline(x=avg_x, line=dict(width=1, color=theme.INK_3, dash="dash"), opacity=0.6)
    fig.add_vline(x=40, line=dict(width=1.2, color=theme.UP, dash="dot"), opacity=0.7)
    # avg-EV/Sales label on the RIGHT edge (the left edge collides with ORCL)
    fig.add_annotation(xref="paper", x=0.995, y=avg_y, yref="y", showarrow=False,
                       text=(f"均值 {avg_y:.1f}x" if prefer_cn else f"Avg {avg_y:.1f}x"),
                       font=dict(size=10, color=theme.INK_3), xanchor="right", yshift=9,
                       bgcolor=theme.PAPER, opacity=0.85)
    fig.add_annotation(x=avg_x, yref="paper", y=0.01, showarrow=False,
                       text=(f"均值 {avg_x:.0f}%" if prefer_cn else f"Avg {avg_x:.0f}%"),
                       font=dict(size=10, color=theme.INK_3), yanchor="bottom", xshift=3,
                       bgcolor=theme.PAPER, opacity=0.85)
    fig.add_annotation(x=40, yref="paper", y=0.99, showarrow=False, text="Rule of 40",
                       font=dict(size=10, color=theme.UP_DEEP), xanchor="left",
                       yanchor="top", xshift=3)

    xl = x_label or ("Rule of 40 = 营收增速 + FCF Margin" if prefer_cn
                     else "Rule of 40 = rev growth + FCF margin")
    yl = y_label or ("EV / Sales（对数）" if prefer_cn else "EV / Sales (log)")
    fig.update_layout(title=_clean_title(title), height=600,
                      margin=dict(l=72, r=84, t=58, b=72))
    fig = theme.style_plotly(fig)
    # log y ticks at human-friendly multiples; clamp top to next tick above the max.
    _tv = [v for v in (1, 2, 3, 5, 10, 20, 30, 50, 80, 120) if v <= y_hi * 1.25]
    # hovermode AFTER style_plotly (which forces 'x unified' — that x-header was the
    # raw "43.2956%" George flagged); 'closest' = one clean per-point tooltip.
    fig.update_layout(
        hovermode="closest",
        xaxis=dict(title=dict(text=xl, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), ticksuffix="%",
                   tickformat=".0f", hoverformat=".1f", range=[x_lo - 12, x_hi + 15]),
        yaxis=dict(type="log", title=dict(text=yl, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), ticksuffix="x",
                   tickmode="array", tickvals=_tv, hoverformat=".1f",
                   range=[math.log10(0.9), math.log10(y_hi * 1.3)]),
    )
    return fig
