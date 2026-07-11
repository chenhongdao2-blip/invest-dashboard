"""CMSI Section 封面头部（方案 C·数据式）— lib/section_header.py
======================================================================

设计源（1:1 移植）：claude.ai/design 「Section 封面头部 美化.dc.html」方案 C
（project 26a29f87, George 2026-07-11 拍板方案 C）：标题 + 右侧实时指数轨，
头部即概览。全站 section 头部可复用——kicker / 标题 / 状态 / 指数轨都是数据位。

一个公共函数：
  render(title, kicker, status, indices, height) -> (doc, iframe_h)

移植约束（INVARIANTS）：
  - 设计稿的 中/EN 切换不进 iframe——页面顶栏已有全局 lang toggle（house 惯例，
    key="lang" 单源绑定），iframe 内嵌开关无法触发 Streamlit rerun，双开关会打架
  - 字体: theme.FONT_FACE_CSS 自托管（禁 Google Fonts CDN，国内 blocked）
  - 青涨(#0d7680) / 红跌(#c8102e) 锁定；卡片 border-top 3px 品牌红
  - 状态 chip 带 pulseDot 呼吸动画（1.6s ease-in-out）
  - iframe body transparent，让页面 cream+wash 透出

indices 每项：
  {"name": str, "lvl": str（已格式化点位）, "pct": float|None（1日%）}

页面接入用 cover()（一站式：读 hc_index_comparison 烘焙指数 → tiles → st.iframe，
数据缺失回退 theme.page_header）；rail 预设见 RAIL_*。
"""
from __future__ import annotations

import math

from lib import theme

_RED   = theme.CMSI_RED        # "#c8102e"
_TEAL  = theme.UP              # "#0d7680"
_INK   = theme.INK             # "#1a1a1a"
_MUT   = theme.INK_3           # "#8a8580"
_DIM   = theme.INK_4           # "#b8b1a8"
_PAPER = theme.PAPER           # "#fff1e5"

_MONO = "'JetBrains Mono',monospace"
_SANS = ("'Space Grotesk','Inter','PingFang SC','Hiragino Sans GB',"
         "'Noto Sans SC','Microsoft YaHei',sans-serif")


def render(title: str, kicker: str, status: str,
           indices: list[dict], height: int = 152) -> tuple[str, int]:
    """Build the 方案C section cover header. Returns (doc, iframe_h)."""
    font_face = theme.FONT_FACE_CSS.strip()

    tiles = ""
    for i, it in enumerate(indices):
        pct = it.get("pct")
        if pct is None or not math.isfinite(float(pct)):
            pct_html = f'<span style="font-family:{_MONO};font-size:11px;color:{_DIM};">—</span>'
        else:
            pct = float(pct)
            col = _TEAL if pct >= 0 else _RED
            sign = "+" if pct >= 0 else "-"
            pct_html = (f'<span style="font-family:{_MONO};font-size:11px;font-weight:700;'
                        f'color:{col};">{sign}{abs(pct):.1f}%</span>')
        tiles += (
            f'<div style="padding:8px 16px;'
            f'{"border-right:1px solid #e2d3c1;" if i < len(indices) - 1 else ""}'
            f'display:flex;flex-direction:column;align-items:flex-start;min-width:96px;">'
            f'<span style="font-family:{_MONO};font-size:9.5px;letter-spacing:.04em;'
            f'color:{_MUT};">{it.get("name", "")}</span>'
            f'<div style="display:flex;align-items:baseline;gap:6px;margin-top:3px;">'
            f'<span style="font-family:{_MONO};font-size:14px;font-weight:700;'
            f'color:{_INK};">{it.get("lvl", "—")}</span>'
            f'{pct_html}'
            f'</div></div>'
        )

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{font_face}'
        '*{box-sizing:border-box;margin:0;padding:0;}'
        f'html,body{{background:transparent;color-scheme:light;font-family:{_SANS};'
        f'color:{_INK};font-feature-settings:"tnum","ss01";}}'
        '@keyframes pulseDot{0%,100%{opacity:1;transform:scale(1);}'
        '50%{opacity:.4;transform:scale(.82);}}'
        '</style></head><body>'

        # 卡片：品牌红顶边 + 纸色底 + 浅影
        f'<div style="background:{_PAPER};border:1px solid #d9c9b5;'
        f'border-top:3px solid {_RED};border-radius:4px;'
        f'box-shadow:0 12px 30px rgba(26,26,26,.06);padding:20px 30px 22px;">'

        # Row 1: kicker + 状态 chip（pulse dot）
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
        f'<span style="font-family:{_MONO};font-size:11px;letter-spacing:.14em;'
        f'color:{_MUT};font-weight:600;">{kicker}</span>'
        f'<span style="margin-left:auto;display:inline-flex;align-items:center;gap:7px;">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{_TEAL};'
        f'display:inline-block;animation:pulseDot 1.6s ease-in-out infinite;"></span>'
        f'<span style="font-family:{_MONO};font-size:10.5px;font-weight:700;'
        f'color:{_TEAL};">{status}</span></span>'
        f'</div>'

        # Row 2: 红肋 + 标题 + 右侧指数轨
        f'<div style="display:flex;align-items:flex-end;gap:20px;margin-top:14px;flex-wrap:wrap;">'
        f'<div style="display:flex;align-items:flex-end;gap:14px;">'
        f'<span style="width:5px;height:40px;background:{_RED};display:inline-block;'
        f'border-radius:1px;"></span>'
        f'<h1 style="font-size:32px;line-height:1;font-weight:700;'
        f'letter-spacing:-0.02em;margin:0;">{title}</h1>'
        f'</div>'
        f'<div style="margin-left:auto;display:flex;gap:0;border:1px solid #e2d3c1;'
        f'border-radius:4px;overflow:hidden;background:rgba(255,255,255,.5);">'
        f'{tiles}'
        f'</div>'
        f'</div>'

        '</div>'
        '</body></html>'
    )
    return doc, height


