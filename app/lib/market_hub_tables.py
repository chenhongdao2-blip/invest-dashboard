"""Market Hub · 行情中枢 — 基准涨跌榜 iframe card · lib/market_hub_tables.py
====================================================================

设计源（1:1 移植）：claude.ai/design 「行情中枢 基准涨跌榜 美化.dc.html」
（handoff5，2026-07-10 George 提供）。

三块 in ONE self-contained st.iframe：
  ① 标普 500 子行业表现 — 11 GICS SPDR ETF 表（^GSPC 钉住基准行，XLV 行高亮）
  ② 医疗健康 · 基准 — HC ETF 表（无钉住行，无行高亮）
  ③ 涨跌榜 · 1 日 — 两张玻璃卡（涨幅前10 teal / 跌幅前10 red）

所有数字由 Python 侧计算后烘入 payload；客户端 JS 只做排序 + tint 渲染。

列结构：代码 / 名称 / 1日 / 5日 / 1月 / 3月 / 年初至今 / 相对PP / 分布
  - 相对 PP = 标的 YTD − ^GSPC YTD（pp）
  - 分布    = 以列内最大超额为满刻度的中心偏离条（纯 JS 渲染）

字体：theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN）。
背景：html,body { background: transparent; color-scheme: light }
     → 让页面 cream+wash 透出。

调用方 (home.py) 传入：
  payload = {
    "sp_rows":  [[tick, name, d1, d5, m1, m3, ytd, relPP], ...],  # 11 GICS ETF
    "sp_ref":   [tick, name, d1, d5, m1, m3, ytd, None],           # ^GSPC 基准行
    "hc_rows":  [[tick, name, d1, d5, m1, m3, ytd, relPP], ...],  # HC ETF
    "gainers":  [[tick, mkt, name, price, d1, d5, m1], ...],       # top 10
    "losers":   [[tick, mkt, name, price, d1, d5, m1], ...],       # bottom 10
    "as_of":    "2026-07-08",
  }
  labels = { hub.tbl.* i18n keys }
"""
from __future__ import annotations

import json
import math

from lib import theme

# ── 设计稿 tokens ──────────────────────────────────────────────────────────
_RED  = theme.CMSI_RED    # "#c8102e"
_TEAL = theme.UP           # "#0d7680"
_INK  = theme.INK          # "#1a1a1a"
_MUT  = "#8a8580"
_DIM  = "#b8b1a8"
_EDGE = "#d4c4b0"
_SEP  = "#e2d3c1"
_ROW  = "#ebd9c8"
_PAPER = theme.PAPER       # "#fff1e5"

# 9 列 grid（设计稿原值）
_GRID = "96px minmax(150px,1fr) 76px 76px 76px 76px 86px 84px minmax(130px,1fr)"
# 涨跌榜卡 7 列 grid
_RANK_GRID = "26px 76px minmax(110px,1fr) 92px 68px 60px 60px"


