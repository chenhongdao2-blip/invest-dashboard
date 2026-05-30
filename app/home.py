"""Home — landing page rendered by the st.navigation hub.

The hub (streamlit_app.py) handles page registration + grouping. This file
just renders the Home dashboard content. Keep its set_page_config so that
when this page is active the browser tab title / icon match.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import db
from lib import format as fmt
from lib import ui
from lib import theme
from lib import i18n

st.set_page_config(
    page_title="invest-dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Unified sidebar search ---
with st.sidebar:
    ui.sidebar_search(key_prefix="home")

# --- Language ---
i18n.init_lang()
i18n.render_lang_toggle()

# --- Header ---
theme.page_header(i18n.t("home.title"))

latest = db.latest_snapshot_date()
fetch_utc = db.last_fetch_utc()
col1, col2, col3 = st.columns([2, 2, 3])
col1.metric(i18n.t("home.metric.latest_snapshot"), latest or "—")
col2.metric(i18n.t("home.metric.last_fetch"), fetch_utc[:16] if fetch_utc else "—")
n_tickers = len(db.all_tickers())
col3.metric(i18n.t("home.metric.universe"), f"{n_tickers}")

st.divider()


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
        column_labels=column_labels,
        height=360,
        heatmap=True,
    )


# --- Benchmarks ---
theme.section_header(i18n.t("home.section.benchmarks"))
bench_df = bm.fetch_benchmarks()
if not bench_df.empty:
    show = bench_df[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]].rename(columns={
        "name": "Name", "last": "Last",
        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    })
    show["Name"] = [i18n.bench_name(s, n) for s, n in zip(show.index, show["Name"])]
    _render_pct_table(show, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"], column_labels=i18n.common_cols())
else:
    st.warning(i18n.t("common.warn.fetch_fail"))

st.divider()

# --- Top movers ---
theme.section_header(i18n.t("home.section.movers"), meta=i18n.t("home.section.movers_meta"))
gainers, losers = db.top_movers(n=10)
if gainers.empty:
    st.info(i18n.t("home.movers.empty"))
else:
    rename_map = {"name": "Name", "last": "Last",
                  "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %"}

    movers_col1, movers_col2 = st.columns(2)
    with movers_col1:
        st.markdown(f"##### {i18n.t('home.movers.gainers')}")
        g = gainers.rename(columns=rename_map)
        # n2: rewrite index to Bloomberg style
        g.index = [fmt.fmt_ticker_bbg(t) for t in g.index]
        _render_pct_table(g, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"], column_labels=i18n.common_cols())

    with movers_col2:
        st.markdown(f"##### {i18n.t('home.movers.drags')}")
        l = losers.rename(columns=rename_map)
        l.index = [fmt.fmt_ticker_bbg(t) for t in l.index]
        _render_pct_table(l, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"], column_labels=i18n.common_cols())

st.divider()

# --- Universe ---
theme.section_header(i18n.t("home.section.universe"))
uni = db.universe_summary()
if not uni.empty:
    uni = uni.copy()
    uni["domain"] = uni["domain"].map(i18n.domain_name)
    uni["sector"] = uni["sector"].map(i18n.sector_name)
    ui.render_html_table(
        uni.rename(columns={"domain": "Domain", "sector": "Sector", "n": "Tickers"}),
        text_cols=["Domain", "Sector"],
        int_cols=["Tickers"],
        column_help={},
        column_labels={
            "Domain": i18n.t("home.col.domain"),
            "Sector": i18n.t("home.col.sector"),
            "Tickers": i18n.t("home.col.tickers"),
        },
        hide_index=True,
        height=460,
    )
else:
    st.warning("universe_member empty — run `jobs/load_universe.py`")

# --- Footer ---
st.divider()
st.caption(i18n.t("home.caveat.data"))
