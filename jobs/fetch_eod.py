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

# Benchmark indices — keep in sync with app/lib/benchmarks.py BENCHMARKS.
# Cron-fetched into benchmarks_daily so the home page never makes a live call.
# GICS sector ETFs (XLK..XLRE) added as S&P 500 sector-level RS proxies.
BENCHMARK_TICKERS = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI", "^HSI", "^GSPC",
                     "^SP500-352020",   # S&P 500 Pharmaceuticals — US MNC big-pharma RS benchmark
                     "^NDX",            # Nasdaq 100 — tech 大盘 for hc_ai / health-tech RS benchmark
                     "IGV",             # iShares Tech-Software — US health-tech / SaaS RS benchmark
                     "XHS",             # SPDR Health Care Services — US hospital_care RS benchmark
                     "512170.SS",       # 中证医疗 ETF (CNY) — A-share healthcare RS benchmark
                     "000001.SS",  # 上证综指 — daily-report A-share gauge (沪深300/ChiNext dropped per George)
                     "XLK", "XLF", "XLE", "XLB", "XLI", "XLY", "XLP", "XLC", "XLU", "XLRE",
                     # AI / semiconductor supply-chain benchmarks (cross-market; LLM Wiki)
                     "^SOX", "SMH", "AIQ", "2644.T", "091160.KS", "442580.KS",
                     "512480.SS", "515880.SS", "159819.SZ", "588200.SS", "3191.HK",
                     # 跨市场 USD 同框 RRG (板块轮动 tab5) 用：全球基准 + FX 时间序列。
                     # URTH = iShares MSCI World (USD)；CNY=X/HKD=X = USDCNY/USDHKD 汇率
                     # (本币/USD)，存入 benchmarks_daily 供 _xmkt_raw 把 A/港板块换 USD。
                     # NB: FX_PAIRS 也抓 USDCNY=X/USDHKD=X，但只落 meta(close_usd 快照)；
                     # 这里用别名 CNY=X/HKD=X(同一标的)落 benchmarks_daily 留完整序列。
                     "URTH", "CNY=X", "HKD=X",
                     # 日本医药 section (2_Healthcare) 用：TOPIX ETF 代理 + 日经 225 +
                     # USDJPY 序列（仿 CNY=X/HKD=X 先例 — FX_PAIRS 只落快照，这里留完整
                     # 序列供 1305.T/^N225 的 JPY→USD 换算）。
                     # ⚠️ TOPIX 代理用 1305.T（大和）不是 1306.T（野村）：1306.T 2026-03-30
                     # 10:1 拆股，Yahoo 缺 split factor → auto_adjust 修不掉 −90% 假断崖。
                     "1305.T", "^N225", "JPY=X"]
# NB: 恒生医疗保健 (HSHCI.HK) is NOT here — yfinance has no pure HK healthcare index.
# It is iFind-seeded via jobs/fetch_cn_benchmarks.py (cron can't reach iFind).

# yfinance.info → company_profile column map (column name == yf.info key, so the
# Ticker Drill page can keep using info.get('ebitda') etc unchanged).
PROFILE_FIELDS = [
    "ebitda", "totalCash", "totalDebt", "totalRevenue", "revenueGrowth",
    "freeCashflow",   # FCF margin = freeCashflow/totalRevenue (Rule-of-40 matrix);
                      # both reporting-currency → ratio is currency-neutral.
    "grossMargins", "operatingMargins", "profitMargins", "returnOnEquity",
    "trailingPegRatio", "dividendYield", "beta", "sharesOutstanding",
    "floatShares", "longBusinessSummary",
]

BATCH_SIZE = 40                   # yfinance batch download size
SLEEP_BETWEEN_INFO = 0.4          # seconds between .info calls (rate limit, M4 doubled)
INFO_MAX_RETRY = 4                # M4: max retries per ticker
INFO_BACKOFF_BASE = 1.5           # M4: exp backoff multiplier
INFO_FAIL_THRESHOLD = 0.20        # M4: fail workflow if >20% .info calls fail


