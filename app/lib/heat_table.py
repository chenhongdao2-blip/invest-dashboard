"""板块热力图 · 横截面热力表 — lib/heat_table.py
================================================================

设计源（1:1 移植）：claude.ai/design 「板块热力图 美化.dc.html」
（handoff zip (3) → three-js/project/，2026-07-10 George 提供）。

整个 section = 一张自包含 st.iframe：
- 板块 tabs（名称 + 家数，红字 + 2.5px 红下划线 = active）—— 客户端切换，无 rerun
- 地区 chips（美股/H股/A股/日股/韩股…，行带 region 时出现，多选过滤）—— 客户端
  切换，无 rerun；tabs / 汇总 / 中位数行 / 染色统计全部随过滤联动
- 摘要条：覆盖 N 家 · 总市值 · YTD 中位 · YTD 广度条（teal 涨 / 红 跌）
- 白玻璃表（rgba(255,255,255,.45)+blur）：
  · 组头带（回报 RETURNS % / 估值 VALUATION × / 现金流）+ 可点击排序列头（sticky）
  · 「板块中位数」基准行
  · 回报列 tint = 列内幅度（青涨/红跌，|v|<0.05 透明）
  · 估值列 tint = 列内分位（青=便宜/红=贵，NM 不参与）；FCF 收益分位反向（高=青）
  · 市值列 √ 刻度红条；NM 淡字
- 口径脚注

数据横截面由页面侧从快照库烘入（demo 只有制药 → 落地读全量）。

⚠ 既有约束：字体 theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN）；iframe body
transparent 让页面 cream+wash 透出。纯 HTML/JS，无 echarts 依赖。
"""
from __future__ import annotations

import json
import math

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

# 12 列 grid。设计稿原值总宽 ~1130px，在侧栏展开的 1240 内容区会把 FCF 列推出
# 视口（要横滚才看到）——各列收窄一档，总宽 ~1050，12 列一屏放下；比例不变。
_GRID = "72px minmax(138px,1fr) 122px 76px 72px 72px 72px 76px 76px 88px 72px 80px"

# 板块汇总 8 列 grid（zip4 设计原样）
_SGRID = "minmax(140px,1.1fr) 56px 84px 84px 84px 92px minmax(150px,1fr) 76px"
_CTRL_EDGE = "#b8ab99"

_NUM_KEYS = ["mcap", "ytd", "m1", "d5", "d1", "peS", "peF", "evE", "evS", "fcf"]


