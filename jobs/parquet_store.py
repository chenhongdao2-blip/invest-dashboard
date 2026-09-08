"""Partitioned Parquet store for the time-series tables (audit R3 §6 / §8.2, design B).

WHY — every data commit today rewrites the whole 67 MB `data/snapshots.db`, because
`INSERT OR REPLACE` reshuffles SQLite pages and git sees a new binary file. Measured:
205 committed versions of that one file = 10.9 GB of history. Splitting the four
time-series tables into per-month/per-year Parquet partitions means a normal run
rewrites ~0.85 MB, older partitions freeze permanently, and git dedupes them forever.

Three properties this module exists to guarantee, in priority order:

1. **Deterministic bytes.** The same logical rows must serialize to the same file,
   byte for byte, or git dedupes nothing and the whole exercise is pointless. The
   recipe is in `write_partition`: stable sort on the declared key, `index=False`,
   fixed `compression="zstd"`, `write_statistics=False` (min/max stats churn the
   footer when a row is appended even if the rest is identical), `store_schema=False`
   (the `pandas` footer key records `pandas_version`, and pandas is NOT pinned
   exactly), and a schema coercion so a partition whose column happens to be all-NaN
   today does not serialize as a different arrow type than the same column tomorrow.
   Parquet embeds no write timestamp, so nothing else leaks — but the writer
   VERSION is embedded in `created_by`, which is why `requirements.txt` pins
   pyarrow exactly. An unpinned bump silently re-churns every partition.

2. **Atomic replacement.** temp file + `os.replace` in the same directory. A
   half-written 70 MB SQLite file was a real failure mode (audit H4); a
   half-written partition is not reachable.

3. **`INSERT OR REPLACE` semantics.** `upsert_rows` merges on the declared primary
   key with `keep="last"`, which is exactly what the SQLite writes it shadows do
   (`fetch_eod.py`, `fetch_fx_world.py`, `load_sw_industry.py`).

`date` stays a VARCHAR in the parquet schema, deliberately: the app compares dates
as strings (`MAX(date)`, `substr`) and a DATE column would silently change those
semantics.

Layout (`data/parquet/<table>/<partition>.parquet`):

    prices_daily/      month=YYYY-MM.parquet
    multiples_daily/   month=YYYY-MM.parquet
    benchmarks_daily/  month=YYYY-MM.parquet
    sw_industry_daily/ year=YYYY.parquet
    sec_fact/          <TICKER>.parquet

Month rather than year for the three hot tables because `fetch_eod.py` fetches a
`today − max(backfill,5)` window for prices/multiples and a 200-day window for
benchmarks: with year partitions every run would rewrite the whole current year.
`sw_industry_daily` is a weekly committed seed — yearly is fine.

(Design B.1 sketched `benchmarks_daily` as yearly. It is written with a 200-day
rolling window on every EOD run — 34% of the table per run, audit §6 — so it is a
hot table by behaviour, not a cold one; it is partitioned monthly here for that
reason.)

Root override for tests / alternate checkouts: `PARQUET_STORE_ROOT`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

# Fixed writer settings. Changing ANY of these re-churns every partition — that is
# a deliberate, reviewable act, not something to tune per call site.
COMPRESSION = "zstd"
_WRITE_KWARGS = dict(
    engine="pyarrow",
    compression=COMPRESSION,
    index=False,             # a RangeIndex would serialize positions that shift on merge
    write_statistics=False,  # min/max stats churn the footer on append
    # No `ARROW:schema` / `pandas` footer keys. The `pandas` one records
    # `pandas_version` verbatim, and requirements.txt allows pandas >=2.2,<3 — so a
    # routine minor bump would change the bytes of every partition a job rewrites
    # while untouched partitions kept the old string. That is churn with no data
    # change, arriving through the one dependency the file does not pin exactly.
    # Safe to drop because `coerce()` reimposes the declared dtypes on every read;
    # nothing downstream consults the footer, and DuckDB never did.
    store_schema=False,
)

# Partition keys are used as filenames. Tickers legitimately carry '.', '^', '=' and
# '-' (^HSI, CNY=X, 600519.SS, BRK-B); nothing else is allowed near the filesystem.
_SAFE_KEY = re.compile(r"^[A-Za-z0-9._^=-]+$")


@dataclass(frozen=True)
class TableSpec:
    """How one table is partitioned, keyed, sorted and typed."""

    part_kind: str          # 'month' | 'year' | 'value'
    part_column: str        # column the partition key is derived from
    pk: tuple[str, ...] | None   # merge key for upsert_rows; None = whole-partition replace
    sort: tuple[str, ...] | None  # stable sort before writing; None = preserve input order
    dtypes: dict[str, str]  # declared schema, in column order


_TEXT = "string"
_F64 = "float64"
_I64 = "Int64"

# `_FACT_COLS` in app/lib/sec_facts.py — kept verbatim (name AND order), the FULL
# 15, deliberately WIDER than the 13 `_load_facts` returns. See jobs/normalize_sec_facts.py.
#
# PR #57 narrowed the read path to `_KPI_FACT_COLS` (= `_FACT_COLS` minus `value_text`
# and `frame`) because the unprojected frame plus its `@st.cache_data` pickle was the
# 1 GB Streamlit Cloud OOM path. That is a statement about what to hold in RAM, not
# about what belongs at rest, and the store does not follow it. The two are kept here
# on purpose:
#
#   • `frame` — the SEC's own calendar-period label ("CY2009Q2I"). Non-empty on
#     419,022 of the store's 1,146,728 rows (36.5%): filed content, not padding.
#     `_load_facts_full` still returns it, and it is the only place the canonical
#     period id survives without re-deriving it from start_date/end_date/fp.
#   • `value_text` — where `_parse_facts` puts a non-numeric fact value, NULLing
#     `value`. Empty across all 1.15M kept rows today, so it costs nothing; the day a
#     filer tags a kept concept with a string, a store without this column would
#     record a NULL and no way to tell why.
#
# The asymmetry is the whole argument: a read shim narrows the store in one line
# (`df[_KPI_FACT_COLS]`), but nothing can widen a column that was never written — and
# this store's destiny is to REPLACE `sec_company.payload_gzip` (audit §6), after which
# whatever it omits is gone. Measured cost of carrying both: 0.417 MB on 7.25 MB (6.1%).
# tests/test_sec_fact_normalize.py pins the superset relation in both directions.
_SEC_FACT_DTYPES = {
    "taxonomy": _TEXT, "concept": _TEXT, "label": _TEXT, "unit": _TEXT,
    "value": _F64, "value_text": _TEXT, "start_date": _TEXT, "end_date": _TEXT,
    "instant": _I64, "fy": _I64, "fp": _TEXT, "form": _TEXT,
    "filed": _TEXT, "accession": _TEXT, "frame": _TEXT,
}

TABLES: dict[str, TableSpec] = {
    "prices_daily": TableSpec(
        part_kind="month", part_column="date",
        pk=("ticker", "date"), sort=("ticker", "date"),
        dtypes={
            "ticker": _TEXT, "date": _TEXT, "open": _F64, "high": _F64, "low": _F64,
            "close": _F64, "adj_close": _F64, "volume": _I64, "currency": _TEXT,
            "close_usd": _F64, "adj_close_usd": _F64,
        },
    ),
    "multiples_daily": TableSpec(
        part_kind="month", part_column="date",
        pk=("ticker", "date"), sort=("ticker", "date"),
        dtypes={
            "ticker": _TEXT, "date": _TEXT, "market_cap_usd": _F64, "mcap_tier": _TEXT,
            "trailing_pe": _F64, "forward_pe": _F64, "trailing_eps": _F64,
            "forward_eps": _F64, "ev_ebitda": _F64, "ev_sales": _F64, "fcf_yield": _F64,
            "peg": _F64, "pb": _F64, "ytd_return": _F64, "last_price": _F64,
            "last_price_usd": _F64, "currency": _TEXT, "target_price_mean": _F64,
            "recommendation_mean": _F64, "n_analysts": _I64,
        },
    ),
    "benchmarks_daily": TableSpec(
        part_kind="month", part_column="date",
        pk=("ticker", "date"), sort=("ticker", "date"),
        dtypes={"ticker": _TEXT, "date": _TEXT, "close": _F64},
    ),
    "sw_industry_daily": TableSpec(
        part_kind="year", part_column="date",
        # PRIMARY KEY (ticker, date) in the DDL — `market` is NOT part of it.
        pk=("ticker", "date"), sort=("ticker", "date"),
        dtypes={
            "ticker": _TEXT, "name_cn": _TEXT, "date": _TEXT,
            "close": _F64, "turnover_rate": _F64, "market": _TEXT,
        },
    ),
    "sec_fact": TableSpec(
        part_kind="value", part_column="ticker",
        # One ticker = one file, rewritten whole from the companyfacts payload.
        # No merge key: the payload is the unit of truth, not individual rows.
        pk=None,
        # sort=None on purpose. `_dedupe_by_end_date` / `_rank` in app/lib/sec_facts.py
        # are STABLE sorts (kind="mergesort"), so a row that ties on all their sort
        # keys is resolved by input order. Re-sorting here would change which fact the
        # app picks in that tie. Determinism comes from the payload's own stable key
        # order — the same guarantee `_load_facts` already relies on today.
        sort=None,
        dtypes=_SEC_FACT_DTYPES,
    ),
}

_PREFIX = {"month": "month=", "year": "year=", "value": ""}


# ──────────────────────────────────────────────────────────────────────────
# paths
# ──────────────────────────────────────────────────────────────────────────
def root() -> Path:
    """Parquet root. `PARQUET_STORE_ROOT` overrides (tests, alternate checkouts)."""
    env = os.environ.get("PARQUET_STORE_ROOT")
    return Path(env) if env else REPO_ROOT / "data" / "parquet"


def _spec(table: str) -> TableSpec:
    try:
        return TABLES[table]
    except KeyError:
        raise KeyError(f"unknown table {table!r}; known: {sorted(TABLES)}") from None


def partition_key(table: str, value: str) -> str:
    """Partition key for one `part_column` value ('2026-09-04' -> '2026-09')."""
    spec = _spec(table)
    v = str(value)
    if spec.part_kind == "month":
        key = v[:7]
        # 01..12, not \d{2}: a `month=2026-13.parquet` reads fine and sorts after
        # every real December, so a corrupt date would land in a file nothing ever
        # scans again rather than failing where it was introduced.
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", key):
            raise ValueError(f"{table}: cannot derive month partition from {value!r}")
    elif spec.part_kind == "year":
        key = v[:4]
        if not re.fullmatch(r"\d{4}", key):
            raise ValueError(f"{table}: cannot derive year partition from {value!r}")
    else:
        key = v
    if not _SAFE_KEY.fullmatch(key):
        raise ValueError(f"{table}: unsafe partition key {key!r}")
    return key


def partition_path(table: str, key: str) -> Path:
    """`data/parquet/<table>/<prefix><key>.parquet`."""
    spec = _spec(table)
    if not _SAFE_KEY.fullmatch(str(key)):
        raise ValueError(f"{table}: unsafe partition key {key!r}")
    return root() / table / f"{_PREFIX[spec.part_kind]}{key}.parquet"


def partitions(table: str) -> list[Path]:
    """Existing partition files for a table, sorted by name."""
    d = root() / table
    return sorted(d.glob("*.parquet")) if d.is_dir() else []


# ──────────────────────────────────────────────────────────────────────────
# schema
# ──────────────────────────────────────────────────────────────────────────
def coerce(table: str, df: pd.DataFrame) -> pd.DataFrame:
    """Project onto the declared schema (column order + dtypes).

    This is a determinism requirement, not tidiness: without it a partition whose
    `volume` happens to be all-NULL this month serializes as a different arrow type
    than the same column next month, and every downstream merge re-churns bytes.
    Unknown columns are dropped; missing ones are created empty.
    """
    spec = _spec(table)
    out = pd.DataFrame(index=pd.RangeIndex(len(df)))
    src = df.reset_index(drop=True)
    for col, dt in spec.dtypes.items():
        if col in src.columns:
            s = src[col]
        else:
            s = pd.Series([None] * len(src), dtype="object")
        if dt == _I64:
            # float64-with-NaN is what read_sql hands back for a nullable INTEGER.
            out[col] = pd.to_numeric(s, errors="coerce").astype("Float64").astype(_I64)
        elif dt == _F64:
            out[col] = pd.to_numeric(s, errors="coerce").astype(_F64)
        else:
            out[col] = s.astype("object").astype(_TEXT)
    return out


def empty_frame(table: str) -> pd.DataFrame:
    """Typed, zero-row frame for a table (what readers get when nothing is stored)."""
    return coerce(table, pd.DataFrame(columns=list(_spec(table).dtypes)))


# ──────────────────────────────────────────────────────────────────────────
# write
# ──────────────────────────────────────────────────────────────────────────
def write_partition(table: str, key: str, df: pd.DataFrame) -> Path:
    """Serialize `df` as the WHOLE content of one partition. Deterministic + atomic.

    Callers that mean "add these rows" want `upsert_rows`; this one replaces.
    """
    spec = _spec(table)
    path = partition_path(table, key)
    path.parent.mkdir(parents=True, exist_ok=True)

    out = coerce(table, df)
    if spec.sort:
        out = out.sort_values(list(spec.sort), kind="mergesort").reset_index(drop=True)

    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    try:
        out.to_parquet(tmp, **_WRITE_KWARGS)
        os.replace(tmp, path)   # atomic within the filesystem
    finally:
        if tmp.exists():
            tmp.unlink()
    return path


def read_partition(table: str, key: str) -> pd.DataFrame:
    """One partition, or a typed empty frame when it does not exist yet."""
    path = partition_path(table, key)
    if not path.exists():
        return empty_frame(table)
    return coerce(table, pd.read_parquet(path))


def upsert_rows(table: str, df: pd.DataFrame) -> dict[str, int]:
    """`INSERT OR REPLACE` onto the partitions the rows touch. New rows win.

    Returns {partition_key: rows_in_partition_after_merge}. Partitions the frame
    does not touch are not opened, let alone rewritten — that is the whole point.
    """
    spec = _spec(table)
    if spec.pk is None:
        raise ValueError(
            f"{table} has no merge key — it is written whole-partition; "
            f"use write_partition({table!r}, key, df)"
        )
    if df is None or len(df) == 0:
        return {}

    rows = coerce(table, df)

    # SQLite declares every PK column NOT NULL and would reject these outright.
    # Parquet declares nothing, so they would land — and then `drop_duplicates`
    # below treats two NAs as equal, so a second null-keyed row silently replaces
    # the first. Checked after `coerce` so every flavour of null (None, NaN, pd.NA)
    # has already collapsed to one. Nothing is written: the whole frame is refused,
    # not partially applied.
    null_pk = [c for c in spec.pk if rows[c].isna().any()]
    if null_pk:
        n = int(rows[list(spec.pk)].isna().any(axis=1).sum())
        raise ValueError(
            f"{table}: {n} row(s) with NULL in primary key column(s) "
            f"{null_pk} — SQLite would reject these; refusing the whole frame"
        )

    keys = rows[spec.part_column].map(lambda v: partition_key(table, v))

    written: dict[str, int] = {}
    for key, chunk in rows.groupby(keys, sort=True):
        old = read_partition(table, key)
        merged = pd.concat([old, chunk], ignore_index=True) if len(old) else chunk
        merged = merged.drop_duplicates(subset=list(spec.pk), keep="last")
        write_partition(table, key, merged)
        written[str(key)] = len(merged)
    return written


# ──────────────────────────────────────────────────────────────────────────
# dual write (transition period — SQLite stays the source of truth)
# ──────────────────────────────────────────────────────────────────────────
DUAL_WRITE_ENV = "PARQUET_DUAL_WRITE"
_OFF = {"", "0", "false", "no", "off"}


def dual_write_enabled() -> bool:
    """Is the Parquet shadow write on? Default ON; `PARQUET_DUAL_WRITE=0` turns it off.

    The flag exists to DISABLE, not to enable: during the dual-write week every job
    must populate both stores or the parity check is meaningless. It is the rollback
    lever — set it to 0 and the jobs behave exactly as they did before this PR.
    """
    return os.environ.get(DUAL_WRITE_ENV, "1").strip().lower() not in _OFF


def dual_write(table: str, rows, columns: list[str] | None = None) -> dict[str, int]:
    """Shadow-write rows that were just committed to SQLite. Never raises.

    `rows` is a DataFrame, or a list of tuples plus `columns`.

    WHY it swallows exceptions: SQLite is still the source of truth this week, and a
    fault in the shadow store must not take down a working data pipeline. That is not
    the same as failing silently — jobs/parity_check.py runs in the workflow after the
    fetch and before the commit, so anything this call fails to write shows up as a
    row-count/anti-join divergence and turns the run red. The loud signal lives where
    it can check the OUTCOME rather than the mechanism.
    """
    if not dual_write_enabled():
        return {}
    try:
        df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows), columns=columns)
        if len(df) == 0:
            return {}
        return upsert_rows(table, df)
    except Exception as e:  # noqa: BLE001 — see docstring
        print(f"[parquet] WARNING dual-write to {table} failed ({type(e).__name__}: {e}); "
              f"SQLite is unaffected — jobs/parity_check.py will flag the divergence")
        return {}


# ──────────────────────────────────────────────────────────────────────────
# read
# ──────────────────────────────────────────────────────────────────────────
def read_table(table: str, where: str | None = None) -> pd.DataFrame:
    """Whole table across partitions, via DuckDB `read_parquet`.

    `where` is a raw SQL predicate spliced into the query — for jobs and tests,
    which supply their own literals. It is NOT a user-input path; do not wire it
    to anything that takes external strings.
    """
    _spec(table)
    files = partitions(table)
    if not files:
        return empty_frame(table)

    import duckdb  # local import: the app must not pay for it at module scope

    glob = str(root() / table / "*.parquet")
    sql = f"SELECT * FROM read_parquet('{glob}')"
    if where:
        sql += f" WHERE {where}"
    con = duckdb.connect(":memory:")
    try:
        return coerce(table, con.execute(sql).df())
    finally:
        con.close()
