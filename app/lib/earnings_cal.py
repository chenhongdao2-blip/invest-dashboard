"""Loader for the earnings-call calendar artifact (data/external/earnings_calendar.json).

Language-agnostic on purpose: this module returns raw data only; labels and
status words are translated by the caller at render time (i18n main-session
rule — cached functions must never read st.session_state["lang"]).
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "external" / "earnings_calendar.json"


@st.cache_data(ttl=300)
def load_calendar(_mtime: float | None = None) -> dict | None:
    """Parsed calendar envelope, or None when absent/corrupt (page shows empty state)."""
    try:
        d = json.loads(_PATH.read_text(encoding="utf-8"))
        if d.get("schema_version") != 1:
            return None
        return d
    except Exception:  # noqa: BLE001 — a broken artifact must not crash Home
        return None


def load() -> dict | None:
    """Cache-busting wrapper: keyed on file mtime so a cron-committed refresh
    is picked up without waiting out the TTL after a Cloud reboot."""
    try:
        mtime = _PATH.stat().st_mtime
    except OSError:
        mtime = None
    return load_calendar(mtime)


# ── local-only transcripts (双轨: gitignored 全文本地可看, 云端目录不存在自动隐藏) ──
_LOCAL_DIR = _PATH.parent.parent / "local" / "earnings_transcripts"


def _norm_speeches(items: list) -> list[dict]:
    """Normalize both minodata schemas to [{speaker:{name,info}, segs:[{text,ts}]}].
    New: {speaker, content:[{text,ts}]}. Old: {speaker, line:[{text,ts}]} or flat text/ts."""
    out = []
    for sp in items or []:
        segs = sp.get("content") or sp.get("line") or (
            [{"text": sp.get("text"), "ts": sp.get("ts")}] if sp.get("text") else [])
        spk = sp.get("speaker") or {}
        if isinstance(spk, str):
            spk = {"name": spk, "info": None}
        if segs:
            out.append({"speaker": spk, "segs": segs})
    return out


@st.cache_data(ttl=300)
def local_transcript(ticker: str, _sig: str = "") -> dict | None:
    """Latest local transcript wrapper for `ticker`, normalized, or None
    (always None on Cloud where the gitignored dir doesn't exist).
    Language-agnostic: returns both EN text and CN ts; caller picks."""
    try:
        stem = ticker.replace(".", "_")
        files = sorted(_LOCAL_DIR.glob(f"{stem}_*.json"))
        if not files:
            return None
        w = json.loads(files[-1].read_text(encoding="utf-8"))
        doc = w.get("transcript") or {}
        pres = _norm_speeches(doc.get("presentation") or [])
        qa = _norm_speeches(doc.get("qa") or [])
        if not pres and isinstance(doc.get("describe"), dict):     # old schema
            pres = _norm_speeches(doc["describe"].get("content") or [])
            if isinstance(doc.get("qa"), dict):
                qa = _norm_speeches(doc["qa"].get("content") or [])
        return {"ticker": w.get("ticker"), "date_hkt": w.get("date_hkt"),
                "name_check": w.get("name_check"), "pres": pres, "qa": qa}
    except Exception:  # noqa: BLE001 — a broken local file must not crash the page
        return None


def transcript_for(ticker: str) -> dict | None:
    """Cache-busting wrapper keyed on the ticker's local file listing."""
    try:
        stem = ticker.replace(".", "_")
        sig = ",".join(f"{p.name}:{p.stat().st_mtime}" for p in sorted(_LOCAL_DIR.glob(f"{stem}_*.json")))
    except OSError:
        sig = ""
    return local_transcript(ticker, sig)
