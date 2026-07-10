"""相对表现 ECharts 卡片 — lib/rs_panel.py
================================================================

设计源（1:1 移植）：claude.ai/design 「相对表现 区间筛选 美化.dc.html」
（handoff zip → three-js/project/，2026-07-10 George 提供）。

每个 panel = 一张自包含 st.iframe 卡片：
- 白玻璃卡 rgba(255,255,255,.55) + blur + 顶部 2px accent 条（设计稿口径）
- 编号 kicker（01 · 港股口径 · HK LENS）+ 标题 + 自绘 svg legend
- **每张图自带 5D / 1M / 6M / 全程 区间控件** —— 客户端 JS 状态切换，
  即时重锚定（窗口首日 = 100），无 Streamlit rerun
- 墨黑 tooltip（cream 字，行序反转 = hero 在最上）
- hero 端点红点 + endLabel 数值；y=100 虚线锚线
- 底部 pp 徽章行（vs 对照线，窗口内累计超额，teal 跑赢 / 红 跑输）+ 来源

调用（2_Healthcare.py）：
    doc, h = rs_panel.render_panel(panel_dict, prefer_cn=...)
    st.iframe(doc, height=h)

panel_dict 契约见 render_panel docstring。

⚠ 不可回退的既有约束（与 heatmap_treemap 同源）：
- echarts.min.js 自托管、**相对路径** "app/static/echarts.min.js"（云端 /~/+/ 前缀，
  绝对路径会撞 login → 空图；见 memory streamlit-cloud-static-path-prefix）
- echarts.init 必须走 echarts_boot.MOUNT_JS 的容器就绪守卫（0 宽 race）
- 字体走 theme.FONT_FACE_CSS 自托管（China 网络禁 Google Fonts CDN）
"""
from __future__ import annotations

import json

from lib import echarts_boot
from lib import theme

_ECHARTS_SRC = "app/static/echarts.min.js"   # 相对路径，禁改绝对（云端丢前缀）

# 设计稿色板（与 theme tokens 同值，卡片内联用）
_RED = theme.CMSI_RED       # #c8102e
_TEAL = theme.UP            # #0d7680
_GREY = "#8f8a84"           # 设计稿对照线灰（比 INK_3 略深）
_INK = theme.INK
_MUTED = "#8a8580"
_FAINT = "#b8b1a8"
_CARD_EDGE = "#d4c4b0"
_RULE = "#ebd9c8"
_GRID = "#eddccb"
_CTRL_EDGE = "#b8ab99"
_CTRL_SEP = "#e2d3c1"
_CREAM = theme.PAPER        # #fff1e5

# iframe 卡片 chrome 高度（header+legend+footer+padding），叠加 chart px 高
_CHROME_H = 168


