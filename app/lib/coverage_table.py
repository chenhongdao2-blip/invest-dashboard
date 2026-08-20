"""CMSI Coverage 覆盖名单 · 玻璃卡片表 — lib/coverage_table.py
================================================================

设计源（1:1 移植）：claude.ai/design 「CMSI 覆盖名单 美化.dc.html」
（handoff5 scratchpad，2026-07-10 George 提供）。

整个 section = 一张自包含 st.iframe：
- 市场 tabs（HK / US / CN / ALL，客户端切换，无 rerun）
- 摘要条：覆盖 N 只 · 总市值 · YTD 中位 · 基准 YTD · 跑赢基准分裂条
- 白玻璃表（rgba(255,255,255,.45)+blur）：
  · 组头带（回报 RETURNS % / 相对{基准} / 估值 VALUATION ×）+ 可点击排序列头（sticky）
  · 「覆盖中位数」基准行
  · 回报列 tint = 列内幅度（青涨/红跌，|v|<0.05 透明）；ytd/exc fontWeight 700
  · 估值列 tint = 列内分位（青=便宜/红=贵，NM 不参与）
  · 负/零估值倍数 → NM（卖方惯例）；缺 mcap → DIM NM 无条
  · NM 恒沉底（设计稿 -Infinity*sortDir 降序时 NM 顶顶 bug 已修正）
- 口径脚注

数据横截面由页面侧从快照库烘入（tabs_payload → client-side ALL 从三市场合并）。

⚠ 既有约束：字体 theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN）；iframe body
transparent 让页面 cream+wash 透出。纯 HTML/JS，无 echarts 依赖。
"""
from __future__ import annotations

import json
import math
import re

from lib import theme

# 设计稿 tokens（内联用）
_RED = theme.CMSI_RED
_TEAL = theme.UP
_INK = theme.INK
_MUT = "#8a8580"
_DIM = "#b8b1a8"
_EDGE = "#d4c4b0"
_SEP = "#e2d3c1"
_ROW_RULE = "#ebd9c8"

# 11 列 grid（与设计稿吻合，在 1240 内容区一屏放下）
# 代码 / 名称 / 市值 / YTD / 1月 / 5日 / 1日 / 超额 / 静PE / 动PE / EV/EBITDA
_GRID = "88px minmax(125px,1fr) 130px 84px 78px 78px 78px 96px 80px 80px 92px"

# 卡片最小宽度 = 列宽合计 + 行内边距 + 表体竖向滚动条宽度。
# 别写死：2026-08-20 实测 min-width 硬编码 1040px，而 11 列合计 1034 + padding 28
# = 内容真实需要 1062px。#scroller 的竖条再吃掉 15px → 可用宽只剩 1025，于是表体
# 自己冒出第二条横向滚动条（叠在外框那条上面），且那条横条又反过来吃掉 15px 高度
# (600→585)，把文档撑过 iframe 高度，再冒出第四条。四条滚动条同源于这一个数。
_ROW_PAD_PX = 28      # 每行 padding:0 14px
_SCROLLBAR_PX = 20    # 竖条实测 15px（macOS）/ Windows 17px，留到 20 覆盖两者


def _grid_min_px(grid: str = _GRID) -> int:
    """_GRID 各列最小宽之和（minmax(a,1fr) 记 a）。加列/改列宽自动跟随。"""
    return sum(int(a or b) for a, b in
               re.findall(r"minmax\(\s*(\d+)px[^)]*\)|(\d+)px", grid))


_CARD_MIN_W = _grid_min_px() + _ROW_PAD_PX + _SCROLLBAR_PX

# tabs + 摘要条 + 脚注 + 卡片边框占用的高度（表体 max-height 之外）。
# 实测 204px @1440px；留 12px 余量吸收换行。原值 180 少算 24px，导致文档高度
# 超出 iframe → iframe 自身多出一条纵向滚动条。
_CHROME_PX = 216


