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
    "mnc_ma_deals":       {"label": "MNC M&A / BD 交易",       "source": "M&A:FactSet(本地) / BD:PatSnap(本地)", "max_age_days": 7},
    "hshci_monthly":      {"label": "HSHCI 月线/长周期",       "source": "Wind(本地)",      "max_age_days": 40},
    "us_hc_13f":          {"label": "美国医疗基金 13F 持仓",   "source": "SEC EDGAR",        "max_age_days": 140},
    # ── 2026-08-29 暗数据纳管：以下数据集此前不在 manifest,过期无人知 ──
    "biotech_catalysts":  {"label": "生科组合 催化剂时点",     "source": "手工(PatSnap变化探测+transcript核对)", "max_age_days": 30},
    "earnings_calendar":  {"label": "业绩会日历",              "source": "minodata API(GH手动dispatch)",          "max_age_days": 7},
    "sw_industry_daily":  {"label": "申万行业日线(板块轮动A股腿)", "source": "Wind(job待改写;原iFind已停用)",     "max_age_days": 7},
    "bd_deals":           {"label": "BD/授权交易明细",         "source": "PatSnap(本地)",                          "max_age_days": 7},
    "etf_hc_holdings":    {"label": "ETF 持仓/画像(HC篮)",     "source": "etf-data CLI(本地)",                     "max_age_days": 45},
    "china_fund_hc_positioning": {"label": "中国基金 HC 持仓(季)", "source": "手工(公募季报 audited xlsx)",       "max_age_days": 135},
    "cn_pharma_headcount":{"label": "医药公司员工人数(年)",    "source": "手工(年报)",                             "max_age_days": 300},
    "funding_quarterly":  {"label": "投融资季度面板(公开源)",  "source": "手工(多源三角+对抗核验)",                "max_age_days": 120},
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
        if col not in df.columns:
            return None
        # errors="coerce": 列里混入非日期字面量(如 "Q1 2026")时跳过而非整列失败
        mx = pd.to_datetime(df[col], errors="coerce", format="mixed").max()
        return str(mx.date()) if pd.notna(mx) else None
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
        # 事件流数据集: 新鲜度 = 上次扫描时间(meta as_of), 不是最后一笔 deal 的日期 ——
        # 安静期没有新交易不等于数据过期
        try:
            j = json.loads((EXT / "mnc_ma_deals_meta.json").read_text())
            return str(j.get("as_of", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
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
        # 用 sec_company.fetched_at 的真实抓取时间, 不再用 prices_daily 当 proxy ——
        # 价格天天新, proxy 会把 SEC 卡死 3 个月的事实遮成 "age=1 ok"(2026-08-29 实锤)。
        if not DB_PATH.exists():
            return None
        try:
            con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            v = pd.read_sql(
                "SELECT MAX(substr(fetched_at,1,10)) FROM sec_company WHERE sec_status='ok'",
                con).iloc[0, 0]
            con.close()
            return str(v) if v else None
        except Exception:  # noqa: BLE001
            return None
    if key == "earnings_calendar":
        try:
            j = json.loads((EXT / "earnings_calendar.json").read_text())
            return str(j.get("as_of_hkt", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
    if key == "sw_industry_daily":
        return _db_max_date("sw_industry_daily")
    if key == "bd_deals":
        # date 列为月粒度(YYYY-MM)。按「月末」计龄: 本月已有入库交易 = 不算过期,
        # 否则月中永远假警报(月初解析会让 8 月数据在 8/8 就报 stale)。
        try:
            df = pd.read_csv(EXT / "bd_deals.csv")
            mx = pd.to_datetime(df["date"], errors="coerce", format="mixed").max()
            if pd.isna(mx):
                return None
            return str((mx + pd.offsets.MonthEnd(0)).date())
        except Exception:  # noqa: BLE001
            return None
    if key == "etf_hc_holdings":
        try:
            j = json.loads((EXT / "etf_hc_meta.json").read_text())
            return str(j.get("as_of", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
    if key == "china_fund_hc_positioning":
        return _csv_max_date(EXT / "china_fund_hc_positioning.csv", col="data_date")
    if key == "cn_pharma_headcount":
        return _csv_max_date(EXT / "cn_pharma_headcount.csv", col="asof")
    if key == "funding_quarterly":
        try:
            j = json.loads((EXT / "funding_public_q1_2026.json").read_text())
            return str(j.get("_meta", {}).get("as_of", ""))[:10] or None
        except Exception:  # noqa: BLE001
            return None
    # biotech_catalysts: CSV 无日期列,source_date 只能手工 bump —— 刻意返回 None,
    # 避免任何自动解析假装知道催化剂表的核对时点。
    return None


def _load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except Exception:  # noqa: BLE001 — corrupt manifest shouldn't block refresh
            return {}
    return {}


def audit() -> None:
    """把 manifest 对齐到「说真话」状态：

    1. DATASETS 里注册了但 manifest 缺的条目 → 补建（source_date 从数据本身解析,
       refreshed_at 留空 —— 不伪造一个从未发生过的刷新时间戳）。
    2. 每条按 source_date + max_age_days 重算 status（ok/stale）。此前 status 是
       写入时盖的章, 永不重算 → 超期 60 天的条目 JSON 里仍是 "ok", 对直接读
       JSON 的消费者(hook/人/CI)撒谎。app 面板(freshness.py)自己按日期算色,
       不受影响。"failed" 保留不覆盖（那是上次运行结果, 与数据年龄是两件事）。
    """
    from datetime import date as _date

    manifest = _load_manifest()
    today = _date.today()
    rows = []
    for key, meta in DATASETS.items():
        entry = manifest.get(key, {})
        entry.setdefault("refreshed_at", None)
        entry.update({"label": meta["label"], "source": meta["source"],
                      "max_age_days": meta["max_age_days"]})
        sd = resolve_source_date(key) or entry.get("source_date")
        if sd:
            entry["source_date"] = sd
        age = None
        if entry.get("source_date"):
            try:
                age = (today - datetime.strptime(str(entry["source_date"])[:10], "%Y-%m-%d").date()).days
            except ValueError:
                age = None
        if entry.get("status") != "failed":
            if age is None:
                entry["status"] = "unknown"
            else:
                entry["status"] = "stale" if age > meta["max_age_days"] else "ok"
        manifest[key] = entry
        rows.append((key, entry.get("source_date", "—"), age, meta["max_age_days"], entry["status"]))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    w = max(len(k) for k, *_ in rows)
    print(f"{'dataset':<{w}}  source_date  age  max  status")
    for key, sd, age, mx, stat in sorted(rows, key=lambda r: -(r[2] if r[2] is not None else 9999)):
        flag = "⚠️ " if stat in ("stale", "failed", "unknown") else "   "
        print(f"{flag}{key:<{w}}  {str(sd):<11}  {str(age):>3}  {mx:>3}  {stat}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Update data/refresh_manifest.json")
    ap.add_argument("key", nargs="?", help="dataset key (see DATASETS)")
    ap.add_argument("status", nargs="?", choices=["ok", "stale", "failed"], help="run outcome")
    ap.add_argument("--note", default="", help="optional free-text note")
    ap.add_argument("--audit", action="store_true",
                    help="补注册 DATASETS 缺失条目 + 按 source_date 重算全部 status")
    args = ap.parse_args()

    if args.audit:
        audit()
        return
    if not args.key or not args.status:
        ap.error("需要 <key> <status>，或用 --audit")

    manifest = _load_manifest()
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
