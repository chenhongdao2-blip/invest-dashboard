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


def index_compare_chart(
    hero: pd.Series,
    peers: dict[str, pd.Series],
    *,
    hero_name: str,
    title: str = "",
    ylabel: str = "Rebased (start=100)",
    height: int = 360,
    peer_styles: dict[str, dict] | None = None,
) -> tuple[go.Figure | None, dict | None]:
    """Rebased=100 comparison of one 'hero' index vs peer index/indices.

    `height` lets the caller drop subsidiary half-width panels (e.g. 260) below the
    full-width hero (360) so the visual hierarchy reads hero → supporting pair.

    Healthcare-analyst framing: the hero (a healthcare index — HSHCI / NBI / S&P
    HC) is the solid CMSI-red emphasis line; peers (broad market) are muted-grey
    dashed/dotted, distinguished by STYLE not color (DESIGN.md §4). All series are
    inner-joined on common trading days and rebased to 100 at the first common
    date (the anchor) — never each series' own start — so no spurious start-gap.

    `peer_styles` (optional) overrides the muted-grey default per peer (keyed by the
    peer's display name) with {"color", "dash", "width"} — used for cross-sector
    panels (e.g. a biotech-family peer in CMSI-red, an AI-hardware peer in teal) where
    STYLE-only differentiation isn't enough. Omitted/missing keys fall back to the
    grey dash-cycle, so the 4 existing healthcare panels render byte-identically.

    Returns (figure, meta) where meta = {"anchor": iso, "spreads": {peer: pp}}.
    `spreads[peer]` = hero_final − peer_final in points of rebased index, i.e. the
    hero's cumulative out/underperformance vs that peer since the anchor — the
    headline number for the caption. Figure is None on too little history (<5 pts).
    """
    if hero is None or hero.dropna().empty or not peers:
        return None, None
    frame: dict[str, pd.Series] = {hero_name: hero.dropna()}
    for name, ser in peers.items():
        if ser is not None and not ser.dropna().empty:
            frame[name] = ser.dropna()
    wide = pd.DataFrame(frame).dropna()          # inner-join → common trading days
    if len(wide) < 5 or wide.shape[1] < 2:
        return None, None
    rebased = wide.divide(wide.iloc[0]) * 100.0   # anchor = first common date
    anchor_iso = wide.index[0].date().isoformat()

    fig = go.Figure()
    dash_cycle = ["dash", "dot", "dashdot"]
    styles = peer_styles or {}
    peer_cols = [c for c in rebased.columns if c != hero_name]
    for i, col in enumerate(peer_cols):
        s = styles.get(col, {})
        fig.add_trace(go.Scatter(
            x=rebased.index, y=rebased[col], mode="lines", name=col,
            line=dict(width=s.get("width", 1.4), color=s.get("color", theme.INK_3),
                      dash=s.get("dash", dash_cycle[i % len(dash_cycle)])),
            hovertemplate="%{x|%Y-%m-%d}<br>" + col + " %{y:.1f}<extra></extra>",
        ))
    # Hero on top — solid CMSI-red emphasis.
    fig.add_trace(go.Scatter(
        x=rebased.index, y=rebased[hero_name], mode="lines", name=hero_name,
        line=dict(width=2.0, color=theme.CMSI_RED),
        hovertemplate="%{x|%Y-%m-%d}<br>" + hero_name + " %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(title=_clean_title(title), yaxis_title=ylabel, height=height)
    fig.add_hline(y=100, line=dict(width=1, color=theme.INK_3, dash="dash"), opacity=0.4)
    spreads = {c: float(rebased[hero_name].iloc[-1] - rebased[c].iloc[-1]) for c in peer_cols}
    return theme.style_plotly(fig), {"anchor": anchor_iso, "spreads": spreads}


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


# ── HK IPO 打新 backtest charts (static cross-section; teal up / red down) ──

# Tier → discrete marker color (4 tiers, semantics consistent with the site).
_IPO_TIER_COLORS = {
    "重点申购+": theme.UP_DEEP,    # 深 teal
    "推荐申购": theme.UP,          # teal
    "谨慎申购": "#a07a2c",         # amber (FT muted)
    "不申购": theme.INK_3,         # grey
}


def ipo_score_scatter(
    df: pd.DataFrame,
    *,
    score_col: str = "score",
    ret_col: str = "ret_pct",
    tier_col: str = "tier",
    name_col: str = "name",
    code_col: str = "code",
    rho_text: str = "",
    title: str = "",
    x_label: str = "Score",
    y_label: str = "Day-1 %",
    trend_label: str = "OLS trend",
    tier_label_fn=None,
    hover_fn=None,
) -> go.Figure:
    """Score × day-1-return scatter for the IPO backtest (listed names only).

    Points colored by tier (discrete). Day-1 sign is encoded by marker FILL:
    up = solid tier-color, down = solid red (symmetric weight) so the breakers
    keep the teal/red signal. An OLS trend line (dashed, light grey —
    deliberately NOT a strong solid line, to avoid implying a strong
    correlation) is overlaid, and the Spearman ρ is annotated top-right (the
    honest alpha of the page).

    When `hover_fn` is passed it is called per-row and wins over `name_col` /
    `code_col`; the caller must therefore have already renamed its display name
    column to whatever `hover_fn` reads (the page renames `name_cn` → `name`).
    """
    fig = go.Figure()
    if df is None or df.empty:
        return theme.style_plotly(fig)
    work = df.copy()
    tier_label_fn = tier_label_fn or (lambda t: str(t))

    # --- OLS trend line (least squares; dashed light grey, drawn UNDER points) ---
    x = work[score_col].astype(float).to_numpy()
    y = work[ret_col].astype(float).to_numpy()
    if len(x) >= 2 and float(x.std()) > 0:
        import numpy as _np
        slope, intercept = _np.polyfit(x, y, 1)
        xs = _np.array([x.min(), x.max()])
        fig.add_trace(go.Scatter(
            x=xs, y=slope * xs + intercept, mode="lines", name=trend_label,
            line=dict(width=1.3, color=theme.INK_3, dash="dash"), opacity=0.6,
            hoverinfo="skip",
        ))

    # --- One marker trace per tier (discrete legend); up=solid, down=hollow-red ---
    for tier in work[tier_col].dropna().unique():
        sub = work[work[tier_col] == tier]
        color = _IPO_TIER_COLORS.get(str(tier), theme.INK_3)
        up = sub[sub[ret_col] >= 0]
        dn = sub[sub[ret_col] < 0]
        if hover_fn is not None:
            up_hover = [hover_fn(r) for _, r in up.iterrows()]
            dn_hover = [hover_fn(r) for _, r in dn.iterrows()]
        else:
            up_hover = dn_hover = None
        if not up.empty:
            fig.add_trace(go.Scatter(
                x=up[score_col], y=up[ret_col], mode="markers",
                name=tier_label_fn(tier),
                marker=dict(size=11, color=color, line=dict(width=1, color=theme.PAPER)),
                text=up_hover, hovertemplate="%{text}<extra></extra>" if up_hover else None,
                legendgroup=str(tier),
            ))
        if not dn.empty:
            # 破发点: keep the TIER FILL colour (so a 推荐档 breaker like 馭勢 stays
            # teal — NOT recoloured red, which the 4-way review flagged as making
            # the model look like it "recommended a破发股"). The day-1 break is
            # flagged by a bold RED RING instead: tier semantics preserved + break
            # still salient. Merged into the tier legend item (no dup entry).
            fig.add_trace(go.Scatter(
                x=dn[score_col], y=dn[ret_col], mode="markers",
                name=tier_label_fn(tier),
                marker=dict(size=12, color=color,
                            line=dict(width=2.5, color=theme.DOWN)),
                text=dn_hover, hovertemplate="%{text}<extra></extra>" if dn_hover else None,
                legendgroup=str(tier), showlegend=up.empty,
            ))

    fig.update_layout(
        title=_clean_title(title),
        xaxis_title=x_label, yaxis_title=y_label, height=460,
    )
    # Honest-alpha annotation: Spearman ρ top-right (not significant).
    if rho_text:
        # TOP-LEFT (not top-right): the highest-score / highest-return point
        # (曦智 8.3 / +384%) sits in the top-right corner, so an opaque box there
        # occludes it. Top-left is empty (low scores never post the top returns).
        fig.add_annotation(
            xref="paper", yref="paper", x=0.01, y=0.98,
            xanchor="left", yanchor="top", showarrow=False,
            text=rho_text, font=dict(size=12, color=theme.INK_2),
            bgcolor=theme.PAPER, bordercolor=theme.PAPER_EDGE, borderwidth=1,
            borderpad=4, opacity=0.92,
        )
    fig = theme.style_plotly(fig)
    # Compliance: X tick ≥11, Y label ≥12, title ≥14. tickfont set explicitly
    # (not relying on template inheritance); score axis tickformat=".1f".
    fig.update_layout(
        xaxis=dict(title=dict(text=x_label, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), tickformat=".1f"),
        yaxis=dict(title=dict(text=y_label, font=dict(size=12, color=theme.INK_2)),
                   tickfont=dict(size=11, color=theme.INK_2), tickformat=",.0f"),
        title=dict(font=dict(size=15, color=theme.INK)),
    )
    return fig


def ipo_intraday_facets(
    paths: list[dict],
    *,
    ncols: int = 4,
    title: str = "",
    use_hover: bool = False,
) -> go.Figure:
    """Small-multiples grid of listing-day intraday paths (opening bar = 100).

    `paths`: list of dicts, each {'title': str, 'x': index, 'y': normalized
    series (open-bar=100), 'up': bool}. Line color keys off `up` = FULL day-1
    sign (teal up / red down) — NOT the intraday path's own sign (which would
    contradict the labelled day-1 return). Grid is decluttered: no legend, no
    gridlines, no x tick labels; a faint y=100 baseline per cell. Shared y range
    so amplitudes are comparable across names.
    """
    from plotly.subplots import make_subplots

    n = len(paths)
    if n == 0:
        return theme.style_plotly(go.Figure())
    nrows = (n + ncols - 1) // ncols
    subplot_titles = [p.get("title", "") for p in paths]
    fig = make_subplots(
        rows=nrows, cols=ncols, subplot_titles=subplot_titles,
        vertical_spacing=0.09, horizontal_spacing=0.04,
    )
    for i, p in enumerate(paths):
        r, c = i // ncols + 1, i % ncols + 1
        color = theme.UP if p.get("up", True) else theme.DOWN
        ht = None
        if use_hover and p.get("hover"):
            ht = p["hover"]
        fig.add_trace(go.Scatter(
            x=list(range(len(p["y"]))), y=list(p["y"]), mode="lines",
            line=dict(width=1.4, color=color), showlegend=False,
            text=ht, hovertemplate="%{text}<extra></extra>" if ht else None,
        ), row=r, col=c)
        # faint 发行价 breakeven baseline (=0%); the path is now plotted as
        # "% vs offer price" so it terminates at the labelled full day-1 return.
        fig.add_hline(y=0, line=dict(width=0.8, color=theme.INK_4, dash="dot"),
                      opacity=0.6, row=r, col=c)

    fig = theme.style_plotly(fig)
    # Declutter x (intraday tick index is meaningless): hide ticks/grid.
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False,
                     linecolor=theme.PAPER_RULE)
    # KEEP y tick labels so the move's magnitude is readable (=100 open bar);
    # only the gridlines are dropped to reduce clutter.
    fig.update_yaxes(showgrid=False, showticklabels=True, zeroline=False,
                     tickfont=dict(size=9, color=theme.INK_3),
                     linecolor=theme.PAPER_RULE)
    # Compliant subplot-title font (≥11pt); title ≥14. Color each subplot title
    # by its day-1 sign (teal up / red down) so it matches its line color; the
    # subplot titles occupy the first len(paths) annotations (the figure-level
    # title is set separately below and is not in this list).
    for i, ann in enumerate(fig.layout.annotations):
        if i < len(paths):
            color = theme.UP if paths[i].get("up", True) else theme.DOWN
        else:
            color = theme.INK_2
        ann.font = dict(size=11, color=color, family=theme.FONT_STACK)
    fig.update_layout(
        title=dict(text=_clean_title(title), font=dict(size=15, color=theme.INK)),
        height=180 * nrows + 60, showlegend=False,
        margin=dict(l=24, r=24, t=92, b=24), hovermode="closest",
    )
    return fig


def capital_dual_axis_chart(
    df: pd.DataFrame,
    *,
    x_col: str,
    bar_col: str,
    line_col: str,
    bar_unit: str = "USD mn",
    title: str = "",
    bar_label: str = "",
    line_label: str = "",
) -> go.Figure:
    """ED-Funding signature chart: capital (bars, left axis) + deal count (line,
    right axis). The sell-side funding-tracker idiom — lets 'dollars up but deal
    count flat' (large-deal concentration) read at a glance.

    df: a period-indexed-or-columned frame; `x_col` is the period (Timestamp or
    label), `bar_col` the capital series (already in the unit named by `bar_unit`),
    `line_col` the deal count. Bars are teal (theme.UP — gross magnitudes, not signed
    returns, so the up/down convention does not apply); the count line is muted ink.

    NOTE on units: `bar_unit` is passed by the caller per-series (总额=USD bn,
    sub-segments=USD mn) and used for the bar hover + axis title — the chart never
    hardcodes a unit, so the medtech panel can't mislabel by 1000x.
    """
    fig = go.Figure()
    if df is None or df.empty:
        return theme.style_plotly(fig)
    x = df[x_col]
    fig.add_trace(go.Bar(
        x=x, y=df[bar_col], name=bar_label or bar_col,
        marker_color=theme.UP, marker_line_width=0, yaxis="y",
        hovertemplate="%{x|%Y-%m}<br>%{y:,.0f} " + bar_unit + "<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df[line_col], name=line_label or line_col,
        mode="lines+markers", yaxis="y2",
        line=dict(width=1.8, color=theme.INK_3),
        marker=dict(size=5, color=theme.INK_3),
        hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(title=_clean_title(title), height=400, barmode="group")
    fig = theme.style_plotly(fig)
    # style_plotly merges PLOTLY_LAYOUT.yaxis (incl. tickformat ',.2f') but does NOT
    # touch yaxis2 — set the left-axis integer format + the full right axis here so
    # the overlay, side, and compliant fonts (≥11 tick / ≥12 title) are authoritative.
    fig.update_layout(
        yaxis=dict(
            title=dict(text=bar_label or bar_unit, font=dict(size=12, color=theme.INK_2)),
            tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2),
        ),
        yaxis2=dict(
            title=dict(text=line_label, font=dict(size=12, color=theme.INK_2)),
            overlaying="y", side="right", showgrid=False,
            tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2),
            linecolor=theme.INK, linewidth=1,
        ),
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


def hshci_history_chart(
    dates: list,
    closes: list,
    annotations: list[dict],     # [{x, y, text, ax, ay}] — ax/ay = label px offset
    *,
    title: str = "",
    ylabel: str = "Index level",
    height: int = 380,
) -> go.Figure:
    """Single calendar-time line of an index's absolute level, with milestone labels.

    Used for HSHCI's full-cycle context (2021.7 high → 2024 trough → 2025 recovery →
    pullback). CMSI-red line + faint fill; annotation callouts at start/trough/peak/
    now. Absolute points (not rebased), so no up/down colour convention applies.
    """
    fig = go.Figure()
    if not dates:
        return theme.style_plotly(fig)
    fig.add_trace(go.Scatter(
        x=list(dates), y=list(closes), mode="lines",
        line=dict(color=theme.CMSI_RED, width=2.4),
        fill="tozeroy", fillcolor="rgba(200,16,46,0.05)",
        hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}<extra></extra>", name="HSHCI",
    ))
    for a in annotations:
        fig.add_trace(go.Scatter(
            x=[a["x"]], y=[a["y"]], mode="markers",
            marker=dict(color=theme.CMSI_RED, size=8), showlegend=False,
            hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}<extra></extra>",
        ))
        fig.add_annotation(
            x=a["x"], y=a["y"], text=a["text"], showarrow=True, arrowhead=0,
            arrowwidth=1, arrowcolor=theme.INK_3, ax=a.get("ax", 0), ay=a.get("ay", -28),
            font=dict(size=10, color=theme.INK_2), align="left",
        )
    fig.update_layout(title=_clean_title(title), height=height, showlegend=False)
    fig = theme.style_plotly(fig)
    fig.update_layout(
        yaxis=dict(title=dict(text=ylabel, font=dict(size=12, color=theme.INK_2)),
                   tickformat=",.0f", tickfont=dict(size=11, color=theme.INK_2)),
        xaxis=dict(tickfont=dict(size=11, color=theme.INK_2), dtick="M12", tickformat="%Y"),
        margin=dict(l=8, r=20, t=64, b=36),
    )
    return fig


