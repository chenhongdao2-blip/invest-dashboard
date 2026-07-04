"""策略页开场 Banner — lib/strategy_banner.py
=====================================================

策略页(pages/4_Strategy_Picks.py)开场区重设计:把纯文字导语换成
「策略速览带」(三策略并排预告:迷你 sparkline + 大号累计收益 + α)+「双轨导览卡」。

设计取舍:小图用内联 SVG 而非 ECharts —— 即时渲染、零依赖。
纯 st.markdown(unsafe_allow_html) 即可,不需要 iframe / JS。

Wave-2 reskin (CONTRACT D2/D3/BANR1-12):
  - 跌色 _DOWN = t.CMSI_RED (#c8102e, page-scope; theme.DOWN 全局不动)
  - EOD 呼吸点恢复(D3),措辞「EOD 跟踪 · DAILY」(非假实时)
  - 玻璃卡 rgba .55/blur14 + 顶边 INK(速览) / 左边 CMSI_RED(双轨)
  - 大号数字 FONT_MONO 32px
  - 盈亏点带接真 win_list(BANR8)

调用(在 page_header 之后、tabs 之前):
    from lib import strategy_banner as sb

    sb.live_title("AI Agent 选股 · 策略表现", as_of="2026-06-29 HKT")
    st.markdown(i18n.t("strategy.pitch"), unsafe_allow_html=True)

    sb.overview_strip([
        {"name":"美国生科 5.0","bench_code":"XBI","pick_date":"2026-05-15","n_picks":N,
         "cum_ret":X,"bench_ret":Y,"alpha":Z,"wins":W,"total":T,"hold_days":D,
         "win_list":[True,False,...],          # per-holding, caller sorts by rank
         "curve":(strat_vals, bench_vals)},     # rebased=100 序列
        {"kind":"ipo","name":"港股 IPO 打新","tag":"六因子 v6.7",
         "n":N,"listed":L,"median":M,"hi":H,"lo":Lo},
    ])

    sb.dual_track([
        ("01","催化剂驱动","围绕生物科技的临床读出……"),
        ("02","新股打新多维评分","以六因子模型……"),
    ], footer="两条线共用同一套<b>数据纪律</b>……")

win_list: 调用页传 (normed.iloc[-1] > 100).tolist() 逐持仓真值(rank 顺序);
          未传时 _curve_card 降级为 wins-first 确定性排列。
curve 序列从 compute_strategy_returns 的 portfolio(策略)和基准 normed 列取(rebased=100)。
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import theme as t

# page-scope 跌/亏色 —— wave-2 reskin 表面用 #c8102e (CONTRACT D2)
# 全局 theme.DOWN = #cc0000 token 不动
_DOWN = t.CMSI_RED


def _ret_color(v) -> str:
    """Return teal(UP) for non-negative, page-scope red(_DOWN) for negative."""
    return t.UP if v >= 0 else _DOWN


# ── Sparkline pair ─────────────────────────────────────────────────────────

def _spark_pair(strat, bench, w=280, h=64, pad=5, gid="sp") -> str:
    """两条对齐 sparkline(策略红实线 + 渐变面积 + 基准灰虚线 + 终点红点)。共用 min/max。
    gid 必须每次调用唯一(同页多张卡的 <linearGradient> id 不能撞)。"""
    strat = [float(v) for v in strat]
    bench = [float(v) for v in bench]
    allv = strat + bench
    lo, hi = min(allv), max(allv)
    rng = (hi - lo) or 1.0

    def pts(vals):
        step = (w - 2) / (len(vals) - 1) if len(vals) > 1 else 0
        return " ".join(
            f"{1 + i * step:.1f},{pad + (h - 2 * pad) - (v - lo) / rng * (h - 2 * pad):.1f}"
            for i, v in enumerate(vals)
        )

    ps, pb = pts(strat), pts(bench)
    lx, ly = ps.rsplit(" ", 1)[-1].split(",")
    base = h - pad
    fill = f"{ps} {w - 1:.1f},{base:.1f} 1.0,{base:.1f}"
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:100%;height:58px;margin-top:12px;display:block">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{t.CMSI_RED}" stop-opacity="0.16"/>'
        f'<stop offset="100%" stop-color="{t.CMSI_RED}" stop-opacity="0.01"/></linearGradient></defs>'
        f'<polygon points="{fill}" fill="url(#{gid})" stroke="none"/>'
        f'<polyline points="{pb}" fill="none" stroke="{t.INK_4}" stroke-width="1.4" '
        f'stroke-dasharray="3 3" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<polyline points="{ps}" fill="none" stroke="{t.CMSI_RED}" stroke-width="2" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        f'<circle cx="{lx}" cy="{ly}" r="2.6" fill="{t.CMSI_RED}"/></svg>'
    )


# ── Win/loss dot band ──────────────────────────────────────────────────────

def _dots(win_list: list) -> str:
    """持仓盈亏散点带:逐持仓真 sign 列表,直接画不造假序列。
    每点 = 一只持仓(truthy=盈 teal, falsy=亏 _DOWN)。调用方控制顺序。
    BANR8: 接真 — 调用页传 (normed.iloc[-1]>100).tolist()。"""
    dots = "".join(
        f'<span style="width:5px;height:5px;display:inline-block">'
        f'<svg width="5" height="5"><circle cx="2.5" cy="2.5" r="2.5" '
        f'fill="{t.UP if v else _DOWN}"/></svg></span>'
        for v in win_list
    )
    return (
        f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:11px" '
        f'title="每点 = 一只持仓,青=盈 / 红=亏">{dots}</div>'
    )


# ── Card renderers ─────────────────────────────────────────────────────────

def _curve_card(it: dict) -> str:
    """Strategy curve card (one of two in the overview strip)."""
    sgn  = "+" if it["cum_ret"]  >= 0 else ""
    asgn = "+" if it["alpha"]    >= 0 else ""
    bsgn = "+" if it["bench_ret"] >= 0 else ""
    col  = _ret_color(it["cum_ret"])
    acol = _ret_color(it["alpha"])
    # α chip bg: teal tint if ≥0; #c8102e tint if <0 (page-scope D2, not t.DOWN)
    abg = "rgba(13,118,128,.12)" if it["alpha"] >= 0 else "rgba(200,16,46,.10)"
    # gradient id: deterministic hash per card name — same-page ids must not collide
    # (N-10 whitelist: Python hash() for gradient id is NOT srcdoc JS pseudo-random)
    gid = "sp_" + str(abs(hash(it["name"])) % 99999)
    spark = _spark_pair(*it["curve"], gid=gid)
    # BANR8: use real win_list if caller provides it; else fall back to count-based
    # (wins-first, deterministic, no shuffle — safe until call-site is updated)
    win_list = it.get("win_list")
    if win_list is None:
        win_list = [True] * it["wins"] + [False] * (it["total"] - it["wins"])
    dots = _dots(win_list)
    return (
        f'<div style="padding:18px 20px;border-right:1px solid {t.PAPER_RULE}">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-size:14px;font-weight:600;color:{t.INK}">{_esc(it["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3}">'
        f'基准 {_esc(it["bench_code"])}</span></div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:2px">'
        f'自 {it["pick_date"]} · {it["n_picks"]} 票</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:14px">'
        # BANR7: FONT_MONO 32px (was sans 34px)
        f'<span style="font-family:{t.FONT_MONO};font-size:32px;line-height:36px;'
        f'font-weight:700;letter-spacing:-.02em;color:{col};'
        f'font-variant-numeric:tabular-nums">{sgn}{it["cum_ret"]:.1f}%</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:700;color:{acol};'
        f'background:{abg};padding:2px 7px;border-radius:2px">'
        f'α {asgn}{it["alpha"]:.1f}pp</span></div>'
        f'{spark}'
        f'{dots}'
        f'<div style="display:flex;justify-content:space-between;margin-top:10px;'
        f'font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}">'
        f'<span>基准 {bsgn}{it["bench_ret"]:.1f}%</span>'
        f'<span>胜率 {it["wins"]}/{it["total"]} · {it["hold_days"]}D</span></div></div>'
    )


def _ipo_card(it: dict) -> str:
    """IPO overview card (static cross-section, bar distribution rows)."""
    hi  = float(it["hi"])
    lo  = float(it["lo"])
    med = float(it["median"])

    def bar(lbl: str, pct: float, width: float, color: str) -> str:
        s = "+" if pct >= 0 else ""
        anchor = "left:0" if pct >= 0 else "right:50%"
        return (
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="font-family:{t.FONT_MONO};font-size:10px;'
            f'color:{t.INK_3};width:30px">{lbl}</span>'
            f'<div style="flex:1;height:8px;background:{t.PAPER_RULE};position:relative">'
            f'<div style="position:absolute;{anchor};top:0;height:8px;'
            f'width:{width:.1f}%;background:{color}"></div></div>'
            f'<span style="font-family:{t.FONT_MONO};font-size:11px;font-weight:700;'
            f'color:{color};width:48px;text-align:right">{s}{pct:.1f}%</span></div>'
        )

    msgn = "+" if med >= 0 else ""
    med_color = t.UP if med >= 0 else _DOWN
    # BANR9: normalized widths capped [2, 100]; lo color = _DOWN (#c8102e, not t.DOWN)
    med_width = max(2.0, min(abs(med) / hi * 100, 100.0)) if hi > 0 else 2.0
    lo_width  = max(2.0, min(abs(lo)  / hi * 100, 100.0)) if hi > 0 else 2.0
    pending = it.get("pending", it["n"] - it["listed"])

    return (
        f'<div style="padding:18px 20px">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-size:14px;font-weight:600;color:{t.INK}">{_esc(it["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3}">'
        f'{_esc(it.get("tag",""))}</span></div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:2px">'
        f'静态截面 · {it["n"]} 样本</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:14px">'
        # BANR7/9: FONT_MONO 32px
        f'<span style="font-family:{t.FONT_MONO};font-size:32px;line-height:36px;'
        f'font-weight:700;letter-spacing:-.02em;color:{t.UP};'
        f'font-variant-numeric:tabular-nums">{msgn}{med:.1f}%</span>'
        f'<span style="font-size:11px;color:{t.INK_3}">中位首日</span></div>'
        f'<div style="margin-top:18px;display:flex;flex-direction:column;gap:7px">'
        f'{bar("最高", hi,  100.0,    t.UP)}'
        f'{bar("中位", med, med_width, med_color)}'
        f'{bar("最差", lo,  lo_width,  _DOWN)}'
        f'</div>'
        f'<div style="margin-top:11px;font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}">'
        f'已上市 {it["listed"]} / 待上市 {pending}</div></div>'
    )


# ── Public API ─────────────────────────────────────────────────────────────

def live_title(title: str, *, as_of: str | None = None, lang: str | None = "中") -> None:
    """H1 + 左侧红导色块 + 右侧: 中/EN 描边分段切换 + EOD 跟踪徽标 + 更新时间戳。

    lang='中'/'EN' 高亮当前语言;None 不显示切换钮。
    呼吸点恢复(wave-2 D3):teal 8px cmsiPulse(theme._CSS .cmsi-live-dot),
    措辞诚实「EOD 跟踪 · DAILY」(非假实时);零「实时跟踪·TRACKING」字样。
    切换交互:<a href="?lang=zh|en" target="_self"> 真锚点,
    调用页读 st.query_params 切 session_state(现机制不动,只换皮)。
    """
    def seg(code: str, code_lang: str) -> str:
        on = (code == lang)
        return (
            f'<a href="?lang={code_lang}" target="_self" '
            f'style="font-family:{t.FONT_MONO};font-size:11px;font-weight:600;'
            f'letter-spacing:.08em;padding:5px 12px;text-decoration:none;'
            f'display:inline-block;'
            f'background:{t.CMSI_RED if on else "transparent"};'
            f'color:{t.PAPER if on else t.INK_3}">{code}</a>'
        )

    toggle = ""
    if lang is not None:
        toggle = (
            f'<div style="display:inline-flex;border:1px solid {t.PAPER_EDGE};'
            f'border-radius:3px;overflow:hidden">'
            f'{seg("中", "zh")}{seg("EN", "en")}</div>'
        )

    # EOD tracking badge (D3: visual restored, honest wording, NOT "实时跟踪")
    # .cmsi-live-dot styled by theme._CSS (background:UP teal + cmsiPulse animation)
    dot_label = (
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<span class="cmsi-live-dot"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;font-weight:600;'
        f'letter-spacing:.16em;text-transform:uppercase;color:{t.UP}">'
        f'EOD 跟踪 · DAILY</span></div>'
    )
    timestamp = (
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;'
        f'color:{t.INK_3};margin-top:5px">更新 {_esc(as_of)} HKT</div>'
    ) if as_of else ""
    dot_block = (
        f'<div style="display:flex;flex-direction:column;align-items:flex-start">'
        f'{dot_label}{timestamp}</div>'
    )

    right = (
        f'<div style="display:flex;align-items:center;gap:18px;flex:none">'
        f'{toggle}{dot_block}</div>'
    )
    st.markdown(
        f'<div style="display:flex;align-items:flex-end;'
        f'justify-content:space-between;gap:20px;'
        f'border-bottom:2px solid {t.INK};padding-bottom:14px;margin-bottom:4px">'
        f'<div style="display:flex;align-items:center;gap:14px;min-width:0">'
        f'<span style="width:5px;height:34px;background:{t.CMSI_RED};'
        f'display:inline-block;flex:none;border-radius:1px"></span>'
        # BANR1: FONT_DISPLAY on H1
        f'<h1 style="font-family:{t.FONT_DISPLAY};font-size:32px;line-height:36px;'
        f'font-weight:700;letter-spacing:-.01em;margin:0;color:{t.INK}">'
        f'{_esc(title)}</h1></div>{right}</div>',
        unsafe_allow_html=True,
    )


def overview_strip(items: list[dict]) -> None:
    """三策略速览带。items 里 curve 卡传 curve=(strat,bench);IPO 卡传 kind='ipo'。
    BANR5: 节标 mono UPPER + counter chip; BANR6: 玻璃容器 rgba .55/blur14/顶边 INK。"""
    n = len(items)
    cards = "".join(
        _ipo_card(it) if it.get("kind") == "ipo" else _curve_card(it)
        for it in items
    )
    # BANR5: mono 12/.16em UPPER section head + gray note + right-float counter chip
    section_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:26px 0 12px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:600;'
        f'letter-spacing:.16em;text-transform:uppercase;color:{t.INK}">'
        f'策略速览 · Strategy Snapshot</span>'
        f'<span style="font-size:12px;color:{t.INK_3}">'
        f'自选股日起的真实累计收益 vs 基准(非回测美化)</span>'
        f'<span style="margin-left:auto;font-family:{t.FONT_MONO};font-size:10px;'
        f'letter-spacing:.1em;text-transform:uppercase;color:{t.INK_3}">'
        f'{n} STRATEGIES</span></div>'
    )
    # BANR6: glass container — inline style (NOT GLASS_CARD_CSS class, per D5)
    container = (
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);'
        f'background:rgba(255,255,255,.55);'
        f'backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);'
        f'border:1px solid rgba(255,255,255,.7);'
        f'border-top:3px solid {t.INK}">{cards}</div>'
    )
    st.markdown(section_head + container, unsafe_allow_html=True)


def dual_track(cards: list[tuple], *, footer: str | None = None) -> None:
    """双轨导览卡 — cards=[(序号, 标题, body_html), ...]。
    BANR10: 玻璃卡(rgba .5/blur14/白边/红左肋); 节标 mono UPPER(无副注)。"""
    # BANR10: glass cards — inline style (NOT GLASS_CARD_CSS class, per D5)
    body = "".join(
        f'<div style="background:rgba(255,255,255,.5);'
        f'backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);'
        f'border:1px solid rgba(255,255,255,.7);'
        f'border-left:3px solid {t.CMSI_RED};padding:18px 22px">'
        f'<div style="display:flex;align-items:baseline;gap:9px">'
        f'<span style="font-family:{t.FONT_MONO};font-size:15px;font-weight:700;'
        f'color:{t.CMSI_RED}">{_esc(num)}</span>'
        f'<span style="font-size:15px;font-weight:700;color:{t.INK}">{_esc(ttl)}</span></div>'
        f'<p style="font-size:13px;line-height:1.65;color:{t.INK_2};margin:10px 0 0">'
        f'{bd}</p></div>'
        for num, ttl, bd in cards
    )
    # BANR10: 节标同 BANR5 无副注 — mono 12/.16em UPPER, margin 30 0 12
    section_head = (
        f'<div style="display:flex;align-items:center;gap:10px;margin:30px 0 12px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};'
        f'display:inline-block"></span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:600;'
        f'letter-spacing:.16em;text-transform:uppercase;color:{t.INK}">'
        f'如何阅读本页 · 两条策略线</span></div>'
    )
    st.markdown(
        section_head +
        f'<div style="display:grid;grid-template-columns:repeat({len(cards)},1fr);'
        f'gap:16px">{body}</div>',
        unsafe_allow_html=True,
    )
    if footer:
        # BANR11: footer data-discipline bar — unchanged from original
        st.markdown(
            f'<div style="margin-top:14px;padding:11px 16px;background:{t.PAPER_DEEP};'
            f'font-size:12.5px;color:{t.INK_2};display:flex;align-items:center;gap:8px">'
            f'<span style="width:3px;height:14px;background:{t.CMSI_RED};'
            f'display:inline-block"></span>{footer}</div>',
            unsafe_allow_html=True,
        )


# ── Theme reference (informational) ───────────────────────────────────────
# theme._CSS at theme.py:741-746 already has .cmsi-live-dot + @keyframes cmsiPulse
# (background: UP = #0d7680 teal). live_title re-activates the DOM element;
# no new CSS rules needed here (CONTRACT GRD6: zero new rules in theme._CSS).
LIVE_DOT_CSS = """
.cmsi-live-dot {{
  width: 8px; height: 8px; border-radius: 50%; background: {UP};
  display: inline-block; animation: cmsiPulse 1.5s ease-in-out infinite;
}}
@keyframes cmsiPulse {{ 0%,100% {{ opacity:1; transform:scale(1); }} 50% {{ opacity:.35; transform:scale(.82); }} }}
"""
