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
           as_of, source, currency=None, initial_capital=None,
           cap_label="初始资金", nav_label="当前净值", gain_label="累计盈亏") -> None:
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

    # --- Absolute-amount NAV block (初始资金 → 当前净值 + 累计盈亏) ---------------
    # Renders only when the caller supplies currency + initial_capital. The curve
    # stays normalized to 100 (chart axis unchanged); this block translates the
    # since-inception cum_ret into real money so the card carries the true book size,
    # not just "123.4% of base 100". current_nav = capital × (1 + cum_ret/100).
    nav_html = ""
    if currency and initial_capital:
        _cap = float(initial_capital)
        _nav = _cap * (1.0 + cum_ret / 100.0)
        _gain = _nav - _cap
        _gain_col = t.UP if _gain >= 0 else t.CMSI_RED
        # sign OUTSIDE the currency so a loss reads "-HKD 50,000", not "HKD -50,000".
        _gain_str = f"{'+' if _gain >= 0 else '-'}{_esc(currency)} {abs(_gain):,.0f}"
        nav_html = f"""
            <div class="nav-blk">
              <div class="nav-row">
                <span class="nav-lbl">{_esc(cap_label)}</span>
                <span class="nav-cap">{_esc(currency)} {_cap:,.0f}</span>
              </div>
              <div class="nav-row">
                <span class="nav-lbl">{_esc(nav_label)}</span>
                <span class="nav-now" style="color:{_cum_col}">{_esc(currency)} {_nav:,.0f}</span>
              </div>
              <div class="nav-row">
                <span class="nav-lbl">{_esc(gain_label)}</span>
                <span class="nav-gain" style="color:{_gain_col}">{_gain_str}</span>
              </div>
            </div>"""

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
            {nav_html}
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