def cap_tier(mcap_usd: float | None) -> str | None:
    """M11: classify market cap into tier."""
    if mcap_usd is None or pd.isna(mcap_usd):
        return None
    if mcap_usd >= 200e9:
        return "mega"
    if mcap_usd >= 50e9:
        return "large"
    if mcap_usd >= 10e9:
        return "mid"
    if mcap_usd >= 2e9:
        return "small"
    return "micro"


# ----- args -----
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--backfill-days", type=int, default=0,
                   help="Days of historical price to backfill (0 = today only).")
    p.add_argument("--skip-multiples", action="store_true",
                   help="Skip yfinance.info multiples fetch (faster, prices only).")
    p.add_argument("--limit", type=int, default=0,
                   help="Process only first N tickers (debug).")
    p.add_argument("--only", type=str, default="",
                   help="Comma-separated tickers to process only (targeted refresh, "
                        "e.g. a new comp group). Overrides --limit.")
    return p.parse_args()


# ----- DB helpers -----
def get_tickers(conn: sqlite3.Connection, limit: int = 0, only: str = "") -> list[str]:
    if only:
        want = [t.strip() for t in only.split(",") if t.strip()]
        have = {row[0] for row in conn.execute(
            "SELECT DISTINCT ticker FROM universe_member").fetchall()}
        return [t for t in want if t in have]
    q = "SELECT DISTINCT ticker FROM universe_member ORDER BY ticker"
    if limit > 0:
        q += f" LIMIT {limit}"
    return [row[0] for row in conn.execute(q).fetchall()]


