"""调仓纪律 & 换仓记录 — lib/rebalance_panel.py
==================================================

Strategy Picks 生科页(v6 当前版)的『调仓纪律 & 换仓记录』区。取代原独立的
「Rebalance 调仓规则/记录」页(裸 st.markdown,审美不统一),把三块内容按本站
玻璃卡设计语言(picks_table / strategy_banner 同族)融进选股介绍下方:

  1. render_chain()      — 收益链:v4 → v5 → v6 分段净值 + 累计 α(编辑部 hairline 卡)
  2. render_rebalance()  — 7 月调仓:卖出 14 / 继续持有 6 / 新建仓 16,新买 + 持有
                            按 biotech_catalysts.csv 注入『近期催化剂 + 时点 + 来源徽标』
  3. render_rulebook()   — 调仓规则 Rulebook v0.1(精简):一句话内核 + 8 条硬约束 +
                            明确别做 + 分阶段

设计约束(与 picks_table / strategy_banner 对齐,勿回退):
  - 纯 st.markdown(unsafe_allow_html) — 自适应高度、继承页面自托管字体(Inter/JetBrains)
    与径向 wash;不走 iframe(避免固定高度 + 字体路径坑)。
  - 玻璃卡 rgba(255,255,255,.55)/blur + 顶边 INK;分组眼眉 = 4px 红 tick + mono 大写。
  - 涨/持有 teal(#0d7680) · 卖出/警示 CMSI_RED(#c8102e) · 修正 gold(#a07a2c),配色锁定不翻转。
  - held / sold / new 三组由 v5(top-20)与 v6 两个 picks CSV **实时求差**得出(非手填),
    只有收益链冻结事实 / 卖出理由 / triage 说明 / rulebook 走 data/content/rebalance_v6.json。

数据源:
  - v6_df / v5_df : strat.load_v6() / load_v5()(rank/ticker/name/…）
  - catalysts_df : strat.load_catalysts()(ticker/catalyst/timing/type/source)
  - meta         : strat.load_rebalance_meta()(rebalance_v6.json 解析)
"""
from __future__ import annotations

from html import escape as _esc

import pandas as pd
import streamlit as st

from lib import theme as t

# ── 配色 tokens(玻璃卡族)──────────────────────────────────────────────────
_RED = t.CMSI_RED       # #c8102e 卖出 / 警示
_TEAL = t.UP            # #0d7680 涨 / 持有 / 核实
_GOLD = "#a07a2c"       # transcript 修正(muted gold, SECTOR_PALETTE 内)
_INK = t.INK            # #1a1a1a
_INK2 = t.INK_2         # #4a4a4a
_MUT = t.INK_3          # #8a8580
_DIM = t.INK_4          # #b8b1a8
_PAPER = t.PAPER        # #fff1e5
_BAND = t.PAPER_BAND    # #f2dfce
_EDGE = t.PAPER_EDGE    # #d4c4b0
_ROW = t.PAPER_RULE     # #ebd9c8
_MONO = t.FONT_MONO
_SANS = t.FONT_STACK

_GLASS = ("background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);"
          "backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.7);"
          f"border-top:2px solid {_INK};")


def _tt(prefer_cn: bool, cn: str, en: str) -> str:
    return cn if prefer_cn else en


def _eyebrow(prefer_cn: bool, cn: str, en: str, right: str = "") -> str:
    """4px 红 tick + mono 大写分组眼眉(strategy_banner 同款),右侧可挂副注。"""
    lbl = f"{cn} · {en.upper()}" if prefer_cn else en.upper()
    right_html = (f'<span style="margin-left:auto;font-family:{_MONO};font-size:10px;'
                  f'letter-spacing:.1em;text-transform:uppercase;color:{_MUT};">{right}</span>'
                  if right else "")
    return (
        f'<div style="display:flex;align-items:center;gap:10px;margin:26px 0 12px;">'
        f'<span style="width:4px;height:16px;background:{_RED};display:inline-block;flex:none;"></span>'
        f'<span style="font-family:{_MONO};font-size:12px;font-weight:600;'
        f'letter-spacing:.14em;text-transform:uppercase;color:{_INK};">{_esc(lbl)}</span>'
        f'{right_html}</div>'
    )


