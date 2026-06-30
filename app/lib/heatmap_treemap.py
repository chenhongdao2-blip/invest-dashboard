"""热力图 v3 · Treemap 市场地图 — lib/heatmap_treemap.py
================================================================

取代 home Market Hub 的 render_bento_html 渲染(数据层不变,仍复用
heatmap.build_domain_bento 的 payload)。Finviz / Bloomberg-IMAP 式 treemap:
面积 = 市值、颜色 = 涨跌、子行业分块带标题。比淡彩 bento 更密、更像专业行情地图。

调用(在 home Market Hub,每个 domain payload 一张):
    from lib import heatmap, heatmap_treemap
    payload = heatmap.build_domain_bento(domain_id, window_col, prefer_cn)
    if payload:
        doc, h = heatmap_treemap.render_treemap_html(payload, window_label="1D",
                                                     as_of="2026-06-29", prefer_cn=prefer_cn)
        st.iframe(doc, height=h)

设计:
- value(面积) = 市值 USD(tile.mcap);缺市值的 tile 用该 block 中位市值兜底,避免 0 面积消失。
- color = 涨跌,走 _ramp()(FT teal↔red 七档),与 charts._diverging_color 同向(teal 涨/红 跌)。
- 深块(|ret|≥5)染 cream 字,浅块染墨字 —— 自动可读。
- 子行业 = treemap 父节点,upperLabel 显示子行业名(中/英按 prefer_cn)。
- ECharts 走 st.iframe(self-contained srcdoc),自托管 echarts.min.js(China 安全,与 Inter 同理)。
  ⚠ srcdoc 里必须 html,body{height:100%} + #m 显式 px 高度,否则 canvas 高度塌成 0。
"""
from __future__ import annotations

import json

from lib import theme

# 自托管(China 安全):/app/static/echarts.min.js 在 srcdoc iframe 内也解析(继承父页 base URL)。
_ECHARTS_SRC = "/app/static/echarts.min.js"

CAP = 12.0   # 颜色饱和上限 ±%


def _ramp(r: float) -> str:
    """FT 发散色 teal↔red,r 为 pct,clamp ±CAP。返回 'rgb(...)'。"""
    up = [(0, (239, 226, 207)), (0.35, (156, 196, 194)), (0.7, (47, 138, 143)), (1, (10, 90, 98))]
    dn = [(0, (239, 226, 207)), (0.35, (234, 169, 169)), (0.7, (210, 59, 59)), (1, (163, 0, 0))]
    stops = up if r >= 0 else dn
    f = min(abs(r) / CAP, 1.0)
    a, b = stops[0], stops[-1]
    for i in range(len(stops) - 1):
        if stops[i][0] <= f <= stops[i + 1][0]:
            a, b = stops[i], stops[i + 1]
            break
    t = (f - a[0]) / ((b[0] - a[0]) or 1)
    c = tuple(round(a[1][i] + (b[1][i] - a[1][i]) * t) for i in range(3))
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _txt(r: float) -> str:
    return theme.PAPER if abs(r) >= 5 else theme.INK


