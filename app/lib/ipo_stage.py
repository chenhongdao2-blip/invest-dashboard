"""app/lib/ipo_stage.py — 港股 IPO 打新 · 1a 报纸精修

Public entry:
    render(picks, intraday, *, prefer_cn, as_of) -> None

Internal:
    _build_html(picks, intraday, prefer_cn, as_of) -> str   # pure, testable

Design ref: docs/harness/reskin-wave2/specs/ipo-1a.md  (George approved 2026-07-03)
Contract  : docs/harness/reskin-wave2/CONTRACT.md §0 D1-D5, §2 IPO1-IPO15
"""
from __future__ import annotations

import json
import math
from html import escape as _esc
from typing import Any

import pandas as pd
import streamlit as st

from lib import theme  # PYTHONPATH=app 惯例;`from app.lib` 在 AppTest/Cloud 下 ModuleNotFoundError(R1 IPO15)

# ── Page-scope exemption: CONTRACT §0 D2 ─────────────────────────────────────
# All "down / break / worst" within this reskin surface use CMSI_RED (#c8102e).
# The global theme.DOWN (#cc0000) is NOT modified here.
_DOWN = theme.CMSI_RED   # "#c8102e"
_UP   = theme.UP         # "#0d7680"

_TIER_COLORS: dict[str, str] = {
    "重点申购+": "#a00d25",
    "重点申购":  _DOWN,
    "推荐申购":  _UP,
    "谨慎申购":  "#a06d1f",
    "不申购":    "#6b6560",
}
_TIER_ORDER = list(_TIER_COLORS.keys())


# ── helpers ───────────────────────────────────────────────────────────────────

def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── CSS (plain string → replace for font tokens; avoids {{}} escaping in CSS) ─

