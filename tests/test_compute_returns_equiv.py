"""`compute_returns` vectorization must be a no-op on the numbers.

PR 2 replaces the per-ticker Python loop (`db.py` on `fix/audit-r3`) with a
column-wise implementation. The loop is the SPEC, not the vectorized rewrite,
so it is copied here verbatim as `_reference_compute_returns` and both are run
over the real `data/snapshots.db` — all tickers, all columns.

Deviation from design A.6: the design splits this into "vectorize with the OLD
YTD anchor" (step 1) then "flip the anchor" (step 2). PR 1 already flipped it on
the base branch, so the reference below is the PR-1-fixed loop and the two steps
collapse into one.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = REPO_ROOT / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from lib import db  # noqa: E402

_COLS = ["last", "1d_%", "5d_%", "1m_%", "3m_%", "6m_%", "ytd_%", "60d_%"]


# --------------------------------------------------------------------------
# verbatim copy of app/lib/db.py:154-231 @ fix/audit-r3 (PR 1 head)
# --------------------------------------------------------------------------
def _reference_compute_returns(closes: pd.DataFrame) -> pd.DataFrame:
    if closes.empty:
        return pd.DataFrame()

    closes = closes.sort_index()
    out: dict[str, dict[str, float | None]] = {}

    NAN = float("nan")
    for ticker in closes.columns:
        ser = closes[ticker].dropna()
        if ser.empty:
            out[ticker] = {k: NAN for k in ("last", "1d_%", "5d_%", "1m_%", "ytd_%", "60d_%")}
            continue

        last = float(ser.iloc[-1])
        SPLIT_GUARD = 0.75

        def ret_back(n: int, ser=ser) -> float:
            if len(ser) <= n:
                return NAN
            seg = ser.iloc[-n - 1:]
            if (seg.pct_change() < -SPLIT_GUARD).any():
                return NAN
            prev = seg.iloc[0]
            if pd.isna(prev) or prev == 0:
                return NAN
            return float((ser.iloc[-1] / prev - 1) * 100)

        year = ser.index.max().year
        jan1 = pd.Timestamp(f"{year}-01-01")
        prior = ser[ser.index < jan1]
        anchor_pos = len(prior) - 1 if len(prior) else 0
        window = ser.iloc[anchor_pos:]
        base = window.iloc[0] if len(window) else NAN
        if (len(window) and not pd.isna(base) and base != 0
                and not (window.pct_change() < -SPLIT_GUARD).any()):
            ytd = float((ser.iloc[-1] / base - 1) * 100)
        else:
            ytd = NAN

        out[ticker] = {
            "last": last,
            "1d_%": ret_back(1),
            "5d_%": ret_back(5),
            "1m_%": ret_back(21),
            "3m_%": ret_back(63),
            "6m_%": ret_back(126),
            "ytd_%": ytd,
            "60d_%": ret_back(60),
        }

    return pd.DataFrame.from_dict(out, orient="index")


def _assert_equivalent(closes: pd.DataFrame, label: str) -> None:
    old = _reference_compute_returns(closes)
    new = db.compute_returns(closes)
    assert list(new.index) == list(old.index), f"{label}: index drift"
    for c in old.columns:
        assert c in new.columns, f"{label}: missing column {c}"
        a, b = old[c].to_numpy(dtype=float), new[c].reindex(old.index).to_numpy(dtype=float)
        assert (np.isnan(a) == np.isnan(b)).all(), (
            f"{label}/{c}: NaN parity broke for "
            f"{list(old.index[np.isnan(a) != np.isnan(b)])[:10]}"
        )
        assert np.allclose(a, b, rtol=1e-9, atol=1e-9, equal_nan=True), (
            f"{label}/{c}: value drift, max |Δ| = "
            f"{np.nanmax(np.abs(a - b)) if len(a) else 0}"
        )


@pytest.fixture(scope="module")
def full_usd_closes() -> pd.DataFrame:
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    closes = db.get_close_series_usd(tuple(db.all_tickers()))
    if closes.empty:
        pytest.skip("prices_daily is empty")
    return closes


@pytest.fixture(scope="module")
def full_local_closes() -> pd.DataFrame:
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    return db.get_close_series(tuple(db.all_tickers()))


def test_usd_frame_matches_the_loop(full_usd_closes):
    assert full_usd_closes.shape[1] > 400, "expected the whole universe"
    _assert_equivalent(full_usd_closes, "close_usd")


def test_local_frame_matches_the_loop(full_local_closes):
    _assert_equivalent(full_local_closes, "close")


def test_column_order_is_stable(full_usd_closes):
    assert list(db.compute_returns(full_usd_closes).columns) == _COLS


def test_empty_input():
    assert db.compute_returns(pd.DataFrame()).empty


@pytest.mark.parametrize("case", ["all_nan", "single_row", "zero_anchor", "split_drop"])
def test_synthetic_edge_cases(case):
    idx = pd.to_datetime(["2025-12-29", "2025-12-30", "2026-01-02", "2026-01-05"])
    data = {
        "all_nan": [np.nan] * 4,
        "single_row": [np.nan, np.nan, np.nan, 10.0],
        "zero_anchor": [0.0, 0.0, 5.0, 6.0],
        "split_drop": [100.0, 100.0, 8.0, 9.0],   # -92% => guard trips
    }[case]
    closes = pd.DataFrame({"X": data, "Y": [1.0, 2.0, 3.0, 4.0]}, index=idx)
    _assert_equivalent(closes, case)


def test_no_prior_year_bar_falls_back_to_first_close_of_year():
    """PR 1's documented fallback: a ticker with no prior-year bar keeps the
    first-close-of-year anchor rather than going NaN."""
    idx = pd.to_datetime(["2026-01-02", "2026-02-02", "2026-03-02"])
    closes = pd.DataFrame({"NEW": [10.0, 12.0, 20.0]}, index=idx)
    _assert_equivalent(closes, "no_prior_year")
    assert db.compute_returns(closes).loc["NEW", "ytd_%"] == pytest.approx(100.0)


def test_ytd_anchor_is_the_prior_year_close(full_usd_closes):
    """R3 audit C1 witnesses, recomputed from the DB rather than frozen.

    The audit quoted SNDK ≈ +525.6% / MU ≈ +226.8% against the 2026-09-04
    snapshot; the committed DB has since moved on, so pinning those literals
    would pin a data vintage instead of the anchor. What must not drift is the
    ANCHOR: last close strictly before Jan 1 of the ticker's own latest year.
    """
    rets = db.compute_returns(full_usd_closes)
    for tkr in ("SNDK", "MU"):
        if tkr not in rets.index:
            pytest.skip(f"{tkr} not in the committed DB")
        ser = full_usd_closes[tkr].dropna()
        jan1 = pd.Timestamp(f"{ser.index.max().year}-01-01")
        prior = ser[ser.index < jan1]
        assert len(prior), f"{tkr} has no prior-year bar; witness is invalid"
        want = (ser.iloc[-1] / prior.iloc[-1] - 1) * 100
        assert rets.loc[tkr, "ytd_%"] == pytest.approx(want, rel=1e-12)
        # and it is materially ABOVE the buggy first-close-of-year anchor
        buggy = (ser.iloc[-1] / ser[ser.index >= jan1].iloc[0] - 1) * 100
        assert rets.loc[tkr, "ytd_%"] > buggy