def upsert_prices(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        """INSERT OR REPLACE INTO prices_daily
           (ticker, date, open, high, low, close, adj_close, volume, currency,
            close_usd, adj_close_usd)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return len(rows)


def upsert_multiples(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        """INSERT OR REPLACE INTO multiples_daily
           (ticker, date, market_cap_usd, mcap_tier, trailing_pe, forward_pe,
            trailing_eps, forward_eps, ev_ebitda, ev_sales, fcf_yield,
            peg, pb, ytd_return, last_price, last_price_usd, currency,
            target_price_mean, recommendation_mean, n_analysts)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return len(rows)


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
        (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )


# ----- FX rate snapshot -----
def fetch_fx_rates(prev_rates: dict[str, float] | None = None) -> dict[str, float]:
    """Get current USD-conversion factors. {ccy → ccy/USD multiplier}.

    M1/m1 audit fix: fail-fast — if FX 数据失败，**raise**，不 silently default to 1.0
    (which made HKD/JPY/KRW market caps wildly wrong). Optionally reuse `prev_rates`.

    Example: USDHKD=X close = 7.8 → 1 HKD = 1/7.8 USD.
    """
    rates: dict[str, float] = {"USD": 1.0}
    symbols = [pair for pair in FX_PAIRS.values() if pair is not None]
    try:
        d = yf.download(symbols, period="5d", auto_adjust=True,
                        progress=False, threads=True, group_by="ticker")
    except Exception as e:
        if prev_rates:
            print(f"[fx] download failed: {e}; reusing previous rates")
            return prev_rates
        raise RuntimeError(f"FX fetch failed and no previous rates available: {e}")

    if d.empty:
        if prev_rates:
            print("[fx] empty result; reusing previous rates")
            return prev_rates
        raise RuntimeError("FX fetch returned empty data")

    missing: list[str] = []
    for ccy, sym in FX_PAIRS.items():
        if sym is None:
            continue
        try:
            if isinstance(d.columns, pd.MultiIndex):
                ser = d[(sym, "Close")].dropna()
            else:
                ser = d["Close"].dropna()
            if ser.empty:
                missing.append(ccy)
                continue
            last = float(ser.iloc[-1])
            # USDXXX=X means how many XXX per 1 USD → invert
            # XXXUSD=X means how many USD per 1 XXX → direct
            if sym.startswith("USD"):
                rates[ccy] = 1.0 / last
            else:
                rates[ccy] = last
        except Exception as e:
            missing.append(f"{ccy}({e})")

    if missing:
        if prev_rates:
            print(f"[fx] missing pairs {missing}; backfilling from previous rates")
            for ccy in missing:
                base = ccy.split("(")[0]
                if base in prev_rates:
                    rates[base] = prev_rates[base]
        else:
            raise RuntimeError(f"FX missing pairs: {missing}")
    print(f"[fx] rates → USD: { {k: round(v, 5) for k, v in rates.items()} }")
    return rates


def last_good_fx(conn: sqlite3.Connection) -> dict[str, float] | None:
    """Recover the most recent FX snapshot from meta table."""
    cur = conn.execute(
        "SELECT value FROM meta WHERE key = 'last_fx_rates'"
    ).fetchone()
    if not cur:
        return None
    try:
        import json
        return json.loads(cur[0])
    except Exception:
        return None


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


def prices_to_rows(
    ticker: str, df: pd.DataFrame, currency: str, fx_to_usd: float = 1.0
) -> list[tuple]:
    """Convert price DataFrame to upsert rows. Includes USD-converted close/adj_close."""
    rows = []
    for ts, r in df.iterrows():
        d = ts.date().isoformat() if hasattr(ts, "date") else str(ts)[:10]
        adj_raw = r.get("Adj Close")
        close_raw = r.get("Close")
        # Explicit NaN-safe fallback (NaN is truthy in `or`, so don't use `or`)
        adj = _safe_float(adj_raw) if not pd.isna(adj_raw) else _safe_float(close_raw)
        close = _safe_float(close_raw)
        close_usd = close * fx_to_usd if close is not None else None
        adj_usd = adj * fx_to_usd if adj is not None else None
        rows.append((
            ticker, d,
            _safe_float(r.get("Open")),
            _safe_float(r.get("High")),
            _safe_float(r.get("Low")),
            close,
            adj,
            _safe_int(r.get("Volume")),
            currency,
            close_usd,
            adj_usd,
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
    """Single-ticker .info fetch with exponential backoff + jitter (M4)."""
    import random
    for attempt in range(INFO_MAX_RETRY):
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            if info and (info.get("marketCap") or info.get("regularMarketPrice")):
                return info
            # Sparse / no useful fields — treat as fail and retry
        except Exception as e:
            print(f"[info] {ticker} attempt {attempt + 1}/{INFO_MAX_RETRY} fail: {e}")
        # Exp backoff with jitter: 0.6s, 1.5s, 3.4s, 7.6s
        sleep_s = (INFO_BACKOFF_BASE ** attempt) * 0.6 + random.uniform(0, 0.3)
        time.sleep(sleep_s)
    return None


def info_to_multiple_row(
    ticker: str, info: dict, snapshot_date: str, fx: dict[str, float]
) -> tuple | None:
    """Convert yfinance.info dict → multiples_daily row tuple."""
    ccy = (info.get("currency") or info.get("financialCurrency") or "USD").upper()
    fx_to_usd = fx.get(ccy, 1.0)
    mcap_local = _safe_float(info.get("marketCap"))
    mcap_usd = mcap_local * fx_to_usd if mcap_local is not None else None
    last_price = _safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
    last_price_usd = last_price * fx_to_usd if last_price is not None else None
    # FCF Yield: explicit guard (M1 audit nit — `a and b and a/b` is dangerous if 0)
    fcf = _safe_float(info.get("freeCashflow"))
    fcf_yield = (fcf / mcap_local) if (fcf is not None and mcap_local and mcap_local > 0) else None

    return (
        ticker,
        snapshot_date,
        mcap_usd,
        cap_tier(mcap_usd),                          # M11: mcap_tier
        _safe_float(info.get("trailingPE")),
        _safe_float(info.get("forwardPE")),
        _safe_float(info.get("trailingEps")),
        _safe_float(info.get("forwardEps")),
        _safe_float(info.get("enterpriseToEbitda")),
        _safe_float(info.get("enterpriseToRevenue")),
        fcf_yield,
        _safe_float(info.get("pegRatio") or info.get("trailingPegRatio")),
        _safe_float(info.get("priceToBook")),
        _safe_float(info.get("ytdReturn")),         # may be None for individual stocks
        last_price,                                   # local ccy
        last_price_usd,                               # M1: USD
        ccy,                                          # currency from info
        # m8 audit: sell-side consensus fields
        _safe_float(info.get("targetMeanPrice")),
        _safe_float(info.get("recommendationMean")),
        _safe_int(info.get("numberOfAnalystOpinions")),
    )


# ----- benchmarks -----
def upsert_benchmarks(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    if not rows:
        return 0
    conn.executemany(
        "INSERT OR REPLACE INTO benchmarks_daily (ticker, date, close) VALUES (?, ?, ?)",
        rows,
    )
    return len(rows)


def fetch_benchmarks(conn: sqlite3.Connection, start: str, end: str) -> int:
    """Download benchmark index closes and store them. INVARIANT: use yf.download
    (not Ticker().history) for index tickers like ^HSI."""
    try:
        d = yf.download(
            BENCHMARK_TICKERS, start=start, end=end,
            auto_adjust=True, progress=False, threads=True, group_by="ticker",
        )
    except Exception as e:  # noqa: BLE001
        print(f"[bench] download failed: {e}")
        return 0
    total = 0
    for t in BENCHMARK_TICKERS:
        try:
            if isinstance(d.columns, pd.MultiIndex):
                ser = d[t]["Close"].dropna() if t in d.columns.get_level_values(0) else pd.Series(dtype=float)
            else:
                ser = d["Close"].dropna()
            rows = [(t, idx.date().isoformat(), float(v)) for idx, v in ser.items()]
            n = upsert_benchmarks(conn, rows)
            total += n
            print(f"[bench] {t}: {n} rows" + ("" if n else "  <- EMPTY"))
        except Exception as e:  # noqa: BLE001
            print(f"[bench] {t}: parse failed ({e})")
    conn.commit()
    return total


# ----- company profile (.info → company_profile) -----
def upsert_profile(conn: sqlite3.Connection, ticker: str, info: dict) -> None:
    """Persist profile fields from an already-fetched .info dict (no extra request)."""
    vals = {f: info.get(f) for f in PROFILE_FIELDS}
    # numeric-ish fields → float; longBusinessSummary stays text
    for f in PROFILE_FIELDS:
        if f != "longBusinessSummary":
            vals[f] = _safe_float(vals[f])
    cols = ["ticker", "fetched_at", *PROFILE_FIELDS]
    placeholders = ", ".join("?" * len(cols))
    conn.execute(
        f"INSERT OR REPLACE INTO company_profile ({', '.join(cols)}) VALUES ({placeholders})",
        (ticker, datetime.now(timezone.utc).isoformat(timespec="seconds"),
         *[vals[f] for f in PROFILE_FIELDS]),
    )


# ----- main -----
def main() -> None:
    args = parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Run init_db.py first.")

    conn = sqlite3.connect(DB_PATH)
    tickers = get_tickers(conn, limit=args.limit, only=args.only)
    if not tickers:
        print("[fetch_eod] No tickers — run load_universe.py first.")
        return

    today = date.today()
    end = (today + timedelta(days=1)).isoformat()    # exclusive in yfinance
    start = (today - timedelta(days=max(args.backfill_days, 5))).isoformat()
    snapshot_date = today.isoformat()

    print(f"[fetch_eod] tickers={len(tickers)} | start={start} | end={end}")

    # 1. FX rates (M1/m1 audit: fail-fast, with last-good fallback)
    import json
    prev_fx = last_good_fx(conn)
    fx = fetch_fx_rates(prev_rates=prev_fx)
    set_meta(conn, "last_fx_rates", json.dumps(fx))

    # 2. Build ticker → currency lookup from universe_member.region
    region_to_ccy = {
        "US": "USD", "HK": "HKD", "JP": "JPY",
        "KR": "KRW", "CN": "CNY", "EU": "EUR", "UK": "GBP", "CH": "CHF",
    }
    ccy_map: dict[str, str] = {}
    cur = conn.execute("SELECT ticker, region FROM universe_member")
    for t, r in cur.fetchall():
        ccy_map[t] = region_to_ccy.get(r, "USD")

    # 3. Batch fetch prices (M1: store USD-converted close + m2: log missing tickers)
    total_prices = 0
    price_fails: list[str] = []
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        bnum = i // BATCH_SIZE + 1
        total_b = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"[prices] batch {bnum}/{total_b} ({len(batch)} tickers)")
        result = fetch_prices_batch(batch, start=start, end=end)
        missing_in_batch = set(batch) - set(result.keys())
        if missing_in_batch:
            print(f"[prices] batch {bnum} MISSING: {sorted(missing_in_batch)}")
            price_fails.extend(missing_in_batch)
        for t, df in result.items():
            ccy = ccy_map.get(t, "USD")
            fx_to_usd = fx.get(ccy, 1.0)
            rows = prices_to_rows(t, df, ccy, fx_to_usd=fx_to_usd)
            total_prices += upsert_prices(conn, rows)
        conn.commit()
        time.sleep(0.5)
    print(f"[prices] total upserted rows: {total_prices}, missing={len(price_fails)}")
    # m2 audit: fail loudly if too many missing
    if len(tickers) > 0 and len(price_fails) / len(tickers) > 0.10:
        raise RuntimeError(
            f"[prices] FAIL: {len(price_fails)}/{len(tickers)} tickers missing (>10% threshold): "
            f"{price_fails[:20]}"
        )

    # 3b. Benchmark indices (cron-cached so home page never calls live yfinance).
    #     Needs a longer window than prices for 1M/YTD returns.
    bench_start = (today - timedelta(days=200)).isoformat()
    n_bench = fetch_benchmarks(conn, start=bench_start, end=end)
    print(f"[bench] total benchmark rows upserted: {n_bench}")

    # 4. Multiples (.info) — M4 audit: track failure rate and raise if > threshold
    if not args.skip_multiples:
        total_mult = 0
        ok = 0
        fail_list: list[str] = []
        for idx, t in enumerate(tickers, 1):
            info = fetch_info_for(t)
            if not info:
                fail_list.append(t)
                continue
            row = info_to_multiple_row(t, info, snapshot_date, fx)
            if row:
                total_mult += upsert_multiples(conn, [row])
                ok += 1
            upsert_profile(conn, t, info)   # piggyback profile from same .info dict
            if idx % 20 == 0:
                conn.commit()
                print(f"[mult] progress {idx}/{len(tickers)} (ok={ok}, fail={len(fail_list)})")
            time.sleep(SLEEP_BETWEEN_INFO)
        conn.commit()
        fail_rate = len(fail_list) / max(len(tickers), 1)
        print(f"[mult] done. ok={ok} fail={len(fail_list)} ({fail_rate:.1%}) rows={total_mult}")
        if fail_list:
            print(f"[mult] failed tickers: {fail_list}")
        if fail_rate > INFO_FAIL_THRESHOLD:
            raise RuntimeError(
                f"[mult] FAIL: {len(fail_list)}/{len(tickers)} (>{INFO_FAIL_THRESHOLD:.0%}) "
                f".info fetches failed — treat as data outage."
            )
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
