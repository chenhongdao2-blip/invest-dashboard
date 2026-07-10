"""港股高股息 · 调仓纪律 & 换仓记录 — lib/hd_rebalance_panel.py
================================================================

Strategy Picks 高股息页(v3 当前版)的『调仓纪律 & 换仓记录』区,与 biotech 的
lib/rebalance_panel **同一套玻璃设计**,但换成高股息口径:

  1. 收益链   — v1 等权 → v2 评分定权 → v3 Wind 单源 的接续净值(复用
                rebalance_panel.render_chain;分段收益由页面 _chain_nav 同路径实时算)。
  2. 换仓明细 — 卖出 / 继续持有 / 新建仓,每只挂**桶(利率溢价桶 rate / 非利率桶
                nonrate)+ 组合权重**,而不是催化剂(高股息没有催化剂概念)。
  3. Rulebook — 高股息的「愿意分 × 分得出 × 分得久」55/25/20 + 换仓逻辑(payout 卡
                band / 评分掉档 / 权重漂移),而不是 readout 那套(复用
                rebalance_panel.render_rulebook,结构通用)。

数据:v1/v2/v3 = strat.load_hd()/load_hd_v2()/load_hd_v3();chain 由页面实时算并传入;
meta = data/content/hd_rebalance_v3.json。held/sold/new 由 v2/v3 picks CSV 实时求差。

设计约束(与 rebalance_panel / picks_table 对齐):纯 st.markdown(unsafe_allow_html)
自适应高度;涨/新建 teal · 卖出 CMSI_RED · 利率溢价桶 teal / 非利率桶 gold(#E0A458);
无 emoji;radius ≤ 2;数字 mono tabular。
"""
from __future__ import annotations

from html import escape as _esc

import pandas as pd
import streamlit as st

from lib import theme as t
from lib import rebalance_panel as rp

_RED = t.CMSI_RED
_TEAL = t.UP
_INK = t.INK
_INK2 = t.INK_2
_MUT = "#8a8580"
_DIM = "#b8b1a8"
_EDGE = t.PAPER_EDGE
_RULE = t.PAPER_RULE
_BAND = t.PAPER_BAND
_GOLD = "#E0A458"
_MONO = t.FONT_MONO

# 桶 tone:利率溢价桶(利率下行重估)= teal;非利率桶(盈利/治理)= gold。
_BUCKET_TONE = {"rate": _TEAL, "nonrate": _GOLD}

_GLASS = ("background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);"
          "backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.7);"
          f"border-top:2px solid {_INK};")


def _tt(prefer_cn: bool, cn: str, en: str) -> str:
    return cn if prefer_cn else en


def _eyebrow(prefer_cn: bool, cn: str, en: str, right: str = "") -> str:
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


def _bucket_label(bucket: str, buckets_meta: dict, prefer_cn: bool) -> str:
    b = buckets_meta.get(bucket, {})
    return _tt(prefer_cn, b.get("label", bucket), b.get("label_en", b.get("label", bucket)))


def _name_map(df: pd.DataFrame) -> dict:
    return {str(r["ticker"]): str(r.get("name", r["ticker"])) for _, r in df.iterrows()}


def _bucket_wt(df: pd.DataFrame) -> dict:
    out = {}
    for _, r in df.iterrows():
        out[str(r["ticker"])] = (
            str(r.get("bucket", "")),
            float(r["weight_pct"]) if pd.notna(r.get("weight_pct")) else None,
        )
    return out