def render_panel(panel: dict, *, prefer_cn: bool = True) -> tuple[str, int]:
    """Build one self-contained relative-performance card. Returns (doc, iframe_h).

    panel = {
      "pid":     str,                  # dom-safe id ("hk" / "jp" ...)
      "kicker":  str,                  # "01 · 港股口径 · HK LENS"
      "title":   str,
      "accent":  str,                  # 卡片顶条色（hex）
      "chart_h": int,                  # 画布 px 高（设计稿：340/300/260）
      "src":     str,                  # "iFind · yfinance"
      "asof":    str,                  # ISO date（footer 来源行）
      "series": [                      # hero 放最后（绘制在最上，legend 最后）
        {"name": str, "dates": [iso], "closes": [float],
         "color": hex, "dash": "solid" | [6,4] | [2,3], "width": float,
         "hero": bool},
      ],
    }

    区间语义（与设计稿 JS 完全一致）：序列按共同交易日内联；5D = 近 5 个共同
    交易日；1M/6M 按日历从窗口末日回溯；窗口首日重锚定 = 100；pp = hero 末值 −
    对照末值（rebased 点数）。
    """
    pid = str(panel["pid"])
    chart_h = int(panel.get("chart_h", 300))
    iframe_h = chart_h + _CHROME_H

    # ── series → JS payload（inner-join 在 JS 侧做，与设计稿一致）──────────
    ser_js = []
    for s in panel["series"]:
        pts = {d: float(v) for d, v in zip(s["dates"], s["closes"])
               if v is not None and v == v}
        ser_js.append({
            "n": s["name"], "c": s["color"],
            "d": s.get("dash", "solid"), "w": float(s.get("width", 1.4)),
            "h": 1 if s.get("hero") else 0, "pts": pts,
        })
    # hero 必须在最后（绘制层级 + legend 顺序），调用方已保证；这里兜底重排
    ser_js.sort(key=lambda x: x["h"])

    win_max = "全程" if prefer_cn else "MAX"
    src_line = (f"来源：{panel['src']}，截至 {panel['asof']}。" if prefer_cn
                else f"Source: {panel['src']}, as of {panel['asof']}.")

    payload = json.dumps({
        "series": ser_js, "maxLabel": win_max, "red": _RED,
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    # ── 静态 HTML（legend 服务端渲染；chip/徽章 JS 每次切窗重写）────────────
    def _dash_attr(d) -> str:
        return "" if d == "solid" else " ".join(str(x) for x in d)

    legend_html = "".join(
        '<span style="display:inline-flex;align-items:center;gap:7px;">'
        f'<svg width="26" height="10" style="flex:none;display:block;">'
        f'<line x1="1" y1="5" x2="25" y2="5" stroke="{s["c"]}" '
        f'stroke-width="{max(s["w"], 1.6)}" stroke-dasharray="{_dash_attr(s["d"])}"></line></svg>'
        f'<span style="font-size:12.5px;color:{theme.INK_2};">{s["n"]}</span></span>'
        for s in ser_js
    )

    btns_html = "".join(
        f'<button data-r="{r}" style="appearance:none;border:none;margin:0;cursor:pointer;'
        f"padding:6px 13px;font-family:'JetBrains Mono',monospace;font-size:11px;"
        f'letter-spacing:.08em;border-right:1px solid {_CTRL_SEP};'
        f'transition:background .15s,color .15s;background:transparent;color:#6b655e;'
        f'font-weight:500;">{win_max if r == "MAX" else r}</button>'
        for r in ("5D", "1M", "6M", "MAX")
    )

    # ── JS：窗口切换 + option 构建（移植设计稿 _panelData/_option）──────────
    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    lib = f'{TAG} src="{_ECHARTS_SRC}">{ETAG}'

    js = r"""
var P = __PAYLOAD__;
var MONO = "'JetBrains Mono',monospace";
var cur = 'MAX';

// 共同交易日（所有序列都有值），升序
var allDates = Object.keys(P.series[P.series.length-1].pts).filter(function(d){
  return P.series.every(function(s){ return s.pts[d] != null; });
}).sort();

function shiftMonths(iso, m){
  var p = iso.split('-').map(Number);
  return new Date(Date.UTC(p[0], p[1]-1+m, p[2])).toISOString().slice(0,10);
}

function sliceWin(r){
  var start = 0;
  if (r === '5D') start = Math.max(0, allDates.length - 5);
  else if (r === '1M' || r === '6M'){
    var cut = shiftMonths(allDates[allDates.length-1], r === '1M' ? -1 : -6);
    start = allDates.findIndex(function(d){ return d >= cut; });
    if (start < 0) start = 0;
  }
  var win = allDates.slice(start);
  if (win.length < 2) win = allDates.slice();
  var out = P.series.map(function(s){
    var base = s.pts[win[0]];
    return { cfg: s, vals: win.map(function(d){ return s.pts[d]/base*100; }) };
  });
  var lo = 100, hi = 100;
  out.forEach(function(s){ s.vals.forEach(function(v){ if(v<lo)lo=v; if(v>hi)hi=v; }); });
  var pad = Math.max((hi-lo)*0.07, 0.4);
  var hero = out[out.length-1];
  return {
    win: win, series: out, anchor: win[0], yMin: lo-pad, yMax: hi+pad,
    spreads: out.slice(0,-1).map(function(s){
      return { name: s.cfg.n, pp: hero.vals[hero.vals.length-1] - s.vals[s.vals.length-1] };
    })
  };
}

function option(d){
  var series = d.series.map(function(s, i){
    var isHero = s.cfg.h === 1;
    var o = {
      type:'line', name:s.cfg.n, showSymbol:false, animationDuration:260,
      data:d.win.map(function(x,j){ return [x, s.vals[j]]; }),
      lineStyle:{ width:isHero?2.2:s.cfg.w, color:s.cfg.c, type:s.cfg.d },
      itemStyle:{ color:s.cfg.c },
      emphasis:{ disabled:true },
      // 每条线都带端点数值（George 2026-07-10：不止红主线一个数）——各自线色，
      // hero 加粗；labelLayout.shiftY 防多线端点值重叠互压
      endLabel:{ show:true, formatter:function(p){ return Number(p.value[1]).toFixed(1); },
        color:s.cfg.c, fontFamily:MONO, fontSize:isHero?11:10, fontWeight:isHero?700:600,
        distance:7 },
      labelLayout:{ moveOverlap:'shiftY' },
      markPoint:{ silent:true, symbol:'circle', symbolSize:isHero?6:4,
        data:[{ coord:[d.win[d.win.length-1], s.vals[s.vals.length-1]] }],
        itemStyle:{ color:s.cfg.c }, label:{ show:false } }
    };
    if (isHero){
      o.markLine = { silent:true, symbol:'none', data:[{ yAxis:100 }],
        lineStyle:{ color:'__FAINT__', type:[6,4], width:1 }, label:{ show:false } };
    }
    return o;
  });
  return {
    animation:true,
    grid:{ left:44, right:56, top:14, bottom:28 },
    xAxis:{ type:'time', min:d.win[0], max:d.win[d.win.length-1],
      axisLine:{ lineStyle:{ color:'__INK__' } },
      axisTick:{ lineStyle:{ color:'__INK__' } },
      axisLabel:{ color:'__MUTED__', fontFamily:MONO, fontSize:10.5, hideOverlap:true,
        formatter:{ year:'{MMM} {yyyy}', month:'{MMM} {yyyy}', day:'{MM}-{dd}' } },
      splitLine:{ show:true, lineStyle:{ color:'__GRID__', width:1 } } },
    yAxis:{ type:'value', min:d.yMin, max:d.yMax,
      axisLine:{ show:true, lineStyle:{ color:'__INK__' } },
      axisLabel:{ color:'__MUTED__', fontFamily:MONO, fontSize:10.5,
        formatter:function(v){ return Math.round(v); } },
      splitLine:{ lineStyle:{ color:'__GRID__', width:1 } }, splitNumber:4 },
    tooltip:{ trigger:'axis', confine:true,
      backgroundColor:'__INK__', borderWidth:0, padding:[9,12],
      textStyle:{ color:'__CREAM__', fontFamily:MONO, fontSize:11 },
      axisPointer:{ type:'line', lineStyle:{ color:'__MUTED__', type:[3,3] } },
      formatter:function(params){
        var ts = params[0].value[0];
        var dt = typeof ts === 'string' ? ts.slice(0,10) : new Date(ts).toISOString().slice(0,10);
        var rows = params.slice().reverse().map(function(p){
          return '<div style="display:flex;gap:10px;align-items:baseline;margin-top:3px;">' +
            '<span style="color:'+p.color+';">━</span>' +
            '<span style="opacity:.8;">'+p.seriesName+'</span>' +
            '<b style="margin-left:auto;padding-left:14px;">'+Number(p.value[1]).toFixed(1)+'</b></div>';
        }).join('');
        return '<div style="font-weight:700;">'+dt+'</div>'+rows;
      } },
    series:series
  };
}

function renderMeta(d){
  document.getElementById('anchor').textContent = '100 = ' + d.anchor;
  var sp = document.getElementById('sp');
  sp.innerHTML = d.spreads.map(function(s){
    var flat = Math.abs(s.pp) < 0.05;
    var v = flat ? 0 : s.pp;
    var color = flat ? '__MUTED__' : (v > 0 ? '__TEAL__' : '__RED__');
    var val = (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(1) + 'pp';
    return '<span style="display:inline-flex;align-items:baseline;gap:6px;">' +
      '<span style="font-family:'+MONO+';font-size:10.5px;color:__MUTED__;">vs '+s.name+'</span>' +
      '<span style="font-family:'+MONO+';font-size:12px;font-weight:700;' +
      'font-variant-numeric:tabular-nums;color:'+color+';">'+val+'</span></span>';
  }).join('');
}

function styleBtns(){
  document.querySelectorAll('#rng button').forEach(function(b){
    var on = b.getAttribute('data-r') === cur;
    b.style.background = on ? '__INK__' : 'transparent';
    b.style.color = on ? '__CREAM__' : '#6b655e';
    b.style.fontWeight = on ? '700' : '500';
  });
}

function build(){
  var d = sliceWin(cur);
  renderMeta(d);
  return option(d);
}

mountEChart('c', build);
styleBtns();
document.querySelectorAll('#rng button').forEach(function(b){
  b.addEventListener('click', function(){
    cur = b.getAttribute('data-r');
    styleBtns();
    var el = document.getElementById('c');
    var ch = (typeof echarts !== 'undefined') && echarts.getInstanceByDom(el);
    if (ch) { ch.setOption(build(), true); } else { mountEChart('c', build); }
  });
});
"""
    js = (js.replace("__PAYLOAD__", payload)
            .replace("__INK__", _INK).replace("__CREAM__", _CREAM)
            .replace("__MUTED__", _MUTED).replace("__FAINT__", _FAINT)
            .replace("__GRID__", _GRID).replace("__TEAL__", _TEAL)
            .replace("__RED__", _RED))

    font_face = theme.FONT_FACE_CSS.strip()
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        "button:hover{opacity:.85;}"
        "</style></head><body>"
        # noqa: E501 —— 以下为设计稿 1:1 内联样式
        # ── 卡片（设计稿 1:1：白玻璃 + 顶部 accent 条）──
        f'<div style="background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);'
        f'backdrop-filter:blur(10px);border:1px solid {_CARD_EDGE};'
        f'border-top:2px solid {panel["accent"]};border-radius:2px;'
        f'padding:14px 20px 12px;display:flex;flex-direction:column;height:{iframe_h - 8}px;">'
        # header：kicker+title 左，区间控件 右
        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<div style="min-width:0;">'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;letter-spacing:.14em;'
        f'text-transform:uppercase;font-weight:600;color:{_MUTED};">{panel["kicker"]}</div>'
        f'<div style="font-size:15.5px;font-weight:600;color:{_INK};margin-top:4px;'
        f'line-height:1.35;">{panel["title"]}</div></div>'
        f'<div id="rng" style="margin-left:auto;flex:none;display:inline-flex;align-items:stretch;'
        f'border:1px solid {_CTRL_EDGE};border-radius:2px;overflow:hidden;'
        f'background:rgba(255,255,255,.6);">{btns_html}</div>'
        '</div>'
        # legend 左 + anchor chip 右
        '<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-top:10px;">'
        f'{legend_html}'
        f'<span id="anchor" style="margin-left:auto;flex:none;font-family:\'JetBrains Mono\',monospace;'
        f'font-size:10px;letter-spacing:.06em;color:{_MUTED};border:1px solid {_CARD_EDGE};'
        f'border-radius:2px;padding:3px 8px;background:rgba(255,255,255,.5);"></span>'
        '</div>'
        # chart
        f'<div id="c" style="width:100%;margin-top:6px;height:{chart_h}px;"></div>'
        # footer：pp 徽章 + 来源
        f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;'
        f'border-top:1px solid {_RULE};padding-top:9px;margin-top:2px;">'
        f'<span id="sp" style="display:inline-flex;gap:14px;flex-wrap:wrap;"></span>'
        f'<span style="margin-left:auto;font-size:11px;color:{_FAINT};">{src_line}</span>'
        '</div>'
        '</div>'
        f'{lib}{TAG}>{echarts_boot.MOUNT_JS}{ETAG}{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, iframe_h


def render_hc_glossary(g: dict, *, height: int = 330) -> tuple[str, int]:
    """「释义 · GLOSSARY」结构化对照卡（zip4 设计新增，替换旧 md_note 版本）。

    配色 = **近白淡色卡**（George 2026-07-10 两轮反馈：既不要与图表卡同款
    cream 玻璃、也不要墨黑——要"跟白色差不多"的淡色）：#fffdf9 近白底 +
    软 hairline + 3px 红左肋 + 红 eyebrow。比 .45/.55 cream 玻璃图表卡白一档，
    层级可分但整页保持浅色。

    g = i18n 文案 dict：eyebrow/title/sub_right/comp_label/feat_label/how_label/
        note_right + 每侧 badge{1,2}/name{1,2}/tag{1,2}/chip{1,2}{a,b}/comp{1,2}/
        feat{1,2} + how1/how2（可含 <b> 与强调 span）。
    """
    mono = "'JetBrains Mono',monospace"
    font_face = theme.FONT_FACE_CSS.strip()
    BG = "#fffdf9"                       # 近白（暖调，比 cream 玻璃卡白一档）
    EDGE = "#e4d2bd"                     # PAPER_EDGE_SOFT

    def _chip(txt: str) -> str:
        return (f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;'
                f'border:1px solid {_CARD_EDGE};border-radius:2px;padding:2px 7px;'
                'background:#fff;">' + txt + '</span>')

    def _side(badge: str, badge_bg: str, name: str, tag: str,
              chip_a: str, chip_b: str, comp: str, feat: str, first: bool) -> str:
        pad = ('padding-right:22px;' if first
               else f'padding-left:22px;border-left:1px solid {_CTRL_SEP};')
        return (
            f'<div style="{pad}display:flex;flex-direction:column;gap:9px;">'
            '<div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;">'
            f'<span style="font-family:{mono};font-size:10.5px;font-weight:700;color:{_CREAM};'
            f'background:{badge_bg};padding:2px 7px;border-radius:2px;letter-spacing:.04em;">{badge}</span>'
            f'<span style="font-size:13.5px;font-weight:700;color:{_INK};">{name}</span>'
            f'<span style="font-size:11px;color:{_MUTED};">{tag}</span></div>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap;">{_chip(chip_a)}{_chip(chip_b)}</div>'
            '<div style="display:grid;grid-template-columns:40px 1fr;gap:6px 10px;'
            'font-size:12.5px;line-height:1.65;color:#4a4a4a;">'
            f'<span style="font-family:{mono};font-size:10px;color:{_FAINT};padding-top:3px;">{g["comp_label"]}</span>'
            f'<span>{comp}</span>'
            f'<span style="font-family:{mono};font-size:10px;color:{_FAINT};padding-top:3px;">{g["feat_label"]}</span>'
            f'<span>{feat}</span></div></div>'
        )

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        f"b{{color:{_INK};}}"
        "@media (max-width:680px){.gl-grid{grid-template-columns:1fr !important;}}"
        "</style></head><body>"
        f'<div style="background:{BG};border:1px solid {EDGE};border-radius:2px;'
        f'border-left:3px solid {_RED};">'
        '<div style="display:flex;align-items:baseline;gap:12px;padding:14px 20px 0;flex-wrap:wrap;">'
        f'<span style="font-family:{mono};font-size:10px;letter-spacing:.14em;text-transform:uppercase;'
        f'font-weight:600;color:{_RED};">{g["eyebrow"]}</span>'
        f'<span style="font-size:14.5px;font-weight:600;color:{_INK};">{g["title"]}</span>'
        f'<span style="margin-left:auto;font-size:11.5px;color:{_MUTED};">{g["sub_right"]}</span></div>'
        '<div class="gl-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:0;padding:12px 20px 14px;">'
        + _side(g["badge1"], _RED, g["name1"], g["tag1"], g["chip1a"], g["chip1b"],
                g["comp1"], g["feat1"], True)
        + _side(g["badge2"], _INK, g["name2"], g["tag2"], g["chip2a"], g["chip2b"],
                g["comp2"], g["feat2"], False)
        + '</div>'
        '<div style="display:flex;align-items:baseline;gap:20px;flex-wrap:wrap;'
        f'border-top:1px solid {_RULE};padding:10px 20px 12px;">'
        f'<span style="font-family:{mono};font-size:10px;letter-spacing:.12em;font-weight:600;'
        f'color:{_MUTED};">{g["how_label"]}</span>'
        f'<span style="font-size:12.5px;color:#4a4a4a;">{g["how1"]}</span>'
        f'<span style="font-size:12.5px;color:#4a4a4a;">{g["how2"]}</span>'
        f'<span style="margin-left:auto;font-size:11px;color:{_FAINT};">{g["note_right"]}</span>'
        '</div></div></body></html>'
    )
    return doc, height


def render_ink_note(eyebrow: str, body_html: str, *, height: int = 210) -> tuple[str, int]:
    """近白淡色释义卡（prose 版）——「怎么读这张图」类长文释义。

    与 render_hc_glossary 同一近白卡语言（#fffdf9 + 软 hairline + 红左肋 +
    红 eyebrow）。函数名沿用（调用方已接线）；曾短暂为墨黑版，George 拍板改淡色。
    body_html 为已转 <b> 的 HTML（页面侧把 markdown **粗体** 转成 <b>）。
    """
    mono = "'JetBrains Mono',monospace"
    font_face = theme.FONT_FACE_CSS.strip()
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        f"b{{color:{_INK};}}"
        "</style></head><body>"
        f'<div style="background:#fffdf9;border:1px solid #e4d2bd;border-left:3px solid {_RED};'
        'border-radius:2px;padding:14px 20px 16px;">'
        f'<div style="font-family:{mono};font-size:10px;letter-spacing:.14em;text-transform:uppercase;'
        f'font-weight:600;color:{_RED};margin-bottom:9px;">' + eyebrow + '</div>'
        '<div style="font-size:12.5px;line-height:1.75;color:#4a4a4a;">'
        + body_html + '</div></div></body></html>'
    )
    return doc, height


