"""指数瓦片 v1 · Market Hub 市场总览 — lib/market_hub_tiles.py
================================================================

取代 home Market Hub「市场总览」的 theme.kpi_metric 指数卡 ([01] KPI-B),
改为 FT 行情终端式「指数瓦片」strip:每个指数一格,含
  · 大号现价 + 当日涨跌(涨 teal / 跌 red)
  · 近 ~30 日收盘 **内联 SVG** 面积 sparkline(颜色随当日涨跌符号)
  · 52 周区间 micro-bar(当前价位置标记)
  · 1M / YTD 情境行

整条 strip = 一个 st.iframe(self-contained srcdoc)。sparkline 用**内联 SVG**(非 echarts):
与 e1 ETF 卡 `_area_spark` / strategy_banner / sector_overview 同套路 —— 全站 sparkline 统一走 SVG。
⚠ 不用 echarts canvas:多张小图在 grid 列(初始 0 宽)里 echarts.init 会因 0 尺寸竞态画空白
  (单张 treemap 不受影响,故 [07] 仍用 echarts)。SVG 无脚本/无加载/无尺寸竞态,bulletproof。
数据为真实值(bm.close_series 近30日收盘 + bench_df 行情),非 MOCK。

调用(home Market Hub「市场总览」,替换 section_header + kpi_strip):
    from lib import market_hub_tiles as mht
    tiles = [{"name":..., "value":"7,354.02", "chg_pct":-0.05,
              "lo":"6,141", "hi":"7,610", "pos":0.82,
              "m1":-2.2, "ytd":7.2, "spark":[...近30收盘...]}, ...]
    doc, h = mht.render_index_tiles(tiles, as_of="2026-06-29", prefer_cn=True)
    st.iframe(doc, height=h)

字段(每个 tile):
  name(str) · value(已格式化 str) · chg_pct(float|None,当日%) ·
  lo/hi(已格式化 52周低/高 str|None) · pos(0-1 现价在52周区间位置|None) ·
  m1/ytd(float|None,%) · spark(list[float],近~30收盘,<2 点则不画线)

设计约束(踩过坑的护栏):
- 大标题「行情中枢」由 home.py 的 theme.page_header 已渲染 —— 本 strip 只从
  「市场总览」eyebrow 起,不重复大标题。
- 无 实时跟踪/TRACKING 徽标(数据是 EOD/cron,非实时 —— George 拍板去掉)。
"""
from __future__ import annotations

from lib import theme


def _ret_color(v) -> str:
    """涨 teal / 跌 red / 缺失 墨。"""
    if v is None:
        return theme.INK_3
    return theme.UP if v >= 0 else theme.DOWN


def _ctx_span(lbl: str, v) -> str:
    """情境行的一格:'1M -2.2%'(值按符号染色),缺失则灰 '—'。"""
    if v is None:
        return f'<span>{lbl} <b style="color:{theme.INK_3}">—</b></span>'
    col = _ret_color(v)
    return f'<span>{lbl} <b style="color:{col}">{v:+.1f}%</b></span>'


