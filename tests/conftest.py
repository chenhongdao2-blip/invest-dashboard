"""Keep the test suite out of the committed Parquet store.

The dual write (PR4) gave the job functions a second side effect: `run_multiples`,
`upsert_prices` and friends now write to `data/parquet/` as well as to whatever
SQLite connection the caller passed. Tests hand them an in-memory database, which
isolates the SQLite half — and nothing isolated the other half.

That is not hypothetical. `tests/test_audit_r3.py::test_r2_gross_divergence_counts_as_unusable`
feeds `run_multiples` nine synthetic tickers named T0..T8; before this file existed,
running the suite wrote nine junk rows into `data/parquet/multiples_daily/month=2026-09.parquet`
and `jobs/parity_check.py` went red on them. The gate did its job; this fixture
removes the reason it had to.

Isolation is the default and opt-out is explicit: a module that genuinely needs to
read the committed store sets `USES_COMMITTED_PARQUET_STORE = True` at module level
(only `test_sec_fact_normalize.py` does, and only to read).
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_COMMITTED = _REPO / "data" / "parquet"


@pytest.fixture(autouse=True)
def _isolate_parquet_store(request, tmp_path_factory, monkeypatch):
    """Point PARQUET_STORE_ROOT at a temp dir for every test that does not opt out."""
    if getattr(request.module, "USES_COMMITTED_PARQUET_STORE", False):
        # Set explicitly rather than left alone, so a stray env var in the shell
        # cannot silently redirect a test that means to read the real store.
        monkeypatch.setenv("PARQUET_STORE_ROOT", str(_COMMITTED))
    else:
        monkeypatch.setenv("PARQUET_STORE_ROOT",
                           str(tmp_path_factory.mktemp("parquet_store")))
