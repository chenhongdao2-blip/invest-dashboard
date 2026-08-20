"""Pull earnings-call transcripts for covered names — LOCAL ONLY, never cloud.

Reads data/local/earnings_calendar_full.json (the gitignored twin of the
committed calendar — it keeps the `ipid` the download API needs; run
jobs/fetch_earnings_calendar.py locally first to produce it) and for
every matched event flagged speech_draft, downloads the minodata transcript
JSON into data/local/earnings_transcripts/ — a gitignored directory. The
local dashboard renders these on Ticker Drill; the public Cloud app never
sees them (George 2026-08-19: 日历事实可公开、纪要正文永不发布).

Each download costs 1 unit of the 5000-file quota → this job downloads only
files it doesn't already have, and only for calendar-matched events.

KURA→Empire guard (vendor has shipped the wrong company for an ipid before,
data/content/rebalance_ledger.md:55): after download we scan the opening of
the transcript for the company's name token; a miss stores name_check:
"unverified" and the UI shows a caveat instead of silently trusting it.

Run (proxy required on CN networks):
    HTTP_PROXY=http://127.0.0.1:7897 MINODATA_KEY=... python jobs/fetch_earnings_transcripts.py

NEVER wire this into GitHub Actions — the output must not exist in CI where
a stray `git add -A` could publish it.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
# The LOCAL twin, not the committed public artifact: the public one has `ipid`
# stripped (vendor primary key, withheld from the public repo) and ipid is what
# the download API keys on. Produced by jobs/fetch_earnings_calendar.py.
CAL_PATH = REPO_ROOT / "data" / "local" / "earnings_calendar_full.json"
OUT_DIR = REPO_ROOT / "data" / "local" / "earnings_transcripts"

API = "http://event.zais.minodata.com/api/event/file-json"


def _texts(doc: dict) -> str:
    """First ~3000 chars of EN text across both new (presentation/qa) and old
    (describe/qa.content) transcript schemas, for the name check."""
    chunks: list[str] = []
    for sec in ("presentation", "qa"):
        for sp in (doc.get(sec) or []):
            for seg in (sp.get("content") or []):
                chunks.append(seg.get("text") or "")
            if len("".join(chunks)) > 3000:
                break
    if not chunks and isinstance(doc.get("describe"), dict):   # old schema
        for sp in (doc["describe"].get("content") or []):
            chunks.append(sp.get("text") or "")
    return "".join(chunks)[:3000].lower()


def name_check(doc: dict, name_en: str | None, ticker: str) -> str:
    head = _texts(doc)
    if not head:
        return "unverified"
    tokens = []
    if name_en:
        tokens.append(name_en.split()[0][:6].lower())
    tokens.append(ticker.split(".")[0].lower())
    return "pass" if any(t and t in head for t in tokens) else "unverified"


def main() -> int:
    key = os.environ.get("MINODATA_KEY", "")
    if not key:
        print("[error] MINODATA_KEY not set", file=sys.stderr)
        return 2
    if os.environ.get("GITHUB_ACTIONS"):
        print("[error] refusing to run in CI — transcripts are local-only", file=sys.stderr)
        return 2
    try:
        cal = json.loads(CAL_PATH.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"[error] cannot read calendar: {e}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    todo = [e for e in cal.get("events", [])
            if e.get("speech_draft") and e.get("ipid")]
    got = skipped = failed = 0
    for e in todo:
        out = OUT_DIR / f"{e['ticker'].replace('.', '_')}_{e['date_hkt']}_{e['ipid']}.json"
        if out.exists():
            skipped += 1
            continue
        try:
            r = requests.get(API, params={"ipid": e["ipid"]},
                             headers={"Authorization": f"Bearer {key}"}, timeout=90)
            r.raise_for_status()
            doc = r.json()
        except Exception as ex:  # noqa: BLE001
            print(f"[warn] {e['ticker']} ipid={e['ipid']} download failed: "
                  f"{type(ex).__name__}", file=sys.stderr)
            failed += 1
            continue
        wrapper = {
            "ticker": e["ticker"], "name_en": e.get("name_en"),
            "name_cn": e.get("name_cn"), "date_hkt": e["date_hkt"],
            "ipid": e["ipid"],
            "name_check": name_check(doc, e.get("name_en"), e["ticker"]),
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "transcript": doc,
        }
        out.write_text(json.dumps(wrapper, ensure_ascii=False), encoding="utf-8")
        print(f"[got] {e['ticker']} {e['date_hkt']} name_check={wrapper['name_check']}")
        got += 1
        time.sleep(1)
    print(f"[done] downloaded={got} cached={skipped} failed={failed} "
          f"(quota spent this run: {got})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