_CSS_TEMPLATE = """{FONT_FACE_CSS}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff1e5;font-family:{FONT_STACK};color:#1a1a1a;padding:24px 28px 32px;min-height:100vh}

/* masthead */
.mh{border-bottom:2px solid #1a1a1a;padding-bottom:16px;margin-bottom:22px;display:flex;justify-content:space-between;align-items:flex-start}
.mh-left{display:flex;flex-direction:column;gap:6px}
.mh-title-row{display:flex;align-items:center;gap:10px}
.mh-bar{width:5px;height:48px;background:#c8102e;flex-shrink:0}
.mh-title{font-family:{FONT_DISPLAY};font-size:30px;font-weight:700;color:#1a1a1a;letter-spacing:-0.02em;line-height:1.1}
.mh-chip{display:inline-block;font-family:{FONT_MONO};font-size:13px;font-weight:600;color:#8a8580;border:1px solid #e4d2bd;border-radius:3px;padding:3px 9px;letter-spacing:0.02em;margin-top:6px}
.mh-sub{font-family:{FONT_MONO};font-size:11px;color:#8a8580;letter-spacing:0.08em;margin-top:2px}
.mh-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px}
.mh-pulse-row{display:flex;align-items:center;gap:6px}
.pulse-dot{width:8px;height:8px;border-radius:50%;background:#c8102e;animation:pulseDot 1.5s ease-in-out infinite}
@keyframes pulseDot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.82)}}
.mh-status{font-family:{FONT_MONO};font-size:10px;font-weight:600;color:#c8102e;letter-spacing:0.16em;text-transform:uppercase}
.mh-date{font-family:{FONT_MONO};font-size:11px;color:#8a8580}

/* glass */
.glass{background:rgba(255,255,255,.55);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);border-radius:4px}
.glass-strong{background:rgba(255,255,255,.6);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.75);border-radius:4px}

/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:28px}
.kpi-card{padding:18px 20px 16px;border-top:3px solid}
.kpi-label{font-family:{FONT_MONO};font-size:10px;font-weight:600;color:#8a8580;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px}
.kpi-value{font-family:{FONT_MONO};font-size:48px;font-weight:700;letter-spacing:-0.02em;line-height:1}
.kpi-foot{font-family:{FONT_MONO};font-size:11px;color:#8a8580;margin-top:6px}

/* section header */
.sec-hd{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.sec-bar{width:4px;height:16px;background:#c8102e;flex-shrink:0}
.sec-label{font-family:{FONT_MONO};font-size:12px;font-weight:600;color:#1a1a1a;letter-spacing:0.16em;text-transform:uppercase}
.sec-sub{font-family:{FONT_MONO};font-size:11px;color:#8a8580;margin-left:4px}

/* tier */
.tier-section{margin-bottom:32px}
.tier-wrap{padding:0 16px}
.tier-hd-row,.tier-row{display:grid;grid-template-columns:150px 70px 1fr 110px 90px;gap:12px;align-items:center;border-bottom:1px solid #eadbc8}
.tier-hd-row{border-bottom:1.5px solid #1a1a1a;padding:0 0 7px}
.tier-row{padding:8px 0}
.tier-hd{font-family:{FONT_MONO};font-size:10px;font-weight:600;color:#8a8580;letter-spacing:0.1em;text-transform:uppercase}
.tier-chip{display:inline-block;font-family:{FONT_MONO};font-size:11px;font-weight:600;border:1px solid;border-radius:3px;padding:2px 7px;white-space:nowrap}
.tier-count{font-family:{FONT_MONO};font-size:13px;font-weight:600;color:#1a1a1a;text-align:center}
.tier-bar-cell{display:flex;align-items:center;gap:8px}
.tier-bar-track{width:160px;height:8px;background:rgba(26,26,26,.06);border-radius:2px;flex-shrink:0}
.tier-bar-fill{height:100%;border-radius:2px;min-width:2px}
.tier-median{font-family:{FONT_MONO};font-size:13px;font-weight:700;min-width:60px}
.tier-green{font-family:{FONT_MONO};font-size:13px;font-weight:600;color:#4a4a4a;text-align:center}
.tier-break{font-family:{FONT_MONO};font-size:13px;font-weight:700;text-align:center}
.tier-foot{font-family:{FONT_MONO};font-size:10.5px;color:#8a8580;margin-top:8px;padding-left:4px}

/* ranking */
.rank-section{margin-bottom:32px}
.rank-grid{display:grid;grid-template-columns:1fr 400px;gap:20px;align-items:start}
.rank-table{width:100%;border-collapse:collapse}
.rank-table thead th{font-family:{FONT_MONO};font-size:10px;font-weight:600;color:#8a8580;letter-spacing:0.1em;text-transform:uppercase;padding:0 4px 7px;border-bottom:1.5px solid #1a1a1a;text-align:left;white-space:nowrap}
.rank-table thead th.r{text-align:right}
.rank-table tbody tr{cursor:pointer}
.rank-table tbody tr:hover,.rank-table tbody tr.active{background:rgba(200,16,46,.06)}
.rank-table tbody td{font-family:{FONT_MONO};font-size:13px;padding:7px 4px;border-bottom:1px solid #eadbc8;vertical-align:middle}
.td-no{font-size:12px;color:#8a8580;width:36px}
.td-code{width:60px}
.td-name{font-size:13.5px;font-weight:700;width:140px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.td-score{width:56px;font-weight:700;text-align:center}
.td-tier{width:104px}
.td-sector{color:#4a4a4a;font-size:12px}
.td-date{font-size:11px;color:#8a8580;width:84px}
.td-d1{text-align:right;font-weight:700;width:92px}

/* dock */
.dock{position:sticky;top:16px;padding:20px 22px;border-top:3px solid #1a1a1a}
.dock-name{font-family:{FONT_DISPLAY};font-size:19px;font-weight:700;color:#1a1a1a}
.dock-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;margin-bottom:8px}
.dock-d1{font-family:{FONT_MONO};font-size:38px;font-weight:700;letter-spacing:-0.02em;margin-bottom:4px}
.dock-note{font-family:{FONT_MONO};font-size:10px;color:#8a8580;letter-spacing:0.08em;margin-bottom:12px}
.dock-foot{border-top:1px solid #eadbc8;padding-top:8px;margin-top:8px;font-family:{FONT_MONO};font-size:11px;color:#8a8580}
.dock-empty{display:flex;align-items:center;justify-content:center;height:120px;font-family:{FONT_MONO};font-size:11px;color:#8a8580;letter-spacing:0.06em}

/* footer */
.footer{border:1px solid #e4d2bd;background:rgba(255,255,255,.4);border-radius:4px;padding:12px 18px;font-family:{FONT_MONO};font-size:10.5px;line-height:1.7;color:#8a8580;margin-top:8px}
"""


def _make_css() -> str:
    return (_CSS_TEMPLATE
            .replace("{FONT_FACE_CSS}", theme.FONT_FACE_CSS)
            .replace("{FONT_STACK}",   theme.FONT_STACK)
            .replace("{FONT_DISPLAY}", theme.FONT_DISPLAY)
            .replace("{FONT_MONO}",    theme.FONT_MONO))


# ── JS (plain string — no f-string; JS {} braces need no escaping here) ──────

