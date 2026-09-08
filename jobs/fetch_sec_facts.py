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
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobs import normalize_sec_facts as nsf, parquet_store as pq, sec_concepts  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "snapshots.db"

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"

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
    """Clock guard: is the stored snapshot younger than FRESH_HOURS?

    Kept as the SECONDARY guard only — see should_refetch(). A clock cannot know
    whether the company filed anything, so on its own it both re-downloads 40 MB of
    unchanged payloads every week AND leaves a same-day filing unfetched for 18h.
    """
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


def _has_sec_fact_parquet(ticker: str) -> bool:
    """Does this ticker's shadow file exist?

    An unsafe partition key reads as present on purpose: `write_sec_fact_parquet`
    cannot produce a file for one either, so treating it as missing would re-download
    a multi-MB payload every single run to satisfy a check that can never pass. No US
    ticker matches that today; the guard is here so it stays a non-event if one does.
    """
    try:
        return pq.partition_path("sec_fact", ticker).exists()
    except ValueError:
        return True


def missing_sec_fact_files(conn: sqlite3.Connection) -> list[str]:
    """Tickers whose SQLite row says 'ok' but whose shadow file is not on disk.

    The backstop for the swallowed exception in `write_sec_fact_parquet`: that write
    warns and lets the fetch stand, and unlike the daily tables there is no parity
    check downstream to catch the result — `sec_fact` shadows a BLOB, so there is
    nothing to anti-join against. This is the anti-join, done on filenames.

    Empty while the shadow write is off: there is no store to be short of.
    """
    if not pq.dual_write_enabled():
        return []
    ok = {r[0] for r in conn.execute(
        "SELECT ticker FROM sec_company WHERE sec_status = 'ok'")}
    return sorted(t for t in ok if not _has_sec_fact_parquet(t))


def latest_filed_from_submissions(session: requests.Session, cik10: str) -> str | None:
    """Newest XBRL-bearing filing date for a CIK, or None if the probe fails.

    Only XBRL filings can change companyfacts, so the `isXBRL` flag is the filter:
    without it every 8-K would look like a reason to re-download a multi-MB payload
    that did not change. Falls back to the newest filing of any kind if the flag
    array is missing, which errs toward re-fetching — the safe direction.
    """
    try:
        r = http_get(session, SEC_SUBMISSIONS_URL.format(cik10=cik10))
        if r.status_code != 200:
            return None
        recent = ((r.json().get("filings") or {}).get("recent") or {})
    except Exception:  # noqa: BLE001 — a probe failure must not fail the ticker
        return None
    dates = recent.get("filingDate") or []
    if not dates:
        return None
    flags = recent.get("isXBRL") or []
    xbrl = [d for i, d in enumerate(dates) if i < len(flags) and flags[i]]
    return max(xbrl) if xbrl else max(dates)


