"""策略表现 Hero(大胆 + 动效)— lib/strategy_hero.py
==============================================================

渲染策略页顶部的「tearsheet hero」:左侧 56px 巨号累计收益(count-up 动画)+ 基准/超额 α,
右侧净值曲线(ECharts draw-in 动画 + 终点标签 + 十字光标),底部 7 格 KPI tile(数字 count-up)。

Wave-2 reskin(2026-07-04): 平面卡 → 玻璃卡(rgba .55 + blur14 + 红顶边 3px);双 radial
洗层;mono 化字号;FONT_DISPLAY(Space Grotesk);竖线 #e4d2bd;MDD #c8102e(CONTRACT D2)。
render_compare_chart(#cmp) 整体不动。

与 ui.render_html_table / heatmap 同套路:用 st.iframe(self-contained HTML) 渲染。
ECharts 自托管(app/static/echarts.min.js)——与 Inter/JetBrains 同理,国内访问 jsdelivr/
unpkg CDN 不稳;/app/static 路径在 components.html srcdoc iframe 内也解析(继承父页 base URL)。
动效/JS 全在 iframe 内,不碰 Streamlit 组件。

调用(在 pages/4_Strategy_Picks.py,拿到 portfolio / benchmark 曲线后):
    from lib import strategy_hero
    strategy_hero.render(
        strat_name="港股高股息选股", strat_dates=dates, strat_curve=port_vals,   # rebased=100
        bench_name="恒生高股息 30", bench_curve=bench_vals,
        cum_ret=..., bench_ret=..., alpha_pp=...,
        pick_date=..., n_hold=..., pool=..., days=...,
        wins=..., n_total=..., mdd=..., sharpe=...,
        bench_code="3466.HK", bench_sub="恒生高股息 30",
        as_of=..., source=...,
    )
"""
from __future__ import annotations

import json
from html import escape as _esc

from lib import theme
from lib import echarts_boot

# 自托管(China 安全)+ 相对路径(NO 前导 /):云端 Streamlit 服务在 /~/+/ 前缀下,srcdoc iframe
# baseURI = 该前缀;相对 "app/static/..." 云端解析为 /~/+/app/static/...(2026-07-01 实机 load ✓),
# 本地(无前缀)解析为 /app/static/...。**禁改回绝对 "/app/static/..."** —— 云端丢前缀 → 撞 login
# 重定向 → echarts 永远 undefined → 全站图空白(旧「0 宽竞态」诊断错靶,真因是此路径)。
# 若要回退 CDN(本地快速验证),改成 "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"。
ECHARTS_SRC = "app/static/echarts.min.js"


def _kpi_tile(label: str, value_attr: str, suffix: str = "", color: str = None,
              sub: str = "", static: str = None) -> str:
    """一格 KPI。static 给定 = 不做 count-up(如选股日/基准);否则用 data-count 由 JS count-up。"""
    t = theme
    col = color or t.INK
    val_html = (f'<span class="kh-num" style="color:{col}">{static}</span>'
                if static is not None else
                f'<span class="kh-num" data-count="{value_attr}" style="color:{col}">0</span>')
    sub_html = f'<span class="kh-sub">{sub}</span>' if sub else ""
    return (f'<div class="kh-tile"><span class="kh-lbl">{_esc(label)}</span>'
            f'<div class="kh-val">{val_html}{("<span class=kh-suf>" + suffix + "</span>") if suffix else ""} {sub_html}</div></div>')


