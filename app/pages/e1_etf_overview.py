"""ETF 专栏 · 总览 — rich 行情卡片 (George's chosen shape, v3).

v2 (plain st.expander text rows) was rejected as 太单调. The fix: each ETF is a
**rich HTML card** (self-contained doc in an st.iframe, same pattern as the heatmap /
RRG) that you read at a glance —
  · big ticker + name + sub-sector,
  · a price sparkline (area-filled, teal-up / red-down — locked convention),
  · color-coded 1M / YTD / 5D return tiles + AUM,
  · the top-5 holdings inline: name · weight bar · weight% · that holding's 1M return,
  · a 3px left accent tinted by the ETF's own 1M direction.
Beneath each card a st.expander opens the FULL holdings table (rank · ticker · name ·
weight bar · per-constituent 1M / YTD + a "+N more" tail) with the per-row Ticker-Drill
deep-link — so 成分股 + 权重 + 表现 stay one click away, "展开还能看到个股".

Returns reuse db.compute_returns over the price DB; holdings reuse lib.etf_panel. No new
analytics — only a richer presentation layer.
"""
from __future__ import annotations

import re
from html import escape as _esc
from urllib.parse import quote

import pandas as pd
import streamlit as st

from lib import db
from lib import etf_panel
from lib import heatmap as hm
from lib import i18n
from lib import theme
from lib import ui
from lib import section_header

st.set_page_config(page_title="ETF Overview · invest-dashboard", page_icon="🧺", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()
with st.sidebar:
    ui.sidebar_search(key_prefix="etf_ovw")

prefer_cn = i18n.get_lang() == "zh"

# Fixed, friendly sub-sector order (broad anchor first); ETFs within sorted by AUM.
SUBSECTOR_ORDER = ["etf_broad", "etf_biotech", "etf_pharma", "etf_devices",
                   "etf_providers", "etf_genomics"]
TAIL_CAP = 40
CARD_H = 188   # iframe height — fixed doc (header + KPI row + top-5 holdings strip)

t = theme


def _sub(sec: str) -> str:
    return (hm._SECTOR_CN if prefer_cn else hm._SECTOR_EN).get(sec, sec)


_CARD_CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{t.PAPER};font-family:{t.FONT_STACK};color:{t.INK};
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}}
.card{{background:#fffaf4;border:1px solid {t.PAPER_EDGE};border-radius:10px;
  padding:13px 18px 12px;box-shadow:0 1px 3px rgba(26,26,26,.07)}}
.top{{display:flex;align-items:flex-start;gap:18px}}
.idblk{{flex:0 0 auto;min-width:150px}}
.tkr{{font-family:{t.FONT_MONO};font-size:23px;font-weight:800;letter-spacing:.3px;
  color:{t.INK};line-height:1.02}}
