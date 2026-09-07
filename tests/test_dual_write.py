"""Dual-write tests: every daily job must land its rows in BOTH stores.

During the cutover week SQLite is the source of truth and Parquet is a shadow. If
a job writes only one of them, jobs/parity_check.py goes red — but that is a
runtime signal on real data. These tests pin the wiring itself, on a synthetic
three-row frame, so a refactor that drops a `_pq_stage` call fails here first.

They also pin the OFF switch: `PARQUET_DUAL_WRITE=0` must leave the SQLite path
completely unchanged, because that is the documented rollback (docs/storage-migration.md).

No network: the jobs' fetch functions are never called, only their upsert paths.
Run: `pytest tests/test_dual_write.py -q` from the repo root.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from jobs import parquet_store as ps  # noqa: E402

_SCHEMA = """
CREATE TABLE prices_daily (
    ticker TEXT NOT NULL, date TEXT NOT NULL, open REAL, high REAL, low REAL,
    close REAL, adj_close REAL, volume INTEGER, currency TEXT,
    close_usd REAL, adj_close_usd REAL, PRIMARY KEY (ticker, date));
CREATE TABLE multiples_daily (
    ticker TEXT NOT NULL, date TEXT NOT NULL, market_cap_usd REAL, mcap_tier TEXT,
    trailing_pe REAL, forward_pe REAL, trailing_eps REAL, forward_eps REAL,
    ev_ebitda REAL, ev_sales REAL, fcf_yield REAL, peg REAL, pb REAL,
    ytd_return REAL, last_price REAL, last_price_usd REAL, currency TEXT,
    target_price_mean REAL, recommendation_mean REAL, n_analysts INTEGER,
    PRIMARY KEY (ticker, date));
CREATE TABLE benchmarks_daily (
    ticker TEXT NOT NULL, date TEXT NOT NULL, close REAL, PRIMARY KEY (ticker, date));
CREATE TABLE sw_industry_daily (
    ticker TEXT NOT NULL, name_cn TEXT, date TEXT NOT NULL, close REAL,
    turnover_rate REAL, market TEXT, PRIMARY KEY (ticker, date));
