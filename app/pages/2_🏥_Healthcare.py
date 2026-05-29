"""Healthcare domain overview — 7 sub-sectors summary."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yaml
from pathlib import Path

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme


def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
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
    )

st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")

# --- Sidebar global search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="hc_overview")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"


@st.cache_data(ttl=600)
def load_domain_cfg() -> dict:
    with DOMAIN_CFG.open() as f:
        return yaml.safe_load(f)


cfg = load_domain_cfg()
theme.page_header(cfg['name'])
st.caption(cfg.get("description", "").strip())

# --- 7 sector aggregate summary ---
theme.section_header("Sector Summary", meta="MEAN RETURNS PER SECTOR")

rows = []
all_returns_by_sector: dict[str, pd.DataFrame] = {}
for sec in cfg["sectors"]:
    uni = db.sector_tickers("healthcare", sec["id"])
    tickers = tuple(uni["ticker"].tolist())
    if not tickers:
        continue
    closes = db.get_close_series_usd(tickers)   # M1 audit: USD-converted
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
    summary = pd.DataFrame(rows).set_index("Sector")
    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    _render_pct_table(summary, pct_cols=pct_cols)

st.divider()

# --- Domain benchmark snapshot ---
theme.section_header("Domain Benchmark (XLV) & Peers")
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    sub = sub.rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    })
    _render_pct_table(sub, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])

st.divider()

# --- Per-sector top 3 movers / drags ---
theme.section_header("Per-Sector Top 3 Movers / Drags · 1D")

name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
for sec in cfg["sectors"]:
    rets = all_returns_by_sector.get(sec["id"])
    if rets is None or rets.empty:
        continue
    with st.expander(f"**{sec['name']}**  ({len(rets)} tickers)"):
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
        # n2: Bloomberg ticker style
        gainers.index = [fmt.fmt_ticker_bbg(t) for t in gainers.index]
        drags.index = [fmt.fmt_ticker_bbg(t) for t in drags.index]
        with c1:
            st.markdown("**Top 3 gainers · 1D**")
            _render_pct_table(gainers, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])
        with c2:
            st.markdown("**Top 3 drags · 1D**")
            _render_pct_table(drags, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])

# --- Onboarding ---
ui.onboarding_expander("Healthcare Overview", """
**Sector Summary**: 展示了医疗健康 7 个子板块的平均涨跌幅。
- **Tickers**: 该板块包含的股票数量。
- **Benchmark**: 该板块对应的行业指数（如 XBI 对应 Biotech）。

**Domain Benchmarks**: XLV (Healthcare) 及其主要细分行业 ETF 的表现。

**Per-sector Movers**: 每个板块内当日表现最好和最差的 3 只个股。
""")
