"""Isolated SEC Company Facts fetch for the NEW biotech tickers only.

Reuses jobs/fetch_sec_facts.py helper functions but scopes the loop to just the
+154 biotech expansion tickers (region='US'), with per-ticker try/except and NO
global failure-threshold abort. Avoids re-attempting the entire US universe.

Run LOCALLY (China network — proxy required for SEC):
    SEC_PROXY=http://127.0.0.1:7897 uv run --python 3.12 \
        --with-requirements requirements.txt python jobs/fetch_sec_biotech_new.py

Writes a JSON coverage report to /tmp/biotech_sec_report.json.
"""
from __future__ import annotations

import gzip
import json
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "jobs"))
import fetch_sec_facts as fs  # noqa: E402

DB = str(REPO_ROOT / "data" / "snapshots.db")
NEW_TSV = "/tmp/new_biotech_pairs.tsv"
REPORT = "/tmp/biotech_sec_report.json"


def main() -> None:
    new_tickers = [l.split("\t")[0].strip() for l in open(NEW_TSV) if l.strip()]
    # SEC tickers are dotted-stripped style; all new biotech are plain US symbols.
    session = fs.make_session()
    print(f"[bio-sec] UA set; proxy={'on' if fs.PROXY else 'off'}")
    conn = sqlite3.connect(DB, timeout=120)
    # Coexist with the concurrent heatmap agent: wait on locks instead of erroring.
    conn.execute("PRAGMA busy_timeout=120000")
    try:
        cik_map = fs.load_cik_map(session)
        print(f"[bio-sec] CIK map loaded: {len(cik_map)} tickers")
        print(f"[bio-sec] tickers to fetch: {len(new_tickers)}")

        n_ok = n_nomap = n_fail = 0
        ok_list, nomap_list, fail_list = [], [], []

        for idx, t in enumerate(new_tickers, 1):
            tk = t.upper()
            if tk not in cik_map:
                fs.upsert_company(conn, {
                    "ticker": tk, "cik": None, "cik10": None, "entity_name": None,
                    "taxonomy_primary": None, "sec_status": "not_mapped",
                    "fetched_at": fs._now(), "latest_filed": None, "facts_count": 0,
                    "last_error": "not in SEC company_tickers.json (likely OTC ADR/foreign, no XBRL)",
                    "payload_gzip": None,
                })
                conn.commit()
                n_nomap += 1
                nomap_list.append(tk)
                print(f"[bio-sec] {idx}/{len(new_tickers)} {tk}: not_mapped")
                continue

            cik, cik10, title = cik_map[tk]
            url = fs.SEC_FACTS_URL.format(cik10=cik10)
            try:
                r = fs.http_get(session, url)
                if r.status_code == 404:
                    fs.upsert_company(conn, {
                        "ticker": tk, "cik": cik, "cik10": cik10, "entity_name": title,
                        "taxonomy_primary": None, "sec_status": "no_xbrl",
                        "fetched_at": fs._now(), "latest_filed": None, "facts_count": 0,
                        "last_error": "companyfacts 404 (no XBRL facts filed)",
                        "payload_gzip": None,
                    })
                    conn.commit()
                    n_nomap += 1
                    nomap_list.append(tk)
                    print(f"[bio-sec] {idx}/{len(new_tickers)} {tk}: no_xbrl (404)")
                    time.sleep(fs.RATE_SLEEP)
                    continue
                raw = r.content
                cf = json.loads(raw)
                n, latest_filed, tax = fs.summarize_facts(cf)
                fs.upsert_company(conn, {
                    "ticker": tk, "cik": cik, "cik10": cik10,
                    "entity_name": cf.get("entityName", title),
                    "taxonomy_primary": tax, "sec_status": "ok",
                    "fetched_at": fs._now(), "latest_filed": latest_filed, "facts_count": n,
                    "last_error": None, "payload_gzip": gzip.compress(raw),
                })
                conn.commit()
                n_ok += 1
                ok_list.append(tk)
                print(f"[bio-sec] {idx}/{len(new_tickers)} {tk}: ok facts={n} tax={tax} latest={latest_filed}")
            except Exception as e:  # noqa: BLE001 — persist failure, keep going
                conn.rollback()
                prior = conn.execute(
                    "SELECT sec_status FROM sec_company WHERE ticker = ?", (tk,)
                ).fetchone()
                if prior and prior[0] == "ok":
                    conn.execute(
                        "UPDATE sec_company SET last_error = ? WHERE ticker = ?",
                        (f"refresh failed (kept prior): {str(e)[:300]}", tk),
                    )
                    print(f"[bio-sec] {idx}/{len(new_tickers)} {tk}: refresh FAILED kept prior ({e})")
                else:
                    fs.upsert_company(conn, {
                        "ticker": tk, "cik": cik, "cik10": cik10, "entity_name": title,
                        "taxonomy_primary": None, "sec_status": "failed",
                        "fetched_at": fs._now(), "latest_filed": None, "facts_count": 0,
                        "last_error": str(e)[:500], "payload_gzip": None,
                    })
                    print(f"[bio-sec] {idx}/{len(new_tickers)} {tk}: FAILED {e}")
                conn.commit()
                n_fail += 1
                fail_list.append(tk)
            time.sleep(fs.RATE_SLEEP)

        fs.set_meta(conn, "last_sec_fetch_utc", fs._now())
        conn.commit()
        print(f"[bio-sec] done. ok={n_ok} no_data={n_nomap} fail={n_fail}")
    finally:
        conn.close()

    report = {
        "new_total": len(new_tickers),
        "sec_ok": n_ok,
        "sec_no_data": n_nomap,
        "sec_fail": n_fail,
        "ok_list_count": len(ok_list),
        "no_data_list": sorted(nomap_list),
        "fail_list": sorted(fail_list),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[bio-sec] report → {REPORT}")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
