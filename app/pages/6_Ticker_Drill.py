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

import hashlib
import re
from html import escape as _esc

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import db
from lib import format as fmt
from lib import strategy as strat
from lib import ui
from lib import wiki
from lib import theme
from lib import i18n


def _reco_label(mean) -> str:
    """Map yfinance recommendation_mean (1=Strong Buy … 5=Strong Sell) to a
    localized consensus label. Thresholds 1.5/2.5/3.5/4.5 per ui.COLUMN_HELP.

    Source is a LOW-reliability third-party aggregate (Yahoo) — the caller MUST
    relabel it "市场一致预期 · 仅供参考" and carry a disclaimer (GLM /cccg compliance)."""
    if mean is None or pd.isna(mean):
        return "—"
    if mean <= 1.5:
        key = "drill.reco.strong_buy"
    elif mean <= 2.5:
        key = "drill.reco.buy"
    elif mean <= 3.5:
        key = "drill.reco.hold"
    elif mean <= 4.5:
        key = "drill.reco.sell"
    else:
        key = "drill.reco.strong_sell"
    return f"{i18n.t(key)} ({mean:.1f})"


# Sector → most-specific sector-benchmark ETF. No CXO / HC-AI ETF exists in
# benchmarks_daily → those route to the broad XLV anchor only.
_SECTOR_BENCH = {
    "biotech": "XBI",                  # user: biotech 用 XBI
    "pharma": "^SP500-352020",         # user: MNC big pharma 用 标普500医药 (vs XPH equal-weight)
    "medtech": "IHI",
    "hospital_care": "XHS",            # 医院/设施运营商 — SPDR 医疗服务 (vs IHF 险企权重高)
    "managed_care": "IHF",             # 险企/管理式医疗 — IHF 前十大即 UNH/ELV/HUM
}
# Priority when a ticker spans multiple sectors (e.g. ISRG = hc_ai + medtech):
# prefer the most specific ETF (medtech→IHI) over the broad fallback.
_SECTOR_BENCH_PRIORITY = ["biotech", "pharma", "medtech", "hospital_care", "managed_care"]
_BROAD_BENCH = "XLV"

# Per-ticker benchmark overrides — names whose sector tag mis-routes the RS chart
# (the comparison peer ≠ the sector default). Curated on user review; keeps the
# universe taxonomy untouched (a name can stay sector=hc_ai for screening yet
# benchmark vs broad healthcare here).
_BENCH_OVERRIDE: dict[str, list[str]] = {
    "OMCL": ["IHI", _BROAD_BENCH],            # Omnicell = 药房自动化设备 (medtech), not SaaS
    "HQY":  [_BROAD_BENCH],                    # HealthEquity = HSA 医疗金融, not software
    "HIMS": [_BROAD_BENCH],                    # Hims & Hers = DTC 远程医疗/消费医疗, not software
    "RPRX": ["^SP500-352020", _BROAD_BENCH],   # Royalty Pharma = 药品特许权金融 (pharma), not biotech
}


def _local_ccy(ticker: str) -> str:
    """Listing-currency code from the ticker suffix (for chart/axis labels)."""
    if ticker.endswith(".HK"):
        return "HKD"
    if ticker.endswith((".SS", ".SZ")):
        return "CNY"
    if ticker.endswith(".T"):
        return "JPY"
    if ticker.endswith((".KS", ".KQ")):   # KOSPI / KOSDAQ
        return "KRW"
    return "USD"


def _fmt_turnover(v, ccy: str) -> str:
    """Compact local-currency turnover, e.g. '1.2B' / '340M' (no $ — ccy goes in
    the card foot)."""
    if v is None or pd.isna(v):
        return "—"
    if v >= 1e9:
        return f"{v / 1e9:.1f}B"
    if v >= 1e6:
        return f"{v / 1e6:.0f}M"
    return f"{v:,.0f}"


