"""CMSI Strategy Picks · v4/v5 评分池全量打分明细表 — lib/scorecard_table.py
======================================================================

数据源：L6 归因附表 data/external/v4_v5_full_scorecard.md（strategy.load_scorecard
解析），替换 v4/v5 底部 expander 里原来的行情列全池表（1日/5日/1月 等对全池
无意义——未建仓票根本没跟踪股价）。

一个公共函数：
  render(rows, labels, height) -> (doc, iframe_h)

设计与 lib/picks_table.render_holdings 同族（玻璃卡 + sticky 表头 + 列排序 JS）：
  - 青涨(#0d7680) / 红跌(#c8102e) 颜色规范锁定，禁止翻转
  - Final 列加粗 + teal mini-bar（按池内区间拉伸）
  - 段收益列按列内幅度 tint（S=0.16），仅已建仓票有值
  - ●（建仓）= 红色实心点；未建仓 = 消字 "—"
  - 字体: theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN）
  - iframe body transparent，让页面 cream+wash 透出

rows 每行（load_scorecard 的 to_dict("records")）：
  {num:int, held:bool, tick:str, name:str, ta:str,
   p/e/f/m/r/final/seg_ret: float|None, driver:str}
"""
from __future__ import annotations

import json
import math

from lib import theme

_RED   = theme.CMSI_RED
_TEAL  = theme.UP
_INK   = theme.INK
_INK2  = theme.INK_2
_MUT   = theme.INK_3
_DIM   = theme.INK_4
_PAPER = theme.PAPER
_EDGE  = theme.PAPER_EDGE
_ROW   = theme.PAPER_RULE

# 默认（biotech）子评分列；HD 调用方传 [("gov","治理55"),("fin","财务25"),("moat","护城河20")]
_DEFAULT_SUB_COLS = [("p", "P"), ("e", "E"), ("f", "F"), ("m", "M"), ("r", "R")]

_MONO = "'JetBrains Mono',monospace"
_SANS = ("'Inter','Space Grotesk','PingFang SC','Hiragino Sans GB',"
         "'Noto Sans SC','Microsoft YaHei',sans-serif")


