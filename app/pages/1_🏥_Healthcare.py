"""Healthcare domain overview — 7 sub-sectors summary."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yaml
from pathlib import Path

from lib import benchmarks as bm
from lib import db
from lib import format as fmt

st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"


@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)


cfg = load_domain_cfg()
st.title(f"{cfg.get('emoji', '🏥')} {cfg['name']}")
st.caption(cfg.get("description", "").strip())

# --- 7 sector aggregate summary ---
st.subheader("📊 Sector summary (mean returns per sector)")

rows = []
all_returns_by_sector: dict[str, pd.DataFrame] = {}
for sec in cfg["sectors"]:
    uni = db.sector_tickers("healthcare", sec["id"])
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        continue
    closes = db.get_close_series(tickers)
    rets = db.compute_returns(closes)
    if rets.empty:
        continue
    all_returns_by_sector[sec["id"]] = rets
    rows.append({
        "Sector": sec["name"],
        "Tickers": len(tickers),
        "1D % avg": rets["1d_%"].mean(),
        "5D % avg": rets["5d_%"].mean(),
        "1M % avg": rets["1m_%"].mean(),
        "YTD % avg": rets["ytd_%"].mean(),
        "Benchmark": sec.get("benchmark", "—"),
    })

if not rows:
    st.warning("No sector data — backfill needed.")
else:
    summary = pd.DataFrame(rows)
    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    styler = (
        summary.style
        .format({c: fmt.fmt_pct for c in pct_cols}, na_rep="—")
        .apply(fmt.style_pct_column, subset=pct_cols)
    )
    st.dataframe(styler, use_container_width=True, hide_index=True)

st.divider()

# --- Domain benchmark snapshot ---
st.subheader("📐 Domain benchmark (XLV) & peers")
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    sub = sub.rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    })
    styler = (
        sub.style
        .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
                 "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
                na_rep="—")
        .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    )
    st.dataframe(styler, use_container_width=True)

st.divider()

# --- Per-sector top 3 movers / drags ---
st.subheader("🎯 Per-sector top 3 movers / drags (1D)")

name_map = db.ticker_to_name()
for sec in cfg["sectors"]:
    rets = all_returns_by_sector.get(sec["id"])
    if rets is None or rets.empty:
        continue
    with st.expander(f"**{sec['name']}**  ({len(rets)} tickers)"):
        rets = rets.copy()
        rets["name"] = rets.index.map(name_map)
        rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
        rets.index.name = "Ticker"

        c1, c2 = st.columns(2)
        gainers = rets.sort_values("1d_%", ascending=False).head(3)
        drags = rets.sort_values("1d_%", ascending=True).head(3)
        with c1:
            st.markdown("🟢 Top 3 gainers (1D)")
            styler = (
                gainers.rename(columns={"name": "Name", "last": "Last",
                                        "1d_%": "1D %", "5d_%": "5D %",
                                        "1m_%": "1M %", "ytd_%": "YTD %"}).style
                .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
                         "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
                        na_rep="—")
                .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
            )
            st.dataframe(styler, use_container_width=True)
        with c2:
            st.markdown("🔴 Top 3 drags (1D)")
            styler = (
                drags.rename(columns={"name": "Name", "last": "Last",
                                      "1d_%": "1D %", "5d_%": "5D %",
                                      "1m_%": "1M %", "ytd_%": "YTD %"}).style
                .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
                         "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
                        na_rep="—")
                .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
            )
            st.dataframe(styler, use_container_width=True)
