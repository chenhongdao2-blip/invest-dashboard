"""CMSI Strategy Picks · 策略方法论卡 + 持仓明细表 — lib/picks_table.py
======================================================================

设计源（1:1 移植）：claude.ai/design 「美国生科 策略方法论 持仓 美化.dc.html」
（handoff6 scratchpad，2026-07-10 George 提供）。

两个公共函数：
  render_methodology(m, prefer_cn) -> (doc, h)   — 方法论 glass 卡（纯 HTML/静态）
  render_holdings(payload, labels, height) -> (doc, h)  — 持仓明细表（含排序 JS）

持仓明细约束（INVARIANTS）：
  - 青涨(#0d7680) / 红跌(#c8102e) 颜色规范锁定，禁止翻转
  - 名次 top-3 chip 红底(#c8102e)+米色文字(#fff1e5)；其余灰底+消字
  - 建仓来 (since) 列 font-weight:700 加粗
  - sparkline 用调用方传入的真实收盘（20 根），非设计稿 seeded random
  - Score mini-bar 按当前书内评分区间拉伸（teal 色）
  - 回报列按列内幅度 tint（S=0.16），|v|<0.05 透明，since 列同规则
  - 字体: theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN）
  - iframe body transparent，让页面 cream+wash 透出

方法论卡携带的 m 结构 (dict)：
  {
    "tag": str,           # 版本 chip（如"夏季调仓"）
    "chip": str,          # 宇宙 chip（如"US Biotech"）
    "dims": [             # 打分维度
      {"name": str, "pct": int, "color": str, "fg": str}, ...
    ],
    "summary_html": str,  # 方法论主体 HTML（多段落，可含 <b><br>）
  }

持仓 payload 每行：
  {
    "rank": int,
    "tick": str,           # 代码（格式化后展示）
    "name": str,
    "score": float | None,
    "price": float,
    "ccy": str,            # 货币前缀，如"$"或"HK$"
    "spark": [float, ...], # ~20 真实收盘价
    "d1":    float | None, # 1日 %（已是 pct，如 +1.23 = +1.23%）
    "d5":    float | None,
    "m1":    float | None,
    "ytd":   float | None,
    "since": float | None, # 建仓来 %
  }
"""
from __future__ import annotations

import json
import math

from lib import theme

# ── 设计稿色彩 tokens ─────────────────────────────────────────────────────────
_RED   = theme.CMSI_RED        # "#c8102e"
_TEAL  = theme.UP              # "#0d7680"
_INK   = theme.INK             # "#1a1a1a"
_INK2  = theme.INK_2           # "#4a4a4a"
_MUT   = theme.INK_3           # "#8a8580"
_DIM   = theme.INK_4           # "#b8b1a8"
_PAPER = theme.PAPER           # "#fff1e5"
_EDGE  = theme.PAPER_EDGE      # "#d4c4b0"
_SEP   = theme.PAPER_EDGE_SOFT # "#e4d2bd"
_ROW   = theme.PAPER_RULE      # "#ebd9c8"

# 11 列 grid（与设计稿吻合）：名次/代码/名称/评分/价格/1日/5日/1月/年初/建仓来/sparkline
_GRID = "50px 72px minmax(168px,1fr) 108px 84px 90px 70px 72px 72px 78px 84px"

_MONO = "'JetBrains Mono',monospace"
_SANS = ("'Inter','Space Grotesk','PingFang SC','Hiragino Sans GB',"
         "'Noto Sans SC','Microsoft YaHei',sans-serif")


