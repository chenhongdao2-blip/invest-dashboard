"""The parity gate must actually fire. A check that cannot go red is decoration.

Each test drops ONE kind of divergence into an otherwise-matching pair of stores
and asserts the gate names it. The three kinds map to the three ways the dual
write can break: a row never written, a row written that SQLite does not have,
and a value that drifted.

Run: `pytest tests/test_parity_check.py -q` from the repo root.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from jobs import parity_check, parquet_store as ps  # noqa: E402

_SCHEMA = """
CREATE TABLE benchmarks_daily (
    ticker TEXT NOT NULL, date TEXT NOT NULL, close REAL, PRIMARY KEY (ticker, date));
"""
ROWS = [("^HSI", "2026-09-01", 25000.0), ("^HSI", "2026-09-02", 25100.0),
        ("XBI", "2026-08-29", 90.0)]


@pytest.fixture()
def stores(tmp_path, monkeypatch):
    """A SQLite table and a Parquet store holding exactly the same three rows."""
    monkeypatch.setenv("PARQUET_STORE_ROOT", str(tmp_path / "parquet"))
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO benchmarks_daily VALUES (?,?,?)", ROWS)
    conn.commit()
    ps.upsert_rows("benchmarks_daily",
                   __import__("pandas").DataFrame(ROWS, columns=["ticker", "date", "close"]))
    yield conn
    conn.close()


def _check(conn) -> list[str]:
    return parity_check.check_table(conn, "benchmarks_daily", max_samples=5)


def test_matching_stores_report_no_problems(stores):
    assert _check(stores) == []


def test_a_row_missing_from_parquet_is_caught(stores):
    """The dual-write did not fire for one row."""
    df = ps.read_partition("benchmarks_daily", "2026-09")
    ps.write_partition("benchmarks_daily", "2026-09", df.iloc[1:])

    problems = _check(stores)
    assert any("row count" in p for p in problems)
    assert any("in SQLite but NOT in Parquet" in p and "^HSI | 2026-09-01" in p
               for p in problems), problems


def test_a_row_sqlite_does_not_have_is_caught(stores):
    """Parquet kept something SQLite dropped — the other direction of the anti-join."""
    stores.execute("DELETE FROM benchmarks_daily WHERE date = '2026-08-29'")
    stores.commit()

    problems = _check(stores)
    assert any("in Parquet but NOT in SQLite" in p and "XBI | 2026-08-29" in p
               for p in problems), problems


def test_a_drifted_value_is_caught(stores):
    """Same PKs on both sides, one number different."""
    df = ps.read_partition("benchmarks_daily", "2026-09")
    df.loc[df.index[0], "close"] = 99999.0
    ps.write_partition("benchmarks_daily", "2026-09", df)

    problems = _check(stores)
    assert len(problems) == 1, problems          # counts and PKs still agree
    assert "column 'close'" in problems[0]
    assert "99999" in problems[0]


def test_null_equals_null_is_not_a_divergence(stores):
    """A NULL close on both sides must not be reported as a mismatch."""
    stores.execute("UPDATE benchmarks_daily SET close = NULL WHERE date = '2026-08-29'")
    stores.commit()
    df = ps.read_partition("benchmarks_daily", "2026-08")
    df.loc[df.index[0], "close"] = None
    ps.write_partition("benchmarks_daily", "2026-08", df)

    assert _check(stores) == []


# ══════════════════════════════════════════════════════════════════════════
# the rollback lever must not be a foot-gun
# ══════════════════════════════════════════════════════════════════════════
def test_main_skips_when_dual_write_is_disabled(tmp_path, monkeypatch, capsys):
    """`PARQUET_DUAL_WRITE=0` is the documented rollback (docs/storage-migration.md).

    The gate runs BEFORE "Commit data" in all three workflows, so a rolled-back
    pipeline whose Parquet store is frozen mid-week would fail here and stop the
    whole run — the rollback lever would break the thing it exists to rescue.
    Divergence is the POINT of this fixture: the store below is deliberately
    empty against a populated SQLite, which is exactly what a mid-week rollback
    looks like on day two.
    """
    monkeypatch.setenv("PARQUET_STORE_ROOT", str(tmp_path / "empty-parquet"))
    monkeypatch.setenv(ps.DUAL_WRITE_ENV, "0")
    db = tmp_path / "snapshots.db"
    conn = sqlite3.connect(db)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO benchmarks_daily VALUES (?,?,?)", ROWS)
    conn.commit()
    conn.close()
    monkeypatch.setattr(sys, "argv",
                    ["parity_check.py", "--db", str(db), "--table", "benchmarks_daily"])

    # sanity: with the flag ON this same pair is a hard failure
    monkeypatch.setenv(ps.DUAL_WRITE_ENV, "1")
    with pytest.raises(SystemExit) as red:
        parity_check.main()
    assert red.value.code == 1

    monkeypatch.setenv(ps.DUAL_WRITE_ENV, "0")
    parity_check.main()          # no SystemExit == exit 0
    out = capsys.readouterr().out
    assert "[parity] SKIP — dual write disabled (PARQUET_DUAL_WRITE=0)" in out


# ══════════════════════════════════════════════════════════════════════════
# sec_fact — the payload is the authority, so the check has a different shape
# ══════════════════════════════════════════════════════════════════════════
_SEC_SCHEMA = """
CREATE TABLE sec_company (
    ticker TEXT PRIMARY KEY, sec_status TEXT NOT NULL, payload_gzip BLOB);
