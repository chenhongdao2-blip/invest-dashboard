"""Lightweight i18n for the dashboard — dict-based, render-layer only.

Ship-gate #3 (Codex): translation MUST happen at render time, never inside an
`@st.cache_data` function. Cache keys do not include the language, so a cached
function that returned translated strings would serve stale-language content
after a toggle. Rule enforced here by construction:
  - `t()` reads `st.session_state["lang"]` at call time and returns a plain str.
  - The locale tables (`locales/zh.py`, `locales/en.py`) are plain module-level
    dicts — never cached, never keyed by anything.
  - Cached data functions stay language-agnostic (raw data only); callers
    translate the *labels* around them.

Language state lives in `st.session_state["lang"]` ∈ {"zh","en"}, initialised
once at the app entry (`init_lang`) so every page — reached by deep-link or nav —
shares one value (avoids the half-Chinese/half-English page Codex flagged).
"""

from __future__ import annotations

from urllib.parse import urlencode

import streamlit as st

from lib import theme
from lib.locales import zh as _zh
from lib.locales import en as _en
from lib.locales import pages_zh as _pages_zh
from lib.locales import pages_en as _pages_en

DEFAULT_LANG = "zh"
# Phase 1 (strategy) + Phase 2 (pages/shared) tables merged per language.
_TABLES = {
    "zh": {**_zh.STRINGS, **_pages_zh.STRINGS},
    "en": {**_en.STRINGS, **_pages_en.STRINGS},
}