def render_compare_chart(*, dates, lines, marker_date=None, marker_label="",
                         title, source, height=460, markers=None) -> None:
    """Multi-line overlay (v1/v2 + benchmarks) as a self-contained ECharts iframe —
    Hero-aligned look (cream, FT grid, NO Plotly modebar, draw-in animation, value
    endLabels). Replaces the old go.Figure compare chart.

    dates  : common ISO date axis (union of every line's dates, sorted).
    lines  : [{name, values (list; None = gap so a late-start line begins at its
             inception), color, dash ∈ solid/dashed/dotted, width}] in back→front order.
    marker_date / marker_label : ISO date + caption for a SINGLE dotted vertical
             markLine (back-compat); pass marker_date=None to omit.
    markers : [{date, label}] for MULTIPLE dotted vertical markLines (e.g. every
             rebalance handover in a chained-account chart). Takes precedence over
             marker_date when given; each dict → one dotted line + label.
    """
    import streamlit as st

    t = theme
    # Normalize the marker inputs into one list (multi `markers` wins; else wrap the
    # single marker_date for back-compat; else empty).
    _markers = list(markers) if markers else (
        [{"date": marker_date, "label": marker_label or ""}] if marker_date else [])
    payload = {
        "dates": list(dates),
        "lines": lines,
        "markers": _markers,
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
      if (D.markers && D.markers.length) series[series.length - 1].markLine = {{
        silent: true, symbol: 'none',
        lineStyle: {{ color: D.INK3, type: 'dotted', width: 1 }},
        label: {{ color: D.INK3, fontFamily: D.MONO, fontSize: 10,
                 position: 'insideEndTop' }},
        data: D.markers.map(function(m) {{ return {{ xAxis: m.date, label: {{ formatter: m.label }} }}; }}) }};
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


def render_gen_compare(
    *, dates, chain_curve, bench_curve, cmp_lines, chain_markers,
    nav_str, cum_str, alpha_str, gain_str, bench_cum_str,
    cards, kpi_tiles, chain_start, currency, capital_str,
    v6_pending, method_note, indep_title, indep_badge, indep_note,
    chain_bench_name, chain_acct_name, source, animate=True,
    show_method=True, show_independent=True,
) -> None:
    """FT-cream editorial recreation of 美国生科三代对比美化.dc.html — ONE
    self-contained st.iframe (same self-host + MOUNT_JS pattern as render()).

    Everything is data-driven from REAL series computed by the caller:
      dates        : common ISO/label x-axis for BOTH charts (union, sorted).
      chain_curve  : chained-account NAV rebased 100 (list, None-gapped to `dates`).
      bench_curve  : benchmark buy&hold rebased 100 (list, None-gapped).
      cmp_lines    : [{name,color,dash,width,values}] for the independent NAV=100 chart.
      chain_markers: [{date,label}] dotted rebalance handovers on the chain chart.
      nav_str/cum_str/alpha_str/gain_str : PRE-FORMATTED headline strings (final
                     values; the JS count-up eases 0→these using the numeric parse).
      cards        : 4 KPI cards [{label,sub,value,color,pending(bool)}] (v4/v5/v6/XBI).
      kpi_tiles    : 6 bottom tiles [{label,value,sub,color?}].
      chain_start  : ISO inception of the chained account (headline sub-line).
      v6_pending   : banner text (or "" to hide the v6-pending banner).
    """
    import streamlit as st

    t = theme
    payload = {
        "dates": list(dates),
        "chain": chain_curve, "bench": bench_curve,
        "cmpLines": cmp_lines, "chainMarkers": chain_markers,
        "chainBenchName": chain_bench_name, "chainAcctName": chain_acct_name,
        "RED": t.CMSI_RED, "UP": t.UP, "AMBER": "#E0A458",
        "INK": t.INK, "INK2": t.INK_2, "INK3": t.INK_3, "INK4": t.INK_4,
        "PAPER": t.PAPER, "RULE": t.PAPER_RULE,
        "FONT": t.FONT_DISPLAY, "MONO": t.FONT_MONO,
        "animate": bool(animate),
    }
    # count-up targets parsed from the pre-formatted headline strings (so the label
    # copy is the single source of truth for sign/decimals/suffix).
    def _num(s):
        import re as _re
        m = _re.search(r"-?[\d,]+\.?\d*", s or "")
        return float(m.group().replace(",", "")) if m else 0.0
    counts = {"nav": _num(nav_str), "cum": _num(cum_str),
              "alpha": _num(alpha_str), "gain": _num(gain_str)}
    fmts = {"nav": nav_str, "cum": cum_str, "alpha": alpha_str, "gain": gain_str}

    # ---- KPI cards (4) ----
    def _card(c):
        pending = c.get("pending")
        val = (f'<div class="bt-cardnum" style="color:{c["color"]}">{_esc(c["value"])}</div>'
               if not pending else
               '<div class="bt-cardpend"><span class="bt-cardnum" '
               'style="color:#b8b1a8">—</span>'
               '<span class="bt-badge">待录入</span></div>')
        return (f'<div class="bt-card" style="border-top-color:{c["color"]}">'
                f'<div class="bt-cardlbl">{_esc(c["label"])}</div>'
                f'<div class="bt-cardsub">{_esc(c.get("sub",""))}</div>{val}</div>')
    cards_html = "".join(_card(c) for c in cards)

    banner_html = ("" if not v6_pending else
        f'<div class="bt-banner"><span class="bt-banner-tag">v6 即将上线</span>'
        f'<span class="bt-banner-txt">{_esc(v6_pending)}</span></div>')

    # ---- 6 bottom KPI tiles ----
    def _tile(x):
        col = x.get("color") or t.INK
        return (f'<div class="bt-tile"><div class="bt-tlbl">{_esc(x["label"])}</div>'
                f'<div class="bt-tval" style="color:{col}">{_esc(x["value"])}</div>'
                f'<div class="bt-tsub">{_esc(x.get("sub",""))}</div></div>')
    tiles_html = "".join(_tile(x) for x in kpi_tiles)

    method_html = ("" if not (show_method and method_note) else
        f'<div class="bt-method"><div class="bt-method-eyebrow">口径 · 接续账户怎么算</div>'
        f'<p class="bt-method-p">{method_note}</p></div>')

    indep_html = ("" if not show_independent else f"""
      <div class="bt-sec">
        <span class="bt-sec-bar"></span>
        <span class="bt-sec-t">{_esc(indep_title)}</span>
        <span class="bt-sec-en">INDEPENDENT NAV PER VERSION</span>
      </div>
      <div class="bt-cmpwrap">
        <div class="bt-cmp-lbl">生物科技 v4 / v5 / v6 · 净值对比 · 基准锚定 v4 建仓日</div>
        {f'<div class="bt-cmp-badge">{_esc(indep_badge)}</div>' if indep_badge else ''}
        <div id="btcmp"></div>
      </div>
      <p class="bt-indep-note">{_esc(indep_note)}</p>""")

    css = _BT_CSS.format(
        RED=t.CMSI_RED, PAPER=t.PAPER, PAPER_DEEP=t.PAPER_DEEP, RULE=t.PAPER_RULE,
        EDGE=t.PAPER_EDGE, EDGE_SOFT=t.PAPER_EDGE_SOFT,
        INK=t.INK, INK2=t.INK_2, INK3=t.INK_3, INK4=t.INK_4,
        UP=t.UP, FONT=t.FONT_DISPLAY, MONO=t.FONT_MONO, FACE=t.FONT_FACE_CSS,
    )

    body = f"""
    <div class="bt-wash"></div>
    <div class="bt-wrap">
      <div class="bt-cards">{cards_html}</div>
      {banner_html}

      <div class="bt-sec">
        <span class="bt-sec-bar"></span>
        <span class="bt-sec-t">接续账户净值 · 跟随换仓</span>
        <span class="bt-sec-sub">同一笔本金一路持有</span>
        <span class="bt-sec-en">CHAINED ACCOUNT NAV</span>
      </div>

      <div class="bt-hero">
        <div class="bt-hero-grid">
          <div class="bt-hero-left">
            <div class="bt-live"><span class="bt-dot"></span>
              <span class="bt-live-t">持续跟踪 · TRACKING LIVE</span></div>
            <div class="bt-hname">{_esc(chain_acct_name)}</div>
            <div class="bt-hsub">AI AGENT · 自 {_esc(chain_start)} 建仓 · 本金 {_esc(currency)} {_esc(capital_str)}</div>
            <div class="bt-bigwrap">
              <div class="bt-biglbl">当前净值 · CURRENT NAV</div>
              <div class="bt-bigrow">
                <span class="bt-cur">{_esc(currency)}</span>
                <span class="bt-big" data-count="nav">0</span>
              </div>
              <div class="bt-foot">
                <div><div class="bt-flbl">累计收益</div>
                  <div class="bt-fv" data-count="cum" style="color:{t.UP}">0</div></div>
                <div class="bt-fdiv"><div class="bt-flbl red">超额 α · ALPHA</div>
                  <div class="bt-fv" data-count="alpha" style="color:{t.UP}">0</div></div>
              </div>
              <div class="bt-gain"><span data-count="gain">0</span> 盈亏 · 基准 {_esc(chain_bench_name)} {_esc(bench_cum_str)}（买入持有）</div>
            </div>
          </div>
          <div class="bt-hero-right">
            <div class="bt-chart-lbl">账户净值 · 建仓日 = 100 · 虚线为换仓日</div>
            <div id="btchain"></div>
          </div>
        </div>
        <div class="bt-tiles">{tiles_html}</div>
      </div>
      <div class="bt-prov">SOURCE: {_esc(source)}</div>

      {method_html}
      {indep_html}
    </div>
    """

    doc = f"""<!doctype html><html><head><meta charset='utf-8'>
    <style>{css}</style></head><body>{body}
    <script src="{ECHARTS_SRC}"></script>
    <script>{echarts_boot.MOUNT_JS}</script>
    <script>
    const D = {json.dumps(payload)};
    const C = {json.dumps(counts)};
    const F = {json.dumps(fmts)};
    // ---- count-up: eases 0→target, formats to match the pre-formatted strings ----
    function fmtCount(el, frac) {{
      const key = el.dataset.count, tgt = C[key], s = F[key] || '';
      const cur = tgt * frac;
      if (key === 'nav' || key === 'gain') {{
        // integer money w/ thousands sep; preserve leading sign + currency prefix
        const sign = s.trim().startsWith('-') ? '-' : (s.trim().startsWith('+') ? '+' : '');
        const pre = (s.match(/[A-Za-z]+/) || [''])[0];  // e.g. USD
        const body = Math.round(Math.abs(cur)).toLocaleString('en-US');
        el.textContent = (sign ? sign + ' ' : '') + (pre ? pre + ' ' : '') + body;
      }} else {{
        const sign = cur >= 0 ? '+' : '';
        const suf = /pp/.test(s) ? 'pp' : (/%/.test(s) ? '%' : '');
        el.textContent = sign + cur.toFixed(2) + suf;
      }}
    }}
    const nodes = [...document.querySelectorAll('[data-count]')];
    if (D.animate) {{
      const t0 = performance.now(), DUR = 1500;
      (function tick(now) {{
        const raw = Math.min((now - t0) / DUR, 1), e = 1 - Math.pow(1 - raw, 3);
        nodes.forEach(el => fmtCount(el, e));
        if (raw < 1) requestAnimationFrame(tick);
      }})(performance.now());
    }} else {{ nodes.forEach(el => fmtCount(el, 1)); }}

    const DASH = {{solid:'solid', dashed:'dashed', dotted:'dotted'}};
    function base() {{ return {{
      backgroundColor:'transparent', animationDuration: D.animate?1900:0, animationEasing:'cubicOut',
      tooltip:{{trigger:'axis',axisPointer:{{type:'line',lineStyle:{{color:D.INK4,type:'dashed'}}}},
        backgroundColor:D.INK,borderColor:D.INK,padding:[8,12],
        textStyle:{{color:D.PAPER,fontFamily:D.MONO,fontSize:11}},
        formatter:function(ps){{let h='<div style=\\'font-size:10px;color:#b8b1a8;margin-bottom:4px\\'>'+ps[0].name+'</div>';
          ps.forEach(p=>{{if(p.value==null)return;const r=(p.value-100).toFixed(1);
            h+='<div>'+p.marker+' '+p.seriesName+' <b>'+(+p.value).toFixed(1)+'</b> ('+(r>=0?'+':'')+r+'%)</div>';}});return h;}}}},
      xAxis:{{type:'category',data:D.dates,boundaryGap:false,axisTick:{{show:false}},
        axisLine:{{lineStyle:{{color:D.INK,width:1}}}},
        axisLabel:{{color:D.INK3,fontFamily:D.MONO,fontSize:10,interval:Math.floor(D.dates.length/7)}},splitLine:{{show:false}}}},
      yAxis:{{type:'value',scale:true,axisLine:{{show:false}},axisTick:{{show:false}},
        axisLabel:{{color:D.INK3,fontFamily:D.MONO,fontSize:10}},splitLine:{{lineStyle:{{color:D.RULE}}}}}},
    }}; }}
    function endLbl(color,prefix,bold) {{ return {{show:true,color,fontFamily:D.MONO,fontSize:11,
      fontWeight:bold?700:400,distance:8,formatter:function(p){{return prefix+' '+(p.value==null?'':(+p.value).toFixed(1));}}}}; }}

    mountEChart('btchain', function() {{
      const o = base();
      o.grid = {{left:44,right:82,top:52,bottom:28}};
      o.legend = {{top:16,right:8,data:[D.chainBenchName,D.chainAcctName],icon:'roundRect',
        itemWidth:18,itemHeight:2,itemGap:18,textStyle:{{color:D.INK2,fontFamily:D.FONT,fontSize:11}}}};
      const acct = {{name:D.chainAcctName,type:'line',data:D.chain,smooth:true,symbol:'none',z:3,
        lineStyle:{{width:2.4,color:D.RED}},
        areaStyle:{{color:new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(200,16,46,0.14)'}},{{offset:1,color:'rgba(200,16,46,0.01)'}}])}},
        endLabel:endLbl(D.RED,'账户',true)}};
      if (D.chainMarkers && D.chainMarkers.length) acct.markLine = {{silent:true,symbol:'none',
        lineStyle:{{color:D.RED,type:'dashed',width:1}},
        label:{{color:D.RED,fontFamily:D.MONO,fontSize:10,fontWeight:700,position:'insideEndTop',distance:6}},
        data:D.chainMarkers.map(function(m){{return {{xAxis:m.date,label:{{formatter:m.label}}}};}})}};
      o.series = [
        {{name:D.chainBenchName,type:'line',data:D.bench,smooth:true,symbol:'none',z:2,
          lineStyle:{{width:1.5,color:D.INK3,type:'dashed'}},endLabel:endLbl(D.INK3,'基准')}},
        acct,
      ];
      return o;
    }});

    if (document.getElementById('btcmp')) mountEChart('btcmp', function() {{
      const o = base();
      o.grid = {{left:44,right:78,top:52,bottom:28}};
      o.legend = {{top:16,right:8,data:D.cmpLines.map(s=>s.name),icon:'roundRect',
        itemWidth:18,itemHeight:2,itemGap:16,textStyle:{{color:D.INK2,fontFamily:D.FONT,fontSize:11}}}};
      o.series = D.cmpLines.map(function(s,i){{return {{
        name:s.name,type:'line',data:s.values,smooth:true,symbol:'none',connectNulls:false,z:2+i,
        lineStyle:{{width:s.width,color:s.color,type:DASH[s.dash]||'solid'}},
        endLabel:{{show:true,distance:4,color:s.color,fontFamily:D.MONO,fontSize:10,fontWeight:700,
          formatter:function(p){{return p.value==null?'':(+p.value).toFixed(1);}}}}
      }};}});
      return o;
    }});
    </script></body></html>"""

    st.iframe(doc, height=1180)


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
.nav-blk {{ margin-top: 16px; padding-top: 14px; border-top: 1px solid {EDGE_SOFT};
  display: flex; flex-direction: column; gap: 6px; }}
.nav-row {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }}
.nav-lbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .1em; text-transform: uppercase;
  color: {INK3}; font-weight: 600; }}