def _pct(v, dp: int = 1) -> str:
    if v is None:
        return "—"
    s = "+" if v >= 0 else "−"
    return f"{s}{abs(v):.{dp}f}%"


def _pp(v) -> str:
    if v is None:
        return "—"
    s = "+" if v >= 0 else "−"
    return f"{s}{abs(v):.2f}pp"


def _col(v) -> str:
    return _TEAL if (v is not None and v >= 0) else _RED


# ═══════════════════════════════════════════════════════════════════════════
# 1. 收益链 — v4 → v5 → v6 分段净值
# ═══════════════════════════════════════════════════════════════════════════

def render_chain(chain: dict, prefer_cn: bool = True,
                 live_current: dict | None = None) -> None:
    """live_current = {ret_pct, bench_pct, alpha_pp, days}(页面侧实时算的 v6 段)。
    传入则「进行中」段改显真实收益 + α;不传则回退「进行中」文案。"""
    cap0 = float(chain.get("capital_start", 0))
    cap1 = float(chain.get("capital_now", 0))
    ccy = chain.get("currency", "USD")
    cum = chain.get("cum_pct")
    bcum = chain.get("bench_cum_pct")
    alpha = chain.get("alpha_pp")
    bench = chain.get("bench", "XBI")
    gain = cap1 - cap0

    # 当前段(v6)有实时收益 → 把它复利到冻结的 v5-末净值上,头部 NAV / 累计 / α / 盈亏
    # 与下方 v6 段数字保持一致(否则段显 +X% 而总净值仍停在 07-09,前后矛盾)。
    if live_current and live_current.get("ret_pct") is not None and cap0:
        _r6 = float(live_current["ret_pct"]) / 100.0
        cap1 = cap1 * (1 + _r6)                       # cap1(=v5 末 NAV)复利 v6 段
        cum = (cap1 / cap0 - 1) * 100.0
        gain = cap1 - cap0
        _b6 = live_current.get("bench_pct")
        if _b6 is not None and bcum is not None:
            _bcum_live = ((1 + bcum / 100.0) * (1 + float(_b6) / 100.0) - 1) * 100.0
            alpha = cum - _bcum_live

    # ── 头部:起始资金 → 当前净值 + 累计 / α ───────────────────────────────
    head_cells = [
        (_tt(prefer_cn, "起始资金", "Start capital"), f"{ccy} {cap0:,.0f}", _INK),
        (_tt(prefer_cn, "当前净值", "Current NAV"), f"{ccy} {cap1:,.0f}", _INK),
        (_tt(prefer_cn, "累计收益", "Cumulative"), _pct(cum, 2), _col(cum)),
        (_tt(prefer_cn, f"超额 vs {bench}", f"Alpha vs {bench}"), _pp(alpha), _col(alpha)),
        (_tt(prefer_cn, "盈亏", "P/L"), f"{'+' if gain >= 0 else '−'}{ccy} {abs(gain):,.0f}", _col(gain)),
    ]
    head_html = ""
    for i, (k, v, c) in enumerate(head_cells):
        brd = "" if i == len(head_cells) - 1 else f"border-right:1px solid {_ROW};"
        head_html += (
            f'<div style="flex:1;min-width:120px;padding:14px 18px;{brd}">'
            f'<div style="font-family:{_MONO};font-size:10px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{_MUT};font-weight:600;">{_esc(k)}</div>'
            f'<div style="font-family:{_MONO};font-size:22px;font-weight:700;color:{c};'
            f'margin-top:6px;font-variant-numeric:tabular-nums;letter-spacing:-.01em;">{_esc(v)}</div>'
            f'</div>'
        )

    # ── 分段卡 v4 / v5 / v6 ───────────────────────────────────────────────
    seg_cards = ""
    segs = chain.get("segments", [])
    for i, s in enumerate(segs):
        ver = s.get("ver", "")
        is_cur = bool(s.get("current"))
        accent = _RED if is_cur else _TEAL
        label = _tt(prefer_cn, s.get("label", ""), s.get("label_en", s.get("label", "")))
        tag = _tt(prefer_cn, s.get("tag", ""), s.get("tag_en", s.get("tag", "")))
        note = _tt(prefer_cn, s.get("note", ""), s.get("note_en", s.get("note", "")))
        rng = f'{s.get("from","")} → {s.get("to") or _tt(prefer_cn, "至今", "now")}'
        n = s.get("n")
        ret = s.get("ret_pct")
        seg_alpha = s.get("alpha_pp")
        bp = s.get("bench_pct")
        days = s.get("days")
        # 当前段(v6):有实时收益就显真实数字 + α,而非静态「进行中」(George 2026-07-10)。
        if is_cur and live_current and live_current.get("ret_pct") is not None:
            ret = live_current.get("ret_pct")
            seg_alpha = live_current.get("alpha_pp")
            bp = live_current.get("bench_pct")
            if live_current.get("days") is not None:
                days = live_current.get("days")
        days_s = f" · {days}{_tt(prefer_cn,'天','d')}" if days else ""

        if is_cur and ret is None:
            big = _tt(prefer_cn, "进行中", "In progress")
            big_c = _RED
            sub = note
        else:
            big = _pct(ret, 2)
            big_c = _col(ret)
            sub = (f'{_tt(prefer_cn,"基准","Bench")} {_pct(bp,1)} · α '
                   f'<span style="color:{_col(seg_alpha)};font-weight:700;">{_pp(seg_alpha)}</span>')

        best = s.get("best")
        worst = s.get("worst")
        movers = ""
        if best or worst:
            movers = (
                f'<div style="margin-top:11px;padding-top:10px;border-top:1px dashed {_ROW};'
                f'font-family:{_MONO};font-size:10.5px;line-height:1.7;">'
                + (f'<div style="color:{_TEAL};">▲ {_esc(best)}</div>' if best else "")
                + (f'<div style="color:{_RED};">▼ {_esc(worst)}</div>' if worst else "")
                + '</div>'
            )
        brd = "" if i == len(segs) - 1 else f"border-right:1px solid {_ROW};"
        seg_cards += (
            f'<div style="flex:1;min-width:210px;padding:16px 18px;{brd}">'
            f'<div style="display:flex;align-items:baseline;gap:8px;">'
            f'<span style="font-family:{_MONO};font-size:13px;font-weight:700;color:{accent};">{_esc(ver)}</span>'
            f'<span style="font-size:13px;font-weight:600;color:{_INK};">{_esc(label)}</span>'
            f'<span style="margin-left:auto;font-family:{_MONO};font-size:10px;color:{_MUT};'
            f'border:1px solid {_EDGE};border-radius:2px;padding:1px 6px;">{_esc(tag)}</span></div>'
            f'<div style="font-family:{_MONO};font-size:11px;color:{_MUT};margin-top:4px;">'
            f'{_esc(rng)}{days_s}{(" · "+str(n)+_tt(prefer_cn,"票","names")) if n else ""}</div>'
            f'<div style="font-family:{_MONO};font-size:26px;font-weight:700;color:{big_c};'
            f'margin-top:12px;letter-spacing:-.02em;font-variant-numeric:tabular-nums;">{big}</div>'
            f'<div style="font-family:{_MONO};font-size:11px;color:{_MUT};margin-top:4px;">{sub}</div>'
            f'{movers}</div>'
        )

    st.markdown(
        _eyebrow(prefer_cn, "收益链", "Performance chain",
                 right=_tt(prefer_cn, "真实累计 · 非回测", "real cumulative · not backtest")),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="{_GLASS}margin-bottom:14px;">'
        f'<div style="display:flex;flex-wrap:wrap;border-bottom:1px solid {_ROW};">{head_html}</div>'
        f'<div style="display:flex;flex-wrap:wrap;">{seg_cards}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. 7 月调仓 — 卖出 / 持有 / 新建仓 + 催化剂注入
# ═══════════════════════════════════════════════════════════════════════════

def _catalyst_stamp(prefer_cn: bool) -> str:
    """催化剂时点新鲜度戳 — 读 refresh_manifest.json 的 biotech_catalysts 条目(单一
    日期真相,与侧栏『数据新鲜度』同源)。CSS 圆点(非 emoji,守 DESIGN Emoji=0):
    绿=新鲜 / 黄=超 max_age / 红=超 2×。催化剂时点是手工维护,自然老化即提醒。缺条目 → 空。"""
    from datetime import date, datetime
    from lib import freshness
    m = freshness.load_manifest().get("biotech_catalysts", {})
    sd = m.get("source_date")
    if not sd:
        return ""
    try:
        age = (date.today() - datetime.strptime(sd[:10], "%Y-%m-%d").date()).days
    except (ValueError, TypeError):
        return ""
    max_age = int(m.get("max_age_days", 30))
    col = _RED if age > 2 * max_age else (_GOLD if age > max_age else _TEAL)
    human = (_tt(prefer_cn, "今天", "today") if age <= 0
             else _tt(prefer_cn, f"{age} 天前", f"{age}d ago"))
    tip = _tt(prefer_cn, "每次成分股 earnings / readout 后刷新",
              "refresh after each holding's earnings / readout")
    stale = (f' · <span style="color:{col};font-weight:600;">'
             f'{_tt(prefer_cn, "建议复核", "review due")}</span>') if age > max_age else ""
    return (
        f'<div style="display:flex;align-items:center;gap:8px;margin:0 0 12px;'
        f'font-family:{_MONO};font-size:10.5px;color:{_MUT};">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{col};'
        f'display:inline-block;flex:none;"></span>'
        f'<span style="color:{col};font-weight:600;">'
        f'{_tt(prefer_cn, "催化剂时点截至", "Catalysts as of")} {_esc(sd)}</span>'
        f'<span>· {human}{stale}</span>'
        f'<span style="color:{_DIM};">· {_esc(tip)}</span></div>'
    )


def _cat_map(catalysts_df: pd.DataFrame) -> dict[str, dict]:
    m: dict[str, dict] = {}
    if catalysts_df is None or catalysts_df.empty:
        return m
    for _, r in catalysts_df.iterrows():
        tk = str(r.get("ticker", "")).strip()
        if tk:
            m[tk] = {
                "catalyst": str(r.get("catalyst", "")),
                "timing": str(r.get("timing", "")),
                "type": str(r.get("type", "")),
                "source": str(r.get("source", "")),
            }
    return m


def _source_badges(source: str, prefer_cn: bool) -> tuple[str, bool]:
    """(徽标 HTML, 追高 flag) — 从 catalyst source 字段派生。
    ★核实(teal) / ⚠修正(gold) / 人工(ink) / 引擎(muted) / 追高(red warning)。"""
    s = source or ""
    chips: list[tuple[str, str]] = []
    if "验证" in s:
        chips.append((_tt(prefer_cn, "★ 核实", "★ verified"), _TEAL))
    if "纠正" in s:
        chips.append((_tt(prefer_cn, "⚠ 修正", "⚠ corrected"), _GOLD))
    if "人工" in s:
        chips.append((_tt(prefer_cn, "人工", "manual"), _INK2))
    if "引擎" in s and not any(k in s for k in ("验证", "纠正", "人工")):
        chips.append((_tt(prefer_cn, "引擎", "engine"), _MUT))
    if not chips:
        chips.append((_tt(prefer_cn, "引擎", "engine"), _MUT))
    hot = "追高" in s
    html = "".join(
        f'<span style="font-family:{_MONO};font-size:9.5px;font-weight:600;color:{c};'
        f'border:1px solid {c};border-radius:2px;padding:1px 5px;letter-spacing:.02em;">{_esc(lbl)}</span>'
        for lbl, c in chips
    )
    return html, hot


def _buy_card(tk: str, name: str, cat: dict | None, is_manual: bool,
              is_triage: bool, prefer_cn: bool) -> str:
    """新建仓 / 持有卡:代码 + 名称 + 催化剂 + 时点 chip + 来源徽标 + 追高/人工/triage 旗。"""
    tags = ""
    if is_manual:
        tags += (f'<span style="font-family:{_MONO};font-size:9px;font-weight:700;color:{_PAPER};'
                 f'background:{_INK2};border-radius:2px;padding:1px 5px;">'
                 f'{_tt(prefer_cn,"人工加入","manual add")}</span>')
    if is_triage:
        tags += (f'<span style="font-family:{_MONO};font-size:9px;font-weight:700;color:{_PAPER};'
                 f'background:{_TEAL};border-radius:2px;padding:1px 5px;">'
                 f'{_tt(prefer_cn,"★ 捞回","★ triage")}</span>')

    body = ""
    hot = False
    if cat:
        badges, hot = _source_badges(cat.get("source", ""), prefer_cn)
        timing = cat.get("timing", "")
        ctype = cat.get("type", "")
        catalyst = cat.get("catalyst", "")
        timing_chip = (
            f'<span style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_INK};'
            f'background:{_BAND};border-radius:2px;padding:1px 7px;">{_esc(timing)}</span>'
            if timing else ""
        )
        type_chip = (
            f'<span style="font-family:{_MONO};font-size:9.5px;color:{_MUT};'
            f'border:1px solid {_EDGE};border-radius:2px;padding:1px 5px;">{_esc(ctype)}</span>'
            if ctype else ""
        )
        body = (
            f'<div style="font-size:11.5px;line-height:1.5;color:{_INK2};margin-top:7px;">{_esc(catalyst)}</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:8px;">'
            f'{timing_chip}{type_chip}{badges}</div>'
        )

    accent = _RED if hot else (_TEAL if not is_manual or is_triage else _INK2)
    hot_flag = (
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:9px;font-weight:700;'
        f'color:{_PAPER};background:{_RED};border-radius:2px;padding:1px 6px;">'
        f'{_tt(prefer_cn,"追高","chased")}</span>' if hot else ""
    )
    return (
        f'<div style="{_GLASS}border-top:1px solid rgba(255,255,255,.7);'
        f'border-left:3px solid {accent};padding:12px 14px;">'
        f'<div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap;">'
        f'<span style="font-family:{_MONO};font-size:12px;font-weight:700;color:{accent};">{_esc(tk)}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{_INK};white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis;max-width:150px;">{_esc(name)}</span>'
        f'{tags}{hot_flag}</div>'
        f'{body}</div>'
    )


def _sold_card(tk: str, name: str, reason: dict | None, prefer_cn: bool) -> str:
    typ = ""
    note = ""
    if reason:
        typ = _tt(prefer_cn, reason.get("type", ""), reason.get("type_en", reason.get("type", "")))
        note = reason.get("note", "")
    typ_chip = (
        f'<span style="margin-left:auto;flex:none;white-space:nowrap;font-family:{_MONO};'
        f'font-size:9px;font-weight:600;color:{_RED};'
        f'border:1px solid {_RED};border-radius:2px;padding:1px 5px;">{_esc(typ)}</span>'
        if typ else ""
    )
    note_html = (
        f'<div style="font-size:10.5px;line-height:1.45;color:{_MUT};margin-top:5px;">{_esc(note)}</div>'
        if note else ""
    )
    return (
        f'<div style="{_GLASS}border-top:1px solid rgba(255,255,255,.7);'
        f'border-left:3px solid {_RED};padding:10px 12px;opacity:.9;">'
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<span style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_RED};'
        f'text-decoration:line-through;">{_esc(tk)}</span>'
        f'<span style="font-size:11px;color:{_INK2};white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;max-width:120px;">{_esc(name)}</span>{typ_chip}</div>'
        f'{note_html}</div>'
    )