def _clean(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _fmt_signed(v: float, suffix: str = "%") -> str:
    sign = "+" if v >= 0 else "−"
    return f"{sign}{abs(v):.2f}{suffix}"


def _summary_strip(summary: dict, labels: dict) -> str:
    """选中效果 stat 条（top20 等权 / 全池等权 / 仅未建仓 / 基准 / top20−全池）。

    summary keys: top20 / pool / unheld / unheld_n / bench / bench_label / diff_pp
    （均为段收益 %，diff_pp 为 top20 − 全池的百分点差）。"""
    def _col(v: float) -> str:
        return _TEAL if v >= 0 else _RED

    cells = [
        (labels.get("sum_top20", "top20 等权"), _fmt_signed(summary["top20"]),
         _col(summary["top20"]), ""),
        (labels.get("sum_pool", "全池等权"), _fmt_signed(summary["pool"]),
         _col(summary["pool"]), ""),
        (labels.get("sum_unheld", "仅未建仓"), _fmt_signed(summary["unheld"]),
         _col(summary["unheld"]), f'({summary.get("unheld_n", "")}{labels.get("sum_n_suffix", "支")})'),
        (str(summary.get("bench_label", "XBI")), _fmt_signed(summary["bench"]),
         _col(summary["bench"]), ""),
        (labels.get("sum_diff", "top20 vs 全池"), _fmt_signed(summary["diff_pp"], "pp"),
         _col(summary["diff_pp"]), labels.get("sum_diff_note", "选中效果")),
    ]
    cell_html = ""
    for i, (lab, val, col, note) in enumerate(cells):
        border = f"border-left:1px solid {_ROW};" if i else ""
        note_html = (f'<span style="font-family:{_SANS};font-size:10.5px;color:{_MUT};'
                     f'margin-left:5px;">{note}</span>') if note else ""
        cell_html += (
            f'<div style="{border}padding:10px 14px 11px;display:flex;'
            f'flex-direction:column;gap:3px;min-width:0;">'
            f'<span style="font-family:{_MONO};font-size:9.5px;font-weight:600;'
            f'letter-spacing:.08em;color:{_MUT};text-transform:uppercase;'
            f'white-space:nowrap;">{lab}</span>'
            f'<span style="white-space:nowrap;">'
            f'<span style="font-family:{_MONO};font-size:16px;font-weight:700;'
            f'color:{col};letter-spacing:-.01em;">{val}</span>{note_html}</span>'
            f'</div>'
        )
    return (
        f'<div style="border:1px solid {_EDGE};border-bottom:0;border-radius:2px 2px 0 0;'
        f'background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);display:grid;'
        f'grid-template-columns:repeat(5,minmax(0,1fr));overflow-x:auto;">'
        f'{cell_html}'
        f'</div>'
    )


def render(rows: list[dict], labels: dict, height: int = 620,
           summary: dict | None = None,
           sub_cols: list[tuple[str, str]] | None = None,
           sub_dp: int = 1, final_dp: int = 2,
           tag_w: int = 118, min_width: int = 1060) -> tuple[str, int]:
    """Build the full-scorecard glass table. Returns (doc, iframe_h).

    labels keys: col_num / col_held / col_tick / col_name / col_ta /
      col_final / col_seg / col_driver / nm_label / footnote / brand
      (+ sum_* keys when `summary` is passed)

    sub_cols: [(row_key, header_label), ...] 子评分列（默认 biotech P/E/F/M/R；
      HD 传 治理/财务/护城河 三列）。sub_dp/final_dp = 小数位（HD 整数分传 0）。
    tag_w: TA/行业列宽 px。summary (optional): 选中效果 stat 条，见 _summary_strip。
    """
    if sub_cols is None:
        sub_cols = _DEFAULT_SUB_COLS
    sub_keys = [k for k, _ in sub_cols]

    clean_rows: list[dict] = []
    for r in rows:
        cr = {
            "num":     int(r.get("num", 0)),
            "held":    bool(r.get("held", False)),
            "tick":    str(r.get("tick", "")),
            "name":    str(r.get("name", "")),
            "ta":      str(r.get("ta", "") or ""),
            "final":   _clean(r.get("final")),
            "seg":     _clean(r.get("seg_ret")),
            "seg_bf":  bool(r.get("seg_bf", False)),
            "driver":  str(r.get("driver", "") or ""),
        }
        for k in sub_keys:
            cr[k] = _clean(r.get(k))
        clean_rows.append(cr)

    payload_json = json.dumps(
        {"rows": clean_rows, "labels": labels,
         "subCols": [{"k": k, "label": lab} for k, lab in sub_cols],
         "fmt": {"sub": int(sub_dp), "final": int(final_dp)}},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    # grid: # / 建 / 代码 / 名称 / TA(行业) / sub_cols… / Final / 段收益 / 驱动·状态
    grid = (f"40px 36px 62px minmax(148px,1fr) {tag_w}px "
            + "44px " * len(sub_cols)
            + "64px 76px minmax(200px,1.3fr)")

    summary_html = _summary_strip(summary, labels) if summary else ""
    summary_h    = 64 if summary else 0
    table_max_h  = max(240, height - 60)
    iframe_h     = height + summary_h

    LT   = chr(60)
    TAG  = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"

    font_face = theme.FONT_FACE_CSS.strip()

    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var rows = P.rows;

var RED   = '__RED__', TEAL = '__TEAL__', INK = '__INK__';
var INK2  = '__INK2__', MUT = '__MUT__',  DIM = '__DIM__';
var PAPER = '__PAPER__', ROW = '__ROW__';
var mono  = __MONO__, sans = __SANS__;
var GRID  = '__GRID__';
var S     = 0.16;   /* seg-ret tint strength */

/* sub-score cols (biotech P/E/F/M/R or HD 治理/财务/护城河) share one renderer */
var SUB_COLS = P.subCols;
var FMT = P.fmt;

var st_ = {key:'num', dir:1};

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function fmtPct(v){
  if(v===null||v===undefined) return '<span style="color:'+DIM+';">'+(L.nm_label||'—')+'</span>';
  var s=v>=0?'+':'-';
  var col=Math.abs(v)<0.05?MUT:(v>0?TEAL:RED);
  return '<span style="color:'+col+';font-weight:700;">'+s+Math.abs(v).toFixed(1)+'%</span>';
}

function segTint(vals, v){
  if(v===null||v===undefined||Math.abs(v)<0.05) return 'transparent';
  var vs=vals.filter(function(x){return x!==null&&x!==undefined;});
  var mx=Math.max.apply(null,vs.map(Math.abs).concat([0.0001]));
  var a=Math.min(Math.abs(v)/mx,1)*S;
  return v>0?'rgba(13,118,128,'+a.toFixed(3)+')':'rgba(200,16,46,'+a.toFixed(3)+')';
}

function finalBar(v, lo, hi){
  if(v===null||v===undefined) return '';
  var range=hi-lo; if(range<=0) range=1;
  var w=Math.max(0,Math.min(1,(v-lo)/range))*100;
  return '<div style="width:100%;height:3px;background:rgba(26,26,26,.1);border-radius:1px;margin-top:4px;">'
    +'<div style="height:100%;background:'+TEAL+';border-radius:1px;width:'+w.toFixed(1)+'%;"></div>'
    +'</div>';
}

function render(){
  /* tint 只按「跟踪值」的幅度定标 — 回补值(†)不淡染也不参与定标 */
  var segVals=rows.filter(function(r){return !r.seg_bf;}).map(function(r){return r.seg;});
  var finals=rows.map(function(r){return r.final;}).filter(function(v){return v!==null;});
  var fLo=finals.length?Math.min.apply(null,finals)-0.15:0;
  var fHi=finals.length?Math.max.apply(null,finals)+0.05:10;

  var sk=st_.key, dir=st_.dir;
  var sorted=rows.slice().sort(function(a,b){
    if(sk==='tick'||sk==='name') return String(a[sk]).localeCompare(String(b[sk]))*dir;
    if(sk==='held') return ((b.held?1:0)-(a.held?1:0))*dir;
    var x=a[sk], y=b[sk];
    var xB=(x===null||x===undefined), yB=(y===null||y===undefined);
    if(xB&&yB) return 0; if(xB) return 1; if(yB) return -1;
    return (x-y)*dir;
  });

  var cols=[
    {k:'num',   label:L.col_num,   align:'center'},
    {k:'held',  label:L.col_held,  align:'center'},
    {k:'tick',  label:L.col_tick,  align:'left'},
    {k:'name',  label:L.col_name,  align:'left'},
    {k:'ta',    label:L.col_ta,    align:'left', nosort:true}
  ].concat(SUB_COLS.map(function(c){return {k:c.k,label:c.label,align:'right'};}))
   .concat([
    {k:'final', label:L.col_final, align:'right'},
    {k:'seg',   label:L.col_seg,   align:'right'},
    {k:'driver',label:L.col_driver,align:'left', nosort:true}
  ]);

  var hdr='';
  cols.forEach(function(c){
    var on=c.k===sk;
    hdr+='<div data-k="'+(c.nosort?'':c.k)+'" style="cursor:'+(c.nosort?'default':'pointer')+';'
      +'display:flex;align-items:center;'
      +'justify-content:'+(c.align==='center'?'center':c.align==='right'?'flex-end':'flex-start')+';'
      +'padding:8px 7px 9px;font-family:'+mono+';font-size:10px;letter-spacing:.06em;'
      +'font-weight:'+(on?700:600)+';color:'+(on?RED:INK2)+';">'
      +esc(c.label)+(on?(dir>0?' ▴':' ▾'):'')
      +'</div>';
  });
  document.getElementById('thead').innerHTML=hdr;

  var body='';
  sorted.forEach(function(r){
    var numCell='<div style="display:flex;align-items:center;justify-content:center;padding:9px 4px;'
      +'font-family:'+mono+';font-size:11px;font-weight:600;color:'+MUT+';">'+r.num+'</div>';

    var heldCell='<div style="display:flex;align-items:center;justify-content:center;padding:9px 4px;">'
      +(r.held
        ?'<span style="width:9px;height:9px;border-radius:50%;background:'+RED+';display:inline-block;"></span>'
        :'<span style="color:'+DIM+';font-size:11px;">—</span>')
      +'</div>';

    var tickCell='<div style="padding:9px 7px;display:flex;align-items:center;font-family:'+mono
      +';font-size:11px;font-weight:600;color:'+MUT+';">'+esc(r.tick)+'</div>';

    var nameCell='<div style="padding:9px 7px;display:flex;align-items:center;font-family:'+sans
      +';font-size:12.5px;font-weight:600;color:'+INK+';white-space:nowrap;overflow:hidden;'
      +'text-overflow:ellipsis;min-width:0;"><span style="overflow:hidden;text-overflow:ellipsis;">'
      +esc(r.name)+'</span></div>';

    var taCell='<div style="padding:9px 7px;display:flex;align-items:center;font-family:'+sans
      +';font-size:11px;color:'+MUT+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
      +'min-width:0;"><span style="overflow:hidden;text-overflow:ellipsis;">'
      +(r.ta?esc(r.ta):'<span style="color:'+DIM+';">—</span>')+'</span></div>';

    var subCells='';
    SUB_COLS.forEach(function(c){
      var v=r[c.k];
      subCells+='<div style="padding:9px 7px;display:flex;align-items:center;justify-content:flex-end;'
        +'font-family:'+mono+';font-size:11.5px;font-variant-numeric:tabular-nums;color:'+INK2+';">'
        +((v===null||v===undefined)?'<span style="color:'+DIM+';">'+(L.nm_label||'—')+'</span>':v.toFixed(FMT.sub))
        +'</div>';
    });

    var finalInner;
    if(r.final===null||r.final===undefined){
      finalInner='<span style="color:'+DIM+';">'+(L.nm_label||'—')+'</span>';
    } else {
      finalInner='<div style="width:100%;text-align:right;">'
        +'<span style="font-size:13.5px;font-weight:700;color:'+INK+';">'+r.final.toFixed(FMT.final)+'</span>'
        +finalBar(r.final,fLo,fHi)
        +'</div>';
    }
    var finalCell='<div style="padding:9px 7px;display:flex;flex-direction:column;justify-content:center;'
      +'align-items:stretch;font-family:'+mono+';font-variant-numeric:tabular-nums;">'+finalInner+'</div>';

    /* 段收益: 跟踪值=青/红加粗+列内tint; 回补值(未建仓,事后补算)=灰色+†,无tint */
    var segHtml, segBg;
    if(r.seg===null||r.seg===undefined){
      segHtml='<span style="color:'+DIM+';">'+(L.nm_label||'—')+'</span>'; segBg='transparent';
    } else if(r.seg_bf){
      var sn=r.seg>=0?'+':'-';
      segHtml='<span style="color:'+MUT+';font-weight:600;">'+sn+Math.abs(r.seg).toFixed(1)+'%†</span>';
      segBg='transparent';
    } else {
      segHtml=fmtPct(r.seg); segBg=segTint(segVals,r.seg);
    }
    var segCell='<div style="padding:9px 7px;display:flex;align-items:center;justify-content:flex-end;'
      +'font-family:'+mono+';font-size:12px;font-variant-numeric:tabular-nums;background:'
      +segBg+';">'+segHtml+'</div>';

    var drvDim=(!r.held||r.driver.charAt(0)==='—');
    var drvCell='<div style="padding:9px 7px;display:flex;align-items:center;font-family:'+sans
      +';font-size:11.5px;line-height:1.4;color:'+(drvDim?DIM:INK2)+';min-width:0;">'
      +esc(r.driver)+'</div>';

    body+='<div class="hrow" style="display:grid;grid-template-columns:'+GRID+';'
      +'border-bottom:1px solid '+ROW+';align-items:stretch;">'
      +numCell+heldCell+tickCell+nameCell+taCell+subCells+finalCell+segCell+drvCell
      +'</div>';
  });
  document.getElementById('tbody').innerHTML=body;
}

document.getElementById('thead').addEventListener('click',function(e){
  var el=e.target.closest('[data-k]');
  if(!el) return;
  var k=el.getAttribute('data-k');
  if(!k) return;
  if(st_.key===k) st_.dir=-st_.dir;
  else { st_.key=k; st_.dir=(k==='tick'||k==='name'||k==='num')?1:-1; }
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
          .replace("__PAPER__", _PAPER).replace("__ROW__", _ROW)
          .replace("__MONO__", json.dumps(_MONO))
          .replace("__SANS__", json.dumps(_SANS))
          .replace("__GRID__", grid))

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

        f'{summary_html}'

        f'<div style="border:1px solid {_EDGE};'
        f'border-radius:{"0 0 2px 2px" if summary else "2px"};'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;">'
        f'<div style="min-width:{min_width}px;">'
        f'<div id="scroller">'

        f'<div id="thead" style="position:sticky;top:0;z-index:3;display:grid;'
        f'grid-template-columns:{grid};'
        f'background:{_PAPER};border-bottom:2px solid {_INK};"></div>'

        '<div id="tbody"></div>'
        '</div></div></div>'

        f'<div style="margin-top:14px;border-top:1px solid {_INK};padding-top:8px;'
        f'display:flex;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-size:11px;line-height:1.7;color:{_MUT};max-width:900px;">'
        f'{footnote}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">{brand}</span>'
        '</div>'

        f'{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, iframe_h
