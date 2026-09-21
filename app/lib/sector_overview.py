"""板块总览 Wave-2 Broadsheet Reskin
================================================

医疗/AI/板块页的「基准」多周期表 + 「涨跌榜」Wave-2 报纸精修:
- 新增 `masthead()`:完整 broadsheet masthead（双页各自传参，全参数化）。
- `benchmark_table()`:玻璃卡容器（rgba .5/blur14/白边，无顶 accent），透明 th + 墨 1.5px
  底线，行 hover rgba(26,26,26,.045)，节标+色阶图例。
- `movers()`:玻璃容器 + 双语列头 + 实符号 d1（N-9，替 abs()）+ rgba 轨道色。
- DOWN 颜色改 page-scope #c8102e（theme.DOWN 全局不动，SOVR13 先例）。

渲染机制不迁：纯 st.markdown(unsafe_allow_html)，无 iframe / echarts / JS。
Sparkline 保持 inline SVG（cross-cutting INVARIANT #4：多小图面禁换 echarts）。
@keyframes pulseDot + tr hover 规则经 <style> 块注入，idempotent。

双页共用（2_Healthcare.py + a2_ai_overview.py）—— 验收两页均需核（SOVR1）。
调用页各自调 `theme.page_radial_wash(1240)` 提供 blur 垫底（SOVR4/D5，非本模块职责）。

典型调用（wave-2 之后）:
    from lib import sector_overview as so

    theme.page_radial_wash(1240)           # 调用页自行注入 wash

    so.masthead(
        title="板块总览 · 医疗健康",
        chip="HEALTHCARE",
        subtitle="基准 ETF 分档表现 × 涨跌榜 · 30 日趋势 · 相对标普超额",
        asof="2026-06-30",
        source="Yahoo Finance cron EOD",
        prefer_cn=True,
    )
    so.benchmark_table([
        {"tk": "XLV", "name": "医疗保健精选行业",
         "periods": {"1日": 3.0, "5日": 7.8, "1月": 8.2, "3月": 10.5, "YTD": 4.0},
         "rel_sp": -3.2, "spark": [...30 raw closes...]},
    ], source="来源 Yahoo Finance cron EOD · 截至 2026-06-30 · 仅供参考")

    so.movers(
        gainers=[{"tk": "XBI", "name": "生物科技", "last": 70.70, "d1": 20.1}],
        losers=[{"tk": "3696 HK", "name": "英矽智能", "last": 38.22, "d1": -16.0}],
        window="1 日",
        prefer_cn=True,
    )

周期列顺序由第一行 periods 的 key 顺序决定（用 dict 保序；统一传同一组 key）。
rel_cap / mov_cap 控制色阶与发散条饱和上限（默认 ±25pp / 22pp）。
"""
from __future__ import annotations

import math
import zlib
from html import escape as _esc

import streamlit as st

from lib import i18n
from lib import theme as t

# ── Page-scope DOWN color for wave-2 reskin surfaces (SOVR13) ────────────────
# theme.DOWN stays #cc0000 (signal-red, global token unchanged).
# This module uses brand red #c8102e per §0 D2 — same pattern as candlestick
# module (_DOWN = theme.CMSI_RED). The per-surface constant keeps the global clean.
_DOWN = t.CMSI_RED       # "#c8102e"
_DOWN_RGB = "200,16,46"  # for rgba() tint/track calculations

REL_CAP = 25.0  # 相对条 / 期间色阶饱和上限 ±pp  (spec: cap 25 → 50%)
MOV_CAP = 22.0  # mover 动量条饱和上限 (spec: cap 22)


# ── CSS injection (pulseDot keyframes + tr hover) ────────────────────────────

