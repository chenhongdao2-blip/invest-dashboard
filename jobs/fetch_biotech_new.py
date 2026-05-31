"""Isolated fetch of the NEW biotech tickers only (prices + multiples + profile).

Mirrors the /tmp/fetch_ai.py pattern: reuses jobs/fetch_eod.py helper FUNCTIONS,
runs ONLY for the +154 biotech expansion tickers, with per-ticker try/except and
NO global failure-threshold abort (logs failures, never aborts the batch). This
keeps it from tripping the healthcare-wide thresholds and from refetching the
whole universe.

Backfills prices from 2025-09-01 so YTD / 3M return windows are populated for the
brand-new names.

Run LOCALLY (China network — proxy required for yfinance):
    HTTPS_PROXY=http://127.0.0.1:7897 uv run --python 3.12 \
        --with-requirements requirements.txt python jobs/fetch_biotech_new.py

Writes a JSON coverage report to /tmp/biotech_fetch_report.json.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "jobs"))
import fetch_eod as fe  # noqa: E402

DB = str(REPO_ROOT / "data" / "snapshots.db")
NEW_TSV = "/tmp/new_biotech_pairs.tsv"
REPORT = "/tmp/biotech_fetch_report.json"

PRICE_BACKFILL_START = "2025-09-01"
BATCH = 40

region_to_ccy = {"US": "USD", "HK": "HKD", "JP": "JPY", "KR": "KRW",
                 "CN": "CNY", "EU": "EUR", "UK": "GBP", "CH": "CHF"}


def main() -> None:
    # the NEW tickers only (from the dedup TSV the loader step produced)
    new_tickers = [l.split("\t")[0].strip() for l in open(NEW_TSV) if l.strip()]
    new_set = set(new_tickers)

    conn = sqlite3.connect(DB, timeout=120)
    # Coexist with the concurrent heatmap agent: wait on locks instead of erroring.
    conn.execute("PRAGMA busy_timeout=120000")
    # pull region from universe_member for ccy mapping (all should be US here)
    rows = conn.execute(
        "SELECT DISTINCT ticker, region FROM universe_member "
        "WHERE domain='healthcare' AND sector='biotech'"
    ).fetchall()
    ccy_map = {t: region_to_ccy.get(r, "USD") for t, r in rows if t in new_set}
    # ensure every new ticker has a ccy (default USD)
    for t in new_tickers:
        ccy_map.setdefault(t, "USD")

    print(f"[bio-fetch] NEW biotech tickers to fetch: {len(new_tickers)}")

    # FX (reuse last-good fallback so a transient FX flake doesn't abort)
    prev = fe.last_good_fx(conn)
    try:
        fx = fe.fetch_fx_rates(prev_rates=prev)
    except Exception as e:  # noqa: BLE001
        print(f"[bio-fetch] FX fetch failed ({e}); defaulting USD-only")
        fx = prev or {"USD": 1.0}
    fx.setdefault("USD", 1.0)
    fe.set_meta(conn, "last_fx_rates", json.dumps(fx))

    today = date.today()
    end = (today + timedelta(days=1)).isoformat()
    snapshot_date = today.isoformat()

    # ---------- 1) PRICES (batched, INVARIANT: yf.download via fetch_prices_batch) ----------
    total_price_rows = 0
    price_ok: list[str] = []
    price_fail: list[str] = []
    for i in range(0, len(new_tickers), BATCH):
        batch = new_tickers[i:i + BATCH]
        bnum = i // BATCH + 1
        nb = (len(new_tickers) + BATCH - 1) // BATCH
        print(f"[bio-fetch] prices batch {bnum}/{nb} ({len(batch)})")
        try:
            res = fe.fetch_prices_batch(batch, start=PRICE_BACKFILL_START, end=end)
        except Exception as e:  # noqa: BLE001
            print(f"[bio-fetch] prices batch {bnum} FAILED: {e}")
            res = {}
        for t in batch:
            df = res.get(t)
            if df is None or df.empty:
                price_fail.append(t)
                continue
            try:
                ccy = ccy_map.get(t, "USD")
                rows_p = fe.prices_to_rows(t, df, ccy, fx_to_usd=fx.get(ccy, 1.0))
                total_price_rows += fe.upsert_prices(conn, rows_p)
                price_ok.append(t)
            except Exception as e:  # noqa: BLE001
                print(f"[bio-fetch] price upsert {t} FAILED: {e}")
                price_fail.append(t)
        conn.commit()
        time.sleep(0.6)
    print(f"[bio-fetch] PRICES rows={total_price_rows} ok={len(price_ok)} fail={len(price_fail)}")

    # ---------- 2) MULTIPLES + PROFILE (.info per-ticker, resilient) ----------
    mult_ok: list[str] = []
    mult_fail: list[str] = []
    profile_ok: list[str] = []
    for idx, t in enumerate(new_tickers, 1):
        try:
            info = fe.fetch_info_for(t)
        except Exception as e:  # noqa: BLE001
            print(f"[bio-fetch] info {t} threw {e}")
            info = None
        if not info:
            mult_fail.append(t)
            time.sleep(0.4)
            continue
        try:
            row = fe.info_to_multiple_row(t, info, snapshot_date, fx)
            if row:
                fe.upsert_multiples(conn, [row])
                mult_ok.append(t)
        except Exception as e:  # noqa: BLE001
            print(f"[bio-fetch] multiples {t} FAILED: {e}")
            mult_fail.append(t)
        try:
            fe.upsert_profile(conn, t, info)
            # count as profile_ok only if it actually carried a summary or longName
            if info.get("longBusinessSummary"):
                profile_ok.append(t)
        except Exception as e:  # noqa: BLE001
            print(f"[bio-fetch] profile {t} FAILED: {e}")
        if idx % 20 == 0:
            conn.commit()
            print(f"[bio-fetch] info progress {idx}/{len(new_tickers)} "
                  f"mult_ok={len(mult_ok)} mult_fail={len(mult_fail)}")
        time.sleep(0.4)
    conn.commit()
    print(f"[bio-fetch] MULTIPLES ok={len(mult_ok)} fail={len(mult_fail)} "
          f"PROFILE_with_summary={len(profile_ok)}")
    conn.close()

    report = {
        "new_total": len(new_tickers),
        "price_ok": len(price_ok),
        "price_fail": sorted(price_fail),
        "price_rows": total_price_rows,
        "mult_ok": len(mult_ok),
        "mult_fail": sorted(mult_fail),
        "profile_with_summary": len(profile_ok),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[bio-fetch] DONE. report → {REPORT}")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