def _route_benchmarks(ticker: str, sectors: list[str]) -> list[str]:
    """Benchmark symbols for the relative-strength chart, routed by LISTING REGION
    so each stock is compared inside its OWN market & currency. Per the user +
    GLM /cccg: HK / China names must NOT benchmark against US biotech ETFs.
      HK   → 恒生医疗保健 HSHCI + 恒生指数 ^HSI   (HKD)
      A股  → 中证医疗 512170                       (CNY)
      US   → most-specific US sector ETF + XLV     (USD)
    Other foreign listings (JP .T / KR .KS …) have no healthcare benchmark on file
    → [] (caller falls back to the absolute local-currency price line).

    AI-domain names (sector ids start with 'ai_') route to AI/semi benchmarks, NOT
    healthcare — same-currency by listing region. All targets are in benchmarks_daily."""
    if any(s.startswith("ai_") for s in sectors):
        if ticker.endswith(".HK"):
            return ["3191.HK", "^HSI"]
        if ticker.endswith((".SS", ".SZ")):
            return ["512480.SS", "159819.SZ"]    # 中证半导体 + 人工智能ETF (CNY)
        if ticker.endswith(".T"):
            return ["2644.T"]                     # Global X Japan Semiconductor (JPY)
        if ticker.endswith((".KS", ".KQ")):
            return ["091160.KS"]                  # KODEX Korea Semiconductor (KRW)
        return ["^SOX", "SMH"]                     # US-listed AI/semi (USD)
    if ticker.endswith(".HK"):
        return ["HSHCI.HK", "^HSI"]
    if ticker.endswith((".SS", ".SZ")):
        return ["512170.SS"]
    if "." in ticker:          # other foreign listing — no benchmark on file
        return []
    if ticker in _BENCH_OVERRIDE:   # curated per-ticker exceptions (see dict above)
        return _BENCH_OVERRIDE[ticker]
    # US-listed: most-specific HARD sector ETF (priority for multi-sector) + broad XLV.
    for s in _SECTOR_BENCH_PRIORITY:
        if s in sectors:
            return [_SECTOR_BENCH[s], _BROAD_BENCH]
    # No hard-sector ETF. CXO / life-sciences-tools (IQVIA, Thermo, Danaher…) →
    # broad healthcare XLV; cxo wins over hc_ai for dual-tagged names (e.g. IQV). (user)
    if "cxo" in sectors:
        return [_BROAD_BENCH]
    # Pure health-tech / SaaS (Veeva, Doximity, Tempus…) trade like software, NOT
    # pharma → benchmark vs software/SaaS (IGV) + Nasdaq 100 tech 大盘, not XLV. (user)
    if "hc_ai" in sectors:
        return ["IGV", "^NDX"]
    # Unclassified → broad healthcare.
    return [_BROAD_BENCH]


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

i18n.init_lang()
i18n.render_lang_toggle()

prefer_cn = i18n.get_lang() == "zh"

# ── 合并页：列表模式(没选股 = 全市场行情表) / 详情模式(选了股 = 个股下钻) ──
# mode 由当前 global_ticker 决定 (下方选股框/返回键改它 → Streamlit rerun)。
_in_detail = bool(
    st.session_state.global_ticker and st.session_state.global_ticker in all_tickers
)


def _back_to_list() -> None:
    """返回列表：清选中票 + 选股框 + ?ticker= 深链。on_click 回调早于 widget 实例化,
    可安全改 drill_local_pick (脚本体里改已实例化 widget 的 key 会报错)。"""
    st.session_state.global_ticker = ""
    st.session_state.drill_local_pick = ""
    st.query_params.clear()


if _in_detail:
    st.button("← 返回列表" if prefer_cn else "← Back to list",
              on_click=_back_to_list, key="drill_back")
    theme.page_header(i18n.t("drill.title"))
    st.caption(i18n.t("drill.caption"))
else:
    theme.page_header("行情 / 个股" if prefer_cn else "Market & Stocks")
    st.caption(
        "用下方选股框选一只看完整详情，或浏览/筛选全市场行情表（按领域/地区/行业）。"
        if prefer_cn else
        "Pick a ticker below for its full drill-down, or browse/filter the full quote table."
    )

# Local selectbox = 选股框 (两模式都在；详情模式可借它快速换股)。
default_idx = 0
if st.session_state.global_ticker in all_tickers:
    default_idx = all_tickers.index(st.session_state.global_ticker) + 1

_drill_names = db.ticker_to_name(prefer_cn=True)  # COALESCE(name_cn, name_en, ticker)


def _drill_label(x: str) -> str:
    """Company name + Bloomberg ticker, e.g. '康臣药业 · 1681 HK' (CN preferred,
    then EN; bare ticker when no name on file)."""
    if not x:
        return i18n.t("sidebar.select_placeholder")
    bbg = fmt.fmt_ticker_bbg(x)
    nm = _drill_names.get(x)
    return f"{nm} · {bbg}" if nm and nm != x else bbg


pick = st.selectbox(
    i18n.t("drill.choose"),
    options=[""] + all_tickers,
    index=default_idx,
    format_func=_drill_label,
    key="drill_local_pick",
)
if pick:
    st.session_state.global_ticker = pick