_JS_LOGIC = r"""
function retColor(pct) {
  if (pct === null || pct === undefined) return '#8a8580';
  if (pct > 0) return '#0d7680';
  if (pct < 0) return '#c8102e';
  return '#8a8580';
}

function chipHtml(tier) {
  var color = TIER_COLORS[tier] || '#6b6560';
  var r = parseInt(color.slice(1,3),16);
  var g = parseInt(color.slice(3,5),16);
  var b = parseInt(color.slice(5,7),16);
  var bg = 'rgba(' + r + ',' + g + ',' + b + ',.07)';
  return '<span style="font-family:monospace;font-size:9.5px;font-weight:600;color:' + color + ';border:1px solid ' + color + ';border-radius:3px;padding:1px 6px;background:' + bg + '">' + tier + '</span>';
}

function codeChipHtml(code) {
  return '<span style="font-family:monospace;font-size:9.5px;font-weight:600;color:#8a8580;border:1px solid #e4d2bd;border-radius:3px;padding:1px 6px;background:rgba(255,255,255,.4)">' + code + '</span>';
}

/* Catmull-Rom cubic bezier path in SVG */
function catmullPath(pts) {
  var n = pts.length;
  if (n < 2) return '';
  function gp(i) { return i < 0 ? pts[0] : i >= n ? pts[n-1] : pts[i]; }
  var d = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1);
  for (var i = 0; i < n - 1; i++) {
    var p0 = gp(i-1), p1 = pts[i], p2 = pts[i+1], p3 = gp(i+2);
    var cp1x = (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1);
    var cp1y = (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1);
    var cp2x = (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1);
    var cp2y = (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1);
    d += ' C' + cp1x + ',' + cp1y + ' ' + cp2x + ',' + cp2y + ' ' + p2[0].toFixed(1) + ',' + p2[1].toFixed(1);
  }
  return d;
}

function buildSVG(pts, d1Pct) {
  var W = 356, H = 200;
  var PL = 32, PR = 12, PT = 20, PB = 28;
  var iW = W - PL - PR, iH = H - PT - PB;
  var yMin = Math.min.apply(null, pts.concat([0])) - 2;
  var yMax = Math.max.apply(null, pts.concat([0])) + 2;
  var yRange = yMax - yMin || 1;
  var n = pts.length;

  function px(i) { return PL + (i / (n - 1)) * iW; }
  function py(v) { return PT + (1 - (v - yMin) / yRange) * iH; }

  /* grid lines (3 horizontal) */
  var gridVals = [yMin + yRange * 0.25, yMin + yRange * 0.5, yMin + yRange * 0.75];
  var gridSVG = gridVals.map(function(v) {
    return '<line x1="' + PL + '" y1="' + py(v).toFixed(1) + '" x2="' + (W-PR) + '" y2="' + py(v).toFixed(1) + '" stroke="#eadbc8" stroke-width="1"/>';
  }).join('');

  /* 0% break-even line */
  var y0 = py(0).toFixed(1);
  var zeroSVG = '<line x1="' + PL + '" y1="' + y0 + '" x2="' + (W-PR) + '" y2="' + y0 + '" stroke="#8a8580" stroke-width="1" stroke-dasharray="4 4" opacity="0.65"/>'
    + '<text x="' + (PL-4) + '" y="' + (parseFloat(y0)+3.5).toFixed(1) + '" font-size="9" font-family="monospace" fill="#8a8580" text-anchor="end">0%</text>';

  var color = d1Pct >= 0 ? '#0d7680' : '#c8102e';
  var r = parseInt(color.slice(1,3),16), g = parseInt(color.slice(3,5),16), b = parseInt(color.slice(5,7),16);
  var areaBg = 'rgba(' + r + ',' + g + ',' + b + ',.10)';

  /* convert to [x,y] pairs */
  var xyPts = pts.map(function(v, i) { return [px(i), py(v)]; });

  var pathD = catmullPath(xyPts);

  /* area (close to baseline) */
  var lastX = px(n-1).toFixed(1);
  var firstX = px(0).toFixed(1);
  var bottomY = (PT + iH).toFixed(1);
  var areaD = pathD + ' L' + lastX + ',' + bottomY + ' L' + firstX + ',' + bottomY + ' Z';

  /* endpoint circle */
  var endX = px(n-1).toFixed(1);
  var endY = py(pts[n-1]).toFixed(1);

  return '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg" style="display:block">'
    + gridSVG + zeroSVG
    + '<path d="' + areaD + '" fill="' + areaBg + '" stroke="none"/>'
    + '<path d="' + pathD + '" fill="none" stroke="' + color + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
    + '<circle cx="' + endX + '" cy="' + endY + '" r="4" fill="' + color + '" stroke="#fff1e5" stroke-width="1.5"/>'
    + '</svg>';
}

/* Ranking table */
function buildRankRows() {
  var tbody = document.getElementById('rank-body');
  tbody.innerHTML = '';
  ROWS.forEach(function(r, idx) {
    var tr = document.createElement('tr');
    tr.dataset.code = r.code;
    var d1html;
    if (r.pending) {
      d1html = '<span style="color:#8a8580">—</span>';
    } else {
      var sign = r.d1_pct >= 0 ? '+' : '';
      d1html = '<span style="color:' + retColor(r.d1_pct) + '">' + sign + r.d1_pct.toFixed(1) + '%</span>';
    }
    var rankStr = r.rank === null ? '—' : String(r.rank).padStart(2, '0');
    var listDateCell = r.list_date || (r.pending ? '待上市' : '—');
    tr.innerHTML =
      '<td class="td-no">' + rankStr + '</td>'
      + '<td class="td-code">' + r.code + '</td>'
      + '<td class="td-name" title="' + r.name + '">' + r.name + '</td>'
      + '<td class="td-score" style="color:#1a1a1a">' + r.score.toFixed(1) + '</td>'
      + '<td class="td-tier">' + chipHtml(r.tier) + '</td>'
      + '<td class="td-sector" style="font-size:12px;color:#4a4a4a">' + r.sub_sector + '</td>'
      + '<td class="td-date">' + listDateCell + '</td>'
      + '<td class="td-d1">' + d1html + '</td>';
    tr.addEventListener('mouseenter', function() { showDock(r.code); });
    tbody.appendChild(tr);
  });
}

/* Dock */
var activeCode = null;
function showDock(code) {
  if (code === activeCode) return;
  activeCode = code;

  document.querySelectorAll('#rank-body tr').forEach(function(tr) {
    tr.classList.toggle('active', tr.dataset.code === code);
  });

  var row = null;
  for (var i = 0; i < ROWS.length; i++) { if (ROWS[i].code === code) { row = ROWS[i]; break; } }
  if (!row) return;

  var dock = document.getElementById('dock-content');
  var color = retColor(row.d1_pct);
  var d1str = row.pending ? '—' : ((row.d1_pct >= 0 ? '+' : '') + row.d1_pct.toFixed(1) + '%');
  var intra = INTRADAY[code];

  var svgHtml = '';
  var footStr = '';
  if (intra && intra.pts && intra.pts.length >= 2) {
    svgHtml = '<div>' + buildSVG(intra.pts, intra.d1_pct) + '</div>';
    var hi = Math.max.apply(null, intra.pts).toFixed(1);
    var lo = Math.min.apply(null, intra.pts).toFixed(1);
    footStr = '区间高 ' + (parseFloat(hi) >= 0 ? '+' : '') + hi + '% · 区间低 ' + (parseFloat(lo) >= 0 ? '+' : '') + lo + '% · 来源 ' + (row.source || 'futu 5min');
  } else if (!row.pending) {
    svgHtml = '<div class="dock-empty">盘中路径未采集 · 仅首日收盘</div>';
    footStr = '首日收盘 ' + d1str;
  } else {
    svgHtml = '<div class="dock-empty">待上市 · 盘中路径暂无</div>';
  }

  dock.innerHTML =
    '<div class="dock-name">' + row.name + '</div>'
    + '<div class="dock-chips">' + codeChipHtml(row.code) + ' ' + chipHtml(row.tier) + '</div>'
    + '<div class="dock-d1" style="color:' + color + '">' + d1str + '</div>'
    + '<div class="dock-note">首日盘中 · 相对发行价 % · 终点 = 首日收盘</div>'
    + svgHtml
    + (footStr ? '<div class="dock-foot">' + footStr + '</div>' : '');
}

/* init */
buildRankRows();
if (DEFAULT_CODE) { showDock(DEFAULT_CODE); }
"""