def _clean(v) -> float | None:
    """NaN/inf → None（JS 侧统一走 NM 分支）。"""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def render_coverage(tabs_payload: list[dict], *, labels: dict,
                    height: int = 760) -> tuple[str, int]:
    """Build the coverage-list glass-card iframe. Returns (doc, iframe_h).

    tabs_payload = [
      {
        "id": "HK" | "US" | "CN" | "ALL",
        "label": str,          # 短名（HK / US / CN / ALL）
        "count": int,
        "bench_label": str,    # 基准短名（e.g. "恒指", "标普500", "上证综指"）
        "bench_ytd": float | None,   # 基准 YTD %（已是百分数），None → 不显示
        "rows": [
          {
            "t": str,          # ticker
            "n": str,          # 名称（本地化）
            "model": bool,     # 有模型页 → ● 标注
            "mcap": float|None,  # 市值 $B
            "ytd": float|None,   # YTD %
            "m1":  float|None,   # 1月 %
            "d5":  float|None,   # 5日 %
            "d1":  float|None,   # 1日 %
            "exc": float|None,   # 超额（vs 本市场基准）pp
            "peS": float|None,   # 静态 P/E
            "peF": float|None,   # 动态 P/E
            "evE": float|None,   # EV/EBITDA
          }
        ]
      },
      ...
    ]

    labels 须包含：
      cover / mcap_total / ytd_med / bench_prefix / beat_label /
      median / brand / footnote /
      cols: {t, n, mcap, ytd, m1, d5, d1, exc, peS, peF, evE} /
      grp_ret / grp_exc / grp_val

    排序语义：NM 恒沉底（设计稿 -Infinity*sortDir bug 已修正）。
    """
    # 清洗数值，负/零估值倍数 → NM（卖方惯例：亏损期 P/E / 负 EBITDA 不进「便宜」分位）
    clean_tabs = []
    for tab in tabs_payload:
        rows = []
        for r in tab["rows"]:
            row: dict = {
                "t": str(r["t"]),
                "n": str(r["n"]),
                "model": bool(r.get("model", False)),
            }
            for k in ("mcap", "ytd", "m1", "d5", "d1", "exc"):
                row[k] = _clean(r.get(k))
            for k in ("peS", "peF", "evE"):
                v = _clean(r.get(k))
                # 负/零 → NM（卖方惯例）
                if v is not None and v <= 0:
                    v = None
                row[k] = v
            rows.append(row)
        clean_tabs.append({
            "id": str(tab["id"]),
            "label": str(tab["label"]),
            "count": int(tab["count"]),
            "bench_label": str(tab.get("bench_label") or "—"),
            "bench_ytd": _clean(tab.get("bench_ytd")),
            "rows": rows,
        })

    payload = json.dumps(
        {"tabs": clean_tabs, "labels": labels},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    table_max_h = max(300, height - _CHROME_PX)  # chrome 之外给表体
    iframe_h = height

    # NM 恒沉底修正：xBad/yBad → 直接返回 1 / -1（不用 -Infinity*sortDir）
    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', MUT='__MUT__', DIM='__DIM__';
var S = 0.16;
var GRID = '__GRIDCOLS__';
var mono = "'JetBrains Mono',monospace";
var sans = "'Space Grotesk','PingFang SC','Hiragino Sans GB','Noto Sans SC','Microsoft YaHei',sans-serif";

var COLS = [
  {k:'t',   label:L.cols.t,   align:'left',  type:'text', grp:0},
  {k:'n',   label:L.cols.n,   align:'left',  type:'text', grp:0},
  {k:'mcap',label:L.cols.mcap,align:'right', type:'mcap', grp:0},
  {k:'ytd', label:L.cols.ytd, align:'right', type:'ret',  grp:1},
  {k:'m1',  label:L.cols.m1,  align:'right', type:'ret',  grp:1},
  {k:'d5',  label:L.cols.d5,  align:'right', type:'ret',  grp:1},
  {k:'d1',  label:L.cols.d1,  align:'right', type:'ret',  grp:1},
  {k:'exc', label:L.cols.exc, align:'right', type:'ret',  grp:2},
  {k:'peS', label:L.cols.peS, align:'right', type:'val',  grp:3},
  {k:'peF', label:L.cols.peF, align:'right', type:'val',  grp:3},
  {k:'evE', label:L.cols.evE, align:'right', type:'val',  grp:3}
];

/* 列边框：ytd=col3, exc=col7, peS=col8 处加分隔线 */
function blFor(i){ return (i===3||i===7||i===8) ? '1px solid __SEP__' : 'none'; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function median(vs){
  var s = vs.filter(function(v){ return v!=null&&isFinite(v); }).slice().sort(function(a,b){return a-b;});
  if(!s.length) return null;
  var m = Math.floor(s.length/2);
  return s.length%2 ? s[m] : (s[m-1]+s[m])/2;
}
function fmt(type, v){
  if(v==null||!isFinite(v)) return 'NM';
  if(type==='ret') return (v>=0?'+':'-')+Math.abs(v).toFixed(1)+'%';
  if(type==='mcap') return '$'+v.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1})+'B';
  if(type==='val') return v.toFixed(1)+'x';
  return String(v);
}

