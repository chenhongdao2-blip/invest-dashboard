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

import streamlit as st

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
_LABELS = {"zh": "中文", "en": "EN"}


def init_lang() -> None:
    """Seed the language once. Call at app entry AND defensively per page (cheap),
    so a deep-linked page never hits a missing key."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANG


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANG)


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
_BENCH_ZH = {
    "XLV": "医疗保健精选行业",
    "XBI": "标普生物科技",
    "XPH": "标普制药",
    "IXJ": "iShares 全球医疗保健",
    "IHF": "美国医疗服务商",
    "IHI": "美国医疗器械",
    "^HSI": "恒生指数",
    "^GSPC": "标普 500 指数",
}
_SECTOR_ZH = {
    "biotech": "生物科技",
    "pharma": "制药",
    "hc_ai": "医疗+AI",
    "medtech": "医疗器械",
    "hospital_care": "医院服务",
    "managed_care": "管理式医疗",
    "cxo": "CXO 与生命科学",
}
_SECTOR_EN = {
    "biotech": "Biotech",
    "pharma": "Pharma",
    "hc_ai": "Healthcare + AI",
    "medtech": "Medtech",
    "hospital_care": "Hospital Care",
    "managed_care": "Managed Care",
    "cxo": "CXO & Life Sciences",
}
_DOMAIN = {"healthcare": {"zh": "医疗健康", "en": "Healthcare"}}


def bench_name(sym: str, fallback: str = "") -> str:
    """Localized benchmark long-name. zh → Chinese; en → English fallback (the
    df already carries the English name)."""
    if get_lang() == "zh":
        return _BENCH_ZH.get(sym, fallback or sym)
    return fallback or sym


def sector_name(sid: str) -> str:
    """Localized sector display name from a raw sector id (e.g. 'hc_ai')."""
    table = _SECTOR_ZH if get_lang() == "zh" else _SECTOR_EN
    return table.get(sid, sid)


def domain_name(d: str) -> str:
    """Localized domain display name from a raw domain id (e.g. 'healthcare')."""
    m = _DOMAIN.get(d)
    if not m:
        return d
    return m["zh"] if get_lang() == "zh" else m["en"]


def render_lang_toggle(anchor_cols: tuple[float, float] = (9.0, 1.0)) -> None:
    """Render the language switch as a SINGLE button pinned to the top-right of
    the content area (the user-visible "top bar"). Call it as the FIRST element
    on a page, before the page header, so subsequent `t()` calls in the same run
    already see the chosen language.

    One button (not a two-segment control): it shows the language you'll switch
    TO — "EN" while Chinese is active, "中文" while English is active — the common
    CN-site convention. `st.button` is a momentary trigger (no persistent widget
    value), so there is no widget-state↔session_state split to fight; on click we
    flip `st.session_state["lang"]` and rerun the whole page in the new language.
    """
    init_lang()
    cur = get_lang()
    other = "en" if cur == "zh" else "zh"
    _, right = st.columns(list(anchor_cols))
    with right:
        if st.button(_LABELS[other], key="_lang_btn", use_container_width=True):
            st.session_state["lang"] = other
            st.rerun()
