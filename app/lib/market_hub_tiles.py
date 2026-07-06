"""指数瓦片 v2 · Market Hub 市场总览 — lib/market_hub_tiles.py
================================================================

取代 home Market Hub「市场总览」的 theme.kpi_metric 指数卡 ([01] KPI-B),
改为 FT 行情终端式「指数瓦片」strip:每个指数一格,含
  · 大号现价(JetBrains Mono 32px/700) + 当日涨跌(涨 teal / 跌 #c8102e page-scope)
  · 近 ~30 日收盘 **内联 SVG** 面积 sparkline(颜色随当日涨跌符号)
  · 52 周区间 micro-bar(当前价位置标记 2×9)
  · 1M / YTD 情境行(mono 10px uppercase)

v2(bold 升级 · 2026-06-30)在 v1 基础上加四轴,**不改 inline-SVG 决策**:
  · 头版:masthead 下加「市场速读」dek(真实 N 涨 M 跌 + 领涨/领跌,非编造)。
  · 贵感:收紧排版 + 强化层级 + hairline 网格。
  · 密度:dek 一行 + 瓦片内信息不变。
  · 动效:**纯入场动画**(不暗示实时)——
      - sparkline draw-in:polyline `pathLength="1"` + CSS stroke-dashoffset 1→0(SVG 内,非 echarts)。
      - 瓦片 staggered fade-rise(CSS animation-delay)。
      - 大号现价 count-up(极简 JS,从 0 数到 value_raw;无 value_raw 则静态)。
    入场动画 ≠ 实时徽标:数据仍是 EOD/cron,无 TRACKING/pulse(George 拍板)。

wave-2 精修(CONTRACT §2 HUB · 2026-07-04):
  · 玻璃容器:rgba(255,255,255,.55)+blur(14px)+白边+墨 3px 顶边,height:248px。
  · 字体:Space Grotesk 主字(body),JetBrains Mono 现价/eyebrow/情境行。
  · 跌色:page-scope #c8102e(_DOWN)。全局 theme.DOWN 不动(§0 D2)。
  · 背景水彩:双 radial 红/青渐变垫底(给玻璃 blur 提供可见前景)。
  · FONT_FACE_CSS 注入 srcdoc(无 Google Fonts CDN)。

整条 strip = 一个 st.iframe(self-contained srcdoc)。sparkline 用**内联 SVG**(非 echarts):
与 e1 ETF 卡 `_area_spark` / strategy_banner / sector_overview 同套路 —— 全站 sparkline 统一走 SVG。
⚠ 不用 echarts canvas:多张小图在 grid 列(初始 0 宽)里 echarts.init 会因 0 尺寸竞态画空白
  (单张 treemap 不受影响,故 [07] 仍用 echarts)。SVG 无加载/无尺寸竞态,bulletproof。
数据为真实值(bm.close_series 近30日收盘 + bench_df 行情),非 MOCK。

调用(home Market Hub「市场总览」):
    from lib import market_hub_tiles as mht
    tiles = build_tiles_from_benchmarks(bench_df)  # 每个 tile 见字段说明
    doc, h = mht.render_index_tiles(tiles, as_of=as_of_str, prefer_cn=True)
    st.iframe(doc, height=h)

字段(每个 tile):
  name(str) · value(已格式化 str) · value_raw(float|None,启用 count-up) · chg_pct(float|None,当日%) ·
  lo/hi(已格式化 52周低/高 str|None) · pos(0-1 现价在52周区间位置|None) ·
  m1/ytd(float|None,%) · spark(list[float],近~30收盘,<2 点则不画线)

设计约束(踩过坑的护栏):
- 大标题「行情中枢」由 home.py 的 theme.page_header 已渲染 —— 本 strip 从「市场总览」eyebrow 起。
- 无 实时跟踪/TRACKING 徽标(数据是 EOD/cron,非实时 —— George 拍板去掉)。入场动画不算实时。
- 跌色 #c8102e 仅本模块生效(_DOWN 常量);theme.DOWN=#cc0000 全局不动(CONTRACT §0 D2)。
- Sparkline 保持内联 SVG(禁换 echarts):HUB7 protected,0 宽竞态守卫。
"""
from __future__ import annotations

