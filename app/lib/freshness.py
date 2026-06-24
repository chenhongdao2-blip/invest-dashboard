"""Data-freshness panel — reads data/refresh_manifest.json and shows, per dataset,
when it was last refreshed and whether it is fresh / stale / failed.

WHY — the page header shows ONE snapshot date, but the dashboard is fed by many
sources on different cadences (daily yfinance, weekly SEC, local Wind/Futu/iFind).
A silently-stale source must look stale, not fresh. This surfaces it honestly.

Graceful: renders nothing if the manifest is absent (older deploys / first run).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import streamlit as st

_MANIFEST = Path(__file__).resolve().parents[2] / "data" / "refresh_manifest.json"


def load_manifest() -> dict:
    try:
        return json.loads(_MANIFEST.read_text())
    except Exception:  # noqa: BLE001 — missing/corrupt manifest = render nothing
        return {}


def _age_days(source_date: str | None) -> int | None:
    if not source_date:
        return None
    try:
        d = datetime.strptime(source_date[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:  # noqa: BLE001
        return None


def status_icon(entry: dict) -> tuple[str, str]:
    """Return (icon, human_age) for one manifest entry.

    🔴 last run failed, or data older than 2× its max_age_days (hard stale)
    🟡 data older than max_age_days (soft stale)
    🟢 fresh
    ⚪ unknown (no source_date)
    """
    if entry.get("status") == "failed":
        return "🔴", "上次刷新失败"
    age = _age_days(entry.get("source_date"))
    if age is None:
        return "⚪", "—"
    max_age = entry.get("max_age_days") or 99
    human = f"{age} 天前" if age > 0 else "今天"
    if age > 2 * max_age:
        return "🔴", human
    if age > max_age:
        return "🟡", human
    return "🟢", human


def render_freshness_panel(*, expanded: bool = False) -> None:
    """Compact per-dataset freshness list. Call inside `with st.sidebar:` or inline."""
    m = load_manifest()
    if not m:
        return
    # worst status drives the expander header so a 🔴 is visible while collapsed
    icons = [status_icon(e)[0] for e in m.values()]
    header_icon = "🔴" if "🔴" in icons else ("🟡" if "🟡" in icons else "🟢")
    with st.expander(f"{header_icon} 数据新鲜度", expanded=expanded):
        for entry in m.values():
            icon, human = status_icon(entry)
            label = entry.get("label", "—")
            sd = entry.get("source_date", "—")
            st.markdown(
                f"{icon} **{label}** · 截至 `{sd}` · {human}  \n"
                f"<span style='color:#8a8580;font-size:0.8em'>来源 {entry.get('source','—')}</span>",
                unsafe_allow_html=True,
            )
