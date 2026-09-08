"""AppTest smoke: every Streamlit page must render without raising.

The unit tests elsewhere in tests/ target pure functions. This one actually
EXECUTES each page script through `streamlit.testing.v1.AppTest`, which is the
only check that catches import errors, signature drift between a page and the
lib function it calls, and exceptions raised during render — i.e. exactly the
class of breakage a refactor introduces (R3 audit §8.5 regression gate).

It reads the committed `data/snapshots.db` and does no network I/O, but a cold
run of all 20 pages takes ~1-2 minutes, so it is OPT-IN under pytest:

    RUN_APPTEST=1 pytest tests/smoke_apptest.py -q      # as a test
    python tests/smoke_apptest.py                       # standalone, prints timings

Pages that legitimately need live network (Strategy Picks fetches yfinance on
load) still render — they surface an in-page error state rather than raising.
"""

from __future__ import annotations

import glob
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = REPO_ROOT / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
os.environ.setdefault("PYTHONPATH", str(_APP_DIR))


def page_paths() -> list[str]:
    """`app/home.py` first, then every page, as repo-relative paths."""
    pages = sorted(glob.glob(str(_APP_DIR / "pages" / "*.py")))
    return [str(_APP_DIR / "home.py")] + pages


def render(path: str, timeout: int = 120, **query_params) -> tuple[float, str | None, int | None]:
    """Run one page. Returns (wall_seconds, exception_text_or_None, n_elements)."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(path, default_timeout=timeout)
    for k, v in query_params.items():
        at.query_params[k] = v
    t0 = time.perf_counter()
    at.run()
    wall = time.perf_counter() - t0
    exc = "; ".join(repr(e) for e in at.exception) if at.exception else None
    try:
        n = len(at.main)
    except Exception:  # noqa: BLE001 — element count is diagnostic only
        n = None
    return wall, exc, n


_SKIP = pytest.mark.skipif(
    not os.environ.get("RUN_APPTEST"),
    reason="slow (~1-2 min for all pages); set RUN_APPTEST=1 to run",
)


@_SKIP
@pytest.mark.parametrize("path", page_paths(), ids=lambda p: Path(p).name)
def test_page_renders_without_exception(path):
    # cwd matters: pages resolve data/ relative to the repo root
    os.chdir(REPO_ROOT)
    wall, exc, _n = render(path)
    assert exc is None, f"{Path(path).name} raised during render ({wall:.2f}s): {exc}"


@_SKIP
def test_ticker_drill_renders_with_a_query_param():
    """The deep-link path (`/Ticker_Drill?ticker=LLY`) is a distinct code path."""
    os.chdir(REPO_ROOT)
    path = str(_APP_DIR / "pages" / "6_Ticker_Drill.py")
    if not Path(path).exists():
        pytest.skip("6_Ticker_Drill.py not present")
    wall, exc, _n = render(path, ticker="LLY")
    assert exc is None, f"6_Ticker_Drill?ticker=LLY raised ({wall:.2f}s): {exc}"


def main() -> int:
    """Standalone runner — prints a per-page table and returns a shell exit code."""
    os.chdir(REPO_ROOT)
    rows, failed = [], 0
    for path in page_paths():
        name = Path(path).name
        try:
            wall, exc, n = render(path)
        except Exception as e:  # noqa: BLE001 — a crash IS the result here
            wall, exc, n = float("nan"), f"{type(e).__name__}: {e}", None
        if exc:
            failed += 1
        rows.append((name, wall, n, exc))
        print(f"{name:34s} {wall:7.2f}s  n_el={str(n):>5s}  {'FAIL: ' + exc if exc else 'ok'}")
    print(f"\n{len(rows) - failed}/{len(rows)} pages rendered without exception")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
