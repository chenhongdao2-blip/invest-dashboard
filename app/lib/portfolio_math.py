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

Weighted variants (HD v2 standard build, 2026-06-11): weighted_buy_hold_portfolio
/ weighted_rebalanced_portfolio take published target weights + an idle-cash
sleeve (cash return = 0, conservative). Same dual-track semantics; the reset
book is the published weights instead of equal weight.
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


def _align_weights(
    cols: pd.Index, weights: pd.Series, cash_weight: float
) -> tuple[pd.Series, float]:
    """Align target weights to `cols` and normalize (Σstock + cash = 1).

    Tickers in `weights` ABSENT from `cols` (price fetch failed entirely)
    fold their weight into the cash sleeve — same conservative convention as
    NaN-at-inception — instead of being renormalized away (which would
    silently upweight the surviving names). Tickers in `cols` without a
    weight get 0. Normalizing by the grand total absorbs publication
    rounding (e.g. the HD v2 book publishes 88.01 + 12 cash) so the curve
    starts at exactly 100 without touching relative weights.
    """
    w_all = weights.astype(float)
    w = w_all.reindex(cols).fillna(0.0)
    absent_mass = float(w_all.sum()) - float(w.sum())
    total = float(w_all.sum()) + float(cash_weight)
    if total <= 0:
        return w * 0.0, 0.0
    return w / total, (float(cash_weight) + absent_mass) / total


def weighted_buy_hold_portfolio(
    normed: pd.DataFrame, weights: pd.Series, cash_weight: float = 0.0
) -> pd.Series:
    """Custom-weight-at-inception, buy & hold, with an idle-cash sleeve.

    value_t = Σ wᵢ · normedᵢ(t) + w_cash · 100 — initial weights set the $
    allocation at inception and then DRIFT with price (the Σw·normed form is
    the drift; no resets). Cash earns 0 (conservative book convention), i.e.
    its indexed sleeve is pinned at 100.

    `weights` are decimal fractions per ticker (0.0641 = 6.41%); together with
    `cash_weight` they are re-normalized to sum to 1 (rounding absorption).
    A ticker that is NaN at inception (all-NaN normed column, see normalize())
    was never bought — its weight FOLDS INTO CASH (flat), mirroring the
    cash-earns-0 conservatism rather than silently upweighting survivors.
    """
    if normed.empty:
        return pd.Series(dtype=float)
    w, cash = _align_weights(normed.columns, weights, cash_weight)
    dead = normed.iloc[0].isna()
    cash += float(w[dead].sum())
    w = w.where(~dead, 0.0)
    live = normed.ffill()  # defensive: post-inception gaps carry last value
    return live.mul(w, axis=1).sum(axis=1, skipna=True) + cash * 100.0


def weighted_rebalanced_portfolio(
    sub: pd.DataFrame, weights: pd.Series, cash_weight: float = 0.0,
    freq: str = "M",
) -> pd.Series:
    """Reset to TARGET weights every `freq` period; cash sleeve flat (×1 daily).

    Same chain-linked-daily-returns algorithm as rebalanced_portfolio (period
    boundary reset effective next trading day, intra-period drift, gap return
    preserved) — only the reset book differs: equal weight → published target
    weights + cash. At each reset, tickers not priced at the prior close fold
    their target weight into cash, consistent with the buy & hold convention.

    The cash sleeve participates in drift: contrib_cash = w_cash × 1.0 each
    day, so cash weight shrinks when stocks rally and cushions drawdowns —
    exactly the published 88/12 book semantics.
    """
    if sub.empty:
        return pd.Series(dtype=float)
    sub = sub.sort_index()
    cols = sub.columns
    periods = sub.index.to_period(freq)
    rets = sub.pct_change()  # row 0 is NaN
    w_target, cash_target = _align_weights(cols, weights, cash_weight)

    def _book(price_row: pd.Series) -> tuple[pd.Series, float]:
        dead = ~(price_row.notna() & (price_row != 0))
        w = w_target.where(~dead, 0.0)
        return w, cash_target + float(w_target[dead].sum())

    value = 100.0
    w, w_cash = _book(sub.iloc[0])  # inception book
    values = [value]

    for i in range(1, len(sub)):
        if periods[i] != periods[i - 1]:
            # new period → rebalance to target over the prior close's book
            w, w_cash = _book(sub.iloc[i - 1])
        r = rets.iloc[i]
        # missing return (halt) → that sleeve is flat (×1); cash always ×1
        contrib = w * (1 + r).where(r.notna(), 1.0)
        total = contrib.sum() + w_cash
        if total <= 0 or pd.isna(total):
            values.append(value)  # degenerate day → carry flat
            continue
        value = value * float(total)
        w = contrib / total  # drift
        w_cash = w_cash / total
        values.append(value)

    return pd.Series(values, index=sub.index)


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