from lib import theme

# Page-scope exemption (CONTRACT §0 D2 / wave-2): wave-2 reskin surfaces use
# #c8102e for down-moves. theme.DOWN (#cc0000) is unchanged globally.
# Pattern mirrors candlestick _DOWN=theme.CMSI_RED (current-state §0 K, sector_overview.py).
_DOWN = theme.CMSI_RED


def _ret_color(v) -> str:
    """涨 teal / 跌 #c8102e(page-scope) / 缺失 墨。"""
    if v is None:
        return theme.INK_3
    return theme.UP if v >= 0 else _DOWN


def _ctx_span(lbl: str, v) -> str:
    """情境行一格:'1M -2.2%'(值按符号染色),缺失则灰 '—'。"""
    if v is None:
        return f'<span>{lbl} <b style="color:{theme.INK_3}">—</b></span>'
    col = _ret_color(v)
    return f'<span>{lbl} <b style="color:{col}">{v:+.1f}%</b></span>'


def _spark_svg(vals, chg, idx: int, *, w: int = 260, h: int = 46, pad: int = 4) -> str:
    """内联 SVG 面积 sparkline — height 46px, gradient opacity 涨.22/跌.20→.01, stroke 1.8px。
    width:100% + viewBox + preserveAspectRatio=none 自适应格宽;<2 点占位保高度。
    line 设 pathLength=1 + class=spk → CSS 用 stroke-dashoffset 1→0 做 draw-in(纯 CSS,无 JS)。"""
    vals = [float(v) for v in (vals or [])]
    if len(vals) < 2:
        return f'<div style="height:{h}px;margin-top:8px"></div>'
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    is_up = (chg is None or chg >= 0)
    col = theme.UP if is_up else _DOWN
    area_op = 0.22 if is_up else 0.20
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = [(pad + i * step, h - pad - (v - lo) / rng * (h - 2 * pad)) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{h - pad:.1f} {line} {pts[-1][0]:.1f},{h - pad:.1f}"
    lx, ly = pts[-1]
    gid = f"mht{idx}"
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:100%;height:{h}px;display:block;margin-top:8px">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{col}" stop-opacity="{area_op}"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0.01"/></linearGradient></defs>'
        f'<polygon class="spk-area" points="{area}" fill="url(#{gid})" stroke="none"/>'
        f'<polyline class="spk" pathLength="1" points="{line}" fill="none" stroke="{col}" '
        f'stroke-width="1.8" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<circle class="spk-dot" cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{col}"/></svg>'
    )


def _range_bar(lo, hi, pos, prefer_cn: bool) -> str:
    """52 周区间 micro-bar: 轨 3px #ebd9c8 / 填充 teal / 墨标 2×9 top:-3 / lo·hi mono 9px #b8b1a8。
    <330d 窗口不标注护栏由调用方控(pos=None 时此函数省略)。"""
    if lo is None or hi is None or pos is None:
        return '<div style="height:23px;margin-top:6px"></div>'
    p = max(0.0, min(float(pos), 1.0)) * 100
    return (
        f'<div style="margin-top:6px">'
        f'<div style="position:relative;height:3px;background:{theme.PAPER_RULE}">'
        f'<div style="position:absolute;left:0;top:0;height:3px;width:{p:.1f}%;background:{theme.UP}"></div>'
        f'<div style="position:absolute;left:{p:.1f}%;top:-3px;height:9px;width:2px;'
        f'background:{theme.INK};transform:translateX(-1px)"></div></div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:5px;'
        f'font-family:{theme.FONT_MONO};font-size:9px;color:{theme.INK_4}">'
        f'<span>52W {lo}</span><span>{hi}</span></div></div>'
    )


