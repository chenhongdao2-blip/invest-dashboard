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

from datetime import date  # noqa: E402

from lib import db  # noqa: E402
from lib import portfolio_math as pm  # noqa: E402
from lib import strategy as strat  # noqa: E402


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


# ══════════════════════════════════════════════════════════════════════════
# PR 2 — Strategy Picks reads the snapshot before it reaches for the network
# ══════════════════════════════════════════════════════════════════════════
def test_picks_closes_db_covers_the_biotech_books_and_not_the_hd_ones():
    """Design A.3's measured coverage, as an assertion rather than a note.

    The three HD books are 0/74 on purpose — onboarding those symbols to
    `universe_member` is a universe decision (see the TODO in
    4_Strategy_Picks.py), so their yfinance path must stay reachable.
    """
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    biotech, hd = 0, 0
    for sid, cfg in strat.STRATEGIES.items():
        picks = cfg["loader"]()
        if picks.empty or "yf_sym" not in picks.columns:
            continue
        syms = tuple(sorted(set(picks["yf_sym"].dropna())))
        got = strat.picks_closes_db(syms, cfg["pick_date"])
        n = 0 if got.empty else len(got.columns)
        if sid.endswith("biotech"):
            assert n >= len(syms) * 0.9, f"{sid}: only {n}/{len(syms)} in prices_daily"
            biotech += 1
        else:
            assert n == 0, f"{sid}: {n} HD symbols unexpectedly in prices_daily"
            hd += 1
    assert biotech == 3 and hd == 3


def test_picks_closes_db_does_not_read_benchmarks_daily():
    """`benchmarks_daily.close` IS adjusted (`fetch_benchmarks` uses
    `auto_adjust=True`) — the earlier "RAW close" reasoning was wrong. The decision
    to keep benchmarks on the live fetch stands anyway: `3466.HK`, the HD books'
    primary benchmark, has no rows in that table, and only a trailing 200-day window
    is rewritten each run, so older rows keep a stale back-adjustment factor."""
    import inspect

    src = inspect.getsource(strat.picks_closes_db)
    assert "benchmarks_daily" not in src.split('"""')[2], src
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    # A symbol that lives ONLY in benchmarks_daily must not be served at all.
    # `XBI` is also a `prices_daily` universe member, where `adj_close` IS the
    # total-return series, so serving it from THERE is correct and expected.
    only_bench = db.query(
        "SELECT DISTINCT ticker FROM benchmarks_daily WHERE ticker NOT IN "
        "(SELECT DISTINCT ticker FROM prices_daily) LIMIT 5"
    )["ticker"].tolist()
    assert only_bench, "expected ^HSI-style benchmark-only symbols in the DB"
    got = strat.picks_closes_db(tuple(only_bench), "2026-01-01")
    assert got.empty or not set(only_bench) & set(got.columns)


def test_fetch_picks_closes_serves_covered_symbols_without_yfinance(monkeypatch):
    """The whole point: a fully covered, fresh book must not touch the network."""
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    cfg = strat.STRATEGIES["v6_biotech"]
    syms = tuple(sorted(set(cfg["loader"]()["yf_sym"].dropna())))
    have = strat.picks_closes_db(syms, cfg["pick_date"])
    if have.empty or len(have.columns) < len(syms):
        pytest.skip("snapshot does not fully cover v6")
    if have.index.max() < pd.Timestamp(date.today()) - pd.Timedelta(days=strat._DB_STALE_DAYS):
        pytest.skip("committed snapshot is stale; the live path is correct there")

    called: list = []

    def _boom(*a, **kw):
        called.append(a)
        raise AssertionError("yfinance was called for a fully covered book")

    monkeypatch.setattr(strat.yf, "download", _boom)
    strat.fetch_picks_closes.clear()
    got = strat.fetch_picks_closes(syms, cfg["pick_date"], 0.0)
    assert not called
    assert set(syms) <= set(got.columns)
    cols = list(have.columns)
    pd.testing.assert_frame_equal(got[cols], have[cols], check_names=False)


def test_fetch_picks_closes_falls_back_when_the_snapshot_is_stale(monkeypatch):
    monkeypatch.setattr(strat, "_DB_STALE_DAYS", -10_000)  # force "stale"
    strat.fetch_picks_closes.clear()
    seen: list = []

    def _fake(syms, **kw):
        seen.append(tuple(syms))
        raise RuntimeError("stop here — reaching the network is the assertion")

    monkeypatch.setattr(strat.yf, "download", _fake)
    monkeypatch.setattr(strat.st, "warning", lambda *a, **k: None)
    strat.fetch_picks_closes(("AAPL", "MSFT"), "2026-01-01", 0.0)
    assert seen and set(seen[0]) == {"AAPL", "MSFT"}


def test_strategy_page_uses_a_lazy_selector_not_st_tabs():
    """`st.tabs` executes EVERY tab body on every run (audit §5's 9.46 s)."""
    src = (Path(__file__).resolve().parent.parent
           / "app" / "pages" / "4_Strategy_Picks.py").read_text()
    assert "st.segmented_control(" in src
    assert "st.tabs(" not in src
    assert "DECISION 2026-09-07" in src, "the HD universe decision must stay documented"