"""

PRICE_ROWS = [
    ("AAA", "2026-09-01", 1.0, 2.0, 0.5, 1.5, 1.5, 1000, "USD", 1.5, 1.5),
    ("BBB", "2026-09-02", 2.0, 3.0, 1.5, 2.5, 2.5, 2000, "HKD", 0.32, 0.32),
    ("AAA", "2026-08-29", 1.1, 2.1, 0.6, 1.6, 1.6, 1100, "USD", 1.6, 1.6),
]
MULT_ROWS = [
    ("AAA", "2026-09-01", 1e9, "small", 10.0, 9.0, 0.1, 0.2, 8.0, 3.0, 0.05,
     1.2, 2.0, 0.1, 1.5, 1.5, "USD", 2.0, 1.8, 7),
]
BENCH_ROWS = [("^HSI", "2026-09-01", 25000.0), ("XBI", "2026-09-01", 90.0)]
SW_ROWS = [("801780.SI", "银行", "a_share", "2026-09-05", 3000.0, 0.5)]


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("PARQUET_STORE_ROOT", str(tmp_path / "parquet"))
    monkeypatch.delenv("PARQUET_DUAL_WRITE", raising=False)
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA)
    yield conn
    conn.close()


def _sqlite_rows(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608


# ══════════════════════════════════════════════════════════════════════════
# fetch_eod — prices / multiples / benchmarks
# ══════════════════════════════════════════════════════════════════════════
def test_fetch_eod_prices_reach_both_stores(env):
    from jobs import fetch_eod

    n = fetch_eod.upsert_prices(env, PRICE_ROWS)
    env.commit()
    assert n == 3
    assert _sqlite_rows(env, "prices_daily") == 3

    # staged, not yet on disk — the flush mirrors the SQLite commit boundary
    fetch_eod._pq_flush("prices_daily")
    pq_df = ps.read_table("prices_daily").sort_values(["ticker", "date"])
    assert len(pq_df) == 3
    assert set(pq_df["ticker"]) == {"AAA", "BBB"}
    # and the rows are the same rows, not merely the same count
    sq = sorted(env.execute("SELECT ticker, date, close FROM prices_daily").fetchall())
    pqr = sorted((r.ticker, r.date, float(r.close)) for r in pq_df.itertuples())
    assert sq == pqr


def test_fetch_eod_multiples_reach_both_stores(env):
    from jobs import fetch_eod

    fetch_eod.upsert_multiples(env, MULT_ROWS)
    env.commit()
    fetch_eod._pq_flush("multiples_daily")
    assert _sqlite_rows(env, "multiples_daily") == 1
    got = ps.read_table("multiples_daily")
    assert len(got) == 1
    assert got.iloc[0]["mcap_tier"] == "small"
    assert int(got.iloc[0]["n_analysts"]) == 7


def test_fetch_eod_benchmarks_reach_both_stores(env):
    from jobs import fetch_eod

    fetch_eod.upsert_benchmarks(env, BENCH_ROWS)
    env.commit()
    fetch_eod._pq_flush("benchmarks_daily")
    assert _sqlite_rows(env, "benchmarks_daily") == 2
    assert len(ps.read_table("benchmarks_daily")) == 2


def test_prices_land_in_the_month_partition_they_belong_to(env):
    """Three rows spanning a month boundary must not all land in one file."""
    from jobs import fetch_eod

    fetch_eod.upsert_prices(env, PRICE_ROWS)
    fetch_eod._pq_flush("prices_daily")
    names = sorted(p.name for p in ps.partitions("prices_daily"))
    assert names == ["month=2026-08.parquet", "month=2026-09.parquet"]


# ══════════════════════════════════════════════════════════════════════════
# fetch_fx_world / load_sw_industry
# ══════════════════════════════════════════════════════════════════════════
def test_fx_world_upsert_reaches_both_stores(env, monkeypatch):
    from jobs import fetch_fx_world

    monkeypatch.setattr(fetch_fx_world, "_PQ_BENCH", [])
    fetch_fx_world._upsert(env, [("URTH", "2026-09-01", 180.0)])
    assert _sqlite_rows(env, "benchmarks_daily") == 1
    # this job stages and flushes once at the end of main()
    assert fetch_fx_world._PQ_BENCH == [("URTH", "2026-09-01", 180.0)]
    ps.dual_write("benchmarks_daily", fetch_fx_world._PQ_BENCH, ["ticker", "date", "close"])
    assert len(ps.read_table("benchmarks_daily")) == 1


def test_sw_industry_upsert_reaches_both_stores(env):
    from jobs import load_sw_industry

    load_sw_industry._upsert(env, SW_ROWS)
    assert _sqlite_rows(env, "sw_industry_daily") == 1
    got = ps.read_table("sw_industry_daily")
    assert len(got) == 1
    assert got.iloc[0]["market"] == "a_share"
    assert ps.partitions("sw_industry_daily")[0].name == "year=2026.parquet"


# ══════════════════════════════════════════════════════════════════════════
# the OFF switch — the documented rollback
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("value", ["0", "false", "off", "no", ""])
def test_dual_write_off_leaves_sqlite_alone_and_writes_no_parquet(env, monkeypatch, value):
    from jobs import fetch_eod, load_sw_industry

    monkeypatch.setenv("PARQUET_DUAL_WRITE", value)
    fetch_eod.upsert_prices(env, PRICE_ROWS)
    fetch_eod._pq_flush("prices_daily")
    load_sw_industry._upsert(env, SW_ROWS)

    assert _sqlite_rows(env, "prices_daily") == 3       # SQLite path unchanged
    assert _sqlite_rows(env, "sw_industry_daily") == 1
    assert ps.partitions("prices_daily") == []          # nothing shadowed
    assert ps.partitions("sw_industry_daily") == []


def test_dual_write_defaults_on_when_the_flag_is_unset(monkeypatch):
    monkeypatch.delenv("PARQUET_DUAL_WRITE", raising=False)
    assert ps.dual_write_enabled() is True


def test_a_parquet_fault_does_not_break_the_sqlite_path(env, monkeypatch, capsys):
    """SQLite is the source of truth this week; the shadow store must not kill a run."""
    from jobs import fetch_eod

    monkeypatch.setattr(ps, "upsert_rows", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    fetch_eod.upsert_prices(env, PRICE_ROWS)
    fetch_eod._pq_flush("prices_daily")          # must not raise
    assert _sqlite_rows(env, "prices_daily") == 3
    assert "dual-write to prices_daily failed" in capsys.readouterr().out