def _clean(v) -> float | None:
    """NaN/inf → None。"""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def render_market_hub(payload: dict, labels: dict,
                      height: int = 1100) -> tuple[str, int]:
    """Build the Market Hub benchmark + movers card. Returns (doc, iframe_h).

    payload 结构：
      sp_rows  : [[tick, name, d1, d5, m1, m3, ytd, relPP], ...]  (11 GICS ETF)
      sp_ref   : [tick, name, d1, d5, m1, m3, ytd, None]           (^GSPC 基准行)
      hc_rows  : [[tick, name, d1, d5, m1, m3, ytd, relPP], ...]  (HC ETF)
      gainers  : [[tick, mkt, name, price, d1, d5, m1], ...]       (top 10 by 1d)
      losers   : [[tick, mkt, name, price, d1, d5, m1], ...]       (bottom 10)
      as_of    : "YYYY-MM-DD"

    labels 结构（i18n；key 缺失时 i18n.t() 返回 key 字符串，不崩溃）：
      hub.tbl.sp.title / hub.tbl.sp.sub / hub.tbl.sp.right
      hub.tbl.hc.title / hub.tbl.hc.sub / hub.tbl.hc.right
      hub.tbl.movers.title / hub.tbl.movers.sub / hub.tbl.movers.right
      hub.tbl.col.tick / hub.tbl.col.name / hub.tbl.col.d1 / hub.tbl.col.d5
      hub.tbl.col.m1 / hub.tbl.col.m3 / hub.tbl.col.ytd / hub.tbl.col.rel
      hub.tbl.col.dist
      hub.tbl.movers.gainers / hub.tbl.movers.losers
      hub.tbl.movers.col.rank / hub.tbl.movers.col.price
      hub.tbl.footnote / hub.tbl.brand
    """
    # 清洗 payload 数值
    def _clean_row(row: list) -> list:
        """row[0]=tick(str) row[1]=name(str) row[2..7]=floats (or None for ref rel)"""
        out = [str(row[0]), str(row[1])]
        for v in row[2:]:
            out.append(_clean(v))
        return out

    sp_rows = [_clean_row(r) for r in (payload.get("sp_rows") or [])]
    sp_ref  = _clean_row(payload["sp_ref"]) if payload.get("sp_ref") else None
    hc_rows = [_clean_row(r) for r in (payload.get("hc_rows") or [])]

    def _clean_mover(row: list) -> list:
        """[tick, mkt, name, price, d1, d5, m1]"""
        return [str(row[0]), str(row[1]), str(row[2]),
                _clean(row[3]), _clean(row[4]), _clean(row[5]), _clean(row[6])]

    gainers = [_clean_mover(r) for r in (payload.get("gainers") or [])]
    losers  = [_clean_mover(r) for r in (payload.get("losers") or [])]
    as_of   = str(payload.get("as_of", ""))

    js_payload = json.dumps(
        {"sp": sp_rows, "spRef": sp_ref, "hc": hc_rows,
         "gainers": gainers, "losers": losers,
         "as_of": as_of, "labels": labels},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    # iframe 高度估算：
    #   ① SP 表：section头46 + 组头带26 + 列头38 + 基准行38 + 11行×36 + 边距12 = ~556
    #   ② HC 表：section头46 + 组头带26 + 列头38 + 9行×36 + 边距12 = ~446
    #   ③ 涨跌榜：section头46 + 列头32 + max(10,10)行×34×2卡 = max(10)*34+78 ≈ 418
    #   ④ 脚注：48
    # 合计 ~1468；用固定 height 参数 + 动态调整
    sp_h  = 46 + 26 + 38 + 38 + len(sp_rows) * 36 + 12
    hc_h  = 46 + 26 + 38 + max(len(hc_rows), 1) * 36 + 12
    mv_h  = 46 + 32 + max(len(gainers), len(losers), 1) * 34 + 20
    fn_h  = 56
    iframe_h = sp_h + hc_h + mv_h + fn_h + 40  # 40 = 内部 padding

    LT   = chr(60)
    TAG  = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"

    font_face = theme.FONT_FACE_CSS.strip()
    mono_css  = "'JetBrains Mono',monospace"
    sans_css  = ("'Space Grotesk','PingFang SC','Hiragino Sans GB',"
                 "'Noto Sans SC','Microsoft YaHei',sans-serif")

    # ── 静态 section header helper（▎red tick + 16px 标题）──────────────────
    def _sec_head(title_key: str, sub_key: str, right_key: str) -> str:
        return (
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:24px;">'
            f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
            f'<span style="font-size:16px;font-weight:700;color:{_INK};">'
            f'{labels.get(title_key, title_key)}</span>'
            f'<span style="font-size:11.5px;color:{_MUT};">'
            f'{labels.get(sub_key, sub_key)}</span>'
            f'<span style="margin-left:auto;font-family:{mono_css};font-size:10px;'
            f'letter-spacing:.1em;color:{_DIM};">'
            f'{labels.get(right_key, right_key)}</span>'
            f'</div>'
        )

    # ── 表格容器 wrapper（玻璃卡）────────────────────────────────────────────
    _card_open = (
        f'<div style="margin-top:10px;border:1px solid {_EDGE};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;">'
        f'<div style="min-width:860px;">'
    )
    _card_close = '</div></div>'

    # ── 组头带（"回报 RETURNS %" / "相对标普 · YTD 超额 PP"）────────────────
    _grp_band = (
        f'<div style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
        f'background:rgba(255,241,229,.9);">'
        f'<span style="grid-column:3 / span 5;font-family:{mono_css};font-size:9px;'
        f'letter-spacing:.16em;color:{_MUT};font-weight:600;padding:8px 10px 0;'
        f'border-left:1px solid {_SEP};text-align:right;">'
        f'{labels.get("hub.tbl.grp.ret","回报 RETURNS %")}</span>'
        f'<span style="grid-column:8 / span 2;font-family:{mono_css};font-size:9px;'
        f'letter-spacing:.16em;color:{_MUT};font-weight:600;padding:8px 10px 0;'
        f'border-left:1px solid {_SEP};">'
        f'{labels.get("hub.tbl.grp.rel","相对标普 · YTD 超额 PP")}</span>'
        f'</div>'
    )

    # ── 列头行（带 data-tid 供 JS 绑定排序）────────────────────────────────
    def _col_headers(tid: str) -> str:
        """静态列头骨架；JS 在 render() 里用 innerHTML 重写加排序指示箭头。"""
        return (
            f'<div id="{tid}head" style="display:grid;grid-template-columns:{_GRID};'
            f'padding:0 14px;background:{_PAPER};border-bottom:2px solid {_INK};"></div>'
        )

    # ── SP 表静态 HTML（section头 + 组头带 + 列头占位 + ref 行占位 + body 占位）─
    sp_html = (
        _sec_head("hub.tbl.sp.title", "hub.tbl.sp.sub", "hub.tbl.sp.right")
        + _card_open
        + _grp_band
        + _col_headers("sp")
        + f'<div id="spref" style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
          f'border-bottom:1px solid {_EDGE};background:rgba(255,255,255,.35);"></div>'
        + '<div id="spbody"></div>'
        + _card_close
    )

    # ── HC 表静态 HTML ──────────────────────────────────────────────────────
    hc_html = (
        _sec_head("hub.tbl.hc.title", "hub.tbl.hc.sub", "hub.tbl.hc.right")
        + _card_open
        + _grp_band
        + _col_headers("hc")
        + '<div id="hcbody"></div>'
        + _card_close
    )

    # ── 涨跌榜 section head + 两卡骨架（JS 填充行）─────────────────────────
    movers_html = (
        _sec_head("hub.tbl.movers.title", "hub.tbl.movers.sub", "hub.tbl.movers.right")
        + f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:10px;">'
        + _rank_card_shell("gainers", labels, _RED, _TEAL, mono_css)
        + _rank_card_shell("losers",  labels, _RED, _RED,  mono_css)
        + '</div>'
    )

    # ── 脚注 ────────────────────────────────────────────────────────────────
    fn_html = (
        f'<div style="margin-top:22px;border-top:1px solid {_INK};padding-top:10px;'
        f'display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:11.5px;line-height:1.7;color:{_MUT};max-width:940px;">'
        f'{labels.get("hub.tbl.footnote","")}</span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">'
        f'{labels.get("hub.tbl.brand","CMSI · MARKET HUB")}</span>'
        f'</div>'
    )

    # ── 主 JS（排序 + tint + bar + 涨跌榜 tint）─────────────────────────────
    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', MUT='__MUT__', DIM='__DIM__';
var S = 0.16;
var GRID = '__GRID__';
var mono = "__MONO__";
var sans = "__SANS__";
// KEYS 对应表头列顺序（第9列 'rel' = 分布 bar，共享 relPP 数据）
var KEYS   = ['tick','name','d1','d5','m1','m3','ytd','rel','rel'];
var LABELS = [L['hub.tbl.col.tick']||'代码', L['hub.tbl.col.name']||'名称',
              L['hub.tbl.col.d1']||'1日', L['hub.tbl.col.d5']||'5日',
              L['hub.tbl.col.m1']||'1月', L['hub.tbl.col.m3']||'3月',
              L['hub.tbl.col.ytd']||'年初至今',
              L['hub.tbl.col.rel']||'相对PP', L['hub.tbl.col.dist']||'分布'];
// 两表独立排序状态
var ST = { sp: {key:'ytd', dir:-1}, hc: {key:'ytd', dir:-1} };

function blFor(i){ return (i===2||i===7) ? '1px solid __SEP__' : 'none'; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtR(v){ return v==null?'NM':(v>=0?'+':'-')+Math.abs(v).toFixed(1)+'%'; }
function fmtPP(v){ return v==null?'—':(v>=0?'+':'-')+Math.abs(v).toFixed(1)+'pp'; }
function fgOf(v){ return (v==null||Math.abs(v)<0.05)?MUT:(v>0?TEAL:RED); }

function tint(k, v, maxAbs){
  if (v==null||Math.abs(v)<0.05||S===0) return 'transparent';
  var a = Math.min(Math.abs(v)/maxAbs,1)*S;
  return v>0 ? 'rgba(13,118,128,'+a.toFixed(3)+')' : 'rgba(200,16,46,'+a.toFixed(3)+')';
}

// 从 array-of-arrays 转 row 对象
function toRows(data){
  return data.map(function(a){
    return {tick:a[0],name:a[1],d1:a[2],d5:a[3],m1:a[4],m3:a[5],ytd:a[6],rel:a[7]};
  });
}

// 排序（NM 恒沉底）
function sortRows(rows, key, dir){
  return rows.slice().sort(function(a,b){
    var x=a[key], y=b[key];
    if (typeof x==='string'||typeof y==='string') return String(x).localeCompare(String(y))*dir;
    var xb=(x==null||!isFinite(x)), yb=(y==null||!isFinite(y));
    if (xb&&yb) return 0; if (xb) return 1; if (yb) return -1;
    return (x-y)*dir;
  });
}

// 列头 HTML（用于 sp / hc 独立排序指示）
function mkHeaders(tid){
  var st = ST[tid];
  return LABELS.map(function(label,i){
    var k = KEYS[i];
    var on = (k===st.key && i!==8);
    return '<button data-tid="'+tid+'" data-k="'+k+'" data-i="'+i+'"'+
      ' style="appearance:none;background:transparent;border:none;margin:0;cursor:pointer;'+
      'font-family:'+mono+';font-size:10px;letter-spacing:.05em;font-weight:'+(on?700:500)+';'+
      'color:'+(on?RED:'#4a4a4a')+';padding:7px 10px 9px;'+
      'text-align:'+(i<2||i===8?'left':'right')+';white-space:nowrap;'+
      'border-left:'+blFor(i)+';">'+
      esc(label)+(on?(st.dir<0?' ▾':' ▴'):'')+
      '</button>';
  }).join('');
}

// 单数据行 HTML（muted=基准行样式）
function mkRow(r, maxAbs, hlTick, padY, muted){
  var hl = !muted && r.tick===hlTick;
  var cells = [];
  // 代码
  cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
    'font-family:'+mono+';font-size:11px;font-weight:'+(hl?700:500)+';'+
    'color:'+(muted?MUT:(hl?RED:MUT))+';padding:'+padY+' 10px;white-space:nowrap;border-left:none;">'+
    esc(r.tick)+'</span>');
  // 名称
  cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
    'font-family:'+sans+';font-size:13px;font-weight:'+(hl?700:600)+';'+
    'color:'+(muted?MUT:(hl?RED:INK))+';padding:'+padY+' 10px;white-space:nowrap;border-left:none;">'+
    esc(r.name)+(hl?' ●':'')+
    '</span>');
  // 数值列 d1/d5/m1/m3/ytd
  ['d1','d5','m1','m3','ytd'].forEach(function(k,j){
    var v=r[k];
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:'+(k==='ytd'?700:600)+';'+
      'color:'+(muted?MUT:fgOf(v))+';'+
      'background:'+(muted?'transparent':tint(k,v,maxAbs[k]))+';'+
      'padding:'+padY+' 10px;white-space:nowrap;font-variant-numeric:tabular-nums;'+
      'border-left:'+(j===0?'1px solid __SEP__':'none')+';">'+
      esc(fmtR(v))+'</span>');
  });
  // 相对PP 列
  var rv = r.rel;
  if (rv==null){
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:600;color:'+DIM+';'+
      'padding:'+padY+' 10px;border-left:1px solid __SEP__;">—</span>');
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
      'padding:'+padY+' 10px;border-left:none;">'+
      '<span style="position:relative;display:block;width:100%;height:8px;'+
      'background:rgba(26,26,26,.06);border-radius:1px;">'+
      '<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:__CTRLEDGE__;"></span>'+
      '</span></span>');
  } else {
    var w = Math.min(Math.abs(rv)/Math.max(maxAbs['rel'],0.0001),1)*47;
    var barLeft = (rv>=0?50:50-w).toFixed(1)+'%';
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:700;'+
      'color:'+(muted?MUT:fgOf(rv))+';'+
      'background:'+(muted?'transparent':tint('rel',rv,maxAbs['rel']))+';'+
      'padding:'+padY+' 10px;white-space:nowrap;font-variant-numeric:tabular-nums;'+
      'border-left:1px solid __SEP__;">'+esc(fmtPP(rv))+'</span>');
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
      'padding:'+padY+' 10px;border-left:none;">'+
      '<span style="position:relative;display:block;width:100%;height:8px;'+
      'background:rgba(26,26,26,.06);border-radius:1px;">'+
      '<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:__CTRLEDGE__;"></span>'+
      '<span style="position:absolute;top:0;bottom:0;left:'+barLeft+';width:'+w.toFixed(1)+'%;'+
      'background:'+(rv>=0?TEAL:RED)+';opacity:.8;border-radius:1px;"></span>'+
      '</span></span>');
  }
  var rowBg = hl ? 'rgba(200,16,46,.05)' : (muted?'rgba(255,255,255,.35)':'transparent');
  return '<div class="hrow" style="display:grid;grid-template-columns:'+GRID+';padding:0 14px;'+
    'border-bottom:1px solid __ROWRULE__;background:'+rowBg+';">'+cells.join('')+'</div>';
}