def render(*, strat_name, strat_dates, strat_curve, bench_name, bench_curve,
           cum_ret, bench_ret, alpha_pp, pick_date, n_hold, pool, days,
           wins, n_total, mdd, sharpe, bench_code, bench_sub,
           as_of, source) -> None:
    import streamlit as st

    t = theme
    # Sign-color the strategy's own signals (cumulative + alpha) — a NEGATIVE return
    # must read red, not teal (港美股 convention; the reference hardcoded UP and would
    # paint a loss green). Benchmark stays neutral ink (a reference, not a signal).
    _cum_col = t.UP if cum_ret >= 0 else t.CMSI_RED   # wave-2 D2: negative on hero surface = #c8102e
    _alpha_col = t.UP if alpha_pp >= 0 else t.CMSI_RED  # wave-2 D2: same
    data = {
        "dates": list(strat_dates),
        "strat": [round(float(v), 2) for v in strat_curve],
        "bench": [round(float(v), 2) for v in bench_curve],
        "stratName": strat_name, "benchName": bench_name,
        "RED": t.CMSI_RED, "INK3": t.INK_3, "INK": t.INK, "PAPER": t.PAPER,
        "RULE": t.PAPER_RULE, "INK4": t.INK_4, "INK2": t.INK_2,
        # Fonts go through json.dumps (NOT inlined as '{t.FONT_DISPLAY}') — the stack
        # contains single quotes, so inlining it inside a JS '...' literal breaks the
        # whole script (Unexpected identifier 'Space Grotesk'). json escapes them safely.
        # FONT_DISPLAY is Space Grotesk-first (wave-2 reskin surface font).
        "FONT": t.FONT_DISPLAY, "MONO": t.FONT_MONO,
    }
    # count-up 目标值
    counts = {
        "cum": cum_ret, "bench": bench_ret, "alpha": alpha_pp,
        "hold": n_hold, "days": days, "wins": wins, "mdd": abs(mdd), "sharpe": sharpe,
    }

    kpi_row = "".join([
        _kpi_tile("选股日", "", static=pick_date),
        _kpi_tile("持仓数", "hold", sub=f"/ 评分池 {pool}", color=t.INK),
        _kpi_tile("持有天数", "days", color=t.INK),
        _kpi_tile("胜率 Win", "wins", sub=f"/ {n_total}", color=t.UP),
        _kpi_tile("最大回撤 MDD", "mdd", suffix="%", color=t.CMSI_RED),  # wave-2 D2: #c8102e
        _kpi_tile("夏普 Sharpe", "sharpe", color=t.INK),
        _kpi_tile("基准", "", static=bench_code, sub=bench_sub),
    ])

    css = _CSS.format(
        RED=t.CMSI_RED, RED_DEEP=t.CMSI_RED_DEEP, PAPER=t.PAPER, PAPER_DEEP=t.PAPER_DEEP,
        PAPER_BAND=t.PAPER_BAND, RULE=t.PAPER_RULE, EDGE=t.PAPER_EDGE,
        EDGE_SOFT=t.PAPER_EDGE_SOFT,
        INK=t.INK, INK2=t.INK_2, INK3=t.INK_3, INK4=t.INK_4,
        UP=t.UP, UP_DEEP=t.UP_DEEP,
        FONT=t.FONT_DISPLAY, MONO=t.FONT_MONO, FACE=t.FONT_FACE_CSS,
    )

    body = f"""
    <div class="wash"></div>
    <div class="wrap">
      <div class="hero">
        <div class="hero-grid">
          <div class="hero-left">
            <div class="live">
              <div class="dot"></div>
              <span class="live-t">持续跟踪 · EOD</span>
            </div>
            <div class="strat-name">{_esc(strat_name)}</div>
            <div class="strat-sub">AI AGENT · 自 {pick_date} 建仓</div>
            <div class="big-wrap">
              <div class="big-lbl">累计收益 · CUMULATIVE</div>
              <div class="big-num" data-count="cum" data-sign="1" data-suf="%" style="color:{_cum_col}">+0.0%</div>
              <div class="big-foot">
                <div><div class="bf-lbl">基准 {_esc(bench_code)}</div>
                     <div class="bf-v" data-count="bench" data-sign="1" data-suf="%" style="color:{t.INK_2}">+0.0%</div></div>
                <div class="bf-div"><div class="bf-lbl red">超额 α · ALPHA</div>
                     <div class="bf-v" data-count="alpha" data-sign="1" data-suf="pp" style="color:{_alpha_col}">+0.0pp</div></div>
              </div>
            </div>
          </div>
          <div class="hero-right">
            <div class="chart-lbl">净值曲线 · rebased 起点 = 100</div>
            <div id="eq"></div>
          </div>
        </div>
        <div class="kpi-row">{kpi_row}</div>
      </div>
      <div class="provrow">SOURCE: {_esc(source)} · 截至 {_esc(as_of)} · 真实累计收益,非回测美化</div>
    </div>
    """

    doc = f"""<!doctype html><html><head><meta charset='utf-8'>
    <style>{css}</style></head><body>{body}
    <script src="{ECHARTS_SRC}"></script>
    <script>{echarts_boot.MOUNT_JS}</script>
    <script>
    const D = {json.dumps(data)};
    const C = {json.dumps(counts)};
    // ---- count-up ----
    function fmt(el, v) {{
      const sign = el.dataset.sign === '1' && v >= 0 ? '+' : '';
      const suf = el.dataset.suf || '';
      const neg = el.classList.contains('kh-num') && el.dataset.count === 'mdd' ? '-' : '';
      const dp = (el.dataset.count === 'sharpe') ? 2 : (Number.isInteger(C[el.dataset.count]) ? 0 : 1);
      el.textContent = neg + sign + v.toFixed(dp) + suf;
    }}
    const nodes = [...document.querySelectorAll('[data-count]')];
    const t0 = performance.now(), DUR = 1500;
    function tick(now) {{
      const raw = Math.min((now - t0) / DUR, 1), e = 1 - Math.pow(1 - raw, 3);
      nodes.forEach(el => fmt(el, C[el.dataset.count] * e));
      if (raw < 1) requestAnimationFrame(tick);
    }}
    requestAnimationFrame(tick);
    // ---- equity curve ----
    mountEChart('eq', function() {{
      return {{
        backgroundColor:'transparent', animationDuration:1900, animationEasing:'cubicOut',
        grid:{{left:44,right:96,top:52,bottom:28}},
        legend:{{top:16,right:8,data:[D.stratName,D.benchName],icon:'roundRect',
          itemWidth:18,itemHeight:2,itemGap:18,textStyle:{{color:D.INK2,fontFamily:D.FONT,fontSize:11}}}},
        tooltip:{{trigger:'axis',axisPointer:{{type:'line',lineStyle:{{color:D.INK4,type:'dashed'}}}},
          backgroundColor:D.INK,borderColor:D.INK,padding:[8,12],
          textStyle:{{color:D.PAPER,fontFamily:D.MONO,fontSize:11}},
          formatter:function(ps){{let h='<div style=\\'font-size:10px;color:#b8b1a8;margin-bottom:4px\\'>'+ps[0].name+'</div>';
            ps.forEach(p=>{{const r=(p.value-100).toFixed(1);h+='<div>'+p.marker+' '+p.seriesName+' <b>'+p.value.toFixed(1)+'</b> ('+(r>=0?'+':'')+r+'%)</div>';}});return h;}}}},
        xAxis:{{type:'category',data:D.dates,boundaryGap:false,axisTick:{{show:false}},
          axisLine:{{lineStyle:{{color:D.INK,width:1}}}},
          axisLabel:{{color:D.INK3,fontFamily:D.MONO,fontSize:10,interval:20}},splitLine:{{show:false}}}},
        yAxis:{{type:'value',scale:true,axisLine:{{show:false}},axisTick:{{show:false}},
          axisLabel:{{color:D.INK3,fontFamily:D.MONO,fontSize:10}},splitLine:{{lineStyle:{{color:D.RULE}}}}}},
        series:[
          {{name:D.stratName,type:'line',data:D.strat,smooth:true,symbol:'none',z:3,
            color:D.RED,
            lineStyle:{{width:2.2,color:D.RED}},
            areaStyle:{{color:new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(200,16,46,0.14)'}},{{offset:1,color:'rgba(200,16,46,0.01)'}}])}},
            endLabel:{{show:true,formatter:'策略 {{@[1]}}',color:D.RED,fontFamily:D.MONO,fontSize:11,fontWeight:700}}}},
          {{name:D.benchName,type:'line',data:D.bench,smooth:true,symbol:'none',z:2,
            color:D.INK3,
            lineStyle:{{width:1.5,color:D.INK3,type:'dashed'}},
            endLabel:{{show:true,formatter:'基准 {{@[1]}}',color:D.INK3,fontFamily:D.MONO,fontSize:11}}}}
        ]
      }};
    }});
    </script></body></html>"""

    st.iframe(doc, height=470)


