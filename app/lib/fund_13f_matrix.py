"""Holder × company 13F matrix — FactSet-style "Institutional Holders" grid.

Rows = the 12 HC funds (ranked by their combined value across the shown names),
columns = top consensus holdings. Each cell is that fund's position value ($M),
colored by the fund's OWN QoQ move in the name (teal = NEW/ADD, red = TRIM,
ink = UNCH) — one more dimension than the FactSet original, same house
convention (color the TEXT, never the cell background).

Column headers carry the price context that replaced the old consensus table's
spark column: ticker + mini 6M sparkline + move since the 13F quarter end.

Rendered as a self-contained HTML doc in an iframe (same pattern as
ui.render_html_table / the ETF rich cards): full CSS control, no glide-grid
canvas, OS dark-mode can't bleed in.
"""

from __future__ import annotations

import html as _html

import streamlit as st

from lib import theme as t

_CELL_W = 74          # px per company column
_NAME_W = 148         # sticky fund-name column
_TOTAL_W = 78


def _esc(s) -> str:
    return _html.escape(str(s))


def _fmt_m(v: float) -> str:
    """USD value → $M display, FactSet-style: `<$1` under 0.5M, comma-thousands."""
    m = v / 1e6
    if m < 0.5:
        return "&lt;$1"
    return f"${m:,.0f}"


def _spark(closes: list[float] | None, w: int = 58, h: int = 16, pad: int = 2) -> str:
    """Tiny header sparkline — teal/red by window direction (same as ui._spark_svg)."""
    vals = [float(v) for v in (closes or [])]
    if len(vals) < 2 or vals[0] == 0:
        return ""
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1.0
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = " ".join(
        f"{pad + i * step:.1f},{h - pad - (v - mn) / rng * (h - 2 * pad):.1f}"
        for i, v in enumerate(vals)
    )
    col = t.UP if vals[-1] >= vals[0] else t.DOWN
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline points="{pts}" fill="none" stroke="{col}" '
            f'stroke-width="1.3" stroke-linejoin="round"/></svg>')


def _since(prices: dict, tkr: str, period: str) -> float | None:
    """Move since the last close ≤ 13F quarter end (mirrors fund_13f.attach_prices)."""
    p = prices.get(tkr)
    if not p or not period:
        return None
    anchor = None
    for d, c in zip(p["dates"], p["closes"]):
        if d <= period:
            anchor = c
        else:
            break
    if not anchor:
        return None
    return p["closes"][-1] / anchor - 1


_QOQ_COLOR = {"NEW": t.UP, "ADD": t.UP, "TRIM": t.DOWN}
_QOQ_MARK = {"NEW": "●", "ADD": "▲", "TRIM": "▼"}


