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
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import parquet_store as pq  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"

# ── PR4 dual write ────────────────────────────────────────────────────────
# Every row committed to SQLite is also staged for the Parquet store and flushed
# at the same three commit boundaries the SQLite path already has. Staged rather
# than written row-by-row because `upsert_multiples` is called once PER TICKER
# (~500×/run) and each call would otherwise re-read and rewrite the whole month
# partition. Column tuples mirror the INSERT statements below — they are the same
# order, and they must stay that way.
_PQ_COLS = {
    "prices_daily": ["ticker", "date", "open", "high", "low", "close", "adj_close",
                     "volume", "currency", "close_usd", "adj_close_usd"],
    "multiples_daily": ["ticker", "date", "market_cap_usd", "mcap_tier", "trailing_pe",
                        "forward_pe", "trailing_eps", "forward_eps", "ev_ebitda",
                        "ev_sales", "fcf_yield", "peg", "pb", "ytd_return",
                        "last_price", "last_price_usd", "currency",
                        "target_price_mean", "recommendation_mean", "n_analysts"],
    "benchmarks_daily": ["ticker", "date", "close"],
}
_PQ_BUF: dict[str, list[tuple]] = {t: [] for t in _PQ_COLS}


def _pq_stage(table: str, rows: list[tuple]) -> None:
    if rows and pq.dual_write_enabled():
        _PQ_BUF[table].extend(rows)


def _pq_flush(table: str) -> None:
    """Write one staged table to Parquet. Mirrors a `conn.commit()` boundary."""
    rows, _PQ_BUF[table] = _PQ_BUF[table], []
    if not rows:
        return
    parts = pq.dual_write(table, rows, _PQ_COLS[table])
    if parts:
        print(f"[parquet] {table}: {len(rows)} rows → "
              f"{', '.join(f'{k}({v})' for k, v in sorted(parts.items()))}")


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
def _has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    """Does `table` have `col` in the DB this process opened?

    Mirrors app/lib/db.py:_has_column. `universe_member.status` is added by
    jobs/load_universe.py's idempotent migration, and this job can run either
    side of it (fresh CI checkout runs load_universe first; a local invocation
    may not) — so ask before filtering rather than crash on a pre-migration DB.
    """
    try:
        return col in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    except sqlite3.Error:
        return False


def get_tickers(conn: sqlite3.Connection, limit: int = 0, only: str = "") -> list[str]:
    # R3 audit (Medium): without the status filter this job spent 4 `.info`
    # retries/day plus a slice of the >10% failure budget on names that can never
    # return data. The count is whatever `universe_member.status` says today, not
    # a constant — measured 2026-09-07: 508 tickers → 494 active, 14 excluded
    # (13 delisted + 1 renamed). Quote the column, not a remembered number.
    active = " WHERE status IS NULL" if _has_column(conn, "universe_member", "status") else ""
    if only:
        want = [t.strip() for t in only.split(",") if t.strip()]
        have = {row[0] for row in conn.execute(
            f"SELECT DISTINCT ticker FROM universe_member{active}").fetchall()}
        return [t for t in want if t in have]
    q = f"SELECT DISTINCT ticker FROM universe_member{active} ORDER BY ticker"
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
    _pq_stage("prices_daily", rows)      # PR4 dual write (flushed at the commit boundary)
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
    _pq_stage("multiples_daily", rows)   # PR4 dual write (flushed at the commit boundary)
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
    skipped: list[str] = []
    for ts, r in df.iterrows():
        d = ts.date().isoformat() if hasattr(ts, "date") else str(ts)[:10]
        adj_raw = r.get("Adj Close")
        close_raw = r.get("Close")
        # Explicit NaN-safe fallback (NaN is truthy in `or`, so don't use `or`)
        adj = _safe_float(adj_raw) if not pd.isna(adj_raw) else _safe_float(close_raw)
        close = _safe_float(close_raw)
        if close is None:
            # A bar with OHLV but no close is a partial/in-session or broken bar
            # (2026-09-04: 292/491 rows). Persisting it would let INSERT OR
            # REPLACE overwrite a good close with NULL on the next window.
            skipped.append(d)
            continue
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
    if skipped:
        print(f"[prices] {ticker}: skipped {len(skipped)} bar(s) without a close: {skipped}")
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


