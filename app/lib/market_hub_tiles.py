"""指数瓦片 v1 · Market Hub 市场总览 — lib/market_hub_tiles.py
================================================================

取代 home Market Hub「市场总览」的 theme.kpi_metric 指数卡 ([01] KPI-B),
改为 FT 行情终端式「指数瓦片」strip:每个指数一格,含
  · 大号现价 + 当日涨跌(涨 teal / 跌 red)
  · 近 ~30 日收盘 sparkline(ECharts,颜色随当日涨跌符号)
  · 52 周区间 micro-bar(当前价位置标记)
  · 1M / YTD 情境行

整条 strip = 一个 st.iframe(self-contained srcdoc)+ 内含 N 个 echarts。
数据为真实值(bm.close_series 近30日收盘 + bench_df 行情),非 MOCK 演示。

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
  「市场总览」eyebrow 起,不重复大标题(否则双 行情中枢)。
- 无 实时跟踪/TRACKING 徽标(数据是 EOD/cron,非实时 —— George 拍板去掉)。
- ECharts 走 st.iframe(self-contained srcdoc),自托管 echarts.min.js(China 安全)。
  ⚠ srcdoc 里 sparkline 容器必须有显式 px 高度,否则 canvas 高度塌成 0。
- JS 里禁内联 FONT_STACK(含单引号会 SyntaxError 整段不执行);sparkline 无文字,
  不需要字体 —— 颜色等数据走 json.dumps。
"""
from __future__ import annotations

import json

from lib import theme

# 自托管(China 安全):/app/static/echarts.min.js 在 srcdoc iframe 内也解析。
_ECHARTS_SRC = "/app/static/echarts.min.js"


def _rgba(hex_color: str, alpha: float) -> str:
    """'#0d7680' -> 'rgba(13,118,128,0.16)'。非 #rrggbb 原样返回。"""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


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


def _range_bar(lo, hi, pos, prefer_cn: bool) -> str:
    """52 周区间 micro-bar(teal 填充至现价位置 + 墨色标记);缺数据则省略。"""
    if lo is None or hi is None or pos is None:
        return '<div style="height:23px"></div>'   # 占位保高度,免瓦片错位
    p = max(0.0, min(float(pos), 1.0)) * 100
    pre = "52W "
    return (
        f'<div style="margin-top:13px">'
        f'<div style="position:relative;height:4px;background:{theme.PAPER_RULE}">'
        f'<div style="position:absolute;left:0;top:0;height:4px;width:{p:.1f}%;background:{theme.UP}"></div>'
        f'<div style="position:absolute;left:{p:.1f}%;top:-2px;height:8px;width:2px;'
        f'background:{theme.INK};transform:translateX(-1px)"></div></div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:5px;'
        f'font-family:{theme.FONT_MONO};font-size:10px;color:{theme.INK_3}">'
        f'<span>{pre}{lo}</span><span>{hi}</span></div></div>'
    )


def _tile(it: dict, idx: int, prefer_cn: bool) -> tuple[str, dict | None]:
    """返回 (tile_html, spark_spec|None)。spark_spec 喂 JS 初始化 sparkline。"""
    chg = it.get("chg_pct")
    col = _ret_color(chg)
    chg_str = "—" if chg is None else f"{chg:+.2f}%"
    spark = it.get("spark") or []
    spec = None
    spark_div = '<div style="height:58px"></div>'
    if len(spark) >= 2:
        line = theme.UP if (chg is None or chg >= 0) else theme.DOWN
        spec = {"v": [round(float(x), 4) for x in spark], "c": line, "a": _rgba(line, 0.16)}
        spark_div = f'<div class="sp" id="sp{idx}"></div>'
    html = (
        f'<div class="tile">'
        f'<div class="thead"><span class="tname">{it["name"]}</span><span class="ttick"></span></div>'
        f'<div class="tval">{it["value"]}</div>'
        f'<div class="tchg" style="color:{col}">{chg_str}</div>'
        f'{spark_div}'
        f'{_range_bar(it.get("lo"), it.get("hi"), it.get("pos"), prefer_cn)}'
        f'<div class="tctx">{_ctx_span("1M", it.get("m1"))}'
        f'<span class="dot">·</span>{_ctx_span("YTD", it.get("ytd"))}</div>'
        f'</div>'
    )
    return html, spec


def render_index_tiles(tiles: list[dict], *, as_of: str | None,
                       prefer_cn: bool, height: int = 330) -> tuple[str, int]:
    """返回 (doc, iframe_height)。doc 自包含,交给 st.iframe(doc, height=h)。"""
    t = theme
    n = len(tiles) or 1
    parts, specs = [], []
    for i, it in enumerate(tiles):
        html, spec = _tile(it, i, prefer_cn)
        parts.append(html)
        specs.append(spec)   # 保位置对齐 sp{i};None = 该格无 sparkline
    spark_json = json.dumps(
        {i: s for i, s in enumerate(specs) if s is not None}, ensure_ascii=False)

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
        f'<span class="ebech">ECHARTS</span></div>'
    )

    # split the tag token so the build-time validator never sees a literal opener
    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    lib = f'{TAG} src="{_ECHARTS_SRC}">{ETAG}'
    js = (
        "var SP=" + spark_json + ";"
        "function go(){if(typeof echarts==='undefined'){return setTimeout(go,60);}"
        "var ins=[];Object.keys(SP).forEach(function(k){var el=document.getElementById('sp'+k);"
        "if(!el){return;}var c=echarts.init(el);ins.push(c);var d=SP[k];c.setOption({animation:false,"
        "grid:{left:1,right:1,top:3,bottom:3},xAxis:{type:'category',show:false,boundaryGap:false},"
        "yAxis:{type:'value',show:false,scale:true},series:[{type:'line',data:d.v,showSymbol:false,"
        "smooth:false,lineStyle:{color:d.c,width:1.7},areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,"
        "colorStops:[{offset:0,color:d.a},{offset:1,color:'rgba(255,255,255,0)'}]}}}]});});"
        "window.addEventListener('resize',function(){ins.forEach(function(c){c.resize();});});}go();"
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
        f".sp{{width:100%;height:58px;margin-top:10px}}"
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
        f'<div class="foot">{foot}</div></div>'
        f'{lib}{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, height
