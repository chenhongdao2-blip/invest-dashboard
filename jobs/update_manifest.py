"""Update data/refresh_manifest.json — the single source of truth for per-dataset
freshness. Each refresh job calls this after it runs so the app (and a human) can
tell, per dataset: where it came from, when it was last refreshed, the latest
DATA date it carries, and whether the last run was ok / stale / failed.

WHY — "网站部署日期" ≠ "数据日期". Without a manifest a silently-failed source
looks identical to a fresh one. This makes staleness visible instead of faked.

Usage:
    python jobs/update_manifest.py <key> <status> [--note "..."]
        <key>    one of the dataset keys below (or any string for ad-hoc)
        <status> ok | stale | failed
    e.g.  python jobs/update_manifest.py benchmarks_fx ok
          python jobs/update_manifest.py hc_index_comparison ok --note "US panels only"

source_date for known keys is resolved from the actual data (DB table max(date)
or CSV), so it never lies about freshness. Unknown keys just record status +
refreshed_at (UTC). Failure to resolve source_date is non-fatal (left as null).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"
EXT = REPO_ROOT / "data" / "external"
MANIFEST = REPO_ROOT / "data" / "refresh_manifest.json"

# Per-dataset metadata: human label, where it comes from, and how stale is "too
# stale" (max_age_days drives the app's grey-out / warning). Cadence reflects the
# agreed frequency tiers, NOT a promise the source ran.
DATASETS: dict[str, dict] = {
    "eod_prices":         {"label": "美股/港股 EOD 价格·估值", "source": "yfinance",        "max_age_days": 4},
    "sec_facts":          {"label": "SEC 公司基本面",          "source": "SEC EDGAR",        "max_age_days": 10},
    "benchmarks_fx":      {"label": "FX / MSCI World 基准",    "source": "yfinance",        "max_age_days": 4},
    "hc_index_comparison":{"label": "相对表现(美股线)",       "source": "yfinance",        "max_age_days": 4},
    "hk_ipo_tracker":     {"label": "港股 IPO 散点/破发",      "source": "Wind+Futu(本地)", "max_age_days": 9},
    "mnc_ma_deals":       {"label": "MNC M&A / BD 交易",       "source": "PharmCube",        "max_age_days": 4},
    "hshci_monthly":      {"label": "HSHCI 月线/长周期",       "source": "iFind(本地)",     "max_age_days": 40},
    "us_hc_13f":          {"label": "美国医疗基金 13F 持仓",   "source": "SEC EDGAR",        "max_age_days": 140},
}


def _db_max_date(table: str, where: str = "") -> str | None:
    if not DB_PATH.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        q = f"SELECT MAX(date) FROM {table}" + (f" WHERE {where}" if where else "")
        v = pd.read_sql(q, con).iloc[0, 0]
        con.close()
        return str(v) if v is not None else None
    except Exception:  # noqa: BLE001 — manifest stamping must never crash a job
        return None


def _csv_max_date(path: Path, col: str = "date") -> str | None:
    try:
        df = pd.read_csv(path)
        return str(pd.to_datetime(df[col]).max().date()) if col in df.columns else None
    except Exception:  # noqa: BLE001
        return None


def resolve_source_date(key: str) -> str | None:
    """Latest DATA date the dataset carries — read from the data itself, not faked."""
    if key in ("eod_prices",):
        return _db_max_date("prices_daily")
    if key in ("benchmarks_fx",):
        return _db_max_date("benchmarks_daily", "ticker IN ('CNY=X','HKD=X','URTH')")
    if key == "hc_index_comparison":
        return _csv_max_date(EXT / "hc_index_comparison.csv")
    if key == "hk_ipo_tracker":
        # meta json carries the curated as_of (first 10 chars = YYYY-MM-DD)
        try:
            meta = json.loads((EXT / "hk_hc_ipo_meta.json").read_text())
            return str(meta.get("as_of", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
    if key == "mnc_ma_deals":
        return _csv_max_date(EXT / "mnc_ma_deals.csv")
    if key == "hshci_monthly":
        return _csv_max_date(EXT / "hshci_history_monthly.csv")
    if key == "us_hc_13f":
        # latest_period = 13F report quarter-end (data date, NOT the fetch date)
        try:
            j = json.loads((EXT / "us_hc_funds_13f.json").read_text())
            return str(j.get("latest_period", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
    if key == "sec_facts":
        return _db_max_date("prices_daily")  # proxy; SEC facts have no own date col
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Update data/refresh_manifest.json")
    ap.add_argument("key", help="dataset key (see DATASETS)")
    ap.add_argument("status", choices=["ok", "stale", "failed"], help="run outcome")
    ap.add_argument("--note", default="", help="optional free-text note")
    args = ap.parse_args()

    manifest: dict = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text())
        except Exception:  # noqa: BLE001 — corrupt manifest shouldn't block refresh
            manifest = {}

    meta = DATASETS.get(args.key, {})
    entry = manifest.get(args.key, {})
    entry.update({
        "label": meta.get("label", args.key),
        "source": meta.get("source", "unknown"),
        "max_age_days": meta.get("max_age_days"),
        "status": args.status,
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    # Only refresh source_date on a successful run; a failed run must NOT bump it.
    if args.status == "ok":
        sd = resolve_source_date(args.key)
        if sd:
            entry["source_date"] = sd
    if args.note:
        entry["note"] = args.note
    manifest[args.key] = entry

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[manifest] {args.key} → {args.status} "
          f"(source_date={entry.get('source_date', '—')}, "
          f"refreshed_at={entry['refreshed_at']})")


if __name__ == "__main__":
    main()
