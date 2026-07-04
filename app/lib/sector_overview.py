"""板块总览 Wave-2 Broadsheet Reskin
================================================

医疗/AI/板块页的「基准」多周期表 + 「涨跌榜」Wave-2 报纸精修:
- 新增 `masthead()`:完整 broadsheet masthead（双页各自传参，全参数化）。
- `benchmark_table()`:玻璃卡容器（rgba .5/blur14/白边，无顶 accent），透明 th + 墨 1.5px
  底线，行 hover rgba(26,26,26,.045)，节标+色阶图例。
- `movers()`:玻璃容器 + 双语列头 + 实符号 d1（N-9，替 abs()）+ rgba 轨道色。
- DOWN 颜色改 page-scope #c8102e（theme.DOWN 全局不动，SOVR13 先例）。

渲染机制不迁：纯 st.markdown(unsafe_allow_html)，无 iframe / echarts / JS。
Sparkline 保持 inline SVG（cross-cutting INVARIANT #4：多小图面禁换 echarts）。
@keyframes pulseDot + tr hover 规则经 <style> 块注入，idempotent。

双页共用（2_Healthcare.py + a2_ai_overview.py）—— 验收两页均需核（SOVR1）。
调用页各自调 `theme.page_radial_wash(1240)` 提供 blur 垫底（SOVR4/D5，非本模块职责）。

典型调用（wave-2 之后）:
    from lib import sector_overview as so

    theme.page_radial_wash(1240)           # 调用页自行注入 wash

    so.masthead(
        title="板块总览 · 医疗健康",
        chip="HEALTHCARE",
        subtitle="基准 ETF 分档表现 × 涨跌榜 · 30 日趋势 · 相对标普超额",
        asof="2026-06-30",
        source="Yahoo Finance cron EOD",
        prefer_cn=True,
    )
    so.benchmark_table([
        {"tk": "XLV", "name": "医疗保健精选行业",
         "periods": {"1日": 3.0, "5日": 7.8, "1月": 8.2, "3月": 10.5, "YTD": 4.0},
         "rel_sp": -3.2, "spark": [...30 raw closes...]},
    ], source="来源 Yahoo Finance cron EOD · 截至 2026-06-30 · 仅供参考")

    so.movers(
        gainers=[{"tk": "XBI", "name": "生物科技", "last": 70.70, "d1": 20.1}],
        losers=[{"tk": "3696 HK", "name": "英矽智能", "last": 38.22, "d1": -16.0}],
        window="1 日",
        prefer_cn=True,
    )

周期列顺序由第一行 periods 的 key 顺序决定（用 dict 保序；统一传同一组 key）。
rel_cap / mov_cap 控制色阶与发散条饱和上限（默认 ±25pp / 22pp）。
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import theme as t

# ── Page-scope DOWN color for wave-2 reskin surfaces (SOVR13) ────────────────
# theme.DOWN stays #cc0000 (signal-red, global token unchanged).
# This module uses brand red #c8102e per §0 D2 — same pattern as candlestick
# module (_DOWN = theme.CMSI_RED). The per-surface constant keeps the global clean.
_DOWN = t.CMSI_RED       # "#c8102e"
_DOWN_RGB = "200,16,46"  # for rgba() tint/track calculations

REL_CAP = 25.0  # 相对条 / 期间色阶饱和上限 ±pp  (spec: cap 25 → 50%)
MOV_CAP = 22.0  # mover 动量条饱和上限 (spec: cap 22)


# ── CSS injection (pulseDot keyframes + tr hover) ────────────────────────────

def _inject_css() -> None:
    """Inject @keyframes pulseDot + sovr-row hover rule.
    Idempotent — Streamlit rerenders call this every time, same CSS overwrites itself.
    """
    st.markdown(
        """<style>
