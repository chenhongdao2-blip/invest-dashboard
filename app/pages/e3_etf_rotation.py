"""ETF 专栏 · 动能轮动 (RRG) — the same Relative Rotation Graph the 板块轮动 page uses,
applied to ETFs: each ETF rotates against the broad-HC benchmark (XLV), so you can
see which HC ETF is Leading / Weakening / Lagging / Improving on momentum.

Pure reuse of lib.rrg (compute_rrg + render_rrg_html) + lib.crowding (overheat guard)
+ lib.regime (cycle-level watermark), identical to pages/3b_Sector_Rotation.py's US drill.
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import crowding
from lib import db
from lib import i18n
from lib import regime
from lib import rrg
from lib import theme
from lib import ui
from lib import section_header

st.set_page_config(page_title="ETF Rotation · invest-dashboard", page_icon="🧭", layout="wide")

i18n.init_lang()
i18n.render_lang_toggle()
with st.sidebar:
    ui.sidebar_search(key_prefix="etf_rot")

prefer_cn = i18n.get_lang() == "zh"

section_header.cover(i18n.t("etf.rot.title"), "CMSI · ETF ROTATION",
                     rail=section_header.RAIL_GLOBAL, prefer_cn=i18n.get_lang() == "zh")
st.caption(i18n.t("etf.rot.caption"))

BENCH = "XLV"   # broad-HC anchor (config/domains/etf.yml benchmarks.primary)
MIN_DAYS = 120  # compute_rrg needs ~22 weeks; 120 sessions leaves margin

roster = db.query("SELECT ticker FROM universe_member WHERE domain = 'etf' ORDER BY ticker")
tickers = tuple(roster["ticker"]) if not roster.empty else ()
if not tickers or BENCH not in tickers:
    st.warning(i18n.t("etf.empty"))
    st.stop()

c1, _ = st.columns([1, 3])
tail = c1.slider(i18n.t("rot.ctrl.tail"), 4, 12, rrg.TAIL_DEFAULT, 1, key="etf_rot_tail")

closes = db.get_close_series_usd(tickers)
if closes.empty or BENCH not in closes.columns:
    st.warning(i18n.t("etf.empty"))
    st.stop()

# Plot every ETF except the benchmark itself, dropping any with too little history.
counts = closes.count()
plot = [t for t in closes.columns if t != BENCH and counts.get(t, 0) >= MIN_DAYS]
if len(plot) < 3:
    st.warning(i18n.t("etf.rot.thin"))
    st.stop()

sectors = {t: closes[t] for t in plot}
bench = closes[BENCH].dropna()
points = rrg.compute_rrg(sectors, bench, tail=tail)
# Drop low-information points: compute_rrg's 20w/10w z-scores need enough weekly
# observations; a thin-history ETF yields a (100,100) fallback that misleads in the
# Leading corner. Keep only points with a full tail of valid RRG weeks (Codex audit).
points = [p for p in points if p.n_valid >= tail]
if len(points) < 3:
    st.warning(i18n.t("etf.rot.thin"))
    st.stop()

meta: dict[str, dict] = {}
for p in points:
    cz = crowding.extension_z(closes[p.label], sma_win=50, z_win=120)
    meta[p.label] = {"overheated": crowding.is_overheated(p.quadrant, cz), "cz": cz}

# Hover cards: ETF name + 1d/5d/1m/YTD returns (same enrichment as the stock drill).
name_map = db.ticker_to_name(prefer_cn=prefer_cn)
rets = db.compute_returns(closes)


def _retspan(v) -> str:
    if v is None or v != v:
        return f"<span style='color:{theme.INK_4}'>—</span>"
    col = theme.UP if v >= 0 else theme.DOWN
    return f"<span style='color:{col};font-weight:800'>{v:+.1f}%</span>"


extra: dict[str, str] = {}
L = ("1日", "5日", "1月") if prefer_cn else ("1d", "5d", "1m")
for tk in plot:
    nm = name_map.get(tk, tk)
    head = f"<div class='nm'>{_esc(str(nm))}</div>"
    line = ""
    if tk in rets.index:
        r = rets.loc[tk]
        line = (f"<div class='rr'>{L[0]} {_retspan(r['1d_%'])} · {L[1]} {_retspan(r['5d_%'])}"
                f" · {L[2]} {_retspan(r['1m_%'])} · YTD {_retspan(r['ytd_%'])}</div>")
    extra[tk] = head + line

mkt_label = (f"医疗 ETF 动能 · vs {BENCH}" if prefer_cn else f"HC ETF momentum · vs {BENCH}")
reg = regime.regime_banner("us_drill", bench, prefer_cn=prefer_cn)
as_of = bench.index.max()
as_of = as_of.date().isoformat() if as_of is not None else None

doc, h = rrg.render_rrg_html(points, meta, prefer_cn=prefer_cn, market_label=mkt_label,
                             regime=reg, as_of=as_of, tail=tail, extra=extra)
st.iframe(doc, height=h)
st.caption(i18n.t("etf.rot.note", bench=BENCH))