def render_compare_chart(*, dates, lines, marker_date, marker_label,
                         title, source, height=460) -> None:
    """Multi-line overlay (v1/v2 + benchmarks) as a self-contained ECharts iframe —
    Hero-aligned look (cream, FT grid, NO Plotly modebar, draw-in animation, value
    endLabels). Replaces the old go.Figure compare chart.

    dates  : common ISO date axis (union of every line's dates, sorted).
    lines  : [{name, values (list; None = gap so a late-start line begins at its
             inception), color, dash ∈ solid/dashed/dotted, width}] in back→front order.
    marker_date / marker_label : ISO date + caption for a dotted vertical markLine
             (e.g. v2 inception); pass marker_date=None to omit.
    """
    import streamlit as st

    t = theme
    payload = {
        "dates": list(dates),
        "lines": lines,
        "marker": marker_date, "markerLabel": marker_label or "",
        "FONT": t.FONT_STACK, "MONO": t.FONT_MONO,
        "INK": t.INK, "INK2": t.INK_2, "INK3": t.INK_3, "INK4": t.INK_4,
        "PAPER": t.PAPER, "RULE": t.PAPER_RULE,
    }
    css = """
    {FACE}
    :root {{ color-scheme: light; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ background: {PAPER}; color: {INK}; font-family: {FONT};
      -webkit-font-smoothing: antialiased; font-feature-settings: 'tnum','ss01'; }}
    .cmp-wrap {{ border: 1px solid {EDGE}; background: {PAPER}; padding: 14px 16px 8px; }}
    .cmp-title {{ font-size: 13px; font-weight: 600; color: {INK}; margin-bottom: 2px; }}
    #cmp {{ width: 100%; height: {CHART_H}px; }}
    .cmp-prov {{ font-family: {MONO}; font-size: 11px; color: {INK3}; letter-spacing: .02em; margin-top: 8px; }}
    """.format(FACE=t.FONT_FACE_CSS, PAPER=t.PAPER, INK=t.INK, INK3=t.INK_3,
               EDGE=t.PAPER_EDGE, FONT=t.FONT_STACK, MONO=t.FONT_MONO,
               CHART_H=height - 96)

    doc = f"""<!doctype html><html><head><meta charset='utf-8'>
    <style>{css}</style></head><body>
    <div class="cmp-wrap"><div class="cmp-title">{_esc(title)}</div><div id="cmp"></div></div>
    <div class="cmp-prov">SOURCE: {_esc(source)}</div>
    <script src="{ECHARTS_SRC}"></script>
    <script>{echarts_boot.MOUNT_JS}</script>
    <script>
    const D = {json.dumps(payload)};
    mountEChart('cmp', function() {{
      const dash = {{solid:'solid', dashed:'dashed', dotted:'dotted'}};
      const series = D.lines.map((s, i) => ({{
        name: s.name, type: 'line', data: s.values, smooth: true, symbol: 'none',
        connectNulls: false, color: s.color, z: 2 + i,
        lineStyle: {{ width: s.width, color: s.color, type: dash[s.dash] || 'solid' }},
        endLabel: {{ show: true, distance: 4,
          formatter: function(p) {{ return p.value == null ? '' : (+p.value).toFixed(1); }},
          color: s.color, fontFamily: D.MONO, fontSize: 10, fontWeight: 700 }}
      }}));
      if (D.marker) series[series.length - 1].markLine = {{ silent: true, symbol: 'none',
        lineStyle: {{ color: D.INK3, type: 'dotted', width: 1 }},
        label: {{ formatter: D.markerLabel, color: D.INK3, fontFamily: D.MONO,
                 fontSize: 10, position: 'insideEndTop' }},
        data: [{{ xAxis: D.marker }}] }};
      return {{
        backgroundColor: 'transparent', animationDuration: 1500, animationEasing: 'cubicOut',
        grid: {{ left: 50, right: 66, top: 44, bottom: 30 }},
        legend: {{ top: 8, left: 0, data: D.lines.map(s => s.name), icon: 'roundRect',
          itemWidth: 18, itemHeight: 2, itemGap: 14,
          textStyle: {{ color: D.INK2, fontFamily: D.FONT, fontSize: 11 }} }},
        tooltip: {{ trigger: 'axis', axisPointer: {{ type:'line', lineStyle:{{color:D.INK4,type:'dashed'}} }},
          backgroundColor: D.INK, borderColor: D.INK, padding: [8,12],
          textStyle: {{ color: D.PAPER, fontFamily: D.MONO, fontSize: 11 }},
          formatter: function(ps) {{
            let h = '<div style=\\'font-size:10px;color:#b8b1a8;margin-bottom:4px\\'>' + ps[0].name + '</div>';
            ps.forEach(p => {{ if (p.value == null) return;
              const r = (p.value - 100).toFixed(1);
              h += '<div>' + p.marker + ' ' + p.seriesName + ' <b>' + (+p.value).toFixed(1) + '</b> (' + (r >= 0 ? '+' : '') + r + '%)</div>'; }});
            return h; }} }},
        xAxis: {{ type:'category', data:D.dates, boundaryGap:false, axisTick:{{show:false}},
          axisLine: {{ lineStyle:{{color:D.INK,width:1}} }},
          axisLabel: {{ color:D.INK3, fontFamily:D.MONO, fontSize:10, interval:Math.floor(D.dates.length/6) }},
          splitLine: {{ show:false }} }},
        yAxis: {{ type:'value', scale:true, axisLine:{{show:false}}, axisTick:{{show:false}},
          axisLabel: {{ color:D.INK3, fontFamily:D.MONO, fontSize:10 }},
          splitLine: {{ lineStyle:{{color:D.RULE}} }} }},
        series: series
      }};
    }});
    </script></body></html>"""

    st.iframe(doc, height=height)