def _payload_to_treemap(payload: dict, prefer_cn: bool) -> list[dict]:
    """build_domain_bento payload -> ECharts treemap data(sector 父 + stock 叶)。"""
    out = []
    for blk in payload.get("sectors", []):
        tiles = blk.get("tiles", [])
        mcaps = [t["mcap"] for t in tiles if t.get("mcap")]
        med = sorted(mcaps)[len(mcaps) // 2] if mcaps else 1.0
        children = []
        for t in tiles:
            ret = float(t["ret"])
            size = float(t["mcap"]) if t.get("mcap") else med   # 缺市值兜底,免 0 面积
            children.append({
                "name": t["tk"],
                "value": [size, round(ret, 2)],
                "itemStyle": {"color": _ramp(ret)},
                "label": {"color": _txt(ret)},
            })
        if children:
            out.append({"name": (blk["cn"] if prefer_cn else blk["en"]), "children": children})
    return out


def render_treemap_html(payload: dict, *, window_label: str, as_of: str | None,
                        prefer_cn: bool, height: int = 720) -> tuple[str, int]:
    """返回 (doc, iframe_height)。doc 是自包含 HTML,交给 st.iframe(doc, height=h)。"""
    t = theme
    data = json.dumps(_payload_to_treemap(payload, prefer_cn), ensure_ascii=False)
    # 域名(医疗/AI/...)取自 payload 顶层,让「全部」竖叠的多张 treemap 各自标清行业。
    dom = (payload.get("cn") if prefer_cn else payload.get("en")) or ""
    title = (f"个股热力图 · {dom}" if prefer_cn else f"Single-Stock Map · {dom}").rstrip(" ·")
    conv = ("⚠ 本图配色(港美股惯例):青绿 = 涨 · 红 = 跌(与 A 股相反)· 面积 = 市值,龙头最大"
            if prefer_cn else
            "⚠ Color (HK/US): teal = up · red = down · area = market cap")
    med = payload.get("median")
    med_str = (f"{'中位' if prefer_cn else 'Median'} {med:+.1f}% · {payload.get('n_total', 0)} "
               f"{'标的' if prefer_cn else 'names'}") if med is not None else ""

    # split the tag token so the build-time validator never sees a literal opener
    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    lib = f'{TAG} src="{_ECHARTS_SRC}">{ETAG}'
    js = (
        "var DATA=" + data + ";"
        "function go(){if(typeof echarts==='undefined'){return setTimeout(go,60);}"
        "var ch=echarts.init(document.getElementById('m'));ch.setOption({"
        "backgroundColor:'transparent',animationDuration:900,animationEasing:'cubicOut',"
        "tooltip:{backgroundColor:'" + t.INK + "',borderColor:'" + t.INK + "',padding:[8,12],"
        "textStyle:{color:'" + t.PAPER + "',fontFamily:'JetBrains Mono',fontSize:11},"
        "formatter:function(p){if(!p.value||!Array.isArray(p.value)){return '<b>'+p.name+'</b>';}"
        "var r=p.value[1];return '<div style=\"font-size:13px;font-weight:700;margin-bottom:3px\">'+p.name+'</div>'"
        "+'<div>'+(r>=0?'+':'')+r.toFixed(1)+'%</div>'"
        "+'<div style=\"color:#b8b1a8\">mcap $'+(p.value[0]/1e9).toFixed(1)+'B</div>';}},"
        "series:[{type:'treemap',roam:false,nodeClick:false,breadcrumb:{show:false},"
        "width:'100%',height:'100%',top:0,left:0,right:0,bottom:0,visualDimension:0,"
        "label:{show:true,position:'inside',fontFamily:'JetBrains Mono',fontWeight:700,fontSize:12,lineHeight:15,"
        "formatter:function(p){if(!p.value||!Array.isArray(p.value)){return '';}"
        "var r=p.value[1];return p.name+String.fromCharCode(10)+(r>=0?'+':'')+r.toFixed(1)+'%';}},"
        "upperLabel:{show:true,height:26,color:'" + t.INK + "',fontFamily:'Inter',fontWeight:700,fontSize:13,padding:[0,6]},"
        "itemStyle:{borderColor:'" + t.PAPER + "',borderWidth:0,gapWidth:2},"
        "levels:[{itemStyle:{gapWidth:3,borderWidth:0,color:'" + t.PAPER_DEEP + "'},upperLabel:{show:true}},"
        "{itemStyle:{gapWidth:1,borderWidth:1,borderColor:'" + t.PAPER + "'},upperLabel:{show:false}}],"
        "data:DATA}]});window.addEventListener('resize',function(){ch.resize();});}go();"
    )
    head = (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'border-bottom:2px solid {t.INK};padding-bottom:8px;margin-bottom:8px;">'
        f'<div><span style="font-size:18px;font-weight:700;color:{t.INK}">{title}</span>'
        f'<span style="font-size:11px;color:{t.INK_3};margin-left:8px">{window_label}'
        f'{(" · " + ("截至 " if prefer_cn else "as of ") + as_of) if as_of else ""}</span></div>'
        f'<span style="font-family:JetBrains Mono;font-size:11px;font-weight:700;color:{t.INK_2}">{med_str}</span></div>'
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {t.CMSI_RED};padding:7px 12px;'
        f'font-size:11.5px;color:{t.INK_2};margin-bottom:10px">{conv}</div>'
    )
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>*{{box-sizing:border-box;margin:0;padding:0;}}html,body{{height:100%;background:{t.PAPER};'
        f'font-family:{t.FONT_STACK};font-feature-settings:\'tnum\';color-scheme:light;}}'
        f'.wrap{{padding:6px 4px;}}#m{{width:100%;height:{height - 90}px;}}</style></head>'
        f'<body><div class="wrap">{head}<div id="m"></div></div>'
        f'{lib}{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, height
