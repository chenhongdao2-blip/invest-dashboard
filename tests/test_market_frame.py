"""`market_frame` must reproduce the loaders it replaces, exactly.

PR 2 collapses `sector_tickers` × N + `get_close_series` + `get_close_series_usd`
+ `latest_multiples` into one cached read per domain. These tests pin the new
frame against the old per-call loaders on the committed `data/snapshots.db`, so
"one query instead of sixteen" cannot quietly become "different numbers".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from lib import db  # noqa: E402

DOMAINS = ["healthcare", "ai", "etf", "software"]


@pytest.fixture(scope="module", autouse=True)
def _needs_db():
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")


@pytest.mark.parametrize("domain", DOMAINS)
def test_members_match_sector_tickers(domain):
    mf = db.market_frame(domain)
    seen = set()
    for sec in db.query(
        "SELECT DISTINCT sector FROM universe_member WHERE domain = ? ORDER BY sector",
        (domain,),
    )["sector"]:
        want = tuple(db.sector_tickers(domain, sec)["ticker"].tolist())
        assert mf.members.get(sec, ()) == want, f"{domain}/{sec}"
        seen.add(sec)
    assert set(mf.members) <= seen


@pytest.mark.parametrize("domain", DOMAINS)
def test_close_frames_match_the_old_wide_pulls(domain):
    mf = db.market_frame(domain)
    tickers = tuple(sorted({t for v in mf.members.values() for t in v}))
    if not tickers:
        pytest.skip(f"{domain} has no active members")
    pd.testing.assert_frame_equal(
        mf.close.reindex(columns=sorted(mf.close.columns)),
        db.get_close_series(tickers).reindex(columns=sorted(tickers)),
        check_freq=False,
    )
    pd.testing.assert_frame_equal(
        mf.close_usd.reindex(columns=sorted(mf.close_usd.columns)),
        db.get_close_series_usd(tickers).reindex(columns=sorted(tickers)),
        check_freq=False,
    )


@pytest.mark.parametrize("domain", DOMAINS)
def test_multiples_match_latest_multiples(domain):
    mf = db.market_frame(domain)
    tickers = tuple(sorted({t for v in mf.members.values() for t in v}))
    if not tickers:
        pytest.skip(f"{domain} has no active members")
    old = db.latest_multiples(tickers).sort_index()
    pd.testing.assert_frame_equal(mf.multiples.sort_index(), old)


def test_meta_is_not_status_filtered_and_members_are():
    """Design A.5 risk 4: delisted names must still resolve to a display name
    (`ticker_to_name` deliberately keeps them), but must not enter a scan."""
    if not db._has_column("universe_member", "status"):
        pytest.skip("status column not migrated in this DB")
    mf = db.market_frame(None)
    delisted = set(db.query(
        "SELECT DISTINCT ticker FROM universe_member WHERE status IS NOT NULL"
    )["ticker"])
    assert delisted, "expected the audit's delisted rows in the committed DB"
    assert delisted <= set(mf.meta.index), "meta dropped a delisted ticker"
    scanned = {t for v in mf.members.values() for t in v}
    assert not (delisted & scanned), "a delisted ticker leaked into members"
    assert not (delisted & set(mf.close.columns)), "a delisted ticker leaked into close"


def test_meta_names_match_ticker_to_name_for_single_row_tickers():
    """`meta` aggregates name_cn/name_en with MAX (skips NULL); `ticker_to_name`
    COALESCEs per row and then GROUP BYs on a bare column, so SQLite returns an
    ARBITRARY row of the group.

    For the 500 tickers with one universe_member row the two agree exactly. For
    the handful listed in more than one sector with inconsistent names they can
    differ — `meta` deterministically finds the non-NULL Chinese name (4151.T →
    协和麒麟) where `ticker_to_name` may return whichever row SQLite picked
    (Kyowa Kirin). That is a latent nondeterminism in `ticker_to_name`, NOT
    something this PR changes: nothing has been repointed at `meta` for names,
    so display output is untouched. Pinned here so the next person sees it.
    """
    mf = db.market_frame(None)
    multi = set(db.query(
        "SELECT ticker FROM universe_member GROUP BY ticker HAVING COUNT(*) > 1"
    )["ticker"])
    for prefer_cn in (True, False):
        want = db.ticker_to_name(prefer_cn=prefer_cn)
        a, b = ("name_cn", "name_en") if prefer_cn else ("name_en", "name_cn")
        got = mf.meta[a].fillna(mf.meta[b]).fillna(mf.meta.index.to_series())
        diverged = {t for t in mf.meta.index if got[t] != want[t]}
        assert not (diverged - multi), (
            f"prefer_cn={prefer_cn}: single-row tickers drifted: "
            f"{sorted(diverged - multi)}"
        )
        for t in diverged:  # meta's pick must still come from that ticker's rows
            rows = db.query(
                "SELECT name_cn, name_en FROM universe_member WHERE ticker = ?", (t,)
            )
            assert got[t] in set(rows["name_cn"].dropna()) | set(rows["name_en"].dropna())


def test_as_of_is_the_last_price_date():
    mf = db.market_frame(None)
    assert mf.as_of == db.query("SELECT MAX(date) AS d FROM prices_daily").iloc[0, 0]


@pytest.mark.parametrize("basis", ["usd", "local"])
def test_returns_for_slice_equals_whole_then_slice(basis):
    """The property every migrated page relies on: compute once per domain and
    slice, rather than once per sub-sector."""
    mf = db.market_frame("healthcare")
    tickers = tuple(sorted({t for v in mf.members.values() for t in v}))
    whole = db.returns_for(tickers, mf.as_of, basis)
    sub = tuple(tickers[:40])
    pd.testing.assert_frame_equal(
        db.returns_for(sub, mf.as_of, basis), whole.loc[list(sub)]
    )


def test_returns_for_matches_compute_returns_on_the_same_slice():
    mf = db.market_frame("ai")
    tickers = tuple(sorted({t for v in mf.members.values() for t in v}))
    pd.testing.assert_frame_equal(
        db.returns_for(tickers, mf.as_of, "usd"),
        db.compute_returns(db.get_close_series_usd(tickers)),
    )


# ──────────────────────────────────────────────────────────────────────────
# The three claims the page migrations actually rest on
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("domain", DOMAINS)
def test_returns_for_a_sector_equals_the_old_per_sector_pull(domain):
    """A sector slice of the DOMAIN frame has a wider date index than the old
    per-sector `get_close_series_usd` pull (dates where only other sectors traded
    are present, as all-NaN rows). `compute_returns` is invariant to those, and
    every migrated page depends on it — so assert it, do not reason about it.
    """
    mf = db.market_frame(domain)
    for sec, tickers in sorted(mf.members.items()):
        if not tickers:
            continue
        old = db.compute_returns(db.get_close_series_usd(tickers))
        new = db.returns_for(tickers, mf.as_of, "usd", domain)
        pd.testing.assert_frame_equal(new, old.reindex(new.index), obj=f"{domain}/{sec}")


@pytest.mark.parametrize("domain", DOMAINS)
def test_multiples_subset_equals_latest_multiples_subset(domain):
    mf = db.market_frame(domain)
    for sec, tickers in sorted(mf.members.items()):
        if not tickers:
            continue
        old = db.latest_multiples(tickers).sort_index()
        new = mf.multiples.loc[mf.multiples.index.intersection(tickers)].sort_index()
        # check_dtype=False: a 1-ticker `latest_multiples` pull leaves an all-None
        # column as object where the domain frame infers float64. Every consumer
        # runs it through `pd.to_numeric`.
        pd.testing.assert_frame_equal(new, old, check_dtype=False, obj=f"{domain}/{sec}")


@pytest.mark.parametrize("domain", DOMAINS)
def test_meta_rows_match_sector_tickers_except_multi_sector(domain):
    """WHY the coverage pages still call `sector_tickers` for their universe frame.

    `meta` aggregates name/region with MAX per ticker; `sector_tickers` returns the
    (domain, sector) ROW. For a ticker whose rows disagree they are different
    values — 6938.HK is 瑞博生物-B under healthcare/hk_hc_ipo and 瑞博生物 under
    _coverage and biotech, so rebuilding `1_CMSI_Coverage`'s list out of `meta`
    renames a holding. Single-sector tickers must never diverge; multi-sector ones
    may, and `meta`'s pick must still come from that ticker's own rows.
    """
    mf = db.market_frame(domain)
    cols = ["name_cn", "name_en", "region", "secondary_listing"]
    multi = set(db.query(
        "SELECT ticker FROM universe_member GROUP BY ticker HAVING COUNT(*) > 1"
    )["ticker"])
    for sec, tickers in sorted(mf.members.items()):
        if not tickers:
            continue
        old = db.sector_tickers(domain, sec).set_index("ticker")[cols]
        new = mf.meta.loc[list(tickers), cols]
        for tkr in tickers:
            for c in cols:
                if old.loc[tkr, c] == new.loc[tkr, c] or (
                        pd.isna(old.loc[tkr, c]) and pd.isna(new.loc[tkr, c])):
                    continue
                assert tkr in multi, f"{domain}/{sec} {tkr}.{c} drifted on a single-row ticker"
                vals = db.query(
                    f"SELECT {c} AS v FROM universe_member WHERE ticker = ?", (tkr,))["v"]
                assert new.loc[tkr, c] in set(vals.dropna())


def test_returns_for_matches_the_old_pull_on_arbitrary_subsets():
    """`quote_table` filters the roster by domain/region/sector, so it asks for
    subsets that are not a sector and not a domain."""
    import random

    random.seed(7)
    mf = db.market_frame(None)
    allt = list(mf.close_usd.columns)
    if not allt:
        pytest.skip("prices_daily is empty")
    for k in (1, 5, 40, 200, len(allt)):
        sub = tuple(random.sample(allt, k))
        old = db.compute_returns(db.get_close_series_usd(sub))
        new = db.returns_for(sub, mf.as_of, "usd")
        pd.testing.assert_frame_equal(new, old.reindex(new.index), obj=f"k={k}")


def test_returns_for_key_is_order_insensitive(monkeypatch):
    """The docstring's promise — "two callers with the same SET share a cache bucket"
    — has to hold at the CACHE KEY, not inside the cached body. Normalising the
    tickers after `@st.cache_data` has already hashed them means `(A, B)` and
    `(B, A)` are two buckets and the frame is recomputed; the ordering the callers
    happen to collect their tickers in is exactly what varies.
    """
    mf = db.market_frame(None)
    allt = list(mf.close_usd.columns)
    if len(allt) < 5:
        pytest.skip("prices_daily is empty")
    sub = tuple(allt[:5])

    calls: list[tuple] = []
    inner = db._returns_for_sorted
    real = getattr(inner, "__wrapped__", inner)

    def _counting(cols, as_of=None, basis="usd", domain=None):
        calls.append(cols)
        return real(cols, as_of, basis, domain)

    monkeypatch.setattr(db, "_returns_for_sorted", _counting)

    a = db.returns_for(sub, mf.as_of, "usd")
    b = db.returns_for(tuple(reversed(sub)), mf.as_of, "usd")
    c = db.returns_for(sub + sub, mf.as_of, "usd")  # duplicates collapse too

    assert len(set(calls)) == 1, f"cache key is order-sensitive: {set(calls)}"
    assert calls[0] == tuple(sorted(set(sub)))
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(a, c)


def test_returns_for_is_a_thin_uncached_wrapper():
    """`returns_for` itself must NOT be cached — a cached shell would hash the raw
    argument and reintroduce the order-sensitive key this normalisation removes."""
    assert not hasattr(db.returns_for, "clear"), "returns_for must not be @st.cache_data"
    assert hasattr(db._returns_for_sorted, "clear"), "_returns_for_sorted must be cached"