def _clean(v) -> float | None:
    """NaN/inf → None（JS 侧统一走 NM 分支）。"""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def render_heat_table(sectors: list[dict], *, labels: dict,
                      height: int = 920) -> tuple[str, int]:
    """Build the sector-heatmap cross-section card. Returns (doc, iframe_h).

    sectors = [{"id": str, "name": str（本地化 tab 名）, "bench": "XLV"（基准 chip，可缺）,
      "rows": [
        {"t": "LLY", "n": "礼来制药", "mcap": 1084.2（$B）,
         "r": "US"（universe_member.region，可缺——缺则不带地区 chips）,
         "ytd"/"m1"/"d5"/"d1": %（已是百分数）,
         "peS"/"peF"/"evE"/"evS": 倍数, "fcf": %（已 ×100）},
    ]}]
    labels = i18n 文案 dict：cover/mcap_total/ytd_med/breadth/up/dn/median/
        grp_ret/grp_val/grp_cf/footnote/footnote_dyn（{max} 占位）/brand +
        sum_title/sum_sub/sum_right/heat_title/heat_sub +
        sum_cols{sector,n,d1,d5,m1,ytd,dist,bench} + cols{t,n,mcap,...,fcf}。
        可选 regions = {"US": "美股", ...} —— 按此顺序渲染地区 chips；缺省 = 全选。

    地区过滤（2026-07-20）：行带 r 字段时，tabs 右侧渲染地区 chips（多选）。
    过滤纯客户端：tabs 家数 / 板块汇总 / 中位数行 / 列染色统计 / 摘要条全部随
    过滤后的行集重算；chips 全灭 = 不过滤（全集），全排除状态不会出现。

    zip(4) 设计新增「板块汇总」：等权平均收益表在热力表上方，行 = 板块（点击行
    切换下方热力表 tab，客户端联动）；YTD 分布 = 以列内最大幅度为满刻度的中心
    偏离条；tint 与热力表同一 S。

    排序语义：点击列头切换；数值列默认降序，再点反转；NM 恒沉底
    （设计稿的 -Infinity*sortDir 在降序时会把 NM 顶到最上——按意图修正）。
    """
    secs_js = []
    for sec in sectors:
        rows = []
        for r in sec["rows"]:
            row = {"t": str(r["t"]), "n": str(r["n"]), "r": str(r.get("r") or "")}
            for k in _NUM_KEYS:
                v = _clean(r.get(k))
                # 卖方惯例：负/零估值倍数（亏损期 P/E、负 EBITDA 的 EV/EBITDA）= NM，
                # 不得进入「便宜」分位染色（-1408x ≠ cheapest）。FCF 收益可合法为负，保留。
                if k in ("peS", "peF", "evE", "evS") and v is not None and v <= 0:
                    v = None
                row[k] = v
            rows.append(row)
        secs_js.append({"id": str(sec["id"]), "name": str(sec["name"]),
                        "bench": str(sec.get("bench") or "—"), "rows": rows})

    # 地区 chips：labels.regions 提供 {code: label}（顺序即渲染顺序），且数据里
    # 至少一行带 r 才启用。chip 默认全选（不过滤）；全部点灭 = 回到全集。
    regions_cfg = labels.get("regions") or {}
    has_regions = bool(regions_cfg) and any(row["r"] for s in secs_js for row in s["rows"])
    payload_regions = (
        [{"code": str(code), "label": str(label), "on": True}
         for code, label in regions_cfg.items()]
        if has_regions else []
    )

    payload = json.dumps(
        {"sectors": secs_js, "labels": labels, "regions": payload_regions},
        ensure_ascii=False, separators=(",", ":"),
    ).replace("</", "<\\/")

    table_max_h = max(320, height - 210)   # tabs+摘要+脚注 chrome 之外给表体
    # 板块汇总块高：section 头 46 + 列头 34 + 行 38×n + 容器边距 12 + 热力图小节头 44
    summary_h = 136 + 38 * len(secs_js)
    regions_h = 38 if has_regions else 0   # 地区 chips 一行（含与 tabs 的间距）
    iframe_h = height + summary_h + regions_h

    js = r"""
var P = __PAYLOAD__;
var L = P.labels;
var RED='__RED__', TEAL='__TEAL__', INK='__INK__', MUT='__MUT__', DIM='__DIM__';
var S = 0.16;                       // tintStrength（设计稿默认）
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
  {k:'peS', label:L.cols.peS, align:'right', type:'val',  grp:2},
  {k:'peF', label:L.cols.peF, align:'right', type:'val',  grp:2},
  {k:'evE', label:L.cols.evE, align:'right', type:'val',  grp:2},
  {k:'evS', label:L.cols.evS, align:'right', type:'val',  grp:2},
  {k:'fcf', label:L.cols.fcf, align:'right', type:'fcf',  grp:3}
];
var st_ = { tab: P.sectors.length ? P.sectors[0].id : null, sortKey: 'mcap', sortDir: -1 };

// ── 地区过滤（chips 多选；全部点灭 = 不过滤 = 全集）──
var REG = P.regions || [];
function filterActive(){
  // null = 不过滤：chips 全亮（初始）或全灭（全灭=全集，避免用户把自己锁进空集）。
  // 全亮时不过滤还有防御意义：数据里出现 chips 列表之外的新 region 不会被误杀。
  var on = REG.filter(function(g){ return g.on; }).map(function(g){ return g.code; });
  if (!on.length || on.length === REG.length) return null;
  return on;
}
function rowsFiltered(sec){
  var act = filterActive();
  if (act == null) return sec.rows;
  return sec.rows.filter(function(r){ return r.r && act.indexOf(r.r) >= 0; });
}
function renderRegionChips(){
  if (!REG.length) return;
  document.getElementById('rchips').innerHTML = REG.map(function(g){
    return '<button data-reg="'+g.code+'" class="rchip'+(g.on?' on':'')+'" ' +
      'style="font-family:'+mono+';">'+esc(g.label)+'</button>';
  }).join('');
}

function median(vs){
  var s = vs.filter(function(v){ return v != null && isFinite(v); }).slice().sort(function(a,b){ return a-b; });
  if (!s.length) return null;
  var m = Math.floor(s.length/2);
  return s.length % 2 ? s[m] : (s[m-1]+s[m])/2;
}
function fmt(type, v){
  if (v == null || !isFinite(v)) return 'NM';
  if (type === 'ret' || type === 'fcf') return (v >= 0 ? '+' : '-') + Math.abs(v).toFixed(1) + '%';
  if (type === 'mcap') return '$' + v.toLocaleString('en-US',{minimumFractionDigits:1,maximumFractionDigits:1}) + 'B';
  if (type === 'val') return v.toFixed(1) + 'x';
  return String(v);
}
function blFor(i){ return (i===3||i===7||i===11) ? '1px solid __SEP__' : 'none'; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// 板块汇总：等权平均（忽略 null，随地区过滤重算），tint 以列内最大幅度为分母，YTD 分布条同刻度
var SUMS = [], S_MAX = [0,0,0,0], YTD_MAX = 1;
function computeSums(){
  SUMS = P.sectors.map(function(s){
    var rows = rowsFiltered(s);
    function avg(k){
      var vs = rows.map(function(r){ return r[k]; }).filter(function(v){ return v != null && isFinite(v); });
      return vs.length ? vs.reduce(function(a,b){ return a+b; }, 0)/vs.length : null;
    }
    return { id:s.id, name:s.name, n:rows.length, bench:s.bench,
             vals:[avg('d1'), avg('d5'), avg('m1'), avg('ytd')] };
  });
  S_MAX = [0,0,0,0];
  SUMS.forEach(function(r){ for (var i=0;i<4;i++){ var v=r.vals[i]; if (v!=null) S_MAX[i]=Math.max(S_MAX[i], Math.abs(v)); } });
  YTD_MAX = S_MAX[3] || 1;
}

function renderSummary(){
  var html = SUMS.map(function(r){
    var active = r.id === st_.tab;
    var cells = r.vals.map(function(v, i){
      var txt = (v == null) ? 'NM' : fmt('ret', v);
      var fg = (v == null) ? DIM : (Math.abs(v) < 0.05 ? MUT : (v > 0 ? TEAL : RED));
      var bg = 'transparent';
      if (v != null && Math.abs(v) >= 0.05 && S_MAX[i] > 0){
        var a = Math.min(Math.abs(v)/S_MAX[i], 1) * 0.16;
        bg = v > 0 ? 'rgba(13,118,128,'+a.toFixed(3)+')' : 'rgba(200,16,46,'+a.toFixed(3)+')';
      }
      return '<span style="display:flex;align-items:center;justify-content:flex-end;padding:9px 10px;' +
        'font-family:'+mono+';font-size:12px;font-weight:'+(i===3?700:600)+';font-variant-numeric:tabular-nums;' +
        'color:'+fg+';background:'+bg+';'+(i===0?'border-left:1px solid __SEP__;':'')+'">'+txt+'</span>';
    }).join('');
    var v = r.vals[3], w = (v == null) ? 0 : Math.min(Math.abs(v)/YTD_MAX, 1)*47;
    var barLeft = (v != null && v >= 0) ? 50 : 50 - w;
    var bar = '<span style="display:flex;align-items:center;padding:9px 10px;border-left:1px solid __SEP__;">' +
      '<span style="position:relative;display:block;width:100%;height:8px;background:rgba(26,26,26,.06);border-radius:1px;">' +
      '<span style="position:absolute;left:50%;top:-1px;bottom:-1px;width:1px;background:__CTRLEDGE__;"></span>' +
      (v == null ? '' :
        '<span style="position:absolute;top:0;bottom:0;left:'+barLeft.toFixed(1)+'%;width:'+w.toFixed(1)+'%;' +
        'background:'+(v >= 0 ? TEAL : RED)+';opacity:.8;border-radius:1px;"></span>') +
      '</span></span>';
    return '<button data-sec="'+r.id+'" class="hrow" style="appearance:none;border:none;margin:0;padding:0 14px;width:100%;' +
      'cursor:pointer;display:grid;grid-template-columns:__SGRIDCOLS__;border-bottom:1px solid __ROWRULE__;' +
      'background:'+(active ? 'rgba(200,16,46,.05)' : 'transparent')+';font-family:inherit;text-align:left;">' +
      '<span style="display:flex;align-items:center;padding:9px 10px;font-size:13px;font-weight:600;' +
      'color:'+(active ? RED : INK)+';white-space:nowrap;">'+esc(r.name)+'</span>' +
      '<span style="display:flex;align-items:center;justify-content:flex-end;padding:9px 10px;' +
      'font-family:'+mono+';font-size:11px;color:'+MUT+';">'+r.n+'</span>' +
      cells + bar +
      '<span style="display:flex;align-items:center;justify-content:flex-end;padding:9px 10px;border-left:1px solid __SEP__;">' +
      '<span style="font-family:'+mono+';font-size:10px;color:#4a4a4a;border:1px solid __EDGE__;border-radius:2px;' +
      'padding:2px 7px;background:rgba(255,255,255,.5);">'+esc(r.bench)+'</span></span></button>';
  }).join('');
  document.getElementById('sumbody').innerHTML = html;
  var fd = document.getElementById('fnDyn');
  if (fd) fd.textContent = L.footnote_dyn.replace('{max}', YTD_MAX.toFixed(1));
}

function render(){
  computeSums();
  renderSummary();
  var sec = null;
  P.sectors.forEach(function(s){ if (s.id === st_.tab) sec = s; });
  if (!sec) return;

  // tabs（家数随地区过滤联动）
  document.getElementById('tabs').innerHTML = P.sectors.map(function(s){
    var on = s.id === st_.tab;
    return '<button data-tab="'+s.id+'" style="appearance:none;background:transparent;border:none;margin:0 0 -1px;cursor:pointer;' +
      'display:inline-flex;align-items:baseline;gap:6px;padding:8px 2px 10px;' +
      'border-bottom:2.5px solid '+(on?RED:'transparent')+';">' +
      '<span style="font-size:14px;font-weight:'+(on?700:500)+';color:'+(on?RED:'#6b655e')+';letter-spacing:.01em;">'+esc(s.name)+'</span>' +
      '<span style="font-family:'+mono+';font-size:10px;color:'+MUT+';">('+rowsFiltered(s).length+')</span></button>';
  }).join('');

  // sort（NM 恒沉底；行集 = 地区过滤后）
  var sk = st_.sortKey, dir = st_.sortDir;
  var rows = rowsFiltered(sec).slice().sort(function(a,b){
    var x = a[sk], y = b[sk];
    if (sk === 't' || sk === 'n') return String(x).localeCompare(String(y)) * dir;
    var xBad = (x == null || !isFinite(x)), yBad = (y == null || !isFinite(y));
    if (xBad && yBad) return 0;
    if (xBad) return 1;
    if (yBad) return -1;
    return (x - y) * dir;
  });

  // column stats
  var colVals = {}, colSorted = {}, colMaxAbs = {};
  COLS.forEach(function(c){
    if (c.type === 'text') return;
    var vs = rows.map(function(r){ return r[c.k]; }).filter(function(v){ return v != null && isFinite(v); });
    colVals[c.k] = vs;
    colSorted[c.k] = vs.slice().sort(function(a,b){ return a-b; });
    colMaxAbs[c.k] = Math.max(Math.max.apply(null, vs.map(Math.abs).concat([0])), 0.0001);
  });
  var maxMcap = Math.max(Math.max.apply(null, (colVals['mcap']||[0]).concat([0])), 1);

  function pct(k, v){
    var s = colSorted[k];
    if (!s || s.length < 2 || v == null || !isFinite(v)) return null;
    var i = 0; while (i < s.length && s[i] < v) i++;
    return i / (s.length - 1);
  }
  function tint(col, v){
    if (v == null || !isFinite(v) || S === 0) return 'transparent';
    if (col.type === 'ret'){
      var a = Math.min(Math.abs(v)/colMaxAbs[col.k], 1) * S;
      if (Math.abs(v) < 0.05) return 'transparent';
      return v > 0 ? 'rgba(13,118,128,'+a.toFixed(3)+')' : 'rgba(200,16,46,'+a.toFixed(3)+')';
    }
    var p = pct(col.k, v);
    if (p == null) return 'transparent';
    if (col.type === 'fcf') p = 1 - p;          // 高 FCF 收益 = 便宜 = 青
    var d = Math.abs(p - 0.5) * 2 * S;
    if (d < 0.01) return 'transparent';
    return p < 0.5 ? 'rgba(13,118,128,'+d.toFixed(3)+')' : 'rgba(200,16,46,'+d.toFixed(3)+')';
  }

  // 摘要条
  var ytds = colVals['ytd'] || [];
  var up = ytds.filter(function(v){ return v > 0; }).length;
  var dn = ytds.filter(function(v){ return v < 0; }).length;
  var mYtd = median(ytds);
  var tot = (colVals['mcap']||[]).reduce(function(a,b){ return a+b; }, 0);
  document.getElementById('sumCount').textContent = rows.length + ' ' + L.unit_names;
  document.getElementById('sumMcap').textContent = '$' + tot.toLocaleString('en-US',{maximumFractionDigits:1,minimumFractionDigits:1}) + 'B';
  var eY = document.getElementById('sumYtd');
  eY.textContent = fmt('ret', mYtd);
  eY.style.color = mYtd > 0 ? TEAL : mYtd < 0 ? RED : INK;
  document.getElementById('bUp').style.width = (up/(up+dn||1)*100).toFixed(1)+'%';
  document.getElementById('bDn').style.width = (dn/(up+dn||1)*100).toFixed(1)+'%';
  document.getElementById('upN').textContent = up;
  document.getElementById('dnN').textContent = dn;

  // 列头
  var head = COLS.map(function(c, i){
    var on = c.k === sk;
    return '<button data-k="'+c.k+'" style="appearance:none;background:transparent;border:none;margin:0;cursor:pointer;' +
      'font-family:'+mono+';font-size:10px;letter-spacing:.05em;font-weight:'+(on?700:500)+';color:'+(on?RED:'#4a4a4a')+';' +
      'padding:7px 10px 9px;text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';">' +
      esc(c.label) + (on ? (dir < 0 ? ' ▾' : ' ▴') : '') + '</button>';
  }).join('');

  // 中位数行
  var med = COLS.map(function(c, i){
    var txt = c.k === 't' ? '—' : c.k === 'n' ? L.median : fmt(c.type, median(colVals[c.k]||[]));
    return '<span style="font-family:'+mono+';font-size:11px;color:'+MUT+';font-weight:500;padding:6px 10px;' +
      'text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';">'+txt+'</span>';
  }).join('');

  // 数据行
  var body = rows.map(function(r){
    var cells = COLS.map(function(c, i){
      var v = r[c.k];
      var flexAlign = c.align === 'right' ? 'flex-end' : 'flex-start';
      var s0 = 'display:flex;flex-direction:column;justify-content:center;align-items:'+flexAlign+';' +
        'padding:8px 10px;text-align:'+c.align+';white-space:nowrap;border-left:'+blFor(i)+';' +
        'font-variant-numeric:tabular-nums;line-height:1.35;';
      if (c.k === 't')
        return '<span style="'+s0+'font-family:'+mono+';font-size:11px;font-weight:500;color:'+MUT+';"><span>'+esc(r.t)+'</span></span>';
      if (c.k === 'n')
        return '<span style="'+s0+'font-family:'+sans+';font-size:13px;font-weight:600;color:'+INK+';"><span>'+esc(r.n)+'</span></span>';
      if (c.type === 'mcap'){
        // 缺市值（multiples 快照无该票）→ 与其它列一致的 DIM 'NM'，且不画条
        if (v == null || !isFinite(v))
          return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:500;color:'+DIM+';"><span>NM</span></span>';
        var bw = Math.sqrt(v/maxMcap)*100;
        return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:600;color:'+INK+';">' +
          '<span>'+fmt('mcap', v)+'</span>' +
          '<span style="display:block;height:3px;background:rgba(26,26,26,.18);border-radius:1px;margin-top:3px;align-self:stretch;">' +
          '<span style="display:block;height:100%;background:'+RED+';border-radius:1px;width:'+bw.toFixed(1)+'%;"></span></span></span>';
      }
      var fg = INK, fw = 500;
      if (v == null || !isFinite(v)) fg = DIM;
      else if (c.type === 'ret' || c.type === 'fcf'){
        var flat = Math.abs(v) < 0.05;
        fg = flat ? MUT : (v > 0 ? TEAL : RED);
        fw = 600;
      }
      return '<span style="'+s0+'font-family:'+mono+';font-size:12px;font-weight:'+fw+';color:'+fg+';background:'+tint(c, v)+';">' +
        '<span>'+fmt(c.type, v)+'</span></span>';
    }).join('');
    return '<div class="hrow" style="display:grid;grid-template-columns:'+GRID+';padding:0 14px;border-bottom:1px solid __ROWRULE__;">'+cells+'</div>';
  }).join('');

  document.getElementById('thead').innerHTML = head;
  document.getElementById('tmed').innerHTML = med;
  document.getElementById('tbody').innerHTML = body;
}

document.getElementById('tabs').addEventListener('click', function(e){
  var b = e.target.closest('button[data-tab]');
  if (!b) return;
  st_.tab = b.getAttribute('data-tab');
  render();
  document.getElementById('scroller').scrollTop = 0;
});
document.getElementById('sumbody').addEventListener('click', function(e){
  var b = e.target.closest('button[data-sec]');
  if (!b) return;
  st_.tab = b.getAttribute('data-sec');
  render();
  document.getElementById('scroller').scrollTop = 0;
});
document.getElementById('thead').addEventListener('click', function(e){
  var b = e.target.closest('button[data-k]');
  if (!b) return;
  var k = b.getAttribute('data-k');
  if (st_.sortKey === k) st_.sortDir = -st_.sortDir;
  else { st_.sortKey = k; st_.sortDir = (k === 't' || k === 'n') ? 1 : -1; }
  render();
});
var _rch = document.getElementById('rchips');
if (_rch) _rch.addEventListener('click', function(e){
  var b = e.target.closest('button[data-reg]');
  if (!b) return;
  var code = b.getAttribute('data-reg');
  REG.forEach(function(g){ if (g.code === code) g.on = !g.on; });
  renderRegionChips();
  render();
});
renderRegionChips();
render();
"""
    js = (js.replace("__PAYLOAD__", payload)
            .replace("__RED__", _RED).replace("__TEAL__", _TEAL)
            .replace("__INK__", _INK).replace("__MUT__", _MUT)
            .replace("__DIM__", _DIM).replace("__SEP__", _SEP)
            .replace("__ROWRULE__", _ROW_RULE)
            .replace("__SGRIDCOLS__", _SGRID).replace("__GRIDCOLS__", _GRID)
            .replace("__CTRLEDGE__", _CTRL_EDGE).replace("__EDGE__", _EDGE))

    LT = chr(60)
    TAG, ETAG = LT + "scr" + "ipt", LT + "/scr" + "ipt>"
    font_face = theme.FONT_FACE_CSS.strip()
    mono_css = "'JetBrains Mono',monospace"

    grp_band = (
        f'<div style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
        'background:rgba(255,241,229,.9);">'
        f'<span style="grid-column:4 / span 4;font-family:{mono_css};font-size:9px;letter-spacing:.16em;'
        f'color:{_MUT};font-weight:600;padding:8px 10px 0;border-left:1px solid {_SEP};text-align:right;">{labels["grp_ret"]}</span>'
        f'<span style="grid-column:8 / span 4;font-family:{mono_css};font-size:9px;letter-spacing:.16em;'
        f'color:{_MUT};font-weight:600;padding:8px 10px 0;border-left:1px solid {_SEP};text-align:right;">{labels["grp_val"]}</span>'
        f'<span style="grid-column:12;font-family:{mono_css};font-size:9px;letter-spacing:.16em;'
        f'color:{_MUT};font-weight:600;padding:8px 10px 0;border-left:1px solid {_SEP};text-align:right;">{labels["grp_cf"]}</span>'
        '</div>'
    )

    def _sum_pair(lbl_key: str, span_id: str) -> str:
        return ('<span style="display:inline-flex;align-items:baseline;gap:7px;">'
                f'<span style="font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_MUT};">{labels[lbl_key]}</span>'
                f'<span id="{span_id}" style="font-family:{mono_css};font-size:13px;font-weight:700;color:{_INK};"></span></span>')

    # 板块汇总列头（静态；行体 JS 渲染进 #sumbody）
    _sc = labels["sum_cols"]

    def _sh(txt: str, align: str = "right", bl: bool = False) -> str:
        return (f'<span style="font-family:{mono_css};font-size:10px;letter-spacing:.05em;'
                f'font-weight:500;color:#4a4a4a;padding:7px 10px 9px;text-align:{align};'
                + (f'border-left:1px solid {_SEP};' if bl else '') + f'">{txt}</span>')

    sum_head = (_sh(_sc["sector"], "left") + _sh(_sc["n"]) + _sh(_sc["d1"], bl=True)
                + _sh(_sc["d5"]) + _sh(_sc["m1"]) + _sh(_sc["ytd"])
                + _sh(_sc["dist"], "left", bl=True) + _sh(_sc["bench"], bl=True))

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f"<style>{font_face}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "html,body{background:transparent;color-scheme:light;"
        f"font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';}}"
        ".hrow{transition:background .12s;}"
        ".hrow:hover{background:rgba(255,255,255,.8);}"
        "button:hover{opacity:.85;}"
        f"#scroller{{max-height:{table_max_h}px;overflow:auto;}}"
        ".rchip{appearance:none;cursor:pointer;border-radius:2px;padding:3px 10px;"
        f"font-size:10px;letter-spacing:.06em;border:1px solid {_EDGE};"
        f"background:rgba(255,255,255,.35);color:{_MUT};font-weight:500;}}"
        ".rchip.on{"
        f"background:rgba(200,16,46,.07);border-color:{_RED};color:{_RED};font-weight:700;}}"
        "</style></head><body>"
        # ── 板块汇总（zip4 设计：等权平均，行点击 = 切换下方热力表 tab）──
        '<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
        f'<span style="font-size:16px;font-weight:700;color:{_INK};">{labels["sum_title"]}</span>'
        f'<span style="font-size:11.5px;color:{_MUT};">{labels["sum_sub"]}</span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_DIM};">{labels["sum_right"]}</span>'
        '</div>'
        f'<div style="margin-top:10px;margin-bottom:24px;border:1px solid {_EDGE};border-radius:2px;'
        'background:rgba(255,255,255,.45);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);overflow-x:auto;">'
        '<div style="min-width:900px;">'
        f'<div style="display:grid;grid-template-columns:{_SGRID};padding:0 14px;'
        f'border-bottom:2px solid {_INK};background:{theme.PAPER};">{sum_head}</div>'
        '<div id="sumbody"></div>'
        '</div></div>'
        # ── 板块热力图小节头 ──
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
        f'<span style="width:4px;height:14px;background:{_RED};border-radius:1px;flex:none;"></span>'
        f'<span style="font-size:16px;font-weight:700;color:{_INK};">{labels["heat_title"]}</span>'
        f'<span style="font-size:11.5px;color:{_MUT};">{labels["heat_sub"]}</span>'
        '</div>'
        # tabs（+ 地区 chips：行带 region 时出现；多选过滤，全部点灭 = 全集）
        f'<div id="tabs" style="display:flex;gap:26px;border-bottom:1px solid {_EDGE};flex-wrap:wrap;"></div>'
        + (
            '<div id="rchips" style="display:flex;gap:8px;flex-wrap:wrap;margin:9px 0 0;"></div>'
            if has_regions else ''
        ) +
        # 摘要条
        '<div style="display:flex;align-items:center;gap:22px;flex-wrap:wrap;padding:13px 2px 14px;">'
        + _sum_pair("cover", "sumCount") + _sum_pair("mcap_total", "sumMcap") + _sum_pair("ytd_med", "sumYtd") +
        '<span style="display:inline-flex;align-items:center;gap:9px;margin-left:auto;">'
        f'<span style="font-family:{mono_css};font-size:10px;letter-spacing:.1em;color:{_MUT};">{labels["breadth"]}</span>'
        f'<span style="display:inline-flex;width:130px;height:7px;border-radius:1px;overflow:hidden;background:{_SEP};">'
        f'<span id="bUp" style="display:block;height:100%;background:{_TEAL};width:0%;"></span>'
        f'<span id="bDn" style="display:block;height:100%;background:{_RED};width:0%;"></span></span>'
        f'<span style="font-family:{mono_css};font-size:11px;color:#4a4a4a;">'
        f'<span id="upN" style="color:{_TEAL};font-weight:700;"></span> {labels["up"]} / '
        f'<span id="dnN" style="color:{_RED};font-weight:700;"></span> {labels["dn"]}</span></span>'
        '</div>'
        # 表格（组头带 + sticky 列头 + 中位数行 + 滚动表体）
        f'<div style="border:1px solid {_EDGE};border-radius:2px;background:rgba(255,255,255,.45);'
        '-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);overflow-x:auto;">'
        '<div style="min-width:1040px;">'
        f'{grp_band}'
        '<div id="scroller">'
        f'<div id="thead" style="position:sticky;top:0;z-index:3;display:grid;grid-template-columns:{_GRID};'
        f'padding:0 14px;background:{theme.PAPER};border-bottom:2px solid {_INK};"></div>'
        f'<div id="tmed" style="display:grid;grid-template-columns:{_GRID};padding:0 14px;'
        f'border-bottom:1px solid {_EDGE};background:rgba(255,255,255,.35);"></div>'
        '<div id="tbody"></div>'
        '</div></div></div>'
        # 口径脚注
        f'<div style="margin-top:18px;border-top:1px solid {_INK};padding-top:10px;display:flex;gap:16px;flex-wrap:wrap;">'
        f'<span style="font-size:11.5px;line-height:1.7;color:{_MUT};max-width:940px;">{labels["footnote"]} '
        '<span id="fnDyn"></span></span>'
        f'<span style="margin-left:auto;font-family:{mono_css};font-size:10.5px;letter-spacing:.08em;color:{_DIM};">{labels["brand"]}</span>'
        '</div>'
        f'{TAG}>{js}{ETAG}</body></html>'
    )
    return doc, iframe_h
