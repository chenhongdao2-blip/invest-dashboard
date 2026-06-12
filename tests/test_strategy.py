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
    w = pd.Series(dtype=float)
    assert pm.buy_hold_portfolio(empty).empty
    assert pm.rebalanced_portfolio(empty).empty
    assert pm.normalize(empty).empty
    assert pm.weighted_buy_hold_portfolio(empty, w).empty
    assert pm.weighted_rebalanced_portfolio(empty, w).empty


# ─────────────────────────────────────────────────────────────────────────
# weighted_buy_hold_portfolio / weighted_rebalanced_portfolio (HD v2 book)
# ─────────────────────────────────────────────────────────────────────────

def test_weighted_buy_hold_two_tickers():
    """A: 100→200 (+100%), B: 100→100 (flat); wA=0.6, wB=0.4, no cash.
    value = 0.6·200 + 0.4·100 = 160."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.6, "B": 0.4})
    port = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w)
    assert port.iloc[0] == pytest.approx(100.0)
    assert port.iloc[-1] == pytest.approx(160.0)


def test_weighted_equal_weights_zero_cash_matches_equal_weight():
    """Regression guard: wA=wB=0.5 + cash 0 must reproduce buy_hold_portfolio."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    normed = pm.normalize(sub)
    eq = pm.buy_hold_portfolio(normed)
    wt = pm.weighted_buy_hold_portfolio(normed, pd.Series({"A": 0.5, "B": 0.5}))
    assert wt.iloc[-1] == pytest.approx(eq.iloc[-1])


def test_weighted_buy_hold_cash_drag():
    """The 88/12 case: both stocks +50%, 12% idle cash earns 0.
    wA=wB=0.44; value = 0.88·150 + 0.12·100 = 132 + 12 = 144
    → +44% = +50% × 0.88 exposure. Cash drag is exactly the uninvested 12%."""
    sub = _df({"A": [100, 150], "B": [100, 150]}, ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.44, "B": 0.44})
    port = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w, cash_weight=0.12)
    assert port.iloc[0] == pytest.approx(100.0)
    assert port.iloc[-1] == pytest.approx(144.0)


def test_weighted_missing_at_inception_folds_to_cash():
    """B has no price at inception → never bought; its 0.38 folds into cash.
    cash = 0.12 + 0.38 = 0.50; A: 100→120.
    value = 0.5·120 + 0.5·100 = 110 (NOT 0.5·120/0.5 = 120: survivors are
    not upweighted)."""
    sub = _df({"A": [100, 120], "B": [float("nan"), 50]},
              ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.5, "B": 0.38})
    port = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w, cash_weight=0.12)
    assert port.iloc[-1] == pytest.approx(110.0)


def test_weighted_rebalanced_single_period_equals_weighted_bh():
    """All rows in ONE month → no reset → must equal weighted buy & hold.
    A:100→200, B:100→100, wA=wB=0.44, cash 0.12:
    day2 contribs A=0.44·2=0.88, B=0.44·1=0.44, cash=0.12 → total 1.44
    → value 144 = weighted BH (0.88+44+12... = 0.44·200+0.44·100+12)."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.44, "B": 0.44})
    bh = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w, cash_weight=0.12)
    rb = pm.weighted_rebalanced_portfolio(sub, w, cash_weight=0.12, freq="M")
    assert rb.iloc[-1] == pytest.approx(bh.iloc[-1])
    assert rb.iloc[-1] == pytest.approx(144.0)


def test_weighted_rebalanced_two_months_resets_to_target():
    """Chain across months, reset to TARGET (not equal) weights.

    Dates: Jan5 (inception), Jan30, Feb27. wA=0.6, wB=0.4, no cash.
      A: 100 → 150 → 180   (+50%, then +20%)
      B: 100 →  50 →  40   (−50%, then −20%)

    BUY & HOLD: 0.6·180 + 0.4·40 = 108 + 16 = 124.

    MONTHLY REBALANCE:
      Jan30: contrib A=0.6·1.5=0.90, B=0.4·0.5=0.20 → total 1.10 → value 110
             (drifted w: A 0.8182 / B 0.1818)
      Feb27 (new month → reset to 0.6/0.4 on Jan30 close):
             r A=180/150=1.2, B=40/50=0.8
             contrib A=0.6·1.2=0.72, B=0.4·0.8=0.32 → total 1.04
             → value 110·1.04 = 114.4
    Buy & hold (124) > rebalanced (114.4): reset re-funds the loser."""
    sub = _df(
        {"A": [100, 150, 180], "B": [100, 50, 40]},
        ["2026-01-05", "2026-01-30", "2026-02-27"],
    )
    w = pd.Series({"A": 0.6, "B": 0.4})
    bh = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w)
    rb = pm.weighted_rebalanced_portfolio(sub, w, freq="M")
    assert bh.iloc[-1] == pytest.approx(124.0)
    assert rb.iloc[-1] == pytest.approx(114.4)
    assert rb.iloc[0] == pytest.approx(100.0)
    assert not rb.isna().any()


def test_weighted_absent_ticker_folds_to_cash():
    """C never made it into the price frame at all (fetch failed) →
    its 0.3 folds into cash, survivors are NOT upweighted.
    A 100→200 (w 0.5), B 100→100 (w 0.2), C absent (w 0.3), cash 0:
    value = 0.5·200 + 0.2·100 + 0.3·100(cash flat) = 100+20+30 = 150."""
    sub = _df({"A": [100, 200], "B": [100, 100]}, ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.5, "B": 0.2, "C": 0.3})
    bh = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w)
    assert bh.iloc[0] == pytest.approx(100.0)
    assert bh.iloc[-1] == pytest.approx(150.0)
    rb = pm.weighted_rebalanced_portfolio(sub, w, freq="M")
    assert rb.iloc[-1] == pytest.approx(150.0)


def test_weighted_rounding_absorbed_starts_at_100():
    """Published HD v2 book: stock weights sum to 88.01% + 12 cash = 100.01.
    _align_weights normalizes by the grand total so the curve starts at
    exactly 100 (publication rounding must not leak into the index base)."""
    sub = _df({"A": [100, 110], "B": [100, 110]}, ["2026-01-05", "2026-01-30"])
    w = pd.Series({"A": 0.4401, "B": 0.4400})  # 88.01% in decimals
    port = pm.weighted_buy_hold_portfolio(pm.normalize(sub), w, cash_weight=0.12)
    assert port.iloc[0] == pytest.approx(100.0)
    rb = pm.weighted_rebalanced_portfolio(sub, w, cash_weight=0.12, freq="M")
    assert rb.iloc[0] == pytest.approx(100.0)