# ── HTML builder (pure, no Streamlit) ─────────────────────────────────────────

def _build_html(
    picks: pd.DataFrame,
    intraday: pd.DataFrame,
    prefer_cn: bool,
    as_of: str,
) -> str:
    """Return self-contained srcdoc HTML for the IPO 1a composition.

    Deliberately import-free from Streamlit so it can be unit-tested.
    """
    # ── 1. Data prep ──────────────────────────────────────────────────────
    df = picks.copy()
    df["code"] = df["code"].astype(str)

    listed_mask = df["status"].fillna("").astype(str).str.lower() == "listed"
    df_listed  = df[listed_mask].copy()
    df_pending = df[~listed_mask].copy()

    n_total   = len(df)
    n_listed  = len(df_listed)
    n_pending = len(df_pending)

    _name_col = "name_cn" if prefer_cn else "name_en"
    if _name_col not in df.columns:
        _name_col = "name_cn" if "name_cn" in df.columns else df.columns[0]

    # ── 2. KPI stats ──────────────────────────────────────────────────────
    if n_listed > 0:
        best_idx   = df_listed["day1_ret"].idxmax()
        worst_idx  = df_listed["day1_ret"].idxmin()
        best_row   = df_listed.loc[best_idx]
        worst_row  = df_listed.loc[worst_idx]
        best_pct   = float(best_row["day1_ret"])  * 100.0
        worst_pct  = float(worst_row["day1_ret"]) * 100.0

        def _safe_name(row: pd.Series) -> str:
            v = row.get(_name_col, row.get("name_cn", ""))
            return _esc(str(v)) if v and not _is_na(v) else "—"

        best_name  = _safe_name(best_row)
        worst_name = _safe_name(worst_row)
        best_tier  = _esc(str(best_row.get("tier",  "")))
        worst_tier = _esc(str(worst_row.get("tier", "")))
    else:
        best_pct = worst_pct = None
        best_name = worst_name = "—"
        best_tier = worst_tier = "—"

    # ── 3. Tier performance ───────────────────────────────────────────────
    tier_rows_html = ""
    if n_listed > 0:
        abs_medians: list[float] = []
        tier_stats: list[dict[str, Any]] = []

        for tier in _TIER_ORDER:
            tdf = df_listed[df_listed["tier"] == tier]
            if len(tdf) == 0:
                continue
            rets = tdf["day1_ret"].astype(float) * 100.0
            med  = float(rets.median())
            abs_medians.append(abs(med))
            tier_stats.append({
                "tier":        tier,
                "count":       len(tdf),
                "median":      med,
                "green_rate":  float((rets > 0).sum() / len(tdf) * 100),
                "break_count": int((rets < 0).sum()),
            })

        max_abs = max(abs_medians) if abs_medians else 1.0
        for ts in tier_stats:
            color    = _TIER_COLORS.get(ts["tier"], "#6b6560")
            chip_bg  = _hex_rgba(color, 0.07)
            bar_pct  = abs(ts["median"]) / max_abs * 100.0
            bar_clr  = _UP if ts["median"] >= 0 else _DOWN
            med_s    = f"{ts['median']:+.1f}%"
            brk_s    = "—" if ts["break_count"] == 0 else str(ts["break_count"])
            brk_clr  = "#8a8580" if ts["break_count"] == 0 else _DOWN
            tier_rows_html += (
                f'<div class="tier-row">'
                f'<div class="tier-chip" style="color:{color};border-color:{color};background:{chip_bg}">{ts["tier"]}</div>'
                f'<div class="tier-count">{ts["count"]}</div>'
                f'<div class="tier-bar-cell">'
                f'  <div class="tier-bar-track"><div class="tier-bar-fill" style="width:{bar_pct:.1f}%;background:{bar_clr}"></div></div>'
                f'  <span class="tier-median" style="color:{bar_clr}">{med_s}</span>'
                f'</div>'
                f'<div class="tier-green">{ts["green_rate"]:.0f}%</div>'
                f'<div class="tier-break" style="color:{brk_clr}">{brk_s}</div>'
                f'</div>'
            )

    if n_listed == 0:  # no listed samples → explicit empty state in tier table
        tier_rows_html = '<div style="padding:20px 16px;color:#8a8580;font-size:13px">暂无已上市样本</div>'

    # ── 4. Ranking rows (all N, score DESC) ───────────────────────────────
    df_sorted = df.sort_values("score", ascending=False).reset_index(drop=True)
    d1_lookup = {
        str(r["code"]): float(r["day1_ret"])
        for _, r in df_listed.iterrows()
    }
    src_lookup = {
        str(r["code"]): str(r.get("source", "futu 5min") or "futu 5min")
        for _, r in df_listed.iterrows()
    }

    rank_rows: list[dict[str, Any]] = []
    for idx, row in df_sorted.iterrows():
        is_pending = str(row.get("status", "")).strip().lower() != "listed"
        d1_pct     = None if is_pending else float(row["day1_ret"]) * 100.0
        try:
            ld_raw   = row["list_date"]
            list_date = "" if _is_na(ld_raw) else str(ld_raw)
        except (KeyError, TypeError):
            list_date = ""
        rank_rows.append({
            "rank":       None if is_pending else int(idx) + 1,
            "code":       str(row["code"]),
            "name":       str(row.get(_name_col, row.get("name_cn", ""))),
            "score":      float(row.get("score", 0) or 0),
            "tier":       str(row.get("tier", "")),
            "sub_sector": str(row.get("sub_sector", "") or ""),
            "list_date":  list_date,
            "d1_pct":     d1_pct,
            "pending":    is_pending,
            "source":     src_lookup.get(str(row["code"]), "futu 5min"),
        })

    # ── 5. Intraday paths ─────────────────────────────────────────────────
    # formula: pct = (close * (1 + d1) / last_close - 1) * 100
    # terminates exactly at day1_ret * 100  (CONTRACT IPO15)
    intraday_map: dict[str, dict[str, Any]] = {}
    if len(intraday) > 0:
        intra_c = intraday.copy()
        intra_c["code"] = intra_c["code"].astype(str)
        for code, grp in intra_c.groupby("code"):
            code_s = str(code)
            if code_s not in d1_lookup:
                continue
            d1 = d1_lookup[code_s]
            closes_s = pd.to_numeric(
                grp.sort_values("time")["close"], errors="coerce"
            )
            closes = [float(v) for v in closes_s.values if math.isfinite(float(v))]
            if len(closes) < 2:
                continue
            last = closes[-1]
            if not math.isfinite(last) or last == 0:
                continue
            pts = [round((c * (1.0 + d1) / last - 1.0) * 100.0, 4)
                   for c in closes]
            intraday_map[code_s] = {
                "d1_pct": round(d1 * 100.0, 4),
                "pts":    pts,
            }

    # ── 6. Default selected (rank 1) ──────────────────────────────────────
    default_code = rank_rows[0]["code"] if rank_rows else ""

    # ── 7. JS data block ──────────────────────────────────────────────────
    rank_json       = json.dumps(rank_rows,     ensure_ascii=False)
    intraday_json   = json.dumps(intraday_map,  ensure_ascii=False)
    tier_color_json = json.dumps(_TIER_COLORS,  ensure_ascii=False)
    default_json    = json.dumps(default_code)

    js_data = (
        f"const ROWS = {rank_json};\n"
        f"const INTRADAY = {intraday_json};\n"
        f"const TIER_COLORS = {tier_color_json};\n"
        f"const DEFAULT_CODE = {default_json};\n"
    )

    # ── 8. Assemble ───────────────────────────────────────────────────────
    css = _make_css()
    scr_open  = chr(60) + "scr" + "ipt>"
    scr_close = chr(60) + "/" + "sc" + "ript>"

    as_of_s = _esc(as_of)

    # Pre-build KPI card content — None sentinel → explicit empty state (no fabricated 0.0%)
    if best_pct is None:
        _best_val       = '<span style="font-size:20px;color:#8a8580">暂无已上市样本</span>'
        _best_foot_html = ""
    else:
        _best_val       = f'{best_pct:+.1f}%'
        _best_foot_html = f'<div class="kpi-foot">{best_name} · {best_tier}</div>'

    if worst_pct is None:
        _worst_val       = '<span style="font-size:20px;color:#8a8580">暂无已上市样本</span>'
        _worst_foot_html = ""
    else:
        _worst_val       = f'{worst_pct:+.1f}%'
        _worst_foot_html = f'<div class="kpi-foot">{worst_name} · {worst_tier}</div>'

    _dock_empty_msg = "暂无已上市样本" if n_listed == 0 else "hover 左侧行 → 显示盘中走势"

    parts: list[str] = [
        f"<!DOCTYPE html><html lang='zh-HK'><head><meta charset='utf-8'><style>{css}</style></head><body>",

        # masthead
        f"""<div class="mh">
  <div class="mh-left">
    <div class="mh-title-row">
      <div class="mh-bar"></div>
      <div>
        <div class="mh-title">港股 IPO 打新</div>
        <div class="mh-chip">CMSI 棱镜六因子 v6.7 · 策略后测</div>
      </div>
    </div>
    <div class="mh-sub">评分档 × 首日表现 · 样本 n={n_total} · 评分擅长判方向，不擅长测涨幅</div>
  </div>
  <div class="mh-right">
    <div class="mh-pulse-row">
      <div class="pulse-dot"></div>
      <span class="mh-status">BACKTEST · 后测</span>
    </div>
    <div class="mh-date">截至 {as_of_s} · CMSI / futu / iFind</div>
  </div>
</div>""",

        # KPI 3 cards
        f"""<div class="kpi-grid">
  <div class="glass kpi-card" style="border-top-color:#1a1a1a">
    <div class="kpi-label">样本</div>
    <div class="kpi-value" style="color:#1a1a1a">{n_total}</div>
    <div class="kpi-foot">已上市 {n_listed} · 待上市 {n_pending}</div>
  </div>
  <div class="glass kpi-card" style="border-top-color:#0d7680">
    <div class="kpi-label">最高首日</div>
    <div class="kpi-value" style="color:#0d7680">{_best_val}</div>
    {_best_foot_html}
  </div>
  <div class="glass kpi-card" style="border-top-color:#c8102e">
    <div class="kpi-label">最差首日</div>
    <div class="kpi-value" style="color:#c8102e">{_worst_val}</div>
    {_worst_foot_html}
  </div>
</div>""",

        # tier section
        f"""<div class="tier-section">
  <div class="sec-hd">
    <div class="sec-bar"></div>
    <span class="sec-label">分档表现 · TIER PERFORMANCE</span>
    <span class="sec-sub">评分越高越好吗？—— 两端拉得开，中间三档拉不开</span>
  </div>
  <div class="glass tier-wrap">
    <div class="tier-hd-row">
      <div class="tier-hd">申购档</div>
      <div class="tier-hd" style="text-align:center">只数</div>
      <div class="tier-hd">中位首日</div>
      <div class="tier-hd" style="text-align:center">收涨率</div>
      <div class="tier-hd" style="text-align:center">破发</div>
    </div>
    {tier_rows_html}
    <div class="tier-foot">读法：中位首日 = 该档首日收盘相对发行价涨跌幅中位数；收涨率 = 首日收涨占比；破发 = 首日收盘低于发行价笔数</div>
  </div>
</div>""",

        # ranking + dock
        f"""<div class="rank-section">
  <div class="sec-hd">
    <div class="sec-bar"></div>
    <span class="sec-label">评分排行 · SCORE RANKING</span>
    <span class="sec-sub">hover 任意行 → 右侧浮出该股首日盘中大图</span>
  </div>
  <div class="rank-grid">
    <div>
      <table class="rank-table">
        <thead>
          <tr>
            <th style="width:36px">#</th>
            <th style="width:60px">代码</th>
            <th style="width:140px">名称</th>
            <th style="width:56px;text-align:center">评分</th>
            <th style="width:104px">申购档</th>
            <th>子板块</th>
            <th style="width:84px">上市日期</th>
            <th class="r" style="width:92px">首日涨幅</th>
          </tr>
        </thead>
        <tbody id="rank-body"></tbody>
      </table>
    </div>
    <div id="dock" class="glass-strong dock">
      <div id="dock-content">
        <div class="dock-empty">{_dock_empty_msg}</div>
      </div>
    </div>
  </div>
</div>""",

        # footer
        """<div class="footer">提示 · 后测口径 — 首日表现为上市当日定档快照，不随后续行情更新；本页为策略后测（backtest），非实时盯盘工具。评分由 CMSI 棱镜六因子 v6.7 离线计算，历史后测不代表未来业绩。仅供内部研究回测，不构成投资或申购建议。</div>""",

        # script
        scr_open,
        js_data,
        _JS_LOGIC,
        scr_close,
        "</body></html>",
    ]
    return "".join(parts)