ticker = st.session_state.global_ticker
if not ticker:
    # 列表模式：全市场行情表(FT精排, 行内「详情↗」点击开新标签) + 筛选 + 下载 + 选股框(上方)。
    from lib import quote_table
    quote_table.render_quote_list(prefer_cn=prefer_cn, key_prefix="drill_list")
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
def _pick_membership(t: str) -> list[str]:
    """Return list of strategy names this ticker is in (e.g. ['v5 biotech', 'HK 高股息']).

    NB: param must NOT start with '_' — Streamlit excludes underscore-prefixed args
    from the cache key, which would return the first ticker's result for every ticker.
    """
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
            if t in df[col].astype(str).values:
                # Strip leading emoji from cfg name for compact badge.
                name = cfg.get("name", sid).lstrip("🧬💰🤖⚕️🏥🩺🧪 ").strip()
                found.append(name)
                break
    return found


pick_strategies = _pick_membership(ticker)

# ---------- Header hero ----------
# Identity row: company name (section-header weight) + Bloomberg ticker in meta.
theme.section_header(display_name, meta=bbg)

# Listing currency (per user: individual stock shown in LOCAL currency). Prefer the
# multiples `currency` column (authoritative), fall back to the ticker suffix. Used
# by the KPI strip (price/mcap dual-ccy, YTD/turnover foots) and the RS chart.
ccy = _local_ccy(ticker)
if mults_row is not None:
    _c = mults_row.get("currency")
    if isinstance(_c, str) and _c:
        ccy = _c

# Identity chips — coverage (CMSI-red accent) + strategy picks (teal). Unified into
# the .cmsi-chip system (P2 design pass); replaces the old plain-caption badge line.
_id_chips: list[tuple[str, str]] = []
if is_in_coverage:
    _id_chips.append((i18n.t("drill.badge.coverage"), "coverage"))
_id_chips += [(nm, "strategy") for nm in pick_strategies]
if _id_chips:
    theme.chips_tagged(_id_chips)

# Consensus / multiples pulled ONCE here — reused by the KPI strip and the Variant
# block below.
upside_pct: float | None = None
n_analysts = None
reco_mean = None
tp = None
if mults_row is not None:
    last_px = mults_row.get("last_price")
    last_px_usd = mults_row.get("last_price_usd")
    mcap = mults_row.get("market_cap_usd")
    fwd_pe = mults_row.get("forward_pe")
    trail_pe = mults_row.get("trailing_pe")
    tp = mults_row.get("target_price_mean")
    n_analysts = mults_row.get("n_analysts")
    reco_mean = mults_row.get("recommendation_mean")
    if pd.notna(tp) and pd.notna(last_px) and last_px > 0:
        upside_pct = (tp - last_px) / last_px * 100

    # KPI strip — 4 editorial cards. DESIGN.md §0.4 "color is a signal not a fill":
    # only TP-upside is sign-colored; price / mcap / P-E are neutral facts (flat).
    # Price + market cap in BOTH local currency and USD (user). For US names
    # (ccy==USD) the USD foot is dropped — it would just duplicate the value.
    _is_usd = ccy == "USD"
    last_val = f"{ccy} {last_px:,.2f}" if pd.notna(last_px) else "—"
    last_foot = (f"USD {last_px_usd:,.2f}"
                 if (pd.notna(last_px_usd) and not _is_usd) else None)
    if pd.notna(mcap) and not _is_usd and pd.notna(last_px) and pd.notna(last_px_usd) and last_px_usd > 0:
        mcap_local = mcap * (last_px / last_px_usd)   # USD mcap × FX (local per USD)
        mcap_val = f"{ccy} {_fmt_turnover(mcap_local, ccy)}"
        mcap_foot = f"USD {_fmt_turnover(mcap, 'USD')}"
    elif pd.notna(mcap):
        mcap_val, mcap_foot = f"USD {_fmt_turnover(mcap, 'USD')}", None
    else:
        mcap_val, mcap_foot = "—", None

    pe_val = (fmt.fmt_ratio(fwd_pe) if pd.notna(fwd_pe) else fmt.fmt_ratio(trail_pe))
    pe_foot = (i18n.t("drill.kpi.pe_foot", pe=fmt.fmt_ratio(trail_pe))
               if pd.notna(trail_pe) else None)

    # YTD return (local ccy, signal-colored) + 20D turnover (liquidity) — these two
    # replace the old "TP Upside" card (consensus upside now lives in the discreet
    # line below + the Variant block) and add density to the header (user).
    _rets = db.compute_returns(db.get_close_series((ticker,)))
    ytd = _rets.loc[ticker, "ytd_%"] if (not _rets.empty and ticker in _rets.index) else None
    ytd_ok = ytd is not None and pd.notna(ytd)
    ytd_val = fmt.fmt_pct(ytd, 1) if ytd_ok else "—"
    ytd_dir = ("up" if ytd > 0 else "down" if ytd < 0 else "flat") if ytd_ok else "flat"
    adv_val = _fmt_turnover(db.adv_20d(ticker), ccy)

    theme.kpi_strip([
        theme.kpi_metric(i18n.t("drill.metric.last_local"), last_val, foot=last_foot),
        theme.kpi_metric(i18n.t("drill.metric.mcap"), mcap_val, foot=mcap_foot),
        theme.kpi_metric(i18n.t("drill.metric.fwd_pe"), pe_val, foot=pe_foot),
        theme.kpi_metric(i18n.t("drill.metric.ytd"), ytd_val,
                         foot=i18n.t("drill.kpi.ytd_foot", ccy=ccy), direction=ytd_dir),
        theme.kpi_metric(i18n.t("drill.metric.adv"), adv_val,
                         foot=i18n.t("drill.kpi.adv_foot", ccy=ccy)),
    ])

    # Discreet consensus-TP line (kept OUT of the colored KPI cards per user). Shown
    # only when there is no house-view Variant block below to avoid duplication.
    # Compliance (GLM /cccg): labeled third-party reference, hidden if no coverage.
    _wiki_pv = wiki.find_wiki(ticker)
    _house_pv = (_wiki_pv is not None and not _wiki_pv.is_sanitized
                 and bool(_wiki_pv.rating or _wiki_pv.tp))
    if upside_pct is not None and not _house_pv:
        st.caption(i18n.t(
            "drill.consensus_line",
            tp=f"{tp:,.2f}", upside=f"{upside_pct:+.1f}%",
            n=(f"{int(n_analysts)}" if pd.notna(n_analysts) else "—"),
        ))
