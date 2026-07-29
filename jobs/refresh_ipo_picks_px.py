"""Refresh the 至今 (since-listing) return column on the HK IPO 打新 record.

Writes two columns back into data/external/ipo_picks.csv:
    cum_ret   — total return vs the OFFER price, from listing day to px_asof
    px_asof   — trade date of the price used

Why the return is chained instead of last_close/offer-1
-------------------------------------------------------
yfinance back-adjusts HK history for splits/bonus issues, and `auto_adjust=False`
does NOT turn that off (it only controls dividends). 3296 华勤技术 is the live
example: its real listing-day close was HK$88.00 (+13.26% on a 77.70 offer) but
yfinance serves that bar as 62.86 — exactly 88.00/1.4. Dividing today's raw price
by the nominal offer would silently mis-state every split-affected name.

So we chain the already-verified day-1 return with the price ratio taken from a
SINGLE yfinance series, where any adjustment factor cancels out:

    cum_ret = (1 + day1_ret) * (last_close / day1_close) - 1

That also means the column only needs day1_ret — not offer_price — so it covers
every listed row, including the early ones whose offer was never recorded.

Usage (idempotent; backs the CSV up first):
    HTTPS_PROXY=http://127.0.0.1:7897 uv run --with yfinance --with pandas \
        python jobs/refresh_ipo_picks_px.py
"""
from __future__ import annotations

import csv
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV = REPO_ROOT / "data" / "external" / "ipo_picks.csv"

REQUEST_GAP_S = 1.2      # yfinance rate-limit courtesy (see skills INVARIANTS)
SPLIT_WARN_TOL = 0.02    # |yf d1 close - recorded d1 close| beyond this ⇒ adjusted


def backup(p: Path) -> Path:
    bak = p.with_name(p.name + f".bak-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(p, bak)
    return bak


def fetch(ticker: str, start: str) -> tuple[float, float, str] | None:
    """Return (day1_close, last_close, last_date) from one yfinance series."""
    df = yf.download(ticker, start=start, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df.index = pd.to_datetime(df.index).date
    df = df[df["Close"].notna()]
    if df.empty:
        return None
    first, last = df.index.min(), df.index.max()
    return float(df.loc[first, "Close"]), float(df.loc[last, "Close"]), str(last)


def main() -> int:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    fields = list(rows[0].keys())
    for col in ("cum_ret", "px_asof"):
        if col not in fields:
            fields.append(col)

    ok = skipped = failed = 0
    notes: list[str] = []
    print(f"{'code':<6}{'name':<14}{'d1_ret':>9}{'cum_ret':>10}{'asof':>13}  note")

    for r in rows:
        r.setdefault("cum_ret", "")
        r.setdefault("px_asof", "")
        if r.get("status", "").strip().lower() != "listed":
            continue
        try:
            d1_ret = float(r["day1_ret"])
        except (TypeError, ValueError):
            skipped += 1
            notes.append(f"{r['code']} {r['name_cn']}: no day1_ret → 至今 left blank")
            continue

        ticker = f"{int(r['code']):04d}.HK"
        try:
            got = fetch(ticker, r["list_date"])
        except Exception as exc:                      # network/API — record, keep going
            got = None
            notes.append(f"{r['code']} {r['name_cn']}: fetch error {exc!r:.70}")
        time.sleep(REQUEST_GAP_S)

        if got is None:
            failed += 1
            notes.append(f"{r['code']} {r['name_cn']}: no yfinance data for {ticker}")
            print(f"{r['code']:<6}{r['name_cn']:<14}{d1_ret:>9.4f}{'—':>10}{'—':>13}  NO DATA")
            continue

        d1_close, last_close, last_date = got
        cum = (1.0 + d1_ret) * (last_close / d1_close) - 1.0

        note = ""
        try:                                          # split/adjustment tripwire
            rec_d1 = float(r["day1_close"])
            if abs(d1_close - rec_d1) / rec_d1 > SPLIT_WARN_TOL:
                note = f"adj×{rec_d1 / d1_close:.3f} (yf back-adjusted; ratio-chain absorbs it)"
                notes.append(f"{r['code']} {r['name_cn']}: {note}")
        except (TypeError, ValueError, ZeroDivisionError):
            pass

        r["cum_ret"] = f"{cum:.4f}"
        r["px_asof"] = last_date
        ok += 1
        print(f"{r['code']:<6}{r['name_cn']:<14}{d1_ret:>9.4f}{cum:>10.4f}{last_date:>13}  {note}")

    bak = backup(CSV)
    with CSV.open("w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {ok} · skipped {skipped} · failed {failed}   backup → {bak.name}")
    if notes:
        print("\nnotes:")
        for n in notes:
            print("  -", n)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
