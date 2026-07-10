"""核心逻辑 · 四条主线编号卡 — lib/thesis_cards.py
========================================================

设计源(1:1 移植):claude.ai/design 「个股详情 礼来 美化.dc.html」的「核心逻辑」区
(handoff zip (8) → three-js/project/,2026-07-10 George 提供)。

把 Ticker Drill 研究备忘里那面「中文文字墙」(wiki `核心投资逻辑` section)拆成
**四条主线编号卡** + 顶部摘要条,和设计稿同一套玻璃语言:
- 摘要条:红左肋玻璃卡,承接 wiki Summary(**bold** → 墨字)。
- 编号卡(2 列 grid):大号 mono 序号(01/02/…)+ 标题 + 圆点要点列表 + 底部
  drug/target chips(从要点里的 **bold** 词派生);顶边 accent 按卡序循环
  红 → 青 → 金(#E0A458)→ 墨。

**数据驱动**(非硬编码 LLY):`parse_pillars()` 解析 wiki `核心投资逻辑` markdown:
  `### N. 标题` → 一张卡;其下 `- 要点` → bullets;要点内 `**bold**` 词 → chips。
解析出 < 2 张卡时,调用方回退渲染原始 markdown(不强套)。

设计约束(勿回退):纯 st.markdown(unsafe_allow_html)——自适应高度、继承页面自托管
字体(theme.FONT_FACE_CSS 全局注入)+ 径向 wash + GLASS_CARD_CSS;涨/主线色锁定;
无 emoji;radius ≤ 2;数字 mono tabular。
"""
from __future__ import annotations

import re
from html import escape as _esc

import streamlit as st

from lib import theme as t

# 卡序 accent 循环(设计稿:01 红 / 02 青 / 03 金 / 04 墨)
_ACCENTS = [t.CMSI_RED, t.UP, "#E0A458", t.INK]

_MONO = t.FONT_MONO
_INK = t.INK
_INK2 = t.INK_2
_MUT = t.INK_3
_EDGE = t.PAPER_EDGE
_RULE = t.PAPER_RULE

_GLASS = ("background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(10px);"
          "backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.7);")


def _strip_bold(s: str) -> str:
    return s.replace("**", "").strip()


# 无歧义的靶点/通路/机制 code —— 作为 chips 安全可派生(IL-13/IL-23/GLP-1/GIP…)。
# 只收编码型 token,不收普通词(避免 T2D/OSA/DTC 之类噪音塞进 chip)。
_CODE_RE = re.compile(
    r"\b(?:IL-\d+|GLP-1|GIP|GCG|KRAS|EGFR|HER2|PD-L?1|VEGF|TL1A|FGFR\d?|BTK|JAK\d?)\b"
)


def _bold_terms(text: str) -> list[str]:
    """要点里的 **bold** 词 + 无歧义靶点 code → chips 候选(去重、保序)。"""
    out: list[str] = []
    for m in re.findall(r"\*\*(.+?)\*\*", text):
        term = re.split(r"[（(]", m.strip())[0].strip(" ·,，、")   # 去括注,取主名
        if term and term not in out:
            out.append(term)
    for code in _CODE_RE.findall(text):
        if code not in out:
            out.append(code)
    return out


