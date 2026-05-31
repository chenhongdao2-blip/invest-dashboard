#!/usr/bin/env python3
"""Precompile sector peer-median derived ratios into table sec_peer_median.

OFFLINE. Reads only the committed snapshots.db (gzip'd companyfacts payloads via
sec_facts) — no network. For every (domain, sector) in universe_member it builds
the peer set = US tickers in that (domain, sector) that are present in the SEC
ok-pool (sf.us_pool() with sec_status=='ok'), computes the 6 derived ratios per
fiscal year per peer USING THE SAME LOGIC AS sec_statements (we IMPORT and reuse
sec_statements._section_series + replicate the exact numerator/denominator pairs
of _derived_df, so tag chains / 口径 never drift), then takes the MEDIAN across
peers per (domain, sector, metric, year) with a peer count n.

口径 (peer set): peers of ticker T in domain D = distinct US tickers with
sec_status=='ok' sharing >=1 sector with T in universe_member(domain=D). Here we
precompute per (domain, sector); the reader (sf.peer_medians) selects T's PRIMARY
sector (sector with the most peers among T's sectors) and excludes T implicitly
(T's own ratios are part of its own sector median — that is the standard "sector
median including self" convention; the reader returns the sector aggregate, the
page overlays T's own line on top for the variance read).

Ratios (metric keys, EXACT): gross_margin, operating_margin, net_margin,
fcf_margin, roe, debt_to_assets — each a per-year percentage (same scale as the
衍生指标 block: value already ×100).

Schema: sec_peer_median(domain TEXT, sector TEXT, metric TEXT, year INTEGER,
median REAL, n INTEGER). DROP+CREATE only this table (DB is backed up; other
tables untouched). Read-WRITE connect to db.DB_PATH (NOT mode=ro).

Run:
  HTTPS_PROXY=http://127.0.0.1:7897 SEC_PROXY=http://127.0.0.1:7897 \
    uv run --python 3.12 --with-requirements requirements.txt \
    python jobs/build_peer_medians.py
(no network is actually used; proxy env is harmless.)

Resilience: a peer that errors is logged and skipped; one bad peer never aborts
the build.
"""

from __future__ import annotations

import sqlite3
import statistics
import sys
import traceback
from pathlib import Path

