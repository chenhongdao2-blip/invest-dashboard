"""Red test for the data-narrative-coupling bug (ccgg-uw gate).

Bug (MAJOR, data-narrative-coupling):
  The hc.pos.verdict_tilt template (pages_en.py / pages_zh.py) bakes in fund-specific
  prose as FROZEN literals: 'the largest fund (3.3bn) is firmly UW at -3.8pp', the
  '2nd-largest ... +1.1pp', and 'up to +6.7pp'. positioning_verdict computes NONE of
  these — it returns only counts + aum_wt_dev. So when build_hc_overview_data.py
  re-bakes a new quarter (the whole point of the CSV pipeline), or the anon Fund-1..12
  file carries different per-fund deviations than the full file, the headline prose
  silently contradicts the diverging-bar chart on the same screen.

  The producer already sorts funds by AUM (the `have` frame). The fix is for the
  PRODUCER to emit the extremal/largest-fund figures so the template can be
  parameterised, instead of leaving them as frozen English.

This test pins the producer-side contract: positioning_verdict must surface the
largest-fund deviation, the 2nd-largest deviation, and the most-overweight deviation,
computed from the data — never hardcoded. RED today (keys absent).

Run: `pytest tests/test_hc_verdict_extremal.py -q` from repo root.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd

if "streamlit" not in sys.modules:
    _st = types.ModuleType("streamlit")
    _st.cache_data = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda fn: fn))
    _st.session_state = {}
    sys.modules["streamlit"] = _st

_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from lib import hc_overview as hco  # noqa: E402


def _frame(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    """rows = [(fund, aum_2026, deviation_2026), ...]."""
    return pd.DataFrame(
        {
            "fund": [r[0] for r in rows],
            "aum_2026": [r[1] for r in rows],
            "deviation_2026": [r[2] for r in rows],
            "ow_uw_2026": ["UW" if r[2] < 0 else "OW" for r in rows],
            "fund_hc_w": [0.05 for _ in rows],
        }
    )


def test_producer_emits_largest_fund_deviation():
    """largest_aum_dev must come from the top-AUM fund, not frozen prose."""
    df = _frame([("Big", "3.3bn", -0.038), ("Mid", "2.9bn", 0.011), ("Small", "1.2bn", 0.0667)])
    v = hco.positioning_verdict(df)
    assert "largest_aum_dev" in v, "verdict omits the largest-fund deviation it narrates"
    assert abs(v["largest_aum_dev"] - (-0.038)) < 1e-9, v.get("largest_aum_dev")


def test_producer_emits_second_largest_deviation():
    df = _frame([("Big", "3.3bn", -0.038), ("Mid", "2.9bn", 0.011), ("Small", "1.2bn", 0.0667)])
    v = hco.positioning_verdict(df)
    assert "second_aum_dev" in v, "verdict omits the 2nd-largest-fund deviation it narrates"
    assert abs(v["second_aum_dev"] - 0.011) < 1e-9, v.get("second_aum_dev")


def test_producer_emits_max_overweight_deviation():
    df = _frame([("Big", "3.3bn", -0.038), ("Mid", "2.9bn", 0.011), ("Small", "1.2bn", 0.0667)])
    v = hco.positioning_verdict(df)
    assert "max_ow_dev" in v, "verdict omits the peak-OW deviation it narrates ('up to +6.7pp')"
    assert abs(v["max_ow_dev"] - 0.0667) < 1e-9, v.get("max_ow_dev")


def test_extremals_track_a_rebaked_quarter():
    """The whole point: when the CSV is re-baked, the emitted figures MUST move with it
    (a frozen-prose template would not). Different per-fund devs -> different extremals."""
    rebaked = _frame([("Big", "4.0bn", 0.025), ("Mid", "3.1bn", -0.012), ("Small", "0.9bn", 0.041)])
    v = hco.positioning_verdict(rebaked)
    assert abs(v["largest_aum_dev"] - 0.025) < 1e-9, "largest-fund figure stayed frozen"
    assert abs(v["second_aum_dev"] - (-0.012)) < 1e-9, "2nd-largest figure stayed frozen"
    assert abs(v["max_ow_dev"] - 0.041) < 1e-9, "peak-OW figure stayed frozen"


def test_extremals_absent_when_no_data():
    """No real-money signal -> no extremal figures to narrate (no frozen fallback)."""
    df = pd.DataFrame(
        {
            "fund": ["A", "B"],
            "aum_2026": ["0", "0mn"],
            "deviation_2026": [0.01, -0.02],
            "ow_uw_2026": ["OW", "UW"],
            "fund_hc_w": [0.05, 0.05],
        }
    )
    v = hco.positioning_verdict(df)
    assert v.get("data_available") is False
    assert "largest_aum_dev" not in v
    assert "second_aum_dev" not in v
    assert "max_ow_dev" not in v
