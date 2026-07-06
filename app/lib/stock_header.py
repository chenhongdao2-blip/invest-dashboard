"""个股行情 broadsheet 头 · glass KPI — lib/stock_header.py
==========================================================

Ticker Drill 顶部「行情/个股」broadsheet 改版(对照设计稿 `K线行情.dc.html`):
masthead(红导色块 + 名称 + 代码 chip + 副标行 + EOD/来源/真实挂钟)+ **玻璃 KPI 带**(5 卡:
最新价/市值/动态P/E/年初至今/20日成交额,毛玻璃 + 统一墨色顶 rule)+ 一致目标价行。

整块走 st.iframe(self-contained) —— cream + 角落径向微光背景(让毛玻璃有东西可糊),
自托管 Inter + JetBrains Mono + Space Grotesk(FONT_FACE_CSS 注入,循 Cloud 相对路径规则)。

守护规则(harness CONTRACT §4 仍有效):
- 涨 teal #0d7680 / 跌 #c8102e(本页新皮;全局 DOWN token 不动)
- 数字 tabular-nums / 无 emoji / 整页 light / 零 box-shadow / radius≤4(卡=0)
- 真实挂钟(hclk)白名单:CONTRACT GR④ 明示一处
- 字体走自托管相对路径(FONT_FACE_CSS)不引 fonts.googleapis.com

调用(pages/6_Ticker_Drill.py,拿到 KPI 值后):
    from lib import stock_header
    stock_header.render(
        name=display_name, ticker=ticker, exchange="KRX · 韩国",
        sector_sub="半导体 · 存储 …",   # backward-compat; prefer `sub`
        as_of=latest_or_none,
        sub="日K线 · MA5 / MA10 / MA20 · 成交量 · HK 09:30—16:00",
        kpis=[{"label":"最新价","value":"KRW 2,650,000","sub":"USD 1,708","color":"ink","accent":"teal"}, ...5],
        consensus="市场一致目标价 …",   # 可 None
        prefer_cn=True,
    )
  KPI color 关键字:ink / teal / up / down / flat(渲染器映射到品牌色)。
  KPI accent 已废弃(v2 统一 border-top:3px solid #1a1a1a);参数保留不报错。
"""
from __future__ import annotations

import re
from html import escape as _esc

from lib import theme

_COL = {"ink": theme.INK, "teal": theme.UP, "up": theme.UP,
        "down": theme.DOWN, "flat": theme.INK, "red": theme.CMSI_RED}


def _c(key) -> str:
    return _COL.get(key or "ink", theme.INK)


# Height budget (px):
#   masthead left col: name row ~44 + sub-line ~20 + bottom-gap ~16
#   masthead right col: eod label ~18 + clock line ~18 + asof line ~18 + padding
#   kpi grid: 5 cards ~90px ea with 13px gaps ≈ 104
#   consensus line ~24 + wrap padding ~20
#   Total comfortable budget ≈ 330 (+10 vs v1 for clock line)
_DEFAULT_HEIGHT = 330