def _inject_css() -> None:
    """Inject @keyframes pulseDot + sovr-row hover rule.
    Idempotent — Streamlit rerenders call this every time, same CSS overwrites itself.
    """
    st.markdown(
        """<style>
@keyframes pulseDot {
  0%,100% { opacity:1; transform:scale(1); }
  50% { opacity:.35; transform:scale(.82); }
}
tr.sovr-row:hover { background:rgba(26,26,26,.045) !important; }

/* ── 可展开板块行(accordion, SOVR15) ──────────────────────────────────────
   母行 = <summary>(display:grid, 与表头同 grid-template) ; 成分面板 = <details> body。
   原生 <details>/<summary>,无 JS —— 同 lib/ipo_detail.py 既有模式。
   open 态用 inset box-shadow 画左红条(非 border-left),避免 grid 列位移。 */
details.sovr-acc > summary { list-style:none; cursor:pointer; }
details.sovr-acc > summary::-webkit-details-marker { display:none; }
details.sovr-acc > summary:hover { background:rgba(26,26,26,.045); }
details.sovr-acc[open] > summary { background:rgba(26,26,26,.030);
  box-shadow:inset 3px 0 0 #c8102e; }
.sovr-caret { transition:transform .16s ease; display:inline-block; }
details.sovr-acc[open] > summary .sovr-caret { transform:rotate(90deg); }
.sovr-mrow:hover { background:rgba(26,26,26,.035); }

/* ── 成分地区过滤 chips (SOVR16) ─────────────────────────────────────────
   纯 CSS：hidden checkbox + label + :has() —— 无 JS、无 rerun，所以筛选时
   已展开的面板不会塌掉（Streamlit 原生控件会 rerun 重建 DOM，<details> 的
   open 态会全部丢失，实测）。逐次渲染的过滤规则由 _acc_filter_css() 生成。 */
/* display 必须由 class 承担：写成内联 style 的话过滤规则(display:none)压不过它。 */
.sovr-m { display:grid; }
.sovr-empty { display:none; }
.sovr-filtered { display:none; color:#c8102e; }
.sovr-chip { cursor:pointer; display:inline-block; font-family:'JetBrains Mono','IBM Plex Mono','SF Mono',monospace;
  font-size:10px; letter-spacing:.06em; color:#4a4a4a; background:rgba(255,255,255,.55);
  border:1px solid #e4d2bd; border-radius:2px; padding:3px 9px; margin-right:6px;
  transition:background .12s ease,color .12s ease,border-color .12s ease; user-select:none; }
.sovr-chip:hover { border-color:#d4c4b0; background:rgba(255,255,255,.85); }
.sovr-f:checked + .sovr-chip { background:#c8102e; color:#fff; border-color:#c8102e; }
.sovr-panel::-webkit-scrollbar { width:8px; }
.sovr-panel::-webkit-scrollbar-thumb { background:#d4c4b0; border-radius:4px; }
</style>""",
        unsafe_allow_html=True,
    )


# ── Internal helpers ─────────────────────────────────────────────────────────

def _is_missing(v) -> bool:
    """True when v is None or NaN — used by all helpers to emit honest empty state."""
    return v is None or (isinstance(v, float) and math.isnan(v))


def _tint(v, cap: float = REL_CAP) -> str:
    """Diverging background tint: teal=up / #c8102e=down, alpha capped at 0.16.
    Dead-zone: |v| < 0.05 or missing returns transparent (SOVR9).
    """
    if _is_missing(v) or abs(v) < 0.05:
        return "transparent"
    a = min(abs(v) / cap, 1.0) * 0.16
    rgb = "13,118,128" if v > 0 else _DOWN_RGB
    return f"rgba({rgb},{a:.3f})"


def _pct_parts(v) -> tuple[str, str]:
    """(inner_html, background) for one period-return cell — shared by td / grid cell."""
    if _is_missing(v):
        return f'<span style="color:{t.INK_3}">—</span>', "transparent"
    gly = "▲" if v > 0 else ("▼" if v < 0 else "·")
    sign = "+" if v > 0 else ""
    col = t.UP if v > 0 else (_DOWN if v < 0 else t.INK_3)
    return (f'<span style="color:{col};font-weight:600">{gly} {sign}{v:.1f}%</span>',
            _tint(v))


def _pct_cell(v) -> str:
    """Period return cell: ▲/▼/· glyph + signed pct + diverging tint bg (SOVR9).
    v=None/NaN → em-dash grey cell, no glyph, transparent bg.
    """
    inner, bg = _pct_parts(v)
    return (
        f'<td style="text-align:right;white-space:nowrap;padding:0 12px;'
        f'border-bottom:1px solid {t.PAPER_RULE};background:{bg}">{inner}</td>'
    )


def _spark_svg(vals, w: int = 110, h: int = 28, pad: int = 3) -> tuple[str, bool]:
    """30D sparkline: polyline stroke-width 1.5 non-scaling + endpoint circle r2.2.
    Geometry identical to wave-1 _spark_svg; only down color switches to _DOWN (SOVR9).
    Returns (svg_html, is_up).
    """
    vals = [float(x) for x in (vals or [])]
    if len(vals) < 2:
        return f'<span style="color:{t.INK_3}">—</span>', True
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    step = (w - 2) / (len(vals) - 1)
    pts = " ".join(
        f"{1 + i * step:.1f},{pad + (h - 2 * pad) - (v - lo) / rng * (h - 2 * pad):.1f}"
        for i, v in enumerate(vals)
    )
    up = vals[-1] >= vals[0]
    color = t.UP if up else _DOWN
    lx, ly = pts.rsplit(" ", 1)[-1].split(",")
    svg = (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:{w}px;height:26px;display:block;vertical-align:middle">'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<circle cx="{lx}" cy="{ly}" r="2.2" fill="{color}"/></svg>'
    )
    return svg, up


def _rel_bar(v, cap: float = REL_CAP) -> str:
    """Center-diverging relative-to-SPX bar (SOVR9).
    Track: #f4ead9 h14; center 1px #d4c4b0; fill extends from center to ±50%.
    Down color: _DOWN (#c8102e). Geometry unchanged from wave-1.
    v=None/NaN → empty state: track + centre line visible, no fill, '—' grey label.
    """
    return (
        f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">'
        f'{_rel_parts(v, cap)}</td>'
    )


