"""日本医药 子板块明细 — lib/japan_panel.py
====================================================

设计源(1:1 移植):claude.ai/design 「日本医药 子板块明细 美化.dc.html」
(handoff zip (7) → three-js/project/,2026-07-10 George 提供)。

替换 2_Healthcare.py 日本 section 的旧 _render_pct_table 双表(子板块汇总 + 40 支
明细),两块各自一张自包含 st.iframe(全客户端,无 rerun):

render_summary(sub_rows, labels)  — 子板块汇总:等权平均收益 4 窗口(列内幅度 tint)
                                    + YTD 分布条(零轴居中,列内最大幅度为满刻度)。
                                    行点击 → postMessage?否——迷你交互仅高亮,筛选
                                    联动放在明细卡自己的 chips(iframe 间无状态共享)。
render_detail(rows, labels, verdict) — 标的明细:子板块 chips 筛选(tone 色)+ 可排序
                                    列头 + 回报 tint(列内幅度、青涨红跌)+ 子板块
                                    chip 染色;底部「研判 · 速览」玻璃卡(领跌/领涨
                                    两 chip 卡从真数据计算 + 口径提示段)。

设计约束(勿回退):
- 字体 theme.FONT_FACE_CSS 自托管(禁 Google Fonts CDN);iframe body transparent
- 青涨 #0d7680 / 红跌 #c8102e 锁定;|v|<0.05 视为平(muted、无 tint)
- 子板块 tone:制药 red / 医疗器械 ink / 诊断·检测 teal / 流通·服务 gold #E0A458
- 数字 tabular-nums / 无 emoji / 零 box-shadow / radius ≤ 2
- 下载按钮留在页面侧 st.download_button(srcdoc iframe 无法发起下载)
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
_GOLD = "#E0A458"

_MONO = "'JetBrains Mono',monospace"
_SANS = ("'Inter','Space Grotesk','PingFang SC','Hiragino Sans GB',"
         "'Noto Sans SC','Microsoft YaHei',sans-serif")

# 子板块 id → tone 色(设计稿 SUBTONE)
SUBTONE = {"pharma": _RED, "medtech": _INK, "diagnostics": _TEAL, "distribution": _GOLD}

_SGRID = "minmax(150px,1.1fr) 64px 86px 86px 86px 96px minmax(150px,1fr)"
_DGRID = "96px minmax(140px,1fr) 116px 90px 78px 78px 78px 88px"


def _clean(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _font_head(extra_css: str = "") -> str:
    font_face = theme.FONT_FACE_CSS.strip()
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;font-family:{_SANS};'
        f'font-feature-settings:"tnum","ss01";}}'
        '.jrow{transition:background .12s;}'
        '.jrow:hover{background:rgba(255,255,255,.8);}'
        f'{extra_css}'
        '</style></head><body>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. 子板块汇总(静态,纯 Python 渲染——无排序交互,不需要 JS)
# ─────────────────────────────────────────────────────────────────────────────

def render_summary(sub_rows: list[dict], labels: dict) -> tuple[str, int]:
    """sub_rows = [{sub_id, name, n, d1, d5, m1, ytd}] 等权平均(百分数,已 ×100)。
    labels: col_sub / col_n / col_1d / col_5d / col_1m / col_ytd / col_dist。
    回报 tint 按列内幅度;YTD 分布条零轴居中。返回 (doc, iframe_h)。"""
    S = 0.16
    cols = ["d1", "d5", "m1", "ytd"]
    mx = {c: max((abs(_clean(r.get(c)) or 0) for r in sub_rows), default=0) or 1 for c in cols}

    def tint(c: str, v: float | None) -> str:
        if v is None or abs(v) < 0.05:
            return "transparent"
        a = min(abs(v) / mx[c], 1) * S
        return (f"rgba(13,118,128,{a:.3f})" if v > 0 else f"rgba(200,16,46,{a:.3f})")

    def fg(v: float | None) -> str:
        if v is None or abs(v) < 0.05:
            return _MUT
        return _TEAL if v > 0 else _RED

    def fmt(v: float | None) -> str:
        if v is None:
            return "—"
        return f"{'+' if v >= 0 else '−'}{abs(v):.1f}%"

    hdr_cells = [
        (labels["col_sub"], "left", False), (labels["col_n"], "right", False),
        (labels["col_1d"], "right", True), (labels["col_5d"], "right", False),
        (labels["col_1m"], "right", False), (labels["col_ytd"], "right", False),
        (labels["col_dist"], "left", True),
    ]
    hdr = "".join(
        f'<span style="font-family:{_MONO};font-size:10px;letter-spacing:.05em;'
        f'font-weight:500;color:{_INK2};padding:8px 10px;text-align:{a};'
        f'{f"border-left:1px solid {_SEP};" if bl else ""}">{t}</span>'
        for t, a, bl in hdr_cells
    )

    ytd_max = mx["ytd"]
    body = ""
    for r in sub_rows:
        tone = SUBTONE.get(str(r.get("sub_id")), _MUT)
        v = _clean(r.get("ytd")) or 0.0
        w = min(abs(v) / ytd_max, 1) * 47
        left = 50.0 if v >= 0 else 50.0 - w
        cells = ""
        for i, c in enumerate(cols):
            cv = _clean(r.get(c))
            bl = f"border-left:1px solid {_SEP};" if i == 0 else ""
            fw = 700 if c == "ytd" else 600
            cells += (
                f'<span style="display:flex;align-items:center;justify-content:flex-end;'
                f'padding:10px;font-family:{_MONO};font-size:12px;font-weight:{fw};'
                f'color:{fg(cv)};background:{tint(c, cv)};{bl}'
                f'font-variant-numeric:tabular-nums;">{fmt(cv)}</span>'
            )
        body += (
            f'<div class="jrow" style="display:grid;grid-template-columns:{_SGRID};'
            f'padding:0 14px;border-bottom:1px solid {_RULE};">'
            f'<span style="display:flex;align-items:center;gap:8px;padding:10px;'
            f'font-size:13.5px;font-weight:600;color:{_INK};white-space:nowrap;">'
            f'<span style="width:3px;height:12px;background:{tone};border-radius:1px;flex:none;"></span>'
            f'{r.get("name","")}</span>'
            f'<span style="display:flex;align-items:center;justify-content:flex-end;padding:10px;'
            f'font-family:{_MONO};font-size:11px;color:{_MUT};">{r.get("n","")}</span>'
            f'{cells}'
            f'<span style="display:flex;align-items:center;padding:10px;border-left:1px solid {_SEP};">'
            f'<span style="position:relative;display:block;width:100%;height:8px;'
            f'background:rgba(26,26,26,.06);border-radius:1px;">'
            f'<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:#b8ab99;"></span>'
            f'<span style="position:absolute;top:0;bottom:0;left:{left:.1f}%;width:{w:.1f}%;'
            f'background:{_TEAL if v >= 0 else _RED};opacity:.8;border-radius:1px;"></span>'
            f'</span></span></div>'
        )

    h = 46 + 42 * len(sub_rows) + 14
    doc = (
        _font_head()
        + f'<div style="border:1px solid {_EDGE};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;"><div style="min-width:760px;">'
        f'<div style="display:grid;grid-template-columns:{_SGRID};padding:0 14px;'
        f'border-bottom:2px solid {_INK};background:rgba(255,241,229,.92);">{hdr}</div>'
        f'{body}</div></div></body></html>'
    )
    return doc, h


# ─────────────────────────────────────────────────────────────────────────────
# 2. 标的明细(chips 筛选 + 排序 + tint;底部研判卡)—— 客户端 JS
# ─────────────────────────────────────────────────────────────────────────────

def render_detail(
    rows: list[dict],
    labels: dict,
    verdict: dict | None = None,
    *,
    height: int = 900,
) -> tuple[str, int]:
    """rows = [{tick, name, sub_id, sub, price, d1, d5, m1, ytd}](收益百分数已×100,
    price 为 USD)。labels: chips_all / col_tick / col_name / col_sub / col_price /
    col_1d / col_5d / col_1m / col_ytd / grp_ret / shown_of / footnote / brand /
    verdict_title / verdict_meta / verdict_note(口径段 HTML)/ source_line。
    verdict = {lag: {title, body_html}, lead: {title, body_html}}(页面侧从真数据算)。"""
    clean_rows = []
    for r in rows:
        clean_rows.append({
            "tick": str(r.get("tick", "")), "name": str(r.get("name", "")),
            "subId": str(r.get("sub_id", "")), "sub": str(r.get("sub", "")),
            "price": _clean(r.get("price")),
            "d1": _clean(r.get("d1")), "d5": _clean(r.get("d5")),
            "m1": _clean(r.get("m1")), "ytd": _clean(r.get("ytd")),
        })
    payload = {"rows": clean_rows, "labels": labels,
               "tones": SUBTONE, "verdict": verdict or {}}
    payload_json = json.dumps(payload, ensure_ascii=False,
                              separators=(",", ":")).replace("</", "<\\/")

    LT = chr(60)
    TAG = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"
    scroll_h = max(320, height - 330)

    js = r"""
