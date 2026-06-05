"""把申万行业指数周线 seed CSV 载入 sw_industry_daily (RRG 板块轮动用).

WHY 分两段 (拉取 vs 入库)：iFind index MCP 只在本地父会话可用，GitHub Actions
cron 上没有 (cron 只有 yfinance 无 auth)。所以申万周线走 "本地 iFind 拉 → committed
seed CSV → 本 loader 入库 (任何环境可跑)"，与 jobs/fetch_cn_benchmarks.py 的 HSHCI
seed 同模式。seed 刷新 = 重跑 jobs/pull_sw_industry_ifind.py (本地) 重生 CSV 后 commit。

seed CSV 列: ticker,name_cn,date,close,turnover_rate   (date=YYYY-MM-DD, 周五周线)

Run:  uv run --with pandas python jobs/load_sw_industry.py
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"
# (seed CSV, 该文件缺 market 列时的默认市场)
SEEDS = [
    (REPO_ROOT / "data" / "external" / "sw_industry_seed.csv", "a_share"),
    (REPO_ROOT / "data" / "external" / "hk_sector_seed.csv", "hk"),
]


def _upsert(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        "INSERT OR REPLACE INTO sw_industry_daily "
        "(ticker, name_cn, market, date, close, turnover_rate) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def load_seed(path: Path, default_market: str) -> list[tuple]:
    if not path.exists():
        print(f"[sw-industry] seed missing: {path}")
        return []
    out: list[tuple] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                close = float(row["close"]) if row.get("close") not in (None, "") else None
                tr = row.get("turnover_rate")
                tr = float(tr) if tr not in (None, "") else None
                market = row.get("market") or default_market
                out.append((row["ticker"], row.get("name_cn"), market, row["date"], close, tr))
            except (KeyError, ValueError):
                continue
    return out


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Run jobs/init_db.py first.")
    conn = sqlite3.connect(DB_PATH)
    try:
        total = 0
        for path, mkt in SEEDS:
            total += _upsert(conn, load_seed(path, mkt))
        print(f"[sw-industry] upserted {total} rows from {len(SEEDS)} seeds")
        cur = conn.execute(
            "SELECT market, COUNT(DISTINCT ticker), MIN(date), MAX(date), COUNT(*) "
            "FROM sw_industry_daily GROUP BY market ORDER BY market"
        )
        for r in cur.fetchall():
            print(f"[sw-industry]   {r[0]}: {r[1]} series, {r[2]}..{r[3]} ({r[4]} rows)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
