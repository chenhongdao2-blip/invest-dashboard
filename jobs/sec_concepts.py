"""The XBRL concept set the app actually consumes — 90 of the ~784 in a payload.

Two sources, and only two:
  • `sec_kpi_map.concepts_json` in the DB (12 rows → 27 concepts), read at
    app/lib/sec_facts.py:174-179 and :199-201;
  • the `tags` lists of INCOME_ROWS / BALANCE_ROWS / CASHFLOW_ROWS in
    app/lib/sec_statements.py (41 rows → 86 concepts).
Union = 90. Everything else in a companyfacts payload is dead weight for this app.

The statement tags are read by **parsing** app/lib/sec_statements.py, not importing
it. Two reasons, both practical: importing pulls streamlit and the app's db module
into a batch job that has no business booting either, and parsing cannot execute
app code as a side effect. It is deliberately brittle — if those three lists stop
being literal `tags=[...]` entries the parse raises rather than silently returning
a short set, because a silently short set would quietly drop financial line items
from every normalized file.

Concepts are compared WITHOUT their taxonomy prefix, matching what the app does:
`sec_facts._facts` filters on the bare concept and falls back across taxonomies,
so `us-gaap:Revenues` and `ifrs-full:Revenue` are both reachable for one KPI.
"""

from __future__ import annotations

import ast
import json
import sqlite3
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATEMENTS_PY = REPO_ROOT / "app" / "lib" / "sec_statements.py"
_ROW_BLOCKS = ("INCOME_ROWS", "BALANCE_ROWS", "CASHFLOW_ROWS")


def statement_tags(path: Path | None = None) -> frozenset[str]:
    """XBRL tags named by the three statement row configs. Raises if it finds none."""
    src = (path or STATEMENTS_PY).read_text(encoding="utf-8")
    tree = ast.parse(src)
    tags: set[str] = set()
    seen: set[str] = set()
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and node.targets
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in _ROW_BLOCKS):
            continue
        seen.add(node.targets[0].id)
        for row in node.value.elts:            # list of dict literals
            for key, val in zip(row.keys, row.values):
                if isinstance(key, ast.Constant) and key.value == "tags":
                    tags.update(ast.literal_eval(val))
    missing = set(_ROW_BLOCKS) - seen
    if missing or not tags:
        raise RuntimeError(
            f"could not parse statement tags from {path or STATEMENTS_PY}: "
            f"missing blocks {sorted(missing)}, {len(tags)} tags found. "
            f"The normalizer would silently drop line items — fix the parse."
        )
    return frozenset(tags)


def kpi_concepts(conn: sqlite3.Connection) -> frozenset[str]:
    """Bare concepts named by sec_kpi_map, taxonomy prefix stripped."""
    out: set[str] = set()
    for (blob,) in conn.execute("SELECT concepts_json FROM sec_kpi_map"):
        for taxconcept in json.loads(blob):
            out.add(str(taxconcept).split(":", 1)[-1])
    return frozenset(out)


@lru_cache(maxsize=4)
def _cached(db_path: str) -> frozenset[str]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return statement_tags() | kpi_concepts(conn)
    finally:
        conn.close()


def used_concepts(db_path: Path | str | None = None) -> frozenset[str]:
    """The 90 concepts to keep. Cached per DB path."""
    p = str(db_path or (REPO_ROOT / "data" / "snapshots.db"))
    return _cached(p)


if __name__ == "__main__":
    tags = statement_tags()
    conn = sqlite3.connect(REPO_ROOT / "data" / "snapshots.db")
    kpi = kpi_concepts(conn)
    print(f"statement tags: {len(tags)}")
    print(f"kpi concepts:   {len(kpi)}")
    print(f"union (KEEP):   {len(tags | kpi)}")
