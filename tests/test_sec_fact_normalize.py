"""The normalized sec_fact parquet must be substitutable for `_load_facts`.

jobs/normalize_sec_facts.py carries a verbatim copy of the row-building loop in
app/lib/sec_facts.py `_load_facts`, plus one concept filter. That duplication is
only safe if something proves the two stay in step — this is that something.

The strong test is the last one: for three real tickers, the parquet file filtered
to one concept must equal, cell for cell and IN THE SAME ORDER, what `_load_facts`
returns for that concept. Order matters and is asserted, not sorted away:
`_dedupe_by_end_date` and `_rank` in app/lib/sec_facts.py are stable sorts, so rows
tying on all their keys resolve by input order. A read shim that changed the order
would silently change which fact the app shows.

Reads the committed data/snapshots.db and data/parquet/sec_fact/ — no network.
Skips (rather than fails) when either is absent, so a checkout without data still
runs the rest of the suite.

Run: `PYTHONPATH=app pytest tests/test_sec_fact_normalize.py -q` from the repo root.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parent.parent
_APP = _REPO / "app"
for p in (str(_REPO), str(_APP)):
    if p not in sys.path:
        sys.path.insert(0, p)

from jobs import normalize_sec_facts as nsf, parquet_store as ps, sec_concepts  # noqa: E402

_DB = _REPO / "data" / "snapshots.db"

# Opt out of tests/conftest.py's temp-store isolation: these tests READ the committed
# data/parquet/sec_fact/ files. They never write to it.
USES_COMMITTED_PARQUET_STORE = True

# Three tickers with big, differently-shaped payloads: a US pharma major, a big-tech
# filer, and a foreign filer that reports under ifrs-full rather than us-gaap.
_TICKERS = ["LLY", "MSFT", "AZN"]


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    """Object dtype with a single null sentinel, so two frames compare on VALUES.

    The parquet round-trip returns pandas extension dtypes (string, Int64) where
    `_load_facts` builds numpy object/float64 columns. That difference is real but
    uninteresting — `int(r["fy"])` behind a `pd.isna` guard, which is what the app
    does, reads both the same. What must not differ is the content, so both sides
    are flattened here rather than one being coerced into the other's shape.
    """
    out = df.reset_index(drop=True).astype(object)
    return out.where(pd.notna(out), None)


@pytest.fixture(scope="module")
def conn():
    if not _DB.exists():
        pytest.skip("data/snapshots.db not present")
    c = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def keep():
    return sec_concepts.used_concepts(_DB)


# ══════════════════════════════════════════════════════════════════════════
# the concept set
# ══════════════════════════════════════════════════════════════════════════
def test_concept_set_is_both_sources_and_neither_is_empty(conn, keep):
    tags = sec_concepts.statement_tags()
    kpi = sec_concepts.kpi_concepts(conn)
    assert len(tags) > 50, "statement tag parse collapsed"
    assert len(kpi) > 10, "sec_kpi_map concepts collapsed"
    assert keep == tags | kpi
    # spot-check one concept from each source so a parse that returns the wrong
    # literals cannot pass on counts alone
    assert "Revenues" in keep                    # INCOME_ROWS
    assert "NetCashProvidedByUsedInOperatingActivities" in keep   # CASHFLOW_ROWS


def test_a_broken_statements_parse_raises_instead_of_returning_a_short_set(tmp_path):
    """A silently short set would drop financial line items from every file."""
    stub = tmp_path / "sec_statements.py"
    stub.write_text("INCOME_ROWS = []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="silently drop"):
        sec_concepts.statement_tags(stub)


# ══════════════════════════════════════════════════════════════════════════
# projection
# ══════════════════════════════════════════════════════════════════════════
def test_projection_keeps_only_wanted_concepts_and_all_of_them(conn, keep):
    row = conn.execute(
        "SELECT payload_gzip FROM sec_company WHERE ticker = 'LLY' AND sec_status = 'ok'"
    ).fetchone()
    if not row or row[0] is None:
        pytest.skip("no LLY payload")
    from lib import sec_facts

    full = sec_facts._load_facts("LLY")
    proj = nsf.facts_frame(row[0], keep)

    assert set(proj["concept"]) <= keep
    # nothing the app can use was dropped
    assert set(proj["concept"]) == set(full["concept"]) & keep
    assert len(proj) < len(full), "projection should be a strict subset for LLY"


# ══════════════════════════════════════════════════════════════════════════
# the drop-in guarantee
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("ticker", _TICKERS)
def test_normalized_parquet_matches_load_facts_for_one_concept(ticker):
    """The written file, filtered to one concept, == `_load_facts` for that concept."""
    path = ps.partition_path("sec_fact", ticker)
    if not path.exists():
        pytest.skip(f"{path.name} not generated — run jobs/normalize_sec_facts.py")
    from lib import sec_facts

    expected_all = sec_facts._load_facts(ticker)
    if expected_all.empty:
        pytest.skip(f"no payload for {ticker}")

    actual_all = ps.read_partition("sec_fact", ticker)
    concepts = [c for c in ("Revenues", "Assets", "NetIncomeLoss",
                            "ResearchAndDevelopmentExpense", "StockholdersEquity")
                if c in set(actual_all["concept"])]
    assert concepts, f"{ticker}: none of the probe concepts survived the projection"

    for concept in concepts:
        exp = _norm(expected_all[expected_all["concept"] == concept])
        act = _norm(actual_all[actual_all["concept"] == concept])
        assert len(act) == len(exp), f"{ticker}/{concept}: row count"
        pd.testing.assert_frame_equal(act, exp, check_dtype=False,
                                      obj=f"{ticker}/{concept}")


@pytest.mark.parametrize("ticker", _TICKERS)
def test_columns_and_row_order_survive_the_round_trip(ticker):
    path = ps.partition_path("sec_fact", ticker)
    if not path.exists():
        pytest.skip(f"{path.name} not generated")
    from lib import sec_facts

    expected = sec_facts._load_facts(ticker)
    if expected.empty:
        pytest.skip(f"no payload for {ticker}")
    keep = sec_concepts.used_concepts(_DB)
    expected = expected[expected["concept"].isin(keep)]

    actual = ps.read_partition("sec_fact", ticker)
    assert list(actual.columns) == list(expected.columns), "column names/order drifted"
    assert len(actual) == len(expected), "row count drifted"
    # the WHOLE frame, in payload order — not just one concept
    pd.testing.assert_frame_equal(_norm(actual), _norm(expected), check_dtype=False)


def test_numeric_values_are_exact_not_merely_close():
    """float64 through parquet must be bit-exact; a rounded value is a wrong value."""
    ticker = _TICKERS[0]
    if not ps.partition_path("sec_fact", ticker).exists():
        pytest.skip("not generated")
    from lib import sec_facts

    exp = sec_facts._load_facts(ticker)
    exp = exp[exp["concept"].isin(sec_concepts.used_concepts(_DB))].reset_index(drop=True)
    act = ps.read_partition("sec_fact", ticker)
    a = act["value"].astype("Float64").to_numpy(dtype="float64", na_value=np.nan)
    b = exp["value"].to_numpy(dtype="float64", na_value=np.nan) if hasattr(
        exp["value"], "to_numpy") else np.asarray(exp["value"], dtype="float64")
    assert np.array_equal(a, b, equal_nan=True)


# ══════════════════════════════════════════════════════════════════════════
# the re-fetch gate — filings first, clock second
# ══════════════════════════════════════════════════════════════════════════
class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p


class _Session:
    """Minimal stand-in for requests.Session — no network, records the calls."""

    def __init__(self, payload, status=200):
        self._r = _Resp(payload, status)
        self.calls: list[str] = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        return self._r


_SEC_SCHEMA = """
CREATE TABLE sec_company (
    ticker TEXT PRIMARY KEY, cik INTEGER, cik10 TEXT, entity_name TEXT,
    taxonomy_primary TEXT, sec_status TEXT NOT NULL, fetched_at TEXT,
    latest_filed TEXT, facts_count INTEGER, last_error TEXT, payload_gzip BLOB);
