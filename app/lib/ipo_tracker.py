"""HK healthcare IPO tracker — loader for the Capital Markets · IPO tab.

Hybrid freshness (local-first, cloud-overlay):
  - `hk_hc_ipo_tracker.csv` (Wind+Futu local reconcile via jobs/build_hk_ipo_tracker.py) is the
    base: fully-computed returns / tiers / suspension flags, Wind-grade turnover.
  - If snapshots.db (cloud yfinance EOD) has a NEWER close for a ticker, overlay it and recompute
    return + current market cap so the page refreshes daily "like the other prices". Suspension /
    no-offer / liquidity-tier / sub-sector flags always stay from the Wind reconcile.

All break-issue / return / tier aggregates exclude no-offer (介绍上市) and suspended (停牌) names and
names with <20 trading sessions — see jobs/build_hk_ipo_tracker.py for the cross-check rationale.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from lib import db

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UNIVERSE_CSV = REPO_ROOT / "data" / "external" / "hk_hc_ipo_universe.csv"
TRACKER_CSV = REPO_ROOT / "data" / "external" / "hk_hc_ipo_tracker.csv"
META_JSON = REPO_ROOT / "data" / "external" / "hk_hc_ipo_meta.json"

# NB: market-cap / liquidity tier thresholds + FX live in jobs/build_hk_ipo_tracker.py — the job
# bakes all tiers/flags into the tracker CSV; this loader only refreshes price/return via overlay.


@st.cache_data(ttl=600)
def load_hk_ipo_tracker() -> pd.DataFrame:
    """Display-ready IPO tracker. Empty frame if the data files are absent (graceful)."""
    if not TRACKER_CSV.exists():
        return pd.DataFrame()
    trk = pd.read_csv(TRACKER_CSV, dtype={"code": str})
    meta = hk_ipo_meta()
    as_of = meta.get("as_of", "")

    # ---- cloud overlay: refresh close from snapshots.db when it is newer than the Wind snapshot ----
    try:
        uni = pd.read_csv(UNIVERSE_CSV, dtype={"code": str})
        yfmap = dict(zip(uni["code"], uni["ticker_yf"]))
        snap_date = db.latest_snapshot_date()
        if snap_date and as_of and str(snap_date) >= str(as_of):
            closes = db.get_close_series(tuple(uni["ticker_yf"].dropna().tolist()))
            if not closes.empty:
                last = closes.ffill().iloc[-1]  # last valid close per ticker
                for i, r in trk.iterrows():
                    if r.get("suspended") or r.get("no_offer"):
                        continue  # never overlay frozen / no-offer names
                    yf = yfmap.get(r["code"])
                    nc = last.get(yf) if yf in last.index else None
                    if nc is None or pd.isna(nc) or nc <= 0:
                        continue
                    # Overlay PRICE-driven fields only (close / return / break). Market cap and
                    # mktcap_tier stay from the Wind reconcile — Wind handles HK corporate actions
                    # (e.g. 长风 H-share full-circulation) that yfinance lags, and the tier must not
                    # jitter across the 100/300亿 boundary on daily yfinance noise.
                    offer = r.get("offer_price_hkd")
                    trk.at[i, "close"] = round(float(nc), 3)
                    if pd.notna(offer) and offer:
                        trk.at[i, "ret_pct"] = round((nc - offer) / offer * 100, 1)
                        trk.at[i, "broke"] = bool(nc < offer)
                trk.attrs["overlay_date"] = str(snap_date)
    except Exception:  # noqa: BLE001 — overlay is best-effort; tracker CSV stands on any error
        pass
    return trk


@st.cache_data(ttl=600)
def hk_ipo_meta() -> dict:
    if not META_JSON.exists():
        return {}
    return json.loads(META_JSON.read_text())


def clean_view(df: pd.DataFrame) -> pd.DataFrame:
    """Names eligible for aggregate stats: has offer, not suspended, >=20 sessions."""
    if df.empty:
        return df
    return df[df["clean"] == True].copy()  # noqa: E712 (CSV bool)


def break_rate_by(df: pd.DataFrame, col: str, order: list[str]) -> pd.DataFrame:
    """Break-issue rate per bucket on the CLEAN universe. Returns bucket/n/broke/rate_pct."""
    c = clean_view(df)
    rows = []
    for b in order:
        sub = c[c[col] == b]
        n = len(sub)
        broke = int((sub["broke"] == True).sum())  # noqa: E712 — CSV bool, avoid fillna downcast warn
        rows.append({"bucket": b, "n": n, "broke": broke,
                     "rate_pct": round(broke / n * 100, 0) if n else None})
    return pd.DataFrame(rows)