def _rel_parts(v, cap: float = REL_CAP, *, h: int = 14, lw: int = 54,
               fs: int = 12, stretch: bool = False) -> str:
    """Inner flex(track + centre line + fill + label) of the relative bar.
    Shared by the <td> wrapper and the grid cell; h/lw/fs shrink it for member rows.
    stretch=True adds width:100% (needed inside a flex grid cell; a <td> child
    block already fills the cell, so the default keeps the <table> path byte-identical).
    """
    _w = ";width:100%" if stretch else ""
    if _is_missing(v):
        return (
            f'<div style="display:flex;align-items:center;gap:8px{_w}">'
            f'<div style="flex:1;position:relative;height:{h}px;background:#f4ead9">'
            f'<div style="position:absolute;top:0;bottom:0;left:50%;width:1px;'
            f'background:{t.PAPER_EDGE}"></div></div>'
            f'<span style="font-family:{t.FONT_MONO};font-size:{fs}px;font-weight:700;'
            f'color:{t.INK_3};width:{lw}px;text-align:right;white-space:nowrap">—</span>'
            f'</div>'
        )
    w = min(abs(v) / cap, 1.0) * 50
    color = t.UP if v >= 0 else _DOWN
    fill = f"left:50%;width:{w:.1f}%" if v >= 0 else f"right:50%;width:{w:.1f}%"
    gly = "▲ +" if v >= 0 else "▼ "
    return (
        f'<div style="display:flex;align-items:center;gap:8px{_w}">'
        f'<div style="flex:1;position:relative;height:{h}px;background:#f4ead9">'
        f'<div style="position:absolute;top:0;bottom:0;left:50%;width:1px;'
        f'background:{t.PAPER_EDGE}"></div>'
        f'<div style="position:absolute;top:2px;bottom:2px;{fill};'
        f'background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:{fs}px;font-weight:700;'
        f'color:{color};width:{lw}px;text-align:right;white-space:nowrap">{gly}{v:.1f}</span>'
        f'</div>'
    )


# ── 可展开板块行 accordion (SOVR15) ──────────────────────────────────────────
# 「板块 · Sub-sectors」表的母行 = 我方自建等权篮子(CMSI Focus)，点开看篮子里有谁。
# 表格无法在无 JS 下让 <tr> 切换兄弟 <tr>，故带成分的表改走 CSS grid + 原生
# <details>/<summary>（lib/ipo_detail.py 已验证的机制，st.markdown 不被 sanitize 掉）。
# 表头 / 母行 / 成分行共用同一 grid-template → 列严格对齐，视觉与 <table> 版一致。
# 不带 members 的调用（基准 ETF 表 / AI 页）仍走原 <table> 分支，零回归。
_ACC_PCT_W = 92          # 期间列宽(px) —— "▲ +31.3%" @13px + 左右 12px padding
_ACC_REL_W = 172         # 相对标普列宽 = 发散条 + 54px 标签
_ACC_SCROLL_AT = 12      # 成分数 > 此值 → 面板内部滚动
_ACC_SCROLL_H = 420      # 滚动面板最大高(px)
# 地区 chips 的渲染顺序；译名复用板块热力图的 heat.tbl.region.* 键
_REGION_ORDER = ("US", "HK", "CN", "JP", "KR")


def _acc_grid(n_periods: int) -> str:
    """表头 / 母行 / 成分行共用的 grid-template-columns。"""
    return (f"136px minmax(150px,1fr) 134px "
            f"repeat({n_periods},{_ACC_PCT_W}px) {_ACC_REL_W}px")


def _acc_cell(inner: str, *, align: str = "left", bg: str = "transparent",
              pad_left: int = 12, extra: str = "") -> str:
    """一个 grid 单元：拉伸到整行高(色阶底满格) + 垂直居中 + 行底 hairline。"""
    just = {"left": "flex-start", "right": "flex-end", "center": "center"}[align]
    return (f'<div style="display:flex;align-items:center;justify-content:{just};'
            f'padding:0 12px 0 {pad_left}px;border-bottom:1px solid {t.PAPER_RULE};'
            f'background:{bg};min-width:0;{extra}">{inner}</div>')


def _acc_head(tk_label: str, periods: list[str]) -> str:
    """表头行 —— 与 <table> 版 _TH 同款(透明底、mono 灰、墨 1.5px 底线)。"""
    def th(label: str, align: str = "right") -> str:
        just = {"left": "flex-start", "right": "flex-end", "center": "center"}[align]
        return (f'<div style="display:flex;align-items:center;justify-content:{just};'
                f'font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.08em;'
                f'text-transform:uppercase;font-weight:600;color:{t.INK_3};'
                f'background:transparent;padding:9px 12px;'
                f'border-bottom:1.5px solid {t.INK}">{_esc(label)}</div>')
    cells = (th(tk_label, "left") + th("名称", "left") + th("趋势 30D", "left")
             + "".join(th(p) for p in periods) + th("相对标普 PP", "center"))
    return cells


