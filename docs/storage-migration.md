# Storage migration: SQLite → partitioned Parquet

**Status: write side done, read side not started.** Both stores are live. SQLite is
still the source of truth and the app reads nothing from Parquet yet.

Source: `docs/audits/round3/2026-09-07-full-chain-audit.md` §6 / §8.2, design B.

## Why

Every data commit rewrites the whole 67 MB `data/snapshots.db`. `INSERT OR REPLACE`
reshuffles SQLite pages, so git sees a new binary file even when three rows changed.
Measured: **205 committed versions of that one file = 10.9 GB** of history, ~53 MB per
data commit, three data commits a day.

With the tables split by month, a normal EOD run rewrites the current month's
partitions — ~0.85 MB — and every older partition is byte-identical across commits, so
git stores it once, forever.

| | today | after cutover |
|---|---|---|
| bytes rewritten per data commit | 67 MB | ~0.85 MB |
| ≈250 trading days | ~50 GB/yr (observed 10.9 GB / 205 versions) | ~0.65 GB/yr |
| weekly SEC | 40 MB blob rewritten whole | only tickers that filed, ~28 KB each |

## Layout

```
data/
  parquet/
    prices_daily/      month=YYYY-MM.parquet    17 files   4.82 MB
    multiples_daily/   month=YYYY-MM.parquet     5 files   2.06 MB
    benchmarks_daily/  month=YYYY-MM.parquet    28 files   0.14 MB
    sw_industry_daily/ year=YYYY.parquet         2 files   0.04 MB
    sec_fact/          <TICKER>.parquet        284 files   8.72 MB
  snapshots.db          still the source of truth; unchanged
```
Measured 2026-09-07: **336 files, 15.78 MB**, 173,971 time-series rows + 1,146,728
SEC fact rows.

**Month, not year, for the three daily tables.** `fetch_eod.py` fetches a
`today − max(backfill,5)` window for prices and multiples and a 200-day window for
benchmarks, so a year partition would be rewritten in full on every run.
`sw_industry_daily` is a weekly committed seed — yearly is right for it.
(Design B.1 sketched `benchmarks_daily` as yearly. It is rewritten 34% per run, so it
is hot by behaviour; monthly costs +0.05 MB and buys the isolation.)

**`date` stays VARCHAR.** The app compares dates as strings (`MAX(date)`, `substr`);
a DATE column would silently change those semantics.

## Deterministic bytes — the property everything rests on

If the same rows do not serialize to the same file, git dedupes nothing and this whole
exercise buys nothing. `jobs/parquet_store.write_partition` fixes every knob that
could churn:

* stable sort on the declared primary key;
* `index=False` (a RangeIndex would serialize positions that shift on merge);
* fixed `compression="zstd"`, `write_statistics=False` (min/max stats churn the footer
  on append even when the rest is identical);
* a schema coercion, so a column that happens to be all-NULL this month does not
  serialize as a different arrow type than the same column next month;
* Parquet embeds no write timestamp — but it does embed the WRITER VERSION in
  `created_by`, which is why `requirements.txt` pins `pyarrow==24.0.0` exactly.

> ⚠️ **Bumping pyarrow re-churns every committed partition.** That is a deliberate,
> reviewable act with a one-off rewrite, not a routine dependency bump.
> `tests/test_parquet_store.py` fails loudly if determinism breaks.

Verified two ways on real data: the migration exporter re-runs byte-identical
(`--verify`, 52/52 partitions), and `jobs/load_sw_industry.py` — a completely
different code path — produces files byte-identical to the exporter's.

`sec_fact` is the one table that is **not** re-sorted. `_dedupe_by_end_date` and
`_rank` in `app/lib/sec_facts.py` are stable sorts, so rows tying on all their keys
resolve by input order; re-sorting would change which fact the app displays. Its
determinism comes from the payload's own stable key order — the same guarantee
`_load_facts` already relies on.

## Flags

| flag | default | effect |
|---|---|---|
| `PARQUET_DUAL_WRITE` | **on** | Jobs shadow every SQLite write into Parquet. `0`/`false`/`no`/`off`/empty turns it off. |
| `PARQUET_STORE_ROOT` | `data/parquet` | Store root. For tests and alternate checkouts. |