def latest_bar(conn: sqlite3.Connection, ticker: str) -> tuple[float, str] | None:
    """Most recent `prices_daily` (close in LOCAL ccy, date) for `ticker`, or None.

    Deliberately the LATEST bar rather than the snapshot date's: prices and the
    `.info` snapshot are written on different calendars (audit H5 — the snapshot
    stamp is the runner's UTC `date.today()`, the bar carries the exchange date),
    so requiring an exact date match would silently disable the cross-check on
    every non-US ticker.

    The DATE comes back with the close because the two are not separable
    evidence: a 2× gap against yesterday's bar is a frozen payload, the same gap
    against a bar three weeks old is just an unpriced ticker. Callers must be
    able to say which they saw, so `info_to_multiple_row` logs the date.
    """
    try:
        r = conn.execute(
            "SELECT close, date FROM prices_daily WHERE ticker = ? AND close IS NOT NULL "
            "ORDER BY date DESC LIMIT 1", (ticker,)
        ).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    close = _safe_float(r[0])
    return (close, str(r[1])) if close is not None else None


# A frozen `.info` payload can disagree wildly with the day's real bar. Measured
# 2026-09-07: 108320.KQ carried a constant multiples price of 78,000 across 27-64
# snapshots while prices_daily moved 36,550 → 37,800 — a 2.06× divergence rendered
# as a valuation time series. Beyond this ratio the row is not trustworthy.
INFO_PRICE_MAX_DIVERGENCE = 0.5


def info_to_multiple_row(
    ticker: str, info: dict, snapshot_date: str, fx: dict[str, float],
    bar_close: float | None = None, bar_date: str | None = None,
) -> tuple | None:
    """Convert yfinance.info dict → multiples_daily row tuple, or None if unusable.

    R3 audit C5 — this returned a tuple unconditionally, so the `if row:` guard at
    the call site was tautologically true and a payload with no price at all still
    produced a `multiples_daily` row (10 tickers ended up with a single constant
    "price" spanning 27-64 snapshots).

    `bar_close` / `bar_date` are the newest `prices_daily` close (LOCAL currency)
    and its exchange date, when one exists.

    A gross divergence between the two prices DROPS THE WHOLE ROW. The first cut
    of this fix overwrote `last_price` with the bar close and kept everything
    else — which shipped a row whose price said 50 while its market_cap implied
    110 and its trailing_pe implied 110. Every derived multiple in that row is
    keyed to the `.info` price; substituting one field does not re-derive the
    rest, it just makes the inconsistency undetectable downstream. The two
    sources disagree about what this instrument is worth and NEITHER can key the
    other's multiples, so the row is dropped and the ticker is counted as a
    failure by `run_multiples` (a systematic mismatch must show up in the failure
    rate, not vanish). Dropping is also the only safe answer to the ambiguity in
    the comparison itself: `bar_date` may be weeks stale, so a 2× gap is equally
    consistent with a frozen payload and with a legitimate pop or a split on a
    ticker whose today-bar is missing — we log both sides and refuse to guess.
    """
    ccy = (info.get("currency") or info.get("financialCurrency") or "USD").upper()
    fx_to_usd = fx.get(ccy, 1.0)
    mcap_local = _safe_float(info.get("marketCap"))
    mcap_usd = mcap_local * fx_to_usd if mcap_local is not None else None
    last_price = _safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
    if last_price is None:
        # No usable price → not a valuation snapshot. Dropping the row is right:
        # the multiples are keyed to a price the payload does not carry.
        print(f"[mult] {ticker}: no regularMarketPrice/currentPrice in .info — row skipped")
        return None
    bar = _safe_float(bar_close)
    if bar is not None and bar > 0 and abs(last_price / bar - 1) > INFO_PRICE_MAX_DIVERGENCE:
        print(f"[mult] DROP {ticker} {snapshot_date}: .info price {last_price} vs "
              f"prices_daily close {bar} (bar_date={bar_date or '?'}) — "
              f"{last_price / bar:.2f}× divergence, row dropped (audit C5)")
        return None
    last_price_usd = last_price * fx_to_usd
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
    _pq_stage("benchmarks_daily", rows)  # PR4 dual write (flushed at the commit boundary)
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
    _pq_flush("benchmarks_daily")
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


# ----- multiples pass -----
class MultiplesResult(NamedTuple):
    """Outcome of one `.info` pass. Every ticker lands in exactly one bucket."""
    ok: int                 # rows written
    priceless: list[str]    # fetched fine, but the payload could not be trusted
    failed: list[str]       # `.info` fetch itself failed (network / delisted)
    rows: int               # upsert row count