def _acc_summary(r: dict, periods: list[str], *, expandable: bool) -> str:
    """母行单元（46px，与 <table> 版行高/字重一致）。带成分时首列多一个 ▸ caret。"""
    svg, _ = _spark_svg(r.get("spark"))
    caret = (f'<span class="sovr-caret" style="color:{t.CMSI_RED};font-size:10px;'
             f'line-height:1">▸</span>' if expandable else
             '<span style="width:6px;display:inline-block"></span>')
    tk = (f'<div style="display:flex;align-items:center;gap:6px;white-space:nowrap;'
          f'font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};font-size:12px;'
          f'letter-spacing:.04em">{caret}<span>{_esc(r["tk"])}</span></div>')
    name = (f'<span style="color:{t.INK};font-weight:500;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis">{_esc(r["name"])}</span>')
    cells = (
        _acc_cell(tk, extra="height:46px")
        + _acc_cell(name, extra="height:46px")
        + _acc_cell(svg, extra="height:46px")
    )
    for p in periods:
        inner, bg = _pct_parts(r["periods"].get(p))
        cells += _acc_cell(inner, align="right", bg=bg,
                           extra="white-space:nowrap;height:46px")
    cells += _acc_cell(_rel_parts(r.get("rel_sp"), stretch=True),
                       extra="height:46px")
    return cells


def _acc_member(m: dict, periods: list[str]) -> str:
    """一支成分行（32px，字号降一档、首列缩进，读作母行下钻）。"""
    chip = ""
    if m.get("secondary"):
        chip = (f'<span style="font-family:{t.FONT_MONO};font-size:9px;color:{t.INK_3};'
                f'border:1px solid {t.PAPER_EDGE_SOFT};border-radius:2px;'
                f'padding:0 4px;margin-left:6px;flex:none">A/H</span>')
    tk = (f'<span style="font-family:{t.FONT_MONO};font-weight:600;color:{t.INK_2};'
          f'font-size:11px;letter-spacing:.03em;white-space:nowrap;overflow:hidden;'
          f'text-overflow:ellipsis">{_esc(m["tk"])}</span>')
    name = (f'<span style="color:{t.INK_2};font-size:12px;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis">{_esc(m["name"])}</span>{chip}')
    cells = (
        _acc_cell(tk, pad_left=34, extra="height:32px")
        + _acc_cell(name, extra="height:32px")
        + _acc_cell("", extra="height:32px")
    )
    for p in periods:
        inner, bg = _pct_parts(m.get("periods", {}).get(p))
        cells += _acc_cell(f'<span style="font-size:12px">{inner}</span>', align="right",
                           bg=bg, extra="white-space:nowrap;height:32px")
    cells += _acc_cell(_rel_parts(m.get("rel_sp"), h=10, lw=54, fs=11, stretch=True),
                       extra="height:32px")
    return cells


def _acc_panel(r: dict, periods: list[str], grid: str, prefer_cn: bool,
               pid: str) -> str:
    """展开后的成分面板：说明行 + 逐支成分（页面侧已按 YTD 降序排好）。"""
    members = r.get("members") or []
    n = len(members)
    cap = (f"成分 · {n} 家 · 等权 · 按 YTD 降序"
           if prefer_cn else f"Constituents · {n} · equal-weight · sorted by YTD")
    # 筛选态提示：说明行的「N 家」是全篮子口径，筛完屏幕上行数会少于 N —— 不提示
    # 就会被读成「篮子缩水了」。纯 CSS 显隐，不需要重新计数。
    fl = ("· 已按地区筛选清单，母行与本行的 N 仍为全篮子口径"
          if prefer_cn else "· list filtered by region; N above is still the full basket")
    cap_html = (f'<div style="font-family:{t.FONT_MONO};font-size:10px;'
                f'letter-spacing:.08em;color:{t.INK_3};padding:8px 12px 6px 34px">'
                f'{_esc(cap)} <span class="sovr-filtered">{_esc(fl)}</span></div>')
    rows_html = "".join(
        f'<div class="sovr-mrow sovr-m {_r_cls(m.get("region"))}" '
        f'style="grid-template-columns:{grid};'
        f'align-items:stretch">{_acc_member(m, periods)}</div>'
        for m in members
    )
    empty_txt = "该地区无成分" if prefer_cn else "No constituents in this region"
    empty_html = (f'<div class="sovr-empty" style="font-size:12px;'
                  f'color:{t.INK_3};padding:10px 12px 12px 34px">{_esc(empty_txt)}</div>')
    scroll = (f"max-height:{_ACC_SCROLL_H}px;overflow-y:auto;"
              if n > _ACC_SCROLL_AT else "")
    return (f'<div class="sovr-panel" id="{pid}" '
            f'style="background:rgba(255,255,255,.34);'
            f'border-bottom:1px solid {t.PAPER_RULE};{scroll}overflow-x:hidden">'
            f'{cap_html}{rows_html}{empty_html}</div>')