def _hold_card(tk: str, name: str, bucket: str, wt: float | None, wmax: float,
               buckets_meta: dict, accent: str, prefer_cn: bool) -> str:
    tone = _BUCKET_TONE.get(bucket, _MUT)
    blab = _bucket_label(bucket, buckets_meta, prefer_cn)
    wbar = f"{(wt / wmax * 100):.0f}%" if (wt is not None and wmax > 0) else "0%"
    wtxt = f"{wt:.2f}%" if wt is not None else "—"
    return (
        f'<div style="{_GLASS}border-top:1px solid rgba(255,255,255,.7);'
        f'border-left:3px solid {accent};padding:12px 14px;">'
        f'<div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap;">'
        f'<span style="font-family:{_MONO};font-size:12px;font-weight:700;color:{accent};">{_esc(tk)}</span>'
        f'<span style="font-size:12px;font-weight:600;color:{_INK};white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis;max-width:130px;">{_esc(name)}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:9.5px;font-weight:600;'
        f'color:{tone};border:1px solid {tone};border-radius:2px;padding:1px 6px;">{_esc(blab)}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:center;gap:9px;margin-top:9px;">'
        f'<span style="display:block;flex:1;height:8px;background:rgba(26,26,26,.06);'
        f'border-radius:2px;overflow:hidden;">'
        f'<span style="display:block;height:100%;background:{tone};border-radius:2px;width:{wbar};"></span></span>'
        f'<span style="font-family:{_MONO};font-size:12px;font-weight:700;color:{_INK};'
        f'font-variant-numeric:tabular-nums;width:54px;text-align:right;flex:none;">{wtxt}</span></div>'
        f'</div>'
    )


def _sold_card(tk: str, name: str, bucket: str, wt: float | None,
               buckets_meta: dict, prefer_cn: bool) -> str:
    tone = _BUCKET_TONE.get(bucket, _MUT)
    blab = _bucket_label(bucket, buckets_meta, prefer_cn)
    wtxt = (f'{_tt(prefer_cn,"原权重","prev wt")} {wt:.2f}%' if wt is not None else "—")
    return (
        f'<div style="{_GLASS}border-top:1px solid rgba(255,255,255,.7);'
        f'border-left:3px solid {_RED};padding:10px 12px;opacity:.9;">'
        f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">'
        f'<span style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_RED};'
        f'text-decoration:line-through;">{_esc(tk)}</span>'
        f'<span style="font-size:11px;color:{_INK2};white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;max-width:110px;">{_esc(name)}</span>'
        f'<span style="margin-left:auto;font-family:{_MONO};font-size:9px;font-weight:600;'
        f'color:{tone};border:1px solid {tone};border-radius:2px;padding:1px 5px;">{_esc(blab)}</span>'
        f'</div>'
        f'<div style="font-family:{_MONO};font-size:10.5px;color:{_MUT};margin-top:5px;">{wtxt}</div>'
        f'</div>'
    )