def should_refetch(conn: sqlite3.Connection, session: requests.Session,
                   ticker: str, cik10: str) -> tuple[bool, str]:
    """Gate the companyfacts download on NEW FILINGS, not on a clock. → (fetch?, why).

    The 18-hour clock this replaces answered the wrong question. companyfacts only
    changes when the company files, so the right question is "has it filed since our
    snapshot?" — one small submissions request answers it and saves the multi-MB
    payload download for the ~99% of weeks when nothing was filed.

    The clock survives as the fallback for the two cases the filing check cannot
    decide: no stored `latest_filed` to compare against, and a failed probe. In both
    it errs toward fetching once the snapshot is older than FRESH_HOURS.

    A missing shadow file is its OWN reason to fetch, ahead of both. `payload_gzip`
    and `data/parquet/sec_fact/<T>.parquet` are written from the same download, but
    `write_sec_fact_parquet` swallows its exceptions — so a transient write failure
    leaves the DB row complete and the file absent, and the filing check would then
    answer "no XBRL filing since ..." every week until the company next files. For a
    10-K-only filer that is a quarter of a hole in a store nothing else refills.
    """
    row = conn.execute(
        "SELECT sec_status, fetched_at, latest_filed FROM sec_company WHERE ticker = ?",
        (ticker,),
    ).fetchone()
    if not row or row[0] != "ok" or not row[1]:
        return True, "no usable prior snapshot"

    if pq.dual_write_enabled() and not _has_sec_fact_parquet(ticker):
        return True, "parquet missing"

    stored = row[2]
    if stored:
        latest = latest_filed_from_submissions(session, cik10)
        if latest:
            if latest > stored:
                return True, f"new filing {latest} (stored latest_filed={stored})"
            return False, f"no XBRL filing since {stored}"
        # probe failed — fall through to the clock rather than guessing

    if is_fresh(conn, ticker):
        return False, f"clock: snapshot younger than {FRESH_HOURS}h"
    return True, f"clock: snapshot older than {FRESH_HOURS}h"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_sec_fact_parquet(ticker: str, cf: dict, keep: frozenset[str]) -> int:
    """Shadow the projected facts into data/parquet/sec_fact/<TICKER>.parquet. → bytes.

    Same policy as the daily jobs' dual write: SQLite (still `payload_gzip`) remains
    the source of truth for the read side, so a fault here warns and lets the fetch
    stand rather than failing a run over a store nothing reads yet. Unlike the daily
    tables there is no parity check to catch it afterwards — sec_fact shadows a BLOB,
    not a table, so there is nothing to anti-join against.

    Two things catch what this swallows, because a warning in a log nobody reads is
    not a signal: `should_refetch` treats an absent file as its own reason to fetch
    again next run, and `missing_sec_fact_files` fails the run at the end if any
    'ok' ticker still has none. Worst case `jobs/normalize_sec_facts.py` rebuilds the
    whole store from the blobs in ~6 seconds.
    """
    if not pq.dual_write_enabled():
        return 0
    try:
        df = nsf.frame_from_companyfacts(cf, keep)
        return nsf.write_ticker(ticker, df) if not df.empty else 0
    except Exception as e:  # noqa: BLE001 — see docstring
        print(f"[sec] WARNING parquet write for {ticker} failed "
              f"({type(e).__name__}: {e}); rebuild with jobs/normalize_sec_facts.py")
        return 0


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

        keep = sec_concepts.used_concepts(DB_PATH)
        print(f"[sec] parquet dual-write: "
              f"{'on' if pq.dual_write_enabled() else 'OFF'} ({len(keep)} concepts kept)")

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
            cik, cik10, title = cik_map[t]
            if not args.force:
                fetch, why = should_refetch(conn, session, t, cik10)
                if not fetch:
                    n_skip += 1
                    print(f"[sec] {idx}/{len(tickers)} {t}: skip — {why}")
                    time.sleep(RATE_SLEEP)   # the submissions probe was a request too
                    continue
                print(f"[sec] {idx}/{len(tickers)} {t}: fetching — {why}")

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
                nbytes = write_sec_fact_parquet(t, cf, keep)
                print(f"[sec] {idx}/{len(tickers)} {t}: ok  facts={n}  taxonomy={tax_primary}  "
                      f"latest={latest_filed}"
                      + (f"  parquet={nbytes / 1024:.1f}KB" if nbytes else ""))
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

        # Completeness, after the outage threshold above so a wholesale SEC failure
        # reports as the outage rather than as 280 missing files. Every 'ok' row must
        # have its shadow file; `write_sec_fact_parquet` only warns, and there is no
        # parity check downstream to notice (sec_fact shadows a BLOB, not a table).
        missing = missing_sec_fact_files(conn)
        if missing:
            print(f"[sec] INCOMPLETE — {len(missing)} ticker(s) marked ok with no "
                  f"data/parquet/sec_fact file: {missing[:20]}"
                  + (f" … and {len(missing) - 20} more" if len(missing) > 20 else ""))
            print("[sec] rebuild the whole store from the blobs: "
                  "python jobs/normalize_sec_facts.py")
            raise SystemExit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
