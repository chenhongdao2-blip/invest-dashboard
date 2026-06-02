"""Red test for the cache-key-omits-input-state bug (ccgg-uw gate).

Bug (MAJOR, cache-key-omits-input-state):
  lib.hc_overview.load_fund_positioning / positioning_source / load_index_comparison
  are zero-arg @st.cache_data(ttl=3600) functions that choose their source path via
  POS_PATH_FULL.exists() (etc.) and read file CONTENTS *inside* the cached body.

  Streamlit keys @st.cache_data by (func.__module__, func.__qualname__, source_text)
  + the HASHED ARGUMENTS only (see lib/db.py:20-25). With zero args the key is the
  empty arg tuple, so NEITHER the chosen path NOR the file mtime is part of the key.

  Defect A (frozen path): first cache miss while the gitignored FULL csv is absent
  caches the anon Fund 1-12 frame; after the full csv lands the loader keeps serving
  anon data until TTL/restart.
  Defect B (stale contents): build_hc_overview_data.py rewrites a csv in place ->
  readers get the pre-rebuild frame for up to an hour with no invalidation.

This test installs a FAITHFUL fake of @st.cache_data that keys exactly like real
Streamlit (qualname + hashed args, NOT module globals / filesystem). Under that fake
the *desired* contract is: the loaders re-read when the underlying file's path
selection or mtime changes -- which is only possible if path + mtime are HASHED ARGS.

Run: `pytest tests/test_hc_overview_cache_key.py -q` from repo root.
"""

from __future__ import annotations

import importlib
import os
import sys
import time
import types
from pathlib import Path

# Put app/ on the path at import time (mirrors tests/test_hc_positioning_na.py) so
# `lib.hc_overview` resolves when pytest is run from the repo root.
_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))


def _install_faithful_cache_stub():
    """Streamlit-faithful @st.cache_data: memoise on (qualname, args, kwargs).

    Mirrors real Streamlit: module globals and filesystem state are INVISIBLE to the
    key; only the hashed call arguments are. A zero-arg cached function therefore has
    a single immutable bucket -- exactly the trap the bug falls into.
    """
    store: dict = {}

    def cache_data(*dargs, **dkwargs):
        def make(fn):
            def wrapper(*args, **kwargs):
                key = (fn.__qualname__, args, tuple(sorted(kwargs.items())))
                if key not in store:
                    store[key] = fn(*args, **kwargs)
                return store[key]
            wrapper.__wrapped__ = fn
            wrapper.__qualname__ = fn.__qualname__
            return wrapper
        # support both @st.cache_data and @st.cache_data(ttl=...)
        if dargs and callable(dargs[0]) and not dkwargs:
            return make(dargs[0])
        return make

    st = types.ModuleType("streamlit")
    st.cache_data = cache_data
    st.session_state = {}
    sys.modules["streamlit"] = st
    return store


def _fresh_hco(tmp_path: Path):
    """Import lib.hc_overview with its data dir redirected into tmp_path."""
    _install_faithful_cache_stub()
    # reload so the faithful stub + path overrides take effect cleanly
    for m in [m for m in list(sys.modules) if m == "lib" or m.startswith("lib.")]:
        del sys.modules[m]
    hco = importlib.import_module("lib.hc_overview")

    ext = tmp_path / "external"
    ext.mkdir(parents=True, exist_ok=True)
    hco._EXT = ext
    hco.POS_PATH_FULL = ext / "china_fund_hc_positioning_full.csv"
    hco.POS_PATH = ext / "china_fund_hc_positioning.csv"
    return hco


_ANON = (
    "fund,aum_2026,fund_hc_w,ow_uw_2026,deviation_2026\n"
    "Fund 1,3.3bn,0.019,UW,-0.038\n"
)
_FULL = (
    "fund,aum_2026,fund_hc_w,ow_uw_2026,deviation_2026\n"
    "Hillhouse,3.3bn,0.019,UW,-0.038\n"
)


def test_full_file_landing_invalidates_anon_frame(tmp_path):
    """Defect A: anon frame must NOT be frozen after the full csv lands."""
    hco = _fresh_hco(tmp_path)
    hco.POS_PATH.write_text(_ANON, encoding="utf-8")

    first = hco.load_fund_positioning()
    assert first["fund"].iloc[0] == "Fund 1"

    # full csv (real names) lands while the process keeps running
    hco.POS_PATH_FULL.write_text(_FULL, encoding="utf-8")

    second = hco.load_fund_positioning()
    assert second["fund"].iloc[0] == "Hillhouse", (
        "anonymised frame stayed frozen after the full csv landed -- zero-arg cache "
        "key omits the chosen path"
    )


def test_inplace_rewrite_invalidates_contents(tmp_path):
    """Defect B: rewriting the same csv in place must invalidate the cached frame."""
    hco = _fresh_hco(tmp_path)
    hco.POS_PATH.write_text(_ANON, encoding="utf-8")

    first = hco.load_fund_positioning()
    assert abs(float(first["deviation_2026"].iloc[0]) - (-0.038)) < 1e-9

    # builder re-bakes the SAME path in place with a new deviation; bump mtime
    rewritten = _ANON.replace("-0.038", "-0.051")
    hco.POS_PATH.write_text(rewritten, encoding="utf-8")
    future = time.time() + 5
    os.utime(hco.POS_PATH, (future, future))

    second = hco.load_fund_positioning()
    assert abs(float(second["deviation_2026"].iloc[0]) - (-0.051)) < 1e-9, (
        "in-place rewrite served the pre-rebuild frame -- file mtime is not in the "
        "zero-arg cache key"
    )