def parse_pillars(section_md: str | None) -> list[dict]:
    """wiki `核心投资逻辑` markdown → [{no, title, points, chips}]。

    识别 `### [N.] 标题` 为卡边界;卡内 `- / * / •` 行为要点;要点内 **bold** → chips。
    无 `###` 分隔(纯 bullet 墙)时返回 [](调用方回退原始 markdown)。
    """
    if not section_md:
        return []
    cards: list[dict] = []
    cur: dict | None = None
    for raw in section_md.splitlines():
        line = raw.rstrip()
        h = re.match(r"^#{2,4}\s+(.*)$", line.strip())
        if h:
            if cur:
                cards.append(cur)
            title = h.group(1).strip()
            # 去掉前导「1. 」「1、」「① 」等编号
            title = re.sub(r"^\s*(?:\d+[.)、．]|[①②③④⑤⑥⑦⑧⑨⑩])\s*", "", title)
            cur = {"title": _strip_bold(title), "points": [], "chips": []}
            continue
        b = re.match(r"^\s*[-*•]\s+(.*)$", line)
        if b and cur is not None:
            item = b.group(1).strip()
            cur["chips"].extend(_bold_terms(item))
            cur["points"].append(_strip_bold(item))
    if cur:
        cards.append(cur)

    out = []
    for i, c in enumerate(cards):
        if not c["points"]:
            continue
        # 标题里的靶点 code 也算 chip(如「GLP-1/GIP 平台」→ GLP-1, GIP),放最前
        title_codes = [x for x in _CODE_RE.findall(c["title"])]
        chips = list(dict.fromkeys(title_codes + c["chips"]))[:4]   # 去重 + 上限 4
        out.append({
            "no": f"{i + 1:02d}",
            "title": c["title"],
            "points": c["points"][:4],   # 每卡上限 4 要点,过长设计会破格
            "chips": chips,
            "accent": _ACCENTS[i % len(_ACCENTS)],
        })
    return out


def _summary_html(summary: str | None) -> str:
    if not summary:
        return ""
    body = re.sub(r"\*\*(.+?)\*\*", rf'<b style="color:{_INK};">\1</b>', _esc(summary))
    return body


def render(section_md: str | None, *, summary: str | None = None,
           prefer_cn: bool = True) -> bool:
    """渲染「核心逻辑」区(摘要条 + 四主线卡)。解析出 ≥2 张卡才渲染并返回 True;
    否则返回 False,调用方回退原始 markdown 展示。"""
    cards = parse_pillars(section_md)
    if len(cards) < 2:
        return False

    # 摘要条(红左肋玻璃)
    summ = _summary_html(summary)
    if summ:
        st.markdown(
            f'<div style="{_GLASS}border-left:3px solid {t.CMSI_RED};border-radius:2px;'
            f'padding:14px 18px;margin-bottom:14px;">'
            f'<div style="font-size:13.5px;line-height:1.7;color:{_INK2};">{summ}</div></div>',
            unsafe_allow_html=True,
        )

    # 四主线卡(2 列 grid)
    card_html = ""
    for c in cards:
        acc = c["accent"]
        pts = "".join(
            f'<div style="display:flex;gap:9px;align-items:baseline;">'
            f'<span style="width:5px;height:5px;border-radius:50%;background:{acc};'
            f'flex:none;margin-top:7px;"></span>'
            f'<span style="font-size:13px;line-height:1.55;color:{_INK2};">{_esc(p)}</span></div>'
            for p in c["points"]
        )
        chips = ""
        if c["chips"]:
            chips = (
                '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px;">'
                + "".join(
                    f'<span style="font-family:{_MONO};font-size:10px;font-weight:600;'
                    f'color:{_INK2};border:1px solid {_EDGE};border-radius:2px;'
                    f'padding:3px 8px;background:rgba(255,255,255,.5);">{_esc(ch)}</span>'
                    for ch in c["chips"]
                )
                + "</div>"
            )
        card_html += (
            f'<div style="{_GLASS}border-top:2px solid {acc};border-radius:2px;'
            f'padding:16px 18px;display:flex;flex-direction:column;">'
            f'<div style="display:flex;align-items:baseline;gap:10px;">'
            f'<span style="font-family:{_MONO};font-size:20px;font-weight:700;'
            f'color:{acc};line-height:1;">{c["no"]}</span>'
            f'<span style="font-size:15px;font-weight:700;color:{_INK};'
            f'line-height:1.3;">{_esc(c["title"])}</span></div>'
            f'<div style="display:flex;flex-direction:column;gap:7px;margin-top:12px;">{pts}</div>'
            f'{chips}</div>'
        )

    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">{card_html}</div>',
        unsafe_allow_html=True,
    )
    return True