def _r_cls(code) -> str:
    """region code → CSS class（非字母数字一律剔除，code 直接进选择器/ID）。"""
    c = "".join(ch for ch in str(code or "") if ch.isalnum())
    return f"r-{c}" if c else ""


def _acc_filter_bar(uid: str, regions: list[tuple[str, str]], prefer_cn: bool) -> str:
    """地区 chips 条：hidden checkbox + label，纯 CSS 多选，无 rerun。"""
    chips = "".join(
        f'<input class="sovr-f" type="checkbox" id="sovr-f-{uid}-{code}" hidden>'
        f'<label for="sovr-f-{uid}-{code}" class="sovr-chip">{_esc(label)}</label>'
        for code, label in regions
    )
    title = "筛选成分" if prefer_cn else "FILTER"
    hint = "未选 = 全部 · 母行口径不变" if prefer_cn else "none selected = all · aggregates unchanged"
    return (
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;'
        f'padding:9px 12px 8px">'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.08em;'
        f'text-transform:uppercase;color:{t.INK_3};font-weight:600">{_esc(title)}</span>'
        f'<span>{chips}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:9px;color:{t.INK_3};'
        f'margin-left:auto">{_esc(hint)}</span>'
        f'</div>'
    )


def _acc_filter_css(uid: str, regions: list[tuple[str, str]],
                    panel_regions: list[tuple[str, set[str]]]) -> str:
    """本次渲染的过滤规则。

    · 任一 chip 勾中 → 先隐藏全部成分行，再按勾中的地区逐条放回（并集语义）。
      放回规则多一个 id + 一个 class，特异性天然高于隐藏规则，不需要 !important。
    · 空态：某面板的地区集合与勾中集合不相交时显示「该地区无成分」——面板的地区
      集合在渲染时已知，所以一条规则里把该面板拥有的地区逐个 :not(:has()) 串起来
      即可，不需要枚举组合。
    """
    w = f"#sovr-w-{uid}"
    out = [f'{w}:has(.sovr-f:checked) .sovr-m{{display:none}}',
           f'{w}:has(.sovr-f:checked) .sovr-filtered{{display:inline}}']
    for code, _ in regions:
        out.append(f'{w}:has(#sovr-f-{uid}-{code}:checked) .sovr-m.r-{code}'
                   f'{{display:grid}}')
    for pid, codes in panel_regions:
        if not codes:
            continue
        nots = "".join(f':not(:has(#sovr-f-{uid}-{c}:checked))' for c in sorted(codes))
        out.append(f'{w}:has(.sovr-f:checked){nots} #{pid} .sovr-empty{{display:block}}')
    return "<style>" + "".join(out) + "</style>"


def _render_accordion(rows: list[dict], periods: list[str], tk_label: str,
                      prefer_cn: bool,
                      region_labels: dict[str, str] | None = None) -> str:
    """整张可展开表的 HTML（可选地区 chips + 表头 + 各行 <details>）。"""
    grid = _acc_grid(len(periods))
    uid = f"{zlib.crc32(tk_label.encode()) % 100000:05d}"
    if region_labels is None:
        region_labels = {c: i18n.t(f"heat.tbl.region.{c}") for c in _REGION_ORDER}

    # 成分里实际出现的地区（按 region_labels 给定顺序），决定 chips 渲不渲染
    present = {_r_cls(m.get("region"))[2:] for r in rows
               for m in (r.get("members") or []) if _r_cls(m.get("region"))}
    regions = [(c, lbl) for c, lbl in (region_labels or {}).items() if c in present]

    head = (f'<div style="display:grid;grid-template-columns:{grid}">'
            f'{_acc_head(tk_label, periods)}</div>')
    out = [_acc_filter_bar(uid, regions, prefer_cn) if regions else "", head]
    panel_regions: list[tuple[str, set[str]]] = []
    for i, r in enumerate(rows):
        members = r.get("members") or []
        summary_cells = _acc_summary(r, periods, expandable=bool(members))
        row_grid = (f'display:grid;grid-template-columns:{grid};align-items:stretch')
        if not members:
            out.append(f'<div class="sovr-mrow" style="{row_grid}">{summary_cells}</div>')
            continue
        pid = f"sovr-p-{uid}-{i}"
        panel_regions.append(
            (pid, {_r_cls(m.get("region"))[2:] for m in members if _r_cls(m.get("region"))}))
        out.append(
            f'<details class="sovr-acc">'
            f'<summary style="{row_grid}">{summary_cells}</summary>'
            f'{_acc_panel(r, periods, grid, prefer_cn, pid)}'
            f'</details>'
        )
    css = _acc_filter_css(uid, regions, panel_regions) if regions else ""
    return (f'{css}<div id="sovr-w-{uid}" style="overflow-x:auto;font-size:13px;'
            f'font-variant-numeric:tabular-nums lining-nums;'
            f'font-family:{t.FONT_DISPLAY}">{"".join(out)}</div>')