def init_lang() -> None:
    """Seed the language once, then adopt `?lang=` from the URL (wave-3 F1:
    the query-param → session_state sync is centralised HERE — single source,
    no per-page `_qp_lang` blocks). Call at app entry AND defensively per page
    (cheap), so a deep-linked page never hits a missing key.

    Assignment only, NO st.rerun(): init_lang runs before any `t()` call on
    every page, so writing session_state here already makes the whole page
    render in the new language this same frame. A rerun here would, under
    st.navigation, bounce a deep-linked sub-page back to the default page on the
    first frame and drop sibling query params like `?ticker=` (wave-3 round-1
    regression — `/Model_Drill?ticker=VEEV&lang=en` jumped to `/`)."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANG
    qp_lang = st.query_params.get("lang")
    if qp_lang in ("zh", "en") and qp_lang != st.session_state["lang"]:
        st.session_state["lang"] = qp_lang


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANG)


def _cur_qp() -> dict:
    """Current query params as {key: [values]} — preserves repeated / list-valued
    params (Codex M4: `to_dict()` collapses multiplicity). Empty when there is
    no run-context.

    The bare `except` is intentional (m6): `lang_toggle_html()` is exercised by
    the C01/C02 pure-string probes at bare import (no Streamlit
    ScriptRunContext), where touching `st.query_params` raises — degrading to
    `{}` there yields a plain `?lang=x` href. Narrowing to a specific class is
    avoided because the no-context exception type is not stable across Streamlit
    versions; the fallback only loses sibling params in that offline probe path,
    never in a live page."""
    try:
        return {k: st.query_params.get_all(k) for k in st.query_params.keys()}
    except Exception:
        return {}


def _lang_href(code_lang: str) -> str:
    """Anchor href that switches language while PRESERVING sibling query params
    (`?ticker=NVDA`, plus any repeated params, stay alive across a toggle —
    C09 / M4). Only `lang` is overridden (to a single value); everything else
    passes through at full multiplicity via `doseq=True`."""
    return "?" + urlencode({**_cur_qp(), "lang": [code_lang]}, doseq=True)


def lang_toggle_html() -> str:
    """The outlined 中|EN segmented language switch (shared HTML).

    Single source for BOTH the strategy-banner toggle and the page-level
    toggle (strategy_banner.live_title calls this too), so the two skins can
    never drift (C05 / BANR2). Segment tokens mirror the frozen banner spec:
    mono 11px / 600 / .08em, padding 5px 12px, active bg CMSI_RED + PAPER
    text, inactive transparent + INK_3, container 1px solid PAPER_EDGE
    radius 3, real `<a target="_self">` anchors (full-page reload — accepted
    BANR2 mechanism). Active state is decided internally via `get_lang()`;
    with no session state it falls back to zh without crashing."""
    cur = get_lang()

    def seg(code: str, code_lang: str) -> str:
        on = (code_lang == cur)
        return (
            f'<a href="{_lang_href(code_lang)}" target="_self" '
            f'style="font-family:{theme.FONT_MONO};font-size:11px;font-weight:600;'
            f'letter-spacing:.08em;padding:5px 12px;text-decoration:none;'
            f'display:inline-block;'
            f'background:{theme.CMSI_RED if on else "transparent"};'
            f'color:{theme.PAPER if on else theme.INK_3}">{code}</a>'
        )

    return (
        f'<div style="display:inline-flex;border:1px solid {theme.PAPER_EDGE};'
        f'border-radius:3px;overflow:hidden">'
        f'{seg("中", "zh")}{seg("EN", "en")}</div>'
    )


def t(key: str, **kwargs) -> str:
    """Translate `key` for the current language (render-layer call).

    Fallback chain: current lang → DEFAULT_LANG → the key itself (so a missing
    string is visible as its key in dev rather than crashing). `kwargs` are
    applied via str.format when present (e.g. t('x.benchmark', sym='XBI'))."""
    lang = get_lang()
    val = _TABLES.get(lang, {}).get(key)
    if val is None:
        val = _TABLES[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            val = val.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return val


def common_cols() -> dict:
    """Shared df-column → translated-header map (render-time). Pass as
    `column_labels=i18n.common_cols()` (merge page-specific extras on top).
    Pure-abbreviation financial columns (EV/EBITDA, EV/Sales, P/B) are left
    untranslated — universal in sell-side tables. Keyed by the EXACT display
    column names the pages build."""
    return {
        "Name": t("common.col.name"),
        "Last": t("common.col.last"),
        "Ticker": t("common.col.ticker"),
        "1D %": t("common.col.1d"),
        "5D %": t("common.col.5d"),
        "1M %": t("common.col.1m"),
        "3M %": t("common.col.3m"),
        "6M %": t("common.col.6m"),
        "YTD %": t("common.col.ytd"),
        "vs SPX": t("common.col.vs_spx"),
        "Mcap USD ($B)": t("common.col.mcap_b"),
        "Trail P/E": t("common.col.trail_pe"),
        "Fwd P/E": t("common.col.fwd_pe"),
        "FCF Yld": t("common.col.fcf_yld"),
    }


# ── data-value localization (benchmarks / sectors / domains) ──────────────
# These translate DATA values (not UI chrome): benchmark long-names from
# lib.benchmarks.BENCHMARKS, and raw sector/domain ids from the universe tables.
# Draft CN names — GLM-reviewed via /cccg. Ticker column already shows the
# symbol (XLV / ^HSI …), so the name column carries the Chinese name only.
_GICS_ZH = {
    "XLK": "信息技术",
    "XLC": "通信服务",
    "XLY": "可选消费",
    "XLF": "金融",
    "XLI": "工业",
    "XLP": "必选消费",
    "XLE": "能源",
    "XLU": "公用事业",
    "XLB": "材料",
    "XLRE": "房地产",
}
_AI_ZH = {
    "^SOX": "费城半导体指数",
    "SMH": "VanEck 半导体",
    "AIQ": "Global X 人工智能",
    "2644.T": "Global X 日本半导体",
    "091160.KS": "KODEX 韩国半导体",
    "442580.KS": "PLUS 全球HBM半导体",
    "512480.SS": "中证半导体",
    "515880.SS": "中证通信(光模块/CPO)",
    "159819.SZ": "人工智能ETF",
    "588200.SS": "科创芯片",
    "3191.HK": "中国半导体(港)",
}
_BENCH_ZH = {
    "XLV": "医疗保健精选行业",
    "XBI": "标普生物科技",
    "XPH": "标普制药",
    "IXJ": "iShares 全球医疗保健",
    "IHF": "美国医疗服务商",
    "IHI": "美国医疗器械",
    "^HSI": "恒生指数",
    "^GSPC": "标普 500 指数",
    "^SP500-352020": "标普500医药",
    "^NDX": "纳斯达克100",
    "000001.SS": "上证综指",
    "IGV": "美国科技软件",
    "XHS": "美国医院服务",
    "HSHCI.HK": "恒生医疗保健",
    "512170.SS": "中证医疗（A股）",
}
_SECTOR_ZH = {
    "biotech": "生物科技",
    "pharma": "制药",
    "hc_ai": "医疗+AI",
    "medtech": "医疗器械",
    "hospital_care": "医院服务",
    "managed_care": "管理式医疗",
    "cxo": "CXO 与生命科学",
    # AI domain sectors (产业链 L1–L6)
    "ai_equip": "半导体设备材料",
    "ai_chip": "芯片设计",
    "ai_memory": "存储芯片",
    "ai_foundry": "代工封测",
    "ai_interconnect": "光互联/PCB",
    "ai_server": "服务器/散热/电源",
    "_coverage": "覆盖",          # CMSI cover-list marker (pseudo-sector, not a real sector)
}
_SECTOR_EN = {
    "biotech": "Biotech",
    "pharma": "Pharma",
    "hc_ai": "Healthcare + AI",
    "medtech": "Medtech",
    "hospital_care": "Hospital Care",
    "managed_care": "Managed Care",
    "cxo": "CXO & Life Sciences",
    # AI domain sectors (supply-chain L1–L6)
    "ai_equip": "Semi Equipment & Materials",
    "ai_chip": "Chip Design",
    "ai_memory": "Memory (DRAM/HBM)",
    "ai_foundry": "Foundry & OSAT",
    "ai_interconnect": "Interconnect (Optical/PCB)",
    "ai_server": "Server/Cooling/Power",
    "_coverage": "Coverage",     # CMSI cover-list marker (pseudo-sector, not a real sector)
}
_DOMAIN = {"healthcare": {"zh": "医疗健康", "en": "Healthcare"},
           "ai": {"zh": "人工智能", "en": "AI"}}

# Therapeutic-area buckets (mnc_ma_deals ta_group) → 中文. On the zh page we show
# bilingual ("肿瘤 Oncology"); on en, English only.
_TA_ZH = {
    "Oncology": "肿瘤",
    "Cardiovascular/Metabolic": "心血管/代谢",
    "Immunology": "免疫",
    "Vaccines": "疫苗",
    "Gene/Cell Therapy": "基因/细胞治疗",
    "CNS/Neurology": "中枢神经",
    "Rare Disease": "罕见病",
    "Dermatology/Aesthetics": "皮肤/医美",
    "Respiratory": "呼吸",
    "Consumer Health": "消费保健",
    "Ophthalmology": "眼科",
    "Diagnostics": "诊断",
    "Anti-Infectives": "抗感染",
    "Other": "其他",
}

# IPO subscription tiers — CSV stores the Chinese label; map to EN for the
# English view. Keys are the EXACT strings in ipo_picks.csv 'tier' column.
_IPO_TIER_EN = {
    "重点申购+": "Strong Buy+",
    "重点申购": "Strong Buy",
    "推荐申购": "Subscribe",
    "谨慎申购": "Cautious",
    "不申购": "Avoid",
}


def ipo_tier(tier_cn: str) -> str:
    """Localize an IPO subscription tier. zh → as-is (CSV is already Chinese);
    en → mapped English label (falls back to the raw value)."""
    if get_lang() == "zh":
        return tier_cn
    return _IPO_TIER_EN.get(tier_cn, tier_cn)


def bench_name(sym: str, fallback: str = "") -> str:
    """Localized benchmark long-name. zh → Chinese; en → English fallback (the
    df already carries the English name)."""
    if get_lang() == "zh":
        return _BENCH_ZH.get(sym) or _GICS_ZH.get(sym) or _AI_ZH.get(sym) or fallback or sym
    return fallback or sym


def sector_name(sid: str) -> str:
    """Localized sector display name from a raw sector id (e.g. 'hc_ai')."""
    table = _SECTOR_ZH if get_lang() == "zh" else _SECTOR_EN
    return table.get(sid, sid)


def ta_name(ta: str) -> str:
    """Therapeutic-area display name. zh → bilingual '肿瘤 Oncology'; en → 'Oncology'."""
    if get_lang() == "zh":
        cn = _TA_ZH.get(ta)
        return f"{cn} {ta}" if cn else ta
    return ta


def domain_name(d: str) -> str:
    """Localized domain display name from a raw domain id (e.g. 'healthcare')."""
    m = _DOMAIN.get(d)
    if not m:
        return d
    return m["zh"] if get_lang() == "zh" else m["en"]


def render_lang_toggle(anchor_cols: tuple[float, float] = (9.0, 1.0)) -> None:
    """Render the language switch as the outlined 中|EN segmented control pinned
    to the top-right of the content area (the user-visible "top bar"). Call it
    as the FIRST element on a page, before the page header.

    wave-3 F1: same skin AND same helper as the strategy-banner toggle
    (`lang_toggle_html()`). Segments are real `<a href="?…lang=…" target=_self>`
    anchors: clicking navigates with the lang query param (sibling params such
    as `?ticker=` preserved), and `init_lang()` adopts it into session_state on
    the next run — so subsequent `t()` calls already see the chosen language.
    `anchor_cols` is retained for signature compatibility with the 19 existing
    call sites but is ignored (a right-aligned flex row needs no column grid).
    """
    del anchor_cols  # kept for call-site compatibility; unused
    init_lang()
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;margin:0 0 6px">'
        f'{lang_toggle_html()}</div>',
        unsafe_allow_html=True,
    )