var P=__PAYLOAD__;
var L=P.labels, TONES=P.tones, V=P.verdict;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', INK2='__INK2__';
var MUT='__MUT__', DIM='__DIM__', SEP='__SEP__', GOLD='__GOLD__';
var mono=__MONO__;
var GRID='__DGRID__';
var S=0.16;
var st_={sub:'*', key:'subId', dir:1};

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtR(v){ if(v==null) return 'NM'; return (v>=0?'+':'-')+Math.abs(v).toFixed(1)+'%'; }
function fgOf(v){ if(v==null) return DIM; return Math.abs(v)<0.05?MUT:(v>0?TEAL:RED); }
function subBg(tone){
  if(tone===GOLD) return 'rgba(224,164,88,.16)';
  if(tone===INK)  return 'rgba(26,26,26,.07)';
  if(tone===RED)  return 'rgba(200,16,46,.10)';
  return 'rgba(13,118,128,.10)';
}
var RET=[{k:'d1',label:L.col_1d},{k:'d5',label:L.col_5d},{k:'m1',label:L.col_1m},{k:'ytd',label:L.col_ytd}];

function render(){
  /* chips */
  var subs=[]; var counts={};
  P.rows.forEach(function(r){ if(subs.indexOf(r.subId)<0) subs.push(r.subId); counts[r.subId]=(counts[r.subId]||0)+1; });
  var subName={}; P.rows.forEach(function(r){ subName[r.subId]=r.sub; });
  var chipsH='';
  [['*',L.chips_all,P.rows.length]].concat(subs.map(function(s){ return [s,subName[s],counts[s]]; }))
    .forEach(function(c){
      var on = c[0]===st_.sub;
      var tone = c[0]==='*' ? RED : (TONES[c[0]]||RED);
      chipsH += '<button data-sub="'+esc(c[0])+'" style="appearance:none;cursor:pointer;font-family:'+mono
        +';font-size:11.5px;font-weight:'+(on?700:500)+';color:'+(on?'#fff1e5':INK2)
        +';background:'+(on?tone:'#f9e6d4')+';border:1px solid '+(on?tone:'#d4c4b0')
        +';padding:6px 13px;border-radius:2px;">'+esc(c[1])
        +' <span style="opacity:.65;">'+c[2]+'</span></button>';
    });
  document.getElementById('chips').innerHTML=chipsH;

  /* filter + sort */
  var rows = P.rows.filter(function(r){ return st_.sub==='*'||r.subId===st_.sub; });
  var k=st_.key, dir=st_.dir;
  rows=rows.slice().sort(function(a,b){
    var x=a[k], y=b[k];
    if(typeof x==='string'||typeof y==='string') return String(x).localeCompare(String(y))*dir;
    var nx=(x==null)?-Infinity*dir:x, ny=(y==null)?-Infinity*dir:y;
    return (nx-ny)*dir;
  });
  document.getElementById('cnt').textContent = rows.length+' / '+P.rows.length;

  /* headers */
  var COLS=[{k:'tick',label:L.col_tick,align:'left'},{k:'name',label:L.col_name,align:'left'},
            {k:'subId',label:L.col_sub,align:'left'},{k:'price',label:L.col_price,align:'right'}];
  var hdr='';
  COLS.concat(RET.map(function(c,j){ return {k:c.k,label:c.label,align:'right',bl:j===0}; }))
    .forEach(function(c){
      var on=c.k===k;
      hdr+='<button data-k="'+c.k+'" style="appearance:none;background:transparent;border:none;cursor:pointer;'
        +'font-family:'+mono+';font-size:10px;letter-spacing:.05em;font-weight:'+(on?700:500)
        +';color:'+(on?RED:INK2)+';padding:7px 10px 9px;text-align:'+c.align+';white-space:nowrap;'
        +(c.bl?'border-left:1px solid '+SEP+';':'')+'">'
        +esc(c.label)+(on?(dir<0?' ▾':' ▴'):'')+'</button>';
    });
  document.getElementById('thead').innerHTML=hdr;

  /* tint within shown rows */
  var maxAbs={};
  RET.forEach(function(c){
    maxAbs[c.k]=Math.max.apply(null, rows.map(function(r){ return Math.abs(r[c.k]==null?0:r[c.k]); }).concat([0.0001]));
  });
  function tint(ck,v){
    if(v==null||Math.abs(v)<0.05) return 'transparent';
    var a=Math.min(Math.abs(v)/maxAbs[ck],1)*S;
    return v>0?'rgba(13,118,128,'+a.toFixed(3)+')':'rgba(200,16,46,'+a.toFixed(3)+')';
  }

  var body='';
  rows.forEach(function(r){
    var tone=TONES[r.subId]||MUT;
    var rets='';
    RET.forEach(function(c,j){
      var v=r[c.k];
      rets+='<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono
        +';font-size:12px;font-weight:'+(c.k==='ytd'?700:600)+';color:'+fgOf(v)+';background:'+tint(c.k,v)
        +';padding:8px 10px;white-space:nowrap;'+(j===0?'border-left:1px solid '+SEP+';':'')
        +'font-variant-numeric:tabular-nums;">'+fmtR(v)+'</span>';
    });
    body+='<div class="jrow" style="display:grid;grid-template-columns:'+GRID+';padding:0 14px;'
      +'border-bottom:1px solid __RULE__;">'
      +'<span style="display:flex;align-items:center;font-family:'+mono+';font-size:11.5px;font-weight:600;color:'+INK+';padding:8px 10px;white-space:nowrap;">'+esc(r.tick)+'</span>'
      +'<span style="align-self:center;font-size:13px;font-weight:500;color:'+INK+';padding:8px 10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;display:block;">'+esc(r.name)+'</span>'
      +'<span style="display:flex;align-items:center;padding:8px 10px;">'
      +'<span style="font-family:'+mono+';font-size:10.5px;color:'+tone+';background:'+subBg(tone)+';border-radius:2px;padding:2px 8px;white-space:nowrap;">'+esc(r.sub)+'</span></span>'
      +'<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:12px;color:'+INK2+';padding:8px 10px;font-variant-numeric:tabular-nums;">'
      +(r.price==null?'—':'$'+r.price.toFixed(2))+'</span>'
      +rets+'</div>';
  });
  document.getElementById('tbody').innerHTML=body;
}

