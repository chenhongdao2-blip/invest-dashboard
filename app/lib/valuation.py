"""Cross-page valuation helpers.

Single home for logic that both valuation scanners need, so the HC page
(`5_Valuation_Scanner.py`) and the AI page (`a4_ai_valuation.py`) cannot drift
apart (R3 audit §6 — the two copies of `sector_pe_percentile` had already
diverged: only the AI copy carried the empty-frame guard).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ──────────────────────────────────────────────────────────────────────────
# Sector-internal P/E percentile
# ──────────────────────────────────────────────────────────────────────────
# CACHE-KEY CONTRACT — read before touching the signature.
#
# Streamlit keys @st.cache_data on (module, qualname, source_text) + the HASHED
# ARGUMENTS, and it EXCLUDES any parameter whose name starts with `_`
# (streamlit/runtime/caching/cache_utils.py). The previous page-local signature
#     sector_pe_percentile(_mults_df, _sector_map, pe_col)
# therefore hashed `pe_col` ALONE — two distinct values. Changing the sector
# selection returned the PREVIOUS sector's percentiles for the whole 300 s TTL
# (R3 audit C3). `6_Ticker_Drill.py:347-349` documents the same rule.
#
# Fix: the cached layer takes only hashable, fully-value-bearing tuples, so the
# key contains the real inputs. The public wrapper does the (cheap) reduction
# and stays uncached.
@st.cache_data(ttl=300)
def _sector_pe_percentile_cached(
    pe_pairs: tuple[tuple[str, float], ...],
    sector_pairs: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[pd.Series, dict[str, int], dict[str, int]]:
    pe = pd.Series(dict(pe_pairs), dtype=float)
    result: dict[str, float] = {}
    sector_n_eligible: dict[str, int] = {}
    sector_n_excluded: dict[str, int] = {}

    sector_tickers: dict[str, list[str]] = {}
    for t, secs in sector_pairs:
        for s in secs:
            sector_tickers.setdefault(s, []).append(t)

    for sec, t_list in sector_tickers.items():
        # dedupe like the original `index.intersection(t_list)` did — a ticker
        # listed twice under one sector must not be double-counted in the rank
        seen: set[str] = set()
        hit = [t for t in t_list if t in pe.index and not (t in seen or seen.add(t))]
        in_sec_all = pe.reindex(hit)
        # exclude non-positive (negative earnings) from the percentile base
        in_sec = in_sec_all[in_sec_all > 0].dropna()
        sector_n_eligible[sec] = len(in_sec)
        sector_n_excluded[sec] = len(t_list) - len(in_sec)
        if in_sec.empty:
            continue
        ranks = in_sec.rank(pct=True) * 100
        for t in t_list:
            if t in ranks.index:
                # keep the MIN percentile across sectors (cheapest ranking wins)
                if t not in result or ranks[t] < result[t]:
                    result[t] = float(ranks[t])
    return (pd.Series(result, name="pe_percentile", dtype=float),
            sector_n_eligible, sector_n_excluded)


def sector_pe_percentile(
    mults_df: pd.DataFrame,
    sector_map: dict[str, list[str]],
    pe_col: str,
) -> tuple[pd.Series, dict[str, int], dict[str, int]]:
    """Rank each ticker's P/E inside its sector (NaN and non-positive excluded).

    Returns (percentile [0,100] where 0 = cheapest, per-sector eligible-N dict,
    per-sector neg/missing-N dict). A ticker in several sectors keeps its
    cheapest ranking.
    """
    empty: tuple[pd.Series, dict[str, int], dict[str, int]] = (
        pd.Series(dtype=float, name="pe_percentile"), {}, {})
    if mults_df is None or mults_df.empty or pe_col not in mults_df.columns:
        return empty

    col = pd.to_numeric(mults_df[pe_col], errors="coerce")
    pe_pairs = tuple((str(t), float(v)) for t, v in col.items() if pd.notna(v))
    sector_pairs = tuple(
        (str(t), tuple(str(s) for s in secs)) for t, secs in sorted(sector_map.items())
    )
    if not sector_pairs:
        return empty
    return _sector_pe_percentile_cached(pe_pairs, sector_pairs)
