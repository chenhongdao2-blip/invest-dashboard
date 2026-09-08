"""Tests for jobs/parquet_store.py — the three properties the design rests on.

1. byte-determinism: same frame written twice → identical sha256
2. idempotent upsert: upserting the same rows twice → identical bytes
3. partition isolation: upserting September must not touch the August file

Each of those is load-bearing. If (1) fails, git dedupes nothing and the whole
storage split buys nothing. If (2) fails, a re-run of a job produces a data commit
with no data change. If (3) fails, we are back to rewriting the whole table daily.

No network, no repo data — everything is a small synthetic frame under tmp_path.
Run: `pytest tests/test_parquet_store.py -q` from the repo root.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pytest

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from jobs import parquet_store as ps  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("PARQUET_STORE_ROOT", str(tmp_path / "parquet"))
    return ps


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _prices(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["ticker", "date", "close"])


AUG = [("AAA", "2026-08-28", 10.0), ("BBB", "2026-08-28", 20.0),
       ("AAA", "2026-08-29", 10.5)]
SEP = [("AAA", "2026-09-01", 11.0), ("BBB", "2026-09-01", 21.0)]


# ══════════════════════════════════════════════════════════════════════════
# 1. deterministic bytes
# ══════════════════════════════════════════════════════════════════════════
def test_write_partition_is_byte_deterministic(store, tmp_path):
    df = _prices(AUG)
    p = store.write_partition("prices_daily", "2026-08", df)
    first = _sha(p)
    p2 = store.write_partition("prices_daily", "2026-08", df)
    assert p2 == p
    assert _sha(p2) == first


def test_row_order_in_does_not_change_bytes_out(store):
    """The declared sort is what makes the bytes stable, not the caller's ordering."""
    a = store.write_partition("prices_daily", "2026-08", _prices(AUG))
    sha_a = _sha(a)
    shuffled = _prices(list(reversed(AUG)))
    b = store.write_partition("prices_daily", "2026-08", shuffled)
    assert _sha(b) == sha_a


def test_all_null_column_serializes_like_a_typed_column(store):
    """A partition whose `volume` is entirely NULL must not drift to another type.

    Without the schema coercion, pandas infers object/float64 depending on the day's
    data and the same logical partition re-churns bytes for no reason.
    """
    df = _prices(AUG)
    df["volume"] = None
    a = store.write_partition("prices_daily", "2026-08", df)
    sha_null = _sha(a)

    df2 = _prices(AUG)
    df2["volume"] = pd.array([None, None, None], dtype="Int64")
    b = store.write_partition("prices_daily", "2026-08", df2)
    assert _sha(b) == sha_null
    assert store.read_partition("prices_daily", "2026-08")["volume"].dtype == "Int64"


def test_the_footer_carries_no_pandas_metadata(store):
    """`requirements.txt` allows pandas >=2.2,<3, so its version cannot be in the file.

    `store_schema=True` embeds an `ARROW:schema` and a `pandas` key, and the latter
    records `pandas_version` verbatim. A routine 2.3.3 → 2.4.0 bump would then change
    the bytes of every partition a job rewrites, while every untouched partition kept
    the old string — churn with no data change, which is the exact thing the split
    exists to stop, arriving through the one pin the file does NOT hold exactly.

    Dropping the metadata is safe because `coerce()` reimposes the declared dtypes on
    every read; nothing downstream consults the footer. The two tests below prove that
    for the cases where the metadata would otherwise be load-bearing.
    """
    import pyarrow.parquet as pyq

    p = store.write_partition("prices_daily", "2026-08", _prices(AUG))
    md = pyq.ParquetFile(p).metadata.metadata or {}
    assert b"pandas" not in md, "a pandas bump would re-churn every partition"
    assert b"ARROW:schema" not in md


def test_dtypes_survive_the_round_trip_without_the_metadata(store):
    """`coerce()` on read, not the footer, is what restores the declared dtypes."""
    df = _prices(AUG)
    df["volume"] = pd.array([1, None, 3], dtype="Int64")
    df["currency"] = ["USD", None, "HKD"]
    store.write_partition("prices_daily", "2026-08", df)

    got = store.read_partition("prices_daily", "2026-08")
    assert dict(got.dtypes.astype(str)) == dict(ps.TABLES["prices_daily"].dtypes)
    assert got["currency"].isna().sum() == 1
    assert got["volume"].isna().sum() == 1


def test_an_all_null_string_column_reads_back_as_string_not_object(store):
    """The nastiest case: with no metadata an all-NULL string column arrives as
    object/None, and only `coerce()` puts it back to string/pd.NA."""
    df = _prices(AUG)
    df["currency"] = None
    store.write_partition("prices_daily", "2026-08", df)

    got = store.read_partition("prices_daily", "2026-08")
    assert got["currency"].dtype == "string"
    assert got["currency"].isna().all()


# ══════════════════════════════════════════════════════════════════════════
# 2. idempotent upsert
# ══════════════════════════════════════════════════════════════════════════
def test_upsert_twice_is_byte_identical(store):
    store.upsert_rows("prices_daily", _prices(AUG))
    p = store.partition_path("prices_daily", "2026-08")
    first = _sha(p)
    store.upsert_rows("prices_daily", _prices(AUG))
    assert _sha(p) == first


def test_upsert_replaces_on_primary_key(store):
    """INSERT OR REPLACE semantics: same (ticker, date) → the new row wins."""
    store.upsert_rows("prices_daily", _prices(AUG))
    store.upsert_rows("prices_daily", _prices([("AAA", "2026-08-28", 99.0)]))
    got = store.read_partition("prices_daily", "2026-08")
    assert len(got) == 3          # replaced, not appended
    row = got[(got.ticker == "AAA") & (got.date == "2026-08-28")]
    assert float(row["close"].iloc[0]) == 99.0