# sec_facts.py does `from lib import db`, so app/ must be on sys.path (the repo
# root is NOT enough). Mirror the probe's fix.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _REPO_ROOT / "app"
for _p in (str(_APP_DIR), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib import db                       # noqa: E402
from lib import sec_facts as sf          # noqa: E402
from lib import sec_statements as ss     # noqa: E402

DB_PATH = db.DB_PATH

# Metric keys are EXACT and must match sf.peer_medians + the page consumer.
METRICS = ("gross_margin", "operating_margin", "net_margin",
           "fcf_margin", "roe", "debt_to_assets")


def _peer_ratios(ticker: str) -> dict[str, dict[int, float]]:
    """Per-year derived ratios for ONE peer, reusing sec_statements series logic.

    Returns {metric: {year: pct}} (pct already ×100, matching the 衍生指标 block).
    Mirrors sec_statements._derived_df numerator/denominator pairs EXACTLY; only
    the per-year ratio math is inlined here (the page's _derived_df returns a
    DataFrame keyed by years-of-interest, which we don't want — we want every
    year the peer has). Underlying series come from the SHARED _section_series so
    tag fallback chains are never re-implemented.

    CURRENCY-AGNOSTIC (DECISION 1): the 6 metrics are RATIOS (num/den in the SAME
    currency) → unitless. Foreign IFRS filers (TSM/ASX report TWD, GSK GBP) only
    report monetary facts in their local currency, so we fetch each peer in its
    OWN taxonomy AND its OWN dominant monetary unit (auto-detected) rather than
    forcing USD. No FX conversion needed — the ratio cancels the currency.
    """
    status = sf.company_status(ticker) or {}
    tax = status.get("taxonomy_primary") or "us-gaap"

    # Per-peer reporting currency (e.g. TWD for TSM/ASX, GBP for GSK, USD else).
    # Falls back to USD so domestic us-gaap filers are unchanged.
    mon_unit = ss.dominant_monetary_unit(ticker, tax) or "USD"

    inc = ss._section_series(ticker, tax, ss.INCOME_ROWS, "annual", monetary_unit=mon_unit)
    bal = ss._section_series(ticker, tax, ss.BALANCE_ROWS, "annual", monetary_unit=mon_unit)
    cf = ss._section_series(ticker, tax, ss.CASHFLOW_ROWS, "annual", monetary_unit=mon_unit)

    rev = inc.get("revenue", {}) or {}
    gp = inc.get("gross_profit", {}) or {}
    oi = inc.get("operating_income", {}) or {}
    ni = inc.get("net_income", {}) or {}
    fcf = cf.get("fcf", {}) or {}
    eq = bal.get("equity", {}) or {}
    tl = bal.get("total_liabilities", {}) or {}
    ta = bal.get("total_assets", {}) or {}

    def _pct(num_map: dict, den_map: dict) -> dict[int, float]:
        out: dict[int, float] = {}
        for y, d in den_map.items():
            n = num_map.get(y)
            if n is not None and d not in (None, 0):
                out[y] = n / d * 100.0
        return out

    return {
        "gross_margin":     _pct(gp, rev),   # 毛利率
        "operating_margin": _pct(oi, rev),   # 营业利润率
        "net_margin":       _pct(ni, rev),   # 净利率
        "fcf_margin":       _pct(fcf, rev),  # 自由现金流利润率
        "roe":              _pct(ni, eq),    # ROE = net_income / equity
        "debt_to_assets":   _pct(tl, ta),    # 资产负债率 = total_liabilities / total_assets
    }


def _ok_pool_by_domain() -> dict[str, set[str]]:
    """{domain: set(upper-ticker)} for sec_status=='ok' US names in the pool."""
    pool = sf.us_pool()
    ok = pool[pool["sec_status"] == "ok"].copy()
    ok["t"] = ok["ticker"].astype(str).str.upper()
    out: dict[str, set[str]] = {}
    for dom in ok["domain"].dropna().unique():
        out[str(dom)] = set(ok[ok["domain"] == dom]["t"])
    return out


def _sectors_for_domain(con: sqlite3.Connection, domain: str) -> dict[str, list[str]]:
    """{sector: [upper-ticker, ...]} from universe_member for a domain."""
    cur = con.execute(
        "SELECT sector, ticker FROM universe_member WHERE domain = ?", (domain,)
    )
    out: dict[str, list[str]] = {}
    for sector, ticker in cur.fetchall():
        if sector is None or ticker is None:
            continue
        out.setdefault(str(sector), []).append(str(ticker).upper())
    return out


def build() -> None:
    domains = ("healthcare", "ai")
    ok_by_dom = _ok_pool_by_domain()

    # ratio cache: compute each peer's ratios once (a ticker may sit in >1 sector,
    # e.g. _coverage + a real sector — avoid recomputing the heavy series).
    ratio_cache: dict[str, dict[str, dict[int, float]]] = {}

    def get_ratios(t: str) -> dict[str, dict[int, float]]:
        if t not in ratio_cache:
            try:
                ratio_cache[t] = _peer_ratios(t)
            except Exception as e:  # resilient: skip a broken peer
                print(f"  [skip] {t}: {type(e).__name__}: {e}", flush=True)
                ratio_cache[t] = {m: {} for m in METRICS}
        return ratio_cache[t]

    # (domain, sector, metric, year) -> [values]
    agg: dict[tuple[str, str, str, int], list[float]] = {}

    # read membership from a temporary read-only-ish connection (the build conn is
    # created later; reuse db.query which opens its own ro conn).
    ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        for domain in domains:
            dom_ok = ok_by_dom.get(domain, set())
            sectors = _sectors_for_domain(ro, domain)
            print(f"\n=== DOMAIN {domain}: {len(sectors)} sectors, "
                  f"{len(dom_ok)} ok-pool tickers ===", flush=True)
            for sector, members in sorted(sectors.items()):
                # _coverage is a curated catch-all overlay, NOT a real industry
                # sector → its members are not valid comparables. Skip it so it
                # never produces a peer-median row (DECISION 3).
                if sector == "_coverage":
                    print(f"  sector {sector!r}: catch-all overlay -> skip", flush=True)
                    continue
                peers = sorted(set(members) & dom_ok)
                if not peers:
                    print(f"  sector {sector!r}: 0 peers in ok-pool -> skip", flush=True)
                    continue
                print(f"  sector {sector!r}: {len(peers)} peers -> {peers[:8]}"
                      f"{' ...' if len(peers) > 8 else ''}", flush=True)
                for t in peers:
                    ratios = get_ratios(t)
                    for metric in METRICS:
                        for year, val in (ratios.get(metric) or {}).items():
                            if val is None:
                                continue
                            agg.setdefault((domain, sector, metric, int(year)), []).append(float(val))
    finally:
        ro.close()

    # aggregate -> median + n
    rows: list[tuple[str, str, str, int, float, int]] = []
    for (domain, sector, metric, year), vals in agg.items():
        clean = [v for v in vals if v is not None]
        if not clean:
            continue
        rows.append((domain, sector, metric, year, float(statistics.median(clean)), len(clean)))
    rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))

    # write (DROP + CREATE only this table; non-destructive to others)
    con = sqlite3.connect(str(DB_PATH))
    try:
        con.execute("DROP TABLE IF EXISTS sec_peer_median")
        con.execute(
            """CREATE TABLE sec_peer_median (
                   domain TEXT NOT NULL,
                   sector TEXT NOT NULL,
                   metric TEXT NOT NULL,
                   year   INTEGER NOT NULL,
                   median REAL,
                   n      INTEGER,
                   PRIMARY KEY (domain, sector, metric, year)
               )"""
        )
        con.executemany(
            "INSERT INTO sec_peer_median (domain, sector, metric, year, median, n) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        con.commit()
    finally:
        con.close()

    # summary
    print(f"\n[OK] wrote {len(rows)} rows to sec_peer_median", flush=True)
    by_dom: dict[str, int] = {}
    for r in rows:
        by_dom[r[0]] = by_dom.get(r[0], 0) + 1
    print(f"  rows per domain: {by_dom}", flush=True)
    print("  sample rows (domain, sector, metric, year, median, n):", flush=True)
    for r in rows[:12]:
        print(f"    {r[0]:11s} {r[1]:16s} {r[2]:17s} {r[3]}  median={r[4]:8.2f}  n={r[5]}", flush=True)


if __name__ == "__main__":
    try:
        build()
    except Exception:
        print("FATAL:", flush=True)
        traceback.print_exc()
        sys.exit(1)
