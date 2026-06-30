"""板块总览美化 — 新模块 lib/sector_overview.py
================================================

医疗/AI/板块页的「基准」多周期表 + 「涨跌榜」升级:
- 基准表加 30 日趋势 sparkline 列(内联 SVG,表格保持 DOM/可排序)。
- 期间收益(1日/5日/1月/3月/YTD)发散热力色阶(≤16% tint,teal 涨/红 跌)。
- 「相对标普 PP」改成居中发散条(0 居中,跑赢右青/跑输左红)。
- 涨跌榜每行行内动量条。

纯 st.markdown(unsafe_allow_html),无 iframe / JS —— sparkline 用 SVG(贴合 ui._spark_svg,
表格要可排序就不能进 canvas)。色阶逻辑与 format.background_gradient_diverging 同源(teal/红)。

调用(在 pages/2_Healthcare.py / a*_ 板块页):
    from lib import sector_overview as so

    so.benchmark_table([
        {"tk":"XLV","name":"医疗保健精选行业",
         "periods":{"1日":3.0,"5日":7.8,"1月":8.2,"3月":10.5,"YTD":4.0},
         "rel_sp":-3.2, "spark":[...30 个收盘价...]},     # 原始价即可
        ...
    ], source="来源 Yahoo Finance cron EOD · 截至 2026-06-29 · 仅供参考")

    so.movers(
        gainers=[{"tk":"TECH","name":"生物科技","last":70.70,"d1":20.1}, ...],
        losers=[{"tk":"3696 HK","name":"英矽智能","last":38.22,"d1":-16.0}, ...],
        window="1 日",
    )

周期列顺序由第一行 periods 的 key 顺序决定(用 dict 保序;统一传同一组 key)。
rel_cap / sp_cap 控制发散色阶与相对条的饱和上限(默认 ±25pp)。
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import theme as t

REL_CAP = 25.0   # 相对条 / 期间色阶 饱和上限(±pp)


def _tint(v, cap: float = REL_CAP) -> str:
    if v is None or abs(v) < 0.05:
        return "transparent"
    a = min(abs(v) / cap, 1.0) * 0.16
    rgb = "13,118,128" if v > 0 else "204,0,0"
    return f"rgba({rgb},{a:.3f})"


def _pct_cell(v) -> str:
    gly = "▲" if v > 0 else ("▼" if v < 0 else "·")
    sign = "+" if v > 0 else ""
    col = t.UP if v > 0 else (t.DOWN if v < 0 else t.INK_3)
    return (
        f'<td style="text-align:right;white-space:nowrap;padding:0 12px;'
        f'border-bottom:1px solid {t.PAPER_RULE};background:{_tint(v)}">'
        f'<span style="color:{col};font-weight:600">{gly} {sign}{v:.1f}%</span></td>'
    )


def _spark_svg(vals, w=110, h=28, pad=3) -> tuple[str, bool]:
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
    color = t.UP if up else t.DOWN
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
    w = min(abs(v) / cap, 1.0) * 50
    color = t.UP if v >= 0 else t.DOWN
    fill = (f"left:50%;width:{w:.1f}%" if v >= 0 else f"right:50%;width:{w:.1f}%")
    gly = "▲ +" if v >= 0 else "▼ "
    return (
        f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">'
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<div style="flex:1;position:relative;height:14px;background:#f4ead9">'
        f'<div style="position:absolute;top:0;bottom:0;left:50%;width:1px;background:{t.PAPER_EDGE}"></div>'
        f'<div style="position:absolute;top:2px;bottom:2px;{fill};background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:700;color:{color};'
        f'width:54px;text-align:right">{gly}{v:.1f}</span></div></td>'
    )


def benchmark_table(rows: list[dict], *, source: str | None = None) -> None:
    """基准多周期表 + sparkline + 发散色阶 + 相对标普发散条。"""
    if not rows:
        return
    periods = list(rows[0]["periods"].keys())

    def th(label, align="right", first=False, last=False):
        br = f"border-right:1px solid {t.PAPER_EDGE};" if (first or last) else ""
        return (f'<th style="text-align:{align};background:{t.PAPER_BAND};color:{t.CMSI_RED};'
                f'font-size:10px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;'
                f'padding:9px 12px;border-bottom:1px solid {t.CMSI_RED};{br}">{_esc(label)}</th>')

    head = (th("Ticker", "left", first=True) + th("名称", "left") + th("趋势 30D", "left")
            + "".join(th(p) for p in periods[:-1]) + th(periods[-1], last=True)
            + th("相对标普 PP", "center"))

    body = []
    for r in rows:
        svg, _ = _spark_svg(r.get("spark"))
        cells = (
            f'<td style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};font-size:12px;'
            f'letter-spacing:.04em;text-align:left;padding:0 12px;height:46px;'
            f'border-bottom:1px solid {t.PAPER_RULE};border-right:1px solid {t.PAPER_EDGE}">{_esc(r["tk"])}</td>'
            f'<td style="text-align:left;color:{t.INK};font-weight:500;padding:0 12px;'
            f'border-bottom:1px solid {t.PAPER_RULE}">{_esc(r["name"])}</td>'
            f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">{svg}</td>'
            + "".join(_pct_cell(r["periods"][p]) for p in periods)
            + _rel_bar(r["rel_sp"])
        )
        body.append(f"<tr>{cells}</tr>")

    src = (f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:8px">'
           f'{_esc(source)}</div>') if source else ""
    st.markdown(
        f'<div style="border:1px solid {t.PAPER_EDGE};overflow:hidden"><table style="width:100%;'
        f'border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums lining-nums">'
        f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>{src}',
        unsafe_allow_html=True,
    )


def _mover_row(m: dict, up: bool) -> str:
    track = "#eef2ec" if up else "#f6ecec"
    color = t.UP if up else t.DOWN
    w = min(abs(m["d1"]) / 22, 1.0) * 100
    bar = (f'left:0;width:{w:.0f}%' if up else f'right:0;width:{w:.0f}%')
    gly = "▲ +" if up else "▼ "
    return (
        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;'
        f'border-bottom:1px solid {t.PAPER_RULE}">'
        f'<span style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};font-size:12px;'
        f'width:64px;flex:none">{_esc(m["tk"])}</span>'
        f'<span style="color:{t.INK};font-size:13px;flex:1;min-width:0;overflow:hidden;'
        f'text-overflow:ellipsis;white-space:nowrap">{_esc(m["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;color:{t.INK_2};width:60px;'
        f'text-align:right;flex:none">{m["last"]:.2f}</span>'
        f'<div style="width:84px;flex:none;position:relative;height:16px;background:{track}">'
        f'<div style="position:absolute;{bar};top:2px;bottom:2px;background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:13px;font-weight:700;color:{color};'
        f'width:58px;text-align:right;flex:none">{gly}{abs(m["d1"]):.1f}%</span></div>'
    )


def movers(*, gainers: list[dict], losers: list[dict], window: str = "1 日") -> None:
    """涨跌榜(行内动量条)。gainers/losers = [{tk,name,last,d1}, ...]。"""
    def col(title, items, up, accent):
        head = (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                f'<span style="width:3px;height:13px;background:{accent};display:inline-block"></span>'
                f'<span style="font-size:12px;font-weight:700;color:{accent};letter-spacing:.04em">{title}</span></div>')
        rows = "".join(_mover_row(m, up) for m in items)
        return f'<div>{head}<div style="border:1px solid {t.PAPER_EDGE}">{rows}</div></div>'

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0 14px">'
        f'<span style="width:3px;height:15px;background:{t.CMSI_RED};display:inline-block"></span>'
        f'<span style="font-size:14px;font-weight:700;color:{t.INK}">涨跌榜</span>'
        f'<span style="font-size:12px;color:{t.INK_3}">· {_esc(window)}</span></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">'
        f'{col("涨幅前 10", gainers, True, t.UP)}{col("跌幅前 10", losers, False, t.DOWN)}</div>',
        unsafe_allow_html=True,
    )
