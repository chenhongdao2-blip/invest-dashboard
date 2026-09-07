"""Regression tests for the Round-3 full-chain audit (docs/audits/round3/).

Each test below is a RED test written before its fix — it pins one of the
Critical / High findings so the bug cannot silently come back.

No network. Real data comes from the committed `data/snapshots.db` (read-only);
everything else is a small synthetic frame.

Run: `pytest tests/test_audit_r3.py -q` from the repo root.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pandas as pd
import pytest

# app/ is on sys.path when Streamlit runs the app; replicate for tests.
_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

_REPO = Path(__file__).resolve().parent.parent


def _closes(rows: dict[str, list[float]], dates: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, index=pd.to_datetime(dates))


# ══════════════════════════════════════════════════════════════════════════
# C1 — YTD anchors on the LAST close of the PRIOR year, not the first of this
# ══════════════════════════════════════════════════════════════════════════
def test_c1_ytd_anchors_on_prior_year_last_close():
    """Dec-31 close 100 → Jan-2 close 110 → last 121 ⇒ YTD = +21.0%, not +10.0%.

    The buggy anchor (first close *of the year*) uses 110 and reports
    (121/110 − 1) = +10.0%, silently dropping the Jan-1 gap.
    """
    from lib import db

    closes = _closes(
        {"X": [100.0, 110.0, 121.0]},
        ["2025-12-31", "2026-01-02", "2026-03-02"],
    )
    out = db.compute_returns(closes)
    assert out.loc["X", "ytd_%"] == pytest.approx(21.0)


def test_c1_ytd_falls_back_to_first_close_of_year_without_prior_data():
    """No prior-year bar ⇒ keep the old behaviour (first close of the year)."""
    from lib import db

    closes = _closes(
        {"X": [110.0, 121.0]},
        ["2026-01-02", "2026-03-02"],
    )
    out = db.compute_returns(closes)
    assert out.loc["X", "ytd_%"] == pytest.approx(10.0)


def test_c1_ytd_split_guard_still_suppresses():
    """SPLIT_GUARD must survive the anchor change: a −80% one-day drop ⇒ NaN."""
    from lib import db

    closes = _closes(
        {"X": [100.0, 100.0, 18.0, 19.0]},
        ["2025-12-31", "2026-01-02", "2026-01-03", "2026-03-02"],
    )
    out = db.compute_returns(closes)
    assert pd.isna(out.loc["X", "ytd_%"])


def test_c1_benchmarks_ytd_uses_prior_year_close():
    """lib.benchmarks._returns_row has the same Jan-1 anchor bug."""
    from datetime import date

    from lib import benchmarks

    ser = pd.Series(
        [100.0, 110.0, 121.0],
        index=pd.to_datetime(["2025-12-31", "2026-01-02", "2026-03-02"]),
    )
    row = benchmarks._returns_row("XLV", ser, date(2026, 3, 2))
    assert row["ytd_%"] == pytest.approx(21.0)


def test_c1_strategy_picks_fetch_starts_before_jan1():
    """4_Strategy_Picks must fetch far enough back that the prior-year close exists.

    A `f"{year}-01-01"` start makes the prior-year anchor unavailable by
    construction, so the page would keep showing the buggy YTD even after the
    db.py fix. Guard the source text.
    """
    lines = (_REPO / "app" / "pages" / "4_Strategy_Picks.py").read_text(
        encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(lines) if "-01-01" in ln and not ln.lstrip().startswith("#")]
    assert hits, "no year-start expression found in 4_Strategy_Picks.py — grep drifted"
    for i in hits:
        assert "Timedelta" in lines[i], (
            "Strategy Picks still anchors its fetch window ON Jan 1 — the "
            "prior-year close the YTD anchor needs is outside the fetched range:\n"
            + lines[i]
        )


# ══════════════════════════════════════════════════════════════════════════
# C2 — SEC annual selection by duration span, deterministic ranking
# ══════════════════════════════════════════════════════════════════════════
def test_c2_agio_fy2014_revenues_is_the_twelve_month_value():
    """Real-DB oracle: AGIO 10-K tags the Q4 3-month row as fp='FY' too.

    `data/snapshots.db` holds three rows ending 2014-12-31:
      2014-01-01→2014-12-31 (365d) = 65,358,000   ← the real FY
      2014-10-01→2014-12-31  (91d) = 14,636,000   filed 2015-02-24, fp=FY
      2014-10-01→2014-12-31  (91d) = 14,636,000   filed 2016-02-26, fp=FY
    An `fp == "FY"` filter lets the 91-day rows through, and the later `filed`
    makes one of them win → a 4.5× understatement.
    """
    from lib import sec_facts as sf

    df = sf._facts("AGIO", "us-gaap", "Revenues", "USD")
    if df.empty:
        pytest.skip("AGIO Revenues facts not present in data/snapshots.db")
    ann = sf._rank(sf._filter_period(df, "duration", "annual"))
    row = ann[ann["end_date"].astype(str) == "2014-12-31"]
    assert not row.empty, "FY2014 dropped entirely by the annual filter"
    assert float(row.iloc[0]["value"]) == pytest.approx(65_358_000.0)


def test_c2_annual_filter_rejects_quarter_span_labelled_fy():
    """Synthetic: a 91-day row with fp='FY' must not survive the annual filter."""
    from lib import sec_facts as sf

    df = pd.DataFrame(
        {
            "start_date": ["2014-01-01", "2014-10-01"],
            "end_date": ["2014-12-31", "2014-12-31"],
            "fp": ["FY", "FY"],
            "form": ["10-K", "10-K"],
            "filed": ["2015-02-24", "2016-02-26"],
            "value": [65_358_000.0, 14_636_000.0],
        }
    )
    out = sf._filter_period(df, "duration", "annual")
    assert list(out["value"]) == [65_358_000.0]


def test_c2_annual_filter_rejects_multi_year_span():
    """A 730-day cumulative row is not an annual period either."""
    from lib import sec_facts as sf

    df = pd.DataFrame(
        {
            "start_date": ["2013-01-01", "2014-01-01"],
            "end_date": ["2014-12-31", "2014-12-31"],
            "fp": ["FY", "FY"],
            "form": ["10-K", "10-K"],
            "filed": ["2015-02-24", "2015-02-24"],
            "value": [999.0, 65_358_000.0],
        }
    )
    out = sf._filter_period(df, "duration", "annual")
    assert list(out["value"]) == [65_358_000.0]


def test_c2_rank_breaks_end_filed_ties_by_longest_span():
    """Two rows, same (end_date, filed), spans 91 and 365 ⇒ the 365 must win.

    Sorting on (end_date, filed) alone leaves the winner to quicksort's
    unstable pivot choice — non-deterministic across pandas versions/row order.
    """
    from lib import sec_facts as sf

    df = pd.DataFrame(
        {
            "start_date": ["2014-10-01", "2014-01-01"],
            "end_date": ["2014-12-31", "2014-12-31"],
            "fp": ["FY", "FY"],
            "form": ["10-K", "10-K"],
            "filed": ["2015-02-24", "2015-02-24"],
            "value": [14_636_000.0, 65_358_000.0],
        }
    )
    assert float(sf._rank(df).iloc[0]["value"]) == pytest.approx(65_358_000.0)
    # order-independence: reversing the input must not change the winner
    rev = df.iloc[::-1].reset_index(drop=True)
    assert float(sf._rank(rev).iloc[0]["value"]) == pytest.approx(65_358_000.0)


def test_c2_concept_timeseries_dedupe_prefers_longest_span():
    """`drop_duplicates(subset=['end_date'])` has the same tie determinism issue."""
    from lib import sec_facts as sf

    df = pd.DataFrame(
        {
            "start_date": ["2014-10-01", "2014-01-01"],
            "end_date": ["2014-12-31", "2014-12-31"],
            "fp": ["FY", "FY"],
            "form": ["10-K", "10-K"],
            "filed": ["2015-02-24", "2015-02-24"],
            "value": [14_636_000.0, 65_358_000.0],
        }
    )
    out = sf._dedupe_by_end_date(df)
    assert len(out) == 1
    assert float(out.iloc[0]["value"]) == pytest.approx(65_358_000.0)


# ══════════════════════════════════════════════════════════════════════════
# C3 / H2 — Streamlit cache keys must include the inputs they depend on
# ══════════════════════════════════════════════════════════════════════════
def test_c3_sector_pe_percentile_reacts_to_sector_map():
    """Same multiples, different sector partition ⇒ different percentiles.

    The buggy signature `(_mults_df, _sector_map, pe_col)` prefixes both real
    inputs with `_`, which Streamlit *excludes* from the cache key — only
    `pe_col` (2 distinct values) is hashed, so switching sectors returns the
    previous sector's percentiles for the whole 300 s TTL.
    """
    from lib import valuation

    mults = pd.DataFrame({"trailing_pe": [10.0, 20.0, 30.0, 40.0]},
                         index=["A", "B", "C", "D"])
    map_one = {"A": ["s1"], "B": ["s1"], "C": ["s1"], "D": ["s1"]}
    map_two = {"A": ["s1"], "B": ["s1"], "C": ["s2"], "D": ["s2"]}

    pct1, _, _ = valuation.sector_pe_percentile(mults, map_one, "trailing_pe")
    pct2, _, _ = valuation.sector_pe_percentile(mults, map_two, "trailing_pe")
    assert not pct1.equals(pct2), (
        "sector_pe_percentile returned identical percentiles for two different "
        "sector partitions — the cache key ignores _sector_map"
    )
    # D is the most expensive name overall (100th pct) but only the dearer of
    # two in s2 (also 100) — C moves from 66.7 to 0.0 between the partitions.
    assert pct1["C"] != pct2["C"]


def test_c3_pages_import_the_single_percentile_definition():
    """Both valuation pages must use lib.valuation, not a local copy."""
    for page in ("5_Valuation_Scanner.py", "a4_ai_valuation.py"):
        src = (_REPO / "app" / "pages" / page).read_text(encoding="utf-8")
        assert "def sector_pe_percentile(" not in src, (
            f"{page} still defines its own sector_pe_percentile — "
            "two copies drift apart (audit §6 duplication)"
        )


@pytest.mark.parametrize(
    "module,func",
    [
        ("lib.earnings_cal", "load_calendar"),
        ("lib.earnings_cal", "local_transcript"),
        ("lib.strategy", "_delisted_overrides"),
        ("lib.strategy", "fetch_picks_closes"),
    ],
)
def test_h2_cache_invalidation_args_are_not_underscore_prefixed(module, func):
    """A `_`-prefixed arg is excluded from the Streamlit cache key.

    These functions pass an mtime/signature purely to bust the cache — naming it
    `_mtime` / `_sig` makes the invalidation a no-op. See lib/hc_overview.py:66
    for the correct idiom in this repo.
    """
    import importlib

    mod = importlib.import_module(module)
    fn = getattr(mod, func)
    fn = getattr(fn, "__wrapped__", fn)
    bad = [p for p in inspect.signature(fn).parameters if p.startswith("_")]
    assert not bad, (
        f"{module}.{func} has cache-excluded parameter(s) {bad}; drop the "
        "leading underscore so the value participates in the cache key"
    )


# ══════════════════════════════════════════════════════════════════════════
# H3 / M — delisted names must not leak into the quote table or the fetch job
# ══════════════════════════════════════════════════════════════════════════
def test_h3_quote_roster_excludes_delisted():
    """`_ticker_roster()` ⊆ `db.all_tickers()` (which filters status IS NULL)."""
    from lib import db, quote_table

    if not db._has_column("universe_member", "status"):
        pytest.skip("universe_member.status not migrated in this DB")
    roster = set(quote_table._ticker_roster()["ticker"])
    active = set(db.all_tickers())
    assert roster, "roster empty — test would pass vacuously"
    assert roster <= active, f"delisted tickers in quote table: {sorted(roster - active)}"


def test_m_fetch_eod_universe_query_filters_status():
    """jobs/fetch_eod.py must not spend its retry budget on dead tickers."""
    import sqlite3

    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    conn = sqlite3.connect(f"file:{_REPO / 'data' / 'snapshots.db'}?mode=ro", uri=True)
    try:
        has_status = "status" in {
            r[1] for r in conn.execute("PRAGMA table_info(universe_member)")
        }
        if not has_status:
            pytest.skip("universe_member.status not migrated in this DB")
        got = set(fetch_eod.get_tickers(conn))
        active = {
            r[0] for r in conn.execute(
                "SELECT DISTINCT ticker FROM universe_member WHERE status IS NULL"
            )
        }
        assert got, "get_tickers returned nothing — test would pass vacuously"
        assert got == active
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════
# H12 — Top movers must honour the UI language
# ══════════════════════════════════════════════════════════════════════════
def test_h12_top_movers_accepts_prefer_cn():
    """`top_movers` must thread the language through to ticker_to_name.

    `ticker_to_name()` defaults to Chinese, so EN mode showed Chinese names on
    every home-page movers table.
    """
    from lib import db

    sig = inspect.signature(getattr(db.top_movers, "__wrapped__", db.top_movers))
    assert "prefer_cn" in sig.parameters
    assert sig.parameters["prefer_cn"].default is True  # preserve current CN default


def test_h12_home_passes_language_to_top_movers():
    """home.py must not call top_movers with the language hard-wired."""
    src = (_REPO / "app" / "home.py").read_text(encoding="utf-8")
    calls = [ln for ln in src.splitlines() if "top_movers(" in ln]
    assert calls, "no top_movers call sites found — grep drifted"
    for ln in calls:
        assert "prefer_cn" in ln, f"top_movers call without prefer_cn: {ln.strip()}"


# ══════════════════════════════════════════════════════════════════════════
# C5 — multiples rows must carry a real price
# ══════════════════════════════════════════════════════════════════════════
def test_c5_info_to_multiple_row_returns_none_without_price():
    """A payload with no regularMarketPrice/currentPrice is unusable.

    The docstring promised `| None` but the function always returned a tuple,
    so `if row:` at the call site was tautologically true and a priceless
    `.info` blob still became a `multiples_daily` row.
    """
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    info = {"currency": "USD", "marketCap": 1_000_000.0, "trailingPE": 12.0}
    assert fetch_eod.info_to_multiple_row("X", info, "2026-09-05", {"USD": 1.0}) is None


def test_c5_info_to_multiple_row_keeps_valid_price():
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    info = {"currency": "USD", "marketCap": 1_000_000.0, "regularMarketPrice": 12.5}
    row = fetch_eod.info_to_multiple_row("X", info, "2026-09-05", {"USD": 1.0})
    assert row is not None
    assert row[0] == "X" and row[1] == "2026-09-05"
    assert row[14] == pytest.approx(12.5)  # last_price (local ccy)


def test_c5_info_price_diverging_from_bar_close_drops_the_row():
    """108320.KQ shipped a frozen `.info` price 2.06× the same-day bar close.

    Review fixup: the first cut kept the row and overwrote `last_price` with the
    bar close, leaving market_cap_usd / trailing_pe / pb on the `.info` basis —
    a row whose price says 37,800 while its market cap and P/E still imply
    78,000. That is a WORSE artifact than either input, because it looks
    internally sourced. A gross divergence means the payload and the tape
    disagree about what this instrument is worth; neither side can be trusted to
    key the other's multiples, so the whole row goes (same as the no-price
    branch) and the ticker counts as a failure.
    """
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    info = {"currency": "KRW", "marketCap": 1e12, "regularMarketPrice": 78_000.0}
    row = fetch_eod.info_to_multiple_row(
        "108320.KQ", info, "2026-09-05", {"KRW": 0.00072},
        bar_close=37_800.0, bar_date="2026-09-04",
    )
    assert row is None


def test_c5_divergence_never_partially_overwrites():
    """No output shape may mix a bar price with `.info` mcap/PE.

    The reviewer's proof: price 50 stored while market_cap implies 110 and
    trailing_pe implies 110. Whatever the drop policy, this combination must be
    unreachable — assert on the whole row, not just on `last_price`.
    """
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    info = {"currency": "USD", "marketCap": 110e6, "trailingPE": 11.0,
            "priceToBook": 5.0, "regularMarketPrice": 110.0}
    row = fetch_eod.info_to_multiple_row(
        "X", info, "2026-09-05", {"USD": 1.0}, bar_close=50.0, bar_date="2026-09-04"
    )
    if row is not None:                      # a future policy may keep the row —
        assert row[14] == pytest.approx(110.0)   # …but then it must not have
        assert row[2] == pytest.approx(110e6)    # rewritten the price alone.


def test_c5_info_price_close_to_bar_close_is_kept():
    """A small divergence (normal intraday/stale drift) must not be rewritten."""
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415

    info = {"currency": "USD", "marketCap": 1e9, "regularMarketPrice": 101.0}
    row = fetch_eod.info_to_multiple_row(
        "X", info, "2026-09-05", {"USD": 1.0}, bar_close=100.0
    )
    assert row[14] == pytest.approx(101.0)


# ══════════════════════════════════════════════════════════════════════════
# C5 review fixup — a dropped multiples row must be ACCOUNTED FOR
#
# The first cut of the C5 fix made `info_to_multiple_row` able to return None,
# but the caller only ever incremented `ok` on a truthy row. A ticker whose
# payload was dropped fell through both counters: not ok, not failed. A
# metadata-only yfinance outage (every `.info` fetch succeeds, none carries a
# price) therefore produced fail_rate=0.0 and total_mult=0 — and the workflow
# stamped `eod_prices ok` over a day with zero valuation rows.
# ══════════════════════════════════════════════════════════════════════════
def _fetch_eod():
    sys.path.insert(0, str(_REPO / "jobs"))
    import fetch_eod  # noqa: PLC0415
    return fetch_eod


def _mem_db():
    """In-memory DB carrying the real schema (jobs/init_db.py is the source)."""
    import re  # noqa: PLC0415
    import sqlite3  # noqa: PLC0415

    sys.path.insert(0, str(_REPO / "jobs"))
    import init_db  # noqa: PLC0415

    conn = sqlite3.connect(":memory:")
    conn.executescript(init_db.SCHEMA)
    # init_db.main() applies idempotent ALTERs *after* the schema string (the
    # m8 analyst columns live only there). Replay them from the source so this
    # fixture cannot drift behind a newly added column.
    for stmt in re.findall(r'_safe_alter\(conn, "([^"]+)"\)',
                           Path(init_db.__file__).read_text(encoding="utf-8")):
        init_db._safe_alter(conn, stmt)
    return conn


def test_r1_all_priceless_trips_the_info_failure_guard(monkeypatch):
    """10 tickers, every `.info` fetch succeeds, none carries a price → raise.

    This is the metadata-only outage. Before the fixup it was indistinguishable
    from a perfect run: ok=0, fail=0, fail_rate=0.0, no exception.
    """
    fetch_eod = _fetch_eod()
    conn = _mem_db()
    tickers = [f"T{i}" for i in range(10)]
    # Priceless: real metadata, no regularMarketPrice / currentPrice.
    monkeypatch.setattr(fetch_eod, "fetch_info_for",
                        lambda t: {"currency": "USD", "marketCap": 1e9, "trailingPE": 20.0})

    with pytest.raises(RuntimeError, match="mult"):
        fetch_eod.run_multiples(conn, tickers, "2026-09-05", {"USD": 1.0}, sleep_s=0)


def test_r1_priceless_are_not_counted_as_ok(monkeypatch, capsys):
    """8 good + 2 priceless: ok=8, priceless=2, and the summary says all three."""
    fetch_eod = _fetch_eod()
    conn = _mem_db()
    tickers = [f"T{i}" for i in range(10)]
    good = {"currency": "USD", "marketCap": 1e9, "regularMarketPrice": 10.0}
    bad = {"currency": "USD", "marketCap": 1e9}          # no price at all

    monkeypatch.setattr(fetch_eod, "fetch_info_for",
                        lambda t: bad if t in ("T8", "T9") else good)

    res = fetch_eod.run_multiples(conn, tickers, "2026-09-05", {"USD": 1.0}, sleep_s=0)
    assert res.ok == 8
    assert sorted(res.priceless) == ["T8", "T9"]
    assert res.failed == []

    summary = [ln for ln in capsys.readouterr().out.splitlines() if "[mult] done." in ln]
    assert len(summary) == 1, "expected exactly one summary line"
    for field in ("ok=", "priceless=", "failed="):
        assert field in summary[0], f"summary line does not report {field!r}: {summary[0]}"


def test_r2_gross_divergence_counts_as_unusable(monkeypatch):
    """A dropped-for-divergence row must land in the same accounting bucket.

    Otherwise a systematic `.info`/tape mismatch (a whole exchange's payloads
    going stale) is silently invisible for exactly the same reason item 1 was.
    """
    fetch_eod = _fetch_eod()
    conn = _mem_db()
    conn.execute(
        "INSERT INTO prices_daily (ticker, date, close, currency) VALUES (?,?,?,?)",
        ("108320.KQ", "2026-09-04", 37_800.0, "KRW"),
    )
    conn.commit()

    # 9 clean tickers alongside it → 10% unusable, below the guard, so the test
    # measures the ACCOUNTING rather than the raise.
    monkeypatch.setattr(
        fetch_eod, "fetch_info_for",
        lambda t: {"currency": "KRW", "marketCap": 1e12, "regularMarketPrice": 78_000.0}
        if t == "108320.KQ"
        else {"currency": "USD", "marketCap": 1e9, "regularMarketPrice": 10.0},
    )
    res = fetch_eod.run_multiples(
        conn, ["108320.KQ", *[f"T{i}" for i in range(9)]], "2026-09-05",
        {"KRW": 0.00072, "USD": 1.0}, sleep_s=0,
    )
    assert res.ok == 9
    assert res.priceless == ["108320.KQ"]
    assert res.failed == []
    assert res.rows == 9


def test_r2_divergence_log_names_the_bar_and_its_date(capsys):
    """The log must carry ticker / info price / bar close / BAR DATE.

    Without the date you cannot tell a frozen payload from a legitimate +120%
    pop measured against a stale bar — the two are the same number.
    """
    fetch_eod = _fetch_eod()
    fetch_eod.info_to_multiple_row(
        "108320.KQ", {"currency": "KRW", "regularMarketPrice": 78_000.0},
        "2026-09-05", {"KRW": 0.00072}, bar_close=37_800.0, bar_date="2026-08-11",
    )
    out = capsys.readouterr().out
    for token in ("108320.KQ", "78", "37", "2026-08-11"):
        assert token in out, f"divergence log omits {token!r}: {out}"


def test_r2_latest_bar_returns_the_bars_date(monkeypatch):
    """The bar lookup must surface WHICH bar it compared against."""
    fetch_eod = _fetch_eod()
    conn = _mem_db()
    for d, c in (("2026-08-11", 10.0), ("2026-09-04", 12.0)):
        conn.execute(
            "INSERT INTO prices_daily (ticker, date, close, currency) VALUES (?,?,?,?)",
            ("X", d, c, "USD"),
        )
    conn.commit()
    assert fetch_eod.latest_bar(conn, "X") == (12.0, "2026-09-04")
    assert fetch_eod.latest_bar(conn, "NOPE") is None


# ══════════════════════════════════════════════════════════════════════════
# H10 review fixup — refresh_manifest.json must be MERGED, not won
#
# `git checkout --theirs` on the manifest keeps this run's whole file, which
# silently discards every dataset entry the OTHER lane stamped while we were
# fetching. The manifest is a per-dataset map with independent writers: two
# lanes racing on it are not editing the same fact, they are each editing their
# own key. Taking one side whole is a lost update, and the thing it loses is
# precisely the `failed` stamp another lane just wrote — the C4 fix.
# ══════════════════════════════════════════════════════════════════════════
_MERGE = _REPO / "scripts" / "merge_manifest.py"


def _run_merge(tmp_path, upstream: str, this_run: str):
    """Run the merge script as the shell does; return (returncode, out, err, text)."""
    import subprocess  # noqa: PLC0415

    up = tmp_path / "upstream.json"
    mine = tmp_path / "this_run.json"
    out = tmp_path / "merged.json"
    up.write_text(upstream, encoding="utf-8")
    mine.write_text(this_run, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(_MERGE), "--upstream", str(up),
         "--this-run", str(mine), "--out", str(out)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout, r.stderr, (out.read_text(encoding="utf-8") if out.exists() else "")


def test_h10_merge_manifest_unions_disjoint_keys(tmp_path):
    """Two lanes stamping different datasets must both survive."""
    import json  # noqa: PLC0415

    up = json.dumps({"sec_facts": {"status": "failed", "refreshed_at": "2026-09-06T01:00:00+00:00"}})
    mine = json.dumps({"eod_prices": {"status": "ok", "refreshed_at": "2026-09-06T02:00:00+00:00"}})
    rc, _, err, text = _run_merge(tmp_path, up, mine)
    assert rc == 0, err
    merged = json.loads(text)
    assert set(merged) == {"sec_facts", "eod_prices"}
    assert merged["sec_facts"]["status"] == "failed"   # the other lane's C4 stamp


def test_h10_merge_manifest_later_refreshed_at_wins(tmp_path):
    import json  # noqa: PLC0415

    up = json.dumps({"eod_prices": {"status": "failed", "refreshed_at": "2026-09-06T09:00:00+00:00"}})
    mine = json.dumps({"eod_prices": {"status": "ok", "refreshed_at": "2026-09-06T02:00:00+00:00"}})
    rc, _, err, text = _run_merge(tmp_path, up, mine)
    assert rc == 0, err
    # Upstream is NEWER here, so upstream wins even though it is not "our" side.
    assert json.loads(text)["eod_prices"]["status"] == "failed"

    rc, _, err, text = _run_merge(tmp_path, mine, up)   # swap: this run is newer
    assert rc == 0, err
    assert json.loads(text)["eod_prices"]["status"] == "failed"


def test_h10_merge_manifest_falls_back_to_this_run(tmp_path):
    """No usable timestamp on either side → this run's entry (documented tie-break)."""
    import json  # noqa: PLC0415

    up = json.dumps({"eod_prices": {"status": "failed", "refreshed_at": None}})
    mine = json.dumps({"eod_prices": {"status": "ok"}})
    rc, _, err, text = _run_merge(tmp_path, up, mine)
    assert rc == 0, err
    assert json.loads(text)["eod_prices"]["status"] == "ok"