def test_upsert_returns_rows_per_partition(store):
    written = store.upsert_rows("prices_daily", _prices(AUG + SEP))
    assert written == {"2026-08": 3, "2026-09": 2}


# ══════════════════════════════════════════════════════════════════════════
# 3. partition isolation
# ══════════════════════════════════════════════════════════════════════════
def test_upserting_september_leaves_august_byte_identical(store):
    store.upsert_rows("prices_daily", _prices(AUG))
    aug = store.partition_path("prices_daily", "2026-08")
    sha_aug = _sha(aug)
    mtime_aug = aug.stat().st_mtime_ns

    store.upsert_rows("prices_daily", _prices(SEP))

    assert _sha(aug) == sha_aug, "August partition was rewritten by a September upsert"
    assert aug.stat().st_mtime_ns == mtime_aug, "August partition was reopened for write"
    assert store.partition_path("prices_daily", "2026-09").exists()


# ══════════════════════════════════════════════════════════════════════════
# partition key resolution
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "table,value,expected_name",
    [
        ("prices_daily", "2026-09-04", "month=2026-09.parquet"),
        ("multiples_daily", "2026-09-04", "month=2026-09.parquet"),
        ("benchmarks_daily", "2026-09-04", "month=2026-09.parquet"),
        ("sw_industry_daily", "2026-09-04", "year=2026.parquet"),
    ],
)
def test_partition_layout(store, table, value, expected_name):
    key = store.partition_key(table, value)
    p = store.partition_path(table, key)
    assert p.name == expected_name
    assert p.parent.name == table


def test_sec_fact_partitions_per_ticker(store):
    key = store.partition_key("sec_fact", "AAPL")
    assert store.partition_path("sec_fact", key).name == "AAPL.parquet"


def test_partition_key_rejects_a_path_traversal(store):
    with pytest.raises(ValueError):
        store.partition_key("sec_fact", "../../etc/passwd")


def test_bad_date_is_a_loud_error_not_a_silent_partition(store):
    with pytest.raises(ValueError):
        store.partition_key("prices_daily", "not-a-date")


@pytest.mark.parametrize("bad", ["2026-13-01", "2026-00-01", "2026-99-01"])
def test_an_impossible_month_is_rejected(store, bad):
    """A month outside 01..12 is a corrupt date, not a partition.

    `\\d{4}-\\d{2}` matched it happily and wrote `month=2026-13.parquet`, which
    then sorts after every real December and is invisible to any month-range
    scan — the file exists, reads fine, and nothing ever looks at it again.
    """
    with pytest.raises(ValueError, match="cannot derive month partition"):
        store.partition_key("prices_daily", bad)


@pytest.mark.parametrize("good", ["2026-01-31", "2026-09-04", "2026-12-31"])
def test_the_real_months_still_resolve(store, good):
    assert store.partition_key("prices_daily", good) == good[:7]


@pytest.mark.parametrize("null", [None, float("nan"), pd.NA])
def test_a_null_primary_key_is_refused(store, null):
    """SQLite declares `ticker TEXT NOT NULL` and would reject the row outright.

    Parquet has no such declaration, so the row would land — and then
    `drop_duplicates` treats two NAs as equal, so a second null-keyed row for
    another date silently replaces the first. The shadow store must not accept
    what the source of truth refuses.
    """
    df = _prices([("AAA", "2026-08-28", 10.0)])
    df.loc[0, "ticker"] = null
    with pytest.raises(ValueError, match="NULL in primary key"):
        store.upsert_rows("prices_daily", df)
    assert store.partitions("prices_daily") == [], "nothing may be written"


def test_a_null_in_a_non_key_column_is_fine(store):
    """Only the key is constrained — a missing close is ordinary data."""
    df = _prices([("AAA", "2026-08-28", 10.0)])
    df.loc[0, "close"] = None
    store.upsert_rows("prices_daily", df)
    assert len(store.read_partition("prices_daily", "2026-08")) == 1


def test_sec_fact_has_no_merge_key(store):
    """sec_fact is rewritten whole from the payload; upsert_rows must refuse it."""
    with pytest.raises(ValueError, match="no merge key"):
        store.upsert_rows("sec_fact", pd.DataFrame({"ticker": ["AAPL"]}))


# ══════════════════════════════════════════════════════════════════════════
# read path
# ══════════════════════════════════════════════════════════════════════════
def test_read_table_spans_partitions(store):
    store.upsert_rows("prices_daily", _prices(AUG + SEP))
    got = store.read_table("prices_daily").sort_values(["ticker", "date"])
    assert len(got) == 5
    assert set(got["ticker"]) == {"AAA", "BBB"}


def test_read_table_where_filters(store):
    store.upsert_rows("prices_daily", _prices(AUG + SEP))
    got = store.read_table("prices_daily", where="date >= '2026-09-01'")
    assert len(got) == 2


def test_read_table_on_empty_store_is_typed_not_an_exception(store):
    got = store.read_table("prices_daily")
    assert got.empty
    assert list(got.columns) == list(ps.TABLES["prices_daily"].dtypes)


def test_column_order_matches_the_declared_schema(store):
    store.upsert_rows("prices_daily", _prices(AUG))
    got = store.read_partition("prices_daily", "2026-08")
    assert list(got.columns) == list(ps.TABLES["prices_daily"].dtypes)