# ── Public API ───────────────────────────────────────────────────────────────

def masthead(
    title: str,
    chip: str,
    subtitle: str,
    *,
    asof: str | None = None,
    source: str | None = None,
    prefer_cn: bool = True,
) -> None:
    """Broadsheet masthead (wave-2 新增块, SOVR2/SOVR3).

    Parameters
    ----------
    title    : e.g. "板块总览 · 医疗健康" / "板块总览 · AI 科技"
    chip     : domain label, e.g. "HEALTHCARE" / "AI TECH"
    subtitle : caption line, e.g. "基准 ETF 分档表现 × 涨跌榜 · 30 日趋势 · 相对标普超额"
    asof     : date string, e.g. "2026-06-30" — appears in dateline
    source   : provenance string, e.g. "Yahoo Finance cron EOD"
    prefer_cn: True → "EOD · 收盘", False → "EOD · CLOSE" (SOVR3, D3 compliant)

    Design: left = red bar 5×48 + title 30px/700 + chip + subtitle.
            right = teal pulseDot 8px + EOD label + dateline mono 11.
            border-bottom 2px #1a1a1a, pb16.
    Note: caller page must have called theme.page_radial_wash(1240) first so
          backdrop-filter has something to blur (SOVR4/D5).
    """
    _inject_css()
    eod_label = "EOD · 收盘" if prefer_cn else "EOD · CLOSE"

    # Dateline: "截至 {asof} · {source}" or en equivalent
    dateline_parts: list[str] = []
    if asof:
        prefix = "截至" if prefer_cn else "As of"
        dateline_parts.append(f"{prefix} {_esc(asof)}")
    if source:
        dateline_parts.append(_esc(source))
    dateline_html = (
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;'
        f'color:{t.INK_3};margin-top:5px">{"  ·  ".join(dateline_parts)}</div>'
    ) if dateline_parts else ""

    right_col = (
        f'<div style="text-align:right;display:flex;flex-direction:column;'
        f'align-items:flex-end">'
        # teal pulseDot + EOD label (SOVR3: cyan semantic = EOD snapshot, not live)
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<div style="width:8px;height:8px;border-radius:50%;background:{t.UP};'
        f'flex:none;animation:pulseDot 1.5s ease-in-out infinite"></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.UP};font-weight:600">'
        f'{_esc(eod_label)}</span></div>'
        f'{dateline_html}'
        f'</div>'
    )

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:flex-end;'
        f'gap:24px;border-bottom:2px solid {t.INK};padding-bottom:16px">'
        # left: red bar + title block
        f'<div style="display:flex;align-items:flex-start;gap:12px">'
        f'<div style="width:5px;height:48px;background:{t.CMSI_RED};'
        f'border-radius:1px;flex:none;margin-top:2px"></div>'
        f'<div>'
        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
        f'<div style="font-family:{t.FONT_DISPLAY};font-size:30px;font-weight:700;'
        f'letter-spacing:-0.01em;color:{t.INK};line-height:1.1">{_esc(title)}</div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:13px;font-weight:600;'
        f'color:{t.INK_3};border:1px solid {t.PAPER_EDGE_SOFT};padding:3px 9px;'
        f'border-radius:2px">{_esc(chip)}</span>'
        f'</div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;letter-spacing:.08em;'
        f'color:{t.INK_3};margin-top:6px">{_esc(subtitle)}</div>'
        f'</div></div>'
        # right
        f'{right_col}'
        f'</div>',
        unsafe_allow_html=True,
    )


