"""Pure portfolio math — NO streamlit / yfinance imports.

Isolated so it is unit-testable without a Streamlit runtime (the app's streamlit
lives in a venv; CI / local `pytest` runs on bare python). `lib.strategy`
delegates the actual return computation here, and `tests/test_strategy.py`
targets these functions directly with fixed price matrices (the math oracle
required by the /cccg ship gate).

Two equal-weight conventions, both indexed to 100 at inception:

- buy_hold_portfolio: equal $ at inception, then BUY & HOLD. Per-ticker weights
  drift with price forever; no rebalancing. (Matches the original dashboard
  semantics — the curve already shipped to clients.)

- rebalanced_portfolio: equal weight RESET every period (default monthly), with
  intra-period drift, chain-linked across periods. This is the "可复制策略"
  reproducible-strategy curve clients ask about.

The two differ whenever constituents diverge within a period: buy & hold lets
winners compound their weight; periodic rebalancing trims winners back to equal
at each reset. See test_strategy.py for the hand-verified divergence case.
"""

from __future__ import annotations

import pandas as pd


def normalize(sub: pd.DataFrame) -> pd.DataFrame:
    """Index every column to 100 at the first row (inception).

    `sub` must already be windowed to >= inception, sorted ascending, and
    forward-filled for halts. A column that is NaN at the first row stays NaN
    throughout (ticker had no price at inception → not in the inception book).
    """
    if sub.empty:
        return sub
    base = sub.iloc[0]
    return (sub / base) * 100


def buy_hold_portfolio(normed: pd.DataFrame) -> pd.Series:
    """Equal-weight-at-inception, buy & hold. = mean of indexed columns each day.

    `skipna=True`: a ticker missing at inception (NaN base → all-NaN column) is
    simply absent from the book; it does not distort surviving weights.
    """
    if normed.empty:
        return pd.Series(dtype=float)
    return normed.mean(axis=1, skipna=True)


def rebalanced_portfolio(sub: pd.DataFrame, freq: str = "M") -> pd.Series:
    """Equal-weight reset every `freq` period, intra-period drift, chain-linked.

    Algorithm (Codex ship-gate spec — chain-linked DAILY returns, weights reset
    at each period boundary; "月末收盘重置等权、下一交易日生效"):

      value = 100; weights = equal over tickers priced at inception
      for each subsequent day t:
          if t starts a new period:                 # rebalance effective today
              weights ← equal over tickers priced at the PRIOR day's close
          r_t = per-ticker simple return (close_t / close_{t-1} - 1)
          contrib_i = weights_i * (1 + r_i)          # missing r_i → flat (×1)
          value *= Σ contrib_i                        # portfolio gross return
          weights ← contrib / Σ contrib               # drift within period

    Resetting weights (NOT re-basing prices) at each boundary preserves the
    cross-boundary "gap" return — re-basing to the period's first price would
    silently discard the last-close→first-close move every period (the bug the
    oracle test `test_rebalanced_two_months_chain` guards against).

    `sub`: closes windowed to >= inception, sorted ascending, forward-filled.
    `freq`: pandas period alias — "M" monthly (default), "Q" quarterly, "W" weekly.
    Returns an index series (start=100). Empty in → empty out.
    """
    if sub.empty:
        return pd.Series(dtype=float)
    sub = sub.sort_index()
    cols = sub.columns
    periods = sub.index.to_period(freq)
    rets = sub.pct_change()  # row 0 is NaN

    def _equal_weights(price_row: pd.Series) -> pd.Series:
        active = price_row[(price_row.notna()) & (price_row != 0)].index
        w = pd.Series(0.0, index=cols)
        if len(active) > 0:
            w[active] = 1.0 / len(active)
        return w

    value = 100.0
    weights = _equal_weights(sub.iloc[0])  # inception book
    values = [value]

    for i in range(1, len(sub)):
        if periods[i] != periods[i - 1]:
            # new period → rebalance to equal weight over the prior close's book
            weights = _equal_weights(sub.iloc[i - 1])
        r = rets.iloc[i]
        # missing return (halt / not-yet-listed) → that sleeve is flat (×1)
        contrib = weights * (1 + r).where(r.notna(), 1.0)
        total = contrib.sum()
        if total <= 0 or pd.isna(total):
            total = 1.0  # degenerate day → carry flat
            values.append(value)
            continue
        value = value * float(total)
        weights = contrib / total  # drift
        values.append(value)

    return pd.Series(values, index=sub.index)