// 计算列内 maxAbs（含 ref 行，以便基准行刻度统一）
function calcMaxAbs(rows, refRow){
  var all = rows.slice();
  if (refRow) all.push(refRow);
  var keys=['d1','d5','m1','m3','ytd','rel'];
  var m={};
  keys.forEach(function(k){
    m[k]=Math.max.apply(null, all.map(function(r){ return Math.abs(r[k]||0); }).concat([0.0001]));
  });
  return m;
}

// renderTable：渲染一张表（sp 或 hc）
function renderTable(tid, data, refData, hlTick){
  var st = ST[tid];
  var rows = sortRows(toRows(data), st.key, st.dir);
  var refRow = refData ? toRows([refData])[0] : null;
  var maxAbs = calcMaxAbs(rows, refRow);
  var padY = '8px';

  // 列头
  document.getElementById(tid+'head').innerHTML = mkHeaders(tid);

  // ref 行（钉住基准行，仅 sp）
  var refEl = document.getElementById(tid+'ref');
  if (refEl){
    if (refRow){
      refEl.innerHTML = mkRow(refRow, maxAbs, null, padY, true);
    } else {
      refEl.innerHTML = '';
    }
  }

  // 数据行
  document.getElementById(tid+'body').innerHTML = rows.map(function(r){
    return mkRow(r, maxAbs, hlTick, padY, false);
  }).join('');
}

