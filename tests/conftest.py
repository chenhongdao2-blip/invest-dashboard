"""Shared pytest setup. Two unrelated leaks, one autouse fixture each.

1. `import streamlit` must keep meaning the real streamlit.

`tests/test_hc_overview_cache_key.py`, `test_hc_positioning_na.py` and
`test_hc_verdict_extremal.py` each install a hand-written stub module as
`sys.modules["streamlit"]` (they need a faithful `cache_data` they can inspect)
and never take it back out. That leaks: every test collected after them sees the
stub, so anything needing the real package — `from streamlit.testing.v1 import
AppTest`, most obviously — dies with

    ModuleNotFoundError: No module named 'streamlit.testing';
    'streamlit' is not a package

which is an artifact of collection order, not a real failure. The suite only got
away with it because the one AppTest file (smoke_apptest.py) is opt-in behind
RUN_APPTEST and so never ran alongside them.

`_restore_real_streamlit` restores the real module after any test that swapped
it, and drops the `lib.*` modules that were imported against the stub so the next
test re-imports them cleanly. Tests keep their stub for their own duration; they
just stop exporting it to everyone else.

2. The suite must stay out of the committed Parquet store.

The dual write (PR4) gave the job functions a second side effect: `run_multiples`,
`upsert_prices` and friends now write to `data/parquet/` as well as to whatever
SQLite connection the caller passed. Tests hand them an in-memory database, which
isolates the SQLite half — and nothing isolated the other half.

That is not hypothetical. `tests/test_audit_r3.py::test_r2_gross_divergence_counts_as_unusable`
feeds `run_multiples` nine synthetic tickers named T0..T8; before this file existed,
running the suite wrote nine junk rows into `data/parquet/multiples_daily/month=2026-09.parquet`
and `jobs/parity_check.py` went red on them. The gate did its job; `_isolate_parquet_store`
removes the reason it had to.

Isolation is the default and opt-out is explicit: a module that genuinely needs to
read the committed store sets `USES_COMMITTED_PARQUET_STORE = True` at module level
(only `test_sec_fact_normalize.py` does, and only to read).

The two fixtures are orthogonal — one owns `sys.modules`, the other owns an env
var — so they compose in any order.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = REPO_ROOT / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

_COMMITTED = REPO_ROOT / "data" / "parquet"

# Import the genuine package once, before any test can shadow it.
_REAL_STREAMLIT = importlib.import_module("streamlit")


@pytest.fixture(autouse=True)
def _restore_real_streamlit():
    yield
    if sys.modules.get("streamlit") is not _REAL_STREAMLIT:
        sys.modules["streamlit"] = _REAL_STREAMLIT
        for name in [m for m in list(sys.modules) if m == "lib" or m.startswith("lib.")]:
            del sys.modules[name]


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
