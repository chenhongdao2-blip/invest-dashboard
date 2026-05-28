"""Shared Streamlit UI components."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db
from lib import format as fmt

# Shared column tooltips — single source of truth for cross-page consistency.
# Reference these via render_styled_table(column_help=COLUMN_HELP) or splice
# into manual column_config dicts.
COLUMN_HELP = {
    "Fwd P/E": (
        "yfinance.info.forwardPE — Next-12-Month rolling consensus forward EPS "
        "(LSEG / Refinitiv source). 与 Yahoo Finance 网页 \"預測市盈率\" "
        "(下一财年 fiscal-year EPS 口径) 数字可能差 5-10%。"
        "Cross-check 请用 Bloomberg / FactSet / 卖方研报。"
    ),
    "Trail P/E": (
        "yfinance.info.trailingPE — Trailing 12-Month GAAP EPS。"
        "Biotech 烧钱期标的可能 NULL / 负值。"
    ),
    "EV/EBITDA": (
        "yfinance.info.enterpriseToEbitda — TTM EBITDA basis。"
        "Biotech / SaaS 早期标的若 EBITDA 为负，倍数无意义。"
    ),
    "EV/Sales": (
        "yfinance.info.enterpriseToRevenue — TTM Revenue basis。"
        "高增长 biotech / hc_ai 看此指标比 P/E 更有意义。"
    ),
    "FCF Yld": (
        "Free Cash Flow Yield = FCF / Market Cap (TTM)。"
        "yfinance.info.freeCashflow / marketCap。"
        "用 USD-converted market cap 计算。"
    ),
    "P/B": (
        "yfinance.info.priceToBook — Latest reported book value basis。"
        "金融 / asset-light 公司参考价值有限。"
    ),
    "TP Upside %": (
        "(targetMeanPrice - currentPrice) / currentPrice × 100%。"
        "yfinance.info.targetMeanPrice — consensus 12M target price mean across "
        "covering analysts。Yahoo aggregator，与 Bloomberg/Wind broker basket 不同。"
    ),
    "Reco": (
        "yfinance.info.recommendationMean: 1=Strong Buy, 2=Buy, 3=Hold, 4=Sell, 5=Strong Sell。"
        "标签按 1.5/2.5/3.5/4.5 阈值切档。"
    ),
    "N analysts": (
        "yfinance.info.numberOfAnalystOpinions — 当前覆盖该标的的卖方分析师数。"
        "<5 时 consensus 不稳健。"
    ),
    "vs HSI YTD": (
        "YTD return - HSI YTD return (pp)。港股 sell-side 早会必看指标。"
    ),
    "Mcap USD ($B)": (
        "Market cap converted to USD via daily FX (yfinance Currency. 港股 HKD/USD, "
        "JP JPY/USD, KR KRW/USD, CN CNY/USD)。"
    ),
}


def sidebar_search(key_prefix: str = ""):
    """Unified sidebar ticker search with session state persistence."""
    st.subheader("🔍 Find ticker")

    if "global_ticker" not in st.session_state:
        st.session_state.global_ticker = ""

    all_t = sorted(db.all_tickers())

    current_index = 0
    if st.session_state.global_ticker in all_t:
        current_index = all_t.index(st.session_state.global_ticker) + 1

    pick = st.selectbox(
        "Jump to ticker drill",
        options=[""] + all_t,
        index=current_index,
        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
        key=f"{key_prefix}_search_box",
    )

    if pick != st.session_state.global_ticker:
        st.session_state.global_ticker = pick

    if st.session_state.global_ticker:
        st.info(
            f"📍 **{fmt.fmt_ticker_bbg(st.session_state.global_ticker)}** "
            "— open *Ticker Drill* page for the full profile."
        )


def onboarding_expander(page_name: str, markdown_text: str):
    """Consistent onboarding expander across pages."""
    with st.expander(f"📖 How to read this {page_name}"):
        st.markdown(markdown_text)


# ---------- Sort-bug-safe table renderer (extracted from CMSI Coverage) ----------

def render_styled_table(
    df: pd.DataFrame,
    *,
    pct_cols: list[str] | None = None,
    pct_decimal_cols: list[str] | None = None,
    mult_cols: list[str] | None = None,
    money_b_cols: list[str] | None = None,
    int_cols: list[str] | None = None,
    text_cols: list[str] | None = None,
    column_widths: dict[str, str] | None = None,
    extra_formats: dict[str, str] | None = None,
    column_help: dict[str, str] | None = None,
    height: int = 500,
    hide_index: bool = False,
) -> None:
    """Render a numeric DataFrame with column_config (sort-safe) + Styler color.

    SOLVES the well-known Streamlit sort bug: passing pre-formatted strings to
    st.dataframe makes header-click sort lexicographic ('100%' < '20%'). Instead
    we keep numeric values and rely on column_config to format on display, while
    still applying Styler.background_gradient on the underlying numeric series.

    Parameters
    ----------
    df : pd.DataFrame
        Numeric DataFrame. Pre-formatted strings will sort as strings — don't.
    pct_cols : columns rendered as `%+.1f%%` with diverging red/green gradient.
    pct_decimal_cols : columns already in decimal (0.025 → +2.5%), high=green.
    mult_cols : columns rendered as `%.1fx` with low-good gradient (cheap=green).
    money_b_cols : columns rendered as `$%.1fB` (no gradient).
    int_cols : columns rendered as `%d`.
    text_cols : columns left as text (no format).
    column_widths : optional per-column width override ("small", "medium", "large").
    extra_formats : optional per-column custom NumberColumn format string.
    height : grid height in pixels.
    hide_index : pass-through to st.dataframe.
    """
    pct_cols = pct_cols or []
    pct_decimal_cols = pct_decimal_cols or []
    mult_cols = mult_cols or []
    money_b_cols = money_b_cols or []
    int_cols = int_cols or []
    text_cols = text_cols or []
    column_widths = column_widths or {}
    extra_formats = extra_formats or {}
    # Default tooltips: caller can pass column_help={} to disable, or splice
    # a custom dict. None → fall back to shared COLUMN_HELP.
    if column_help is None:
        column_help = COLUMN_HELP

    # pct_decimal_cols hold values in [-1, 1] decimal form (e.g. 0.025 → 2.5%).
    # Streamlit NumberColumn `format` does NOT implement the printf `%%`-as-
    # multiplier shorthand, so we pre-multiply the column by 100 on a *local
    # copy* of the DataFrame and display with a plain "%+.2f%%" format. The
    # original frame is untouched.
    if pct_decimal_cols:
        df = df.copy()
        for col in pct_decimal_cols:
            if col in df.columns:
                df[col] = df[col] * 100

    # Build Styler from the numeric DataFrame.
    styler = df.style
    for col in pct_cols:
        if col in df.columns:
            styler = styler.apply(
                lambda s, _c=col: fmt.background_gradient_diverging(df[_c]),
                subset=[col],
            )
    for col in pct_decimal_cols:
        if col in df.columns:
            styler = styler.apply(
                lambda s, _c=col: fmt.background_gradient_low_good(
                    df[_c], low_color="#dc2626", high_color="#16a34a"
                ),
                subset=[col],
            )
    for col in mult_cols:
        if col in df.columns:
            styler = styler.apply(
                lambda s, _c=col: fmt.background_gradient_low_good(df[_c]),
                subset=[col],
            )

    def _num(col: str, fmt_str: str):
        return st.column_config.NumberColumn(
            format=fmt_str,
            width=column_widths.get(col, "small"),
            help=column_help.get(col),
        )

    def _text(col: str):
        return st.column_config.TextColumn(
            width=column_widths.get(col, "small"),
            help=column_help.get(col),
        )

    # Build column_config for display format (keeps sort numeric).
    col_cfg: dict = {}
    for col in pct_cols:
        if col in df.columns:
            col_cfg[col] = _num(col, "%+.1f%%")
    for col in pct_decimal_cols:
        if col in df.columns:
            # df[col] was already multiplied by 100 above, so "%+.2f%%" prints
            # e.g. 0.025 (pre-mul: 2.5) → "+2.50%".
            col_cfg[col] = _num(col, "%+.2f%%")
    for col in mult_cols:
        if col in df.columns:
            col_cfg[col] = _num(col, "%.1fx")
    for col in money_b_cols:
        if col in df.columns:
            col_cfg[col] = _num(col, "$%.1fB")
    for col in int_cols:
        if col in df.columns:
            col_cfg[col] = _num(col, "%d")
    for col in text_cols:
        if col in df.columns:
            col_cfg[col] = _text(col)
    for col, fmt_str in extra_formats.items():
        if col in df.columns:
            col_cfg[col] = _num(col, fmt_str)

    st.dataframe(
        styler,
        use_container_width=True,
        height=height,
        column_config=col_cfg,
        hide_index=hide_index,
    )