document.getElementById('chips').addEventListener('click',function(e){
  var el=e.target.closest('[data-sub]'); if(!el) return;
  var s=el.getAttribute('data-sub');
  st_.sub = (st_.sub===s)?'*':s;
  render();
});
document.getElementById('thead').addEventListener('click',function(e){
  var el=e.target.closest('[data-k]'); if(!el) return;
  var kk=el.getAttribute('data-k');
  if(st_.key===kk) st_.dir=-st_.dir;
  else { st_.key=kk; st_.dir=(kk==='tick'||kk==='name'||kk==='subId')?1:-1; }
  render();
  document.getElementById('scroller').scrollTop=0;
});

/* 研判卡(静态,从 payload verdict 填) */
(function(){
  var el=document.getElementById('verdict');
  if(!el) return;
  if(!V.lag && !V.lead){ el.style.display='none'; return; }
  function chip(v, tone, toneBg){
    if(!v) return '';
    return '<div style="border:1px solid __RULE__;border-left:3px solid '+tone+';border-radius:2px;padding:11px 14px;background:'+toneBg+';">'
      +'<div style="font-family:'+mono+';font-size:9.5px;letter-spacing:.1em;color:'+tone+';font-weight:700;">'+v.title+'</div>'
      +'<div style="font-size:12.5px;line-height:1.6;color:'+INK2+';margin-top:5px;">'+v.body+'</div></div>';
  }
  document.getElementById('vchips').innerHTML =
    chip(V.lag, RED, 'rgba(200,16,46,.03)') + chip(V.lead, TEAL, 'rgba(13,118,128,.03)');
})();