def benchmark_table(rows: list[dict], *, source: str | None = None,
                    section_label: str = "基准 · Benchmark ETF",
                    tk_label: str = "Ticker", prefer_cn: bool = True,
                    region_labels: dict[str, str] | None = None) -> None:
    """基准多周期表 + sparkline + 发散色阶 + 相对标普发散条 (wave-2 glass reskin).

    Row dict: {tk, name, periods:{label:pct,...}, rel_sp(float pp), spark:[~30 closes]}.
    Period column order follows first row's periods key order (caller passes identical keys).
    section_label / tk_label: 复用本表做「板块汇总」等非基准表时可改小节头与首列头
    （默认值 = 原基准表，既有调用零回归）。

    可展开（SOVR15）：行可带 `members: [{tk, name, periods, rel_sp, secondary?}, ...]`
    —— 该行即渲染成可点开的 <details>，展开后列出这只自建等权篮子的全部成分，
    列与母行严格对齐。**任一行带 members 时整表改走 grid 分支**（<tr> 无 JS 无法
    切换兄弟行）；所有行都不带 members 时走原 <table> 分支，输出逐字节不变。
    成分排序由调用页决定（本函数不排序）。prefer_cn 影响成分面板说明行与 chips 文案。

    region_labels（SOVR16）：{code: label}，缺省 = 本模块按 _REGION_ORDER 自取
    heat.tbl.region.* 译名（与板块热力图同一批 code、同一套文案）。只渲染成分里
    实际出现的 code，顺序即给定顺序。**不要把它改回必传的调用方参数**：
    Streamlit(本地与 Cloud 皆然)的热进程会缓存已 import 的 lib 模块，新 page 撞
    旧 lib 时多传一个 kwarg 就是 TypeError 整页崩 —— 2026-09-21 线上实撞过一次。
    新增能力优先走 rows 数据或模块内默认值，不动调用方签名。
    过滤是纯 CSS（hidden checkbox + :has()）—— 无 JS、无 rerun，所以筛选不会把已展开的面板塌掉；
    Streamlit 原生控件做不到这点。**只筛成分清单，母行聚合口径不变**（George
    2026-09-21 裁定）：筛到港股不会把「制药 · 35」改写成「制药 · 8」。
    """
    _inject_css()
    if not rows:
        return
    periods = list(rows[0]["periods"].keys())

    # ── Section header + right-float color legend (SOVR5) ─────────────────
    legend = (
        f'<div style="display:flex;align-items:center;gap:5px;margin-left:auto">'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;font-weight:600;'
        f'color:{_DOWN}">跌</span>'
        f'<div style="width:120px;height:9px;border:1px solid {t.PAPER_EDGE};'
        f'background:linear-gradient(to right,{_DOWN},#f7d9d9,#fff1e5,#d9e8e6,{t.UP})">'
        f'</div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;font-weight:600;'
        f'color:{t.UP}">涨</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:9px;color:{t.INK_3};'
        f'margin-left:4px">期间收益色阶</span>'
        f'</div>'
    )
    sec_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:22px 0 10px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block;border-radius:1px;flex:none"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.INK};font-weight:600">'
        f'{_esc(section_label)}</span>'
        f'{legend}</div>'
    )

    # ── Table header cells (SOVR7): transparent bg, mono gray, ink 1.5px bottom ──
    _TH = (
        f"font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.08em;"
        f"text-transform:uppercase;font-weight:600;color:{t.INK_3};"
        f"background:transparent;padding:9px 12px;"
        f"border-bottom:1.5px solid {t.INK};"
    )

    def _th(label: str, align: str = "right") -> str:
        # no vertical separators (SOVR7: 零竖分隔线)
        return f'<th style="{_TH}text-align:{align}">{_esc(label)}</th>'

    head = (
        _th(tk_label, "left")
        + _th("名称", "left")
        + _th("趋势 30D", "left")
        + "".join(_th(p) for p in periods)
        + _th("相对标普 PP", "center")
    )

    # ── 可展开分支（任一行带 members）：grid + 原生 <details>，列同表头 ──────
    if any(r.get("members") for r in rows):
        glass_style = (
            "background:rgba(255,255,255,.5);"
            "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
            "border:1px solid rgba(255,255,255,.7);"
            "padding:2px 16px 8px;overflow:hidden;"
        )
        src_html = (
            f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};'
            f'margin-top:8px">{_esc(source)}</div>'
        ) if source else ""
        st.markdown(
            f"{sec_head}"
            f'<div style="{glass_style}">'
            f'{_render_accordion(rows, periods, tk_label, prefer_cn, region_labels)}'
            f'</div>{src_html}',
            unsafe_allow_html=True,
        )
        return

    # ── Table body rows (SOVR8/SOVR9) ────────────────────────────────────
    body: list[str] = []
    for r in rows:
        svg, _ = _spark_svg(r.get("spark"))
        cells = (
            # Ticker: mono 12/700 (SOVR8)
            f'<td style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};'
            f'font-size:12px;letter-spacing:.04em;text-align:left;padding:0 12px;'
            f'height:46px;border-bottom:1px solid {t.PAPER_RULE}">{_esc(r["tk"])}</td>'
            # 名称: 500 weight (SOVR8)
            f'<td style="text-align:left;color:{t.INK};font-weight:500;padding:0 12px;'
            f'border-bottom:1px solid {t.PAPER_RULE}">{_esc(r["name"])}</td>'
            # sparkline SVG
            f'<td style="padding:0 12px;border-bottom:1px solid {t.PAPER_RULE}">{svg}</td>'
            + "".join(_pct_cell(r["periods"][p]) for p in periods)
            + _rel_bar(r["rel_sp"])
        )
        # class="sovr-row" enables the CSS hover rule injected by _inject_css()
        body.append(f'<tr class="sovr-row">{cells}</tr>')

    src_html = (
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};'
        f'margin-top:8px">{_esc(source)}</div>'
    ) if source else ""

    # ── Glass container (SOVR6): rgba .5 + blur14 + white border, no top accent ──
    glass_style = (
        "background:rgba(255,255,255,.5);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "border:1px solid rgba(255,255,255,.7);"
        "padding:2px 16px 8px;overflow:hidden;"
    )
    st.markdown(
        f"{sec_head}"
        f'<div style="{glass_style}">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;'
        f'font-variant-numeric:tabular-nums lining-nums;font-family:{t.FONT_DISPLAY}">'
        f'<thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        f'</table></div>{src_html}',
        unsafe_allow_html=True,
    )