def test_fetch_picks_closes_never_extends_past_the_snapshot(monkeypatch):
    """`_apply_delisted_overrides` synthesizes a business-day index out to TODAY, and
    it runs AFTER the `merged.index <= db_last` truncation — so a delisted pick
    reintroduced rows beyond the snapshot's own last bar (measured on v4: 2 rows
    where only FOLD is non-NaN). Those rows carry one synthetic name against NaN for
    every real pick, which is precisely the mixed-vintage tail the truncation exists
    to prevent, and the page still renders `db_last` as its as-of.
    """
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    cfg = strat.STRATEGIES["v4_biotech"]
    syms = tuple(sorted(set(cfg["loader"]()["yf_sym"].dropna())))
    overrides = strat._delisted_overrides(strat._delisted_mtime())
    if not set(syms) & set(overrides):
        pytest.skip("v4 has no delisted overrides; nothing to over-extend")

    have = strat.picks_closes_db(syms, cfg["pick_date"])
    if have.empty or len(have.columns) < len(syms):
        pytest.skip("snapshot does not fully cover v4")
    db_last = have.dropna(how="all").index.max()

    def _boom(*a, **kw):
        raise AssertionError("yfinance was called for a fully covered book")

    monkeypatch.setattr(strat.yf, "download", _boom)
    strat.fetch_picks_closes.clear()
    got = strat.fetch_picks_closes(syms, cfg["pick_date"], strat._delisted_mtime())

    assert got.index.max() <= db_last, (
        f"{(got.index > db_last).sum()} rows past the snapshot's last bar "
        f"({db_last.date()}): {list(got.index[got.index > db_last])}"
    )
    # the override itself must survive the clamp — this is a truncation, not a drop
    sym = next(iter(set(syms) & set(overrides)))
    assert sym in got.columns and got[sym].notna().any()


# Symbols whose DB `adj_close` is allowed to differ from `close` at all. Measured
# 2026-09-07 over every pick + benchmark symbol `picks_closes_db` can serve:
# 75 of 77 are ratio ≡ 1.0, and only these two carry a distribution.
#   REGN  0.396%   XBI  0.466%   (max-vs-min of adj_close/close across the series)
_ADJ_DRIFT_ALLOWLIST = {"REGN", "XBI"}
_ADJ_DRIFT_MAX_PCT = 1.0


def test_db_sourced_picks_have_no_adjustment_drift():
    """`jobs/fetch_eod.py` writes `adj_close` from an `auto_adjust=False` pull over a
    ~5-day rolling window, so every row's back-adjustment factor is FROZEN at write
    time. A distribution re-adjusts the live yfinance series but not the rows already
    in the DB, so for a distributing name the old end of `picks_closes_db` under-
    adjusts and the book understates total return.

    That defect is currently inert only because the pick universe happens to be
    almost entirely non-distributing. This test converts that accident into a
    tripwire: a symbol outside the allowlist must be EXACTLY flat, so onboarding a
    distributing name (the HD books' 74 symbols, say) fails here. HD was decided
    AGAINST onboarding on 2026-09-07 (see the DECISION block in
    `4_Strategy_Picks.py`); this tripwire now guards a reversal of that.
    """
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")
    syms: set[str] = set()
    for cfg in strat.STRATEGIES.values():
        picks = cfg["loader"]()
        if not picks.empty and "yf_sym" in picks.columns:
            syms |= set(picks["yf_sym"].dropna())
        syms |= {b for b in (cfg.get("benchmark"), cfg.get("benchmark2")) if b}
    assert syms

    ph = ",".join("?" * len(syms))
    got = db.query(
        f"SELECT ticker, MIN(adj_close / close) AS lo, MAX(adj_close / close) AS hi "
        f"FROM prices_daily WHERE ticker IN ({ph}) "
        f"AND close IS NOT NULL AND close != 0 AND adj_close IS NOT NULL "
        f"GROUP BY ticker", tuple(sorted(syms)))
    if got.empty:
        pytest.skip("no DB-sourced pick symbols")
    got["drift_pct"] = (got["hi"] - got["lo"]) / got["lo"] * 100

    drifting = got[got["drift_pct"] > 0]
    unexpected = drifting[~drifting["ticker"].isin(_ADJ_DRIFT_ALLOWLIST)]
    assert unexpected.empty, (
        "adj_close is frozen per row at write time, so a distributing symbol makes "
        "the DB series understate total return. New drifting symbols:\n"
        + unexpected[["ticker", "drift_pct"]].to_string(index=False)
        + "\nEither re-adjust prices_daily.adj_close for the full history on every "
          "run, compute TR from a dividends table, or allowlist it here with the "
          "measured magnitude and a reason."
    )
    over = drifting[drifting["drift_pct"] > _ADJ_DRIFT_MAX_PCT]
    assert over.empty, (
        f"allowlisted symbols drifted past {_ADJ_DRIFT_MAX_PCT}%:\n"
        + over[["ticker", "drift_pct"]].to_string(index=False))