.nm{{font-size:12.5px;color:{t.INK_2};margin-top:3px;max-width:230px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.sub{{font-size:10px;color:{t.INK_3};text-transform:uppercase;letter-spacing:.7px;margin-top:3px}}
.spkblk{{flex:0 0 auto;align-self:center;padding-top:2px}}
.spk{{display:block}}
.kpis{{display:flex;gap:18px;flex:1 1 auto;justify-content:flex-end;align-items:flex-start}}
.kpi{{text-align:right;min-width:54px}}
.kl{{font-size:9.5px;color:{t.INK_3};text-transform:uppercase;letter-spacing:.5px}}
.kv{{font-family:{t.FONT_MONO};font-size:18px;font-weight:800;line-height:1.25;margin-top:2px;
  font-variant-numeric:tabular-nums}}
.kv.val{{color:{t.INK};font-size:16px}}
.up{{color:{t.UP}}} .down{{color:{t.DOWN}}} .flat{{color:{t.INK_4}}}
.gly{{font-size:.74em;margin-right:1px;vertical-align:.5px}}
.holds{{margin-top:11px;padding-top:10px;border-top:1px solid {t.PAPER_RULE}}}
.hlbl{{font-size:9.5px;color:{t.INK_3};text-transform:uppercase;letter-spacing:.7px;margin-bottom:7px}}
.chips{{display:flex;gap:16px}}
.chip{{flex:1 1 0;min-width:0}}
.cn{{font-size:11.5px;color:{t.INK_2};font-weight:600;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;line-height:1.25}}
.bar{{height:4px;background:{t.PAPER_BAND};border-radius:2px;margin:5px 0 4px;overflow:hidden}}
.fill{{height:100%;background:{t.INK_3};border-radius:2px}}
.cmeta{{font-family:{t.FONT_MONO};font-size:11px;color:{t.INK_3};
  display:flex;gap:7px;align-items:baseline;font-variant-numeric:tabular-nums}}
.wt{{color:{t.INK};font-weight:700}}
"""


def _area_spark(vals, w=184, h=46, pad=4, uid="") -> str:
    """Area-filled sparkline (teal-up / red-down) for the card hero."""
    vals = [float(v) for v in (vals or []) if not pd.isna(v)]
    if len(vals) < 2 or vals[0] == 0:
        return f'<span class="flat" style="font-size:11px">—</span>'
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1.0
    step = (w - 2 * pad) / (len(vals) - 1)
    pts = [(pad + i * step, h - pad - (v - mn) / rng * (h - 2 * pad)) for i, v in enumerate(vals)]
    chg = vals[-1] / vals[0] - 1
    col = t.UP if chg >= 0 else t.DOWN
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{h - pad:.1f} {line} {pts[-1][0]:.1f},{h - pad:.1f}"
    lx, ly = pts[-1]
    gid = f"g{uid}"
    return (
        f'<svg class="spk" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{col}" stop-opacity="0.20"/>'
        f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#{gid})"/>'
        f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="1.8" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{col}"/></svg>'
    )


def _kpi(label: str, v) -> str:
    if v is None or pd.isna(v):
        return f'<div class="kpi"><div class="kl">{_esc(label)}</div><div class="kv flat">—</div></div>'
    cls = "up" if v > 0 else ("down" if v < 0 else "flat")
    gly = "▲" if v > 0 else ("▼" if v < 0 else "·")
    sign = "+" if v > 0 else ""
    return (f'<div class="kpi"><div class="kl">{_esc(label)}</div>'
            f'<div class="kv {cls}"><span class="gly">{gly}</span>{sign}{v:.1f}%</div></div>')


def _val(label: str, text: str) -> str:
    """Non-directional value tile (price / AUM) — ink, no sign color."""
    return (f'<div class="kpi"><div class="kl">{_esc(label)}</div>'
            f'<div class="kv val">{_esc(text)}</div></div>')


def _chip(nm: str, w_pct: float, ret1m, wmax: float) -> str:
    barw = max(5.0, min(100.0, (w_pct / wmax * 100.0) if wmax else 0.0))
    if ret1m is None or pd.isna(ret1m):
        rspan = '<span class="flat">—</span>'
    else:
        rcls = "up" if ret1m >= 0 else "down"
        rspan = f'<span class="{rcls}">{ret1m:+.1f}%</span>'
    return (
        f'<div class="chip"><div class="cn">{_esc(nm)}</div>'
        f'<div class="bar"><div class="fill" style="width:{barw:.0f}%"></div></div>'
        f'<div class="cmeta"><span class="wt">{w_pct:.1f}%</span>{rspan}</div></div>'
    )


def _crow(sym):
    """(1m_%, ytd_%) for a constituent, or (NA, NA) if not in the price DB."""
    if sym in _cret.index:
        r = _cret.loc[sym]
        return r.get("1m_%"), r.get("ytd_%")
    return pd.NA, pd.NA


section_header.cover(i18n.t("etf.title"), "CMSI · ETF",
                     rail=section_header.RAIL_GLOBAL, prefer_cn=i18n.get_lang() == "zh")
as_of = db.latest_snapshot_date() or "—"
st.caption(i18n.t("etf.caption", date=as_of))

roster = db.query("SELECT ticker, sector FROM universe_member WHERE domain = 'etf' ORDER BY ticker")
hold = etf_panel.load_etf_holdings()
meta = etf_panel.etf_meta()
if roster.empty:
    st.warning(i18n.t("etf.empty"))
    st.stop()

sub_of = dict(zip(roster["ticker"], roster["sector"]))

# ETF-level returns + closes (closes reused for the card sparkline) + AUM.
etf_tickers = tuple(roster["ticker"])
etf_closes = db.get_close_series_usd(etf_tickers)
etf_rets = db.compute_returns(etf_closes)
name_map = db.ticker_to_name(prefer_cn=prefer_cn)
uni_csv = etf_panel.load_etf_universe()
aum_of = dict(zip(uni_csv.get("ticker", []), uni_csv.get("aum", []))) if not uni_csv.empty else {}
cov_map = meta.get("weight_sum_pct_by_etf", {}) or {}

# Constituent returns: pass ALL weighted holding symbols to the price query and let
# prices_daily decide availability (missing ones render "—"). Codex audit: don't
# pre-filter on universe_member.all_tickers.
_csyms = []
if not hold.empty:
    _csyms = sorted({str(s) for s in hold[hold["rank"].notna()]["symbol"].dropna()})
_cret = db.compute_returns(db.get_close_series_usd(tuple(_csyms)))


def _card_doc(tkr: str) -> str:
    er = etf_rets.loc[tkr] if tkr in etf_rets.index else None
    m1 = er.get("1m_%") if er is not None else None
    ytd = er.get("ytd_%") if er is not None else None
    d5 = er.get("5d_%") if er is not None else None
    last = er.get("last") if er is not None else None
    last_s = f"{last:,.2f}" if last is not None and pd.notna(last) else "—"
    aum = aum_of.get(tkr)
    aum_s = f"${aum / 1e9:.1f}B" if aum and pd.notna(aum) else "—"
    nm = name_map.get(tkr, tkr)
    sub = _sub(sub_of.get(tkr, ""))
    series = etf_closes[tkr].dropna().tail(90).tolist() if tkr in etf_closes.columns else []
    spark = _area_spark(series, uid=re.sub(r"\W", "", tkr))
    accent = t.UP if (m1 is not None and not pd.isna(m1) and m1 >= 0) else (
        t.DOWN if (m1 is not None and not pd.isna(m1)) else t.PAPER_EDGE)

    weighted, tail = etf_panel.holdings_for(hold, tkr)
    chips = ""
    if not weighted.empty:
        wmax = float(pd.to_numeric(weighted["weight_pct"], errors="coerce").max() or 0)
        for _, r in weighted.head(5).iterrows():
            sym = str(r["symbol"]) if pd.notna(r["symbol"]) else ""
            hn = str(r.get("name") or sym)
            wp = float(r["weight_pct"]) if pd.notna(r["weight_pct"]) else 0.0
            chips += _chip(hn, wp, _crow(sym)[0] if sym else pd.NA, wmax)
    holds_html = (
        f'<div class="holds"><div class="hlbl">{_esc(i18n.t("etf.card.holdings"))}</div>'
        f'<div class="chips">{chips}</div></div>'
    ) if chips else ""

    body = (
        f'<div class="card" style="border-left:4px solid {accent}">'
        f'<div class="top">'
        f'<div class="idblk"><div class="tkr">{_esc(tkr)}</div>'
        f'<div class="nm">{_esc(str(nm))}</div><div class="sub">{_esc(str(sub))}</div></div>'
        f'<div class="spkblk">{spark}</div>'
        f'<div class="kpis">'
        f'{_val(i18n.t("etf.col.last"), last_s)}'
        f'{_kpi(i18n.t("etf.col.m1"), m1)}{_kpi(i18n.t("etf.col.ytd"), ytd)}'
        f'{_kpi(i18n.t("etf.col.d5"), d5)}'
        f'{_val(i18n.t("etf.col.aum"), aum_s)}'
        f'</div></div>{holds_html}</div>'
    )
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<style>{t.FONT_FACE_CSS}{_CARD_CSS}</style></head><body>{body}</body></html>")


def _render_full_holdings(tkr: str) -> None:
    """Full holdings table inside the per-ETF expander (rank · ticker · name · weight
    bar · per-constituent 1M / YTD + Ticker-Drill deep-link + "+N more" tail)."""
    weighted, tail = etf_panel.holdings_for(hold, tkr)
    n_total = (0 if weighted.empty else int(weighted["rank"].notna().sum())) + len(tail)
    with st.expander(i18n.t("etf.card.expand", n=n_total)):
        if weighted.empty:
            st.caption("—")
            return
        hd = weighted[["rank", "symbol", "name", "weight_pct"]].copy()
        hd["m1"] = [_crow(str(s))[0] if pd.notna(s) else pd.NA for s in hd["symbol"]]
        hd["ytd"] = [_crow(str(s))[1] if pd.notna(s) else pd.NA for s in hd["symbol"]]
        hd["nav"] = [
            f"/Ticker_Drill?ticker={quote(str(s).strip(), safe='.-')}"
            if pd.notna(s) and str(s).strip() else ""
            for s in hd["symbol"]
        ]
        ui.render_html_table(
            hd,
            int_cols=["rank"],
            text_cols=["symbol", "name"],
            bar_cols=["weight_pct"],
            extra_formats={"weight_pct": "%.1f%%"},
            pct_cols=["m1", "ytd"],
            nav_cols=["nav"],
            column_labels={
                "rank": i18n.t("hc_etf.col.rank"),
                "symbol": i18n.t("hc_etf.col.symbol"),
                "name": i18n.t("hc_etf.col.name"),
                "weight_pct": i18n.t("hc_etf.col.weight"),
                "m1": i18n.t("etf.col.m1"),
                "ytd": i18n.t("etf.col.ytd"),
                "nav": "",
            },
            hide_index=True,
            height=80 + 26 * len(hd),
        )
        notes = []
        cov = cov_map.get(tkr)
        if cov is not None:
            notes.append(i18n.t("hc_etf.coverage", n=int(weighted["rank"].notna().sum()),
                                cov=f"{cov:.1f}"))
        if tail:
            if len(tail) <= TAIL_CAP:
                notes.append(i18n.t("hc_etf.tail_more", n=len(tail), syms=", ".join(tail)))
            else:
                notes.append(i18n.t("hc_etf.tail_more_trunc", n=len(tail),
                                    shown=TAIL_CAP, syms=", ".join(tail[:TAIL_CAP])))
        if notes:
            st.caption("  ·  ".join(notes))


# Render: sub-sector groups, ETFs within sorted by AUM desc — full-width rich card +
# full-holdings expander stacked (1-up; the horizontal card carries the density).
present = [s for s in SUBSECTOR_ORDER if s in set(roster["sector"])]
for sec in present:
    members = [t_ for t_ in roster[roster["sector"] == sec]["ticker"]]
    members.sort(key=lambda x: (aum_of.get(x) or 0), reverse=True)
    st.markdown(f"#### {_sub(sec)}")
    for tkr in members:
        st.iframe(_card_doc(tkr), height=CARD_H)
        _render_full_holdings(tkr)

st.caption(i18n.t("etf.click_hint"))
theme.provenance(i18n.t("etf.provenance", src="yfinance EOD", date=as_of))
