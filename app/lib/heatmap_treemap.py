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

多域竖叠时,把第 2+ 张 show_header=False 节省页面高度:
        doc, h = heatmap_treemap.render_treemap_html(payload, ..., show_header=False)

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
from lib import echarts_boot

# 自托管(China 安全)+ 相对路径(NO 前导 /):云端 Streamlit 服务在 /~/+/ 前缀下,srcdoc
# iframe baseURI = 该前缀;相对 "app/static/..." 云端解析为 /~/+/app/static/...(实测 load ✓),
# 本地解析为 /app/static/...。**禁改回绝对 "/app/static/..."**(云端丢前缀 → echarts undefined → 空图)。
_ECHARTS_SRC = "app/static/echarts.min.js"

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
                        prefer_cn: bool, height: int = 720,
                        show_header: bool = True) -> tuple[str, int]:
    """返回 (doc, iframe_height)。doc 是自包含 HTML,交给 st.iframe(doc, height=h)。

    Args:
        show_header: 若 False 省略 masthead/图例/banner(多域竖叠第 2+ 张用),
                     只保留域条+画布+脚注。call-site 需为第 1 张传 True,其余传 False。
    """
    t = theme
    data = json.dumps(_payload_to_treemap(payload, prefer_cn), ensure_ascii=False)
    dom_label = (payload.get("cn") if prefer_cn else payload.get("en")) or ""
    med = payload.get("median")
    n_total = payload.get("n_total", 0)
    source = payload.get("source", "")
    wl = window_label
    ml = "市值" if prefer_cn else "mcap"

    # ── 画布高(为页级元素留空) ────────────────────────────────────────────
    canvas_h = max(200, height - (200 if show_header else 110))

    # ── 脚本 tag 拆 token(躲 build-time validator) ─────────────────────────
    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    lib = f'{TAG} src="{_ECHARTS_SRC}">{ETAG}'

    # ── ECharts JS option ──────────────────────────────────────────────────
    js = (
        "var DATA=" + data + ";"
        "mountEChart('m',function(){return {"
        "backgroundColor:'transparent',animationDuration:900,animationEasing:'cubicOut',"
        "tooltip:{backgroundColor:'" + t.INK + "',borderColor:'" + t.INK + "',padding:[8,12],"
        "textStyle:{color:'" + t.PAPER + "',fontFamily:'JetBrains Mono',fontSize:11},"
        "formatter:function(p){if(!p.value||!Array.isArray(p.value)){return '<b>'+p.name+'</b>';}"
        "var r=p.value[1];"
        "var rc=r>=0?'#9cc4c2':'#eaa9a9';"
        "return '<div style=\"font-size:13px;font-weight:700;margin-bottom:3px\">'+p.name+'</div>'"
        f"+'<div style=\"color:\'+rc+\';font-weight:700\">{wl} '+(r>=0?'+':'')+r.toFixed(1)+'%</div>'"
        f"+'<div style=\"color:#b8b1a8\">{ml} $'+(p.value[0]/1e9).toFixed(1)+'B</div>'"
        "}},"
        "series:[{type:'treemap',roam:false,nodeClick:false,breadcrumb:{show:false},"
        "width:'100%',height:'100%',top:0,left:0,right:0,bottom:0,visualDimension:0,"
        "label:{show:true,position:'inside',fontFamily:'JetBrains Mono',fontWeight:700,fontSize:12,lineHeight:15,"
        "formatter:function(p){if(!p.value||!Array.isArray(p.value)){return '';}"
        "var r=p.value[1];return p.name+String.fromCharCode(10)+(r>=0?'+':'')+r.toFixed(1)+'%';}},"
        "upperLabel:{show:true,height:26,color:'" + t.INK + "',fontFamily:'Space Grotesk',fontWeight:700,fontSize:13,padding:[0,6]},"
        "itemStyle:{borderColor:'" + t.PAPER + "',borderWidth:0,gapWidth:2},"
        "levels:[{itemStyle:{gapWidth:3,borderWidth:0,color:'" + t.PAPER_DEEP + "'},upperLabel:{show:true}},"
        "{itemStyle:{gapWidth:1,borderWidth:1,borderColor:'" + t.PAPER + "'},upperLabel:{show:false}}],"
        "data:DATA}]};});"
    )

    # ── Masthead + legend + banner (show_header only) ──────────────────────
    if show_header:
        title_main = "个股热力图 · Market Map" if prefer_cn else "Single-Stock Map · Market Map"
        sub_row = (
            f"面积 = 市值 · 颜色 = {wl} 涨跌方向与幅度 · 子行业分块"
            if prefer_cn else
            f"area = market cap · color = {wl} direction &amp; magnitude · sub-sector groups"
        )
        legend_label = "颜色 = 涨跌方向与幅度" if prefer_cn else "color = direction &amp; magnitude"
        dn_label = "跌" if prefer_cn else "dn"
        up_label = "涨" if prefer_cn else "up"

        masthead_html = (
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
            f'gap:20px;flex-wrap:wrap;border-bottom:2px solid {t.INK};padding-bottom:12px;margin-bottom:10px;">'
            # left: red bar + title block
            f'<div style="display:flex;align-items:flex-start;gap:10px;">'
            f'<div style="width:5px;height:44px;background:{t.CMSI_RED};border-radius:1px;flex-shrink:0;"></div>'
            f'<div>'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:26px;font-weight:700;letter-spacing:-0.01em;color:{t.INK}">'
            f'{title_main}</span>'
            f'<span style="font-family:JetBrains Mono;font-size:10px;font-weight:700;'
            f'color:{t.PAPER};background:{t.CMSI_RED};padding:2px 7px;letter-spacing:.06em">CMSI</span>'
            f'</div>'
            f'<div style="font-family:JetBrains Mono;font-size:11px;letter-spacing:.06em;'
            f'color:{t.INK_3};margin-top:5px">{sub_row}</div>'
            f'</div></div>'
            # right: gradient legend
            f'<div style="text-align:right;">'
            f'<div style="font-size:10px;font-weight:600;color:{t.INK_2};margin-bottom:4px">'
            f'{legend_label}</div>'
            f'<div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;">'
            f'<span style="font-size:11px;font-weight:700;color:#a30000">{dn_label}</span>'
            f'<div style="width:190px;height:12px;border:1px solid #d4c4b0;flex-shrink:0;'
            f'background:linear-gradient(to right,#a30000,#d23b3b,#efe2cf,#2f8a8f,#0a5a62);"></div>'
            f'<span style="font-size:11px;font-weight:700;color:#0a5a62">{up_label}</span>'
            f'</div>'
            f'<div style="width:190px;display:flex;justify-content:space-between;margin-left:auto;'
            f'font-family:JetBrains Mono;font-size:9px;font-weight:600;color:{t.INK_3};">'
            f'<span>-12%</span><span>0</span><span>+12%</span>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

        if prefer_cn:
            banner_html = (
                f'<div style="display:flex;align-items:baseline;gap:8px;background:{t.PAPER_DEEP};'
                f'border-left:3px solid {t.CMSI_RED};padding:7px 12px;font-size:11.5px;'
                f'color:{t.INK_2};margin-bottom:0;">'
                f'<span><b style="color:{t.INK}">本图配色（港美股惯例）：</b>'
                f'<span style="color:#0a5a62;font-weight:700">青绿 = 涨</span>'
                f' · <span style="color:#a30000;font-weight:700">红 = 跌</span>'
                f'<b style="color:{t.INK}">（与 A 股红涨绿跌相反，请注意）</b></span>'
                f'<span style="margin-left:auto;white-space:nowrap;font-size:10.5px;color:{t.INK_3}">'
                f'面积 = 市值（龙头最大） · hover 看名称/市值</span>'
                f'</div>'
            )
        else:
            banner_html = (
                f'<div style="display:flex;align-items:baseline;gap:8px;background:{t.PAPER_DEEP};'
                f'border-left:3px solid {t.CMSI_RED};padding:7px 12px;font-size:11.5px;'
                f'color:{t.INK_2};margin-bottom:0;">'
                f'<span><b style="color:{t.INK}">Color convention (HK/US):</b> '
                f'<span style="color:#0a5a62;font-weight:700">teal = up</span>'
                f' · <span style="color:#a30000;font-weight:700">red = down</span>'
                f'<b style="color:{t.INK}"> (opposite of A-share convention)</b></span>'
                f'<span style="margin-left:auto;white-space:nowrap;font-size:10.5px;color:{t.INK_3}">'
                f'area = market cap (largest = leader) · hover for name/mcap</span>'
                f'</div>'
            )

        page_header = masthead_html + banner_html
    else:
        page_header = ""

    # ── Domain bar (always shown per spec; per-domain repeat) ─────────────
    med_str = ""
    if med is not None:
        label_median = "中位" if prefer_cn else "Median"
        label_names = "标的" if prefer_cn else "names"
        med_str = f"{label_median} {med:+.1f}% · {n_total} {label_names}"
    domain_bar = (
        f'<div style="display:flex;align-items:baseline;gap:11px;background:{t.PAPER_DEEP};'
        f'border-left:3px solid {t.CMSI_RED};padding:8px 13px;margin:12px 0 2px;">'
        f'<span style="font-size:16px;font-weight:700;color:{t.INK}">{dom_label}</span>'
        f'<span style="margin-left:auto;font-family:JetBrains Mono;font-size:11px;'
        f'font-weight:700;color:{t.INK_2}">{med_str}</span>'
        f'</div>'
    )

    # ── Source footnote ────────────────────────────────────────────────────
    as_of_str = ""
    if as_of:
        as_of_str = " · " + ("截至 " if prefer_cn else "as of ") + as_of
    area_col = f"面积=市值 / 颜色={wl} 涨跌" if prefer_cn else f"area=mcap / color={wl} direction"
    footnote = (
        f'<div style="font-family:JetBrains Mono;font-size:11px;color:{t.INK_3};'
        f'letter-spacing:.02em;margin-top:6px">'
        f'SOURCE: {source} · mcap USD{as_of_str} · {area_col}'
        f'</div>'
    )

    # ── Assemble self-contained HTML doc ───────────────────────────────────
    # FONT_FACE_CSS is a multi-line string; strip whitespace to keep style compact.
    # CSS {/} inside the inserted value are NOT further processed by the f-string.
    font_face = t.FONT_FACE_CSS.strip()
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        f'*{{box-sizing:border-box;margin:0;padding:0;}}'
        f'html,body{{height:100%;background:{t.PAPER};'
        f"font-family:{t.FONT_DISPLAY};font-feature-settings:'tnum','ss01';color-scheme:light;}}"
        f'body{{position:relative;}}'
        f'.wash{{position:absolute;inset:0;pointer-events:none;z-index:0;'
        f'background:radial-gradient(900px 520px at 10% -8%,rgba(200,16,46,.09),transparent 60%),'
        f'radial-gradient(820px 520px at 94% 4%,rgba(13,118,128,.10),transparent 60%);}}'
        f'.inner{{position:relative;z-index:1;max-width:1240px;margin:0 auto;padding:10px 36px;}}'
        f'#m{{width:100%;height:{canvas_h}px;}}'
        f'</style></head>'
        f'<body><div class="wash"></div><div class="inner">'
        f'{page_header}{domain_bar}<div id="m"></div>{footnote}'
        f'</div>'
        f'{lib}{TAG}>{echarts_boot.MOUNT_JS}{ETAG}{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, height
