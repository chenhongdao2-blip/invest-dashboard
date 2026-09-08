"""Fetch MSCI World (URTH) + FX (USDCNY, USDHKD) into benchmarks_daily.

WHY — the cross-market USD-overlay RRG (板块轮动「跨市场」tab) needs:
  • a global yardstick   → URTH (iShares MSCI World, USD)  ── developed-markets MSCI
    World; used purely as a relative-strength benchmark for A/HK/US sectors.
  • FX to put A-share (CNY) and HK (HKD) sector indices into USD:
      USDCNY = CNY=X  (CNY per 1 USD ≈ 6.8)   index_usd = index_cny / USDCNY
      USDHKD = HKD=X  (HKD per 1 USD ≈ 7.8)   index_usd = index_hkd / USDHKD

All three are on yfinance (unlike the iFind-only 申万/恒生 sector seeds), so this is
a cron-friendly job — same model as jobs/fetch_eod.py BENCHMARK_TICKERS. benchmarks_daily
stores each instrument's NATIVE quote (URTH in USD; CNY=X / HKD=X as the FX rate itself).

China network: set HTTP_PROXY / HTTPS_PROXY before running (yfinance honors env proxies).
Run:  HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 \
      uv run --with yfinance --with pandas python jobs/fetch_fx_world.py
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import parquet_store as pq  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"

# ticker → role (doc only). All quoted in their native unit; conversion happens in-app.
TICKERS = ["URTH", "CNY=X", "HKD=X"]
PERIOD = "2y"          # cover the 52-week 申万/恒生 seed window (2025-06 →) with margin


def _close_series(tk: str) -> pd.Series:
    """yfinance close for one ticker → clean Series (handles MultiIndex columns)."""
    df = yf.download(tk, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    cols = df.columns
    if isinstance(cols, pd.MultiIndex):       # newer yfinance: (field, ticker)
        df = df.copy()
        df.columns = cols.droplevel(1)
    s = df["Close"].dropna()
    return s


# PR4 dual write. Staged rather than written per ticker: this job re-fetches a
# 2-year window for EACH of the three tickers, so a per-ticker write would rewrite
# the same ~25 month partitions three times over. One flush at the end of main().
_PQ_BENCH: list[tuple[str, str, float]] = []


def _upsert(conn: sqlite3.Connection, rows: list[tuple[str, str, float]]) -> int:
    conn.executemany(
        "INSERT OR REPLACE INTO benchmarks_daily (ticker, date, close) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    if rows and pq.dual_write_enabled():
        _PQ_BENCH.extend(rows)
    return len(rows)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    total = 0
    try:
        for tk in TICKERS:
            try:
                s = _close_series(tk)
            except Exception as e:               # API hiccup → skip this ticker, keep rest
                print(f"[fx-world] {tk:8} ERR {type(e).__name__}: {str(e)[:70]}")
                continue
            if s.empty:
                print(f"[fx-world] {tk:8} EMPTY (no data returned)")
                continue
            rows = [(tk, d.strftime("%Y-%m-%d"), float(v)) for d, v in s.items()]
            n = _upsert(conn, rows)
            total += n
            print(f"[fx-world] {tk:8} {n:4d} rows  {s.index[0].date()} → {s.index[-1].date()}  last={float(s.iloc[-1]):.4f}")
            time.sleep(1.0)                       # rate-limit (skills INVARIANT)
    finally:
        conn.close()
    if _PQ_BENCH:
        parts = pq.dual_write("benchmarks_daily", _PQ_BENCH, ["ticker", "date", "close"])
        if parts:
            print(f"[parquet] benchmarks_daily: {len(_PQ_BENCH)} rows → "
                  f"{len(parts)} partitions ({min(parts)}..{max(parts)})")
    print(f"[fx-world] done — {total} rows upserted into benchmarks_daily")


if __name__ == "__main__":
    main()