else:
    st.caption(i18n.t("drill.no_mults"))

# ---------- Variant: House view vs Consensus (the alpha block) ----------
# Renders ONLY when there is an actual CMS HK house view (wiki rating/TP, non-
# sanitized) to set against the consensus — otherwise consensus already shows in
# the KPI strip and a 3-col block of consensus-only would be noise.
# Compliance (GLM /cccg G2): consensus is a LOW-reliability 3rd-party aggregate
# (Yahoo, weak for HK 18A) — explicitly relabeled "仅供参考", carries a disclaimer,
# and the whole block hides when the ticker has no analyst coverage.
_wiki_variant = wiki.find_wiki(ticker)
_has_house = (_wiki_variant is not None and not _wiki_variant.is_sanitized
              and bool(_wiki_variant.rating or _wiki_variant.tp))
_has_consensus = (mults_row is not None and pd.notna(n_analysts)
                  and n_analysts and n_analysts > 0
                  and (pd.notna(reco_mean) or pd.notna(tp)))
if _has_house and _has_consensus:
    theme.section_header(i18n.t("drill.variant.title"))
    # Side-by-side 一致预期 vs 自有观点 (theme.consensus_house) — upgrade of the prior
    # 3-KPI-card layout. Same data/gating/compliance disclaimer; richer visual diff.
    _zh = i18n.get_lang() == "zh"
    _lbl_reco = "评级" if _zh else "Rating"
    _lbl_tp = "目标价" if _zh else "Target Price"
    _lbl_n = "覆盖券商" if _zh else "Analysts"
    _lbl_up = "一致上行空间" if _zh else "Consensus Upside"
    # Consensus (left, neutral ink) — relabelled 仅供参考 via drill.variant.consensus.
    _cons_rows: list[tuple[str, str]] = [(_lbl_reco, _esc(_reco_label(reco_mean)))]
    if pd.notna(tp):
        _cons_rows.append((_lbl_tp, f"{_esc(ccy)} {tp:,.2f}"))
    if pd.notna(n_analysts):
        _cons_rows.append((_lbl_n, f"{int(n_analysts)}"))
    if upside_pct is not None:
        _up_cls = "cmsi-ch-up" if upside_pct >= 0 else "cmsi-ch-down"
        _cons_rows.append((_lbl_up, f"<span class='{_up_cls}'>{upside_pct:+.1f}%</span>"))
    # House (right, red tint) — CMS HK wiki rating/TP, with TP divergence vs consensus.
    _house_rows: list[tuple[str, str]] = []
    if _wiki_variant.rating:
        _house_rows.append((_lbl_reco, f"<b>{_esc(_wiki_variant.rating)}</b>"))
    if _wiki_variant.tp:
        _tp_html = _esc(_wiki_variant.tp)
        # Annotate "(±x% vs 一致)" ONLY when the wiki TP explicitly carries the SAME
        # currency code as the consensus (no symbol/empty-ccy guesses → no cross-ccy
        # false diff, audit MEDIUM C1) and parse the LAST monetary number so a leading
        # "12-month TP HK$120" isn't read as 12 (audit MEDIUM C2).
        _nums = re.findall(r"\d[\d,]*\.?\d*", _wiki_variant.tp)
        _same_ccy = bool(ccy) and ccy in _wiki_variant.tp
        if _nums and _same_ccy and pd.notna(tp) and tp > 0:
            _hp = float(_nums[-1].replace(",", ""))
            _d = (_hp / tp - 1) * 100
            _dcls = "cmsi-ch-up" if _d >= 0 else "cmsi-ch-down"
            _vs = "vs 一致" if _zh else "vs cons."
            _tp_html += f" <span class='{_dcls}'>({_d:+.0f}% {_vs})</span>"
        _house_rows.append((_lbl_tp, _tp_html))
    theme.consensus_house(_cons_rows, _house_rows,
                          consensus_label=i18n.t("drill.variant.consensus"),
                          house_label=i18n.t("drill.variant.house"))
    st.caption(i18n.t("drill.variant.disclaimer"))

