"""Password-gated trust research on the existing CMSI invest-dashboard shell."""
from __future__ import annotations

import base64
import re

import streamlit as st

from lib import theme
from lib.trust_web.auth import render_gate
from lib.trust_web.component import board
from lib.trust_web.store import ReleaseError, store_from_settings

# No private data access, component mount, or CSV construction may precede this.
theme.inject_css()
render_gate(st)

try:
    store = store_from_settings(st)
    roster = store.read_json("roster.json.gz")
    if roster.get("schema_version") != 1:
        raise ReleaseError("本次研究版本不兼容。")
except ReleaseError as exc:
    st.error(str(exc))
    st.stop()

state = st.session_state
selected = state.get("trust_selected")
detail = None
if selected:
    try:
        kind, _, key = selected.partition(":")
        if kind == "company" and re.fullmatch(r"[A-Za-z0-9.]+", key) and key in {r["code"] for r in roster["companies"]}:
            detail = store.read_json(f"companies/{key}.json.gz")
        elif kind == "person" and key in {r["id"] for r in roster["people"]}:
            detail = store.read_json(f"people/{key}.json.gz")
        else:
            state["trust_selected"] = None
            selected = None
    except ReleaseError as exc:
        st.error(str(exc))
        st.stop()

source = state.get("trust_source_request")
protected_document = None
if source:
    try:
        content, mime = store.report(source[7:]) if source.startswith("report:") else store.evidence(source)
        protected_document = {"mime": mime, "content": base64.b64encode(content).decode("ascii")}
    except ReleaseError as exc:
        st.warning(str(exc))

pending_export = state.get("trust_pending_export")
export_blob = None
if pending_export:
    try:
        content = store.read("exports/个人三情形试算_全926人.csv")
        export_blob = {"name": "个人三情形试算_全926人.csv", "content": base64.b64encode(content).decode("ascii"),
                       "nonce": pending_export}
    except ReleaseError as exc:
        st.warning(str(exc))

result = board(data={"roster": roster, "detail": detail,
                     "ui": state.get("trust_ui") or {}, "document": protected_document,
                     "export_blob": export_blob}, key="cmsi_trust_board")

# Component triggers are opaque identifiers, never paths or authorization.
if result.get("ui") is not None and isinstance(result.get("ui"), dict):
    state["trust_ui"] = result.get("ui")
if result.get("selected") is not None:
    requested = result.get("selected") or None
    if requested != selected:
        state["trust_selected"] = requested
        state["trust_source_request"] = None
        st.rerun()
if result.get("source_request") is not None and result.get("source_request") != state.get("trust_source_request"):
    state["trust_source_request"] = result.get("source_request")
    st.rerun()
if result.get("export_request") and result.get("export_request") != state.get("trust_handled_export"):
    state["trust_handled_export"] = result.get("export_request")
    state["trust_pending_export"] = result.get("export_request")
    st.rerun()
if result.get("export_done") and result.get("export_done") == state.get("trust_pending_export"):
    state["trust_pending_export"] = None
    st.rerun()
