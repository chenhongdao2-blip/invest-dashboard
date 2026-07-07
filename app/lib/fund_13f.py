"""Loader for the Healthcare page's "US HC funds 13F" section.

Reads the committed data/external/us_hc_funds_13f.json baked by
jobs/fetch_13f_hc_funds.py (SEC EDGAR 13F-HR, public data — real fund names,
no anonymisation). Mirrors hc_overview.py's cache discipline: path + mtime
are resolved OUTSIDE @st.cache_data and passed in as hashed args, so an
in-place rebuild invalidates the cache (cache-key-omits-input-state trap).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
F13_PATH = REPO_ROOT / "data" / "external" / "us_hc_funds_13f.json"


def _resolve(p: Path) -> tuple[str, float]:
    try:
        return str(p), p.stat().st_mtime
    except OSError:
        return "", 0.0


@st.cache_data(ttl=3600)
def _read(path_str: str, mtime: float) -> dict:
    if not path_str:
        return {}
    try:
        return json.loads(Path(path_str).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — malformed file = empty section, not a crash
        return {}


def load_13f() -> dict:
    path_str, mtime = _resolve(F13_PATH)
    return _read(path_str, mtime)


def _label(row: dict) -> str:
    """Display label: ticker when mapped, else issuer name (never fabricate)."""
    return row.get("ticker") or row.get("issuer", "?")


def consensus_table(data: dict, min_funds: int = 2) -> pd.DataFrame:
    """Cross-fund consensus holdings: name | n_funds | total value | QoQ counts."""
    rows = (data.get("aggregate") or {}).get("consensus") or []
    out = [
        {
            "label": _label(r), "n_funds": r["n_funds"], "total_value": r["total_value"],
            "n_new": r["n_new"], "n_add": r["n_add"], "n_trim": r["n_trim"],
            "funds": ", ".join(r["funds"]),
        }
        for r in rows if r["n_funds"] >= min_funds
    ]
    return pd.DataFrame(out)


def top_new_buys(data: dict) -> pd.DataFrame:
    rows = (data.get("aggregate") or {}).get("top_new_buys") or []
    return pd.DataFrame([
        {"label": _label(r), "n_new": r["n_new"], "n_funds": r["n_funds"],
         "total_value": r["total_value"], "funds": ", ".join(r["funds"])}
        for r in rows
    ])


def top_exits(data: dict) -> pd.DataFrame:
    rows = (data.get("aggregate") or {}).get("top_exits") or []
    return pd.DataFrame([
        {"label": _label(r), "n_exits": r["n_exits"], "funds": ", ".join(r["funds"])}
        for r in rows
    ])


def fund_snapshot(fund: dict) -> pd.DataFrame:
    """One fund's top holdings as display DataFrame (weight, QoQ tag, shares chg)."""
    return pd.DataFrame([
        {
            "label": _label(r), "weight": r["weight"], "value": r["value"],
            "qoq": r["qoq"],
            "shares_chg_pct": r.get("shares_chg_pct"),
        }
        for r in fund.get("top_holdings") or []
    ])


def funds_ok(data: dict) -> list[dict]:
    """Funds with a usable snapshot (ok or stale-with-data), biggest AUM first."""
    return sorted(
        [f for f in data.get("funds") or [] if f.get("top_holdings")],
        key=lambda f: -(f.get("total_value") or 0),
    )


def attach_prices(df: pd.DataFrame, data: dict, label_col: str = "label") -> pd.DataFrame:
    """Add `spark` (close sequence — feeds render_html_table spark_cols) and
    `since_qend_pct` (decimal move since the 13F report date) columns, keyed on
    the display label (= ticker when mapped). Unmapped issuers get NaN → the
    table renders an em-dash; we never fabricate a series.

    since_qend_pct anchors at the LAST close ≤ latest_period (quarter end), so
    it reads "what happened to this name AFTER the funds' snapshot" — the one
    move a 45-day-stale filing can't tell you.
    """
    prices = data.get("prices") or {}
    period = str(data.get("latest_period") or "")

    def _series(lbl: str) -> list[float] | None:
        p = prices.get(str(lbl))
        return p["closes"] if p else None

    def _since(lbl: str) -> float | None:
        p = prices.get(str(lbl))
        if not p or not period:
            return None
        anchor = None
        for d, c in zip(p["dates"], p["closes"]):
            if d <= period:
                anchor = c
            else:
                break
        if anchor is None or anchor == 0:
            return None
        return p["closes"][-1] / anchor - 1

    df = df.copy()
    df["spark"] = df[label_col].map(_series)
    df["since_qend_pct"] = df[label_col].map(_since)
    return df


def prices_as_of(data: dict) -> str | None:
    return data.get("prices_as_of")


def verdict(data: dict) -> dict:
    """Headline numbers for the section verdict line — all computed, never prose."""
    ok = funds_ok(data)
    if not ok:
        return {}
    agg = data.get("aggregate") or {}
    cons = agg.get("consensus") or []
    top = cons[0] if cons else {}
    buys = agg.get("top_new_buys") or []
    hot = buys[0] if buys else {}
    return {
        "n_funds": len(ok),
        "period": data.get("latest_period") or "—",
        "total_aum_bn": sum(f.get("total_value") or 0 for f in ok) / 1e9,
        "top_label": _label(top) if top else "—",
        "top_n_funds": top.get("n_funds", 0),
        "hot_label": _label(hot) if hot else "—",
        "hot_n_new": hot.get("n_new", 0),
    }
