"""Every literal key passed to i18n.t() in app/ must exist in the locale tables.

The en/zh parity test cannot catch a call site that asks for a key neither
table defines: t() falls back to the key itself and the UI silently shows the
literal string (2026-09-07: "scan.filters.sectors" rendered as a label on both
Valuation Scanner pages after a page merge).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_APP = _REPO / "app"
_KEY_RE = re.compile(r"""\bt\(\s*["']([A-Za-z0-9_.\-]+)["']""")


def _all_keys() -> set[str]:
    sys.path.insert(0, str(_APP))
    from lib import i18n  # noqa: PLC0415

    keys: set[str] = set()
    for table in i18n._TABLES.values():
        keys.update(table)
    return keys


def test_every_literal_t_key_exists_in_a_locale_table():
    keys = _all_keys()
    missing: list[tuple[str, int, str]] = []
    for path in _APP.rglob("*.py"):
        if "locales" in path.parts or path.name == "i18n.py":
            continue
        for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for key in _KEY_RE.findall(line):
                if key not in keys:
                    missing.append((str(path.relative_to(_REPO)), ln, key))
    assert not missing, "t() called with keys no locale defines:\n" + "\n".join(
        f"  {f}:{n}  {k}" for f, n, k in missing
    )