var st_ = { tab: P.tabs.length ? P.tabs[0].id : null, sortKey:'mcap', sortDir:-1 };

function getTab(){
  var found=null;
  P.tabs.forEach(function(t){ if(t.id===st_.tab) found=t; });
  return found;
}

function render(){
  /* --- tabs bar --- */
  document.getElementById('tabs').innerHTML = P.tabs.map(function(t){
    var on = t.id===st_.tab;
    return '<button data-tab="'+t.id+'" style="appearance:none;background:transparent;border:none;' +
      'margin:0 0 -1px;cursor:pointer;display:inline-flex;align-items:baseline;gap:6px;' +
      'padding:8px 2px 10px;border-bottom:2.5px solid '+(on?RED:'transparent')+';font-family:inherit;">' +
      '<span style="font-family:'+mono+';font-size:13px;font-weight:'+(on?700:500)+';' +
      'color:'+(on?RED:'#6b655e')+';letter-spacing:.04em;">'+esc(t.label)+'</span>' +
      '<span style="font-family:'+mono+';font-size:10px;color:'+MUT+';">('+t.count+')</span></button>';
  }).join('');

  var tab = getTab();
  if(!tab){ return; }

  /* --- sort (NM 恒沉底) --- */
  var sk=st_.sortKey, dir=st_.sortDir;
  var rows = tab.rows.slice().sort(function(a,b){
    var x=a[sk], y=b[sk];
    if(sk==='t'||sk==='n') return String(x).localeCompare(String(y))*dir;
    var xBad=(x==null||!isFinite(x)), yBad=(y==null||!isFinite(y));
    if(xBad&&yBad) return 0;
    if(xBad) return 1;   /* NM 沉底，不受 sortDir 影响 */
    if(yBad) return -1;
    return (x-y)*dir;
  });

  /* --- column stats --- */
  var colVals={}, colSorted={}, colMaxAbs={};
  COLS.forEach(function(c){
    if(c.type==='text') return;
    var vs=rows.map(function(r){return r[c.k];}).filter(function(v){return v!=null&&isFinite(v);});
    colVals[c.k]=vs;
    colSorted[c.k]=vs.slice().sort(function(a,b){return a-b;});
    colMaxAbs[c.k]=Math.max(Math.max.apply(null,vs.map(Math.abs).concat([0])),0.0001);
  });
  var maxMcap=Math.max(Math.max.apply(null,(colVals['mcap']||[0]).concat([0])),1);

  function pct(k,v){
    var s=colSorted[k];
    if(!s||s.length<2||v==null||!isFinite(v)) return null;
    var i=0; while(i<s.length&&s[i]<v) i++;
    return i/(s.length-1);
  }
  function tint(col,v){
    if(v==null||!isFinite(v)||S===0) return 'transparent';
    if(col.type==='ret'){
      if(Math.abs(v)<0.05) return 'transparent';
      var a=Math.min(Math.abs(v)/colMaxAbs[col.k],1)*S;
      return v>0?'rgba(13,118,128,'+a.toFixed(3)+')':'rgba(200,16,46,'+a.toFixed(3)+')';
    }
    var p=pct(col.k,v);
    if(p==null) return 'transparent';
    var d=Math.abs(p-0.5)*2*S;
    if(d<0.01) return 'transparent';
    return p<0.5?'rgba(13,118,128,'+d.toFixed(3)+')':'rgba(200,16,46,'+d.toFixed(3)+')';
  }

  /* --- 摘要条 --- */
  var ytds=colVals['ytd']||[];
  var excs=rows.map(function(r){return r.exc;}).filter(function(v){return v!=null&&isFinite(v);});
  var beat=excs.filter(function(v){return v>0;}).length;
  var tot=(colVals['mcap']||[]).reduce(function(a,b){return a+b;},0);
  var mYtd=median(ytds);
  document.getElementById('sumCount').textContent=rows.length+' '+L.unit_names;
  document.getElementById('sumMcap').textContent='$'+tot.toLocaleString('en-US',{maximumFractionDigits:1,minimumFractionDigits:1})+'B';
  var eY=document.getElementById('sumYtd');
  eY.textContent=fmt('ret',mYtd);
  eY.style.color=mYtd>0?TEAL:mYtd<0?RED:INK;

  /* 基准 YTD */
  var eBench=document.getElementById('sumBench');
  var eBenchLabel=document.getElementById('sumBenchLabel');
  eBenchLabel.textContent=L.bench_prefix+(tab.bench_label||'—')+' YTD';
  if(tab.bench_ytd!=null&&isFinite(tab.bench_ytd)){
    eBench.textContent=fmt('ret',tab.bench_ytd);
    eBench.style.color=tab.bench_ytd>0?TEAL:tab.bench_ytd<0?RED:INK;
    eBench.style.display='';
  } else {
    eBench.style.display='none';
  }

  /* 跑赢分裂条 */
  var beatPct=(beat/(excs.length||1)*100).toFixed(1);
  var lagPct=((excs.length-beat)/(excs.length||1)*100).toFixed(1);
  document.getElementById('bBeat').style.width=beatPct+'%';
  document.getElementById('bLag').style.width=lagPct+'%';
  document.getElementById('beatN').textContent=beat;
  document.getElementById('allN').textContent=excs.length;
  /* 跑赢标签 */
  document.getElementById('beatLabel').textContent=L.beat_label+(tab.bench_label||'—');

  /* --- 组头带（动态超额列标题）--- */
  var grpHtml=
    '<span style="grid-column:4 / span 4;font-family:'+mono+';font-size:9px;letter-spacing:.16em;' +
    'color:'+MUT+';font-weight:600;padding:8px 10px 0;border-left:1px solid __SEP__;text-align:right;">' +
    esc(L.grp_ret)+'</span>' +
    '<span style="grid-column:8;font-family:'+mono+';font-size:9px;letter-spacing:.16em;' +
    'color:'+MUT+';font-weight:600;padding:8px 10px 0;border-left:1px solid __SEP__;text-align:right;">' +
    esc(L.grp_exc_prefix+(tab.bench_label||'—'))+'</span>' +
    '<span style="grid-column:9 / span 3;font-family:'+mono+';font-size:9px;letter-spacing:.16em;' +
    'color:'+MUT+';font-weight:600;padding:8px 10px 0;border-left:1px solid __SEP__;text-align:right;">' +
    esc(L.grp_val)+'</span>';
  document.getElementById('grpBand').innerHTML=grpHtml;

  /* 超额列 header 也同步 bench_label */
  var excLbl=L.cols.exc_prefix+(tab.bench_label||'—')+L.cols.exc_suffix;
  var dynCols=COLS.map(function(c){return c.k==='exc'?Object.assign({},c,{label:excLbl}):c;});

  /* --- 列头 --- */
  var head=dynCols.map(function(c,i){
    var on=c.k===sk;
    return '<button data-k="'+c.k+'" style="appearance:none;background:transparent;border:none;margin:0;cursor:pointer;' +
      'font-family:'+mono+';font-size:10px;letter-spacing:.05em;font-weight:'+(on?700:500)+';color:'+(on?RED:'#4a4a4a')+';' +
      'padding:7px 10px 9px;text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';">' +
      esc(c.label)+(on?(dir<0?' ▾':' ▴'):'')+' </button>';
  }).join('');

  /* --- 中位数行 --- */
  var med=COLS.map(function(c,i){
    var txt=c.k==='t'?'—':c.k==='n'?L.median:fmt(c.type,median(colVals[c.k]||[]));
    return '<span style="font-family:'+mono+';font-size:11px;color:'+MUT+';font-weight:500;padding:6px 10px;' +
      'text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';">'+txt+'</span>';
  }).join('');

  /* --- 数据行 --- */
  var body=rows.map(function(r){
    var cells=COLS.map(function(c,i){
      var v=r[c.k];
      var flexAlign=c.align==='right'?'flex-end':'flex-start';
      var s0='display:flex;flex-direction:column;justify-content:center;align-items:'+flexAlign+';' +
        'padding:8px 10px;text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';' +
        'font-variant-numeric:tabular-nums;line-height:1.35;';
      if(c.k==='t')
        return '<span style="'+s0+'font-family:'+mono+';font-size:11px;font-weight:500;color:'+MUT+';"><span>'+esc(r.t)+'</span></span>';
      if(c.k==='n'){
        /* 名称 + 模型标记（有模型时追加红色 ● ） */
        var dot=r.model?'<span style="color:'+RED+';font-size:9px;margin-left:4px;">●</span>':'';
        return '<span style="'+s0+'font-family:'+sans+';font-size:13px;font-weight:600;color:'+INK+';"><span>'+esc(r.n)+dot+'</span></span>';
      }
      if(c.type==='mcap'){
        if(v==null||!isFinite(v))
          return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:500;color:'+DIM+';"><span>NM</span></span>';
        var bw=Math.sqrt(v/maxMcap)*100;
        return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:600;color:'+INK+';">' +
          '<span>'+fmt('mcap',v)+'</span>' +
          '<span style="display:block;height:3px;background:rgba(26,26,26,.18);border-radius:1px;margin-top:3px;align-self:stretch;">' +
          '<span style="display:block;height:100%;background:'+RED+';border-radius:1px;width:'+bw.toFixed(1)+'%;"></span></span></span>';
      }
      var fg=INK, fw=500;
      if(v==null||!isFinite(v)) fg=DIM;
      else if(c.type==='ret'){
        var flat=Math.abs(v)<0.05;
        fg=flat?MUT:(v>0?TEAL:RED);
        fw=(c.k==='exc'||c.k==='ytd')?700:600;
      }
      return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:'+fw+';color:'+fg+';background:'+tint(c,v)+';">' +
        '<span>'+fmt(c.type,v)+'</span></span>';
    }).join('');
    return '<div class="covrow" style="display:grid;grid-template-columns:'+GRID+';padding:0 14px;border-bottom:1px solid __ROWRULE__;">'+cells+'</div>';
  }).join('');

  document.getElementById('thead').innerHTML=head;
  document.getElementById('tmed').innerHTML=med;
  document.getElementById('tbody').innerHTML=body;
}