def render_history_panel(panel: dict, *, prefer_cn: bool = True) -> tuple[str, int]:
    """HSHCI 全周期绝对点位卡 —— 与 render_panel 同款卡片 chrome（白玻璃 + accent 条
    + kicker + 墨黑 tooltip + 端点红点 + footer 徽章行），但无窗口控件（月度里程碑
    叙事图，5D/1M 无意义）；右上 chip 为口径说明而非锚定日。

    panel = {
      "kicker": str, "title": str, "chip": str, "accent": hex, "chart_h": int,
      "src": str, "asof": iso, "name": str（series 名，tooltip/legend 用）,
      "dates": [iso], "closes": [float],
      "anns": [{"d": iso, "v": float, "t": str, "pos": echarts label position}],
      "chips": [{"k": str, "v": "+x.x%" str, "neg": bool}],
    }
    """
    chart_h = int(panel.get("chart_h", 340))
    iframe_h = chart_h + _CHROME_H
    mono = "'JetBrains Mono',monospace"
    font_face = theme.FONT_FACE_CSS.strip()

    payload = json.dumps({
        "name": panel["name"],
        "pts": [[d, float(v)] for d, v in zip(panel["dates"], panel["closes"])],
        "anns": panel.get("anns", []),
    }, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    src_line = (f"来源：{panel['src']}，截至 {panel['asof']}。" if prefer_cn
                else f"Source: {panel['src']}, as of {panel['asof']}.")

    chips_html = "".join(
        '<span style="display:inline-flex;align-items:baseline;gap:6px;">'
        f'<span style="font-family:{mono};font-size:10.5px;color:{_MUTED};">{c["k"]}</span>'
        f'<span style="font-family:{mono};font-size:12px;font-weight:700;'
        f'font-variant-numeric:tabular-nums;color:{_RED if c.get("neg") else _TEAL};">{c["v"]}</span></span>'
        for c in panel.get("chips", [])
    )

    legend_html = (
        '<span style="display:inline-flex;align-items:center;gap:7px;">'
        '<svg width="26" height="10" style="flex:none;display:block;">'
        f'<line x1="1" y1="5" x2="25" y2="5" stroke="{_RED}" stroke-width="2.4"></line></svg>'
        f'<span style="font-size:12.5px;color:{theme.INK_2};">{panel["name"]}</span></span>'
    )

    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    lib = f'{TAG} src="{_ECHARTS_SRC}">{ETAG}'

    js = r"""
var P = __PAYLOAD__;
var MONO = "'JetBrains Mono',monospace";
mountEChart('c', function(){
  var last = P.pts[P.pts.length-1];
  return {
    animation:true,
    grid:{ left:54, right:64, top:26, bottom:28 },
    xAxis:{ type:'time',
      axisLine:{ lineStyle:{ color:'__INK__' } },
      axisTick:{ lineStyle:{ color:'__INK__' } },
      axisLabel:{ color:'__MUTED__', fontFamily:MONO, fontSize:10.5, hideOverlap:true,
        formatter:{ year:'{yyyy}', month:'{yyyy}' } },
      splitLine:{ show:true, lineStyle:{ color:'__GRID__', width:1 } } },
    yAxis:{ type:'value', min:0,
      axisLine:{ show:true, lineStyle:{ color:'__INK__' } },
      axisLabel:{ color:'__MUTED__', fontFamily:MONO, fontSize:10.5,
        formatter:function(v){ return v.toLocaleString('en-US'); } },
      splitLine:{ lineStyle:{ color:'__GRID__', width:1 } }, splitNumber:4 },
    tooltip:{ trigger:'axis', confine:true,
      backgroundColor:'__INK__', borderWidth:0, padding:[9,12],
      textStyle:{ color:'__CREAM__', fontFamily:MONO, fontSize:11 },
      axisPointer:{ type:'line', lineStyle:{ color:'__MUTED__', type:[3,3] } },
      formatter:function(params){
        var p = params[0];
        var ts = p.value[0];
        var dt = typeof ts === 'string' ? ts.slice(0,7) : new Date(ts).toISOString().slice(0,7);
        return '<div style="font-weight:700;">'+dt+'</div>' +
          '<div style="display:flex;gap:10px;align-items:baseline;margin-top:3px;">' +
          '<span style="color:'+p.color+';">━</span><span style="opacity:.8;">'+p.seriesName+'</span>' +
          '<b style="margin-left:auto;padding-left:14px;">'+Math.round(p.value[1]).toLocaleString('en-US')+'</b></div>';
      } },
    series:[{
      type:'line', name:P.name, showSymbol:false, animationDuration:400,
      data:P.pts,
      lineStyle:{ width:2.4, color:'__RED__' },
      itemStyle:{ color:'__RED__' },
      emphasis:{ disabled:true },
      areaStyle:{ color:'rgba(200,16,46,0.05)' },
      markPoint:{ silent:true, symbol:'circle', symbolSize:7,
        itemStyle:{ color:'__RED__' },
        label:{ show:true, fontFamily:MONO, fontSize:10, color:'#4a4a4a', fontWeight:600 },
        data:P.anns.map(function(a){
          return { coord:[a.d, a.v], label:{ formatter:a.t, position:a.pos || 'top' } };
        }).concat([{ coord:[last[0], last[1]], symbolSize:6, label:{ show:false } }])
      }
    }]
  };
});
"""
    js = (js.replace("__PAYLOAD__", payload)
            .replace("__INK__", _INK).replace("__CREAM__", _CREAM)
            .replace("__MUTED__", _MUTED).replace("__GRID__", _GRID)
            .replace("__RED__", _RED))

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        "</style></head><body>"
        f'<div style="background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);'
        f'backdrop-filter:blur(10px);border:1px solid {_CARD_EDGE};'
        f'border-top:2px solid {panel.get("accent", _RED)};border-radius:2px;'
        f'padding:14px 20px 12px;display:flex;flex-direction:column;height:{iframe_h - 8}px;">'
        '<div style="display:flex;align-items:flex-start;gap:12px;">'
        '<div style="min-width:0;">'
        f'<div style="font-family:{mono};font-size:10px;letter-spacing:.14em;'
        f'text-transform:uppercase;font-weight:600;color:{_MUTED};">{panel["kicker"]}</div>'
        f'<div style="font-size:15.5px;font-weight:600;color:{_INK};margin-top:4px;'
        f'line-height:1.35;">{panel["title"]}</div></div>'
        f'<span style="margin-left:auto;flex:none;font-family:{mono};font-size:10px;'
        f'letter-spacing:.06em;color:{_MUTED};border:1px solid {_CARD_EDGE};border-radius:2px;'
        f'padding:3px 8px;background:rgba(255,255,255,.5);">{panel["chip"]}</span>'
        '</div>'
        f'<div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-top:10px;">{legend_html}</div>'
        f'<div id="c" style="width:100%;margin-top:6px;height:{chart_h}px;"></div>'
        f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;'
        f'border-top:1px solid {_RULE};padding-top:9px;margin-top:2px;">'
        f'<span style="display:inline-flex;gap:14px;flex-wrap:wrap;">{chips_html}</span>'
        f'<span style="margin-left:auto;font-size:11px;color:{_FAINT};">{src_line}</span>'
        '</div></div>'
        f'{lib}{TAG}>{echarts_boot.MOUNT_JS}{ETAG}{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, iframe_h