st.divider()

# ---------- LLM Wiki memo ----------
wiki_page = wiki.find_wiki(ticker)
if wiki_page is None:
    st.caption(i18n.t("drill.wiki.none"))
else:
    # Compliance gate — different banner for internal vs sanitized public view.
    if wiki_page.is_sanitized:
        theme.md_note("公开研究摘要" if i18n.get_lang() == "zh" else "Public research summary", i18n.t("drill.wiki.banner_public"))
    else:
        st.warning(
            "**本材料仅供内部参考，不构成任何证券的投资建议或邀请。** "
            "分析师个人观点不代表 CMS HK / 招商证券国际公司立场。"
            "Rating / TP 引用自 CMS HK 官方研报，请勿对外分发。"
            "Source-of-truth 仍是 Bloomberg / Wind / 官方研报 PDF。",
            icon="⚠️",
        )
    # Editorial memo: ▎red section title (updated date in meta) → rating/TP hairline
    # strip → sector chips → eyebrow-labelled Summary / Thesis. Replaces the old
    # generic "### title / **评级**: x · **目标价**: y / **摘要**: …" markdown.
    theme.section_header(i18n.t("drill.wiki.memo_title"),
                         meta=(wiki_page.last_updated or None))
    _bar: list[tuple[str, str]] = []
    if wiki_page.rating:
        _bar.append((i18n.t("drill.wiki.rating"), wiki_page.rating))
    if wiki_page.tp:
        _bar.append((i18n.t("drill.wiki.tp"), wiki_page.tp))
    if _bar:
        theme.memo_meta_bar(_bar)
    if wiki_page.sectors:
        theme.chips(wiki_page.sectors)

    if wiki_page.summary:
        theme.eyebrow(i18n.t("drill.wiki.summary"))
        st.markdown(wiki_page.summary)
    if wiki_page.thesis:
        theme.eyebrow(i18n.t("drill.wiki.thesis"))
        st.markdown(wiki_page.thesis)
    if wiki_page.sources:
        st.caption(f"{i18n.t('drill.wiki.sources')}: {wiki_page.sources}")

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

    st.caption(f"{i18n.t('drill.wiki.source_file')}: `{wiki_page.file_path}`")
    st.divider()

# ---------- 行情终端 (dark candlestick — Hybrid 基调:chart-heavy surface 局部上暗色交易台) ----------
# DB 只存 close;K 线单独取真实 OHLCV(yfinance,cached 1h)。无数据则整段跳过(不留空标题)。
from lib import candlestick_terminal as cterm

_ohlcv = cterm.fetch_ohlcv(ticker)
if not _ohlcv.empty:
    theme.section_header("行情终端" if i18n.get_lang() == "zh" else "Price Terminal")
    cterm.render(ticker=ticker, name=display_name, df=_ohlcv, ccy=ccy,
                 prefer_cn=(i18n.get_lang() == "zh"))
    st.divider()

