"""Shared pytest setup: keep `import streamlit` meaning the real streamlit.

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

The autouse fixture below restores the real module after any test that swapped
it, and drops the `lib.*` modules that were imported against the stub so the next
test re-imports them cleanly. Tests keep their stub for their own duration; they
just stop exporting it to everyone else.
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

# Import the genuine package once, before any test can shadow it.
_REAL_STREAMLIT = importlib.import_module("streamlit")


@pytest.fixture(autouse=True)
def _restore_real_streamlit():
    yield
    if sys.modules.get("streamlit") is not _REAL_STREAMLIT:
        sys.modules["streamlit"] = _REAL_STREAMLIT
        for name in [m for m in list(sys.modules) if m == "lib" or m.startswith("lib.")]:
            del sys.modules[name]