def _mover_row(m: dict, up: bool) -> str:
    """Single mover row with momentum bar and real-signed d1 (N-9, SOVR10).

    N-9: design shows '▼ -16.0%' — negative sign preserved (replacing old abs()).
    Row layout: tk w64 / name flex / last w60 / bar 84×16 / d1 w58.
    """
    color = t.UP if up else _DOWN
    track = "rgba(13,118,128,.10)" if up else f"rgba({_DOWN_RGB},.08)"
    bar_anchor = "left:0" if up else "right:0"
    d1 = m.get("d1")
    if _is_missing(d1):
        w = 0
        d1_display = "—"
        color = t.INK_3   # neutral grey for missing magnitude
    else:
        w = min(abs(d1) / MOV_CAP, 1.0) * 100
        # N-9: gainers "▲ +x.x%", losers "▼ -x.x%" (d1 is already negative for losers)
        if up:
            d1_display = f"▲ +{abs(d1):.1f}%"
        else:
            d1_display = f"▼ {d1:.1f}%"   # d1 < 0, %.1f keeps the minus sign
    return (
        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;'
        f'border-bottom:1px solid {t.PAPER_RULE}">'
        f'<span style="font-family:{t.FONT_MONO};font-weight:700;color:{t.INK};'
        f'font-size:12px;width:64px;flex:none">{_esc(m["tk"])}</span>'
        f'<span style="color:{t.INK};font-size:13px;flex:1;min-width:0;overflow:hidden;'
        f'text-overflow:ellipsis;white-space:nowrap">{_esc(m["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;color:{t.INK_2};'
        f'width:60px;text-align:right;flex:none">{m["last"]:.2f}</span>'
        f'<div style="width:84px;flex:none;position:relative;height:16px;'
        f'background:{track}">'
        f'<div style="position:absolute;{bar_anchor};top:2px;bottom:2px;'
        f'width:{w:.0f}%;background:{color}"></div></div>'
        f'<span style="font-family:{t.FONT_MONO};font-size:13px;font-weight:700;'
        f'color:{color};width:58px;text-align:right;flex:none">'
        f'{_esc(d1_display)}</span></div>'
    )


def movers(
    *,
    gainers: list[dict],
    losers: list[dict],
    window: str = "1 日",
    prefer_cn: bool = True,
) -> None:
    """涨跌榜 — wave-2 glass reskin with bilingual column headers (SOVR10/SOVR14).

    Parameters
    ----------
    gainers   : [{tk, name, last, d1}, ...] — d1 in real signed percent
    losers    : [{tk, name, last, d1}, ...] — d1 negative for losers
    window    : period label, e.g. "1 日" / "1D"
    prefer_cn : True → subtitle in Chinese, False → English
    """
    _inject_css()
    # Section header subtitle
    subtitle = (
        f"{_esc(window)}涨跌幅前 10" if prefer_cn else f"Top 10 by {_esc(window)} change"
    )
    sec_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:34px 0 4px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block;border-radius:1px;flex:none"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;letter-spacing:.16em;'
        f'text-transform:uppercase;color:{t.INK};font-weight:600">'
        f'涨跌榜 · Movers</span>'
        f'<span style="font-size:12px;color:{t.INK_3}">{subtitle}</span>'
        f'</div>'
    )

    # Glass container (same formula as benchmark_table, no padding per spec)
    glass_style = (
        "background:rgba(255,255,255,.5);"
        "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        "border:1px solid rgba(255,255,255,.7);"
        "overflow:hidden;"
    )

    def _col_html(col_title: str, items: list[dict], up: bool, accent: str) -> str:
        # Column header: vertical bar 3×13 + mono 11/700/.1em bilingual label (SOVR10)
        col_head = (
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">'
            f'<span style="width:3px;height:13px;background:{accent};'
            f'display:inline-block;border-radius:1px;flex:none"></span>'
            f'<span style="font-family:{t.FONT_MONO};font-size:11px;font-weight:700;'
            f'letter-spacing:.1em;color:{accent}">{_esc(col_title)}</span></div>'
        )
        rows_html = "".join(_mover_row(m, up) for m in items)
        return (
            f'<div>{col_head}'
            f'<div style="{glass_style}">{rows_html}</div></div>'
        )

    # Bilingual column labels (CN · EN in one label — works for both lang modes)
    gain_title = "涨幅前 10 · GAINERS"
    lose_title = "跌幅前 10 · LOSERS"

    st.markdown(
        f"{sec_head}"
        f'<div style="display:grid;grid-template-columns:1fr 1fr;'
        f'gap:20px;margin-top:14px">'
        f'{_col_html(gain_title, gainers, True, t.UP)}'
        f'{_col_html(lose_title, losers, False, _DOWN)}'
        f'</div>',
        unsafe_allow_html=True,
    )