def _clean(v) -> float | None:
    """NaN/inf → None."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


# ─────────────────────────────────────────────────────────────────────────────
# 1. render_methodology
# ─────────────────────────────────────────────────────────────────────────────

def render_methodology(m: dict, prefer_cn: bool = True) -> tuple[str, int]:
    """Build the strategy methodology glass card.

    Returns (doc, iframe_h).

    m dict keys:
      tag (str)           — 版本标签 chip text
      chip (str)          — 宇宙/品种 chip text
      dims (list)         — [{name, pct, color, fg}, ...]  权重维度
      summary_html (str)  — 正文 HTML（支持 <b>/<br>/<ul>/<li> 等）
    """
    tag          = str(m.get("tag", ""))
    chip         = str(m.get("chip", ""))
    dims         = m.get("dims", [])
    summary_html = str(m.get("summary_html", ""))

    font_face = theme.FONT_FACE_CSS.strip()

    # ── 权重条：按 dims 生成彩色线段 ──────────────────────────────────────────
    bar_segs = ""
    for d in dims:
        pct   = int(d.get("pct", 0))
        color = str(d.get("color", _INK))
        bar_segs += (
            f'<span style="display:inline-block;width:{pct}%;height:100%;'
            f'background:{color};"></span>'
        )

    # ── 维度 chip 列表 ─────────────────────────────────────────────────────────
    dim_chips = ""
    for d in dims:
        name  = str(d.get("name", ""))
        pct   = int(d.get("pct", 0))
        color = str(d.get("color", _INK))
        fg    = str(d.get("fg", _PAPER))
        dim_chips += (
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'padding:4px 10px 4px 6px;border-radius:2px;'
            f'background:{color};white-space:nowrap;">'
            f'<span style="font-family:{_MONO};font-size:15px;font-weight:700;'
            f'color:{fg};letter-spacing:-.01em;">{pct}%</span>'
            f'<span style="font-family:{_SANS};font-size:12px;font-weight:600;'
            f'color:{fg};opacity:.9;">{name}</span>'
            f'</span>'
        )

    # ── tag + chip rows ────────────────────────────────────────────────────────
    chips_html = ""
    if tag:
        chips_html += (
            f'<span style="font-family:{_MONO};font-size:11px;font-weight:600;'
            f'color:{_MUT};border:1px solid {_SEP};border-radius:2px;'
            f'padding:2px 8px;letter-spacing:.04em;">{tag}</span> '
        )
    if chip:
        chips_html += (
            f'<span style="font-family:{_MONO};font-size:11px;font-weight:600;'
            f'color:{_TEAL};border:1px solid {_TEAL};border-radius:2px;'
            f'padding:2px 8px;letter-spacing:.04em;">{chip}</span>'
        )

    # ── 卡高度估算（无 JS，纯静态） ────────────────────────────────────────────
    # 顶边栏(32) + 权重条(20) + dims chips行（inline-flex wrap；≤5 dims全在1行: 40px）
    # + 正文（按字符估行数，每行约18px）+ 底边padding(28)
    char_est  = len(summary_html.replace("<br>", "\n").replace("<br/>", "\n"))
    line_est  = max(3, char_est // 60)
    dims_h    = 40 if len(dims) <= 5 else 72   # inline-flex wraps to 2 rows for >5 dims
    body_h    = 32 + 20 + dims_h + line_est * 18 + 28
    iframe_h  = max(220, body_h)

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;font-family:{_SANS};}}'
        '</style></head><body style="padding:0 2px 16px;">'

        # 玻璃卡
        f'<div style="background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);'
        f'backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.7);'
        f'border-top:2px solid {_INK};border-radius:0;padding:18px 22px 20px;">'

        # 顶行：section bar + chip 组
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
        f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
        f'<span style="font-family:{_MONO};font-size:10px;font-weight:600;color:{_MUT};'
        f'letter-spacing:.14em;text-transform:uppercase;">策略方法论</span>'
        f'<span style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap;">{chips_html}</span>'
        f'</div>'

        # 权重条（全宽彩色段）
        f'<div style="width:100%;height:8px;border-radius:2px;overflow:hidden;display:flex;margin-bottom:12px;">'
        f'{bar_segs}'
        f'</div>'

        # 维度 chip 行
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">'
        f'{dim_chips}'
        f'</div>'

        # 正文
        f'<div style="font-size:13px;line-height:1.7;color:{_INK2};">'
        f'{summary_html}'
        f'</div>'

        '</div>'
        '</body></html>'
    )
    return doc, iframe_h


# ─────────────────────────────────────────────────────────────────────────────
# 2. render_holdings
# ─────────────────────────────────────────────────────────────────────────────

def render_holdings(
    payload: list[dict],
    labels:  dict,
    height:  int = 560,
) -> tuple[str, int]:
    """Build the holdings glass-card table with sortable columns.

    Returns (doc, iframe_h).

    payload rows: see module docstring.

    labels dict must contain keys (may be zh or en per caller):
      col_rank / col_tick / col_name / col_score / col_price /
      col_d1 / col_d5 / col_m1 / col_ytd / col_since / col_spark /
      nm_label / unit_pct / footnote / brand

    All None/NaN numerics rendered as nm_label (default "NM").
    """
    # ── 清洗数值 ──────────────────────────────────────────────────────────────
    clean_rows: list[dict] = []
    for r in payload:
        cr: dict = {
            "rank":  int(r.get("rank", 0)),
            "tick":  str(r.get("tick", "")),
            "name":  str(r.get("name", "")),
            "score": _clean(r.get("score")),
            "price": _clean(r.get("price")),
            "ccy":   str(r.get("ccy", "$")),
            "spark": [_clean(v) for v in (r.get("spark") or [])],
            "d1":    _clean(r.get("d1")),
            "d5":    _clean(r.get("d5")),
            "m1":    _clean(r.get("m1")),
            "ytd":   _clean(r.get("ytd")),
            "since": _clean(r.get("since")),
        }
        # Prune None tails from spark (keep contiguous leading non-None)
        cr["spark"] = [v for v in cr["spark"] if v is not None]
        clean_rows.append(cr)

    payload_json = json.dumps(
        {"rows": clean_rows, "labels": labels},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    table_max_h = max(240, height - 60)
    iframe_h    = height

    LT   = chr(60)
    TAG  = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"

    font_face = theme.FONT_FACE_CSS.strip()

    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var rows = P.rows;

/* color tokens */
var RED   = '__RED__', TEAL  = '__TEAL__', INK   = '__INK__';
var INK2  = '__INK2__', MUT  = '__MUT__',  DIM   = '__DIM__';
var PAPER = '__PAPER__', EDGE = '__EDGE__', ROW   = '__ROW__';
var mono  = __MONO__, sans = __SANS__;
var GRID  = '__GRID__';
var S     = 0.16;   /* tint strength */

/* columns meta (ret cols for tint / sort) */
var RET_COLS = [
  {k:'d1',    label:L.col_d1,    bold:false},
  {k:'d5',    label:L.col_d5,    bold:false},
  {k:'m1',    label:L.col_m1,    bold:false},
  {k:'ytd',   label:L.col_ytd,   bold:false},
  {k:'since', label:L.col_since, bold:true}
];

/* sort state */
var st_ = {key:'rank', dir:1};

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function fmtPct(v, bold){
  if(v===null||v===undefined) return '<span style="color:'+DIM+';">'+(L.nm_label||'NM')+'</span>';
  var s=v>=0?'+':'-';
  var f=Math.abs(v).toFixed(1)+'%';
  var col=Math.abs(v)<0.05?MUT:(v>0?TEAL:RED);
  var fw=bold?'700':'600';
  return '<span style="color:'+col+';font-weight:'+fw+';">'+s+f+'</span>';
}

function fmtPrice(v,ccy){
  if(v===null||v===undefined) return '<span style="color:'+DIM+';">'+(L.nm_label||'NM')+'</span>';
  return esc(ccy)+v.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
}

/* tint: column magnitude tint (|v|/maxAbs * S), ret sign drives color */
function colTint(vals, v){
  if(v===null||v===undefined) return 'transparent';
  if(Math.abs(v)<0.05) return 'transparent';
  var vs=vals.filter(function(x){return x!==null&&x!==undefined;});
  var mx=Math.max.apply(null,vs.map(Math.abs).concat([0.0001]));
  var a=Math.min(Math.abs(v)/mx,1)*S;
  return v>0?'rgba(13,118,128,'+a.toFixed(3)+')':'rgba(200,16,46,'+a.toFixed(3)+')';
}

/* score mini-bar (teal, scaled to book range) */
function scoreBar(score, sLo, sHi){
  if(score===null||score===undefined) return '';
  var range=sHi-sLo; if(range<=0) range=1;
  var w=Math.max(0,Math.min(1,(score-sLo)/range))*100;
  return '<div style="width:100%;height:3px;background:rgba(26,26,26,.1);border-radius:1px;margin-top:4px;">'
    +'<div style="height:100%;background:'+TEAL+';border-radius:1px;width:'+w.toFixed(1)+'%;"></div>'
    +'</div>';
}

/* sparkline SVG from real closes */
function spark(vals){
  var pts=vals.filter(function(v){return v!==null;});
  if(pts.length<2) return '<svg width="80" height="24"></svg>';
  var lo=Math.min.apply(null,pts), hi=Math.max.apply(null,pts);
  var rng=hi-lo; if(rng===0) rng=1;
  var n=pts.length, H=24, pad=3, W=80;
  var coords=pts.map(function(y,i){
    var x=(i/(n-1))*W;
    var yy=H-pad-((y-lo)/rng)*(H-2*pad);
    return x.toFixed(1)+','+yy.toFixed(1);
  }).join(' ');
  var lastV=pts[pts.length-1], firstV=pts[0];
  var col=lastV>=firstV?TEAL:RED;
  return '<svg width="80" height="24" viewBox="0 0 80 24" style="display:block;">'
    +'<polyline points="'+coords+'" fill="none" stroke="'+col+'" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>'
    +'</svg>';
}

function render(){
  /* collect column values for tint */
  var retVals={};
  RET_COLS.forEach(function(c){
    retVals[c.k]=rows.map(function(r){return r[c.k];});
  });

  /* score range */
  var scores=rows.map(function(r){return r.score;}).filter(function(v){return v!==null;});
  var sLo=scores.length?Math.min.apply(null,scores)-0.15:0;
  var sHi=scores.length?Math.max.apply(null,scores)+0.05:10;

  /* sort */
  var sk=st_.key, dir=st_.dir;
  var sorted=rows.slice().sort(function(a,b){
    if(sk==='rank') return (a.rank-b.rank)*dir;
    if(sk==='tick'||sk==='name') return String(a[sk]).localeCompare(String(b[sk]))*dir;
    var x=a[sk], y=b[sk];
    var xB=(x===null||x===undefined), yB=(y===null||y===undefined);
    if(xB&&yB) return 0; if(xB) return 1; if(yB) return -1;
    return (x-y)*dir;
  });

  /* header */
  var hdr='';
  /* fixed left cols */
  var fixedCols=[
    {k:'rank', label:L.col_rank, align:'center'},
    {k:'tick', label:L.col_tick, align:'left'},
    {k:'name', label:L.col_name, align:'left'},
    {k:'score', label:L.col_score, align:'right'},
    {k:'price', label:L.col_price, align:'right'}
  ];
  var allCols=fixedCols.concat(RET_COLS.map(function(c){return {k:c.k,label:c.label,align:'right'};}));
  allCols.push({k:'spark', label:L.col_spark, align:'center', nosort:true});

  allCols.forEach(function(c){
    var on=c.k===sk;
    var cursor=c.nosort?'default':'pointer';
    hdr+='<div data-k="'+(c.nosort?'':c.k)+'" style="cursor:'+cursor+';display:flex;align-items:center;'
      +'justify-content:'+(c.align==='center'?'center':c.align==='right'?'flex-end':'flex-start')+';'
      +'padding:8px 8px 9px;font-family:'+mono+';font-size:10px;letter-spacing:.06em;'
      +'font-weight:'+(on?700:600)+';color:'+(on?RED:INK2)+';">'
      +esc(c.label)+(on?(dir>0?' ▴':' ▾'):'')
      +'</div>';
  });
  document.getElementById('thead').innerHTML=hdr;

  /* rows */
  var body='';
  sorted.forEach(function(r){
    var rank=r.rank, isTop=(rank<=3);
    var rankBg=isTop?RED:'rgba(26,26,26,.08)';
    var rankFg=isTop?PAPER:MUT;

    /* rank chip */
    var rankCell='<div style="display:flex;align-items:center;justify-content:center;padding:10px 6px;">'
      +'<span style="width:28px;height:28px;border-radius:50%;background:'+rankBg+';color:'+rankFg+';'
      +'font-family:'+mono+';font-size:11px;font-weight:700;display:flex;align-items:center;'
      +'justify-content:center;">'+rank+'</span></div>';

    /* tick */
    var tickCell='<div style="padding:10px 8px;font-family:'+mono+';font-size:11px;font-weight:600;color:'+MUT+';">'
      +esc(r.tick)+'</div>';

    /* name */
    var nameCell='<div style="padding:10px 8px;font-family:'+sans+';font-size:13px;font-weight:600;color:'+INK+';'
      +'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(r.name)+'</div>';

    /* score — wrap in a block div so the bar track has a defined parent width */
    var scoreInner;
    if(r.score===null||r.score===undefined){
      scoreInner='<span style="color:'+DIM+';">'+(L.nm_label||'NM')+'</span>';
    } else {
      /* inner wrapper: block, text-align right, gives bar track a real width */
      scoreInner='<div style="width:100%;text-align:right;">'
        +'<span style="font-size:14px;font-weight:700;color:'+INK+';">'+r.score.toFixed(2)+'</span>'
        +scoreBar(r.score,sLo,sHi)
        +'</div>';
    }
    var scoreCell='<div style="padding:10px 8px;display:flex;flex-direction:column;justify-content:center;'
      +'align-items:stretch;font-family:'+mono+';font-variant-numeric:tabular-nums;">'+scoreInner+'</div>';

    /* price */
    var priceCell='<div style="padding:10px 8px;font-family:'+mono+';font-size:12px;font-weight:600;color:'+INK+';'
      +'text-align:right;font-variant-numeric:tabular-nums;">'+fmtPrice(r.price,r.ccy)+'</div>';

    /* ret cols */
    var retCells='';
    RET_COLS.forEach(function(c){
      var bg=colTint(retVals[c.k],r[c.k]);
      retCells+='<div style="padding:10px 8px;text-align:right;font-family:'+mono+';font-size:12px;'
        +'font-variant-numeric:tabular-nums;background:'+bg+';display:flex;align-items:center;'
        +'justify-content:flex-end;">'+fmtPct(r[c.k],c.bold)+'</div>';
    });

    /* sparkline */
    var sparkCell='<div style="padding:6px 8px;display:flex;align-items:center;justify-content:center;">'
      +spark(r.spark)+'</div>';

    body+='<div class="hrow" style="display:grid;grid-template-columns:'+GRID+';'
      +'border-bottom:1px solid '+ROW+';align-items:stretch;">'
      +rankCell+tickCell+nameCell+scoreCell+priceCell+retCells+sparkCell
      +'</div>';
  });
  document.getElementById('tbody').innerHTML=body;
}

/* event delegation: header sort */
document.getElementById('thead').addEventListener('click',function(e){
  var el=e.target.closest('[data-k]');
  if(!el) return;
  var k=el.getAttribute('data-k');
  if(!k) return;
  if(st_.key===k) st_.dir=-st_.dir;
  else { st_.key=k; st_.dir=(k==='tick'||k==='name')?1:-1; }
  render();
  document.getElementById('scroller').scrollTop=0;
});

render();
"""

    js = (js
          .replace("__PAYLOAD__", payload_json)
          .replace("__RED__", _RED).replace("__TEAL__", _TEAL)
          .replace("__INK__", _INK).replace("__INK2__", _INK2)
          .replace("__MUT__", _MUT).replace("__DIM__", _DIM)
          .replace("__PAPER__", _PAPER).replace("__EDGE__", _EDGE)
          .replace("__ROW__", _ROW)
          .replace("__MONO__", json.dumps(_MONO))
          .replace("__SANS__", json.dumps(_SANS))
          .replace("__GRID__", _GRID))

    nm = labels.get("nm_label", "NM")
    footnote = labels.get("footnote", "")
    brand    = labels.get("brand", "CMSI")

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;font-family:{_SANS};'
        f'font-feature-settings:"tnum","ss01";}}'
        '.hrow{transition:background .1s;}'
        '.hrow:hover{background:rgba(255,255,255,.75);}'
        f'#scroller{{max-height:{table_max_h}px;overflow:auto;}}'
        '</style></head><body>'

        # 玻璃卡表格外框
        f'<div style="border:1px solid {_EDGE};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;">'
        '<div style="min-width:900px;">'
        f'<div id="scroller">'

        # sticky 列头（ink top-bar）
        f'<div id="thead" style="position:sticky;top:0;z-index:3;display:grid;'
        f'grid-template-columns:{_GRID};'
        f'background:{_PAPER};border-bottom:2px solid {_INK};"></div>'

        # 表体
        '<div id="tbody"></div>'
        '</div></div></div>'

        # 口径脚注
        f'<div style="margin-top:14px;border-top:1px solid {_INK};padding-top:8px;'
        f'display:flex;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-size:11px;line-height:1.7;color:{_MUT};max-width:860px;">'
        f'{footnote}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">{brand}</span>'
        '</div>'

        f'{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, iframe_h
