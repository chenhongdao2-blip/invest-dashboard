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


def test_a4_factset_weights_every_row_and_no_weight_is_ever_zero():
    """A4: under the FactSet source there is no symbol-only tail — every persisted
    row carries a real weight.

    This flipped on 2026-09-07. stockanalysis weighted only the top ~25 and the
    rest arrived symbol-only, so the invariant then was "a tail row's weight is
    NaN, never 0". stockanalysis now 404s and FactSet weights the whole book, so
    the invariant becomes "there is no unweighted row at all". The half that did
    NOT change is the one that matters: an unknown weight must never be written
    as 0.0, because zero is a claim and unknown is not.
    """
    holdings = _load_holdings_raw()

    unweighted = holdings[holdings["weight_pct"].isna()]
    assert len(unweighted) == 0, (
        f"{len(unweighted)} rows have no weight; FactSet weights every constituent, "
        "so this means the panel was built from the dead stockanalysis path"
    )
    assert (holdings["weight_pct"] != 0.0).all(), (
        "a 0.0 weight would turn 'unknown' into 'zero'"
    )
    assert holdings["rank"].notna().all(), "every weighted row is ranked"
    assert holdings["name"].notna().all(), "FactSet names every line it weights"


def test_a4b_a_weightless_tail_is_still_split_off_if_one_ever_returns():
    """The loader's degradation handling must survive the source swap.

    No committed row exercises it any more, so the protection added after the
    2026-08-29 incident would rot silently. Feed it a frame shaped like the old
    upstream and check the split still keys on the weight, not on the rank.
    """
    from lib import etf_panel  # noqa: PLC0415

    frame = pd.DataFrame([
        {"etf_ticker": "ZZZ", "rank": 1, "symbol": "AAA", "name": "A", "weight_pct": 60.0},
        {"etf_ticker": "ZZZ", "rank": 2, "symbol": "BBB", "name": "B", "weight_pct": 40.0},
        # the shape barchart returned: numbered, but weightless
        {"etf_ticker": "ZZZ", "rank": 3, "symbol": "CCC", "name": None, "weight_pct": None},
    ])
    weighted, tail = etf_panel.holdings_for(frame, "ZZZ")
    assert list(weighted["symbol"]) == ["AAA", "BBB"]
    assert tail == ["CCC"], "a ranked-but-weightless row is still tail"
    assert etf_panel.degraded_etfs(frame) == [], "2 of 3 weighted is not fully degraded"


def test_a5_xlv_rank1_is_lly_and_every_xlv_row_is_weighted():
    """A5: XLV's top line is Eli Lilly, and the whole XLV book is weighted.

    The row count is no longer pinned at 25 (that was stockanalysis's cap, not a
    property of the fund). The band on LLY is wide on purpose: it is a
    "did the mapping put the right number on the right symbol" check, not a
    market call.
    """
    holdings = _load_holdings_raw()

    xlv = holdings[holdings["etf_ticker"] == "XLV"]
    assert len(xlv) > 25, "FactSet returns the whole book, not a top-25 cap"
    assert xlv["weight_pct"].notna().all(), "every XLV row must carry a weight"

    rank1 = xlv[xlv["rank"] == 1]
    assert len(rank1) == 1, "Expected exactly one XLV rank-1 row"
    assert rank1.iloc[0]["symbol"] == "LLY"
    weight = float(rank1.iloc[0]["weight_pct"])
    assert 10.0 <= weight <= 20.0, f"XLV LLY weight: {weight}% (expected 10–20)"

    ranks = xlv.sort_values("rank")["weight_pct"].tolist()
    assert ranks == sorted(ranks, reverse=True), "rank must follow weight, descending"

    total = float(xlv["weight_pct"].sum())
    assert 95.0 <= total <= 101.0, f"XLV weights sum to {total}% — the book is incomplete"


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
    """B2: load_etf_holdings() returns a non-empty, fully weighted DataFrame."""
    from lib import etf_panel  # noqa: PLC0415

    df = etf_panel.load_etf_holdings()

    assert isinstance(df, pd.DataFrame), "load_etf_holdings() must return a DataFrame"
    assert not df.empty, "load_etf_holdings() returned empty DataFrame"

    missing = EXPECTED_HOLDINGS_COLS - set(df.columns)
    assert not missing, f"Missing columns: {missing}"

    assert df["weight_pct"].notna().all(), (
        "FactSet weights every constituent — an unweighted row means the panel was "
        "rebuilt from the dead stockanalysis/barchart path"
    )
    assert df["rank"].notna().all()
    assert df["etf_ticker"].nunique() == 10


def test_b3_holdings_for_xlv_returns_sorted_weighted_df_and_tail_list():
    """B3: holdings_for(df, 'XLV') -> (weighted_df, tail_symbols).

    weighted_df: every row ranked and weighted, sorted by rank ascending.
    tail_symbols: a list[str], now EMPTY — FactSet leaves nothing unweighted.
    The page caps what it draws (e1_etf_overview.HEAD_CAP); the loader does not.
    """
    from lib import etf_panel  # noqa: PLC0415

    holdings = etf_panel.load_etf_holdings()
    weighted_df, tail_symbols = etf_panel.holdings_for(holdings, "XLV")

    # weighted_df contract
    assert isinstance(weighted_df, pd.DataFrame)
    assert len(weighted_df) > 25, "the loader returns the whole book, uncapped"
    assert weighted_df["rank"].notna().all(), "weighted_df contains null-rank rows"
    assert weighted_df["weight_pct"].notna().all(), "weighted_df contains null weight_pct"

    ranks = weighted_df["rank"].tolist()
    assert ranks == sorted(ranks), f"weighted_df not sorted by rank: {ranks[:5]}..."

    # tail_symbols contract
    assert isinstance(tail_symbols, list), f"tail_symbols must be list, got {type(tail_symbols)}"
    assert tail_symbols == [], "nothing is unweighted under the FactSet source"


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


def test_e1_xbi_surfaces_its_whole_equal_weight_book():
    """E: XBI's long equal-weight book must all be there — and now WITH weights.

    This used to assert >100 *tail* symbols, i.e. >100 constituents whose weight
    stockanalysis never told us. The same 100+ names are still surfaced; the
    difference is that every one of them now carries a number.
    """
    from lib import etf_panel  # noqa: PLC0415

    holdings = etf_panel.load_etf_holdings()
    weighted_df, tail_symbols = etf_panel.holdings_for(holdings, "XBI")

    assert len(weighted_df) > 100, (
        f"XBI has {len(weighted_df)} weighted rows; expected >100 for an equal-weight ETF"
    )
    assert tail_symbols == []
    assert float(weighted_df["weight_pct"].max()) < 5.0, (
        "an equal-weight fund should have no dominant line — a big top weight would "
        "mean the weights were mapped to the wrong fund"
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
    "hc_etf.rest_more",
    "hc_etf.rest_more_trunc",
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
