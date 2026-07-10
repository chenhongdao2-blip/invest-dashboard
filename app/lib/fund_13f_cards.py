"""13F 分基金持仓卡 — lib/fund_13f_cards.py
====================================================

设计源(1:1 移植):claude.ai/design 「13F 分基金持仓 美化.dc.html」
(handoff zip (7) → three-js/project/,2026-07-10 George 提供)。

替换 2_Healthcare.py 13F section 的旧 Block C(每基金 st.expander + 裸 html 表):
整块 = 一张自包含 st.iframe,12 家基金各一张玻璃卡(可折叠,客户端切换无 rerun):
- 基金头:折叠 caret + 名称 + AUM(红 mono)+「N 只持仓 · 申报日期 · 显示前 N 大」
  + 右侧快览(第一大重仓 / 本季动向 新+加/减/平 计数)
- 集中度条:前 N 大权重叠加,分段红→暖棕渐变
- 持仓表 grid:名次+代码+名称 / 权重条(以该基金前 N 大最大权重为满刻度,
  #1 红、#2-3 红 .75、其余墨 .42)/ 合计市值 / 季度动向 chip(新进·加仓 teal /
  减仓 red / 持平 muted+dot)/ 持股数 Δ%(teal/red 染字)
- 口径脚注 + CMSI brand

设计约束(勿回退):
- 字体 theme.FONT_FACE_CSS 自托管(禁 Google Fonts CDN);iframe body transparent
- 涨/加 teal #0d7680 · 减/卖 CMSI_RED #c8102e,配色锁定不翻转
- 数字 tabular-nums / 无 emoji / 零 box-shadow / radius ≤ 2
- 默认第一家展开、其余折叠;整卡列表内滚(单 iframe,高度固定,内部 scroller)

数据:page 侧传 funds = f13.funds_ok(data)(原始 dict,weight/shares_chg_pct 为小数)。
"""
from __future__ import annotations

import json
import math

from lib import theme

_RED = theme.CMSI_RED
_TEAL = theme.UP
_INK = theme.INK
_INK2 = theme.INK_2
_MUT = "#8a8580"
_DIM = "#b8b1a8"
_EDGE = "#d4c4b0"
_SEP = "#e2d3c1"
_RULE = "#ebd9c8"

_MONO = "'JetBrains Mono',monospace"
_SANS = ("'Inter','Space Grotesk','PingFang SC','Hiragino Sans GB',"
         "'Noto Sans SC','Microsoft YaHei',sans-serif")

# 设计稿 5 列 grid:标的 / 组合权重 / 合计市值 / 季度动向 / 持股数 Δ%
_GRID = "minmax(150px,1.1fr) 220px 96px 104px 112px"