def run_multiples(
    conn: sqlite3.Connection,
    tickers: list[str],
    snapshot_date: str,
    fx: dict[str, float],
    sleep_s: float = SLEEP_BETWEEN_INFO,
) -> MultiplesResult:
    """Fetch `.info` for every ticker, write multiples, and police the outcome.

    REVIEW FIXUP — the accounting is the point of this function existing.
    `info_to_multiple_row` can return None (no price, or a gross divergence from
    the tape). The previous call site only ever incremented `ok` on a truthy row,
    so a dropped ticker was neither ok NOR failed: it fell out of the arithmetic
    entirely. A metadata-only yfinance outage — every `.info` request succeeds,
    none carries a price — therefore produced ok=0, fail=0, fail_rate=0.0, no
    exception, zero rows written, and a workflow that stamped `eod_prices ok`.
    The guard existed and could not fire, because the thing it measured was
    "requests that errored", not "tickers we got usable data for".

    Both drop reasons are folded into ONE rate against INFO_FAIL_THRESHOLD rather
    than given a second threshold: from the dashboard's point of view a ticker
    with no valuation row today is the same event however the payload failed, and
    a single number cannot be gamed by an outage that shifts tickers from one
    bucket to the other.
    """
    total_rows = 0
    ok = 0
    failed: list[str] = []
    priceless: list[str] = []

    for idx, t in enumerate(tickers, 1):
        info = fetch_info_for(t)
        if not info:
            failed.append(t)
            continue
        bar = latest_bar(conn, t)
        row = info_to_multiple_row(
            t, info, snapshot_date, fx,
            bar_close=bar[0] if bar else None,
            bar_date=bar[1] if bar else None,
        )
        if row:
            total_rows += upsert_multiples(conn, [row])
            ok += 1
        else:
            priceless.append(t)
        upsert_profile(conn, t, info)   # piggyback profile from same .info dict
        if idx % 20 == 0:
            conn.commit()
            print(f"[mult] progress {idx}/{len(tickers)} "
                  f"(ok={ok}, priceless={len(priceless)}, failed={len(failed)})")
        if sleep_s:
            time.sleep(sleep_s)
    conn.commit()
    _pq_flush("multiples_daily")

    unusable = len(priceless) + len(failed)
    fail_rate = unusable / max(len(tickers), 1)
    print(f"[mult] done. ok={ok} priceless={len(priceless)} failed={len(failed)} "
          f"unusable={unusable}/{len(tickers)} ({fail_rate:.1%}) rows={total_rows}")
    if failed:
        print(f"[mult] .info fetch failed: {failed}")
    if priceless:
        print(f"[mult] dropped (no usable price / tape divergence): {priceless}")
    if fail_rate > INFO_FAIL_THRESHOLD:
        raise RuntimeError(
            f"[mult] FAIL: {unusable}/{len(tickers)} tickers produced no usable "
            f"multiples row (>{INFO_FAIL_THRESHOLD:.0%}) — "
            f"{len(failed)} .info fetch failures + {len(priceless)} unusable payloads. "
            f"Treat as a data outage."
        )
    return MultiplesResult(ok=ok, priceless=priceless, failed=failed, rows=total_rows)


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
    _pq_flush("prices_daily")
    print(f"[prices] total upserted rows: {total_prices}, missing={len(price_fails)}")
    # m2 audit: fail loudly if too many missing
    if len(tickers) > 0 and len(price_fails) / len(tickers) > 0.10:
        raise RuntimeError(
            f"[prices] FAIL: {len(price_fails)}/{len(tickers)} tickers missing (>10% threshold): "
            f"{price_fails[:20]}"
        )

    # 3b. Benchmark indices (cron-cached so home page never calls live yfinance).
    #     Needs a longer window than prices for 1M/YTD returns. Respect a deeper
    #     --backfill-days too（曾硬编码 200 天 → JP 面板基准比 40 支价格短 2 个月，
    #     图表共同锚被钉在基准起点，市值加权 vs 等权的 9-11 月分歧全被锚掉）。
    bench_start = (today - timedelta(days=max(200, args.backfill_days or 0))).isoformat()
    n_bench = fetch_benchmarks(conn, start=bench_start, end=end)
    print(f"[bench] total benchmark rows upserted: {n_bench}")

    # 4. Multiples (.info) — M4 audit + C5 review fixup: see run_multiples(). It
    #    raises when too many tickers yield no usable row, which is what stops the
    #    workflow stamping `eod_prices ok` over an outage.
    if not args.skip_multiples:
        run_multiples(conn, tickers, snapshot_date, fx)
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
