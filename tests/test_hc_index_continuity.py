"""Continuity gate for the baked index-comparison series.

The regression this file pins, concretely: on 2026-09-07 the Healthcare page's
"S&P 500 Health Care vs S&P 500" panel drew a straight red line from mid-July to
early September. yfinance had returned NO bars for ^SP500-35 between 2026-07-17
and 2026-09-04 — 242 points against ^GSPC's 276 in the same panel — and
jobs/build_hc_overview_data.py wrote whatever it received. The front end joined
the two surviving endpoints 35 sessions apart, so the reader saw a smooth ~6%
climb that never happened.

The gate's contract, in one line: a hole longer than MAX_GAP_TRADING_DAYS is
REFUSED (exit non-zero, message naming the series and both dates), and can only be
persisted via --allow-gaps, which labels it degraded in the sibling meta json.

HOW IT WAS RESOLVED (2026-09-07). The gate cannot conjure the missing bars, and no
source we can reach serves the index: FactSet GlobalPrices returns fsymId: null for
every ^SP500-35 candidate id (the XLV control resolves, so index ids are simply
unsupported), FactSet Macroeconomics' 715-row US catalogue has no equity-index
category, Bigdata has no such entity (its "Health Care" row IS XLV, fixed windows
only), Quartr is subscription_required. Worse, the surviving prints are unstable —
the 2026-09-04 point sat in the committed CSV while yfinance, re-probed the same
day, returned nothing after 2026-07-17. So ^SP500-35 was RETIRED and the XLV ETF
took its place on a PRICE-return basis (^GSPC beside it is a price index; total
return would have added 1.14pp of dividend as fake health-care alpha). The tests
below now pin BOTH halves: the gate still works, AND the panel is clean because the
series was replaced rather than because the threshold was loosened.

Run: pytest tests/test_hc_index_continuity.py -v  (from repo root)
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
JOB_PATH = REPO_ROOT / "jobs" / "build_hc_overview_data.py"

# The real dates of the defect, kept as named constants so a future reader can see
# the gate is calibrated against an observed failure, not an invented one.
HOLE_PREV = "2026-07-17"
HOLE_NEXT = "2026-09-04"
HOLE_TRADING_DAYS = 35


def _load_job():
    """Import the job by path — jobs/ is not a package, and importing must not
    trigger any network call (yfinance is imported inside build_index_comparison)."""
    spec = importlib.util.spec_from_file_location("build_hc_overview_data", JOB_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


JOB = _load_job()


def _series(dates: list[str] | pd.DatetimeIndex, start: float = 100.0) -> pd.DataFrame:
    """closes-map entry: df(date, close) with a monotone dummy close."""
    idx = pd.DatetimeIndex(pd.to_datetime(list(dates)))
    return pd.DataFrame({"date": idx, "close": [start + i for i in range(len(idx))]})


# ──────────────────────────────────────────────────────────────────────────────
# 1. A continuous series passes
# ──────────────────────────────────────────────────────────────────────────────

def test_continuous_series_passes():
    """A gap-free daily series must produce zero breaks and must not exit.

    Pins the gate against over-firing: if this ever fails, the gate has become a
    tripwire on normal data and every rebuild is blocked.
    """
    closes = {"^GSPC": _series(pd.bdate_range("2026-01-02", "2026-06-30"))}
    assert JOB.find_continuity_breaks(closes) == []
    assert JOB.enforce_continuity(closes) == []


BAKED_CSV = REPO_ROOT / "data" / "external" / "hc_index_comparison.csv"


def _baked_closes() -> dict[str, pd.DataFrame]:
    """The committed CSV as the job's own per-series closes map (one entry per series,
    de-duplicated across panels — ^NBI / XBI live in two panels each)."""
    if not BAKED_CSV.exists():                # pragma: no cover - baked file is committed
        pytest.skip("baked hc_index_comparison.csv not present")
    df = pd.read_csv(BAKED_CSV)
    return {
        sid: (g[["date", "close"]].assign(date=pd.to_datetime(g["date"]))
              .drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True))
        for sid, g in df.groupby("series_id")
    }


def test_real_baked_csv_is_clean():
    """The committed CSV must now pass the gate with ZERO breaks.

    This assertion used to read "exactly one break, and it is ^SP500-35" — that was the
    defect being recorded. It is inverted deliberately: the hole is gone because the
    series was REPLACED (XLV, price basis), not because the threshold was relaxed. If
    this ever reports a break again, a source has started dropping sessions and the
    page must not be rebuilt until it is understood.
    """
    breaks = JOB.find_continuity_breaks(_baked_closes())
    assert breaks == [], f"baked CSV is no longer continuous: {breaks}"


def test_sphc_panel_no_longer_carries_the_retired_index():
    """^SP500-35 must be gone from the job config AND from the baked CSV.

    Pins the retirement itself. The index is not merely sparse — yfinance retracted
    prints it had already served (the 2026-09-04 point vanished between the bake and
    the next probe), so a series that reappears here is a regression, not a recovery.
    """
    assert "^SP500-35" not in JOB.SERIES_META
    assert "^SP500-35" not in JOB.PANEL_SERIES["sphc"]
    assert JOB.PANEL_SERIES["sphc"] == ["XLV", "^GSPC"]
    assert "^SP500-35" not in {sid for sids in JOB.PANEL_SERIES.values() for sid in sids}

    df = pd.read_csv(BAKED_CSV) if BAKED_CSV.exists() else pytest.skip("no baked CSV")
    assert "^SP500-35" not in set(df["series_id"]), "the retired index is back in the CSV"
    assert set(df[df["panel"] == "sphc"]["series_id"]) == {"XLV", "^GSPC"}


def test_xlv_is_continuous_across_the_full_window():
    """XLV must be gap-free AND cover exactly the sessions ^GSPC covers in its panel.

    Two assertions, because "continuous" alone is not enough: a series can be
    internally gap-free and still be short at the tail (^SP500-35 was gap-free right
    up to 2026-07-17). Sharing ^GSPC's session set is what makes the comparison a
    comparison — the panel inner-joins on common dates, so a short leg silently
    truncates the chart instead of holing it.
    """
    closes = _baked_closes()
    assert "XLV" in closes, "sphc hero missing from the baked CSV"
    assert JOB.find_continuity_breaks({"XLV": closes["XLV"]}) == []

    xlv, gspc = set(closes["XLV"]["date"]), set(closes["^GSPC"]["date"])
    assert xlv == gspc, (
        f"XLV and ^GSPC do not cover the same sessions "
        f"(XLV-only {sorted(xlv - gspc)[:5]}, ^GSPC-only {sorted(gspc - xlv)[:5]})"
    )
    assert closes["XLV"]["date"].min() == pd.Timestamp(JOB.ANCHOR)


def test_baked_meta_records_a_clean_build():
    """The sibling meta must positively assert degraded=false — absent is not clean."""
    meta_path = REPO_ROOT / "data" / "external" / "hc_index_comparison_meta.json"
    if not meta_path.exists():                # pragma: no cover - committed alongside the CSV
        pytest.skip("meta json not present")
    meta = json.loads(meta_path.read_text())
    assert meta["degraded"] is False
    assert meta["continuity_breaks"] == []


# ──────────────────────────────────────────────────────────────────────────────
# 2. Normal weekend / holiday gaps do NOT trip
# ──────────────────────────────────────────────────────────────────────────────

def test_weekend_gap_does_not_trip():
    """Fri -> Mon is one trading day, not three.

    Pins the calendar choice: a calendar-day threshold would fire on every weekend.
    """
    assert JOB._trading_day_gap(pd.Timestamp("2026-09-04"), pd.Timestamp("2026-09-07")) == 1
    closes = {"X": _series(["2026-09-03", "2026-09-04", "2026-09-07", "2026-09-08"])}
    assert JOB.find_continuity_breaks(closes) == []


def test_us_market_holiday_gaps_do_not_trip():
    """A series that skips real US market holidays must stay clean.

    pd.bdate_range does not know holidays, so each one is OVER-counted by a day.
    This pins that the deliberate over-count stays far below the threshold: the
    worst clusters here (Thanksgiving, Christmas, New Year, July 4th) reach 2, not 5.
    """
    holidays = {  # actual US market closures inside the window
        "2025-11-27",  # Thanksgiving
        "2025-12-25",  # Christmas
        "2026-01-01",  # New Year's Day
        "2026-07-03",  # Independence Day (observed)
    }
    sessions = [d for d in pd.bdate_range("2025-11-03", "2026-07-31")
                if d.strftime("%Y-%m-%d") not in holidays]
    closes = {"X": _series(sessions)}
    assert JOB.find_continuity_breaks(closes) == [], (
        "a normal holiday calendar tripped the gate — the bdate_range over-count "
        "has eaten the safety margin"
    )
    # and the worst single holiday gap is well inside the budget
    assert JOB._trading_day_gap(pd.Timestamp("2025-11-26"), pd.Timestamp("2025-11-28")) == 2
    assert JOB._trading_day_gap(pd.Timestamp("2025-12-24"), pd.Timestamp("2025-12-26")) == 2


# ──────────────────────────────────────────────────────────────────────────────
# 3. A seven-week hole is refused
# ──────────────────────────────────────────────────────────────────────────────

def test_seven_week_hole_is_refused_with_a_naming_message():
    """The observed ^SP500-35 hole must exit non-zero and name series + both dates + gap.

    Pins the whole point of the gate: before it, this frame was written silently and
    the chart lied. The message assertions pin that an operator can act on the failure
    without opening the CSV.
    """
    closes = {"^SP500-35": _series(
        list(pd.bdate_range("2026-06-01", HOLE_PREV)) + [pd.Timestamp(HOLE_NEXT)]
    )}
    with pytest.raises(SystemExit) as excinfo:
        JOB.enforce_continuity(closes)

    code = excinfo.value.code
    assert code not in (0, None), "gate must exit NON-ZERO so callers/CI fail loudly"
    msg = str(code)
    assert "REFUSING TO WRITE" in msg
    assert "^SP500-35" in msg
    assert HOLE_PREV in msg and HOLE_NEXT in msg
    assert str(HOLE_TRADING_DAYS) in msg
    assert "--allow-gaps" in msg, "message must state the deliberate opt-out"


def test_gap_of_exactly_the_threshold_is_allowed_but_one_more_is_not():
    """5 trading days passes, 6 refuses — pins the boundary so it can't silently drift."""
    base = pd.Timestamp("2026-03-02")  # a Monday
    ok = _series([base, base + pd.tseries.offsets.BDay(5)])
    bad = _series([base, base + pd.tseries.offsets.BDay(6)])
    assert JOB.find_continuity_breaks({"X": ok}) == []
    assert len(JOB.find_continuity_breaks({"X": bad})) == 1