"""


def _payload(*revenues: float) -> bytes:
    """A minimal companyfacts blob using one concept that survives the projection."""
    import gzip
    import json

    items = [{"start": "2026-01-01", "end": f"2026-03-3{i}", "val": v,
              "fy": 2026, "fp": "Q1", "form": "10-Q", "filed": "2026-04-01",
              "accn": f"0000-{i}", "frame": "CY2026Q1"}
             for i, v in enumerate(revenues)]
    return gzip.compress(json.dumps(
        {"facts": {"us-gaap": {"Revenues": {"label": "Revenues",
                                            "units": {"USD": items}}}}}).encode())


@pytest.fixture()
def sec_stores(tmp_path, monkeypatch):
    """One ok ticker whose parquet file matches the payload it was derived from."""
    from jobs import normalize_sec_facts as nsf, sec_concepts

    monkeypatch.setenv("PARQUET_STORE_ROOT", str(tmp_path / "parquet"))
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SEC_SCHEMA)
    blob = _payload(100.0, 200.0)
    conn.execute("INSERT INTO sec_company VALUES ('LLY', 'ok', ?)", (blob,))
    conn.commit()
    nsf.write_ticker("LLY", nsf.facts_frame(blob, sec_concepts.used_concepts()))
    yield conn
    conn.close()


def _sec_check(conn) -> list[str]:
    return parity_check.check_sec_fact(conn, max_samples=5)[0]


def test_a_matching_sec_store_reports_no_problems(sec_stores):
    assert _sec_check(sec_stores) == []


def test_a_ticker_with_no_parquet_file_is_caught(sec_stores):
    """The dual-write never fired for this ticker — `write_sec_fact_parquet` swallows."""
    sec_stores.execute("INSERT INTO sec_company VALUES ('MSFT', 'ok', ?)",
                       (_payload(5.0),))
    sec_stores.commit()

    problems = _sec_check(sec_stores)
    assert any("have NO parquet file" in p and "MSFT" in p for p in problems), problems


def test_a_stale_file_with_fewer_rows_is_caught(sec_stores):
    """The payload gained a fact and the partition was not rewritten."""
    sec_stores.execute("UPDATE sec_company SET payload_gzip = ? WHERE ticker = 'LLY'",
                       (_payload(100.0, 200.0, 300.0),))
    sec_stores.commit()

    problems = _sec_check(sec_stores)
    assert any("differ in row count" in p and "parquet=2" in p and "payload=3" in p
               for p in problems), problems


def test_a_stale_file_the_row_COUNT_cannot_see_is_caught(sec_stores):
    """The case that motivated this check, and the one the EOD tables never hit.

    A SEC refresh REPLACES a payload rather than appending to it, so a restated
    figure leaves the row count untouched. The file stays present and well-formed
    and is simply wrong; only a cellwise comparison finds it. Nine real files were
    in this state after PRs #56/#57/#59 merged, with the suite green.
    """
    sec_stores.execute("UPDATE sec_company SET payload_gzip = ? WHERE ticker = 'LLY'",
                       (_payload(100.0, 999.0),))          # same 2 rows, one restated
    sec_stores.commit()

    problems = _sec_check(sec_stores)
    assert not any("differ in row count" in p for p in problems), \
        f"row count must NOT be the signal here: {problems}"
    assert any("differ cell for cell" in p and "LLY" in p for p in problems), problems


def test_a_not_ok_ticker_is_not_expected_to_have_a_file(sec_stores):
    """`sec_status != 'ok'` never gets normalized, so its absence is not a divergence."""
    sec_stores.execute("INSERT INTO sec_company VALUES ('RHHBY', 'not_mapped', NULL)")
    sec_stores.commit()
    assert _sec_check(sec_stores) == []
