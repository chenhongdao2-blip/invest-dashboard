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

# --- Domain benchmark snapshot (AI: ^SOX primary + peers) ---
theme.section_header(i18n.t("ai.section.benchmark"))
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["^SOX", "SMH", "AIQ", "512480.SS", "515880.SS", "442580.KS"]
    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    if not sub.empty:
        sub = sub.rename(columns={
            "name": "Name", "last": "Last",
            "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "3m_%": "3M %", "ytd_%": "YTD %",
        })
        sub["Name"] = [i18n.bench_name(s, n) for s, n in zip(sub.index, sub["Name"])]
        _render_pct_table(
            sub,
            pct_cols=["1D %", "5D %", "1M %", "3M %", "YTD %"],
            num_cols=["Last"],
            column_labels=i18n.common_cols(),
        )

st.divider()

# --- Per-sector top 3 movers / drags ---
theme.section_header(i18n.t("hc.section.movers"))

name_map = db.ticker_to_name(prefer_cn=True)
for sec in cfg["sectors"]:
    rets = all_returns_by_sector.get(sec["id"])
    if rets is None or rets.empty:
        continue
    with st.expander(f"**{i18n.sector_name(sec['id'])}**  ({len(rets)} tickers)"):
        rets = rets.copy()
        rets["name"] = rets.index.map(name_map)
        rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
        rets.index.name = "Ticker"

        rename_map = {"name": "Name", "last": "Last",
                      "1d_%": "1D %", "5d_%": "5D %",
                      "1m_%": "1M %", "ytd_%": "YTD %"}
        c1, c2 = st.columns(2)
        gainers = rets.sort_values("1d_%", ascending=False).head(3).rename(columns=rename_map)
        drags = rets.sort_values("1d_%", ascending=True).head(3).rename(columns=rename_map)
        gainers.index = [fmt.fmt_ticker_bbg(t) for t in gainers.index]
        drags.index = [fmt.fmt_ticker_bbg(t) for t in drags.index]
        with c1:
            st.markdown(f"**{i18n.t('hc.movers.gainers')}**")
            _render_pct_table(
                gainers,
                pct_cols=["1D %", "5D %", "1M %", "YTD %"],
                num_cols=["Last"],
                column_labels=i18n.common_cols(),
            )
        with c2:
            st.markdown(f"**{i18n.t('hc.movers.drags')}**")
            _render_pct_table(
                drags,
                pct_cols=["1D %", "5D %", "1M %", "YTD %"],
                num_cols=["Last"],
                column_labels=i18n.common_cols(),
            )

# --- Onboarding ---
with st.expander(i18n.t("hc.onboarding.title")):
    st.markdown(i18n.t("hc.onboarding.body"))
