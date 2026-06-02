"""Loader for analyst-model extracts (data/models/<TICKER>.json).

Produced by jobs/extract_model.py. Two-tier storage (George 2026-06-02):

  - data/models/<T>.json         — FULL model (incl. dcf/target price). Confidential
                                    (TP/DCF + Visible Alpha) → gitignored, LOCAL-ONLY.
  - data/models_public/<T>.json  — DESENSITIZED model (dcf block stripped) produced by
                                    jobs/export_public_model.py → committed, ships to
                                    the public Streamlit Cloud.

load_model() prefers the FULL local file and falls back to the desensitized public
one — so George's Mac shows the target price while Cloud serves the valuation-stripped
view. cache_data is keyed by the `ticker` ARG (not a no-arg global) — the cross-page
cache-collision trap this project hit before.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = REPO_ROOT / "data" / "models"                 # full, gitignored, local-only
PUBLIC_MODELS_DIR = REPO_ROOT / "data" / "models_public"   # desensitized, committed


def _resolve(ticker: str) -> Path | None:
    """Full model wins over the desensitized public copy; None if neither on disk."""
    full = MODELS_DIR / f"{ticker}.json"
    if full.exists():
        return full
    pub = PUBLIC_MODELS_DIR / f"{ticker}.json"
    return pub if pub.exists() else None


@st.cache_data(ttl=600)
def load_model(ticker: str) -> dict | None:
    """Return the ModelView dict for `ticker`, or None if no model on disk."""
    p = _resolve(ticker)
    if p is None:
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def has_model(ticker: str) -> bool:
    return _resolve(ticker) is not None


@st.cache_data(ttl=600)
def available_models() -> list[str]:
    """Union of full + public model tickers (full takes precedence on collision)."""
    stems: set[str] = set()
    for d in (MODELS_DIR, PUBLIC_MODELS_DIR):
        if d.exists():
            stems.update(p.stem for p in d.glob("*.json"))
    return sorted(stems)