// 涨跌榜 tint（两卡独立 maxAbs）
function renderRank(cardId, data, sign){
  var maxD1 = Math.max.apply(null, data.map(function(a){ return Math.abs(a[4]||0); }).concat([0.0001]));
  var cur = {HK:'HK$', JP:'¥', CN:'¥', KR:'₩', US:'$'};
  var padY = '7px';
  var html = data.map(function(a,i){
    var alpha = Math.min(Math.abs(a[4]||0)/maxD1,1)*S;
    var d1bg = sign>0 ? 'rgba(13,118,128,'+alpha.toFixed(3)+')' : 'rgba(200,16,46,'+alpha.toFixed(3)+')';
    var price = a[3]==null ? '—' : (cur[a[1]]||'$')+(+a[3]).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
    return '<div class="hrow" style="display:grid;grid-template-columns:__RANKGRID__;padding:0 12px;border-bottom:1px solid __ROWRULE__;">'+
      '<span style="display:flex;align-items:center;font-family:'+mono+';font-size:10.5px;color:'+DIM+';padding:'+padY+' 6px;">'+(i+1).toString().padStart(2,'0')+'</span>'+
      '<span style="display:flex;align-items:center;font-family:'+mono+';font-size:10.5px;color:'+MUT+';padding:'+padY+' 6px;white-space:nowrap;">'+esc(a[0]+(a[1]!=='US'?' '+a[1]:''))+'</span>'+
      '<span style="align-self:center;font-size:12.5px;font-weight:600;color:'+INK+';padding:'+padY+' 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;display:block;">'+esc(a[2])+'</span>'+
      '<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;color:#4a4a4a;padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;">'+esc(price)+'</span>'+
      '<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:12px;font-weight:700;color:'+fgOf(a[4])+';background:'+d1bg+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;border-left:1px solid __SEP__;">'+esc(fmtR(a[4]))+'</span>'+
      '<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;font-weight:500;color:'+fgOf(a[5])+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;">'+esc(fmtR(a[5]))+'</span>'+
      '<span style="display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;font-weight:500;color:'+fgOf(a[6])+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;">'+esc(fmtR(a[6]))+'</span>'+
      '</div>';
  }).join('');
  var el = document.getElementById(cardId);
  if (el) el.innerHTML = html;
}

function render(){
  renderTable('sp', P.sp, P.spRef, 'XLV');
  renderTable('hc', P.hc, null, null);
  renderRank('gainers_body', P.gainers, 1);
  renderRank('losers_body',  P.losers,  -1);
}