def render_matrix(data: dict, *, top_n: int = 15, prefer_cn: bool = True,
                  labels: dict[str, str] | None = None) -> None:
    """labels keys: holder / total / legend_new / legend_add / legend_trim / legend_unch."""
    lb = labels or {}
    cons = (data.get("aggregate") or {}).get("consensus") or []
    cols = [c for c in cons if c.get("by_fund")][:top_n]
    if not cols:
        return
    prices = data.get("prices") or {}
    period = str(data.get("latest_period") or "")

    # rows: every fund holding ≥1 shown name, ranked by combined value across cols
    fund_tot: dict[str, float] = {}
    for c in cols:
        for f, cell in c["by_fund"].items():
            fund_tot[f] = fund_tot.get(f, 0.0) + cell["value"]
    funds = sorted(fund_tot, key=lambda f: -fund_tot[f])

    # --- header row: ticker + mini spark + since-Q-end ---
    heads = ""
    for c in cols:
        tk = c.get("ticker") or ""
        label = tk or str(c.get("issuer", ""))[:10]
        sq = _since(prices, tk, period) if tk else None
        if sq is None:
            sq_html = f'<span style="color:{t.INK_3}">—</span>'
        else:
            scol = t.UP if sq >= 0 else t.DOWN
            sq_html = f'<span style="color:{scol};font-weight:700">{sq * 100:+.0f}%</span>'
        spark = _spark((prices.get(tk) or {}).get("closes")) if tk else ""
        heads += (
            f'<th style="width:{_CELL_W}px;min-width:{_CELL_W}px;padding:7px 4px 5px;'
            f'vertical-align:bottom;border-bottom:1px solid {t.CMSI_RED};background:{t.PAPER_BAND}">'
            f'<div style="font-family:{t.FONT_MONO};font-size:11px;font-weight:700;'
            f'color:{t.INK};letter-spacing:.02em">{_esc(label)}</div>'
            f'<div style="height:16px;margin:2px 0 1px">{spark}</div>'
            f'<div style="font-family:{t.FONT_MONO};font-size:10px">{sq_html}</div></th>'
        )

    # --- body rows ---
    body = ""
    for i, f in enumerate(funds):
        cells = ""
        for c in cols:
            cell = c["by_fund"].get(f)
            if not cell:
                cells += (f'<td style="color:{t.INK_3};text-align:center;'
                          f'font-size:11px">–</td>')
                continue
            qoq = cell.get("qoq", "UNCH")
            col = _QOQ_COLOR.get(qoq, t.INK_2)
            mark = _QOQ_MARK.get(qoq, "")
            mark_html = (f'<span style="font-size:8px;vertical-align:1px">{mark}</span> '
                         if mark else "")
            cells += (
                f'<td style="text-align:right;font-family:{t.FONT_MONO};font-size:12px;'
                f'font-variant-numeric:tabular-nums;color:{col};'
                f'font-weight:{700 if mark else 400}">{mark_html}{_fmt_m(cell["value"])}</td>'
            )
        # fund short name: drop the legal-suffix tail for row width
        short = (f.replace(" Advisors", "").replace(" Management", "")
                 .replace(" Investments", "").replace(" Capital Advisors", " Capital")
                 .replace(" Group", ""))
        body += (
            f'<tr style="border-bottom:1px solid {t.PAPER_RULE}">'
            f'<td style="position:sticky;left:0;background:{t.PAPER};z-index:1;'
            f'font-size:12px;color:{t.INK};padding:0 8px;white-space:nowrap;'
            f'width:{_NAME_W}px;min-width:{_NAME_W}px">'
            f'<span style="font-family:{t.FONT_MONO};font-size:10px;color:{t.INK_3};'
            f'display:inline-block;width:18px">{i + 1}</span>{_esc(short)}</td>'
            f'<td style="text-align:right;font-family:{t.FONT_MONO};font-size:12px;'
            f'font-weight:700;color:{t.INK};font-variant-numeric:tabular-nums;'
            f'padding-right:8px">{_fmt_m(fund_tot[f])}</td>'
            f'{cells}</tr>'
        )

    holder_lbl = lb.get("holder", "机构" if prefer_cn else "Holder")
    total_lbl = lb.get("total", "合计" if prefer_cn else "Total")
    th_base = (f'padding:7px 6px;vertical-align:bottom;text-align:right;'
               f'border-bottom:1px solid {t.CMSI_RED};background:{t.PAPER_BAND};'
               f'font-size:10px;letter-spacing:.08em;text-transform:uppercase;'
               f'font-weight:600;color:{t.CMSI_RED}')
    legend = (
        f'<span style="color:{t.UP};font-weight:700">● {lb.get("legend_new", "新建")}</span>　'
        f'<span style="color:{t.UP};font-weight:700">▲ {lb.get("legend_add", "加仓")}</span>　'
        f'<span style="color:{t.DOWN};font-weight:700">▼ {lb.get("legend_trim", "减仓")}</span>　'
        f'<span style="color:{t.INK_2}">{lb.get("legend_unch", "无标记＝持平")}</span>'
    )

    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{t.FONT_FACE_CSS}"
        f":root{{color-scheme:light}}*{{box-sizing:border-box}}"
        f"html,body{{margin:0;padding:0;background:{t.PAPER};color:{t.INK};"
        f"font-family:{t.FONT_STACK};-webkit-font-smoothing:antialiased}}"
        f"td{{padding:0 6px;height:32px;white-space:nowrap}}"
        f"</style></head><body>"
        f'<div style="overflow-x:auto;border:1px solid {t.PAPER_EDGE}">'
        f'<table style="border-collapse:collapse;width:max-content;min-width:100%">'
        f'<thead><tr>'
        f'<th style="{th_base};text-align:left;position:sticky;left:0;z-index:2;'
        f'width:{_NAME_W}px;min-width:{_NAME_W}px">{_esc(holder_lbl)}</th>'
        f'<th style="{th_base};width:{_TOTAL_W}px;min-width:{_TOTAL_W}px">{_esc(total_lbl)}</th>'
        f'{heads}</tr></thead><tbody>{body}</tbody></table></div>'
        f'<div style="font-size:11px;color:{t.INK_3};margin-top:6px;'
        f'font-family:{t.FONT_STACK}">{legend}　·　$M</div>'
        "</body></html>"
    )
    st.iframe(doc, height=64 + 32 * len(funds) + 40)