## Commands

```bash
# one-off export from SQLite (idempotent; --verify asserts bytes did not move)
python jobs/migrate_sqlite_to_parquet.py
python jobs/migrate_sqlite_to_parquet.py --verify

# rebuild the whole SEC store from the gzip blobs (~6s for 284 tickers)
python jobs/normalize_sec_facts.py
python jobs/sec_concepts.py            # what the 90 kept concepts are, and where from

# compare the two stores (this is the CI gate)
python jobs/parity_check.py
python jobs/parity_check.py --table prices_daily --max-samples 20
```

## Parity check

`jobs/parity_check.py` runs in all three data workflows **after the fetch and before
the commit**, so a divergence fails the run instead of being committed and found later
(audit §8.1). Per table: row counts → anti-join on the PK in both directions → value
equality column by column, plus a duplicate-PK scan on the Parquet side.

Current state:

```
[parity] prices_daily       OK        120,223 rows match on 11 columns
[parity] multiples_daily    OK         33,946 rows match on 20 columns
[parity] benchmarks_daily   OK         16,926 rows match on  3 columns
[parity] sw_industry_daily  OK          2,876 rows match on  6 columns
[parity] PASS — 4 table(s) identical across both stores
```

**`sec_fact` is not parity-checkable.** It shadows a BLOB, not a table, so there is no
SQLite side to anti-join against. Its guarantee is different: it is fully re-derivable
from `payload_gzip` in seconds, and `tests/test_sec_fact_normalize.py` pins its output
against the real `_load_facts` for five tickers, whole-frame and in row order.

What it gets instead is an anti-join on **filenames**, at the end of
`jobs/fetch_sec_facts.py`: every ticker whose row says `sec_status='ok'` must have a
`data/parquet/sec_fact/<TICKER>.parquet`, or the run prints the missing list and exits
non-zero (so the workflow's `if: failure()` stamp fires and the manifest does not go
green over a hole). `write_sec_fact_parquet` only warns on failure — deliberately, so
a shadow-store fault cannot kill a working fetch — and without this check that warning
would be the only trace.

The same gap is also its own reason to re-fetch: `should_refetch` returns
`(True, "parquet missing")` when the file is absent, ahead of the filing check. Without
that, a ticker that lost its file would get "no XBRL filing since ..." every week until
the company next filed — for a 10-K-only filer, a quarter.

### The local crash window — a killed backfill leaves parity red

The two stores do not commit on the same boundary. `jobs/fetch_eod.py` calls
`conn.commit()` once per batch of tickers (`fetch_eod.py:713`), but stages its Parquet
rows in `_PQ_BUF` and flushes the whole table **once, after the batch loop finishes**
(`_pq_flush("prices_daily")`, `fetch_eod.py:715`). Batching is deliberate —
`upsert_multiples` is called once per ticker, ~500× a run, and an unbuffered write
would re-read and rewrite the month partition every time — but it means a run killed
mid-loop has SQLite rows that Parquet never saw. Ctrl-C, a laptop sleeping, an OOM
kill: the window is the whole fetch.

That is survivable for a normal run and **not** survivable for a deep local backfill.
The next run fetches `today − max(--backfill-days, 5)` days, so a plain re-run only
re-stages the last five days. Everything a killed `--backfill-days 60` had already
committed to SQLite outside that window is now in one store and not the other, no
subsequent ordinary run will ever touch those rows again, and `jobs/parity_check.py`
stays red until the *same* deep backfill is repeated.

Recover by re-deriving the partitions from SQLite rather than by re-fetching — it is
seconds instead of minutes and does not depend on yfinance returning the same history:

```bash
python jobs/migrate_sqlite_to_parquet.py     # renders every partition whole from SQLite
python jobs/parity_check.py                  # must be green before committing
```

Re-running `python jobs/fetch_eod.py --backfill-days 60` also works, and is the right
choice if the interruption also left SQLite short. CI is not exposed to this: each
workflow run is a fresh checkout that either completes or commits nothing.

