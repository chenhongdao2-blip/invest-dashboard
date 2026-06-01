"""Loader for analyst-model extracts (data/models/<TICKER>.json).

Produced by jobs/extract_model.py. Confidential (TP/DCF) → gitignored, local-only
in MVP (not on public Cloud). cache_data is keyed by the `ticker` ARG (not a
no-arg global) — the cross-page cache-collision trap this project hit before.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "data" / "models"


@st.cache_data(ttl=600)
def load_model(ticker: str) -> dict | None:
    """Return the ModelView dict for `ticker`, or None if no model on disk."""
    p = MODELS_DIR / f"{ticker}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def has_model(ticker: str) -> bool:
    return (MODELS_DIR / f"{ticker}.json").exists()


@st.cache_data(ttl=600)
def available_models() -> list[str]:
    if not MODELS_DIR.exists():
        return []
    return sorted(p.stem for p in MODELS_DIR.glob("*.json"))
