"""Acceptance gate for the ETF panel feature — authored by the independent Evaluator.

Covers criteria A (data integrity), B (loader contract), E (tail/coverage),
and G (i18n keys) from docs/etf-harness/ACCEPTANCE.md.

Real-machine criteria C, D, F are NOT tested here (they require Streamlit running).

The Builder is FORBIDDEN from editing this file. Tests that fail today because the
loader or locale keys don't exist yet are expected and intentional — that is the
point of a gate.

Run: pytest tests/test_etf_panel.py -v  (from repo root)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "external"
APP_DIR = REPO_ROOT / "app"

UNIVERSE_CSV_PATH = DATA_DIR / "etf_hc_universe.csv"
HOLDINGS_CSV_PATH = DATA_DIR / "etf_hc_holdings.csv"
META_JSON_PATH = DATA_DIR / "etf_hc_meta.json"

# Add app/ to sys.path so `from lib import ...` mirrors how Streamlit sees it.
sys.path.insert(0, str(APP_DIR))

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures (shared across A and B groups)
# ──────────────────────────────────────────────────────────────────────────────

EXPECTED_UNIVERSE_COLS = {
    "domain", "sub_sector", "ticker", "name",
    "aum", "expense_ratio", "price",
    "year_high", "year_low",
    "ret_1m", "ret_3m", "ret_ytd", "ret_1y", "ret_3y", "ret_5y",
    "vol", "max_dd",
}

EXPECTED_HOLDINGS_COLS = {"etf_ticker", "rank", "symbol", "name", "weight_pct"}


def _load_universe_raw() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_CSV_PATH)


def _load_holdings_raw() -> pd.DataFrame:
    return pd.read_csv(HOLDINGS_CSV_PATH)


def _load_meta_raw() -> dict:
    with open(META_JSON_PATH) as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# A. Data integrity (read baked files directly — no app import)
# ──────────────────────────────────────────────────────────────────────────────


EXPECTED_TICKERS = {"XLV", "VHT", "IYH", "IBB", "XBI", "XPH", "PPH", "IHI", "IHF", "ARKG"}


def test_a1_universe_row_count_and_required_columns_and_domain():
    """A1: universe has exactly the curated 10 rows (exact ticker set); required columns present; every domain=='healthcare'."""
    df = _load_universe_raw()

    assert len(df) == 10, f"Expected 10 ETFs, got {len(df)}"

    actual_tickers = set(df["ticker"].tolist())
    assert actual_tickers == EXPECTED_TICKERS, (
        f"Ticker set mismatch. Extra: {actual_tickers - EXPECTED_TICKERS}  "
        f"Missing: {EXPECTED_TICKERS - actual_tickers}"
    )

    missing_cols = EXPECTED_UNIVERSE_COLS - set(df.columns)
    assert not missing_cols, f"Missing columns: {missing_cols}"

    non_hc = df[df["domain"] != "healthcare"]
    assert len(non_hc) == 0, f"Non-healthcare domain rows: {non_hc['ticker'].tolist()}"


def test_a2_each_etf_has_positive_aum_valid_expense_ratio_finite_ret_1y():
    """A2: aum>0; 0 < expense_ratio < 1; ret_1y is finite (not NaN/inf) for every row."""
    df = _load_universe_raw()

    bad_aum = df[~(df["aum"] > 0)]
    assert len(bad_aum) == 0, f"ETFs with aum <= 0: {bad_aum['ticker'].tolist()}"

    bad_er = df[~((df["expense_ratio"] > 0) & (df["expense_ratio"] < 1))]
    assert len(bad_er) == 0, f"ETFs with expense_ratio outside (0,1): {bad_er['ticker'].tolist()}"

    bad_ret = df[~df["ret_1y"].apply(lambda x: math.isfinite(float(x)))]
    assert len(bad_ret) == 0, f"ETFs with non-finite ret_1y: {bad_ret['ticker'].tolist()}"


def test_a3_weighted_rows_sum_matches_meta_within_tolerance_per_etf():
    """A3: for each ETF, sum of weighted-row weight_pct ≈ meta.weight_sum_pct_by_etf within ±0.5pp."""
    holdings = _load_holdings_raw()
    meta = _load_meta_raw()
    weight_sums = meta["weight_sum_pct_by_etf"]

    failures = []
    for ticker, expected_sum in weight_sums.items():
        weighted = holdings[(holdings["etf_ticker"] == ticker) & holdings["rank"].notna()]
        actual_sum = weighted["weight_pct"].sum()
        diff = abs(actual_sum - expected_sum)
        if diff > 0.5:
            failures.append(
                f"{ticker}: CSV sum={actual_sum:.4f}% meta={expected_sum}% diff={diff:.4f}pp (exceeds ±0.5pp)"
            )

    assert not failures, "Weight sum mismatches:\n" + "\n".join(failures)


def test_a4_tail_rows_have_null_weight_pct_and_empty_name():
    """A4: tail rows (rank is null) have weight_pct NaN/empty (NOT 0) AND name empty — 'unknown ≠ zero'."""
    holdings = _load_holdings_raw()
    tail = holdings[holdings["rank"].isna()]

    assert len(tail) > 0, "No tail rows found; expected symbol-only rows with null rank"

    # weight_pct must be NaN — explicitly not zero
    zero_weight_tail = tail[tail["weight_pct"] == 0.0]
    assert len(zero_weight_tail) == 0, (
        f"{len(zero_weight_tail)} tail rows have weight_pct==0.0 (must be NaN, not zero)"
    )

    non_nan_weight = tail[tail["weight_pct"].notna()]
    assert len(non_nan_weight) == 0, (
        f"{len(non_nan_weight)} tail rows have a non-null weight_pct"
    )

    # name must be empty/NaN — not a real name
    non_empty_name = tail[tail["name"].notna() & (tail["name"].astype(str).str.strip() != "")]
    assert len(non_empty_name) == 0, (
        f"{len(non_empty_name)} tail rows have a non-empty name field"
    )


def test_a5_xlv_rank1_is_lly_with_expected_weight_and_25_weighted_rows():
    """A5: XLV rank-1 symbol == 'LLY' with weight 16.0–16.8; XLV weighted-row count == 25."""
    holdings = _load_holdings_raw()

    xlv_weighted = holdings[(holdings["etf_ticker"] == "XLV") & holdings["rank"].notna()]
    assert len(xlv_weighted) == 25, f"XLV weighted rows: {len(xlv_weighted)} (expected 25)"

    rank1 = xlv_weighted[xlv_weighted["rank"] == 1]
    assert len(rank1) == 1, "Expected exactly one XLV rank-1 row"

    symbol = rank1.iloc[0]["symbol"]
    assert symbol == "LLY", f"XLV rank-1 symbol: '{symbol}' (expected 'LLY')"

    weight = float(rank1.iloc[0]["weight_pct"])
    assert 16.0 <= weight <= 16.8, f"XLV LLY weight: {weight}% (expected 16.0–16.8)"


# ──────────────────────────────────────────────────────────────────────────────
# B. Loader contract (imports app.lib.etf_panel — will fail until Builder ships)
# ──────────────────────────────────────────────────────────────────────────────


def test_b1_load_etf_universe_returns_10_rows_with_expected_columns():
    """B1: load_etf_universe() returns DataFrame with 10 rows and expected columns."""
    from lib import etf_panel  # noqa: PLC0415

    df = etf_panel.load_etf_universe()

    assert isinstance(df, pd.DataFrame), "load_etf_universe() must return a DataFrame"
    assert len(df) == 10, f"Expected 10 rows, got {len(df)}"
    missing = EXPECTED_UNIVERSE_COLS - set(df.columns)
    assert not missing, f"Missing columns: {missing}"


def test_b2_load_etf_holdings_returns_non_empty_with_weighted_and_tail_rows():
    """B2: load_etf_holdings() returns non-empty DataFrame containing both weighted and tail rows."""
    from lib import etf_panel  # noqa: PLC0415

    df = etf_panel.load_etf_holdings()

    assert isinstance(df, pd.DataFrame), "load_etf_holdings() must return a DataFrame"
    assert not df.empty, "load_etf_holdings() returned empty DataFrame"

    missing = EXPECTED_HOLDINGS_COLS - set(df.columns)
    assert not missing, f"Missing columns: {missing}"

    weighted = df[df["rank"].notna()]
    tail = df[df["rank"].isna()]
    assert len(weighted) > 0, "No weighted rows found (rank not null)"
    assert len(tail) > 0, "No tail rows found (rank null)"


def test_b3_holdings_for_xlv_returns_sorted_weighted_df_and_tail_list():
    """B3: holdings_for(df, 'XLV') -> (weighted_df, tail_symbols).

    weighted_df: ≤25 rows, all rank not-null, monotonically increasing rank, all weight_pct not-null.
    tail_symbols: non-empty list[str].
    """
    from lib import etf_panel  # noqa: PLC0415

    holdings = etf_panel.load_etf_holdings()
    weighted_df, tail_symbols = etf_panel.holdings_for(holdings, "XLV")

    # weighted_df contract
    assert isinstance(weighted_df, pd.DataFrame)
    assert len(weighted_df) <= 25, f"weighted_df has {len(weighted_df)} rows (max 25)"
    assert weighted_df["rank"].notna().all(), "weighted_df contains null-rank rows"
    assert weighted_df["weight_pct"].notna().all(), "weighted_df contains null weight_pct"

    ranks = weighted_df["rank"].tolist()
    assert ranks == sorted(ranks), f"weighted_df not sorted by rank: {ranks[:5]}..."

    # tail_symbols contract
    assert isinstance(tail_symbols, list), f"tail_symbols must be list, got {type(tail_symbols)}"
    assert len(tail_symbols) > 0, "tail_symbols is empty for XLV"
    assert all(isinstance(s, str) for s in tail_symbols), "tail_symbols must be list[str]"


def test_b4_missing_files_return_empty_dataframe_and_empty_dict(tmp_path, monkeypatch):
    """B4: when data files are absent, loaders return empty DataFrame; etf_meta() returns {}.

    Monkeypatches the module-level path constants UNIVERSE_CSV, HOLDINGS_CSV, META_JSON
    to point at non-existent files.
    """
    from lib import etf_panel  # noqa: PLC0415

    absent_csv = tmp_path / "does_not_exist.csv"
    absent_json = tmp_path / "does_not_exist.json"
    # These paths do not exist — do not create them.

    monkeypatch.setattr(etf_panel, "UNIVERSE_CSV", absent_csv)
    monkeypatch.setattr(etf_panel, "HOLDINGS_CSV", absent_csv)
    monkeypatch.setattr(etf_panel, "META_JSON", absent_json)

    uni = etf_panel.load_etf_universe()
    assert isinstance(uni, pd.DataFrame) and uni.empty, (
        "load_etf_universe() must return empty DataFrame when file is missing"
    )

    hld = etf_panel.load_etf_holdings()
    assert isinstance(hld, pd.DataFrame) and hld.empty, (
        "load_etf_holdings() must return empty DataFrame when file is missing"
    )

    meta = etf_panel.etf_meta()
    assert meta == {}, f"etf_meta() must return {{}} when file is missing, got {meta}"


def test_b5_no_fabricated_zero_weight_in_tail():
    """B5: loader must NOT fabricate weight_pct==0.0 for tail rows; NaN must be preserved."""
    from lib import etf_panel  # noqa: PLC0415

    holdings = etf_panel.load_etf_holdings()
    tail = holdings[holdings["rank"].isna()]

    zero_rows = tail[tail["weight_pct"] == 0.0]
    assert len(zero_rows) == 0, (
        f"Loader fabricated weight_pct==0.0 for {len(zero_rows)} tail rows "
        f"(symbols: {zero_rows['symbol'].tolist()[:5]})"
    )


# ──────────────────────────────────────────────────────────────────────────────
# E. Tail / coverage helper
# ──────────────────────────────────────────────────────────────────────────────


def test_e1_xbi_tail_symbols_count_exceeds_100():
    """E: holdings_for(..., 'XBI') tail_symbols length > 100 — equal-weight tail surfaced."""
    from lib import etf_panel  # noqa: PLC0415

    holdings = etf_panel.load_etf_holdings()
    _weighted_df, tail_symbols = etf_panel.holdings_for(holdings, "XBI")

    assert len(tail_symbols) > 100, (
        f"XBI tail_symbols has {len(tail_symbols)} entries; expected >100 for an equal-weight ETF"
    )


# ──────────────────────────────────────────────────────────────────────────────
# G. i18n keys
# ──────────────────────────────────────────────────────────────────────────────

REQUIRED_ETF_I18N_KEYS = {
    "hc_etf.title",
    "hc_etf.caption",
    "hc_etf.col.rank",
    "hc_etf.col.symbol",
    "hc_etf.col.name",
    "hc_etf.col.weight",
    "hc_etf.tail_more",
    "hc_etf.coverage",
}


def test_g1_required_etf_keys_exist_in_english_strings():
    """G1: all hc_etf.* keys are present in pages_en.STRINGS."""
    from lib.locales import pages_en  # noqa: PLC0415

    missing = REQUIRED_ETF_I18N_KEYS - set(pages_en.STRINGS.keys())
    assert not missing, f"Missing keys in pages_en.STRINGS: {sorted(missing)}"


def test_g1_required_etf_keys_exist_in_chinese_strings():
    """G1: all hc_etf.* keys are present in pages_zh.STRINGS."""
    from lib.locales import pages_zh  # noqa: PLC0415

    missing = REQUIRED_ETF_I18N_KEYS - set(pages_zh.STRINGS.keys())
    assert not missing, f"Missing keys in pages_zh.STRINGS: {sorted(missing)}"
