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


def test_real_baked_csv_has_exactly_one_break_and_it_is_sphc():
    """The committed CSV must reproduce the observed defect: ^SP500-35 and nothing else.

    Pins BOTH directions at once — that the gate catches the real hole, and that the
    other 10 baked series (HK iFind + US yfinance, 13 months, two holiday calendars)
    are clean at a threshold of 5. If a future change makes this report extra series,
    the threshold has drifted into false positives.
    """
    csv = REPO_ROOT / "data" / "external" / "hc_index_comparison.csv"
    if not csv.exists():                      # pragma: no cover - baked file is committed
        pytest.skip("baked hc_index_comparison.csv not present")
    df = pd.read_csv(csv)
    closes = {
        sid: g[["date", "close"]].assign(date=pd.to_datetime(g["date"]))
                                 .sort_values("date").reset_index(drop=True)
        for sid, g in df.groupby("series_id")
    }
    breaks = JOB.find_continuity_breaks(closes)
    assert [b["series_id"] for b in breaks] == ["^SP500-35"], (
        f"expected the ^SP500-35 hole and nothing else, got {breaks}"
    )
    assert breaks[0]["prev_date"] == HOLE_PREV
    assert breaks[0]["next_date"] == HOLE_NEXT


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