# ---------- Relative strength (vs sector benchmark) ----------
# Replaces the old absolute USD price line — a single ticker's absolute curve has
# near-zero judgment value for a sell-side desk; what matters is whether it is
# out/under-performing its sector. Falls back to the absolute price line when no
# benchmark overlap is available (no sector tag, or benchmarks_daily empty).
theme.section_header(i18n.t("drill.section.rs"))
# LOCAL currency (per user): HK stock in HKD, A-share in CNY, US in USD — matched
# against a same-currency benchmark so the rebased comparison carries no FX noise.
closes = db.get_close_series((ticker,))
ser = closes[ticker].dropna() if (not closes.empty and ticker in closes.columns) else None
if ser is None or ser.empty:
    st.warning(i18n.t("drill.warn.no_price"))
else:
    from lib import charts
    from lib import benchmarks as bench

    chosen = _route_benchmarks(ticker, sectors)
    bench_series = bench.close_series()
    avail = [s for s in chosen if s in bench_series]
    # Chart legend + caption use LOCALIZED benchmark names (user: 中文描述, not raw
    # symbols like HSHCI.HK / ^HSI / ^SP500-352020).
    labels = {s: i18n.bench_name(s, bench.BENCHMARKS.get(s, s)) for s in avail}
    bdict = {labels[s]: bench_series[s] for s in avail}

    fig_rs, anchor_iso = (None, None)
    if bdict:
        fig_rs, anchor_iso = charts.relative_strength_chart(
            ser, bdict, stock_name=display_name,
            title=i18n.t("drill.rs.title", bbg=bbg),
        )

    if fig_rs is not None:
        st.plotly_chart(fig_rs, width="stretch", theme=None, config={"displayModeBar": False})
        bench_names = " · ".join(labels[s] for s in avail)
        st.caption(i18n.t("drill.rs.caption", date=anchor_iso, benches=bench_names, ccy=ccy))
    else:
        # Graceful fallback: absolute close in the stock's LOCAL currency
        # (foreign listing with no healthcare benchmark, or benchmarks_daily empty).
        ydf = ser.to_frame(name=display_name)
        fig = charts.price_line_chart(
            ydf,
            title=i18n.t("drill.chart.title", bbg=bbg, n=len(ser), ccy=ccy),
            ylabel=f"{ccy} close",
        )
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})
        st.caption(i18n.t("drill.rs.fallback"))

# ---------- Return windows + multiples panel ----------
rets = db.compute_returns(closes)
col_perf, col_mult = st.columns(2)
with col_perf:
    theme.subsection(i18n.t("drill.ret_windows"))
    if rets.empty or ticker not in rets.index:
        st.caption(i18n.t("drill.warn.no_return"))
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
            column_labels={"Return %": i18n.t("drill.col.return")},
            index_label=i18n.t("drill.col.window"),
        )

