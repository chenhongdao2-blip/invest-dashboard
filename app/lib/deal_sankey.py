"""交易资金流 Sankey · ECharts — lib/deal_sankey.py
=====================================================

Capital Markets「谁把钱投向哪个治疗领域」一图流:MNC 收购方(左) → 治疗领域 TA(右),
连线宽度 = 累计交易额(USD bn)。比「按买家排名 hbar + 按 TA 排名 hbar」两张分立条形图
更有冲击力——一眼看资金在 收购方×TA 网络里的流向。

与 strategy_hero / candlestick_terminal 同套路:单张大 echarts 走 st.iframe(self-contained srcdoc),
自托管 echarts(`/app/static/echarts.min.js`,China 安全)。单张图 → 不触 0 宽竞态;`html,body{height:100%}`。
cream FT 调色,JetBrains/Inter 自托管字体,无 emoji/shadow。数据为真实 deals(非 mock)。

调用(pages/9_HC_Capital_Markets.py):
    from lib import deal_sankey
    deal_sankey.render(nodes, links, title=…, source=…, prefer_cn=…)
  nodes: [{"name": "PFE", "side": "L"} | {"name": "Oncology", "side": "R"}, ...]  (name 唯一)
  links: [{"source": "PFE", "target": "Oncology", "value": 90.2}, ...]            (value = USD bn)
"""
from __future__ import annotations

import json

from lib import theme
from lib import echarts_boot

ECHARTS_SRC = "/app/static/echarts.min.js"

# 左(收购方)节点配 teal 家族;右(TA)节点配 招商红/暖家族;连线随源色低透明度。
_L_COLOR = theme.UP            # 收购方节点 teal #0d7680
_R_COLOR = theme.CMSI_RED      # TA 节点 招商红 #c8102e


def render(nodes: list[dict], links: list[dict], *, title: str, source: str,
           prefer_cn: bool, height: int = 560,
           left_label: str | None = None, right_label: str | None = None) -> bool:
    """渲染交易流 sankey;成功 True,无数据 False。"""
    import streamlit as st

    if not nodes or not links:
        return False

    t = theme
    ll = left_label or ("收购方 · MNC" if prefer_cn else "Acquirer · MNC")
    rl = right_label or ("治疗领域 · TA" if prefer_cn else "Therapeutic Area")

    # echarts sankey 节点带颜色 + depth(左 0 / 右 1),连线着源色。
    # 右列(TA)label 放节点**左侧**,否则默认画在节点右边 → 溢出 iframe 右缘被裁。
    ec_nodes = [{"name": n["name"],
                 "itemStyle": {"color": _L_COLOR if n.get("side") == "L" else _R_COLOR},
                 "depth": 0 if n.get("side") == "L" else 1,
                 "label": {"position": "left" if n.get("side") == "R" else "right"}}
                for n in nodes]
    src_color = {n["name"]: (_L_COLOR if n.get("side") == "L" else _R_COLOR) for n in nodes}
    ec_links = [{"source": l["source"], "target": l["target"],
                 "value": round(float(l["value"]), 2),
                 "lineStyle": {"color": src_color.get(l["source"], _L_COLOR), "opacity": 0.26}}
                for l in links]

    payload = {
        "nodes": ec_nodes, "links": ec_links,
        "INK": t.INK, "INK2": t.INK_2, "INK3": t.INK_3, "PAPER": t.PAPER,
        "EDGE": t.PAPER_EDGE, "MONO": t.FONT_MONO, "FONT": t.FONT_STACK,
        "unit": "bn",
    }

    css = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{height:100%;background:{t.PAPER};color:{t.INK};font-family:{t.FONT_STACK};
      font-feature-settings:'tnum','ss01';-webkit-font-smoothing:antialiased;color-scheme:light}}
    .wrap{{padding:6px 4px}}
    .head{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}}
    .ttl{{display:flex;align-items:center;gap:10px}}
    .tick{{width:4px;height:18px;background:{t.CMSI_RED};display:inline-block}}
    .ttx{{font-size:15px;font-weight:700;color:{t.INK};letter-spacing:-.01em}}
    .cols{{display:flex;gap:16px;font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.12em;
      text-transform:uppercase;color:{t.INK_3};padding-top:4px}}
    .cols .l b{{color:{theme.UP}}}.cols .r b{{color:{theme.CMSI_RED}}}
    #sk{{width:100%;height:{height - 96}px}}
    .foot{{margin-top:8px;font-family:{t.FONT_MONO};font-size:10.5px;color:{t.INK_3};letter-spacing:.02em}}
    """

    js = """
    mountEChart('sk', function(){
      return {
        backgroundColor:'transparent', animationDuration:780, animationEasing:'cubicOut',
        tooltip:{trigger:'item',triggerOn:'mousemove',
          backgroundColor:D.INK,borderColor:D.INK,padding:[8,12],
          textStyle:{color:D.PAPER,fontFamily:D.MONO,fontSize:12},
          formatter:function(p){
            if(p.dataType==='edge'){return p.data.source+' → '+p.data.target
              +' &nbsp;<b>$'+(+p.data.value).toFixed(1)+'B</b>';}
            return '<b>'+p.name+'</b>';}},
        series:[{
          type:'sankey', left:8, right:8, top:10, bottom:14,
          data:D.nodes, links:D.links,
          nodeWidth:13, nodeGap:9, nodeAlign:'justify', draggable:false,
          emphasis:{focus:'adjacency'},
          label:{color:D.INK,fontFamily:D.FONT,fontSize:11.5,fontWeight:600},
          lineStyle:{curveness:0.5},
          itemStyle:{borderWidth:0}
        }]
      };
    });
    """

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="wrap">'
        '<div class="head">'
        f'<div class="ttl"><span class="tick"></span><span class="ttx">{title}</span></div>'
        f'<div class="cols"><span class="l">◀ <b>{ll}</b></span>'
        f'<span class="r"><b>{rl}</b> ▶</span></div></div>'
        '<div id="sk"></div>'
        f'<div class="foot">{source}</div></div>'
        f'<script>var D={json.dumps(payload)};</script>'
        f'<script src="{ECHARTS_SRC}"></script>'
        f'<script>{echarts_boot.MOUNT_JS}</script>'
        f'<script>{js}</script>'
        '</body></html>'
    )
    st.iframe(doc, height=height)
    return True
