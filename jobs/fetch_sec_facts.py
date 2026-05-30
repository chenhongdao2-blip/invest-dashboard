"""Fetch SEC Company Facts (XBRL) for US tickers in universe_member.

Mirrors fetch_eod.py conventions (argparse, sqlite upsert, sleep-based rate limit,
fail-threshold). Industry-agnostic: pulls every region='US' ticker regardless of
domain. Foreign filers (NVS/AZN/BNTX...) report under ifrs-full not us-gaap — we
flatten ALL taxonomies, so downstream KPI selection falls back across taxonomies.
OTC ADRs absent from company_tickers.json (RHHBY/LZAGY) are marked 'not_mapped'.

Network:
    - User-Agent is MANDATORY (SEC 403s a missing/default UA). Override via SEC_UA.
    - Proxy is OPTIONAL: set SEC_PROXY=http://127.0.0.1:7897 when running from
      mainland China. Unset on GitHub Actions (US runners reach SEC directly).

Usage:
    python jobs/fetch_sec_facts.py                       # all US tickers (skip fresh)
    SEC_PROXY=http://127.0.0.1:7897 python jobs/fetch_sec_facts.py --limit 5
    python jobs/fetch_sec_facts.py --ticker LLY --force
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"

# SEC requires a UA carrying contact info. Override with a real name+email via SEC_UA.
UA = os.environ.get("SEC_UA", "invest-dashboard research (contact: research@invest-dashboard.local)")
PROXY = os.environ.get("SEC_PROXY")  # e.g. http://127.0.0.1:7897 (local CN); unset on Actions

RATE_SLEEP = 0.5          # protective ~2 req/s (SEC ceiling is 10/s)
MAX_RETRY = 4
BACKOFF_BASE = 1.6
FAIL_THRESHOLD = 0.30     # raise only if >30% of mapped tickers fail (SEC flaps occasionally)
TIMEOUT = (10, 60)        # (connect, read)
FRESH_HOURS = 18          # skip re-fetch if snapshot younger than this (unless --force)


# ----- args -----
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=0, help="Process only first N tickers (debug).")
    p.add_argument("--ticker", type=str, default="", help="Fetch a single ticker (debug).")
    p.add_argument("--force", action="store_true", help="Re-fetch even if snapshot is fresh.")
    return p.parse_args()


# ----- http -----
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    if PROXY:
        s.proxies.update({"http": PROXY, "https": PROXY})
    return s


def http_get(session: requests.Session, url: str) -> requests.Response:
    """GET with retry on 429/5xx/network. Returns response (incl. 404). Raises on exhausted transient."""
    last = "unknown error"
    for attempt in range(MAX_RETRY):
        try:
            r = session.get(url, timeout=TIMEOUT)
            if r.status_code == 200 or r.status_code == 404:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
            else:
                # 403 (bad UA), 401 etc — not worth retrying
                r.raise_for_status()
                return r
        except requests.RequestException as e:
            last = str(e)
        time.sleep(BACKOFF_BASE ** attempt + 0.3)
    raise RuntimeError(f"GET failed after {MAX_RETRY} tries: {last}")


# ----- ticker -> CIK -----
def load_cik_map(session: requests.Session) -> dict[str, tuple[int, str, str]]:
    """Return {TICKER: (cik_int, cik10, title)} from SEC company_tickers.json."""
    r = http_get(session, SEC_TICKERS_URL)
    data = r.json()
    m: dict[str, tuple[int, str, str]] = {}
    for v in data.values():
        cik = int(v["cik_str"])
        m[str(v["ticker"]).upper()] = (cik, str(cik).zfill(10), v.get("title", ""))
    return m


def get_us_tickers(conn: sqlite3.Connection, limit: int = 0, only: str = "") -> list[str]:
    if only:
        return [only.upper()]
    rows = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT ticker FROM universe_member WHERE region = 'US' ORDER BY ticker"
        ).fetchall()
    ]
    return rows[:limit] if limit > 0 else rows


def ticker_domain(conn: sqlite3.Connection, ticker: str) -> str | None:
    row = conn.execute(
        "SELECT domain FROM universe_member WHERE ticker = ? LIMIT 1", (ticker,)
    ).fetchone()
    return row[0] if row else None


# ----- summarize companyfacts (metadata only; full facts live in the gzip payload) -----
def summarize_facts(cf: dict) -> tuple[int, str | None, str | None]:
    """Scan companyfacts JSON for metadata without persisting individual rows.

    Returns (facts_count, latest_filed, taxonomy_primary). The full payload is
    stored gzip'd and re-parsed on demand by the app, so we deliberately do NOT
    explode facts into a flat table here (avoids 600MB+ committed-DB bloat).
    taxonomy_primary = the financial taxonomy with the most facts (us-gaap | ifrs-full).
    """
    facts = cf.get("facts", {})
    count = 0
    latest_filed: str | None = None
    tax_counts: dict[str, int] = {}
    for taxonomy, concepts in facts.items():
        for cdata in concepts.values():
            for items in (cdata.get("units") or {}).values():
                for it in items:
                    if not it.get("end"):
                        continue
                    count += 1
                    tax_counts[taxonomy] = tax_counts.get(taxonomy, 0) + 1
                    filed = it.get("filed")
                    if filed and (latest_filed is None or filed > latest_filed):
                        latest_filed = filed
    fin = {k: v for k, v in tax_counts.items() if k in ("us-gaap", "ifrs-full")}
    taxonomy_primary = max(fin, key=fin.get) if fin else None
    return count, latest_filed, taxonomy_primary


# ----- db writes -----
def upsert_company(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO sec_company
           (ticker, cik, cik10, entity_name, taxonomy_primary, sec_status,
            fetched_at, latest_filed, facts_count, last_error, payload_gzip)
           VALUES (:ticker, :cik, :cik10, :entity_name, :taxonomy_primary, :sec_status,
                   :fetched_at, :latest_filed, :facts_count, :last_error, :payload_gzip)""",
        row,
    )


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
        (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )


def is_fresh(conn: sqlite3.Connection, ticker: str) -> bool:
    row = conn.execute(
        "SELECT sec_status, fetched_at FROM sec_company WHERE ticker = ?", (ticker,)
    ).fetchone()
    if not row or row[0] != "ok" or not row[1]:
        return False
    try:
        fetched = datetime.fromisoformat(row[1])
        age_h = (datetime.now(timezone.utc) - fetched).total_seconds() / 3600
        return age_h < FRESH_HOURS
    except ValueError:
        return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ----- main -----
def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at {DB_PATH}. Run jobs/init_db.py first.")

    session = make_session()
    print(f"[sec] UA={UA!r}  proxy={'on (' + PROXY + ')' if PROXY else 'off (direct)'}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cik_map = load_cik_map(session)
        print(f"[sec] CIK map loaded: {len(cik_map)} tickers")

        tickers = get_us_tickers(conn, limit=args.limit, only=args.ticker)
        print(f"[sec] universe US tickers: {len(tickers)}")

        n_ok = n_skip = n_nomap = n_fail = 0
        mapped = 0

        for idx, t in enumerate(tickers, 1):
            if t not in cik_map:
                upsert_company(conn, {
                    "ticker": t, "cik": None, "cik10": None, "entity_name": None,
                    "taxonomy_primary": None, "sec_status": "not_mapped",
                    "fetched_at": _now(), "latest_filed": None, "facts_count": 0,
                    "last_error": "not in SEC company_tickers.json (likely OTC ADR, no XBRL)",
                    "payload_gzip": None,
                })
                conn.commit()
                n_nomap += 1
                print(f"[sec] {idx}/{len(tickers)} {t}: not_mapped (skip)")
                continue

            mapped += 1
            if not args.force and is_fresh(conn, t):
                n_skip += 1
                print(f"[sec] {idx}/{len(tickers)} {t}: fresh (skip)")
                continue

            cik, cik10, title = cik_map[t]
            url = SEC_FACTS_URL.format(cik10=cik10)
            try:
                r = http_get(session, url)
                if r.status_code == 404:
                    upsert_company(conn, {
                        "ticker": t, "cik": cik, "cik10": cik10, "entity_name": title,
                        "taxonomy_primary": None, "sec_status": "no_xbrl",
                        "fetched_at": _now(), "latest_filed": None, "facts_count": 0,
                        "last_error": "companyfacts 404 (no XBRL facts filed)",
                        "payload_gzip": None,
                    })
                    conn.commit()
                    n_nomap += 1
                    print(f"[sec] {idx}/{len(tickers)} {t}: no_xbrl (404)")
                    time.sleep(RATE_SLEEP)
                    continue

                raw = r.content
                cf = json.loads(raw)
                n, latest_filed, tax_primary = summarize_facts(cf)
                upsert_company(conn, {
                    "ticker": t, "cik": cik, "cik10": cik10,
                    "entity_name": cf.get("entityName", title),
                    "taxonomy_primary": tax_primary, "sec_status": "ok",
                    "fetched_at": _now(), "latest_filed": latest_filed, "facts_count": n,
                    "last_error": None, "payload_gzip": gzip.compress(raw),
                })
                conn.commit()
                n_ok += 1
                print(f"[sec] {idx}/{len(tickers)} {t}: ok  facts={n}  taxonomy={tax_primary}  latest={latest_filed}")
            except Exception as e:  # noqa: BLE001 — persist failure, keep going
                conn.rollback()
                # Preserve a previously-good snapshot: a transient SEC/proxy outage
                # must NOT wipe usable cached data. Only record the error; keep the
                # old payload + 'ok' status if we already have one.
                prior = conn.execute(
                    "SELECT sec_status FROM sec_company WHERE ticker = ?", (t,)
                ).fetchone()
                if prior and prior[0] == "ok":
                    conn.execute(
                        "UPDATE sec_company SET last_error = ?, fetched_at = fetched_at "
                        "WHERE ticker = ?",
                        (f"refresh failed (kept prior snapshot): {str(e)[:400]}", t),
                    )
                    print(f"[sec] {idx}/{len(tickers)} {t}: refresh FAILED — kept prior cache ({e})")
                else:
                    upsert_company(conn, {
                        "ticker": t, "cik": cik, "cik10": cik10, "entity_name": title,
                        "taxonomy_primary": None, "sec_status": "failed",
                        "fetched_at": _now(), "latest_filed": None, "facts_count": 0,
                        "last_error": str(e)[:500], "payload_gzip": None,
                    })
                    print(f"[sec] {idx}/{len(tickers)} {t}: FAILED {e}")
                conn.commit()
                n_fail += 1

            time.sleep(RATE_SLEEP)

        set_meta(conn, "last_sec_fetch_utc", _now())
        conn.commit()
        print(f"[sec] done. ok={n_ok} skip={n_skip} no_data={n_nomap} fail={n_fail}")

        # fail-threshold over tickers we actually attempted (mapped & not skipped)
        attempted = mapped - n_skip
        if attempted > 0 and n_fail / attempted > FAIL_THRESHOLD:
            raise RuntimeError(
                f"[sec] >{FAIL_THRESHOLD:.0%} of attempted fetches failed "
                f"({n_fail}/{attempted}) — check proxy / UA / SEC status"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
