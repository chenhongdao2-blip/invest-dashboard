"""The XBRL concepts the app actually reads.

`_load_facts` used to materialise EVERY concept in a company's companyfacts
payload — 784 of them for ELV, 40,102 rows, 30.55 MB resident, doubled by
Streamlit's pickle copy. A 10-ticker comp table therefore carried ~600 MB, which
is the 1 GB Streamlit Cloud OOM path in R3 audit §5.

The set the KPI and statement paths can ever ask for is small and fully
enumerable, and it lives in exactly two places:

* `sec_kpi_map.concepts_json` in the DB — the KPI fallback chains, as
  "taxonomy:concept" strings (`sec_facts.kpis_for_domain`);
* `sec_statements.{INCOME,BALANCE,CASHFLOW}_ROWS` — each row's `tags` list.

Both are read here so ONE grep answers "what do we keep". Adding a KPI row to the
DB or a tag to a statement row widens the projection automatically; nothing else
has to change.

This does NOT cover the full XBRL browser (`sec_facts.all_facts`) or
`sec_statements.dominant_monetary_unit`, which histograms units across every
concept a filer reports. Those read the unprojected parse — see
`sec_facts._load_facts_full`.
"""

from __future__ import annotations

import json

import streamlit as st

from lib import db


@st.cache_data(ttl=600)
def used_concepts() -> frozenset[str]:
    """Bare concept names (taxonomy stripped) reachable from a KPI or a statement row."""
    out: set[str] = set()

    try:
        rows = db.query("SELECT concepts_json FROM sec_kpi_map")
    except Exception:  # noqa: BLE001 — a DB without the KPI map must not break the app
        rows = None
    if rows is not None and not rows.empty:
        for raw in rows["concepts_json"]:
            try:
                chain = json.loads(raw)
            except (TypeError, ValueError):
                continue
            for tc in chain or []:
                tax, sep, concept = str(tc).partition(":")
                out.add(concept if sep else tax)

    from lib import sec_statements as _ss  # noqa: PLC0415 — circular at module scope

    for block in (_ss.INCOME_ROWS, _ss.BALANCE_ROWS, _ss.CASHFLOW_ROWS):
        for row in block:
            out.update(str(t) for t in row.get("tags", ()))

    return frozenset(out)