def _spark_svg(vals, chg, idx: int, *, w: int = 260, h: int = 58, pad: int = 4) -> str:
    """内联 SVG 面积 sparkline(颜色随当日涨跌 chg 符号:涨 teal/跌 red)。
    width:100% + viewBox + preserveAspectRatio=none 自适应格宽;<2 点占位保高度。"""
    vals = [float(v) for v in (vals or [])]
    if len(vals) < 2:
        return '<div style="height:58px"></div>'   # 占位保高度,免瓦片错位
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    col = theme.UP if (chg is None or chg >= 0) else theme.DOWN
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = [(pad + i * step, h - pad - (v - lo) / rng * (h - 2 * pad)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{h - pad:.1f} {line} {pts[-1][0]:.1f},{h - pad:.1f}"
    lx, ly = pts[-1]
    gid = f"mht{idx}"
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:100%;height:{h}px;display:block;margin-top:10px">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{col}" stop-opacity="0.16"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#{gid})" stroke="none"/>'
        f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="1.7" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{col}"/></svg>'
    )


def _range_bar(lo, hi, pos, prefer_cn: bool) -> str:
    """52 周区间 micro-bar(teal 填充至现价位置 + 墨色标记);缺数据则省略。"""
    if lo is None or hi is None or pos is None:
        return '<div style="height:23px"></div>'   # 占位保高度,免瓦片错位
    p = max(0.0, min(float(pos), 1.0)) * 100
    return (
        f'<div style="margin-top:13px">'
        f'<div style="position:relative;height:4px;background:{theme.PAPER_RULE}">'
        f'<div style="position:absolute;left:0;top:0;height:4px;width:{p:.1f}%;background:{theme.UP}"></div>'
        f'<div style="position:absolute;left:{p:.1f}%;top:-2px;height:8px;width:2px;'
        f'background:{theme.INK};transform:translateX(-1px)"></div></div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:5px;'
        f'font-family:{theme.FONT_MONO};font-size:10px;color:{theme.INK_3}">'
        f'<span>52W {lo}</span><span>{hi}</span></div></div>'
    )


def _tile(it: dict, idx: int, prefer_cn: bool) -> str:
    chg = it.get("chg_pct")
    col = _ret_color(chg)
    chg_str = "—" if chg is None else f"{chg:+.2f}%"
    return (
        f'<div class="tile">'
        f'<div class="thead"><span class="tname">{it["name"]}</span><span class="ttick"></span></div>'
        f'<div class="tval">{it["value"]}</div>'
        f'<div class="tchg" style="color:{col}">{chg_str}</div>'
        f'{_spark_svg(it.get("spark"), chg, idx)}'
        f'{_range_bar(it.get("lo"), it.get("hi"), it.get("pos"), prefer_cn)}'
        f'<div class="tctx">{_ctx_span("1M", it.get("m1"))}'
        f'<span class="dot">·</span>{_ctx_span("YTD", it.get("ytd"))}</div>'
        f'</div>'
    )


def render_index_tiles(tiles: list[dict], *, as_of: str | None,
                       prefer_cn: bool, height: int = 330) -> tuple[str, int]:
    """返回 (doc, iframe_height)。doc 自包含(纯 HTML+SVG,无脚本),交给 st.iframe(doc, height=h)。"""
    t = theme
    n = len(tiles) or 1
    parts = [_tile(it, i, prefer_cn) for i, it in enumerate(tiles)]

    eb_ttl = "市场总览" if prefer_cn else "Market Overview"
    eb_sub = ("四大指数 · 30 日走势 + 52 周区间" if prefer_cn
              else "4 indices · 30-day trend + 52-week range")
    foot = (f"来源 Yahoo Finance cron EOD · 截至 {as_of} · 仅供参考" if prefer_cn
            else f"Source: Yahoo Finance cron EOD · as of {as_of} · for reference")
    if not as_of:
        foot = "来源 Yahoo Finance cron EOD · 仅供参考" if prefer_cn else "Source: Yahoo Finance cron EOD"

    eyebrow = (
        f'<div class="eyebrow">'
        f'<span class="ebtick"></span>'
        f'<span class="ebttl">{eb_ttl}</span>'
        f'<span class="ebsub">{eb_sub}</span>'
        f'<span class="ebech">SVG</span></div>'
    )
    css = (
        f"*{{box-sizing:border-box;margin:0;padding:0}}"
        f"html,body{{height:100%;background:{t.PAPER};font-family:{t.FONT_STACK};"
        f"font-feature-settings:'tnum';color-scheme:light;color:{t.INK}}}"
        f".wrap{{padding:4px 2px}}"
        f".eyebrow{{display:flex;align-items:baseline;gap:10px;margin:2px 0 12px}}"
        f".ebtick{{width:4px;height:16px;background:{t.CMSI_RED};display:inline-block;align-self:center}}"
        f".ebttl{{font-size:14px;font-weight:700;color:{t.INK}}}"
        f".ebsub{{font-size:12px;color:{t.INK_3}}}"
        f".ebech{{margin-left:auto;font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.14em;color:{t.INK_4}}}"
        f".grid{{display:grid;grid-template-columns:repeat({n},1fr);"
        f"border:1px solid {t.PAPER_EDGE};background:{t.PAPER}}}"
        f".tile{{padding:16px 18px;border-right:1px solid {t.PAPER_RULE}}}"
        f".tile:last-child{{border-right:none}}"
        f".thead{{display:flex;justify-content:space-between;align-items:flex-start}}"
        f".tname{{font-size:13px;font-weight:600;color:{t.INK};letter-spacing:.01em}}"
        f".ttick{{width:4px;height:15px;background:{t.CMSI_RED};display:inline-block;flex:none}}"
        f".tval{{font-size:34px;line-height:38px;font-weight:700;letter-spacing:-.02em;"
        f"margin-top:8px;font-variant-numeric:tabular-nums}}"
        f".tchg{{font-family:{t.FONT_MONO};font-size:13px;font-weight:700;margin-top:2px;"
        f"font-variant-numeric:tabular-nums}}"
        f".tctx{{display:flex;gap:7px;margin-top:11px;font-family:{t.FONT_MONO};"
        f"font-size:11px;color:{t.INK_3}}}"
        f".tctx .dot{{color:{t.INK_4}}}"
        f".foot{{margin-top:11px;font-family:{t.FONT_MONO};font-size:10.5px;"
        f"letter-spacing:.02em;color:{t.INK_3}}}"
    )
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="wrap">'
        f'{eyebrow}<div class="grid">{"".join(parts)}</div>'
        f'<div class="foot">{foot}</div></div></body></html>'
    )
    return doc, height