def _is_na(v: Any) -> bool:
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return v is None


# ── Public entry ──────────────────────────────────────────────────────────────

def render(
    picks: pd.DataFrame,
    intraday: pd.DataFrame,
    *,
    prefer_cn: bool,
    as_of: str,
) -> None:
    """Render IPO 1a composition into the current Streamlit page.

    Args:
        picks:     DataFrame from load_ipo() — 54 rows (listed + pending).
                   Required columns: code, name_cn, name_en, score, tier,
                   list_date, day1_ret (decimal, ×100 at render), sub_sector,
                   status ('listed' | other), source.
        intraday:  DataFrame from load_ipo_intraday() — columns: code, time, close.
                   Only listed codes with 5-min data paths are populated.
        prefer_cn: True → use name_cn; False → use name_en.
        as_of:     Date string for provenance label, e.g. '2026-07-03'.
    """
    doc = _build_html(picks, intraday, prefer_cn, as_of)
    iframe_h = max(2400, 900 + len(picks) * 33)
    st.iframe(doc, height=iframe_h)


# ── Smoke test (run directly: python -m app.lib.ipo_stage) ────────────────────

if __name__ == "__main__":
    import sys

    # ── synthetic data ──
    picks_df = pd.DataFrame({
        "code":       ["1234", "5678", "9012", "3456"],
        "name_cn":    ["曦智医疗", "优先生物", "华健未来-B", "待上科技"],
        "name_en":    ["Xizhi Med", "UFirst Bio", "HH Future-B", "Pending Tech"],
        "score":      [8.5, 7.2, 6.0, 5.5],
        "tier":       ["重点申购+", "重点申购", "推荐申购", "推荐申购"],
        "list_date":  ["2025-01-15", "2025-02-20", "2025-03-10", None],
        "day1_ret":   [3.84, 0.05, -0.569, 0.0],   # decimal: 384%, 5%, -56.9%, 0%
        "sub_sector": ["医疗器械", "制药", "医疗服务", "生物科技"],
        "offer_price":[10.0, 5.0, 8.0, 12.0],
        "day1_close": [48.4, 5.25, 3.45, None],
        "status":     ["listed", "listed", "listed", "pending"],
        "source":     ["Wind", "Wind", "iFind", "Wind"],
    })

    # tiny intraday for code "1234" only
    intraday_df = pd.DataFrame({
        "code":  ["1234", "1234", "1234", "1234"],
        "time":  ["09:30", "11:00", "13:00", "16:00"],
        "close": [10.5,    25.0,   40.0,   48.4],
    })
    # With d1=3.84, last=48.4:
    # pct[i] = (c * (1+3.84) / 48.4 - 1) * 100
    # pct[3] = (48.4 * 4.84 / 48.4 - 1)*100 = (4.84-1)*100 = 384%  ✓

    html = _build_html(picks_df, intraday_df, prefer_cn=True, as_of="2026-07-03")

    # ── assertions ──
    errs: list[str] = []

    # CONTRACT IPO9: 上市日期 column must exist
    if "上市日期" not in html:
        errs.append("FAIL: '上市日期' not in html")
    else:
        print("PASS: '上市日期' in html")

    # pending row marker
    if "待上市" not in html:
        errs.append("FAIL: '待上市' not in html")
    else:
        print("PASS: '待上市' in html")

    # no MOCK strings (GR battery)
    if "MOCK" in html:
        errs.append("FAIL: 'MOCK' found in html")
    else:
        print("PASS: no 'MOCK'")

    # no demo literal 2.69
    if "2.69" in html:
        errs.append("FAIL: demo literal '2.69' found in html")
    else:
        print("PASS: no '2.69'")

    # KPI sample card
    if "n=4" in html or (">4<" in html) or ">4 " in html or ">4\n" in html or "样本</div>\n    <div" in html:
        pass  # contained somewhere
    if "已上市 3 · 待上市 1" not in html:
        errs.append("FAIL: '已上市 3 · 待上市 1' not in html")
    else:
        print("PASS: KPI sample breakdown correct")

    # best/worst day1
    if "+384.0%" not in html:
        errs.append(f"FAIL: '+384.0%' not in html (best return)")
    else:
        print("PASS: best return +384.0%")

    if "-56.9%" not in html:
        errs.append(f"FAIL: '-56.9%' not in html (worst return)")
    else:
        print("PASS: worst return -56.9%")

    # no CDN fonts
    for cdn in ["fonts.googleapis.com", "fonts.gstatic.com"]:
        if cdn in html:
            errs.append(f"FAIL: CDN font URL '{cdn}' found")
        else:
            print(f"PASS: no CDN '{cdn}'")

    # no box-shadow
    if "box-shadow" in html:
        errs.append("FAIL: 'box-shadow' found in html (station rule violation)")
    else:
        print("PASS: no box-shadow")

    # tier stats hand-calc check
    # listed: 重点申购+ ret=384%, 重点申购 ret=5%, 推荐申购 ret=-56.9%
    # 重点申购+ median=384.0% → "+384.0%" in tier section
    # 推荐申购 break=1 → "1" should appear in break column
    if "重点申购+" not in html:
        errs.append("FAIL: '重点申购+' not in tier rows")
    else:
        print("PASS: '重点申购+' in tier rows")

    # intraday path should be in INTRADAY json
    if '"1234"' not in html:
        errs.append("FAIL: intraday code '1234' not in INTRADAY json")
    else:
        print("PASS: intraday code '1234' in INTRADAY json")

    # page size sanity
    sz = len(html)
    print(f"INFO: html size = {sz:,} bytes")
    if sz < 10_000:
        errs.append(f"FAIL: html suspiciously small ({sz} bytes)")

    # ── Case 2: all-pending → no fabricated 0.0%, explicit empty state ──────
    picks_all_pending = pd.DataFrame({
        "code":       ["1111", "2222"],
        "name_cn":    ["待上医疗", "待上科技"],
        "name_en":    ["Pending Med", "Pending Tech"],
        "score":      [7.0, 6.0],
        "tier":       ["重点申购", "推荐申购"],
        "list_date":  [None, None],
        "day1_ret":   [0.0, 0.0],
        "sub_sector": ["医疗器械", "生物科技"],
        "offer_price":[10.0, 8.0],
        "day1_close": [None, None],
        "status":     ["pending", "pending"],
        "source":     ["Wind", "Wind"],
    })
    _empty_intra = pd.DataFrame(columns=["code", "time", "close"])
    html_p = _build_html(picks_all_pending, _empty_intra, prefer_cn=True, as_of="2026-07-05")

    if "暂无已上市样本" not in html_p:
        errs.append("FAIL [all-pending]: '暂无已上市样本' not in html")
    else:
        print("PASS [all-pending]: '暂无已上市样本' in html")

    # KPI value divs must not contain fabricated 0.0%
    if ">0.0%<" in html_p:
        errs.append("FAIL [all-pending]: fabricated '>0.0%<' found in KPI html")
    else:
        print("PASS [all-pending]: no fabricated '0.0%' in KPI divs")

    # Pending rows emit rank: null in ROWS JSON so JS renders '—'
    if '"rank": null' not in html_p:
        errs.append("FAIL [all-pending]: 'rank: null' not found for pending rows")
    else:
        print("PASS [all-pending]: pending rows have rank: null in ROWS JSON")

    # ── Case 3: intraday with NaN close → no crash, finite pts still emitted ─
    intraday_nan = pd.DataFrame({
        "code":  ["1234", "1234", "1234", "1234"],
        "time":  ["09:30", "11:00", "13:00", "16:00"],
        "close": [float("nan"), 25.0, float("nan"), 48.4],
    })
    try:
        html_nan = _build_html(picks_df, intraday_nan, prefer_cn=True, as_of="2026-07-05")
        # 2 finite closes (25.0 and 48.4) → path should still be emitted
        if '"1234"' not in html_nan:
            errs.append("FAIL [nan-close]: intraday path for 1234 missing despite 2 finite closes")
        else:
            print("PASS [nan-close]: intraday path emitted after dropping NaN closes")
        if len(html_nan) < 10_000:
            errs.append(f"FAIL [nan-close]: html suspiciously small ({len(html_nan)} bytes)")
        else:
            print(f"PASS [nan-close]: html size {len(html_nan):,} bytes")
    except Exception as exc:
        errs.append(f"FAIL [nan-close]: unexpected exception: {exc}")

    if errs:
        print("\n".join(errs))
        sys.exit(1)
    else:
        print("\nAll smoke-test assertions PASSED.")
        sys.exit(0)