def test_break_is_reported_once_per_series_not_once_per_panel():
    """The gate runs on the per-series closes map, before the panel explode.

    ^NBI and XBI belong to two panels each (nbi + ai_bio). Pins that a hole in such a
    series is reported once, not duplicated per panel.
    """
    assert JOB.PANEL_SERIES["nbi"].count("^NBI") + JOB.PANEL_SERIES["ai_bio"].count("^NBI") == 2
    closes = {"^NBI": _series(["2026-06-01", "2026-08-03"])}
    breaks = JOB.find_continuity_breaks(closes)
    assert len(breaks) == 1 and breaks[0]["series_id"] == "^NBI"


# ──────────────────────────────────────────────────────────────────────────────
# 4. The opt-out flag writes, and labels the output degraded
# ──────────────────────────────────────────────────────────────────────────────

def test_allow_gaps_returns_breaks_instead_of_exiting():
    """--allow-gaps must NOT exit, and must hand the breaks back for labelling.

    Pins that the opt-out is 'persist deliberately + record it', never 'ignore it'.
    """
    closes = {"^SP500-35": _series([HOLE_PREV, HOLE_NEXT])}
    breaks = JOB.enforce_continuity(closes, allow_gaps=True)
    assert breaks == [{
        "series_id": "^SP500-35",
        "prev_date": HOLE_PREV,
        "next_date": HOLE_NEXT,
        "trading_day_gap": HOLE_TRADING_DAYS,
    }]