render();
"""

    js = (js
          .replace("__PAYLOAD__", payload_json)
          .replace("__RED__", _RED).replace("__TEAL__", _TEAL)
          .replace("__INK__", _INK).replace("__INK2__", _INK2)
          .replace("__MUT__", _MUT).replace("__DIM__", _DIM)
          .replace("__SEP__", _SEP).replace("__RULE__", _RULE)
          .replace("__GOLD__", _GOLD)
          .replace("__MONO__", json.dumps(_MONO))
          .replace("__DGRID__", _DGRID))

    shown_of = labels.get("shown_of", "")
    grp_ret = labels.get("grp_ret", "回报 RETURNS %(USD)")
    footnote = labels.get("footnote", "")
    brand = labels.get("brand", "USD 口径")
    vt = labels.get("verdict_title", "研判 · 速览")
    vm = labels.get("verdict_meta", "数据要点 · 由本页数据归纳")
    vnote = labels.get("verdict_note", "")
    src = labels.get("source_line", "")

    doc = (
        _font_head(f'#scroller{{max-height:{scroll_h}px;overflow-y:auto;}}')
        # chips 行 + 计数
        + f'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
        f'<div id="chips" style="display:flex;gap:8px;flex-wrap:wrap;"></div>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10px;'
        f'letter-spacing:.1em;color:{_DIM};"><span id="cnt"></span> {shown_of}</span></div>'
        # 表
        + f'<div style="margin-top:12px;border:1px solid {_EDGE};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;"><div style="min-width:800px;">'
        # 组头带
        f'<div style="display:grid;grid-template-columns:{_DGRID};padding:0 14px;'
        f'background:rgba(255,241,229,.9);">'
        f'<span style="grid-column:5 / span 4;font-family:{_MONO};font-size:9px;'
        f'letter-spacing:.16em;color:{_MUT};font-weight:600;padding:8px 10px 0;'
        f'border-left:1px solid {_SEP};text-align:right;">{grp_ret}</span></div>'
        # 列头 + scroller 体
        f'<div id="thead" style="position:sticky;top:0;z-index:3;display:grid;'
        f'grid-template-columns:{_DGRID};padding:0 14px;background:#fff1e5;'
        f'border-bottom:2px solid {_INK};"></div>'
        f'<div id="scroller"><div id="tbody"></div></div>'
        f'</div></div>'
        # 研判卡
        + f'<div id="verdict" style="margin-top:22px;background:rgba(255,255,255,.55);'
        f'-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);'
        f'border:1px solid {_EDGE};border-top:2px solid {_RED};border-radius:2px;'
        f'padding:18px 22px 20px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
        f'<span style="font-size:15px;font-weight:700;color:{_INK};">{vt}</span>'
        f'<span style="font-family:{_MONO};font-size:10px;letter-spacing:.1em;color:{_DIM};">{vm}</span></div>'
        f'<div id="vchips" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px;"></div>'
        f'<p style="font-size:12.5px;line-height:1.7;color:{_INK2};margin:14px 0 0;">{vnote}</p>'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;'
        f'border-top:1px solid {_RULE};padding-top:12px;margin-top:14px;">'
        f'<span style="font-size:11px;line-height:1.6;color:{_MUT};">{src}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">CMSI · JAPAN HC</span></div></div>'
        # 口径脚注
        + f'<div style="margin-top:14px;border-top:1px solid {_INK};padding-top:10px;'
        f'display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:11.5px;line-height:1.7;color:{_MUT};max-width:940px;">{footnote}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">{brand}</span></div>'
        + f'{TAG}>{js}{ETAG}'
        '</body></html>'
    )
    return doc, height