.nav-cap {{ font-family: {MONO}; font-size: 13px; font-weight: 600; color: {INK2};
  font-variant-numeric: tabular-nums; }}
.nav-now {{ font-family: {MONO}; font-size: 18px; font-weight: 700; letter-spacing: -.01em;
  font-variant-numeric: tabular-nums; }}
.nav-gain {{ font-family: {MONO}; font-size: 13px; font-weight: 600;
  font-variant-numeric: tabular-nums; }}
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


# ─────────────────────────────────────────────────────────────────────────
# CSS for render_gen_compare (FT-cream 三代对比 美化.dc.html recreation).
# .format() token injection → literal braces doubled.
# ─────────────────────────────────────────────────────────────────────────
_BT_CSS = """
{FACE}
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: {PAPER}; color: {INK}; font-family: {FONT};
  -webkit-font-smoothing: antialiased; font-feature-settings: 'tnum','ss01';
  position: relative; }}
@keyframes cmsiPulse {{ 0%,100% {{ opacity:1; transform:scale(1); }} 50% {{ opacity:.35; transform:scale(.82); }} }}
.bt-wash {{ position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%),
    radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%); }}
.bt-wrap {{ position: relative; }}

/* ---- 4 KPI cards ---- */
.bt-cards {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 14px; }}
.bt-card {{ background: rgba(255,255,255,.55); border: 1px solid {EDGE};
  border-top: 2px solid {INK}; border-radius: 2px; padding: 16px 18px 15px; }}
.bt-cardlbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.bt-cardsub {{ font-size: 11px; color: {INK4}; margin-top: 2px; }}
.bt-cardnum {{ font-family: {MONO}; font-size: 32px; line-height: 1; font-weight: 700; letter-spacing: -.02em; font-variant-numeric: tabular-nums; margin-top: 12px; }}
.bt-cardpend {{ display: flex; align-items: baseline; gap: 10px; margin-top: 12px; }}
.bt-badge {{ font-family: {MONO}; font-size: 10px; font-weight: 700; letter-spacing: .06em; color: {RED}; border: 1px solid {RED}; border-radius: 2px; padding: 2px 7px; }}

/* ---- v6 pending banner ---- */
.bt-banner {{ display: flex; align-items: baseline; gap: 10px; background: {PAPER_DEEP};
  border-left: 3px solid {RED}; padding: 11px 16px; margin-top: 14px; }}
.bt-banner-tag {{ font-family: {MONO}; font-size: 10px; font-weight: 700; letter-spacing: .1em; color: {RED}; flex: none; }}
.bt-banner-txt {{ font-size: 12.5px; line-height: 1.6; color: {INK2}; }}

/* ---- section headers ---- */
.bt-sec {{ display: flex; align-items: baseline; gap: 10px; margin: 44px 0 14px;
  border-top: 1px solid {INK}; padding-top: 12px; flex-wrap: wrap; }}
.bt-sec-bar {{ width: 4px; height: 17px; background: {RED}; display: inline-block; align-self: center; }}
.bt-sec-t {{ font-size: 20px; font-weight: 600; color: {INK}; }}
.bt-sec-sub {{ font-size: 13px; color: {INK3}; }}
.bt-sec-en {{ margin-left: auto; font-family: {MONO}; font-size: 10.5px; letter-spacing: .08em; color: {INK3}; text-transform: uppercase; }}

/* ---- chained hero tearsheet ---- */
.bt-hero {{ background: rgba(255,255,255,.55); backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,.7); border-top: 3px solid {RED}; }}
.bt-hero-grid {{ display: grid; grid-template-columns: 340px 1fr; }}
.bt-hero-left {{ position: relative; padding: 24px 28px; border-right: 1px solid {EDGE_SOFT};
  display: flex; flex-direction: column; background: rgba(255,255,255,.35); }}
.bt-live {{ display: flex; align-items: center; gap: 8px; }}
.bt-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {UP}; display: inline-block; animation: cmsiPulse 1.5s ease-in-out infinite; }}
.bt-live-t {{ font-family: {MONO}; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: {UP}; font-weight: 600; }}
.bt-hname {{ font-size: 20px; font-weight: 600; color: {INK}; margin-top: 14px; }}
.bt-hsub {{ font-family: {MONO}; font-size: 11px; color: {INK3}; margin-top: 4px; letter-spacing: .02em; }}
.bt-bigwrap {{ margin-top: auto; padding-top: 26px; }}
.bt-biglbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.bt-bigrow {{ display: flex; align-items: baseline; gap: 8px; margin-top: 6px; }}
.bt-cur {{ font-family: {MONO}; font-size: 16px; font-weight: 600; color: {INK3}; }}
.bt-big {{ font-family: {MONO}; font-size: 46px; line-height: 50px; font-weight: 700; letter-spacing: -.03em; color: {UP}; font-variant-numeric: tabular-nums lining-nums; }}
.bt-foot {{ display: flex; gap: 18px; margin-top: 16px; }}
.bt-flbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: {INK3}; font-weight: 600; }}
.bt-flbl.red {{ color: {RED}; }}
.bt-fv {{ font-family: {MONO}; font-size: 17px; font-weight: 700; font-variant-numeric: tabular-nums; margin-top: 2px; }}
.bt-fdiv {{ border-left: 1px solid {EDGE_SOFT}; padding-left: 18px; }}
.bt-gain {{ font-family: {MONO}; font-size: 11px; color: {INK3}; margin-top: 12px; }}
.bt-hero-right {{ padding: 18px 18px 8px; position: relative; }}
.bt-chart-lbl {{ position: absolute; top: 18px; left: 22px; z-index: 2; font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
#btchain {{ width: 100%; height: 300px; }}
.bt-tiles {{ display: grid; grid-template-columns: repeat(6,1fr); border-top: 1px solid {EDGE}; }}
.bt-tile {{ padding: 14px 16px; border-right: 1px solid {RULE}; }}
.bt-tile:last-child {{ border-right: none; }}
.bt-tlbl {{ font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.bt-tval {{ font-family: {MONO}; font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; margin-top: 8px; letter-spacing: -.01em; }}
.bt-tsub {{ font-size: 10px; color: {INK3}; margin-top: 1px; }}
.bt-prov {{ font-family: {MONO}; font-size: 11px; color: {INK3}; letter-spacing: .02em; margin-top: 8px; }}

/* ---- method note ---- */
.bt-method {{ background: {PAPER_DEEP}; border-left: 3px solid {RED}; padding: 18px 24px; margin-top: 22px; }}
.bt-method-eyebrow {{ font-size: 11px; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; color: {RED}; margin-bottom: 10px; }}
.bt-method-p {{ font-size: 13px; line-height: 1.7; color: {INK2}; margin: 0; }}
.bt-method-p b {{ color: {INK}; }}

/* ---- independent NAV chart ---- */
.bt-cmpwrap {{ background: rgba(255,255,255,.55); backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px); border: 1px solid rgba(255,255,255,.7); padding: 18px 18px 8px; position: relative; }}
.bt-cmp-lbl {{ position: absolute; top: 18px; left: 22px; z-index: 2; font-family: {MONO}; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: {INK3}; }}
.bt-cmp-badge {{ position: absolute; top: 14px; right: 18px; z-index: 2; font-family: {MONO}; font-size: 10px; font-weight: 700; letter-spacing: .06em; color: {RED}; border: 1px solid {RED}; border-radius: 2px; padding: 3px 8px; background: rgba(255,241,229,.7); }}
#btcmp {{ width: 100%; height: 330px; }}
.bt-indep-note {{ font-size: 12px; line-height: 1.65; color: {INK3}; margin: 8px 0 0; max-width: 980px; }}

@media (max-width: 860px) {{
  .bt-hero-grid {{ grid-template-columns: 1fr; }}
  .bt-hero-left {{ border-right: none; border-bottom: 1px solid {RULE}; }}
  .bt-tiles {{ grid-template-columns: repeat(3,1fr); }}
}}
"""
