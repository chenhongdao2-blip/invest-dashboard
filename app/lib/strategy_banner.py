"""策略页开场 Banner — 新模块 lib/strategy_banner.py
=====================================================

策略页(pages/4_Strategy_Picks.py)开场区重设计:把纯文字导语换成
「策略速览带」(三策略并排预告:迷你 sparkline + 大号累计收益 + α)+「双轨导览卡」。

设计取舍:小图用内联 SVG 而非 ECharts —— 即时渲染、零依赖、贴合 ui.py 现有 _spark_svg。
纯 st.markdown(unsafe_allow_html) 即可,不需要 iframe / JS。

调用(在 page_header 之后、tabs 之前):
    from lib import strategy_banner as sb

    sb.live_title("AI Agent 选股 · 策略表现", as_of="2026-06-29 16:08 HKT")
    st.markdown("<p style='font-size:14px;line-height:1.65;color:#4a4a4a;max-width:880px'>"
                "让 AI 像分析师一样读数据……</p>", unsafe_allow_html=True)

    sb.overview_strip([
        {"name":"美国生科 5.0","bench_code":"XBI","pick_date":"2026-05-15","n_picks":40,
         "cum_ret":24.3,"bench_ret":9.1,"alpha":15.2,"wins":28,"total":40,"hold_days":45,
         "curve":(strat_vals_v5, bench_vals_v5)},                      # rebased=100 序列
        {"name":"港股高股息","bench_code":"3466.HK","pick_date":"2026-03-20","n_picks":20,
         "cum_ret":18.7,"bench_ret":6.2,"alpha":12.5,"wins":14,"total":20,"hold_days":102,
         "curve":(strat_vals_hd, bench_vals_hd)},
        {"kind":"ipo","name":"港股 IPO 打新","tag":"六因子 v6.7","n":20,"listed":20,
         "median":12.4,"hi":384.0,"lo":-4.6},
    ])

    sb.dual_track([
        ("01","催化剂驱动","围绕生物科技的临床读出、FDA / NMPA 审批节点……"),
        ("02","新股打新多维评分","以六因子模型(流通盘稀缺度、基石阵容……)……"),
    ], footer="两条线共用同一套<b>数据纪律</b>:数字标来源与时效、卖方一致预期与自有观点分离、结论可操作。")

curve 序列从 compute_strategy_returns 的 `portfolio`(策略)和基准 normed 列取(rebased=100);
传 ~20-60 个点即可,helper 会自动按两序列共同 min/max 对齐 y 轴。
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import theme as t


def live_title(title: str, *, as_of: str | None = None, lang: str | None = "中") -> None:
    """H1 + 左侧红导色块,右侧 中/EN 描边分段切换 + 更新时间戳。
    lang='中'/'EN' 高亮当前语言;None 不显示切换钮。实时跟踪·TRACKING 徽标已去除
    (数据 EOD/cron 非实时 — George 拍板)。切换交互:中/EN = <a href="?lang=zh|en"> 真链接,
    调用页读 st.query_params 切 session_state(替代顶部实心红钮,不留两个语言钮)。"""
    def seg(code: str, code_lang: str) -> str:
        on = (code == lang)
        return (
            f'<a href="?lang={code_lang}" target="_self" '
            f'style="font-family:{t.FONT_MONO};font-size:11px;font-weight:600;letter-spacing:.08em;'
            f'padding:5px 12px;text-decoration:none;display:inline-block;'
            f'background:{t.CMSI_RED if on else "transparent"};'
            f'color:{t.PAPER if on else t.INK_3}">{code}</a>'
        )

    toggle = ""
    if lang is not None:
        toggle = (f'<div style="display:inline-flex;border:1px solid {t.PAPER_EDGE};'
                  f'border-radius:3px;overflow:hidden">{seg("中", "zh")}{seg("EN", "en")}</div>')

    stamp = ""
    if as_of:
        stamp = (f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}">'
                 f'更新 {_esc(as_of)} HKT</div>')

    right = (f'<div style="display:flex;align-items:center;gap:18px;flex:none">{toggle}{stamp}</div>'
             if (toggle or stamp) else "")
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:20px;'
        f'border-bottom:2px solid {t.INK};padding-bottom:14px;margin-bottom:4px">'
        f'<div style="display:flex;align-items:center;gap:14px;min-width:0">'
        f'<span style="width:5px;height:34px;background:{t.CMSI_RED};display:inline-block;'
        f'flex:none;border-radius:1px"></span>'
        f'<h1 style="font-size:32px;line-height:36px;font-weight:700;letter-spacing:-.01em;'
        f'margin:0;color:{t.INK}">{_esc(title)}</h1></div>{right}</div>',
        unsafe_allow_html=True,
    )


def _spark_pair(strat, bench, w=280, h=64, pad=5, gid="sp") -> str:
    """两条对齐 sparkline(策略红实线 + 渐变面积 + 基准灰虚线 + 终点红点)。共用 min/max 对齐 y 轴。
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