def funding_yoy_bar(
    rows: list[dict],
    *,
    label_key: str = "label",
    cur_key: str = "cur_bn",
    prior_key: str = "prior_bn",
    cur_name: str = "Q1 2026",
    prior_name: str = "Q1 2025",
    title: str = "",
    ylabel: str = "USD bn",
) -> go.Figure:
    """Grouped YoY bar for the venture / VC family (prior-year vs current).

    Intended ONLY for similar-magnitude segments (the $3-9B venture/digital-health
    set) so bars stay comparable — do NOT mix in M&A ($41B) / licensing ($83B) /
    IPO ($1.8B), whose magnitudes + measures differ (non-additive). Prior year is
    muted ink, current is teal; gross magnitudes so the up/down convention does not
    apply.
    """
    fig = go.Figure()
    if not rows:
        return theme.style_plotly(fig)
    labels = [r[label_key] for r in rows]
    fig.add_trace(go.Bar(
        x=labels, y=[r[prior_key] for r in rows], name=prior_name,
        marker_color=theme.INK_3, marker_line_width=0,
        hovertemplate="%{x}<br>%{y:.1f} " + ylabel + "<extra>" + prior_name + "</extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels, y=[r[cur_key] for r in rows], name=cur_name,
        marker_color=theme.UP, marker_line_width=0,
        hovertemplate="%{x}<br>%{y:.1f} " + ylabel + "<extra>" + cur_name + "</extra>",
    ))
    fig.update_layout(title=_clean_title(title), height=360, barmode="group")
    fig = theme.style_plotly(fig)
    fig.update_layout(
        yaxis=dict(title=dict(text=ylabel, font=dict(size=12, color=theme.INK_2)),
                   tickformat=",.1f", tickfont=dict(size=11, color=theme.INK_2)),
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


def model_dcf_sensitivity(dcf, *, prefer_cn=True):
    """WACC×TG → TP heatmap. Sequential teal ramp (deep = higher TP); a TP grid
    is NOT market up/down, so it deliberately does NOT use the diverging teal/red."""
    s = dcf["sensitivity"]
    x = [f"{v:.1%}" for v in s["x"]]
    y = [f"{v:.1%}" for v in s["y"]]
    fig = go.Figure(go.Heatmap(
        x=x, y=y, z=s["grid"],
        colorscale=[[0, theme.PAPER], [0.5, theme.UP_TINT], [1, theme.UP_DEEP]],
        text=[[f"{v:.0f}" if v is not None else "" for v in row] for row in s["grid"]],
        texttemplate="%{text}", textfont=dict(size=10, family=theme.FONT_MONO),
        hovertemplate="WACC %{y} · TG %{x} · TP $%{z:.0f}<extra></extra>",
        colorbar=dict(title="TP $")))
    fig.update_layout(height=360,
                      xaxis_title=("永续增长率" if prefer_cn else "Terminal Growth"),
                      yaxis_title="WACC", yaxis=dict(autorange="reversed"))
    bx, by = s.get("base_x"), s.get("base_y")
    if bx in s["x"] and by in s["y"]:
        fig.add_annotation(x=f"{bx:.1%}", y=f"{by:.1%}", text="◆", showarrow=False,
                           font=dict(size=15, color=theme.CMSI_RED))
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
