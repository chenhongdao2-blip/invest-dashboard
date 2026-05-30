"""Backfill HK / China healthcare benchmarks into benchmarks_daily.

Why this is separate from jobs/fetch_eod.py:
- 恒生医疗保健指数 (HSHCI.HK) is NOT on yfinance — only iFind has the pure index.
  iFind is an interactive/local MCP that cannot run on the US yfinance cron runner,
  so HSHCI ships as a committed seed CSV (data/external/hk_cn_benchmarks_seed.csv,
  pulled via the iFind index MCP). Refresh = re-pull via iFind, regenerate the seed,
  commit (same "data committed to repo" model as the EOD snapshots).
- A-share healthcare ETFs (512170.SS 中证医疗 …) ARE on yfinance, so they are
  fetched live here and could later move into the main EOD cron.

Currency note: benchmarks_daily.close is each instrument's NATIVE currency
(HSHCI in HKD points, 512170 in CNY). The Ticker Drill relative-strength chart
rebases to 100, and routes each stock to a SAME-currency benchmark (HK stock HKD
→ HSHCI/^HSI HKD; A-share CNY → 512170 CNY), so there is no FX distortion.

Run:  uv run --with yfinance --with pandas python jobs/fetch_cn_benchmarks.py
"""
from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"
SEED_CSV = REPO_ROOT / "data" / "external" / "hk_cn_benchmarks_seed.csv"

# yfinance-fetchable benchmarks have moved to jobs/fetch_eod.py BENCHMARK_TICKERS
# (512170.SS 中证医疗, ^SP500-352020 标普500医药) so the main cron keeps them fresh.
# This job now only seeds the iFind-only index HSHCI.HK that the cron cannot reach.
YF_CN_BENCHMARKS: list[str] = []


def _upsert(conn: sqlite3.Connection, rows: list[tuple[str, str, float]]) -> int:
    conn.executemany(
        "INSERT OR REPLACE INTO benchmarks_daily (ticker, date, close) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def load_seed() -> list[tuple[str, str, float]]:
    """HSHCI.HK (恒生医疗保健) from the iFind-pulled committed seed CSV."""
    if not SEED_CSV.exists():
        print(f"[cn-bench] seed missing: {SEED_CSV}")
        return []
    out: list[tuple[str, str, float]] = []
    with SEED_CSV.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                out.append((row["ticker"], row["date"], float(row["close"])))
            except (KeyError, ValueError):
                continue
    return out


def fetch_yf() -> list[tuple[str, str, float]]:
    """A-share healthcare ETFs from yfinance (proxy-aware)."""
    import pandas as pd
    import yfinance as yf

    out: list[tuple[str, str, float]] = []
    for t in YF_CN_BENCHMARKS:
        try:
            d = yf.download(t, period="9mo", auto_adjust=True, progress=False)
        except Exception as e:
            print(f"[cn-bench] {t} fetch failed: {e}")
            continue
        if d is None or d.empty:
            print(f"[cn-bench] {t} empty")
            continue
        close = d["Close"]
        if isinstance(close, pd.DataFrame):           # MultiIndex single-ticker
            close = close.iloc[:, 0]
        for ts, v in close.dropna().items():
            out.append((t, ts.date().isoformat(), float(v)))
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        seed = load_seed()
        n1 = _upsert(conn, seed) if seed else 0
        print(f"[cn-bench] HSHCI seed upserted: {n1} rows")
        yfr = fetch_yf()
        n2 = _upsert(conn, yfr) if yfr else 0
        print(f"[cn-bench] yfinance A-share upserted: {n2} rows")
        # report
        cur = conn.execute(
            "SELECT ticker, MIN(date), MAX(date), COUNT(*) FROM benchmarks_daily "
            "WHERE ticker IN ('HSHCI.HK','512170.SS') GROUP BY ticker"
        )
        for row in cur.fetchall():
            print(f"[cn-bench]   {row[0]}: {row[1]}..{row[2]} ({row[3]} rows)")
    finally:
        conn.close()


if __name__ == "__main__":
    os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:7897")
    os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:7897")
    main()
