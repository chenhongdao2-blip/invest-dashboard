"""调仓规则 & 换仓记录 — Rebalance rulebook + performance ledger.

Renders two version-controlled markdown docs (data/content/):
- rebalance_rulebook.md : 调仓/权重迭代 rulebook v0.1 (quant + biotech + portfolio 三方综合)
- rebalance_ledger.md   : 换仓与收益台账 (4-22 → 5-15 → 7-9 收益链, 每次换仓追加)

Read-only display page — the source of truth stays in the markdown files so
the rules/ledger stay diff-able and portable (also mirrored in LLM Wiki RAW/).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lib import i18n

_CONTENT = Path(__file__).resolve().parents[2] / "data" / "content"


def _read(name: str) -> str:
    p = _CONTENT / name
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"_未找到 {name} — 请确认 `data/content/{name}` 存在。_"


def render() -> None:
    _en = i18n.get_lang() == "en"
    _t = lambda en, zh: en if _en else zh

    st.title(_t("Rebalance Rules & Ledger", "调仓规则 & 换仓记录"))
    st.caption(_t(
        "US Biotech catalyst portfolio · operating rulebook + performance ledger · 招商证券(香港) AI 投研",
        "美股 Biotech 催化剂组合 · 调仓操作手册 + 收益台账 · 招商证券(香港) AI 投研",
    ))

    tab_rules, tab_ledger = st.tabs([
        _t("📏 Rebalance Rulebook", "📏 调仓规则 Rulebook"),
        _t("📒 Rebalance Ledger", "📒 换仓记录 & 收益台账"),
    ])

    with tab_rules:
        st.info(_t(
            "v0.1 design baseline. Numbers are prior-reasonable values, not backtest-optimal — "
            "promote to 'validated' only after forward ledger vs dead-equal-weight shadow control.",
            "v0.1 设计起点。数字是「先验合理值」非回测最优值 —— 须走前瞻账本 vs 死等权影子对照验证后才升级「已验证」。",
        ))
        st.markdown(_read("rebalance_rulebook.md"))

    with tab_ledger:
        st.success(_t(
            "$1,000,000 → $1,296,511  (+29.65%, vs XBI +19.76% → alpha +9.89pp) · as of 2026-07-09",
            "$1,000,000 → $1,296,511(+29.65%,vs XBI +19.76% → alpha +9.89pp)· 截至 2026-07-09",
        ))
        st.markdown(_read("rebalance_ledger.md"))


render()
