"""Fetch EOD price + multiple snapshot for all tickers in universe_member.

Pattern crib from ~/strategy-weekly/weekly_perf.py:74-102 (yfinance batch).

Usage:
    python jobs/fetch_eod.py                       # today's EOD only
    python jobs/fetch_eod.py --backfill-days 30    # 30-day historical backfill
    python jobs/fetch_eod.py --skip-multiples      # prices only
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

# FX 转 USD（local ccy → USD）
FX_PAIRS = {
    "USD": None,                  # no conversion
    "HKD": "USDHKD=X",
    "JPY": "USDJPY=X",
    "KRW": "USDKRW=X",
    "CNY": "USDCNY=X",
    "EUR": "EURUSD=X",            # inverse pair (we divide differently)
    "GBP": "GBPUSD=X",            # inverse pair
    "CHF": "USDCHF=X",
}

BATCH_SIZE = 40                   # yfinance batch download size
SLEEP_BETWEEN_INFO = 0.2          # seconds between .info calls (rate limit)


# ----- args -----
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--backfill-days", type=int, default=0,
                   help="Days of historical price to backfill (0 = today only).")
    p.add_argument("--skip-multiples", action="store_true",
                   help="Skip yfinance.info multiples fetch (faster, prices only).")
    p.add_argument("--limit", type=int, default=0,
                   help="Process only first N tickers (debug).")
    return p.parse_args()


# ----- DB helpers -----
def get_tickers(conn: sqlite3.Connection, limit: int = 0) -> list[str]:
    q = "SELECT DISTINCT ticker FROM universe_member ORDER BY ticker"
    if limit > 0:
        q += f" LIMIT {limit}"
    return [row[0] for row in conn.execute(q).fetchall()]


def upsert_prices(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        """INSERT OR REPLACE INTO prices_daily
           (ticker, date, open, high, low, close, adj_close, volume, currency)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return len(rows)