def _tile(it: dict, idx: int, prefer_cn: bool) -> str:
    chg = it.get("chg_pct")
    col = _ret_color(chg)
    chg_str = "—" if chg is None else f"{chg:+.2f}%"
    raw = it.get("value_raw")
    # count-up only when a raw number is supplied; else the formatted string is shown as-is.
    val_attr = f' data-countup="{raw}"' if isinstance(raw, (int, float)) else ""
    return (
        f'<div class="tile" style="animation-delay:{idx * 90}ms">'
        f'<div class="thead"><span class="tname">{it["name"]}</span><span class="ttick"></span></div>'
        f'<div class="tval"{val_attr}>{it["value"]}</div>'
        f'<div class="tchg" style="color:{col}">{chg_str}</div>'
        f'{_spark_svg(it.get("spark"), chg, idx)}'
        f'{_range_bar(it.get("lo"), it.get("hi"), it.get("pos"), prefer_cn)}'
        f'<div class="tctx">{_ctx_span("1M", it.get("m1"))}'
        f'<span class="dot">·</span>{_ctx_span("YTD", it.get("ytd"))}</div>'
        f'</div>'
    )


def _market_read(tiles: list[dict], prefer_cn: bool) -> str:
    """市场速读 dek:从真实 chg_pct 算 N 涨 M 跌 + 领涨/领跌(非编造)。无有效涨跌则省略。"""
    rated = [(t, t.get("chg_pct")) for t in tiles if isinstance(t.get("chg_pct"), (int, float))]
    if not rated:
        return ""
    up = sum(1 for _, c in rated if c >= 0)
    dn = len(rated) - up
    leader = max(rated, key=lambda x: x[1])
    laggard = min(rated, key=lambda x: x[1])
    up_c, dn_c = theme.UP, _DOWN
    if prefer_cn:
        head = (f'今日 <b style="color:{up_c}">{up} 涨</b> '
                f'<b style="color:{dn_c}">{dn} 跌</b>')
        bits = []
        if leader[1] >= 0:
            bits.append(f'<b style="color:{up_c}">{leader[0]["name"]}</b> 领涨 '
                        f'<b style="color:{up_c}">{leader[1]:+.2f}%</b>')
        if laggard[1] < 0:
            bits.append(f'<b style="color:{dn_c}">{laggard[0]["name"]}</b> 领跌 '
                        f'<b style="color:{dn_c}">{laggard[1]:+.2f}%</b>')
        body = " · ".join([head] + bits)
    else:
        head = (f'<b style="color:{up_c}">{up} up</b> '
                f'<b style="color:{dn_c}">{dn} down</b>')
        bits = []
        if leader[1] >= 0:
            bits.append(f'<b style="color:{up_c}">{leader[0]["name"]}</b> leads '
                        f'<b style="color:{up_c}">{leader[1]:+.2f}%</b>')
        if laggard[1] < 0:
            bits.append(f'<b style="color:{dn_c}">{laggard[0]["name"]}</b> lags '
                        f'<b style="color:{dn_c}">{laggard[1]:+.2f}%</b>')
        body = " · ".join([head] + bits)
    return f'<div class="dek">{body}</div>'