def _dots(total: int, wins: int, seed: int = 7) -> str:
    """持仓盈亏散点带:total 个小圆点,wins 个青(盈)其余红(亏),伪随机打散。
    每点 = 一只持仓,一眼看离散度。纯 SVG 圆点(无需 JS)。"""
    arr = [t.UP if i < wins else t.DOWN for i in range(total)]
    s = seed
    for i in range(len(arr) - 1, 0, -1):
        s = (s * 9301 + 49297) % 233280
        j = int(s / 233280 * (i + 1))
        arr[i], arr[j] = arr[j], arr[i]
    dots = "".join(
        f'<span style="width:5px;height:5px;display:inline-block">'
        f'<svg width="5" height="5"><circle cx="2.5" cy="2.5" r="2.5" fill="{c}"/></svg></span>'
        for c in arr
    )
    return (f'<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:11px" '
            f'title="每点 = 一只持仓,青=盈 / 红=亏">{dots}</div>')


def _ret_color(v) -> str:
    return t.UP if v >= 0 else t.DOWN


def _curve_card(it: dict) -> str:
    sgn = "+" if it["cum_ret"] >= 0 else ""
    asgn = "+" if it["alpha"] >= 0 else ""
    bsgn = "+" if it["bench_ret"] >= 0 else ""
    col = _ret_color(it["cum_ret"])
    # Sign-color the α chip too — a NEGATIVE alpha (underperformance) must read red,
    # not teal (the reference hardcoded UP and would paint an underperformer green).
    acol = _ret_color(it["alpha"])
    abg = "rgba(13,118,128,.12)" if it["alpha"] >= 0 else "rgba(204,0,0,.10)"
    gid = "sp_" + str(abs(hash(it["name"])) % 99999)   # 唯一 gradient id,免同页撞
    spark = _spark_pair(*it["curve"], gid=gid)
    dots = _dots(it["total"], it["wins"], seed=it["total"] * 7 + 3)
    return (
        f'<div style="padding:18px 20px;border-right:1px solid {t.PAPER_RULE}">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-size:14px;font-weight:600;color:{t.INK}">{_esc(it["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3}">基准 {_esc(it["bench_code"])}</span></div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:2px">'
        f'自 {it["pick_date"]} · {it["n_picks"]} 票</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:14px">'
        f'<span style="font-size:34px;line-height:36px;font-weight:700;letter-spacing:-.02em;'
        f'color:{col};font-variant-numeric:tabular-nums">{sgn}{it["cum_ret"]:.1f}%</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:12px;font-weight:700;color:{acol};'
        f'background:{abg};padding:2px 7px;border-radius:2px">α {asgn}{it["alpha"]:.1f}pp</span></div>'
        f'{spark}'
        f'{dots}'
        f'<div style="display:flex;justify-content:space-between;margin-top:10px;'
        f'font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}">'
        f'<span>基准 {bsgn}{it["bench_ret"]:.1f}%</span>'
        f'<span>胜率 {it["wins"]}/{it["total"]} · {it["hold_days"]}D</span></div></div>'
    )