## Rollback

```bash
PARQUET_DUAL_WRITE=0        # in the workflow env, or the local shell
```

That is the whole rollback. SQLite is untouched by this PR — the dual write is
strictly additive, after the existing `executemany` — so with the flag off the jobs
behave exactly as they did before. `tests/test_dual_write.py` pins that. The
committed Parquet files can then be left in place (stale but harmless, since nothing
reads them) or deleted with `git rm -r data/parquet`.

**The parity check honours the same flag.** With `PARQUET_DUAL_WRITE=0` it prints

```
[parity] SKIP — dual write disabled (PARQUET_DUAL_WRITE=0)
```

and exits 0 without opening either store. That is not a courtesy: the gate runs before
"Commit data" in all three workflows, so a rolled-back pipeline — whose Parquet store
is frozen while SQLite keeps moving — would otherwise diverge within a day and fail
here, stopping the whole data pipeline on the exact path taken to get out of trouble.
Nothing reads Parquet yet, so there is nothing left to protect once the shadow write
is off. `tests/test_parity_check.py::test_main_skips_when_dual_write_is_disabled`
pins it against a deliberately divergent store.

Re-enabling the flag after a rollback leaves the Parquet store short by exactly the
rows written while it was off, and the next parity run will say so. Backfill before
re-arming the gate:

```bash
python jobs/migrate_sqlite_to_parquet.py     # idempotent; re-derives every partition
python jobs/normalize_sec_facts.py           # and the SEC store from the blobs
python jobs/parity_check.py                  # must be green before trusting CI again
```

A shadow-write fault does not fail a run on its own: it warns and lets the fetch
stand, because SQLite is still the source of truth and a working pipeline must not
die for a store nothing reads. The parity check is what turns the resulting
divergence into a red run.

## What is left — the cutover

Not started. In order:

1. **Read shim** — `DASHBOARD_DB` env var in `app/lib/db.py` selecting sqlite/duckdb;
   DuckDB views over `read_parquet`, with the six small config tables materialised
   from SQLite (design B.4). Two known hazards, both already surveyed:
   * `ORDER BY` on a nullable column — **SQLite puts NULLs first, DuckDB last.** No
     current query targets a nullable column, but the diff must compare row ORDER, not
     just set equality.
   * `PRAGMA table_info` (`db.py:84`) uses a raw sqlite3 connection; leave it.
2. **`_load_facts` reads `data/parquet/sec_fact/<TICKER>.parquet`** instead of
   decompressing the blob. The frame is already column-, order- and value-identical.
   Note `all_facts()` then covers 90 curated concepts, not 784 — decide whether to
   relabel it or keep an unprojected second parse. **Do not let it shrink silently.**
3. **`scripts/backend_diff.py`** over every loader, both backends, row order included;
   run it on every data commit for a week.
4. **Flip the default to duckdb**, keep both paths one more week.
5. **Drop `payload_gzip`**, drop the time-series tables from `init_db.py`, `VACUUM`.
   `snapshots.db` should land ≤ 2 MB.
6. **`git gc --aggressive --prune=now`** on the shared `.git` (6.16 GiB loose).
   **Do not rewrite history** — the log is the audit trail; `filter-repo` would change
   every commit SHA, break every `docs/audits/*` reference, and only reclaim blobs
   that `gc` packs anyway.

### One writer that is not here yet

Design B.8 flags `jobs/fix_splits.py:44` as a `prices_daily` writer that must move to
the Parquet helper. **That file is not on this branch** — it lives on
`fix/prices-split-adjust` (commit `adc609f`). When that branch merges it becomes a
fourth writer of `prices_daily` with no dual write, and the parity check will go red
on the first run after a split adjustment. Give it `parquet_store.upsert_rows` as part
of that merge.

Every writer that IS on this branch has the dual write:
`fetch_eod.py` (prices / multiples / benchmarks), `fetch_fx_world.py`,
`load_sw_industry.py`, `fetch_cn_benchmarks.py` (local-only, but its hand-run rows
would otherwise read as a divergence on the next CI run), and `fetch_sec_facts.py`
(sec_fact).