/* --- 事件委托 --- */
document.getElementById('tabs').addEventListener('click',function(e){
  var b=e.target.closest('button[data-tab]');
  if(!b) return;
  st_.tab=b.getAttribute('data-tab');
  render();
  document.getElementById('scroller').scrollTop=0;
});
document.getElementById('thead').addEventListener('click',function(e){
  var b=e.target.closest('button[data-k]');
  if(!b) return;
  var k=b.getAttribute('data-k');
  if(st_.sortKey===k) st_.sortDir=-st_.sortDir;
  else { st_.sortKey=k; st_.sortDir=(k==='t'||k==='n')?1:-1; }
  render();
});
render();
"""
    js = (js.replace("__PAYLOAD__", payload)
            .replace("__RED__", _RED).replace("__TEAL__", _TEAL)
            .replace("__INK__", _INK).replace("__MUT__", _MUT)
            .replace("__DIM__", _DIM).replace("__SEP__", _SEP)
            .replace("__ROWRULE__", _ROW_RULE)
            .replace("__GRIDCOLS__", _GRID))

    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    font_face = theme.FONT_FACE_CSS.strip()
    mono_css = "'JetBrains Mono',monospace"

    def _sum_pair(lbl_key: str, span_id: str) -> str:
        return (
            '<span style="display:inline-flex;align-items:baseline;gap:7px;">'
            f'<span style="font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_MUT};">'
            f'{labels[lbl_key]}</span>'
            f'<span id="{span_id}" style="font-family:{mono_css};font-size:13px;font-weight:700;color:{_INK};"></span>'
            '</span>'
        )

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        ".covrow{transition:background .12s;}"
        ".covrow:hover{background:rgba(255,255,255,.8);}"
        "button:hover{opacity:.85;}"
        f"#scroller{{max-height:{table_max_h}px;overflow:auto;}}"
        "</style></head><body>"
        # tabs
        f'<div id="tabs" style="display:flex;gap:26px;border-bottom:1px solid {_EDGE};flex-wrap:wrap;margin-bottom:0;"></div>'
        # 摘要条
        '<div style="display:flex;align-items:center;gap:22px;flex-wrap:wrap;padding:13px 2px 14px;">'
        + _sum_pair("cover", "sumCount")
        + _sum_pair("mcap_total", "sumMcap")
        + _sum_pair("ytd_med", "sumYtd")
        # 基准 YTD（label 动态 by tab）
        + (f'<span style="display:inline-flex;align-items:baseline;gap:7px;">'
           f'<span id="sumBenchLabel" style="font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_MUT};"></span>'
           f'<span id="sumBench" style="font-family:{mono_css};font-size:13px;font-weight:700;color:{_INK};"></span>'
           f'</span>')
        # 跑赢分裂条（右对齐）
        + (f'<span style="display:inline-flex;align-items:center;gap:9px;margin-left:auto;">'
           f'<span id="beatLabel" style="font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_MUT};"></span>'
           f'<span style="display:inline-flex;width:130px;height:7px;border-radius:1px;overflow:hidden;background:{_SEP};">'
           f'<span id="bBeat" style="display:block;height:100%;background:{_TEAL};width:0%;"></span>'
           f'<span id="bLag" style="display:block;height:100%;background:{_RED};width:0%;"></span>'
           f'</span>'
           f'<span style="font-family:{mono_css};font-size:11px;color:#4a4a4a;">'
           f'<span id="beatN" style="color:{_TEAL};font-weight:700;"></span>'
           f' / <span id="allN"></span></span></span>')
        + '</div>'
        # 表格（组头带 + sticky 列头 + 中位数行 + 滚动表体）
        f'<div style="border:1px solid {_EDGE};border-radius:2px;background:rgba(255,255,255,.45);'
        '-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);overflow-x:auto;">'
        f'<div style="min-width:{_CARD_MIN_W}px;">'
        # 组头带（动态内容 by JS）
        f'<div id="grpBand" style="display:grid;grid-template-columns:{_GRID};padding:0 14px;background:rgba(255,241,229,.9);"></div>'
        '<div id="scroller">'
        f'<div id="thead" style="position:sticky;top:0;z-index:3;display:grid;grid-template-columns:{_GRID};'
        f'padding:0 14px;background:{theme.PAPER};border-bottom:2px solid {_INK};"></div>'
        f'<div id="tmed" style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
        f'border-bottom:1px solid {_EDGE};background:rgba(255,255,255,.35);"></div>'
        '<div id="tbody"></div>'
        '</div></div></div>'
        # 口径脚注
        f'<div style="margin-top:18px;border-top:1px solid {_INK};padding-top:10px;display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:11.5px;line-height:1.7;color:{_MUT};max-width:940px;">{labels["footnote"]}</span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10.5px;letter-spacing:.08em;color:{_DIM};">{labels["brand"]}</span>'
        '</div>'
        f'{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, iframe_h