def test_h10_merge_manifest_malformed_side_exits_zero_with_warning(tmp_path):
    """A corrupt side must not wedge the push — warn, keep this run, exit 0."""
    import json  # noqa: PLC0415

    mine = json.dumps({"eod_prices": {"status": "ok", "refreshed_at": "2026-09-06T02:00:00+00:00"}})
    rc, out, err, text = _run_merge(tmp_path, "{not json at all", mine)
    assert rc == 0, f"a corrupt side must not fail the merge: {err}"
    assert "warn" in (out + err).lower(), "malformed input merged silently"
    assert json.loads(text)["eod_prices"]["status"] == "ok"


def test_h10_merge_manifest_writes_repo_json_style(tmp_path):
    """indent=2, ensure_ascii=False, sorted keys, trailing newline."""
    import json  # noqa: PLC0415

    real = json.loads((_REPO / "data" / "refresh_manifest.json").read_text(encoding="utf-8"))
    rc, _, err, text = _run_merge(tmp_path, json.dumps(real), json.dumps(real))
    assert rc == 0, err
    assert text == json.dumps(real, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert "\\u" not in text, "non-ASCII labels were escaped"


def test_h10_commit_data_merges_the_manifest_instead_of_taking_a_side(tmp_path):
    """The shell must route the manifest through the merge, not `--theirs` it."""
    src = (_REPO / "scripts" / "commit_data.sh").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    assert "merge_manifest.py" in code, (
        "commit_data.sh still resolves data/refresh_manifest.json by taking one "
        "whole side — that discards the other lane's dataset entries"
    )
    assert "refresh_manifest.json" in code


# ══════════════════════════════════════════════════════════════════════════
# C4 / H10 — every workflow stamps `failed` and pushes through commit_data.sh
# ══════════════════════════════════════════════════════════════════════════
_WORKFLOWS = sorted((_REPO / ".github" / "workflows").glob("*.yml"))


@pytest.mark.parametrize("wf", _WORKFLOWS, ids=lambda p: p.name)
def test_c4_workflow_stamps_failure_in_manifest(wf):
    """Three runs died in Aug/Sep 2026 with no `failed` row in the manifest."""
    src = wf.read_text(encoding="utf-8")
    assert "if: failure()" in src, f"{wf.name} has no failure stamp step"
    assert "update_manifest.py" in src and "failed" in src, (
        f"{wf.name} failure step does not write a `failed` manifest status"
    )


@pytest.mark.parametrize("wf", _WORKFLOWS, ids=lambda p: p.name)
def test_h10_workflows_push_via_commit_data(wf):
    """Naive `git add/commit/push` races the other lanes on main (H10)."""
    src = wf.read_text(encoding="utf-8")
    assert "commit_data.sh" in src, f"{wf.name} does not use scripts/commit_data.sh"
    assert "git push" not in src, f"{wf.name} still pushes directly"


def test_c4_commit_data_recovers_from_binary_rebase_conflict():
    """2026-09-01: a snapshots.db binary conflict wedged the retry loop.

    Every retry re-entered `git pull --rebase` with unmerged files present and
    died on "Pulling is not possible because you have unmerged files".
    """
    src = (_REPO / "scripts" / "commit_data.sh").read_text(encoding="utf-8")
    assert "rebase --abort" in src or "REBASE_HEAD" in src, (
        "commit_data.sh has no conflict recovery path"
    )
    assert "checkout" in src and "snapshots.db" in src, (
        "commit_data.sh does not resolve the binary conflict in favour of the "
        "freshly-produced data file"
    )
    # `reset --hard` may be NAMED in a comment (the header explains why it is the
    # wrong cure); it must never be EXECUTED.
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    assert "reset --hard" not in code, (
        "a hard reset would discard the run's freshly fetched data"
    )
    assert "--theirs" in code, (
        "during a REBASE `--theirs` is the commit being replayed (this run's data) "
        "and `--ours` is origin/main — keeping our file requires --theirs"
    )