// 事件委托：列头排序（两表独立）
document.addEventListener('click', function(e){
  var btn = e.target.closest('button[data-tid][data-k]');
  if (!btn) return;
  var tid = btn.getAttribute('data-tid');
  var k   = btn.getAttribute('data-k');
  var i   = parseInt(btn.getAttribute('data-i'));
  if (i===8) return;  // 分布 bar 不可排序
  if (ST[tid].key===k) ST[tid].dir = -ST[tid].dir;
  else { ST[tid].key=k; ST[tid].dir=(k==='tick'||k==='name')?1:-1; }
  render();
});

render();
"""
    # 字符串替换（同 heat_table 模式）
    js = (js
          .replace("__PAYLOAD__", js_payload)
          .replace("__RED__",     _RED)
          .replace("__TEAL__",    _TEAL)
          .replace("__INK__",     _INK)
          .replace("__MUT__",     _MUT)
          .replace("__DIM__",     _DIM)
          .replace("__SEP__",     _SEP)
          .replace("__ROWRULE__", _ROW)
          .replace("__CTRLEDGE__", "#b8ab99")
          .replace("__GRID__",    _GRID)
          .replace("__RANKGRID__", _RANK_GRID)
          .replace("__MONO__",    mono_css)
          .replace("__SANS__",    sans_css))

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;'
        f'font-family:{sans_css};font-feature-settings:"tnum","ss01";}}'
        '.hrow{transition:background .12s;}'
        '.hrow:hover{background:rgba(255,255,255,.8)!important;}'
        'button:hover{opacity:.85;}'
        f'</style></head><body style="padding:0 0 16px;">'
        + sp_html
        + hc_html
        + movers_html
        + fn_html
        + f'{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, iframe_h


def render_bench_block(rows: list, labels: dict) -> tuple[str, int]:
    """Render a single standalone benchmark table block (glass card, sortable).

    Reuses the exact same JS/table builder as the hub's HC block.
    No movers, no ref row, no SP block — one bench table + footnote.

    rows    : [[tick, name, d1, d5, m1, m3, ytd, relPP], ...]
              (relPP = ytd − ^GSPC ytd; pass None if unavailable)
    labels  : {
        "bench.title"  : section title (e.g. "基准 / AI · BENCHMARKS")
        "bench.sub"    : subtitle muted text
        "bench.right"  : mono right tag (e.g. "AI BENCHMARK")
        "hub.tbl.grp.ret"  : group band label for returns columns
        "hub.tbl.grp.rel"  : group band label for relative PP columns
        "hub.tbl.col.tick" / .name / .d1 / .d5 / .m1 / .m3 / .ytd / .rel / .dist
        "hub.tbl.footnote" : footnote text
        "hub.tbl.brand"    : right-side brand tag
      }
    Returns (doc_html_str, iframe_h).
    """
    def _clean_row(row: list) -> list:
        out = [str(row[0]), str(row[1])]
        for v in row[2:]:
            out.append(_clean(v))
        return out

    bench_rows = [_clean_row(r) for r in (rows or [])]
    as_of = str(labels.get("bench.as_of", ""))

    js_payload = json.dumps(
        {"rows": bench_rows, "labels": labels, "as_of": as_of},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    # Height: section head 46 + group band 26 + col header 38 + rows×36 + footnote 56 + padding 28
    n = max(len(bench_rows), 1)
    iframe_h = 46 + 26 + 38 + n * 36 + 56 + 28

    LT   = chr(60)
    TAG  = LT + "scr" + "ipt"
    ETAG = LT + "/scr" + "ipt>"

    font_face = theme.FONT_FACE_CSS.strip()
    mono_css  = "'JetBrains Mono',monospace"
    sans_css  = ("'Space Grotesk','PingFang SC','Hiragino Sans GB',"
                 "'Noto Sans SC','Microsoft YaHei',sans-serif")

    def _sec_head_b(title_key: str, sub_key: str, right_key: str) -> str:
        return (
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:4px;">'
            f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
            f'<span style="font-size:16px;font-weight:700;color:{_INK};">'
            f'{labels.get(title_key, title_key)}</span>'
            f'<span style="font-size:11.5px;color:{_MUT};">'
            f'{labels.get(sub_key, sub_key)}</span>'
            f'<span style="margin-left:auto;font-family:{mono_css};font-size:10px;'
            f'letter-spacing:.1em;color:{_DIM};">'
            f'{labels.get(right_key, right_key)}</span>'
            f'</div>'
        )

    _grp_band_b = (
        f'<div style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
        f'background:rgba(255,241,229,.9);">'
        f'<span style="grid-column:3 / span 5;font-family:{mono_css};font-size:9px;'
        f'letter-spacing:.16em;color:{_MUT};font-weight:600;padding:8px 10px 0;'
        f'border-left:1px solid {_SEP};text-align:right;">'
        f'{labels.get("hub.tbl.grp.ret", "RETURNS %")}</span>'
        f'<span style="grid-column:8 / span 2;font-family:{mono_css};font-size:9px;'
        f'letter-spacing:.16em;color:{_MUT};font-weight:600;padding:8px 10px 0;'
        f'border-left:1px solid {_SEP};">'
        f'{labels.get("hub.tbl.grp.rel", "vs S&P 500 · YTD excess PP")}</span>'
        f'</div>'
    )

    _card_open_b = (
        f'<div style="margin-top:10px;border:1px solid {_EDGE};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);'
        f'backdrop-filter:blur(8px);overflow-x:auto;">'
        f'<div style="min-width:860px;">'
    )
    _card_close_b = '</div></div>'

    bench_html = (
        _sec_head_b("bench.title", "bench.sub", "bench.right")
        + _card_open_b
        + _grp_band_b
        + f'<div id="benchhead" style="display:grid;grid-template-columns:{_GRID};'
          f'padding:0 14px;background:{_PAPER};border-bottom:2px solid {_INK};"></div>'
        + '<div id="benchbody"></div>'
        + _card_close_b
    )

    fn_html_b = (
        f'<div style="margin-top:16px;border-top:1px solid {_INK};padding-top:10px;'
        f'display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:11.5px;line-height:1.7;color:{_MUT};max-width:940px;">'
        f'{labels.get("hub.tbl.footnote", "")}</span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10.5px;'
        f'letter-spacing:.08em;color:{_DIM};">'
        f'{labels.get("hub.tbl.brand", "CMSI · MARKET HUB")}</span>'
        f'</div>'
    )

    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', MUT='__MUT__', DIM='__DIM__';
var S = 0.16;
var GRID = '__GRID__';
var mono = "__MONO__";
var sans = "__SANS__";
var KEYS   = ['tick','name','d1','d5','m1','m3','ytd','rel','rel'];
var LABELS = [L['hub.tbl.col.tick']||'代码', L['hub.tbl.col.name']||'名称',
              L['hub.tbl.col.d1']||'1日', L['hub.tbl.col.d5']||'5日',
              L['hub.tbl.col.m1']||'1月', L['hub.tbl.col.m3']||'3月',
              L['hub.tbl.col.ytd']||'年初至今',
              L['hub.tbl.col.rel']||'相对PP', L['hub.tbl.col.dist']||'分布'];
var ST_BENCH = {key:'ytd', dir:-1};

function blFor(i){ return (i===2||i===7) ? '1px solid __SEP__' : 'none'; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function fmtR(v){ return v==null?'NM':(v>=0?'+':'-')+Math.abs(v).toFixed(1)+'%'; }
function fmtPP(v){ return v==null?'—':(v>=0?'+':'-')+Math.abs(v).toFixed(1)+'pp'; }
function fgOf(v){ return (v==null||Math.abs(v)<0.05)?MUT:(v>0?TEAL:RED); }

function tint(k, v, maxAbs){
  if (v==null||Math.abs(v)<0.05||S===0) return 'transparent';
  var a = Math.min(Math.abs(v)/maxAbs,1)*S;
  return v>0 ? 'rgba(13,118,128,'+a.toFixed(3)+')' : 'rgba(200,16,46,'+a.toFixed(3)+')';
}

function toRows(data){
  return data.map(function(a){
    return {tick:a[0],name:a[1],d1:a[2],d5:a[3],m1:a[4],m3:a[5],ytd:a[6],rel:a[7]};
  });
}

function sortRows(rows, key, dir){
  return rows.slice().sort(function(a,b){
    var x=a[key], y=b[key];
    if (typeof x==='string'||typeof y==='string') return String(x).localeCompare(String(y))*dir;
    var xb=(x==null||!isFinite(x)), yb=(y==null||!isFinite(y));
    if (xb&&yb) return 0; if (xb) return 1; if (yb) return -1;
    return (x-y)*dir;
  });
}

function calcMaxAbs(rows){
  var keys=['d1','d5','m1','m3','ytd','rel'];
  var m={};
  keys.forEach(function(k){
    m[k]=Math.max.apply(null, rows.map(function(r){ return Math.abs(r[k]||0); }).concat([0.0001]));
  });
  return m;
}

function mkHeaders(){
  var st = ST_BENCH;
  return LABELS.map(function(label,i){
    var k = KEYS[i];
    var on = (k===st.key && i!==8);
    return '<button data-k="'+k+'" data-i="'+i+'"'+
      ' style="appearance:none;background:transparent;border:none;margin:0;cursor:pointer;'+
      'font-family:'+mono+';font-size:10px;letter-spacing:.05em;font-weight:'+(on?700:500)+';'+
      'color:'+(on?RED:'#4a4a4a')+';padding:7px 10px 9px;'+
      'text-align:'+(i<2||i===8?'left':'right')+';white-space:nowrap;'+
      'border-left:'+blFor(i)+';">'+
      esc(label)+(on?(st.dir<0?' ▾':' ▴'):'')+
      '</button>';
  }).join('');
}

function mkRow(r, maxAbs){
  var cells = [];
  cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
    'font-family:'+mono+';font-size:11px;font-weight:500;'+
    'color:'+MUT+';padding:8px 10px;white-space:nowrap;border-left:none;">'+
    esc(r.tick)+'</span>');
  cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
    'font-family:'+sans+';font-size:13px;font-weight:600;'+
    'color:'+INK+';padding:8px 10px;white-space:nowrap;border-left:none;">'+
    esc(r.name)+'</span>');
  ['d1','d5','m1','m3','ytd'].forEach(function(k,j){
    var v=r[k];
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:'+(k==='ytd'?700:600)+';'+
      'color:'+fgOf(v)+';'+
      'background:'+tint(k,v,maxAbs[k])+';'+
      'padding:8px 10px;white-space:nowrap;font-variant-numeric:tabular-nums;'+
      'border-left:'+(j===0?'1px solid __SEP__':'none')+';">'+
      esc(fmtR(v))+'</span>');
  });
  var rv = r.rel;
  if (rv==null){
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:600;color:'+DIM+';'+
      'padding:8px 10px;border-left:1px solid __SEP__;">—</span>');
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
      'padding:8px 10px;border-left:none;">'+
      '<span style="position:relative;display:block;width:100%;height:8px;'+
      'background:rgba(26,26,26,.06);border-radius:1px;">'+
      '<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:#b8ab99;"></span>'+
      '</span></span>');
  } else {
    var w = Math.min(Math.abs(rv)/Math.max(maxAbs['rel'],0.0001),1)*47;
    var barLeft = (rv>=0?50:50-w).toFixed(1)+'%';
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-end;'+
      'font-family:'+mono+';font-size:12px;font-weight:700;'+
      'color:'+fgOf(rv)+';'+
      'background:'+tint('rel',rv,maxAbs['rel'])+';'+
      'padding:8px 10px;white-space:nowrap;font-variant-numeric:tabular-nums;'+
      'border-left:1px solid __SEP__;">'+esc(fmtPP(rv))+'</span>');
    cells.push('<span style="display:flex;align-items:center;justify-content:flex-start;'+
      'padding:8px 10px;border-left:none;">'+
      '<span style="position:relative;display:block;width:100%;height:8px;'+
      'background:rgba(26,26,26,.06);border-radius:1px;">'+
      '<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:#b8ab99;"></span>'+
      '<span style="position:absolute;top:0;bottom:0;left:'+barLeft+';width:'+w.toFixed(1)+'%;'+
      'background:'+(rv>=0?TEAL:RED)+';opacity:.8;border-radius:1px;"></span>'+
      '</span></span>');
  }
  return '<div class="hrow" style="display:grid;grid-template-columns:'+GRID+';padding:0 14px;'+
    'border-bottom:1px solid __ROWRULE__;background:transparent;">'+cells.join('')+'</div>';
}

function render(){
  var rows = sortRows(toRows(P.rows), ST_BENCH.key, ST_BENCH.dir);
  var maxAbs = calcMaxAbs(rows);
  document.getElementById('benchhead').innerHTML = mkHeaders();
  document.getElementById('benchbody').innerHTML = rows.map(function(r){ return mkRow(r, maxAbs); }).join('');
}

document.addEventListener('click', function(e){
  var btn = e.target.closest('button[data-k]');
  if (!btn) return;
  var k = btn.getAttribute('data-k');
  var i = parseInt(btn.getAttribute('data-i'));
  if (i===8) return;
  if (ST_BENCH.key===k) ST_BENCH.dir = -ST_BENCH.dir;
  else { ST_BENCH.key=k; ST_BENCH.dir=(k==='tick'||k==='name')?1:-1; }
  render();
});

render();
"""
    js = (js
          .replace("__PAYLOAD__", js_payload)
          .replace("__RED__",     _RED)
          .replace("__TEAL__",    _TEAL)
          .replace("__INK__",     _INK)
          .replace("__MUT__",     _MUT)
          .replace("__DIM__",     _DIM)
          .replace("__SEP__",     _SEP)
          .replace("__ROWRULE__", _ROW)
          .replace("__GRID__",    _GRID)
          .replace("__MONO__",    mono_css)
          .replace("__SANS__",    sans_css))

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;'
        f'font-family:{sans_css};font-feature-settings:"tnum","ss01";}}'
        '.hrow{transition:background .12s;}'
        '.hrow:hover{background:rgba(255,255,255,.8)!important;}'
        'button:hover{opacity:.85;}'
        f'</style></head><body style="padding:0 0 16px;">'
        + bench_html
        + fn_html_b
        + f'{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, iframe_h