# ─────────────────────────────────────────────────────────────────────────
# CSS(.format() 注入 token) — wave-2 reskin 2026-07-04
# 变更摘要: 玻璃卡(rgba .55+blur14+红顶边) / 双 radial 洗层 / mono 字族 /
#          巨号 56px / 脚注/KPI 值 17px / KPI label 10px /
#          左栏白纱+竖线 #e4d2bd / cmsiPulse 动画名
# ─────────────────────────────────────────────────────────────────────────
_CSS = """
{FACE}
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ height: 100%; background: {PAPER}; color: {INK}; font-family: {FONT};
  -webkit-font-smoothing: antialiased; font-feature-settings: 'tnum','ss01';
  position: relative; overflow: hidden; }}
.wash {{ position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%),
    radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%); }}
.wrap {{ position: relative; }}
.hero {{
  background: rgba(255,255,255,.55);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,.7);
  border-top: 3px solid {RED};
}}
.hero-grid {{ display: grid; grid-template-columns: 340px 1fr; }}
.hero-left {{ padding: 24px 26px; background: rgba(255,255,255,.35); overflow: hidden;
  position: relative; border-right: 1px solid {EDGE_SOFT}; display: flex; flex-direction: column; }}
.live {{ display: flex; align-items: center; gap: 8px; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: {UP}; animation: cmsiPulse 1.5s ease-in-out infinite; }}
@keyframes cmsiPulse {{ 0%,100% {{ opacity:1; transform:scale(1); }} 50% {{ opacity:.35; transform:scale(.82); }} }}
.live-t {{ font-family: {MONO}; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: {UP}; font-weight: 600; }}
.strat-name {{ font-size: 20px; font-weight: 600; color: {INK}; margin-top: 14px; }}
.strat-sub {{ font-family: {MONO}; font-size: 11px; color: {INK3}; margin-top: 4px; letter-spacing: .02em; }}
.big-wrap {{ margin-top: auto; padding-top: 24px; }}
.big-lbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.big-num {{ font-family: {MONO}; font-size: 56px; line-height: 60px; font-weight: 700; letter-spacing: -.03em;
  font-variant-numeric: tabular-nums lining-nums; margin-top: 6px; }}
.big-foot {{ display: flex; gap: 18px; margin-top: 16px; }}
.bf-lbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: {INK3}; font-weight: 600; }}
.bf-lbl.red {{ color: {RED}; }}
.bf-v {{ font-family: {MONO}; font-size: 17px; font-weight: 600; font-variant-numeric: tabular-nums; margin-top: 2px; }}
.bf-div .bf-v {{ font-weight: 700; }}
.bf-div {{ border-left: 1px solid {EDGE_SOFT}; padding-left: 18px; }}
.hero-right {{ padding: 16px 16px 6px; position: relative; }}
.chart-lbl {{ position: absolute; top: 18px; left: 22px; z-index: 2; font-family: {MONO}; font-size: 10px;
  letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
#eq {{ width: 100%; height: 290px; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(7,1fr); border-top: 1px solid {EDGE}; }}
.kh-tile {{ padding: 14px 16px; border-right: 1px solid {RULE}; }}
.kh-tile:last-child {{ border-right: none; }}
.kh-lbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.kh-val {{ margin-top: 8px; }}
.kh-num {{ font-family: {MONO}; font-size: 17px; font-weight: 600; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }}
.kh-suf {{ font-family: {MONO}; font-size: 14px; font-weight: 600; }}
.kh-sub {{ font-size: 11px; color: {INK3}; font-weight: 500; }}
.provrow {{ font-family: {MONO}; font-size: 11px; color: {INK3}; letter-spacing: .02em; margin-top: 8px; }}
@media (max-width: 860px) {{ .hero-grid {{ grid-template-columns: 1fr; }}
  .hero-left {{ border-right: none; border-bottom: 1px solid {RULE}; }}
  .kpi-row {{ grid-template-columns: repeat(3,1fr); }} }}
"""