def _clean_name(name: str) -> str:
    """去掉 v6 CSV 里的『(人工加入)』后缀 + 常见公司后缀,展示更干净。"""
    n = str(name).replace("(人工加入)", "").strip()
    for suf in [", Inc.", " Inc.", " N.V.", " plc", " A/S", " Ltd.", " Limited",
                " Corporation", " Incorporated", " Holdings", " Company", " SE",
                " Pharmaceuticals", " Therapeutics", " Pharma", " Sciences"]:
        if n.endswith(suf):
            n = n[: -len(suf)].strip()
    return n or str(name)


def render_rebalance(v6_df: pd.DataFrame, v5_df: pd.DataFrame,
                     catalysts_df: pd.DataFrame, rb: dict,
                     prefer_cn: bool = True) -> None:
    if v6_df is None or v6_df.empty or v5_df is None or v5_df.empty:
        return

    cat = _cat_map(catalysts_df)
    manual = set(rb.get("manual", []))
    triage_in = set(rb.get("triage", {}).get("in", []))
    sold_reasons = rb.get("sold_reasons", {})

    v6_name = {str(r["ticker"]): _clean_name(r["name"]) for _, r in v6_df.iterrows()}
    v6_order = [str(r["ticker"]) for _, r in v6_df.sort_values("rank").iterrows()]
    v6_set = set(v6_order)

    v5_top = v5_df.sort_values("rank").head(20)
    v5_name = {str(r["ticker"]): _clean_name(r["name"]) for _, r in v5_top.iterrows()}
    v5_order = [str(r["ticker"]) for _, r in v5_top.iterrows()]
    v5_set = set(v5_order)

    held = [tk for tk in v6_order if tk in v5_set]
    new = [tk for tk in v6_order if tk not in v5_set]
    sold = [tk for tk in v5_order if tk not in v6_set]

    # ── 摘要 strip ──────────────────────────────────────────────────────────
    summary = [
        (_tt(prefer_cn, "换仓日", "Rebalance date"), rb.get("pick_date", "")),
        (_tt(prefer_cn, "换手率", "Turnover"), f'{rb.get("turnover_pct","")}%'),
        (_tt(prefer_cn, "卖出", "Sold"), f"{len(sold)}"),
        (_tt(prefer_cn, "继续持有", "Held"), f"{len(held)}"),
        (_tt(prefer_cn, "新建仓", "New"), f"{len(new)}"),
    ]
    sum_html = ""
    for i, (k, v) in enumerate(summary):
        brd = "" if i == len(summary) - 1 else f"border-right:1px solid {_ROW};"
        sum_html += (
            f'<div style="flex:1;min-width:96px;padding:12px 16px;{brd}">'
            f'<div style="font-family:{_MONO};font-size:10px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{_MUT};font-weight:600;">{_esc(k)}</div>'
            f'<div style="font-family:{_MONO};font-size:20px;font-weight:700;color:{_INK};'
            f'margin-top:5px;">{_esc(str(v))}</div></div>'
        )
    logic = _tt(prefer_cn, rb.get("logic", ""), rb.get("logic_en", rb.get("logic", "")))

    st.markdown(
        _eyebrow(prefer_cn, "7 月调仓", "July rebalance",
                 right=f'v5 → v6 · {rb.get("pick_date","")}'),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="{_GLASS}margin-bottom:12px;">'
        f'<div style="display:flex;flex-wrap:wrap;border-bottom:1px solid {_ROW};">{sum_html}</div>'
        f'<div style="padding:12px 18px;font-size:12.5px;line-height:1.6;color:{_INK2};">'
        f'<b style="color:{_INK};">{_tt(prefer_cn,"换仓逻辑","Rebalance logic")}</b> — {_esc(logic)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 催化剂时点新鲜度戳(手工维护数据 → 自然老化即提醒复核)
    _stamp = _catalyst_stamp(prefer_cn)
    if _stamp:
        st.markdown(_stamp, unsafe_allow_html=True)

    grid = "display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:10px;"
    sold_grid = "display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;"

    # ── 新建仓(催化剂注入,最重)─────────────────────────────────────────────
    new_cards = "".join(
        _buy_card(tk, v6_name.get(tk, tk), cat.get(tk), tk in manual, tk in triage_in, prefer_cn)
        for tk in new
    )
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_TEAL};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:6px 0 8px;">'
        f'＋ {_tt(prefer_cn,"新建仓","New positions")} · {len(new)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"(14 引擎 + 2 人工)· 含近期催化剂","(14 engine + 2 manual) · with near-term catalysts")}</span></div>'
        f'<div style="{grid}">{new_cards}</div>',
        unsafe_allow_html=True,
    )

    # ── 继续持有 ─────────────────────────────────────────────────────────────
    held_cards = "".join(
        _buy_card(tk, v6_name.get(tk, tk), cat.get(tk), False, False, prefer_cn)
        for tk in held
    )
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_INK};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:18px 0 8px;">'
        f'= {_tt(prefer_cn,"继续持有","Held")} · {len(held)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"催化剂窗口仍在","catalyst window still open")}</span></div>'
        f'<div style="{grid}">{held_cards}</div>',
        unsafe_allow_html=True,
    )

    # ── 卖出 ────────────────────────────────────────────────────────────────
    sold_cards = "".join(
        _sold_card(tk, v5_name.get(tk, tk), sold_reasons.get(tk), prefer_cn)
        for tk in sold
    )
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_RED};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:18px 0 8px;">'
        f'− {_tt(prefer_cn,"卖出","Sold")} · {len(sold)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"催化剂兑现 / 落袋 / 走弱","catalyst spent / profit-take / weakened")}</span></div>'
        f'<div style="{sold_grid}">{sold_cards}</div>',
        unsafe_allow_html=True,
    )

    # ── transcript triage callout + 风险 ───────────────────────────────────
    tri = rb.get("triage", {})
    tri_note = _tt(prefer_cn, tri.get("note", ""), tri.get("note_en", tri.get("note", "")))
    tri_in = " / ".join(tri.get("in", []))
    tri_out = " / ".join(tri.get("out", []))
    risk = _tt(prefer_cn, rb.get("risk", ""), rb.get("risk_en", rb.get("risk", "")))
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;">'
        # triage
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_TEAL};padding:14px 18px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_TEAL};'
        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;">'
        f'★ {_tt(prefer_cn,"Transcript 捞回","Transcript triage")} · '
        f'<span style="color:{_TEAL};">{_esc(tri_in)} ⇄ {_esc(tri_out)}</span></div>'
        f'<div style="font-size:12px;line-height:1.6;color:{_INK2};">{_esc(tri_note)}</div></div>'
        # risk
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_RED};padding:14px 18px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_RED};'
        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;">'
        f'⚠ {_tt(prefer_cn,"建仓风险","Build risk")}</div>'
        f'<div style="font-size:12px;line-height:1.6;color:{_INK2};">{_esc(risk)}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3. 调仓规则 Rulebook v0.1(精简)
