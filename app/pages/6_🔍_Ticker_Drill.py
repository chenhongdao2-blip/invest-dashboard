"""D6 Ticker Drill — single-ticker deep dive page.

Sources (in order of trust):
1. LLM Wiki (~/Documents/LLM Wiki/Wiki/companies/) — if a page exists for the
   ticker, render Summary / Thesis / Rating / TP / Catalysts / Risks / sections.
2. SQLite snapshots.db — price history (USD-converted), latest multiples,
   cross-sector membership, return windows.
3. yfinance.info live — fill in fundamentals fields not in SQLite (EBITDA / cash /
   debt / sales 24A/25E etc) with 1h cache.

Resolved ticker priority:
1. ?ticker URL query param (e.g. ?ticker=LLY) — supports deep-linking.
2. Page-local selectbox.
3. st.session_state.global_ticker from sidebar_search.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import db
from lib import format as fmt
from lib import strategy as strat
from lib import ui
from lib import wiki
from lib import theme

st.set_page_config(
    page_title="Ticker Drill · invest-dashboard",
    page_icon="🔍",
    layout="wide",
)

# ---------- Sidebar ----------
with st.sidebar:
    ui.sidebar_search(key_prefix="drill")

# ---------- Ticker resolution ----------
all_tickers = sorted(db.all_tickers())

# Initialize session_state.global_ticker first so the selectbox below can read it.
if "global_ticker" not in st.session_state:
    st.session_state.global_ticker = ""

# URL query param overrides everything (deep-link support).
q_params = st.query_params
url_ticker = q_params.get("ticker", "")
if isinstance(url_ticker, list):
    url_ticker = url_ticker[0] if url_ticker else ""
if url_ticker and url_ticker in all_tickers and st.session_state.global_ticker != url_ticker:
    st.session_state.global_ticker = url_ticker

theme.page_header("02 / 07", "Ticker Drill")
st.caption("Single-ticker deep dive — wiki memo (if any) + price chart + multiples + cross-sector tags.")

# Local selectbox (fallback when sidebar empty).
default_idx = 0
if st.session_state.global_ticker in all_tickers:
    default_idx = all_tickers.index(st.session_state.global_ticker) + 1

pick = st.selectbox(
    "Choose ticker",
    options=[""] + all_tickers,
    index=default_idx,
    format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    key="drill_local_pick",
)
if pick:
    st.session_state.global_ticker = pick

ticker = st.session_state.global_ticker
if not ticker:
    st.info("Pick a ticker from the sidebar or the selectbox above.")
    st.stop()

# ---------- Header card ----------
name_map = db.ticker_to_name(prefer_cn=True)
display_name = name_map.get(ticker, ticker)
bbg = fmt.fmt_ticker_bbg(ticker)

mults_df = db.latest_multiples((ticker,))
mults_row = mults_df.iloc[0] if not mults_df.empty else None

# Sector membership (multi-row in universe_member).
sec_df = db.query(
    "SELECT DISTINCT sector FROM universe_member WHERE ticker = ? ORDER BY sector",
    (ticker,),
)
sectors = sec_df["sector"].tolist() if not sec_df.empty else []
is_in_coverage = "_coverage" in sectors

# Strategy pick badge.
@st.cache_data(ttl=600)
def _pick_membership(_t: str) -> list[str]:
    """Return list of strategy names this ticker is in (e.g. ['v5 biotech', 'HK 高股息'])."""
    found: list[str] = []
    for sid, cfg in strat.STRATEGIES.items():
        try:
            df = cfg["loader"]()
        except Exception:
            continue
        if df is None or df.empty:
            continue
        cols_to_check = [c for c in ("yf_sym", "ticker") if c in df.columns]
        for col in cols_to_check:
            if _t in df[col].astype(str).values:
                # Strip leading emoji from cfg name for compact badge.
                name = cfg.get("name", sid).lstrip("🧬💰🤖⚕️🏥🩺🧪 ").strip()
                found.append(name)
                break
    return found


pick_strategies = _pick_membership(ticker)

# Compose header bar.
c_name, c_price, c_mcap, c_pe = st.columns([3, 2, 2, 2])
with c_name:
    st.markdown(f"### {display_name}")
    badges: list[str] = [f"`{bbg}`"]
    if is_in_coverage:
        badges.append("CMSI Coverage")
    if pick_strategies:
        badges.append(f"Pick: {' · '.join(pick_strategies)}")
    st.markdown(" · ".join(badges))

if mults_row is not None:
    last_px = mults_row.get("last_price")
    last_px_usd = mults_row.get("last_price_usd")
    mcap = mults_row.get("market_cap_usd")
    fwd_pe = mults_row.get("forward_pe")
    trail_pe = mults_row.get("trailing_pe")
    tp = mults_row.get("target_price_mean")

    with c_price:
        if pd.notna(last_px):
            label = "Last (local)"
            sub = f"USD {last_px_usd:,.2f}" if pd.notna(last_px_usd) else None
            st.metric(label, f"{last_px:,.2f}", delta=None, help=sub)
        else:
            st.metric("Last", "—")
    with c_mcap:
        if pd.notna(mcap):
            st.metric("Market cap", fmt.fmt_money_b(mcap))
        else:
            st.metric("Market cap", "—")
    with c_pe:
        if pd.notna(fwd_pe):
            st.metric("Fwd P/E", fmt.fmt_ratio(fwd_pe),
                      help=f"Trailing P/E: {fmt.fmt_ratio(trail_pe)}")
        else:
            st.metric("Fwd P/E", fmt.fmt_ratio(trail_pe))

    # TP upside callout.
    if pd.notna(tp) and pd.notna(last_px) and last_px > 0:
        upside_pct = (tp - last_px) / last_px * 100
        n_analysts = mults_row.get("n_analysts")
        analysts_str = f" · {int(n_analysts)} analysts" if pd.notna(n_analysts) else ""
        st.caption(
            f"Consensus TP: **{tp:,.2f}** ({upside_pct:+.1f}% vs last){analysts_str}"
        )
else:
    st.caption("No multiples snapshot — ticker may be picks-only (not in main fetch universe).")

st.divider()

# ---------- LLM Wiki memo ----------
wiki_page = wiki.find_wiki(ticker)
if wiki_page is None:
    st.caption(
        "No LLM Wiki memo for this ticker. "
        f"Drop a `companies/*.md` file in `~/Documents/LLM Wiki/Wiki/` to surface a thesis here."
    )
else:
    # Compliance gate — different banner for internal vs sanitized public view.
    if wiki_page.is_sanitized:
        st.info(
            "**公开版 memo** — Rating / TP / 研报源文件引用 / 分析师姓名已剥离。"
            "公开数据 + thesis 框架 only。完整内部版本需在本地 "
            "`~/Documents/LLM Wiki/Wiki/` 下访问。"
            "本材料不构成任何证券的投资建议或邀请。",
            icon="📋",
        )
    else:
        st.warning(
            "**本材料仅供内部参考，不构成任何证券的投资建议或邀请。** "
            "分析师个人观点不代表 CMS HK / 招商证券国际公司立场。"
            "Rating / TP 引用自 CMS HK 官方研报，请勿对外分发。"
            "Source-of-truth 仍是 Bloomberg / Wind / 官方研报 PDF。",
            icon="⚠️",
        )
    st.markdown(f"### Research memo · {wiki_page.title}")
    meta_bits: list[str] = []
    if wiki_page.rating:
        meta_bits.append(f"**Rating**: {wiki_page.rating}")
    if wiki_page.tp:
        meta_bits.append(f"**TP**: {wiki_page.tp}")
    if wiki_page.last_updated:
        meta_bits.append(f"**Updated**: {wiki_page.last_updated}")
    if wiki_page.sectors:
        meta_bits.append("**Wiki sectors**: " + ", ".join(f"`{s}`" for s in wiki_page.sectors))
    if meta_bits:
        st.markdown(" · ".join(meta_bits))

    if wiki_page.summary:
        st.markdown(f"**Summary**: {wiki_page.summary}")
    if wiki_page.thesis:
        st.markdown(f"**Thesis**: {wiki_page.thesis}")
    if wiki_page.sources:
        st.caption(f"Sources: {wiki_page.sources}")

    # Pull the high-value sections to the top, leave the rest in expanders.
    priority_keys = ["核心投资逻辑", "催化剂", "风险点", "财务快照"]
    rendered: set[str] = set()
    for key in priority_keys:
        body = wiki_page.sections.get(key)
        if body:
            with st.expander(f"{key}", expanded=(key in ("催化剂", "风险点"))):
                st.markdown(body)
            rendered.add(key)
    for key, body in wiki_page.sections.items():
        if key in rendered or not body:
            continue
        with st.expander(f"{key}", expanded=False):
            st.markdown(body)

    st.caption(f"Source file: `{wiki_page.file_path}`")
    st.divider()

# ---------- Price chart ----------
theme.section_header("Price · USD-normalized")
closes = db.get_close_series_usd((ticker,))
if closes.empty:
    st.warning("No price history in snapshots.db — backfill needed for this ticker.")
else:
    ser = closes[ticker].dropna()
    if ser.empty:
        st.warning("Price series all-NaN.")
    else:
        from lib import charts
        ydf = ser.to_frame(name=display_name)
        fig = charts.price_line_chart(
            ydf,
            title=f"{bbg} · USD close (snapshots.db, {len(ser)} obs)",
            ylabel="USD close",
        )
        st.plotly_chart(fig, width="stretch", theme=None)

# ---------- Return windows + multiples panel ----------
rets = db.compute_returns(closes)
col_perf, col_mult = st.columns(2)
with col_perf:
    st.markdown("##### Return windows")
    if rets.empty or ticker not in rets.index:
        st.caption("No return data.")
    else:
        r = rets.loc[ticker]
        perf_df = pd.DataFrame({
            "Window": ["1D", "5D", "1M", "3M", "6M", "YTD"],
            "Return %": [
                r.get("1d_%"), r.get("5d_%"), r.get("1m_%"),
                r.get("3m_%"), r.get("6m_%"), r.get("ytd_%"),
            ],
        })
        ui.render_styled_table(
            perf_df.set_index("Window"),
            pct_cols=["Return %"],
            height=260,
        )

with col_mult:
    st.markdown("##### Latest multiples (yfinance)")
    if mults_row is None:
        st.caption("No multiples snapshot.")
    else:
        mult_rows = []
        for label, key, kind in [
            ("Trailing P/E", "trailing_pe", "x"),
            ("Forward P/E", "forward_pe", "x"),
            ("EV/EBITDA", "ev_ebitda", "x"),
            ("EV/Sales", "ev_sales", "x"),
            ("P/B", "pb", "x"),
            ("FCF Yield", "fcf_yield", "pct_dec"),
        ]:
            v = mults_row.get(key)
            if pd.isna(v):
                disp = "—"
            elif kind == "x":
                disp = fmt.fmt_ratio(v)
            else:
                disp = fmt.fmt_pct_decimal(v)
            mult_rows.append({"Metric": label, "Value": disp})
        # st.table renders a static, non-sortable grid — correct for vertical
        # properties lists where Value column is mixed-type ($/%/x).
        st.table(pd.DataFrame(mult_rows).set_index("Metric"))

st.divider()

# ---------- Extended fundamentals (live yfinance.info, cached 1h) ----------
# Gated behind an explicit button so that Streamlit Cloud cold-start visits
# don't pay a 30s+ yfinance.info round-trip on every page load. The button
# triggers a single cached fetch — subsequent reruns hit the cache.
@st.cache_data(ttl=3600, show_spinner="Fetching live fundamentals…")
def _yf_info(_t: str) -> dict:
    try:
        info = yf.Ticker(_t).info or {}
    except Exception:
        return {}
    return info or {}


with st.expander("Extended fundamentals (live yfinance.info — click to fetch)", expanded=False):
    btn_key = f"fetch_yf_info_{ticker}"
    fetched_key = f"fetched_yf_info_{ticker}"

    cols = st.columns([1, 3])
    if cols[0].button("Fetch live", key=btn_key, help="Calls yfinance.info; result cached 1 hour."):
        st.session_state[fetched_key] = True

    if not st.session_state.get(fetched_key):
        st.caption(
            "Click *Fetch live* to pull EBITDA / margins / shares / business summary "
            "from yfinance.info. Avoided by default to keep the page snappy on "
            "Streamlit Cloud (cold-start visits skip the live call)."
        )
    else:
        info = _yf_info(ticker)
        if not info:
            st.caption("yfinance.info returned empty — network issue, rate limit, or ticker delisted.")
        else:
            rows: list[dict[str, object]] = []

            def _push(label: str, val, kind: str = "money") -> None:
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    disp = "—"
                elif kind == "money":
                    disp = fmt.fmt_money_b(val)
                elif kind == "pct":
                    disp = f"{val * 100:+.2f}%" if abs(val) < 5 else f"{val:+.2f}%"
                elif kind == "x":
                    disp = fmt.fmt_ratio(val)
                elif kind == "int":
                    disp = f"{int(val):,}" if val else "—"
                else:
                    disp = str(val)
                rows.append({"Metric": label, "Value": disp})

            _push("EBITDA (TTM)", info.get("ebitda"))
            _push("Total cash", info.get("totalCash"))
            _push("Total debt", info.get("totalDebt"))
            _push("Total revenue (TTM)", info.get("totalRevenue"))
            _push("Revenue growth (YoY)", info.get("revenueGrowth"), "pct")
            _push("Gross margin", info.get("grossMargins"), "pct")
            _push("Operating margin", info.get("operatingMargins"), "pct")
            _push("Profit margin", info.get("profitMargins"), "pct")
            _push("Return on equity", info.get("returnOnEquity"), "pct")
            _push("PEG ratio", info.get("trailingPegRatio"), "x")
            _push("Dividend yield", info.get("dividendYield"), "pct")
            _push("Beta", info.get("beta"), "x")
            _push("Shares outstanding", info.get("sharesOutstanding"), "int")
            _push("Float shares", info.get("floatShares"), "int")

            # st.table — static, no sort header (Value column is mixed-type).
            st.table(pd.DataFrame(rows).set_index("Metric"))

            if info.get("longBusinessSummary"):
                st.markdown("##### Business summary")
                st.markdown(info["longBusinessSummary"])

# ---------- Cross-sector tags ----------
st.markdown("##### Universe membership")
if sectors:
    icons = {
        "biotech": "BIO", "pharma": "PHAR", "hc_ai": "AI",
        "medtech": "MED", "hospital_care": "HOSP",
        "managed_care": "MC", "cxo": "CXO", "_coverage": "COV",
    }
    tags = " · ".join(f"{icons.get(s, s)} `{s}`" for s in sectors)
    st.markdown(tags)
else:
    st.caption("Ticker is not in any configured sector universe.")

# ---------- Footer caveats ----------
ui.onboarding_expander("Ticker Drill", """
**Memo source**: 如果 `~/Documents/LLM Wiki/Wiki/companies/<ticker>-*.md` 文件存在，
本页顶部会渲染 wiki memo 的 Summary / Thesis / Rating / TP / 核心投资逻辑 / 催化剂 /
风险点 / 财务快照。Memo 写入在 wiki 端，本页只读，不会回写。

**Price**: USD-converted close from `snapshots.db` (cron 每日累积；data 始于
~ 2025-12-01)。

**Multiples**: yfinance trailing + 12M forward only。Multi-year forward
(25E / 26E / 27E) 不在 dashboard 范围。

**Extended fundamentals**: 来自 yfinance.info 的 live fetch，1 小时 cache。
NaN 或 "—" 表示 yfinance 未提供该字段（小盘 / 港股常见）。

**Deep-link**: 可通过 `?ticker=LLY` URL 参数直接跳到该票。
""")
st.caption(
    "Wiki memo 反映 CMS HK 内部观点 + George 自己的迭代，**不是中立分析**。"
    " 评级 / TP 引用必带 wiki Last updated 时间戳，>30 天请回到原研报核对。"
)