def render(*, name: str, ticker: str, exchange: str, sector_sub: str | None = None,
           as_of: str | None, kpis: list[dict], consensus: str | None,
           prefer_cn: bool, sub: str | None = None, height: int = _DEFAULT_HEIGHT) -> None:
    import streamlit as st

    t = theme
    # KPI 卡:值色 = color(信号染色;价/市值/PE 中性墨)。
    # border-top 统一 3px solid #1a1a1a via .kc CSS(CONTRACT P8a 无 per-accent 色带)。
    cards = []
    for k in kpis:
        col = _c(k.get("color"))
        _ks = _esc(str(k.get("sub") or ""))
        cards.append(
            f'<div class="kc">'
            f'<div class="kl">{_esc(str(k.get("label", "")))}</div>'
            f'<div class="kv" style="color:{col}">{_esc(str(k.get("value", "—")))}</div>'
            f'<div class="ks">{_ks}</div></div>'
        )
    kpi_grid = (f'<div class="kgrid" style="grid-template-columns:repeat({len(kpis) or 1},1fr)">'
                f'{"".join(cards)}</div>')

    cons = f'<div class="cons">{consensus}</div>' if consensus else ""
    chip = (f'<span class="chip">{_esc(ticker)} · {_esc(exchange)}</span>' if exchange
            else f'<span class="chip">{_esc(ticker)}</span>')
    _sub_text = sub or sector_sub
    sub_html = f'<div class="sub">{_esc(_sub_text)}</div>' if _sub_text else ""
    eod_lbl = "EOD 数据流" if prefer_cn else "EOD DATA FEED"
    asof = ((f"截至 {as_of} · 来源 yfinance" if prefer_cn else f"as of {as_of} · yfinance") if as_of
            else ("来源 yfinance" if prefer_cn else "yfinance"))

    css = f"""
{t.FONT_FACE_CSS}
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{height:100%;font-family:{t.FONT_STACK};color:{t.INK};
      font-feature-settings:'tnum','ss01';-webkit-font-smoothing:antialiased;color-scheme:light}}
    body{{position:relative;background:{t.PAPER};overflow:hidden}}
    .glow{{position:absolute;inset:0;z-index:0;
      background:radial-gradient(900px 520px at 10% -8%,rgba(200,16,46,.09),transparent 60%),
                 radial-gradient(820px 520px at 94% 4%,rgba(13,118,128,.10),transparent 60%)}}
    .wrap{{position:relative;z-index:1;padding:6px 4px}}
    .mast{{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
      border-bottom:2px solid {t.INK};padding-bottom:16px}}
    .mid{{display:flex;align-items:center;gap:15px;min-width:0}}
    .tick{{width:5px;height:44px;background:{t.CMSI_RED};display:inline-block;flex:none;border-radius:1px}}
    .nm{{font-size:30px;font-weight:700;letter-spacing:-.01em;line-height:1.05;
      font-family:{t.FONT_DISPLAY}}}
    .chip{{font-family:{t.FONT_MONO};font-size:13px;font-weight:600;color:{t.INK_3};
      border:1px solid {t.PAPER_EDGE_SOFT};padding:3px 9px;white-space:nowrap}}
    .nmrow{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
    .sub{{font-family:{t.FONT_MONO};font-size:12.5px;letter-spacing:.04em;color:{t.INK_3};
      margin-top:6px}}
    .right{{text-align:right;flex:none}}
    .eod{{display:flex;align-items:center;gap:8px;justify-content:flex-end;
      font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.16em;text-transform:uppercase;
      color:{t.UP};font-weight:600}}
    .dot{{width:8px;height:8px;border-radius:50%;background:{t.UP};display:inline-block;
      animation:liveBlink 1.5s ease-in-out infinite}}
    @keyframes liveBlink{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
    .clk{{font-family:{t.FONT_MONO};font-size:12px;color:{t.INK_3};margin-top:4px;text-align:right}}
    .asof{{font-family:{t.FONT_MONO};font-size:12px;color:{t.INK_3};margin-top:4px}}
    .kgrid{{display:grid;gap:13px;margin-top:18px}}
    .kc{{background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(14px);
      backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);
      border-top:3px solid {t.INK};border-radius:0;padding:15px 17px}}
    .kl{{font-family:{t.FONT_MONO};font-size:10px;letter-spacing:.1em;text-transform:uppercase;
      color:{t.INK_3};font-weight:600}}
    .kv{{font-size:26px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums;
      margin-top:9px;line-height:1.05;word-break:break-word}}
    .ks{{font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:6px}}
    .cons{{font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};margin-top:11px;
      letter-spacing:.02em}}
    @media (max-width:820px){{.kgrid{{grid-template-columns:repeat(2,1fr)!important}}}}
    """

    # Wall-clock update — the ONE GR④-whitelisted timer in this file.
    # IIFE runs u() immediately (no --:--:-- flash) then keeps updating every 1s.
    _clk_js = (
        '<script>!function(){function u(){var d=new Date();'
        'document.getElementById("hclk").textContent='
        '[d.getHours(),d.getMinutes(),d.getSeconds()]'
        '.map(function(n){return n<10?"0"+n:n}).join(":")}'
        'u();setInterval(u,1000)}();</script>'
    )

    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="glow"></div><div class="wrap">'
        '<div class="mast"><div class="mid"><span class="tick"></span><div>'
        f'<div class="nmrow"><span class="nm">{_esc(name)}</span>{chip}</div>{sub_html}'
        '</div></div>'
        f'<div class="right"><div class="eod"><span class="dot"></span>{eod_lbl}</div>'
        f'<div class="clk"><span id="hclk">--:--:--</span></div>'
        f'<div class="asof">{_esc(asof)}</div></div></div>'
        f'{kpi_grid}{cons}'
        f'</div>{_clk_js}</body></html>'
    )
    st.iframe(doc, height=height)