def upsert_multiples(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        """INSERT OR REPLACE INTO multiples_daily
           (ticker, date, market_cap_usd, trailing_pe, forward_pe,
            trailing_eps, forward_eps, ev_ebitda, ev_sales, fcf_yield,
            peg, pb, ytd_return, last_price)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return len(rows)


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
        (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )


# ----- FX rate snapshot -----
def fetch_fx_rates() -> dict[str, float]:
    """Get current USD-conversion factors. {ccy → ccy/USD multiplier}.

    Example: USDHKD=X close = 7.8 → 1 HKD = 1/7.8 USD.
    Output: {"HKD": 1/7.8, "JPY": 1/152, ...} so price * factor[ccy] = USD.
    """
    rates: dict[str, float] = {"USD": 1.0}
    symbols = [pair for pair in FX_PAIRS.values() if pair is not None]
    try:
        d = yf.download(symbols, period="5d", auto_adjust=True,
                        progress=False, threads=True, group_by="ticker")
    except Exception as e:
        print(f"[fx] download failed: {e}; defaulting all FX to 1.0")
        return {ccy: 1.0 for ccy in FX_PAIRS}

    for ccy, sym in FX_PAIRS.items():
        if sym is None:
            continue
        try:
            if isinstance(d.columns, pd.MultiIndex):
                ser = d[(sym, "Close")].dropna()
            else:
                ser = d["Close"].dropna()
            if ser.empty:
                rates[ccy] = 1.0
                continue
            last = float(ser.iloc[-1])
            # USDXXX=X means how many XXX per 1 USD
            # XXXUSD=X means how many USD per 1 XXX
            if sym.startswith("USD"):
                rates[ccy] = 1.0 / last
            else:
                rates[ccy] = last
        except Exception:
            rates[ccy] = 1.0
    print(f"[fx] rates → USD: { {k: round(v, 5) for k, v in rates.items()} }")
    return rates


# ----- price batch fetch -----
def fetch_prices_batch(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    """Return {ticker → DataFrame[Open, High, Low, Close, Volume]} indexed by date."""
    out: dict[str, pd.DataFrame] = {}
    # We always batch; yfinance handles single ticker in MultiIndex too with group_by='ticker'.
    try:
        d = yf.download(
            tickers, start=start, end=end,
            auto_adjust=False,   # keep both close and adj_close
            progress=False, threads=True, group_by="ticker",
        )
    except Exception as e:
        print(f"[prices] batch download failed: {e}")
        return out

    if d.empty:
        return out

    # Handle single-ticker DataFrame vs multi-ticker MultiIndex
    if len(tickers) == 1:
        t = tickers[0]
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.droplevel(1)
        out[t] = d
        return out

    for t in tickers:
        try:
            if t in d.columns.get_level_values(0):
                sub = d[t].dropna(how="all")
                if not sub.empty:
                    out[t] = sub
        except Exception:
            pass
    return out


def prices_to_rows(ticker: str, df: pd.DataFrame, currency: str) -> list[tuple]:
    rows = []
    for ts, r in df.iterrows():
        d = ts.date().isoformat() if hasattr(ts, "date") else str(ts)[:10]
        rows.append((
            ticker, d,
            _safe_float(r.get("Open")),
            _safe_float(r.get("High")),
            _safe_float(r.get("Low")),
            _safe_float(r.get("Close")),
            _safe_float(r.get("Adj Close") or r.get("Close")),
            _safe_int(r.get("Volume")),
            currency,
        ))
    return rows


def _safe_float(v) -> float | None:
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def _safe_int(v) -> int | None:
    f = _safe_float(v)
    return int(f) if f is not None else None


# ----- multiples fetch (.info) -----
def fetch_info_for(ticker: str) -> dict | None:
    """Single-ticker .info fetch with retry."""
    for attempt in range(2):
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            if info and (info.get("marketCap") or info.get("regularMarketPrice")):
                return info
        except Exception as e:
            print(f"[info] {ticker} attempt {attempt + 1} fail: {e}")
        time.sleep(0.5)
    return None


def info_to_multiple_row(
    ticker: str, info: dict, snapshot_date: str, fx: dict[str, float]
) -> tuple | None:
    """Convert yfinance.info dict → multiples_daily row tuple."""
    ccy = (info.get("currency") or info.get("financialCurrency") or "USD").upper()
    fx_to_usd = fx.get(ccy, 1.0)
    mcap_local = _safe_float(info.get("marketCap"))
    mcap_usd = mcap_local * fx_to_usd if mcap_local is not None else None

    return (
        ticker,
        snapshot_date,
        mcap_usd,
        _safe_float(info.get("trailingPE")),
        _safe_float(info.get("forwardPE")),
        _safe_float(info.get("trailingEps")),
        _safe_float(info.get("forwardEps")),
        _safe_float(info.get("enterpriseToEbitda")),
        _safe_float(info.get("enterpriseToRevenue")),
        _safe_float(info.get("freeCashflow") and mcap_local
                    and info.get("freeCashflow") / mcap_local),
        _safe_float(info.get("pegRatio") or info.get("trailingPegRatio")),
        _safe_float(info.get("priceToBook")),
        _safe_float(info.get("ytdReturn")),         # may be None for individual stocks
        _safe_float(info.get("regularMarketPrice") or info.get("currentPrice")),
    )


# ----- main -----
def main() -> None:
    args = parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Run init_db.py first.")

    conn = sqlite3.connect(DB_PATH)
    tickers = get_tickers(conn, limit=args.limit)
    if not tickers:
        print("[fetch_eod] No tickers — run load_universe.py first.")
        return

    today = date.today()
    end = (today + timedelta(days=1)).isoformat()    # exclusive in yfinance
    start = (today - timedelta(days=max(args.backfill_days, 5))).isoformat()
    snapshot_date = today.isoformat()

    print(f"[fetch_eod] tickers={len(tickers)} | start={start} | end={end}")

    # 1. FX rates
    fx = fetch_fx_rates()

    # 2. Build ticker → currency lookup from universe_member.region
    region_to_ccy = {
        "US": "USD", "HK": "HKD", "JP": "JPY",
        "KR": "KRW", "CN": "CNY", "EU": "EUR", "UK": "GBP", "CH": "CHF",
    }
    ccy_map: dict[str, str] = {}
    cur = conn.execute("SELECT ticker, region FROM universe_member")
    for t, r in cur.fetchall():
        ccy_map[t] = region_to_ccy.get(r, "USD")

    # 3. Batch fetch prices
    total_prices = 0
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        print(f"[prices] batch {i // BATCH_SIZE + 1}/{(len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} tickers)")
        result = fetch_prices_batch(batch, start=start, end=end)
        for t, df in result.items():
            ccy = ccy_map.get(t, "USD")
            rows = prices_to_rows(t, df, ccy)
            total_prices += upsert_prices(conn, rows)
        conn.commit()
        time.sleep(0.5)
    print(f"[prices] total upserted rows: {total_prices}")

    # 4. Multiples (.info)  — slower, one by one
    if not args.skip_multiples:
        total_mult = 0
        ok = 0
        fail = 0
        for idx, t in enumerate(tickers, 1):
            info = fetch_info_for(t)
            if not info:
                fail += 1
                continue
            row = info_to_multiple_row(t, info, snapshot_date, fx)
            if row:
                total_mult += upsert_multiples(conn, [row])
                ok += 1
            if idx % 20 == 0:
                conn.commit()
                print(f"[mult] progress {idx}/{len(tickers)} (ok={ok}, fail={fail})")
            time.sleep(SLEEP_BETWEEN_INFO)
        conn.commit()
        print(f"[mult] done. ok={ok} fail={fail} rows={total_mult}")
    else:
        print("[mult] skipped (--skip-multiples)")

    # 5. Meta
    set_meta(conn, "last_fetch_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    set_meta(conn, "last_snapshot_date", snapshot_date)
    conn.commit()
    conn.close()
    print(f"[fetch_eod] done. snapshot_date={snapshot_date}")


if __name__ == "__main__":
    main()