def _render_board(v2_df: pd.DataFrame, v3_df: pd.DataFrame, rb: dict,
                  prefer_cn: bool) -> None:
    v3_order = [str(r["ticker"]) for _, r in v3_df.sort_values("rank").iterrows()]
    v3_set = set(v3_order)
    v2_order = [str(r["ticker"]) for _, r in v2_df.sort_values("rank").iterrows()]
    v2_set = set(v2_order)

    v3_name, v2_name = _name_map(v3_df), _name_map(v2_df)
    v3_bw, v2_bw = _bucket_wt(v3_df), _bucket_wt(v2_df)
    wmax = max((w for _, (_, w) in v3_bw.items() if w is not None), default=0.01)

    held = [tk for tk in v3_order if tk in v2_set]
    new = [tk for tk in v3_order if tk not in v2_set]
    sold = [tk for tk in v2_order if tk not in v3_set]

    buckets_meta = rb.get("buckets", {})

    # summary strip
    summary = [
        (_tt(prefer_cn, "换仓日", "Rebalance date"), rb.get("pick_date", "")),
        (_tt(prefer_cn, "换手率", "Turnover"), f'{rb.get("turnover_pct","")}%'),
        (_tt(prefer_cn, "卖出", "Sold"), f"{len(sold)}"),
        (_tt(prefer_cn, "继续持有", "Held"), f"{len(held)}"),
        (_tt(prefer_cn, "新建仓", "New"), f"{len(new)}"),
    ]
    sum_html = ""
    for i, (k, v) in enumerate(summary):
        brd = "" if i == len(summary) - 1 else f"border-right:1px solid {_RULE};"
        sum_html += (
            f'<div style="flex:1;min-width:96px;padding:12px 16px;{brd}">'
            f'<div style="font-family:{_MONO};font-size:10px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:{_MUT};font-weight:600;">{_esc(k)}</div>'
            f'<div style="font-family:{_MONO};font-size:20px;font-weight:700;color:{_INK};'
            f'margin-top:5px;">{_esc(str(v))}</div></div>'
        )
    logic = _tt(prefer_cn, rb.get("logic", ""), rb.get("logic_en", rb.get("logic", "")))

    st.markdown(
        _eyebrow(prefer_cn, "换仓明细", "Rebalance detail",
                 right=f'v2 → v3 · {rb.get("pick_date","")}'),
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="{_GLASS}margin-bottom:12px;">'
        f'<div style="display:flex;flex-wrap:wrap;border-bottom:1px solid {_RULE};">{sum_html}</div>'
        f'<div style="padding:12px 18px;font-size:12.5px;line-height:1.6;color:{_INK2};">'
        f'<b style="color:{_INK};">{_tt(prefer_cn,"换仓逻辑","Rebalance logic")}</b> — {_esc(logic)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    grid = "display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:10px;"
    sold_grid = "display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;"

    def _cards(tks, name_map, bw, accent):
        return "".join(
            _hold_card(tk, name_map.get(tk, tk), bw.get(tk, ("", None))[0],
                       bw.get(tk, ("", None))[1], wmax, buckets_meta, accent, prefer_cn)
            for tk in tks
        )

    # 新建仓
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_TEAL};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:6px 0 8px;">'
        f'＋ {_tt(prefer_cn,"新建仓","New positions")} · {len(new)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"按综合分定权 · 挂桶 + 权重","score-weighted · bucket + weight")}</span></div>'
        f'<div style="{grid}">{_cards(new, v3_name, v3_bw, _TEAL)}</div>',
        unsafe_allow_html=True,
    )
    # 继续持有
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_INK};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:18px 0 8px;">'
        f'= {_tt(prefer_cn,"继续持有","Held")} · {len(held)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"评分与 payout 仍达标","score & payout still clear")}</span></div>'
        f'<div style="{grid}">{_cards(held, v3_name, v3_bw, _INK)}</div>',
        unsafe_allow_html=True,
    )
    # 卖出
    sold_cards = "".join(
        _sold_card(tk, v2_name.get(tk, tk), v2_bw.get(tk, ("", None))[0],
                   v2_bw.get(tk, ("", None))[1], buckets_meta, prefer_cn)
        for tk in sold
    )
    st.markdown(
        f'<div style="font-family:{_MONO};font-size:11px;font-weight:700;color:{_RED};'
        f'letter-spacing:.06em;text-transform:uppercase;margin:18px 0 8px;">'
        f'− {_tt(prefer_cn,"卖出","Sold")} · {len(sold)} '
        f'<span style="color:{_MUT};font-weight:400;">'
        f'{_tt(prefer_cn,"评分下移 / payout 转弱 / 权重优化","rank slip / payout weakened / weight optimized")}</span></div>'
        f'<div style="{sold_grid}">{sold_cards}</div>',
        unsafe_allow_html=True,
    )

    # 桶说明 + 风险
    rate_m = buckets_meta.get("rate", {})
    nonrate_m = buckets_meta.get("nonrate", {})
    risk = _tt(prefer_cn, rb.get("risk", ""), rb.get("risk_en", rb.get("risk", "")))
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px;">'
        # rate bucket
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_TEAL};padding:12px 16px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_TEAL};'
        f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;">'
        f'{_esc(_tt(prefer_cn, rate_m.get("label","利率溢价桶"), rate_m.get("label_en","Rate-premium")))}</div>'
        f'<div style="font-size:11.5px;line-height:1.55;color:{_INK2};">'
        f'{_esc(_tt(prefer_cn, rate_m.get("note",""), rate_m.get("note_en","")))}</div></div>'
        # nonrate bucket
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_GOLD};padding:12px 16px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_GOLD};'
        f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;">'
        f'{_esc(_tt(prefer_cn, nonrate_m.get("label","非利率桶"), nonrate_m.get("label_en","Non-rate")))}</div>'
        f'<div style="font-size:11.5px;line-height:1.55;color:{_INK2};">'
        f'{_esc(_tt(prefer_cn, nonrate_m.get("note",""), nonrate_m.get("note_en","")))}</div></div>'
        # risk
        f'<div style="background:{t.PAPER_DEEP};border-left:3px solid {_RED};padding:12px 16px;">'
        f'<div style="font-family:{_MONO};font-size:10px;font-weight:700;color:{_RED};'
        f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;">'
        f'⚠ {_tt(prefer_cn,"风险","Risk")}</div>'
        f'<div style="font-size:11.5px;line-height:1.55;color:{_INK2};">{_esc(risk)}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render(v1_df: pd.DataFrame, v2_df: pd.DataFrame, v3_df: pd.DataFrame,
           chain: dict, meta: dict, prefer_cn: bool = True) -> None:
    """整块高股息『调仓纪律 & 换仓记录』(收益链 → 换仓明细 → Rulebook)。
    chain = 页面实时算好的收益链 dict(喂给 rebalance_panel.render_chain);
    meta = hd_rebalance_v3.json。缺 meta/chain 静默跳过。"""
    if not meta or v3_df is None or v3_df.empty or v2_df is None or v2_df.empty:
        return
    t.section_header(
        _tt(prefer_cn, "调仓纪律 & 换仓记录", "Rebalance Discipline & Ledger"),
        en=("Rebalance Discipline & Ledger" if prefer_cn else None),
        meta=_tt(prefer_cn, "真实换仓链 · 非回测", "real rebalance chain · not backtest"),
    )
    st.markdown(
        f'<p style="font-size:13px;line-height:1.65;color:{_INK2};max-width:880px;margin:2px 0 4px;">'
        f'{_tt(prefer_cn, "本组合按<b>连续换仓链</b>追踪真实资金(v1 等权建仓 → v2 评分定权 → v3 Wind 单源),每次换仓记账并沉淀规则。下方 = 收益链、本轮 v2→v3 调仓明细(挂桶 + 权重)、以及高股息选股/换仓 Rulebook。", "This book tracks real capital through a <b>continuous rebalance chain</b> (v1 EW build → v2 score-weighted → v3 Wind single-source). Below: the performance chain, this v2→v3 rebalance in detail (bucket + weight), and the high-div selection/rebalance rulebook.")}</p>',
        unsafe_allow_html=True,
    )
    if chain:
        rp.render_chain(chain, prefer_cn)
    rb = meta.get("rebalance")
    if rb:
        _render_board(v2_df, v3_df, rb, prefer_cn)
    rk = meta.get("rulebook")
    if rk:
        rp.render_rulebook(rk, prefer_cn)
    st.caption(_tt(
        prefer_cn,
        "来源:招商证券(香港) AI 投研 · 收益链口径 = 各版权重买入持有(v1 等权 / v2·v3 定权 + ~12% 现金)、含息复权、基准 恒生高股息30(3466.HK)· 数字为研究工具,不构成投资建议。",
        "Source: CMS (HK) AI Research · chain basis = per-version weights buy&hold (v1 EW / v2·v3 weighted + ~12% cash), total return, benchmark Hang Seng High-Div 30 (3466.HK) · research tool, not investment advice.",
    ))
