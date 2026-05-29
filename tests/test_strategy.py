"""Math oracle for portfolio curves (/cccg ship gate #4).

Targets lib.portfolio_math directly with FIXED price matrices — no streamlit,
no yfinance, no live data. Run: `pytest tests/ -q` from repo root.

Every expected number below is hand-computed in the docstring of its test so a
reviewer can verify the curve math without trusting the implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# app/ is on sys.path when Streamlit runs streamlit_app.py; replicate for tests.
APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from lib import portfolio_math as pm  # noqa: E402


def _df(rows: dict[str, list[float]], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, index=pd.to_datetime(dates))


# ─────────────────────────────────────────────────────────────────────────
# buy_hold_portfolio
# ─────────────────────────────────────────────────────────────────────────

def test_buy_hold_two_tickers_basic():
    """A: 100→200 (+100%), B: 100→100 (flat).
    normed A=[100,200], B=[100,100]; equal-weight mean=[100,150]. Last=150."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    normed = pm.normalize(sub)
    port = pm.buy_hold_portfolio(normed)
    assert port.iloc[0] == pytest.approx(100.0)
    assert port.iloc[-1] == pytest.approx(150.0)


def test_buy_hold_missing_at_inception_excluded():
    """B is NaN at inception → not in the book; portfolio = A alone.
    A: 100→120 → normed [100,120]; mean over {A} = [100,120]."""
    sub = _df({"A": [100, 120], "B": [float("nan"), 50]},
              ["2026-01-05", "2026-01-30"])
    normed = pm.normalize(sub)
    port = pm.buy_hold_portfolio(normed)
    assert port.iloc[-1] == pytest.approx(120.0)


# ─────────────────────────────────────────────────────────────────────────
# rebalanced_portfolio
# ─────────────────────────────────────────────────────────────────────────

def test_rebalanced_single_period_equals_buy_hold():
    """All rows in ONE month → no reset happens → must equal buy & hold.
    A:100→200, B:100→100 within Jan → both =150 at end."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    bh = pm.buy_hold_portfolio(pm.normalize(sub))
    rb = pm.rebalanced_portfolio(sub, freq="M")
    assert rb.iloc[-1] == pytest.approx(bh.iloc[-1])
    assert rb.iloc[-1] == pytest.approx(150.0)


def test_rebalanced_vs_buyhold_divergence():
    """Hand-verified divergence — the whole point of the dual curve.

    Dates: Jan5 (inception), Jan30 (end month1), Feb27 (end month2).
      A: 100 → 150 → 180
      B: 100 →  50 →  40

    BUY & HOLD (no reset, anchor=Jan5):
      normed A = [100, 150, 180]; B = [100, 50, 40]
      mean    = [100, 100, 110]            → last = 110.0

    MONTHLY REBALANCE (reset equal weight at each month's first row):
      Jan segment (Jan5 base A=100,B=100):
        seg_norm A=[1.0,1.5], B=[1.0,0.5]; mean=[1.0,1.0]; value=100*[1,1]
        → running = 100  (winners trimmed back to equal at month end view)
      Feb segment (Feb27 only; base = Feb27 row itself A=180,B=40):
        single row → seg_norm=[1.0,1.0]; mean=1.0; value=100
        → last = 100.0
    So buy&hold (110) > rebalanced (100): holding the winner (A) beat trimming it.
    """
    sub = _df(
        {"A": [100, 150, 180], "B": [100, 50, 40]},
        ["2026-01-05", "2026-01-30", "2026-02-27"],
    )
    bh = pm.buy_hold_portfolio(pm.normalize(sub))
    rb = pm.rebalanced_portfolio(sub, freq="M")
    assert bh.iloc[-1] == pytest.approx(110.0)
    assert rb.iloc[-1] == pytest.approx(100.0)
    # continuity: series starts at 100, no NaN
    assert rb.iloc[0] == pytest.approx(100.0)
    assert not rb.isna().any()


def test_rebalanced_two_months_chain():
    """Chain-link across months with a clean reset.
    Jan: A,B both 100→110 (+10%). Feb: both 110→121 (+10%).
      Jan seg: mean=[1.0,1.1] → value [100,110]; running=110
      Feb seg base=110: [1.0,1.1] → value [110,121]
    Last = 121 (two +10% months compounded)."""
    sub = _df(
        {"A": [100, 110, 121], "B": [100, 110, 121]},
        ["2026-01-10", "2026-01-30", "2026-02-26"],
    )
    rb = pm.rebalanced_portfolio(sub, freq="M")
    assert rb.iloc[-1] == pytest.approx(121.0)


def test_empty_in_empty_out():
    empty = pd.DataFrame()
    assert pm.buy_hold_portfolio(empty).empty
    assert pm.rebalanced_portfolio(empty).empty
    assert pm.normalize(empty).empty