def _rank_card_shell(card_id: str, labels: dict, accent_color: str,
                     title_accent: str, mono_css: str) -> str:
    """涨跌榜 glass 卡 HTML（列头静态，行体 JS 填充）。"""
    if card_id == "gainers":
        title = labels.get("hub.tbl.movers.gainers", "涨幅前 10")
        sub   = "GAINERS · 1D"
        accent = _TEAL
    else:
        title = labels.get("hub.tbl.movers.losers", "跌幅前 10")
        sub   = "LOSERS · 1D"
        accent = _RED

    rank_lbl  = labels.get("hub.tbl.movers.col.rank", "#")
    price_lbl = labels.get("hub.tbl.movers.col.price", "最新价")
    tick_lbl  = labels.get("hub.tbl.col.tick", "代码")
    name_lbl  = labels.get("hub.tbl.col.name", "名称")
    d1_lbl    = labels.get("hub.tbl.col.d1",  "1日")
    d5_lbl    = labels.get("hub.tbl.col.d5",  "5日")
    m1_lbl    = labels.get("hub.tbl.col.m1",  "1月")

    mono = mono_css
    _RANK_GRID_CSS = _RANK_GRID

    return (
        f'<div style="border:1px solid {_EDGE};border-top:2px solid {accent};border-radius:2px;'
        f'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);overflow-x:auto;">'
        f'<div style="display:flex;align-items:baseline;gap:10px;padding:11px 16px 9px;">'
        f'<span style="font-size:14px;font-weight:700;color:{accent};">{title}</span>'
        f'<span style="margin-left:auto;font-family:{mono};font-size:10px;letter-spacing:.08em;color:{_DIM};">{sub}</span>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:{_RANK_GRID_CSS};padding:0 12px;border-bottom:2px solid {_INK};">'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;">{rank_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;">{tick_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;">{name_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;text-align:right;">{price_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;text-align:right;border-left:1px solid {_SEP};">{d1_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;text-align:right;">{d5_lbl}</span>'
        f'<span style="font-family:{mono};font-size:10px;color:#4a4a4a;padding:4px 6px 8px;text-align:right;">{m1_lbl}</span>'
        f'</div>'
        f'<div id="{card_id}_body"></div>'
        f'</div>'
    )


def render_movers_block(gainers: list, losers: list, labels: dict,
                        *, title_keys: tuple = ("hub.tbl.movers.title",
                                                "hub.tbl.movers.sub",
                                                "hub.tbl.movers.right")) -> tuple[str, int]:
    """独立涨跌榜块（双 glass 卡）——非 healthcare hub 场景（如 AI expander）复用。

    gainers/losers: [[tick, mkt('HK'/'JP'/'CN'/'US'), name, price, d1, d5, m1], ...]
    labels: 与 render_market_hub 同一套 hub.tbl.movers.* / hub.tbl.col.* keys +
            title_keys 三元组指向 section 头文案。
    """
    def _cm(row: list) -> list:
        # [tick, mkt, name, price, d1, d5, m1] — 数值位过 _clean（NaN→None→NM）
        return [str(row[0]), str(row[1]), str(row[2])] + [_clean(v) for v in row[3:7]]

    g = [_cm(r) for r in (gainers or [])]
    l = [_cm(r) for r in (losers or [])]

    payload = json.dumps({"g": g, "l": l}, ensure_ascii=False,
                         separators=(",", ":")).replace("</", "<\\/")

    n = max(len(g), len(l), 1)
    iframe_h = 40 + 46 + 32 + n * 34 + 24

    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    font_face = theme.FONT_FACE_CSS.strip()
    mono_css = "'JetBrains Mono',monospace"
    sans_css = ("'Space Grotesk','PingFang SC','Hiragino Sans GB',"
                "'Noto Sans SC','Microsoft YaHei',sans-serif")

    sec_head = (
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
        f'<span style="font-size:16px;font-weight:700;color:{_INK};">{labels.get(title_keys[0], "涨跌榜 · 1 日")}</span>'
        f'<span style="font-size:11.5px;color:{_MUT};">{labels.get(title_keys[1], "")}</span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10px;'
        f'letter-spacing:.1em;color:{_DIM};">{labels.get(title_keys[2], "TOP MOVERS")}</span>'
        f'</div>'
    )

    js = (
        "var P=" + payload + ";"
        "var S=0.16,MUT='" + _MUT + "',DIM='" + _DIM + "',INK='" + _INK + "',"
        "TEAL='" + _TEAL + "',RED='" + _RED + "';"
        "var mono=\"'JetBrains Mono',monospace\";"
        "function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}"
        "function fmtR(v){if(v==null||!isFinite(v))return 'NM';return (v>=0?'+':'-')+Math.abs(v).toFixed(1)+'%';}"
        "function fgOf(v){if(v==null||!isFinite(v))return DIM;return Math.abs(v)<0.05?MUT:(v>0?TEAL:RED);}"
        "function renderRank(cardId,data,sign){"
        "var maxD1=Math.max.apply(null,data.map(function(a){return Math.abs(a[4]||0);}).concat([0.0001]));"
        "var cur={HK:'HK$',JP:'\\u00a5',CN:'\\u00a5',KR:'\\u20a9',US:'$'};var padY='7px';"
        "var html=data.map(function(a,i){"
        "var alpha=Math.min(Math.abs(a[4]||0)/maxD1,1)*S;"
        "var d1bg=sign>0?'rgba(13,118,128,'+alpha.toFixed(3)+')':'rgba(200,16,46,'+alpha.toFixed(3)+')';"
        "var price=a[3]==null?'\\u2014':(cur[a[1]]||'$')+(+a[3]).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});"
        "return '<div class=\"hrow\" style=\"display:grid;grid-template-columns:" + _RANK_GRID + ";padding:0 12px;border-bottom:1px solid " + _ROW + ";\">'+"
        "'<span style=\"display:flex;align-items:center;font-family:'+mono+';font-size:10.5px;color:'+DIM+';padding:'+padY+' 6px;\">'+(i+1).toString().padStart(2,'0')+'</span>'+"
        "'<span style=\"display:flex;align-items:center;font-family:'+mono+';font-size:10.5px;color:'+MUT+';padding:'+padY+' 6px;white-space:nowrap;\">'+esc(a[0]+(a[1]!=='US'?' '+a[1]:''))+'</span>'+"
        "'<span style=\"align-self:center;font-size:12.5px;font-weight:600;color:'+INK+';padding:'+padY+' 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;display:block;\">'+esc(a[2])+'</span>'+"
        "'<span style=\"display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;color:#4a4a4a;padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;\">'+esc(price)+'</span>'+"
        "'<span style=\"display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:12px;font-weight:700;color:'+fgOf(a[4])+';background:'+d1bg+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;border-left:1px solid " + _SEP + ";\">'+esc(fmtR(a[4]))+'</span>'+"
        "'<span style=\"display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;font-weight:500;color:'+fgOf(a[5])+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;\">'+esc(fmtR(a[5]))+'</span>'+"
        "'<span style=\"display:flex;align-items:center;justify-content:flex-end;font-family:'+mono+';font-size:11px;font-weight:500;color:'+fgOf(a[6])+';padding:'+padY+' 6px;white-space:nowrap;font-variant-numeric:tabular-nums;\">'+esc(fmtR(a[6]))+'</span>'+"
        "'</div>';}).join('');"
        "var el=document.getElementById(cardId);if(el)el.innerHTML=html;}"
        "renderRank('gainers_body',P.g,1);renderRank('losers_body',P.l,-1);"
    )

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{sans_css};font-feature-settings:'tnum','ss01';}}"
        ".hrow{transition:background .12s;}"
        ".hrow:hover{background:rgba(255,255,255,.8);}"
        "</style></head><body>"
        + sec_head +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:10px;">'
        + _rank_card_shell("gainers", labels, _RED, _TEAL, mono_css)
        + _rank_card_shell("losers", labels, _RED, _RED, mono_css)
        + '</div>'
        f'{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, iframe_h