with col_mult:
    theme.subsection(i18n.t("drill.latest_mults"))
    if mults_row is None:
        st.caption(i18n.t("drill.warn.no_mult_snap"))
    else:
        mult_rows = []
        for label, key, kind in [
            (i18n.t("drill.mult.trailing_pe"), "trailing_pe", "x"),
            (i18n.t("drill.mult.forward_pe"), "forward_pe", "x"),
            (i18n.t("drill.mult.ev_ebitda"), "ev_ebitda", "x"),
            (i18n.t("drill.mult.ev_sales"), "ev_sales", "x"),
            (i18n.t("drill.mult.pb"), "pb", "x"),
            (i18n.t("drill.mult.fcf_yield"), "fcf_yield", "pct_dec"),
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
        _mlabel, _vlabel = i18n.t("drill.ext.col.metric"), i18n.t("drill.ext.col.value")
        st.table(
            pd.DataFrame(mult_rows)
            .rename(columns={"Metric": _mlabel, "Value": _vlabel})
            .set_index(_mlabel)
        )

st.divider()

# ---------- SEC financial trends (US-only, multi-period XBRL) ----------
# Multi-period Revenue / R&D / Cash from SEC XBRL via lib.sec_facts (reads the
# committed snapshots.db → works offline). US-GAAP only: HK 18A (IFRS) / 科创板
# (PRC CAS) file no SEC report → graceful note (financial-strategist + Codex/GLM
# /cccg: ship US-only with fallback, never blank columns for HK/A names).
from lib import sec_facts as _sf
from lib import charts as _charts

theme.section_header(i18n.t("drill.sec.section"))
_sec_status = _sf.company_status(ticker)
if not _sec_status or _sec_status.get("sec_status") != "ok":
    st.caption(i18n.t("drill.sec.na"))
else:
    _trend_specs = [
        ("revenue", i18n.t("drill.sec.revenue"), theme.UP),
        ("rnd", i18n.t("drill.sec.rnd"), theme.SECTOR_PALETTE[2]),
        ("cash", i18n.t("drill.sec.cash"), theme.INK_2),
    ]
    _cols = st.columns(3)
    for _i, (_kpi_key, _label, _color) in enumerate(_trend_specs):
        _ts, _concept = _sf.kpi_timeseries(ticker, _kpi_key, freq="annual")
        with _cols[_i]:
            _valid = _ts.dropna(subset=["value"]) if not _ts.empty else _ts
            if _valid.empty:
                theme.subsection(_label)
                st.caption(i18n.t("drill.sec.no_concept"))
                continue
            _tail = _valid.tail(6)
            _mx = _tail["value"].abs().max()
            _scale, _unit = (1e9, "USD bn") if _mx >= 1e9 else (1e6, "USD mn")
            _ser = _tail.set_index(pd.to_datetime(_tail["end_date"]))["value"] / _scale
            _fig = _charts.mini_trend_chart(_ser, title=_label, color=_color, ylabel=_unit)
            st.plotly_chart(_fig, width="stretch", theme=None, config={"displayModeBar": False})
            _last = _tail.iloc[-1]
            _yoy = _last.get("yoy")
            _yoy_str = f" · YoY {_yoy:+.1f}%" if pd.notna(_yoy) else ""
            st.caption(i18n.t("drill.sec.latest", val=fmt.fmt_money_b(_last["value"]),
                              date=str(_last["end_date"])) + _yoy_str)

    # Cash runway (biotech only): (cash + short-term investments) / annual R&D burn.
    # Codex /cccg: cash is instant, R&D is duration — use latest annual of each and
    # label it as a rough estimate with the period end.
    if "biotech" in sectors:
        _cash_ts, _ = _sf.kpi_timeseries(ticker, "cash", freq="annual")
        _rnd_ts, _ = _sf.kpi_timeseries(ticker, "rnd", freq="annual")
        _sti_ts, _ = _sf.kpi_timeseries(ticker, "short_term_investments", freq="annual")
        _cv = _cash_ts.dropna(subset=["value"]) if not _cash_ts.empty else _cash_ts
        _rv = _rnd_ts.dropna(subset=["value"]) if not _rnd_ts.empty else _rnd_ts
        if not _cv.empty and not _rv.empty:
            _cash_v = _cv.iloc[-1]["value"]
            _rnd_v = _rv.iloc[-1]["value"]
            _sti_v = (_sti_ts.dropna(subset=["value"]).iloc[-1]["value"]
                      if (not _sti_ts.empty and not _sti_ts["value"].dropna().empty) else 0.0)
            if _rnd_v and _rnd_v > 0:
                _runway = (_cash_v + (_sti_v or 0)) / _rnd_v
                st.caption(i18n.t("drill.sec.runway", years=f"{_runway:.1f}",
                                  date=str(_cv.iloc[-1]["end_date"])))
    st.caption(i18n.t("drill.sec.source", filed=str(_sec_status.get("latest_filed") or "—")))

st.divider()

# ---------- Extended fundamentals (live yfinance.info, cached 1h) ----------
# Gated behind an explicit button so that Streamlit Cloud cold-start visits
# don't pay a 30s+ yfinance.info round-trip on every page load. The button
# triggers a single cached fetch — subsequent reruns hit the cache.
@st.cache_data(ttl=3600, show_spinner="Loading fundamentals…")
def _yf_info(t: str) -> dict:
    """Fundamentals as an info-like dict, cached 1h PER TICKER.

    Source priority: cron-cached company_profile in snapshots.db FIRST (live
    yfinance.info is rate-limited/blocked from Streamlit Cloud IPs → returns empty);
    live yfinance.info only as fallback when the ticker has no cached profile row.

    NB: param must NOT start with '_' — Streamlit drops underscore-prefixed args
    from the cache key. With `_t`, the first ticker fetched was cached and returned
    for every other ticker (the "every company shows Innovent" bug).
    """
    prof = db.query("SELECT * FROM company_profile WHERE ticker = ?", (t,))
    if not prof.empty:
        row = prof.iloc[0].to_dict()
        row.pop("ticker", None)
        row.pop("fetched_at", None)
        # drop nulls so the page's "—" fallback still shows for missing fields
        return {k: v for k, v in row.items()
                if v is not None and not (isinstance(v, float) and pd.isna(v))}
    try:  # fallback: live (works locally w/ proxy; usually blocked on cloud)
        return yf.Ticker(t).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def _summary_cn(ticker: str, en_text: str) -> str | None:
    """Cached Chinese translation of the business summary (jobs/translate_profiles.py),
    but only if its en_hash still matches the current English text (else it's stale →
    return None so the page shows the English source)."""
    df = db.query("SELECT en_hash, summary_cn FROM profile_cn WHERE ticker = ?", (ticker,))
    if df.empty:
        return None
    row = df.iloc[0]
    if row["en_hash"] == hashlib.sha256((en_text or "").encode("utf-8")).hexdigest():
        return row["summary_cn"]
    return None


with st.expander(i18n.t("drill.ext.expander"), expanded=False):
    btn_key = f"fetch_yf_info_{ticker}"
    fetched_key = f"fetched_yf_info_{ticker}"

    cols = st.columns([1, 3])
    if cols[0].button(i18n.t("drill.ext.fetch"), key=btn_key, help=i18n.t("drill.ext.fetch_help")):
        st.session_state[fetched_key] = True

    if not st.session_state.get(fetched_key):
        st.caption(i18n.t("drill.ext.hint"))
    else:
        info = _yf_info(ticker)
        if not info:
            st.caption(i18n.t("drill.ext.empty"))
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

            _push(i18n.t("drill.ext.f.ebitda"), info.get("ebitda"))
            _push(i18n.t("drill.ext.f.total_cash"), info.get("totalCash"))
            _push(i18n.t("drill.ext.f.total_debt"), info.get("totalDebt"))
            _push(i18n.t("drill.ext.f.total_rev"), info.get("totalRevenue"))
            _push(i18n.t("drill.ext.f.rev_growth"), info.get("revenueGrowth"), "pct")
            _push(i18n.t("drill.ext.f.gross_margin"), info.get("grossMargins"), "pct")
            _push(i18n.t("drill.ext.f.op_margin"), info.get("operatingMargins"), "pct")
            _push(i18n.t("drill.ext.f.profit_margin"), info.get("profitMargins"), "pct")
            _push(i18n.t("drill.ext.f.roe"), info.get("returnOnEquity"), "pct")
            _push(i18n.t("drill.ext.f.peg"), info.get("trailingPegRatio"), "x")
            _push(i18n.t("drill.ext.f.div_yield"), info.get("dividendYield"), "pct")
            _push(i18n.t("drill.ext.f.beta"), info.get("beta"), "x")
            _push(i18n.t("drill.ext.f.shares_out"), info.get("sharesOutstanding"), "int")
            _push(i18n.t("drill.ext.f.float_shares"), info.get("floatShares"), "int")

            # st.table — static, no sort header (Value column is mixed-type).
            ext_df = pd.DataFrame(rows).rename(columns={
                "Metric": i18n.t("drill.ext.col.metric"),
                "Value": i18n.t("drill.ext.col.value"),
            }).set_index(i18n.t("drill.ext.col.metric"))
            st.table(ext_df)

            if info.get("longBusinessSummary"):
                theme.subsection(i18n.t("drill.ext.biz_summary"))
                en_summary = info["longBusinessSummary"]
                cn_summary = _summary_cn(ticker, en_summary) if i18n.get_lang() == "zh" else None
                if cn_summary:
                    st.markdown(cn_summary)
                else:
                    if i18n.get_lang() == "zh":
                        st.caption(i18n.t("drill.ext.biz_summary_note"))
                    st.markdown(en_summary)

# ---------- Cross-sector tags ----------
theme.subsection(i18n.t("drill.membership"))
# Drop the synthetic "_coverage" pseudo-sector — it's surfaced as the red coverage
# chip in the header now, so it would be redundant (and confusing) down here.
_member_sectors = [s for s in sectors if s != "_coverage"]
if _member_sectors:
    theme.chips(_member_sectors)
else:
    st.caption(i18n.t("drill.no_sector"))

# ---------- Footer caveats ----------
with st.expander(i18n.t("drill.onboarding.title")):
    st.markdown(i18n.t("drill.onboarding.body"))
st.caption(
    "Wiki memo 反映 CMS HK 内部观点 + George 自己的迭代，**不是中立分析**。"
    " 评级 / TP 引用必带 wiki Last updated 时间戳，>30 天请回到原研报核对。"
)