def _run_main(monkeypatch, tmp_path, *, breaks, argv):
    """Drive main() with a stubbed build_index_comparison (no network) into tmp_path."""
    frame = pd.DataFrame({
        "date": ["2026-09-03", "2026-09-04"],
        "series_id": ["^SP500-35", "^SP500-35"],
        "name_en": ["S&P 500 Health Care"] * 2,
        "name_cn": ["标普500医疗保健"] * 2,
        "panel": ["sphc"] * 2,
        "close": [1990.0, 1996.03],
        "source": ["yfinance"] * 2,
    })
    monkeypatch.setattr(JOB, "OUT", tmp_path)
    monkeypatch.setattr(JOB, "build_index_comparison",
                        lambda **kw: (frame, breaks))
    monkeypatch.setattr("sys.argv", ["build_hc_overview_data.py", *argv])
    JOB.main()
    return json.loads((tmp_path / "hc_index_comparison_meta.json").read_text())


def test_allow_gaps_writes_the_csv_and_marks_the_meta_degraded(monkeypatch, tmp_path):
    """With --allow-gaps the CSV IS written, and the meta records degraded=true + the break.

    Pins the 'labelled, not silent' half of the contract: the failure mode being fixed
    was a holed series landing in the CSV with nothing downstream able to tell.
    """
    breaks = [{"series_id": "^SP500-35", "prev_date": HOLE_PREV,
               "next_date": HOLE_NEXT, "trading_day_gap": HOLE_TRADING_DAYS}]
    meta = _run_main(monkeypatch, tmp_path, breaks=breaks,
                     argv=["--public-only", "--allow-gaps"])

    assert (tmp_path / "hc_index_comparison.csv").exists(), "opt-out must still write"
    assert meta["degraded"] is True
    assert meta["continuity_breaks"] == breaks
    assert meta["max_gap_trading_days"] == JOB.MAX_GAP_TRADING_DAYS