@keyframes pulseDot {
  0%,100% { opacity:1; transform:scale(1); }
  50% { opacity:.35; transform:scale(.82); }
}
tr.sovr-row:hover { background:rgba(26,26,26,.045) !important; }
</style>""",
        unsafe_allow_html=True,
    )


# ── Internal helpers ─────────────────────────────────────────────────────────

def _tint(v, cap: float = REL_CAP) -> str:
    """Diverging background tint: teal=up / #c8102e=down, alpha capped at 0.16.
    Dead-zone: |v| < 0.05 returns transparent (SOVR9).
    """
    if v is None or abs(v) < 0.05:
        return "transparent"
    a = min(abs(v) / cap, 1.0) * 0.16
    rgb = "13,118,128" if v > 0 else _DOWN_RGB
    return f"rgba({rgb},{a:.3f})"


def _pct_cell(v) -> str:
    """Period return cell: ▲/▼/· glyph + signed pct + diverging tint bg (SOVR9)."""
    gly = "▲" if v > 0 else ("▼" if v < 0 else "·")
    sign = "+" if v > 0 else ""
    col = t.UP if v > 0 else (_DOWN if v < 0 else t.INK_3)
    return (
        f'<td style="text-align:right;white-space:nowrap;padding:0 12px;'
        f'border-bottom:1px solid {t.PAPER_RULE};background:{_tint(v)}">'
        f'<span style="color:{col};font-weight:600">{gly} {sign}{v:.1f}%</span></td>'
    )


def _spark_svg(vals, w: int = 110, h: int = 28, pad: int = 3) -> tuple[str, bool]:
    """30D sparkline: polyline stroke-width 1.5 non-scaling + endpoint circle r2.2.
    Geometry identical to wave-1 _spark_svg; only down color switches to _DOWN (SOVR9).
    Returns (svg_html, is_up).
    """
    vals = [float(x) for x in (vals or [])]
    if len(vals) < 2:
        return f'<span style="color:{t.INK_3}">—</span>', True
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    step = (w - 2) / (len(vals) - 1)
    pts = " ".join(
        f"{1 + i * step:.1f},{pad + (h - 2 * pad) - (v - lo) / rng * (h - 2 * pad):.1f}"
        for i, v in enumerate(vals)
    )
    up = vals[-1] >= vals[0]
    color = t.UP if up else _DOWN
    lx, ly = pts.rsplit(" ", 1)[-1].split(",")
    svg = (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:{w}px;height:26px;display:block;vertical-align:middle">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<circle cx="{lx}" cy="{ly}" r="2.2" fill="{color}"/></svg>'
    )
    return svg, up


def _rel_bar(v, cap: float = REL_CAP) -> str:
    """Center-diverging relative-to-SPX bar (SOVR9).
    Track: #f4ead9 h14; center 1px #d4c4b0; fill extends from center to ±50%.
    Down color: _DOWN (#c8102e). Geometry unchanged from wave-1.
    """
    w = min(abs(v) / cap, 1.0) * 50
    color = t.UP if v >= 0 else _DOWN
    fill = f"left:50%;width:{w:.1f}%" if v >= 0 else f"right:50%;width:{w:.1f}%"
    gly = "▲ +" if v >= 0 else "▼ "
    return (
        f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">'
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<div style="flex:1;position:relative;height:14px;background:#f4ead9">'
        f'<div style="position:absolute;top:0;bottom:0;left:50%;width:1px;'
        f'background:{t.PAPER_EDGE}"></div>'
        f'<div style="position:absolute;top:2px;bottom:2px;{fill};'
        f'background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:700;'
        f'color:{color};width:54px;text-align:right">{gly}{v:.1f}</span>'
        f'</div></td>'
    )


# ── Public API ───────────────────────────────────────────────────────────────

def masthead(
    title: str,
    chip: str,
    subtitle: str,
    *,
    asof: str | None = None,
    source: str | None = None,
    prefer_cn: bool = True,
) -> None:
    """Broadsheet masthead (wave-2 新增块, SOVR2/SOVR3).

    Parameters
    ----------
    title    : e.g. "板块总览 · 医疗健康" / "板块总览 · AI 科技"
    chip     : domain label, e.g. "HEALTHCARE" / "AI TECH"
    subtitle : caption line, e.g. "基准 ETF 分档表现 × 涨跌榜 · 30 日趋势 · 相对标普超额"
    asof     : date string, e.g. "2026-06-30" — appears in dateline
    source   : provenance string, e.g. "Yahoo Finance cron EOD"
    prefer_cn: True → "EOD · 收盘", False → "EOD · CLOSE" (SOVR3, D3 compliant)

    Design: left = red bar 5×48 + title 30px/700 + chip + subtitle.
            right = teal pulseDot 8px + EOD label + dateline mono 11.
            border-bottom 2px #1a1a1a, pb16.
    Note: caller page must have called theme.page_radial_wash(1240) first so
          backdrop-filter has something to blur (SOVR4/D5).
    """
    _inject_css()
    eod_label = "EOD · 收盘" if prefer_cn else "EOD · CLOSE"

    # Dateline: "截至 {asof} · {source}" or en equivalent
    dateline_parts: list[str] = []
    if asof:
        prefix = "截至" if prefer_cn else "As of"
        dateline_parts.append(f"{prefix} {_esc(asof)}")
    if source:
        dateline_parts.append(_esc(source))
    dateline_html = (
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;'
        f'color:{t.INK_3};margin-top:5px">{"  ·  ".join(dateline_parts)}</div>'
    ) if dateline_parts else ""

    right_col = (
        f'<div style="text-align:right;display:flex;flex-direction:column;'
        f'align-items:flex-end">'
        # teal pulseDot + EOD label (SOVR3: cyan semantic = EOD snapshot, not live)
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<div style="width:8px;height:8px;border-radius:50%;background:{t.UP};'
        f'flex:none;animation:pulseDot 1.5s ease-in-out infinite"></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.UP};font-weight:600">'
        f'{_esc(eod_label)}</span></div>'
        f'{dateline_html}'
        f'</div>'
    )

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-end;'
        f'gap:24px;border-bottom:2px solid {t.INK};padding-bottom:16px">'
        # left: red bar + title block
        f'<div style="display:flex;align-items:flex-start;gap:12px">'
        f'<div style="width:5px;height:48px;background:{t.CMSI_RED};'
        f'border-radius:1px;flex:none;margin-top:2px"></div>'
        f'<div>'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
        f'<div style="font-family:{t.FONT_DISPLAY};font-size:30px;font-weight:700;'
        f'letter-spacing:-0.01em;color:{t.INK};line-height:1.1">{_esc(title)}</div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:13px;font-weight:600;'
        f'color:{t.INK_3};border:1px solid {t.PAPER_EDGE_SOFT};padding:3px 9px;'
        f'border-radius:2px">{_esc(chip)}</span>'
        f'</div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;letter-spacing:.08em;'
        f'color:{t.INK_3};margin-top:6px">{_esc(subtitle)}</div>'
        f'</div></div>'
        # right
        f'{right_col}'
        f'</div>',
        unsafe_allow_html=True,
    )


def benchmark_table(rows: list[dict], *, source: str | None = None) -> None:
    """基准多周期表 + sparkline + 发散色阶 + 相对标普发散条 (wave-2 glass reskin).

    Row dict: {tk, name, periods:{label:pct,...}, rel_sp(float pp), spark:[~30 closes]}.
    Period column order follows first row's periods key order (caller passes identical keys).
    """
    _inject_css()
    if not rows:
        return
    periods = list(rows[0]["periods"].keys())

    # ── Section header + right-float color legend (SOVR5) ─────────────────
    legend = (
        f'<div style="display:flex;align-items:center;gap:5px;margin-left:auto">'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;font-weight:600;'
        f'color:{_DOWN}">跌</span>'
        f'<div style="width:120px;height:9px;border:1px solid {t.PAPER_EDGE};'
        f'background:linear-gradient(to right,{_DOWN},#f7d9d9,#fff1e5,#d9e8e6,{t.UP})">'
        f'</div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;font-weight:600;'
        f'color:{t.UP}">涨</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:9px;color:{t.INK_3};'
        f'margin-left:4px">期间收益色阶</span>'
        f'</div>'
    )
    sec_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:22px 0 10px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block;border-radius:1px;flex:none"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.INK};font-weight:600">'
        f'基准 · Benchmark ETF</span>'
        f'{legend}</div>'
    )

    # ── Table header cells (SOVR7): transparent bg, mono gray, ink 1.5px bottom ──
    _TH = (
        f"font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.08em;"
        f"text-transform:uppercase;font-weight:600;color:{t.INK_3};"
        f"background:transparent;padding:9px 12px;"
        f"border-bottom:1.5px solid {t.INK};"
    )

    def _th(label: str, align: str = "right") -> str:
        # no vertical separators (SOVR7: 零竖分隔线)
        return f'<th style="{_TH}text-align:{align}">{_esc(label)}</th>'

    head = (
        _th("Ticker", "left")
        + _th("名称", "left")
        + _th("趋势 30D", "left")
        + "".join(_th(p) for p in periods)
        + _th("相对标普 PP", "center")
    )

    # ── Table body rows (SOVR8/SOVR9) ────────────────────────────────────
    body: list[str] = []
    for r in rows:
        svg, _ = _spark_svg(r.get("spark"))
        cells = (
            # Ticker: mono 12/700 (SOVR8)
            f'<td style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};'
            f'font-size:12px;letter-spacing:.04em;text-align:left;padding:0 12px;'
            f'height:46px;border-bottom:1px solid {t.PAPER_RULE}">{_esc(r["tk"])}</td>'
            # 名称: 500 weight (SOVR8)
            f'<td style="text-align:left;color:{t.INK};font-weight:500;padding:0 12px;'
            f'border-bottom:1px solid {t.PAPER_RULE}">{_esc(r["name"])}</td>'
            # sparkline SVG
            f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">{svg}</td>'
            + "".join(_pct_cell(r["periods"][p]) for p in periods)
            + _rel_bar(r["rel_sp"])
        )
        # class="sovr-row" enables the CSS hover rule injected by _inject_css()
        body.append(f'<tr class="sovr-row">{cells}</tr>')

    src_html = (
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};'
        f'margin-top:8px">{_esc(source)}</div>'
    ) if source else ""

    # ── Glass container (SOVR6): rgba .5 + blur14 + white border, no top accent ──
    glass_style = (
        "background:rgba(255,255,255,.5);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "border:1px solid rgba(255,255,255,.7);"
        "padding:2px 16px 8px;overflow:hidden;"
    )
    st.markdown(
        f"{sec_head}"
        f'<div style="{glass_style}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;'
        f'font-variant-numeric:tabular-nums lining-nums;font-family:{t.FONT_DISPLAY}">'
        f'<thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        f'</table></div>{src_html}',
        unsafe_allow_html=True,
    )


def _mover_row(m: dict, up: bool) -> str:
    """Single mover row with momentum bar and real-signed d1 (N-9, SOVR10).

    N-9: design shows '▼ -16.0%' — negative sign preserved (replacing old abs()).
    Row layout: tk w64 / name flex / last w60 / bar 84×16 / d1 w58.
    """
    color = t.UP if up else _DOWN
    track = "rgba(13,118,128,.10)" if up else f"rgba({_DOWN_RGB},.08)"
    bar_anchor = "left:0" if up else "right:0"
    w = min(abs(m["d1"]) / MOV_CAP, 1.0) * 100
    # N-9: gainers "▲ +x.x%", losers "▼ -x.x%" (d1 is already negative for losers)
    if up:
        d1_display = f"▲ +{abs(m['d1']):.1f}%"
    else:
        d1_display = f"▼ {m['d1']:.1f}%"   # m['d1'] < 0, %.1f keeps the minus sign
    return (
        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;'
        f'border-bottom:1px solid {t.PAPER_RULE}">'
        f'<span style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};'
        f'font-size:12px;width:64px;flex:none">{_esc(m["tk"])}</span>'
        f'<span style="color:{t.INK};font-size:13px;flex:1;min-width:0;overflow:hidden;'
        f'text-overflow:ellipsis;white-space:nowrap">{_esc(m["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;color:{t.INK_2};'
        f'width:60px;text-align:right;flex:none">{m["last"]:.2f}</span>'
        f'<div style="width:84px;flex:none;position:relative;height:16px;'
        f'background:{track}">'
        f'<div style="position:absolute;{bar_anchor};top:2px;bottom:2px;'
        f'width:{w:.0f}%;background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:13px;font-weight:700;'
        f'color:{color};width:58px;text-align:right;flex:none">'
        f'{_esc(d1_display)}</span></div>'
    )


def movers(
    *,
    gainers: list[dict],
    losers: list[dict],
    window: str = "1 日",
    prefer_cn: bool = True,
) -> None:
    """涨跌榜 — wave-2 glass reskin with bilingual column headers (SOVR10/SOVR14).

    Parameters
    ----------
    gainers   : [{tk, name, last, d1}, ...] — d1 in real signed percent
    losers    : [{tk, name, last, d1}, ...] — d1 negative for losers
    window    : period label, e.g. "1 日" / "1D"
    prefer_cn : True → subtitle in Chinese, False → English
    """
    _inject_css()
    # Section header subtitle
    subtitle = (
        f"{_esc(window)}涨跌幅前 10" if prefer_cn else f"Top 10 by {_esc(window)} change"
    )
    sec_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:34px 0 4px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block;border-radius:1px;flex:none"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.INK};font-weight:600">'
        f'涨跌榜 · Movers</span>'
        f'<span style="font-size:12px;color:{t.INK_3}">{subtitle}</span>'
        f'</div>'
    )

    # Glass container (same formula as benchmark_table, no padding per spec)
    glass_style = (
        "background:rgba(255,255,255,.5);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "border:1px solid rgba(255,255,255,.7);"
        "overflow:hidden;"
    )

    def _col_html(col_title: str, items: list[dict], up: bool, accent: str) -> str:
        # Column header: vertical bar 3×13 + mono 11/700/.1em bilingual label (SOVR10)
        col_head = (
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">'
            f'<span style="width:3px;height:13px;background:{accent};'
            f'display:inline-block;border-radius:1px;flex:none"></span>'
            f'<span style="font-family:{t.FONT_MONO};font-size:11px;font-weight:700;'
            f'letter-spacing:.1em;color:{accent}">{_esc(col_title)}</span></div>'
        )
        rows_html = "".join(_mover_row(m, up) for m in items)
        return (
            f'<div>{col_head}'
            f'<div style="{glass_style}">{rows_html}</div></div>'
        )

    # Bilingual column labels (CN · EN in one label — works for both lang modes)
    gain_title = "涨幅前 10 · GAINERS"
    lose_title = "跌幅前 10 · LOSERS"

    st.markdown(
        f"{sec_head}"
        f'<div style="display:grid;grid-template-columns:1fr 1fr;'
        f'gap:20px;margin-top:14px">'
        f'{_col_html(gain_title, gainers, True, t.UP)}'
        f'{_col_html(lose_title, losers, False, _DOWN)}'
        f'</div>',
        unsafe_allow_html=True,
    )