def render_index_tiles(tiles: list[dict], *, as_of: str | None,
                       prefer_cn: bool, height: int = 372) -> tuple[str, int]:
    """返回 (doc, iframe_height)。doc 自包含(HTML+SVG+count-up JS),交给 st.iframe。

    wave-2 精修变更(CONTRACT §2 HUB):
    - 玻璃容器(rgba .55 + blur14 + 白边 + 墨 3px 顶边,height:248px)
    - Space Grotesk 主字(FONT_DISPLAY) + JetBrains Mono 数字/eyebrow
    - 跌色 _DOWN=#c8102e(page-scope;theme.DOWN 全局不动)
    - 背景双 radial 红/青水彩(给玻璃提供可 blur 的底)
    - FONT_FACE_CSS 自托管字体注入(零 Google Fonts CDN)
    - 眼眉改 mono 12px uppercase 双语「市场总览 · Market Overview」
    - 现价 mono 32/38/700,情境行 10px uppercase
    """
    t = theme
    n = len(tiles) or 1
    parts = [_tile(it, i, prefer_cn) for i, it in enumerate(tiles)]

    # Eyebrow subtitle switches by language; title is always bilingual (HUB3 spec)
    eb_sub = ("四大指数 · 30 日走势 + 52 周区间" if prefer_cn
              else "4 indices · 30-day trend + 52-week range")
    # Footnote provenance — no "MOCK" strings (HUB11)
    if as_of:
        foot = (f"SOURCE: Yahoo Finance cron EOD · 截至 {as_of} · 仅供参考" if prefer_cn
                else f"SOURCE: Yahoo Finance cron EOD · as of {as_of} · for reference")
    else:
        foot = "SOURCE: Yahoo Finance cron EOD · 仅供参考" if prefer_cn else "SOURCE: Yahoo Finance cron EOD"

    # Eyebrow: always bilingual title (HUB3); renderer label stays SVG (no echarts in this module)
    eyebrow = (
        f'<div class="eyebrow">'
        f'<span class="ebtick"></span>'
        f'<span class="ebttl">市场总览 · Market Overview</span>'
        f'<span class="ebsub">{eb_sub}</span>'
        f'<span class="ebech">SVG</span></div>'
    )
    dek = _market_read(tiles, prefer_cn)

    css = (
        # Self-hosted @font-face — relative paths for Cloud /~/+/ prefix compat (D4)
        f"{t.FONT_FACE_CSS}"
        f"*{{box-sizing:border-box;margin:0;padding:0}}"
        # body: Space Grotesk display stack + dual-radial water-color wash (HUB5)
        f"html,body{{height:100%;"
        f"background:"
        f"radial-gradient(700px 320px at 8% -20%,rgba(200,16,46,.09),transparent 60%),"
        f"radial-gradient(700px 320px at 94% -10%,rgba(13,118,128,.10),transparent 60%),"
        f"{t.PAPER};"
        f"font-family:{t.FONT_DISPLAY};"
        f"font-feature-settings:'tnum','ss01';color-scheme:light;color:{t.INK};"
        f"-webkit-font-smoothing:antialiased}}"
        f".wrap{{padding:4px 2px}}"
        # Eyebrow: JetBrains Mono 12px/.16em UPPER bilingual (HUB3)
        f".eyebrow{{display:flex;align-items:baseline;gap:10px;margin:2px 0 9px}}"
        f".ebtick{{width:4px;height:16px;background:{t.CMSI_RED};display:inline-block;align-self:center}}"
        f".ebttl{{font-family:{t.FONT_MONO};font-size:12px;font-weight:600;color:{t.INK};"
        f"letter-spacing:.16em;text-transform:uppercase}}"
        f".ebsub{{font-size:12px;color:{t.INK_3}}}"
        f".ebech{{margin-left:auto;font-family:{t.FONT_MONO};font-size:10px;"
        f"letter-spacing:.1em;text-transform:uppercase;color:{t.INK_4}}}"
        # Market-read dek — real N-up/M-down, entry fade only (HUB10)
        f".dek{{font-size:13px;line-height:1.5;color:{t.INK_2};margin:0 0 13px;"
        f"padding-bottom:12px;border-bottom:1px solid {t.PAPER_RULE};"
        f"opacity:0;animation:mhtFade .6s ease .05s forwards}}"
        f".dek b{{font-weight:700}}"
        # Glass container row (HUB4): rgba .55 + blur14 + white border + ink 3px top
        f".grid{{display:flex;"
        f"border:1px solid rgba(255,255,255,.7);"
        f"border-top:3px solid {t.INK};"
        f"background:rgba(255,255,255,.55);"
        f"backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"
        f"height:248px;overflow:hidden}}"
        # Tiles: flex:1, separated by 1px #ebd9c8, last no border (HUB6)
        f".tile{{flex:1;min-width:0;padding:18px 20px;border-right:1px solid {t.PAPER_RULE};"
        f"opacity:0;animation:mhtRise .55s cubic-bezier(.22,.61,.36,1) both;overflow:hidden}}"
        f".tile:last-child{{border-right:none}}"
        f".thead{{display:flex;justify-content:space-between;align-items:flex-start}}"
        # Index name: 11px/0.06em/600 #8a8580 + red tick 4×12 (HUB6a)
        f".tname{{font-size:11px;font-weight:600;color:{t.INK_3};letter-spacing:.06em}}"
        f".ttick{{width:4px;height:12px;background:{t.CMSI_RED};display:inline-block;flex:none}}"
        # Price: JetBrains Mono 32/38/700 -0.02em tabular (HUB6b)
        f".tval{{font-family:{t.FONT_MONO};font-size:32px;line-height:38px;font-weight:700;"
        f"letter-spacing:-.02em;margin-top:8px;font-variant-numeric:tabular-nums}}"
        # Day change: mono 13/700, color set inline per sign (HUB6c)
        f".tchg{{font-family:{t.FONT_MONO};font-size:13px;font-weight:700;margin-top:2px;"
        f"font-variant-numeric:tabular-nums}}"
        # Context row: mono 10/.04em UPPER, values sign-colored (HUB9)
        f".tctx{{display:flex;gap:7px;margin-top:8px;font-family:{t.FONT_MONO};"
        f"font-size:10px;color:{t.INK_3};letter-spacing:.04em;text-transform:uppercase}}"
        f".tctx .dot{{color:{t.INK_4}}}"
        f".foot{{margin-top:11px;font-family:{t.FONT_MONO};font-size:10.5px;"
        f"letter-spacing:.02em;color:{t.INK_3}}}"
        # Sparkline draw-in: pathLength=1 → dashoffset 1→0; area + dot fade-in (HUB10)
        f".spk{{stroke-dasharray:1;stroke-dashoffset:1;animation:mhtDraw 1.15s ease .15s forwards}}"
        f".spk-area{{opacity:0;animation:mhtFade .9s ease .35s forwards}}"
        f".spk-dot{{opacity:0;animation:mhtFade .4s ease 1.15s forwards}}"
        f"@keyframes mhtDraw{{to{{stroke-dashoffset:0}}}}"
        f"@keyframes mhtFade{{to{{opacity:1}}}}"
        f"@keyframes mhtRise{{from{{opacity:0;transform:translateY(9px)}}to{{opacity:1;transform:none}}}}"
        # prefers-reduced-motion: kill all entry animations (HUB10)
        f"@media (prefers-reduced-motion:reduce){{"
        f".tile,.dek,.spk,.spk-area,.spk-dot{{animation:none!important;opacity:1!important;"
        f"stroke-dashoffset:0!important;transform:none!important}}}}"
    )

    # Minimal count-up: reads data-countup, 1050ms easeOutCubic, no echarts/no size dependency.
    # Safe: only updates textContent of .tval nodes — does not interfere with inline SVG guard.
    countup_js = (
        "<script>(function(){var R=matchMedia('(prefers-reduced-motion:reduce)').matches;"
        "var ns=[].slice.call(document.querySelectorAll('[data-countup]'));"
        "if(R){return;}"
        "var t0=performance.now(),D=1050;"
        "function f(n){return n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}"
        "function tick(now){var r=Math.min((now-t0)/D,1),e=1-Math.pow(1-r,3);"
        "ns.forEach(function(el){var v=parseFloat(el.getAttribute('data-countup'));"
        "if(isFinite(v))el.textContent=f(v*e);});"
        "if(r<1)requestAnimationFrame(tick);}"
        "if(ns.length)requestAnimationFrame(tick);})();</script>"
    )
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="wrap">'
        f'{eyebrow}{dek}<div class="grid">{"".join(parts)}</div>'
        f'<div class="foot">{foot}</div></div>{countup_js}</body></html>'
    )
    return doc, height