def test_clean_build_writes_meta_marked_not_degraded(monkeypatch, tmp_path):
    """A clean build still writes the meta, with degraded=false and no breaks.

    Pins that 'clean' is asserted positively — absent meta must not be readable as
    'probably fine'.
    """
    meta = _run_main(monkeypatch, tmp_path, breaks=[], argv=["--public-only"])
    assert meta["degraded"] is False
    assert meta["continuity_breaks"] == []
    assert meta["anchor"] == JOB.ANCHOR


# ──────────────────────────────────────────────────────────────────────────────
# 5. The replacement series' BASIS — price, not total return
# ──────────────────────────────────────────────────────────────────────────────

def test_price_basis_tickers_names_xlv_only():
    """XLV is the one series that must come back on a price basis.

    ^GSPC beside it in the sphc panel is a PRICE index and ^SP500-35 was one too, so
    the proxy has to be quoted the same way. The other ETFs (XBI / KURE / MCHI) stay
    total-return on purpose — their panels compare them against other total-return
    ETFs or against indices where the mismatch is already disclosed in the title.
    """
    assert JOB.PRICE_BASIS_TICKERS == {"XLV"}
    assert "XLV" in JOB.US_TICKERS
    assert "price" in JOB.SERIES_META["XLV"][2].lower(), (
        "the CSV's own source column must state the basis — it is the provenance a "
        "downstream reader sees without opening this job"
    )


def test_xlv_is_fetched_with_auto_adjust_false_and_the_rest_with_true(monkeypatch):
    """Pins the actual yfinance call, not just the constant.

    This is the assertion that stops the 1.14pp regression: over 2026-01-02 ->
    2026-09-04, XLV total return was +11.19% against the index's +10.05%, while XLV
    price return was +10.25%. A single auto_adjust=True fetch would therefore paint
    ~1.1pp of dividend as health-care outperformance versus the S&P — a difference
    large enough to flip the read of the panel, and invisible in the chart.
    """
    calls: list[tuple[tuple[str, ...], bool]] = []

    def _fake_download(tickers, *, start, end, auto_adjust, progress, threads, group_by):
        tickers = list(tickers)
        calls.append((tuple(sorted(tickers)), auto_adjust))
        idx = pd.bdate_range(start, "2026-09-04", name="Date")
        cols = pd.MultiIndex.from_product([tickers, ["Close"]])
        return pd.DataFrame(
            [[100.0 + i] * len(cols) for i in range(len(idx))], index=idx, columns=cols
        )

    fake_yf = type("_FakeYF", (), {"download": staticmethod(_fake_download)})
    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yf)

    df, breaks = JOB.build_index_comparison()
    assert breaks == []

    by_flag = {flag: set(tk) for tk, flag in calls}
    assert by_flag[False] == {"XLV"}, f"only XLV may be price-basis, got {by_flag[False]}"
    assert "XLV" not in by_flag[True], "XLV must not also be pulled total-return"
    assert by_flag[True] == set(JOB.US_TICKERS) - {"XLV"}
    assert set(df[df["panel"] == "sphc"]["series_id"]) == {"XLV", "^GSPC"}