def _clean(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _fund_payload(f: dict, top_n: int) -> dict:
    """One fund dict → JSON-safe card payload. weight/shares_chg_pct 保持小数,
    JS 侧 ×100;qoq 原样传(NEW/ADD/TRIM/UNCH)。"""
    holds = []
    for h in (f.get("top_holdings") or [])[:top_n]:
        holds.append({
            "tick": str(h.get("ticker") or "") or str(h.get("issuer", "?"))[:14],
            "name": str(h.get("issuer") or ""),
            "w": _clean(h.get("weight")),
            "val": _clean(h.get("value")),
            "qoq": str(h.get("qoq") or "UNCH"),
            "chg": _clean(h.get("shares_chg_pct")),
        })
    return {
        "name": str(f.get("name") or "?"),
        "aum": _clean(f.get("total_value")),
        "count": int(f.get("n_positions") or 0),
        "date": str(f.get("period") or "—"),
        "stale": f.get("status") == "stale",
        "holds": holds,
    }


def render_fund_cards(
    funds: list[dict],
    labels: dict,
    *,
    top_n: int = 15,
    height: int = 780,
) -> tuple[str, int]:
    """Build the per-fund cards iframe. Returns (doc, iframe_h).

    labels keys: legend_add / legend_trim / legend_flat / qoq_new / qoq_add /
    qoq_trim / qoq_flat / holdings_meta("{count} 只持仓 · 申报 {date} · 显示前 {n} 大")
    / top_hold / q_moves / conc / col_name / col_weight / col_value / col_move /
    col_delta / footnote / brand / stale。
    """
    payload = {
        "funds": [_fund_payload(f, top_n) for f in funds if f.get("top_holdings")],
        "labels": labels,
        "topN": top_n,
    }
    payload_json = json.dumps(payload, ensure_ascii=False,
                              separators=(",", ":")).replace("</", "<\\/")

    LT = chr(60)
    TAG = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"
    font_face = theme.FONT_FACE_CSS.strip()
    scroll_h = max(300, height - 24)

    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', INK2='__INK2__';
var MUT='__MUT__', DIM='__DIM__', EDGE='__EDGE__', SEP='__SEP__', RULE='__RULE__';
var mono=__MONO__, sans=__SANS__;
var GRID='__GRID__';
var open_ = {};
P.funds.forEach(function(f,i){ open_[i] = (i===0); });   /* 第一家默认展开 */

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtAum(v){
  if(v==null) return '—';
  return '$' + (v/1e9).toFixed(1) + 'bn';
}
function fmtVal(v){
  if(v==null) return '—';
  var b = v/1e9;
  return b >= 1 ? '$'+b.toFixed(1)+'B' : '$'+(v/1e6).toFixed(0)+'M';
}
/* 集中度分段色:红 → 暖棕 渐变(设计稿 concColor) */
function concColor(i,n){
  var t = i/Math.max(n-1,1);
  var a=[200,16,46], b=[184,171,152];
  var c=a.map(function(x,k){ return Math.round(x+(b[k]-x)*t); });
  return 'rgb('+c[0]+','+c[1]+','+c[2]+')';
}
var QOQ = {
  NEW:  {label:L.qoq_new,  fg:TEAL, bg:'rgba(13,118,128,.16)', fw:700, dot:false},
  ADD:  {label:L.qoq_add,  fg:TEAL, bg:'rgba(13,118,128,.12)', fw:700, dot:false},
  TRIM: {label:L.qoq_trim, fg:RED,  bg:'rgba(200,16,46,.10)',  fw:700, dot:false},
  UNCH: {label:L.qoq_flat, fg:MUT,  bg:'rgba(26,26,26,.05)',   fw:600, dot:true}
};

function hdrCell(txt, align, bl){
  return '<span style="font-family:'+mono+';font-size:10px;letter-spacing:.05em;color:'+INK2+';'
    +'font-weight:500;padding:8px 10px;text-align:'+align+';'
    +(bl?'border-left:1px solid '+SEP+';':'')+'">'+esc(txt)+'</span>';
}

function fundCard(f, idx){
  var isOpen = open_[idx];
  var shown = f.holds.length;
  var nAdd=0,nTrim=0,nFlat=0;
  f.holds.forEach(function(h){
    if(h.qoq==='NEW'||h.qoq==='ADD') nAdd++;
    else if(h.qoq==='TRIM') nTrim++;
    else nFlat++;
  });
  var maxW = 0.0001, concSum = 0;
  f.holds.forEach(function(h){ if(h.w!=null){ maxW=Math.max(maxW,h.w); concSum+=h.w; } });
  var top0 = f.holds[0] || {};
  var meta = L.holdings_meta.replace('{count}', f.count).replace('{date}', f.date).replace('{n}', shown);
  var stale = f.stale ? ' <span style="color:'+RED+';font-weight:700;">'+esc(L.stale)+'</span>' : '';

  /* --- 基金头(点击折叠) --- */
  var head =
    '<button data-idx="'+idx+'" style="appearance:none;width:100%;text-align:left;cursor:pointer;'
    +'border:none;background:transparent;display:flex;align-items:center;gap:14px;'
    +'padding:14px 20px;font-family:inherit;flex-wrap:wrap;">'
    +'<span style="font-family:'+mono+';font-size:12px;color:'+MUT+';width:14px;flex:none;">'+(isOpen?'▾':'▸')+'</span>'
    +'<div style="min-width:0;">'
    +'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">'
    +'<span style="font-size:16px;font-weight:700;color:'+INK+';letter-spacing:-.01em;">'+esc(f.name)+'</span>'
    +'<span style="font-family:'+mono+';font-size:12px;font-weight:700;color:'+RED+';">'+fmtAum(f.aum)+'</span></div>'
    +'<div style="font-family:'+mono+';font-size:10.5px;color:'+MUT+';margin-top:3px;letter-spacing:.02em;">'+meta+stale+'</div>'
    +'</div>'
    +'<div style="margin-left:auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap;">'
    +'<div style="text-align:right;">'
    +'<div style="font-family:'+mono+';font-size:9.5px;letter-spacing:.1em;color:'+MUT+';">'+esc(L.top_hold)+'</div>'
    +'<div style="font-family:'+mono+';font-size:12px;font-weight:700;color:'+INK+';margin-top:2px;">'
    +esc(top0.tick||'—')+' · '+(top0.w!=null?(top0.w*100).toFixed(2)+'%':'—')+'</div></div>'
    +'<div style="text-align:right;border-left:1px solid '+SEP+';padding-left:18px;">'
    +'<div style="font-family:'+mono+';font-size:9.5px;letter-spacing:.1em;color:'+MUT+';">'+esc(L.q_moves)+'</div>'
    +'<div style="display:flex;align-items:baseline;gap:9px;margin-top:3px;font-family:'+mono+';font-size:12px;font-weight:700;">'
    +'<span style="color:'+TEAL+';">'+esc(L.legend_add)+' '+nAdd+'</span>'
    +'<span style="color:'+RED+';">'+esc(L.legend_trim)+' '+nTrim+'</span>'
    +'<span style="color:'+MUT+';">'+esc(L.legend_flat)+' '+nFlat+'</span>'
    +'</div></div></div></button>';

  if(!isOpen){
    return '<div style="border:1px solid '+EDGE+';border-top:2px solid '+RED+';border-radius:2px;'
      +'background:rgba(255,255,255,.5);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);'
      +'overflow:hidden;">'+head+'</div>';
  }

  /* --- 集中度条 --- */
  var segs='';
  f.holds.forEach(function(h,i){
    var w = h.w!=null ? (h.w/(concSum||1)*100) : 0;
    segs += '<span style="width:'+w.toFixed(2)+'%;background:'+concColor(i,shown)
      +';border-right:1px solid rgba(255,241,229,.5);"></span>';
  });
  var conc =
    '<div style="display:flex;align-items:center;gap:12px;padding:0 20px 12px;flex-wrap:wrap;">'
    +'<span style="font-family:'+mono+';font-size:9.5px;letter-spacing:.1em;color:'+MUT+';flex:none;">'
    +esc(L.conc.replace('{n}', shown))+'</span>'
    +'<span style="display:flex;height:8px;flex:1;min-width:220px;border-radius:2px;overflow:hidden;background:#eddccb;">'+segs+'</span>'
    +'<span style="font-family:'+mono+';font-size:12px;font-weight:700;color:'+INK+';flex:none;">'
    +(concSum*100).toFixed(0)+'%</span></div>';

  /* --- 持仓表 --- */
  var thead = '<div style="display:grid;grid-template-columns:'+GRID+';padding:0 20px;'
    +'background:rgba(255,241,229,.92);border-bottom:2px solid '+INK+';">'
    +hdrCell(L.col_name,'left',false)
    +hdrCell(L.col_weight,'left',false)
    +hdrCell(L.col_value,'right',true)
    +hdrCell(L.col_move,'left',false)
    +hdrCell(L.col_delta,'right',false)
    +'</div>';

  var body='';
  f.holds.forEach(function(h,i){
    var mv = QOQ[h.qoq] || QOQ.UNCH;
    var wBar = h.w!=null ? (h.w/maxW*100).toFixed(1)+'%' : '0%';
    var wColor = i===0 ? RED : (i<3 ? 'rgba(200,16,46,.75)' : 'rgba(26,26,26,.42)');
    var d = h.chg;
    var flatD = (d==null) || Math.abs(d) < 0.00005;
    var dTxt = (d==null) ? '—' : (flatD ? '—' : ((d>0?'+':'-') + Math.abs(d*100).toFixed(2) + '%'));
    var dFg = flatD ? DIM : (d>0 ? TEAL : RED);
    var dot = mv.dot ? '<span style="width:4px;height:4px;border-radius:50%;background:'+DIM+';"></span>' : '';
    body += '<div class="frow" style="display:grid;grid-template-columns:'+GRID+';padding:0 20px;'
      +'border-bottom:1px solid '+RULE+';">'
      /* 标的 */
      +'<span style="display:flex;align-items:center;gap:9px;padding:8px 10px;min-width:0;">'
      +'<span style="font-family:'+mono+';font-size:10px;color:'+DIM+';flex:none;">'+String(i+1).padStart(2,'0')+'</span>'
      +'<span style="font-family:'+mono+';font-size:12.5px;font-weight:700;color:'+INK+';flex:none;">'+esc(h.tick)+'</span>'
      +'<span style="font-size:11px;color:'+MUT+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;">'+esc(h.name)+'</span></span>'
      /* 权重条 */
      +'<span style="display:flex;align-items:center;gap:10px;padding:8px 10px;">'
      +'<span style="display:block;flex:1;height:9px;background:rgba(26,26,26,.06);border-radius:2px;overflow:hidden;">'
      +'<span style="display:block;height:100%;background:'+wColor+';border-radius:2px;width:'+wBar+';"></span></span>'
      +'<span style="font-family:'+mono+';font-size:12px;font-weight:700;color:'+INK+';font-variant-numeric:tabular-nums;width:56px;text-align:right;flex:none;">'
      +(h.w!=null?(h.w*100).toFixed(2)+'%':'—')+'</span></span>'
      /* 合计市值 */
      +'<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11.5px;color:'+INK2+';'
      +'padding:8px 10px;font-variant-numeric:tabular-nums;border-left:1px solid '+SEP+';">'+fmtVal(h.val)+'</span>'
      /* 季度动向 chip */
      +'<span style="display:flex;align-items:center;padding:8px 10px;">'
      +'<span style="display:inline-flex;align-items:center;gap:5px;font-family:'+mono+';font-size:10.5px;font-weight:'+mv.fw
      +';color:'+mv.fg+';background:'+mv.bg+';border-radius:2px;padding:3px 8px;">'+dot+esc(mv.label)+'</span></span>'
      /* Δ% */
      +'<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:12px;font-weight:'
      +(flatD?500:700)+';color:'+dFg+';padding:8px 10px;font-variant-numeric:tabular-nums;">'+dTxt+'</span>'
      +'</div>';
  });

  return '<div style="border:1px solid '+EDGE+';border-top:2px solid '+RED+';border-radius:2px;'
    +'background:rgba(255,255,255,.5);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);'
    +'overflow:hidden;">'
    +head+conc
    +'<div style="overflow-x:auto;border-top:1px solid '+EDGE+';"><div style="min-width:760px;">'
    +thead+body+'</div></div></div>';
}

function render(){
  var html='';
  P.funds.forEach(function(f,i){ html += fundCard(f,i); });
  document.getElementById('cards').innerHTML = html;
}
document.getElementById('cards').addEventListener('click', function(e){
  var el = e.target.closest('[data-idx]');
  if(!el) return;
  var i = +el.getAttribute('data-idx');
  open_[i] = !open_[i];
  render();
});
render();
"""

    js = (js
          .replace("__PAYLOAD__", payload_json)
          .replace("__RED__", _RED).replace("__TEAL__", _TEAL)
          .replace("__INK__", _INK).replace("__INK2__", _INK2)
          .replace("__MUT__", _MUT).replace("__DIM__", _DIM)
          .replace("__EDGE__", _EDGE).replace("__SEP__", _SEP)
          .replace("__RULE__", _RULE)
          .replace("__MONO__", json.dumps(_MONO))
          .replace("__SANS__", json.dumps(_SANS))
          .replace("__GRID__", _GRID))

    footnote = labels.get("footnote", "")
    brand = labels.get("brand", "CMSI · 13F HOLDINGS")

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;font-family:{_SANS};'
        f'font-feature-settings:"tnum","ss01";}}'
        '.frow{transition:background .12s;}'
        '.frow:hover{background:rgba(255,255,255,.8);}'
        f'#scroller{{max-height:{scroll_h}px;overflow-y:auto;'
        'display:flex;flex-direction:column;gap:16px;padding-right:2px;}}'
        '</style></head><body>'
        '<div id="scroller"><div id="cards" style="display:flex;flex-direction:column;gap:16px;"></div>'
        # 口径脚注
        f'<div style="border-top:1px solid {_INK};padding-top:8px;display:flex;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-size:11px;line-height:1.7;color:{_MUT};max-width:900px;">{footnote}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">{brand}</span></div>'
        '</div>'
        f'{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, height
