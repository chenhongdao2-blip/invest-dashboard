"""Regression test for the undisclosed-fund (NA-row) mishandling bug (ccgg-uw gate).

Confirmed bug — ONE root cause, TWO sinks:

  The fund-positioning CSV has one row whose ow_uw_2026 carries the literal token
  N/A (that fund discloses NO healthcare weight). pandas.read_csv's DEFAULT
  na_values includes "N/A", so the cell loads as float('nan'), NOT the string the
  consumers assume. lib.hc_overview.load_fund_positioning restores the sentinel at
  the loader boundary so both sinks below behave.

  Sink #1 (lib.hc_overview.positioning_verdict): n_na = (ow_uw == "N/A").sum()
     was always 0 (cell was "nan"), dropping the undisclosed fund from the tally
     so n_ow+n_uw+n_neu+n_na != universe.
  Sink #2 (app/pages/2_Healthcare.py stance map): str(nan).strip() == "nan"
     missed every key, mislabelling the undisclosed fund "Neutral" instead of N/A.

This test is NAME-AGNOSTIC on purpose: the committed CSV is anonymised (Fund 1–12)
on Cloud but carries real names locally, so the undisclosed fund is identified by
its blank HC weight (fund_hc_w is NaN), never by a hardcoded fund name. The
contract holds regardless of the load mechanism: the NA fund must be (a) counted
as n_na and (b) routed to the NA stance key — never dropped or mislabelled Neutral.

Run: `pytest tests/test_hc_positioning_na.py -q` from repo root.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd

# ── make lib.hc_overview importable without a real streamlit install ──────────
# hc_overview imports streamlit at module top + uses @st.cache_data on the loaders;
# positioning_verdict itself is pure. Stub st so the import succeeds.
if "streamlit" not in sys.modules:
    _st = types.ModuleType("streamlit")
    _st.cache_data = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda fn: fn))
    sys.modules["streamlit"] = _st

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from lib import hc_overview as hco  # noqa: E402

# Mirror of the stance map + lookup in app/pages/2_Healthcare.py.
_STANCE_KEY = {
    "OW": "hc.pos.stance.OW",
    "UW": "hc.pos.stance.UW",
    "Neutral": "hc.pos.stance.Neutral",
    "Slightly OW": "hc.pos.stance.SlightlyOW",
    "N/A": "hc.pos.stance.NA",
}


def _stance_key_for(s) -> str:
    """Exact production mapping from 2_Healthcare.py."""
    return _STANCE_KEY.get(str(s).strip(), "hc.pos.stance.Neutral")


def _load() -> pd.DataFrame:
    pos = hco.load_fund_positioning()
    assert not pos.empty, "fixture CSV missing — china_fund_hc_positioning.csv"
    return pos


def _undisclosed_mask(pos: pd.DataFrame) -> pd.Series:
    """The undisclosed fund(s): blank/NaN disclosed HC weight — name-independent."""
    return pos["fund_hc_w"].isna()


def test_exactly_one_undisclosed_fund_present():
    """Sanity: the fixture still has exactly one no-HC-weight row this bug rests on."""
    pos = _load()
    assert _undisclosed_mask(pos).sum() == 1, "expected exactly one undisclosed-HC fund in the fixture"


def test_verdict_counts_cover_every_fund():
    """Sink #1: n_ow+n_uw+n_neu+n_na must equal the universe size."""
    pos = _load()
    v = hco.positioning_verdict(pos)
    total = v["n_ow"] + v["n_uw"] + v["n_neu"] + v["n_na"]
    assert total == len(pos), (
        f"verdict counts {total} funds but the universe has {len(pos)}; "
        f"the undisclosed fund was dropped (n_na={v['n_na']})"
    )


def test_verdict_counts_the_undisclosed_fund_as_na():
    """Sink #1, sharper: exactly one undisclosed fund → n_na == 1."""
    pos = _load()
    v = hco.positioning_verdict(pos)
    assert v["n_na"] == 1, (
        f"expected exactly 1 undisclosed (N/A) fund, got n_na={v['n_na']} — "
        "the documented N/A branch is dead code"
    )


def test_undisclosed_fund_maps_to_NA_stance_not_neutral():
    """Sink #2: the undisclosed fund's stance cell must resolve to the NA key."""
    pos = _load()
    stance = pos.loc[_undisclosed_mask(pos), "ow_uw_2026"].iloc[0]
    key = _stance_key_for(stance)
    assert key == "hc.pos.stance.NA", (
        f"undisclosed fund rendered via key {key!r} (raw cell={stance!r}); "
        "it must route to hc.pos.stance.NA, never the Neutral fallback"
    )


# ── robustness of positioning_verdict (synthetic frames, no CSV / no module state) ──
# Covers the three hardening fixes made alongside the N/A bug:
#   (1) count symmetry: n_uw uses contains() so "Slightly UW" lands in the UW lean,
#       mirroring n_ow's contains() catching "Slightly OW";
#   (2) zero / unparseable AUM denominator → no-data sentinel (no NaN tilt);
#   (3) the four counts partition the universe.

def _synthetic(stances: list[str], devs=None, aums=None) -> pd.DataFrame:
    n = len(stances)
    return pd.DataFrame({
        "fund": [f"F{i}" for i in range(n)],
        "ow_uw_2026": stances,
        "deviation_2026": devs if devs is not None else [0.01] * n,
        "aum_2026": aums if aums is not None else ["1.0bn"] * n,
    })


def test_slightly_uw_counts_as_underweight():
    """n_uw must include 'Slightly UW' (contains-match), symmetric with n_ow/'Slightly OW'."""
    v = hco.positioning_verdict(_synthetic(["UW", "Slightly UW"]))
    assert v["n_uw"] == 2, f"'Slightly UW' dropped from the underweight tally: n_uw={v['n_uw']}"


def test_counts_partition_the_universe():
    """n_ow + n_uw + n_neu + n_na == universe across the full stance vocabulary."""
    df = _synthetic(["OW", "UW", "Slightly OW", "Slightly UW", "Neutral", "N/A"])
    v = hco.positioning_verdict(df)
    assert v["n_ow"] + v["n_uw"] + v["n_neu"] + v["n_na"] == len(df)


def test_zero_aum_denominator_is_no_data_not_nan_tilt():
    """All-zero AUM → data_available False, aum_wt_dev OMITTED — never a NaN tilt the page
    would render as a fabricated '+0.0pp'/'+nanpp' directional conclusion."""
    v = hco.positioning_verdict(_synthetic(["OW", "UW"], aums=["0", "0mn"]))
    assert v.get("data_available") is False, f"zero AUM denominator advertised data: {v!r}"
    assert "aum_wt_dev" not in v, f"aum_wt_dev should be omitted on zero denominator: {v.get('aum_wt_dev')!r}"
    assert v.get("tilt") != "~flat", "no-data must not advertise a near-flat tilt"
