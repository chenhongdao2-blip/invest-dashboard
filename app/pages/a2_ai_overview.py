"""AI domain overview — 6 supply-chain layers summary (mirrors Healthcare overview).

Mirror of `2_🏥_Healthcare.py` with domain='ai', reading config/domains/ai.yml.
Empty-data safe: sectors with no prices yet are skipped; an empty universe shows
the standard "backfill needed" warning rather than crashing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n
from lib import sector_overview as so


def _render_pct_table(
    df: pd.DataFrame,
    pct_cols: list[str],
    num_cols: list[str] | None = None,
    column_labels: dict | None = None,
) -> None:
    """Sort-bug-safe: numeric DataFrame + column_config + Styler color (delegates to ui)."""
    text_cols = [c for c in df.columns if c not in pct_cols and (num_cols is None or c not in num_cols)]
    extra_formats = {c: "%.2f" for c in (num_cols or []) if c in df.columns}
    ui.render_styled_table(
        df,
        pct_cols=pct_cols,
        text_cols=text_cols,
        extra_formats=extra_formats,
        height=360,
        heatmap=True,
        column_labels=column_labels,
    )


st.set_page_config(page_title="AI Overview · invest-dashboard", page_icon="🏥", layout="wide")

# --- Sidebar global search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="ai_ov")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "ai.yml"


cfg = db.load_domain_cfg(str(DOMAIN_CFG))
i18n.init_lang()
i18n.render_lang_toggle()
theme.page_header(i18n.t("ai.ov.title"))
st.caption(cfg.get("description", "").strip())
prefer_cn = i18n.get_lang() == "zh"
theme.page_radial_wash(1240)

# --- 6 sector aggregate summary ---
theme.section_header(i18n.t("hc.section.summary"), meta=i18n.t("hc.section.summary_meta"))

rows = []
all_returns_by_sector: dict[str, pd.DataFrame] = {}
for sec in cfg["sectors"]:
    uni = db.sector_tickers("ai", sec["id"])
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        continue
    closes = db.get_close_series_usd(tickers)   # USD-converted for fair cross-region compare
    rets = db.compute_returns(closes)
    if rets.empty:
        continue
    all_returns_by_sector[sec["id"]] = rets
    rows.append({
        "Sector": i18n.sector_name(sec["id"]),
        "Tickers": len(tickers),
        "1D % avg": rets["1d_%"].mean(),
        "5D % avg": rets["5d_%"].mean(),
        "1M % avg": rets["1m_%"].mean(),
        "YTD % avg": rets["ytd_%"].mean(),
        "Benchmark": sec.get("benchmark", "—"),
    })

if not rows:
    st.warning(i18n.t("hc.summary.empty"))
else:
    summary = pd.DataFrame(rows).set_index("Sector")
    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    _render_pct_table(
        summary,
        pct_cols=pct_cols,
        column_labels={
            "Sector": i18n.t("hc.col.sector"),
            "Tickers": i18n.t("hc.col.tickers"),
            "Benchmark": i18n.t("hc.col.benchmark"),
            "1D % avg": i18n.t("hc.col.1d_avg"),
            "5D % avg": i18n.t("hc.col.5d_avg"),
            "1M % avg": i18n.t("hc.col.1m_avg"),
            "YTD % avg": i18n.t("hc.col.ytd_avg"),
        },
    )

st.divider()

# --- Domain benchmark snapshot (AI: ^SOX primary + peers) — [10] sector_overview ---
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["^SOX", "SMH", "AIQ", "512480.SS", "515880.SS", "442580.KS"]
    _present = [s for s in focus if s in bench_df.index]
    if _present:
        _cs = bm.close_series()
        _gspc_ytd = bench_df.loc["^GSPC", "ytd_%"] if "^GSPC" in bench_df.index else None
        _pmap = {"1日": "1d_%", "5日": "5d_%", "1月": "1m_%", "3月": "3m_%", "YTD": "ytd_%"}
        _rows = []
        for _s in _present:
            _r = bench_df.loc[_s]
            _ser = _cs.get(_s)
            _spark = ([float(v) for v in _ser.dropna().sort_index().tail(30).tolist()]
                      if _ser is not None else [])
            _ytd = _r["ytd_%"]
            _rel = (float(_ytd) - float(_gspc_ytd)
                    if (_gspc_ytd is not None and not pd.isna(_ytd) and not pd.isna(_gspc_ytd)) else None)
            _rows.append({
                "tk": _s,
                "name": i18n.bench_name(_s, _r["name"]),
                "periods": {lbl: (None if pd.isna(_r[col]) else float(_r[col])) for lbl, col in _pmap.items()},
                "rel_sp": _rel,
                "spark": _spark,
            })
        _asof = db.latest_snapshot_date()
        _src = (f"来源 Yahoo Finance cron EOD · 截至 {_asof} · 仅供参考"
                if i18n.get_lang() == "zh"
                else f"Source: Yahoo Finance cron EOD · as of {_asof} · for reference")
        so.masthead(
            title=i18n.t("ai.section.benchmark"),
            chip="AI TECH",
            subtitle="基准 ETF 分档表现 · 30 日趋势 · 相对标普超额",
            asof=_asof,
            source=_src,
            prefer_cn=prefer_cn,
        )
        so.benchmark_table(_rows, source=_src)

st.divider()

# --- Movers — [10] sector_overview: domain-wide top-10 gainers / losers (行内动量条) ---
_name_map = db.ticker_to_name(prefer_cn=(i18n.get_lang() == "zh"))
_all_rets = [df for df in all_returns_by_sector.values() if df is not None and not df.empty]
if _all_rets:
    _combined = pd.concat(_all_rets)
    _combined = _combined[~_combined.index.duplicated(keep="first")]   # 跨子层去重(一票只算一次)
    _combined = _combined[pd.notna(_combined["1d_%"])]

    def _mv_rows(_df: pd.DataFrame) -> list[dict]:
        return [{"tk": fmt.fmt_ticker_bbg(_tk),
                 "name": _name_map.get(_tk, _tk),
                 "last": (0.0 if pd.isna(_row["last"]) else float(_row["last"])),
                 "d1": float(_row["1d_%"])}
                for _tk, _row in _df.iterrows()]

    _gainers = _mv_rows(_combined.sort_values("1d_%", ascending=False).head(10))
    _losers = _mv_rows(_combined.sort_values("1d_%", ascending=True).head(10))
    so.movers(gainers=_gainers, losers=_losers,
              window=("1 日" if prefer_cn else "1D"), prefer_cn=prefer_cn)

# --- Onboarding ---
with st.expander(i18n.t("hc.onboarding.title")):
    st.markdown(i18n.t("hc.onboarding.body"))
