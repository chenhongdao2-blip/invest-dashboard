"""Projecting the SEC fact frame must not change a single KPI answer.

`_load_facts` now keeps only `sec_concepts.used_concepts()` (90 of ELV's 784) and
downcasts the repeated strings to categories — R3 audit §5's 1 GB OOM path. The
claim that makes it safe is narrow and testable: nothing on the KPI or statement
path can reach a concept outside that set. So run `pick_kpi_fact` for every KPI
in the map against BOTH frames and require identical dicts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from lib import db, sec_concepts, sec_facts as sf, sec_statements as ss  # noqa: E402

TICKERS = ["LLY", "ELV", "AMGN", "PFE", "JNJ"]


@pytest.fixture(scope="module", autouse=True)
def _needs_db():
    if not db.DB_PATH.exists():
        pytest.skip("data/snapshots.db not present")


@pytest.fixture(scope="module")
def kpi_keys() -> list[str]:
    df = db.query("SELECT kpi_key FROM sec_kpi_map ORDER BY kpi_key")
    if df.empty:
        pytest.skip("sec_kpi_map is empty")
    return df["kpi_key"].tolist()


@pytest.fixture(scope="module")
def _unprojected(monkeypatch_module=None):
    """`pick_kpi_fact` against the FULL parse, by swapping the loader it reads."""
    return sf._load_facts_full


def _pick_all(ticker: str, kpi_keys: list[str], period: str) -> dict:
    return {k: sf.pick_kpi_fact(ticker, k, period=period) for k in kpi_keys}


@pytest.mark.parametrize("ticker", TICKERS)
@pytest.mark.parametrize("period", ["annual", "quarterly"])
def test_pick_kpi_fact_identical_projected_vs_full(ticker, period, kpi_keys, monkeypatch):
    if db.query("SELECT 1 FROM sec_company WHERE ticker = ? AND sec_status = 'ok'",
                (ticker,)).empty:
        pytest.skip(f"{ticker} has no ok SEC payload")

    projected = _pick_all(ticker, kpi_keys, period)

    # Re-run the identical selection logic over the unprojected, undowncast frame.
    monkeypatch.setattr(sf, "_load_facts", sf._load_facts_full)
    sf.concept_timeseries.clear()
    full = _pick_all(ticker, kpi_keys, period)

    assert set(projected) == set(full)
    for k in kpi_keys:
        a, b = projected[k], full[k]
        assert (a is None) == (b is None), f"{ticker}/{k}: presence differs"
        if a is None:
            continue
        assert set(a) == set(b), f"{ticker}/{k}: key set differs"
        for field in a:
            av, bv = a[field], b[field]
            if isinstance(av, float) and isinstance(bv, float):
                assert av == pytest.approx(bv, rel=1e-12) or (pd.isna(av) and pd.isna(bv)), \
                    f"{ticker}/{k}/{field}: {av!r} != {bv!r}"
            else:
                assert av == bv, f"{ticker}/{k}/{field}: {av!r} != {bv!r}"


@pytest.mark.parametrize("ticker", TICKERS[:3])
def test_statement_rows_reach_only_kept_concepts(ticker):
    """Every tag a statement row can ask for survives the projection."""
    kept = sec_concepts.used_concepts()
    for block in (ss.INCOME_ROWS, ss.BALANCE_ROWS, ss.CASHFLOW_ROWS):
        for row in block:
            for tag in row.get("tags", ()):
                assert tag in kept, f"{row['key']} tag {tag} would be projected away"


def test_kpi_chains_are_all_kept():
    import json

    kept = sec_concepts.used_concepts()
    for raw in db.query("SELECT concepts_json FROM sec_kpi_map")["concepts_json"]:
        for tc in json.loads(raw):
            concept = str(tc).partition(":")[2] or str(tc)
            assert concept in kept, f"{tc} would be projected away"


def test_all_facts_still_sees_every_concept():
    """Design A.5 risk: the browser must NOT silently shrink to 90 concepts."""
    if db.query("SELECT 1 FROM sec_company WHERE ticker = 'ELV' AND sec_status = 'ok'").empty:
        pytest.skip("ELV has no ok SEC payload")
    full = sf.all_facts("ELV")
    assert full["concept"].nunique() > 400, "all_facts got projected"
    assert {"label", "frame", "value_text", "accession"} <= set(full.columns)


def test_projection_actually_saves_memory():
    if db.query("SELECT 1 FROM sec_company WHERE ticker = 'ELV' AND sec_status = 'ok'").empty:
        pytest.skip("ELV has no ok SEC payload")
    small = sf._load_facts("ELV").memory_usage(deep=True).sum()
    big = sf._load_facts_full("ELV").memory_usage(deep=True).sum()
    assert small * 10 < big, f"expected >10x; got {big / small:.1f}x ({small/1e6:.2f} MB)"


def test_comp_table_is_cached_and_matches_pick_kpi_fact(kpi_keys):
    """`comp_table` is now `@st.cache_data`, so it must take TUPLES (audit §5 clocked
    it at 838 ms WARM precisely because list args meant it was never cached)."""
    import inspect

    tickers = tuple(db.query(
        "SELECT ticker FROM sec_company WHERE sec_status = 'ok' ORDER BY ticker LIMIT 5"
    )["ticker"])
    if not tickers:
        pytest.skip("no ok SEC payloads")
    keys = tuple(kpi_keys[:5])

    got = sf.comp_table(tickers, keys, "en")

    # transitive equivalence: pick_kpi_fact is already pinned against the full frame
    kmeta = {k: sf._kpi_row(k) for k in keys}
    for _, row in got.iterrows():
        t = row["Ticker"]
        ends = []
        for k in keys:
            f = sf.pick_kpi_fact(t, k, period="annual")
            want = None if f is None else f["value"]
            cell = row[kmeta[k]["label_en"]]
            assert (cell == want) or (pd.isna(cell) and want is None), f"{t}/{k}"
            if f and f.get("end_date"):
                ends.append(f["end_date"])
        assert row["FY End"] == (max(ends) if ends else None)

    inner = getattr(sf.comp_table, "__wrapped__", sf.comp_table)
    params = inspect.signature(inner).parameters
    assert "tuple" in str(params["tickers"].annotation), "list args are unhashable"
    assert "tuple" in str(params["kpi_keys"].annotation)


def test_comp_table_call_sites_pass_tuples():
    for page in ("8_SEC_Facts.py", "a5_ai_sec.py"):
        src = (Path(__file__).resolve().parent.parent / "app" / "pages" / page).read_text()
        assert "sf.comp_table(tuple(comp_tickers), tuple(comp_kpis)" in src, page


# ──────────────────────────────────────────────────────────────────────────
# Out-of-projection concepts: the browser offers them, so they must still chart
# ──────────────────────────────────────────────────────────────────────────
_BROWSER_TICKER = "A"


def _browsable_out_of_projection(ticker: str) -> list[tuple[str, str, str]]:
    """(taxonomy, concept, unit) triples the SEC page's selectbox offers but the
    projection drops — built exactly the way `8_SEC_Facts.py` builds `ts_opts`."""
    kept = sec_concepts.used_concepts()
    all_df = sf.all_facts(ticker)
    if all_df.empty:
        return []
    grp = (all_df[all_df["value"].notna()]
           .groupby(["taxonomy", "concept", "unit"])["end_date"].nunique())
    return [(tax, c, u) for (tax, c, u), n in grp.items() if n >= 2 and c not in kept]


def test_browser_offers_concepts_the_projection_drops():
    """Pins the premise of the next test: the two sets really do diverge."""
    if db.query("SELECT 1 FROM sec_company WHERE ticker = ? AND sec_status = 'ok'",
                (_BROWSER_TICKER,)).empty:
        pytest.skip(f"{_BROWSER_TICKER} has no ok SEC payload")
    assert _browsable_out_of_projection(_BROWSER_TICKER), \
        "expected the browser to offer concepts outside used_concepts()"


def test_concept_timeseries_serves_out_of_projection_concepts(monkeypatch):
    """`8_SEC_Facts.py` / `a5_ai_sec.py` populate the concept picker from
    `all_facts` (unprojected) and chart through `concept_timeseries`. If that read
    only the projected frame, ~694 of A's 784 selectable concepts would render an
    empty chart. Every offered concept must return what the pre-projection code
    path returned — i.e. what `_load_facts_full` yields.
    """
    if db.query("SELECT 1 FROM sec_company WHERE ticker = ? AND sec_status = 'ok'",
                (_BROWSER_TICKER,)).empty:
        pytest.skip(f"{_BROWSER_TICKER} has no ok SEC payload")

    offered = _browsable_out_of_projection(_BROWSER_TICKER)
    assert offered
    # A deterministic spot-check plus a broad sweep: the named one is the concept
    # the R3 review reproduced against.
    named = [t for t in offered if t[1] == "EntityPublicFloat"]
    sample = named + [t for t in offered[:40] if t not in named]

    got = {tc: sf.concept_timeseries(_BROWSER_TICKER, *tc) for tc in sample}

    # The pre-PR path: same selection logic over the unprojected frame.
    monkeypatch.setattr(sf, "_load_facts", sf._load_facts_full)
    sf.concept_timeseries.clear()
    want = {tc: sf.concept_timeseries(_BROWSER_TICKER, *tc) for tc in sample}
    sf.concept_timeseries.clear()

    empties = [tc for tc, df in got.items() if df.empty and not want[tc].empty]
    assert not empties, f"{len(empties)}/{len(sample)} offered concepts chart empty: {empties[:5]}"
    for tc in sample:
        pd.testing.assert_frame_equal(
            got[tc].reset_index(drop=True), want[tc].reset_index(drop=True),
            check_dtype=False, obj=f"{tc}",
        )