# ═══════════════════════════════════════════════════════════════════════════

def render_rulebook(rk: dict, prefer_cn: bool = True) -> None:
    core = _tt(prefer_cn, rk.get("core", ""), rk.get("core_en", rk.get("core", "")))
    positioning = _tt(prefer_cn, rk.get("positioning", ""), rk.get("positioning_en", rk.get("positioning", "")))
    version = rk.get("version", "v0.1")

    # ── 8 条硬约束卡 ─────────────────────────────────────────────────────────
    rule_cards = ""
    for r in rk.get("rules", []):
        rid = r.get("id", "")
        title = _tt(prefer_cn, r.get("title", ""), r.get("title_en", r.get("title", "")))
        desc = _tt(prefer_cn, r.get("desc", ""), r.get("desc_en", r.get("desc", "")))
        rule_cards += (
            f'<div style="border-left:2px solid {_RED};padding:9px 12px;background:rgba(255,255,255,.4);">'
            f'<div style="display:flex;align-items:baseline;gap:7px;">'
            f'<span style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_RED};">{_esc(rid)}</span>'
            f'<span style="font-size:12.5px;font-weight:700;color:{_INK};">{_esc(title)}</span></div>'
            f'<div style="font-size:11.5px;line-height:1.5;color:{_INK2};margin-top:4px;">{_esc(desc)}</div>'
            f'</div>'
        )

    # ── 明确别做 ─────────────────────────────────────────────────────────────
    avoid_cards = ""
    for a in rk.get("avoid", []):
        ttl = _tt(prefer_cn, a.get("t", ""), a.get("t_en", a.get("t", "")))
        why = _tt(prefer_cn, a.get("why", ""), a.get("why_en", a.get("why", "")))
        avoid_cards += (
            f'<div style="padding:9px 12px;">'
            f'<div style="font-size:12.5px;font-weight:700;color:{_INK};">'
            f'<span style="color:{_RED};">✕</span> {_esc(ttl)}</div>'
            f'<div style="font-size:11px;line-height:1.5;color:{_MUT};margin-top:3px;">{_esc(why)}</div></div>'
        )

    phase = _tt(prefer_cn, rk.get("phase_note", ""), rk.get("phase_note_en", rk.get("phase_note", "")))

    st.markdown(
        _eyebrow(prefer_cn, "调仓规则 Rulebook", "Rebalance rulebook",
                 right=f'{version} · {_tt(prefer_cn,"设计起点待前瞻校准","design baseline")}'),
        unsafe_allow_html=True,
    )
    # 一句话内核 + 定位
    st.markdown(
        f'<div style="{_GLASS}border-top:2px solid {_RED};padding:16px 20px;margin-bottom:12px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_RED};'
        f'letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px;">'
        f'{_tt(prefer_cn,"一句话内核 · 三方共识","One-line core · tri-party consensus")}</div>'
        f'<div style="font-size:13.5px;line-height:1.7;color:{_INK};font-weight:600;">{_esc(core)}</div>'
        f'<div style="font-size:11px;line-height:1.6;color:{_MUT};margin-top:10px;'
        f'padding-top:10px;border-top:1px dashed {_ROW};">{_esc(positioning)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # 8 条硬约束
    st.markdown(
        f'<div style="{_GLASS}padding:16px 18px;margin-bottom:12px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_INK};'
        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px;">'
        f'{_tt(prefer_cn,"Phase 1 · 8 条风控硬约束(现在就上)","Phase 1 · 8 hard risk constraints (live now)")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:9px;">'
        f'{rule_cards}</div></div>',
        unsafe_allow_html=True,
    )
    # 明确别做 + 分阶段
    st.markdown(
        f'<div style="display:grid;grid-template-columns:2fr 1fr;gap:12px;">'
        # avoid
        f'<div style="{_GLASS}padding:14px 16px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_RED};'
        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;">'
        f'{_tt(prefer_cn,"明确别做(三方一致)","Explicitly avoid (consensus)")}</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;">{avoid_cards}</div></div>'
        # phase
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_TEAL};padding:14px 16px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_TEAL};'
        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;">'
        f'{_tt(prefer_cn,"分阶段","Phased rollout")}</div>'
        f'<div style="font-size:11.5px;line-height:1.6;color:{_INK2};">{_esc(phase)}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def render(v6_df: pd.DataFrame, v5_df: pd.DataFrame,
           catalysts_df: pd.DataFrame, meta: dict,
           prefer_cn: bool = True, live_current: dict | None = None) -> None:
    """渲染整块『调仓纪律 & 换仓记录』区(收益链 → 7 月调仓 → Rulebook)。
    meta = rebalance_v6.json 解析后的 dict。缺 meta 则静默跳过(不崩)。
    live_current = 页面实时算的当前(v6)段收益,传入则收益链末段显真实数字而非「进行中」。"""
    if not meta:
        return
    from lib import theme as _t
    _t.section_header(
        _tt(prefer_cn, "调仓纪律 & 换仓记录", "Rebalance Discipline & Ledger"),
        en=("Rebalance Discipline & Ledger" if prefer_cn else None),
        meta=_tt(prefer_cn, "真实换仓链 · 非回测", "real rebalance chain · not backtest"),
    )
    st.markdown(
        f'<p style="font-size:13px;line-height:1.65;color:{_INK2};max-width:880px;margin:2px 0 4px;">'
        f'{_tt(prefer_cn, "本页组合按<b>连续换仓链</b>追踪真实资金(v4 春季建仓 → v5 夏季调仓 → v6 7 月调仓),每次换仓记账并沉淀规则。下方 = 收益链、本轮调仓明细(含近期催化剂)、以及调仓/权重迭代 Rulebook。", "This book tracks real capital through a <b>continuous rebalance chain</b> (v4 spring build → v5 summer → v6 July). Below: the performance chain, this rebalance in detail (with near-term catalysts), and the rebalance/weighting rulebook.")}</p>',
        unsafe_allow_html=True,
    )
    chain = meta.get("chain")
    if chain:
        render_chain(chain, prefer_cn, live_current=live_current)
    rb = meta.get("rebalance")
    if rb:
        render_rebalance(v6_df, v5_df, catalysts_df, rb, prefer_cn)
    rk = meta.get("rulebook")
    if rk:
        render_rulebook(rk, prefer_cn)
    st.caption(_tt(
        prefer_cn,
        "来源:招商证券(香港) AI 投研 · 收益链口径 = Top-N 等权买入持有、含息复权、基准 XBI · 数字为研究工具,不构成投资建议。",
        "Source: CMS (HK) AI Research · chain basis = Top-N equal-weight buy&hold, total return, benchmark XBI · research tool, not investment advice.",
    ))