"""


def _sec_conn(status="ok", fetched_at=None, latest_filed="2026-08-01"):
    from datetime import datetime, timedelta, timezone

    c = sqlite3.connect(":memory:")
    c.executescript(_SEC_SCHEMA)
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    elif fetched_at == "stale":
        fetched_at = (datetime.now(timezone.utc) - timedelta(days=9)).isoformat(
            timespec="seconds")
    c.execute("INSERT INTO sec_company (ticker, sec_status, fetched_at, latest_filed) "
              "VALUES ('LLY', ?, ?, ?)", (status, fetched_at, latest_filed))
    c.commit()
    return c


def _subs(dates, xbrl=None):
    recent = {"filingDate": dates}
    if xbrl is not None:
        recent["isXBRL"] = xbrl
    return {"filings": {"recent": recent}}


def test_a_new_filing_triggers_a_refetch():
    from jobs import fetch_sec_facts as fsf

    conn = _sec_conn(latest_filed="2026-08-01")
    s = _Session(_subs(["2026-09-05", "2026-07-01"], [1, 1]))
    fetch, why = fsf.should_refetch(conn, s, "LLY", "0000059478")
    assert fetch is True
    assert "2026-09-05" in why


def test_no_new_filing_skips_the_multi_mb_download():
    """The point of the gate: a fresh clock is not what decides this, the filings are."""
    from jobs import fetch_sec_facts as fsf

    conn = _sec_conn(fetched_at="stale", latest_filed="2026-08-01")
    s = _Session(_subs(["2026-08-01", "2026-05-01"], [1, 1]))
    fetch, why = fsf.should_refetch(conn, s, "LLY", "0000059478")
    assert fetch is False, "an 9-day-old snapshot with no new filing must NOT re-download"
    assert "no XBRL filing since 2026-08-01" in why


def test_non_xbrl_filings_do_not_trigger_a_refetch():
    """An 8-K cannot change companyfacts; treating it as a reason would re-fetch weekly."""
    from jobs import fetch_sec_facts as fsf

    conn = _sec_conn(latest_filed="2026-08-01")
    s = _Session(_subs(["2026-09-06", "2026-08-01"], [0, 1]))   # newest is non-XBRL
    fetch, why = fsf.should_refetch(conn, s, "LLY", "0000059478")
    assert fetch is False, why


def test_a_failed_probe_falls_back_to_the_clock():
    from jobs import fetch_sec_facts as fsf

    conn_stale = _sec_conn(fetched_at="stale")
    assert fsf.should_refetch(conn_stale, _Session({}, status=503), "LLY", "0")[0] is True
    conn_fresh = _sec_conn()
    ok, why = fsf.should_refetch(conn_fresh, _Session({}, status=503), "LLY", "0")
    assert ok is False and "clock" in why


def test_no_prior_snapshot_always_fetches():
    from jobs import fetch_sec_facts as fsf

    conn = sqlite3.connect(":memory:")
    conn.executescript(_SEC_SCHEMA)
    fetch, why = fsf.should_refetch(conn, _Session({}), "LLY", "0")
    assert fetch is True and "no usable prior snapshot" in why


def test_a_failed_prior_status_is_not_treated_as_a_snapshot():
    from jobs import fetch_sec_facts as fsf

    conn = _sec_conn(status="failed")
    assert fsf.should_refetch(conn, _Session({}), "LLY", "0")[0] is True