def _ipo_card(it: dict) -> str:
    def bar(lbl, pct, width, color):
        s = "+" if pct >= 0 else ""
        anchor = "left:0" if pct >= 0 else "right:50%"
        return (
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3};width:30px">{lbl}</span>'
            f'<div style="flex:1;height:8px;background:{t.PAPER_RULE};position:relative">'
            f'<div style="position:absolute;{anchor};top:0;height:8px;width:{width}%;background:{color}"></div></div>'
            f'<span style="font-family:{t.FONT_MONO};font-size:11px;font-weight:700;color:{color};'
            f'width:48px;text-align:right">{s}{pct:.1f}%</span></div>'
        )
    msgn = "+" if it["median"] >= 0 else ""
    return (
        f'<div style="padding:18px 20px">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
        f'<span style="font-size:14px;font-weight:600;color:{t.INK}">{_esc(it["name"])}</span>'
        f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3}">{_esc(it.get("tag",""))}</span></div>'
        f'<div style="font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:2px">'
        f'静态截面 · {it["n"]} 样本</div>'
        f'<div style="display:flex;align-items:baseline;gap:8px;margin-top:14px">'
        f'<span style="font-size:34px;line-height:36px;font-weight:700;letter-spacing:-.02em;'
        f'color:{t.UP};font-variant-numeric:tabular-nums">{msgn}{it["median"]:.1f}%</span>'
        f'<span style="font-size:11px;color:{t.INK_3}">中位首日</span></div>'
        f'<div style="margin-top:18px;display:flex;flex-direction:column;gap:7px">'
        f'{bar("最高", it["hi"], 100, t.UP)}'
        f'{bar("中位", it["median"], max(2, min(abs(it["median"])/it["hi"]*100, 100)), t.UP)}'
        f'{bar("最差", it["lo"], 2, t.DOWN)}</div>'
        f'<div style="margin-top:11px;font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}">'
        f'已上市 {it["listed"]} / 待上市 {it["n"]-it["listed"]}</div></div>'
    )


def overview_strip(items: list[dict]) -> None:
    """三策略速览带。items 里 curve 卡传 curve=(strat,bench);IPO 卡传 kind='ipo'。"""
    cards = "".join(_ipo_card(it) if it.get("kind") == "ipo" else _curve_card(it) for it in items)
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:10px;margin:26px 0 12px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};display:inline-block"></span>'
        f'<span style="font-size:13px;font-weight:600;color:{t.INK}">策略速览</span>'
        f'<span style="font-size:12px;color:{t.INK_3}">自选股日起的真实累计收益 vs 基准(非回测美化)</span></div>'
        f'<div style="display:grid;grid-template-columns:repeat({len(items)},1fr);'
        f'border:1px solid {t.PAPER_EDGE};background:{t.PAPER}">{cards}</div>',
        unsafe_allow_html=True,
    )


def dual_track(cards: list[tuple], *, footer: str | None = None) -> None:
    """双轨导览卡 — cards=[(序号, 标题, body_html), ...]。替代「如何阅读本页」灰折叠。"""
    body = "".join(
        f'<div style="border:1px solid {t.PAPER_EDGE};background:{t.PAPER};border-left:3px solid {t.CMSI_RED};'
        f'padding:18px 22px"><div style="display:flex;align-items:baseline;gap:9px">'
        f'<span style="font-family:{t.FONT_MONO};font-size:15px;font-weight:700;color:{t.CMSI_RED}">{_esc(num)}</span>'
        f'<span style="font-size:15px;font-weight:700;color:{t.INK}">{_esc(ttl)}</span></div>'
        f'<p style="font-size:13px;line-height:1.65;color:{t.INK_2};margin:10px 0 0">{bd}</p></div>'
        for num, ttl, bd in cards
    )
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:10px;margin:30px 0 12px">'
        f'<span style="width:4px;height:16px;background:{t.CMSI_RED};display:inline-block"></span>'
        f'<span style="font-size:13px;font-weight:600;color:{t.INK}">如何阅读本页 · 两条策略线</span></div>'
        f'<div style="display:grid;grid-template-columns:repeat({len(cards)},1fr);gap:16px">{body}</div>',
        unsafe_allow_html=True,
    )
    if footer:
        st.markdown(
            f'<div style="margin-top:14px;padding:11px 16px;background:{t.PAPER_DEEP};font-size:12.5px;'
            f'color:{t.INK_2};display:flex;align-items:center;gap:8px">'
            f'<span style="width:3px;height:14px;background:{t.CMSI_RED};display:inline-block"></span>'
            f'{footer}</div>',
            unsafe_allow_html=True,
        )


# ── 追加到 theme.py 的 _CSS f-string(LIVE 脉冲点) ──────────────────────
LIVE_DOT_CSS = """
.cmsi-live-dot {{
  width: 8px; height: 8px; border-radius: 50%; background: {UP};
  display: inline-block; animation: cmsiPulse 1.5s ease-in-out infinite;
}}
@keyframes cmsiPulse {{ 0%,100% {{ opacity:1; transform:scale(1); }} 50% {{ opacity:.35; transform:scale(.82); }} }}
"""