# ── cover(): 页面一站式接入 ──────────────────────────────────────────────────

# series_id → (中文名, 英文名)。数据源 = data/external/hc_index_comparison.csv
# （HK 指数 = iFind 增量烘焙，US = yfinance；GitHub Action cron 日刷 US 腿）。
_SID_NAMES = {
    "HSI.HK":    ("恒生指数", "HSI"),
    "HSTECH.HK": ("恒生科技", "HSTECH"),
    "HSHCI.HK":  ("恒生医疗", "HSHCI"),
    "^GSPC":     ("标普500", "S&P 500"),
    "^IXIC":     ("纳指", "NASDAQ"),
    "^NBI":      ("NBI", "NBI"),
    "XBI":       ("XBI", "XBI"),
    "^SOX":      ("费城半导体", "SOX"),
    "^SP500-35": ("标普医疗", "S&P HC"),
}

# 页面族 rail 预设（四指数）
RAIL_GLOBAL = ["HSI.HK", "HSTECH.HK", "^GSPC", "^IXIC"]     # 跨市场页
RAIL_HC     = ["HSHCI.HK", "HSTECH.HK", "^NBI", "^GSPC"]    # 医疗域页
RAIL_US     = ["^GSPC", "^IXIC", "^NBI", "^SOX"]            # 美股/SEC 页
RAIL_AI     = ["^SOX", "^IXIC", "HSTECH.HK", "^GSPC"]       # AI 域页
RAIL_STRAT  = ["XBI", "^NBI", "HSI.HK", "^GSPC"]            # 策略组合页


def cover(title: str, kicker: str, rail: list[str] | None = None,
          prefer_cn: bool = True, height: int = 152) -> None:
    """页面封面头部一站式入口：直接渲染（st.iframe），非返回 doc。

    读 hc_index_comparison 烘焙指数造四 tile 轨；数据缺失（文件空/系列不足）
    自动回退 theme.page_header(title)，页面永不因数据问题空头。"""
    import streamlit as st
    from lib import hc_overview as hco   # 函数内 import 防潜在环

    tiles: list[dict] = []
    asof = ""
    try:
        idx = hco.load_index_comparison()
        if not idx.empty:
            for sid in (rail or RAIL_GLOBAL):
                s = idx[idx["series_id"] == sid].sort_values("date")
                if len(s) >= 2:
                    lvl, prev = float(s.iloc[-1]["close"]), float(s.iloc[-2]["close"])
                    cn, en = _SID_NAMES.get(sid, (sid, sid))
                    tiles.append({"name": cn if prefer_cn else en,
                                  "lvl": f"{lvl:,.0f}",
                                  "pct": (lvl / prev - 1) * 100})
            asof = idx["date"].max().date().isoformat()
    except Exception:
        tiles = []
    if len(tiles) >= 2:
        doc, h = render(title=title, kicker=kicker,
                        status=f"EOD · {asof}", indices=tiles, height=height)
        st.iframe(doc, height=h)
    else:
        theme.page_header(title)