# ── 多空看板 BULL vs BEAR(催化剂 / 风险点 玻璃卡)──────────────────────────────
def _parse_items(md: str) -> list[dict]:
    """把 wiki memo 的 催化剂/风险点 markdown 解析成 [{title, desc}]。
    支持 `- **标题**: 描述` / `- 标题:描述` / `- 纯文本`(纯文本 → title 即整行,无 desc)。"""
    items: list[dict] = []
    for raw in (md or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        m = re.match(r"^(?:[-*•]|\d+[.)])\s+(.*)$", s)
        if m:
            s = m.group(1).strip()
        title, desc = None, None
        b = re.match(r"^\*\*(.+?)\*\*[:：]?\s*(.*)$", s)
        if b:
            title, desc = b.group(1).strip(), (b.group(2).strip() or None)
        else:
            for sep in ("：", ":"):
                if sep in s and len(s.split(sep, 1)[0]) <= 24:   # 只在短前缀处当 title:desc
                    a, c = s.split(sep, 1)
                    title, desc = a.strip(), (c.strip() or None)
                    break
            if title is None:
                title = s
        title = title.replace("**", "")
        desc = desc.replace("**", "") if desc else None
        if title:
            items.append({"title": title, "desc": desc})
    return items


def render_bull_bear(bull_md: str | None, bear_md: str | None, *, prefer_cn: bool,
                     contradiction: str | None = None) -> bool:
    """多空看板:催化剂→BULL(teal)/ 风险点→BEAR(red)两张玻璃卡 + 可选矛盾 callout。
    成功 True;两边都空 False(上层回退原 expander)。"""
    import streamlit as st

    bull = _parse_items(bull_md or "")
    bear = _parse_items(bear_md or "")
    if not bull and not bear:
        return False

    t = theme

    def _items_html(items: list[dict], accent: str) -> str:
        rows = []
        for it in items:
            d = (f'<div class="bd">{_esc(it["desc"])}</div>' if it.get("desc") else "")
            rows.append(f'<div class="bi" style="border-left:2px solid {accent}">'
                        f'<div class="bt">{_esc(it["title"])}</div>{d}</div>')
        return "".join(rows)

    bull_lbl = ("催化剂 · BULL" if prefer_cn else "Catalysts · BULL")
    bear_lbl = ("风险点 · BEAR" if prefer_cn else "Risks · BEAR")
    n_lbl = (lambda n: f"{n} 项") if prefer_cn else (lambda n: f"{n}")

    bull_card = (
        f'<div class="card" style="border-top:3px solid {t.UP}">'
        f'<div class="ch"><span class="ca" style="color:{t.UP}">▲</span>'
        f'<span class="cl" style="color:{t.UP}">{bull_lbl}</span>'
        f'<span class="cn">{n_lbl(len(bull))}</span></div>'
        f'<div class="cb">{_items_html(bull, "rgba(13,118,128,.32)")}</div></div>'
    ) if bull else ""
    bear_card = (
        f'<div class="card" style="border-top:3px solid {t.CMSI_RED}">'
        f'<div class="ch"><span class="ca" style="color:{t.CMSI_RED}">▼</span>'
        f'<span class="cl" style="color:{t.CMSI_RED}">{bear_lbl}</span>'
        f'<span class="cn">{n_lbl(len(bear))}</span></div>'
        f'<div class="cb">{_items_html(bear, "rgba(200,16,46,.30)")}</div></div>'
    ) if bear else ""

    callout = ""
    if contradiction:
        _lines = []
        for ln in contradiction.splitlines():
            s = ln.strip()
            if not s:
                continue
            s = re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", s).replace("**", "")
            _lines.append(_esc(s))
        _ctext = "<br>".join(_lines)
        if _ctext:
            callout = (
                f'<div class="callout"><div class="col-eb">⚠ '
                f'{"矛盾与待验证 · CONTRADICTION" if prefer_cn else "CONTRADICTION"}</div>'
                f'<div class="col-tx">{_ctext}</div></div>'
            )

    cols = 2 if (bull and bear) else 1
    h = 110 + 58 * max(len(bull), len(bear), 1) + (96 if contradiction else 0)
    h = min(h, 920)

    css = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{height:100%;font-family:{t.FONT_STACK};color:{t.INK};
      font-feature-settings:'tnum','ss01';-webkit-font-smoothing:antialiased;color-scheme:light}}
    body{{position:relative;background:{t.PAPER};overflow:hidden}}
    .glow{{position:absolute;inset:0;z-index:0;background:
      radial-gradient(700px 420px at 4% -14%,rgba(13,118,128,.07),transparent 60%),
      radial-gradient(700px 420px at 98% 6%,rgba(200,16,46,.07),transparent 60%)}}
    .wrap{{position:relative;z-index:1;padding:4px 2px}}
    .grid{{display:grid;grid-template-columns:repeat({cols},1fr);gap:15px}}
    .card{{background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(14px);
      backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);
      border-radius:0;padding:18px 20px}}
    .ch{{display:flex;align-items:center;gap:8px;margin-bottom:15px}}
    .ca{{font-size:14px}}
    .cl{{font-size:14px;font-weight:700;letter-spacing:.02em}}
    .cn{{margin-left:auto;font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3}}}
    .cb{{display:flex;flex-direction:column;gap:13px}}
    .bi{{padding-left:13px}}
    .bt{{font-size:14px;font-weight:700;color:{t.INK};line-height:1.4}}
    .bd{{font-size:13px;line-height:1.55;color:{t.INK_2};margin-top:3px}}
    .callout{{background:{t.PAPER_DEEP};border-left:3px solid {t.CMSI_RED};
      padding:14px 20px;margin-top:15px}}
    .col-eb{{font-family:{t.FONT_MONO};font-size:11px;letter-spacing:.12em;
      text-transform:uppercase;color:{t.CMSI_RED};font-weight:600;margin-bottom:7px}}
    .col-tx{{font-size:13px;line-height:1.6;color:{t.INK_2}}}
    @media (max-width:760px){{.grid{{grid-template-columns:1fr}}}}
    """
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="glow"></div><div class="wrap">'
        f'<div class="grid">{bull_card}{bear_card}</div>{callout}'
        '</div></body></html>'
    )
    st.iframe(doc, height=h)
    return True
