"""Fetch the earnings-call calendar for covered names — minodata 海外纪要 API.

Produces data/external/earnings_calendar.json: factual calendar rows ONLY
(ticker / date / time / flags). Transcript content is never written here —
the public repo publishes calendar facts, nothing licensed beyond that.

Methodology guards (agreed 2026-08-19, Codex-reviewed):
- API `time` is US Eastern for ALL venues (empirically calibrated: NVDA/ZM
  17:00 = the public 5pm ET; SMIC 08-13 20:30 ET = 08-14 08:30 HKT). The
  HKT conversion is DST-aware and the HKT date often crosses midnight —
  never treat the API date as an HKT date.
- Matching is a strict (venue, code) double key. Exchange names are matched
  against an exact allow-list (NFC-normalized), never by substring — ASX /
  India numeric codes must not collide with HK codes. v1 supports US + HKEX
  only; every other venue is counted in quarantine, not guessed.
- HK codes compare NUMERICALLY ("01801" ↔ roster "1801.HK"); the roster
  spelling is always what gets published. No global zero strip/pad.
- company_code can be null and preview titles are machine-translated junk —
  display names always come from our own universe roster.
- MINODATA_KEY comes from the environment only. It must never appear in a
  URL, log line, exception message, or the committed artifact.
- A schema-valid response with zero matches is a VALID empty calendar; an
  invalid/incomplete response preserves the previous artifact and exits
  non-zero (so update_manifest is never stamped "ok" for it).

Local runs need the proxy (DNS for the API host is poisoned on CN networks):
    HTTP_PROXY=http://127.0.0.1:7897 MINODATA_KEY=... python jobs/fetch_earnings_calendar.py
GitHub Actions US runners connect directly (no proxy env set).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time as _time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"
OUT_PATH = REPO_ROOT / "data" / "external" / "earnings_calendar.json"
# Local-only twin carrying the vendor's internal record id (`ipid`) and the
# quarantine breakdown. gitignored — jobs/fetch_earnings_transcripts.py reads
# THIS file, because ipid is what the transcript download API keys on.
FULL_PATH = REPO_ROOT / "data" / "local" / "earnings_calendar_full.json"

API_BASE = "http://event.zais.minodata.com/api/event"
ET = ZoneInfo("America/New_York")
HKT = ZoneInfo("Asia/Hong_Kong")

LOOKBACK_HKT_DAYS = 3    # "who just reported" window
LOOKAHEAD_HKT_DAYS = 7   # "who's next" window

# Exact exchange-name allow-lists (NFC-normalized, stripped). Substring
# matching is FORBIDDEN — e.g. "香港" in exc would be sloppy and a future
# "香港创业板" style label must be an explicit decision, not an accident.
US_EXCHANGES = {
    "纽约证券交易所",
    "纽约证券交易所美国板",
    "纳斯达克资本市场",
    "纳斯达克全球市场",
    "纳斯达克全球精选市场",
}
HK_EXCHANGES = {"香港交易所"}

# Vendor→roster US ticker aliases; applied only when the target exists in the
# roster (class shares: vendor uses dots, yfinance uses dashes).
US_ALIASES = {"BRK.B": "BRK-B", "BRK.A": "BRK-A", "BF.B": "BF-B"}


def _norm(s: str | None) -> str:
    return unicodedata.normalize("NFC", (s or "")).strip()


def load_roster() -> dict:
    """Universe roster keyed for strict (venue, code) matching.

    Returns {"us": {code: row}, "hk": {int_code: row}} where row =
    {ticker, name_cn, name_en, region}. Roster spelling is canonical.
    """
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = con.execute(
        "SELECT ticker, MAX(name_cn), MAX(name_en), MAX(region) "
        "FROM universe_member GROUP BY ticker")
    us: dict[str, dict] = {}
    hk: dict[int, dict] = {}
    for ticker, name_cn, name_en, region in cur.fetchall():
        row = {"ticker": ticker, "name_cn": name_cn, "name_en": name_en,
               "region": region}
        if ticker.endswith(".HK"):
            stem = ticker[:-3]
            if stem.isdigit():
                hk[int(stem)] = row
        elif "." not in ticker:                      # US bare (GILD, BRK-B)
            us[ticker.upper()] = row
        # .T / .SS / .SZ / .KS etc. → unsupported venues in v1 (quarantined
        # on the API side by the exchange allow-list, so nothing to do here)
    con.close()
    return {"us": us, "hk": hk}


def match_event(code: str | None, exc: str | None, roster: dict) -> tuple[str, dict | None]:
    """Strict (venue, code) match. Returns (outcome, roster_row|None).

    outcome ∈ matched | unsupported_venue | malformed_code | out_of_universe
    """
    exc_n = _norm(exc)
    code_n = _norm(code)
    if exc_n in US_EXCHANGES:
        if not code_n:
            return "malformed_code", None
        c = US_ALIASES.get(code_n.upper(), code_n.upper())
        if c in roster["us"]:
            return "matched", roster["us"][c]
        return "out_of_universe", None
    if exc_n in HK_EXCHANGES:
        if not code_n.isdigit():
            return "malformed_code", None
        row = roster["hk"].get(int(code_n))
        return ("matched", row) if row else ("out_of_universe", None)
    return "unsupported_venue", None


def name_sanity_ok(api_company: str | None, row: dict) -> bool:
    """Crude guard against vendor code/name mix-ups (KURA→Empire precedent):
    the first token of our roster English name should appear in the vendor's
    company string. Missing names on either side → pass (no evidence)."""
    api = _norm(api_company).lower()
    ours = _norm(row.get("name_en")).lower()
    if not api or not ours:
        return True
    return ours.split()[0][:6] in api


def et_to_hkt(date_str: str, time_str: str | None) -> tuple[str, str | None]:
    """API (date, time) in US Eastern → (date_hkt, time_hkt). Missing time →
    date passes through unshifted (we can't know the HKT date without it)."""
    if not time_str:
        return date_str, None
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    hk = dt.replace(tzinfo=ET).astimezone(HKT)
    return hk.strftime("%Y-%m-%d"), hk.strftime("%H:%M")


def fetch_list(key: str, sdate: str, edate: str) -> list[dict]:
    """Fetch the full event list (with previews) for an ET date range.
    Paginates; raises on HTTP error or short pagination (incomplete data
    must never silently become an 'empty calendar')."""
    rows: list[dict] = []
    page, total = 1, None
    while True:
        r = requests.post(
            f"{API_BASE}/list",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"date": {"sdate": sdate, "edate": edate},
                  "page": page, "page_size": 10000, "with_preview": True},
            timeout=60)
        r.raise_for_status()
        d = r.json()
        if d.get("code") != 200:
            raise RuntimeError(f"API returned code={d.get('code')}")
        total = int(d.get("total", 0))
        batch = d.get("data") or []
        rows.extend(batch)
        if len(rows) >= total or not batch:
            break
        page += 1
        _time.sleep(1)
    if total is not None and len(rows) < total:
        raise RuntimeError(f"incomplete pagination: got {len(rows)} of {total}")
    print(f"[fetch] {sdate}..{edate} (ET) → {len(rows)} events")
    return rows


def build(rows: list[dict], roster: dict, today_hkt: str) -> dict:
    lo = (datetime.strptime(today_hkt, "%Y-%m-%d")
          - timedelta(days=LOOKBACK_HKT_DAYS)).strftime("%Y-%m-%d")
    hi = (datetime.strptime(today_hkt, "%Y-%m-%d")
          + timedelta(days=LOOKAHEAD_HKT_DAYS)).strftime("%Y-%m-%d")
    q = {"unsupported_venue": 0, "malformed_code": 0, "out_of_universe": 0,
         "name_mismatch": 0, "out_of_window": 0}
    events: list[dict] = []
    seen: set[tuple] = set()
    for r in rows:
        outcome, row = match_event(r.get("company_code"), r.get("exc"), roster)
        if outcome != "matched":
            q[outcome] += 1
            continue
        if not name_sanity_ok(r.get("company"), row):
            q["name_mismatch"] += 1
            continue
        date_hkt, time_hkt = et_to_hkt(r.get("date"), r.get("time"))
        if not (lo <= date_hkt <= hi):
            q["out_of_window"] += 1
            continue
        k = (row["ticker"], date_hkt)
        if k in seen:                      # same call listed twice → keep first
            continue
        seen.add(k)
        events.append({
            "ticker": row["ticker"],
            "name_cn": row["name_cn"],
            "name_en": row["name_en"],
            "region": row["region"],
            "date_hkt": date_hkt,
            "time_hkt": time_hkt,
            "date_et": r.get("date"),
            "time_et": (r.get("time") or "")[:5] or None,
            "upcoming": date_hkt >= today_hkt,
            "speech_draft": bool(r.get("speech_draft")),
            "ipid": r.get("ipid"),
        })
    # Vendor lists the same call twice near the event: the actual row plus a
    # stale preview row with a placeholder time, dated 1-3 days later. Keep
    # the EARLIEST row per ticker and drop same-ticker rows within 3 days
    # after it. Two real earnings calls 3 days apart don't happen, so nothing
    # genuine is lost. (The previous guard only tested `upcoming` rows, so a
    # ghost that had already aged into the past survived — observed 2026-08-20:
    # FN actual 08-18 + ghost 08-19, both upcoming=false, both shipped.)
    events.sort(key=lambda e: (e["date_hkt"], e["time_hkt"] or "99:99"))
    kept: list[dict] = []
    anchor: dict[str, str] = {}          # ticker → date_hkt of the row we kept
    dropped = 0
    for e in events:
        a = anchor.get(e["ticker"])
        if a is not None:
            gap = (datetime.strptime(e["date_hkt"], "%Y-%m-%d")
                   - datetime.strptime(a, "%Y-%m-%d")).days
            if 0 <= gap <= 3:
                dropped += 1
                continue
        anchor[e["ticker"]] = e["date_hkt"]
        kept.append(e)
    if dropped:
        q["preview_shadow"] = dropped
    events = kept
    return {
        "schema_version": 1,
        "retrieved_at_utc": datetime.now(ZoneInfo("UTC")).isoformat(timespec="seconds"),
        "as_of_hkt": today_hkt,
        "source_timezone": "America/New_York",
        "window_hkt": {"from": lo, "to": hi},
        "n_events": len(events),
        "quarantine_counts": q,
        "source": "minodata 海外纪要 API (calendar facts only)",
        "events": events,
    }


# Event keys withheld from the PUBLIC artifact. `ipid` is minodata's internal
# record id: the dashboard never reads it, and a public repo shouldn't carry a
# paid vendor's primary keys. It stays in the local twin for the transcript job.
_PUBLIC_DROP_EVENT_KEYS = ("ipid",)


def to_public(payload: dict) -> dict:
    """Calendar facts only — the artifact that lands in the PUBLIC repo.

    Drops `ipid` per event and the top-level `quarantine_counts` (whose
    unsupported_venue/out_of_universe tallies disclose the vendor's coverage
    scale). Everything the UI renders survives untouched."""
    pub = {k: v for k, v in payload.items() if k != "quarantine_counts"}
    pub["events"] = [{k: v for k, v in e.items()
                      if k not in _PUBLIC_DROP_EVENT_KEYS}
                     for e in payload["events"]]
    return pub


def validate(payload: dict) -> None:
    assert payload["schema_version"] == 1
    assert payload["as_of_hkt"]
    for e in payload["events"]:
        assert e["ticker"] and e["date_hkt"]
        assert e["time_hkt"] is None or len(e["time_hkt"]) == 5


# ── selftest fixtures (no network) ───────────────────────────────────────────
def selftest() -> int:
    roster = {
        "us": {"GILD": {"ticker": "GILD", "name_en": "Gilead Sciences",
                        "name_cn": "吉利德", "region": "US"},
               "BRK-B": {"ticker": "BRK-B", "name_en": "Berkshire Hathaway",
                         "name_cn": None, "region": "US"}},
        "hk": {1801: {"ticker": "1801.HK", "name_en": "Innovent Biologics",
                      "name_cn": "信达生物", "region": "HK"}},
    }
    checks = [
        # US exact
        (match_event("GILD", "纳斯达克全球精选市场", roster)[0], "matched"),
        # HK numeric compare 01801 ↔ 1801.HK
        (match_event("01801", "香港交易所", roster)[0], "matched"),
        (match_event("01801", "香港交易所", roster)[1]["ticker"], "1801.HK"),
        # supported venue, not covered
        (match_event("01810", "香港交易所", roster)[0], "out_of_universe"),
        # A-share venue quarantined in v1
        (match_event("603259", "上海证券交易所", roster)[0], "unsupported_venue"),
        # ASX numeric code must NOT collide with HK codes
        (match_event("1801", "澳大利亚证券交易所", roster)[0], "unsupported_venue"),
        # class-share alias only via explicit map
        (match_event("BRK.B", "纽约证券交易所", roster)[0], "matched"),
        # null code on a supported venue
        (match_event(None, "纽约证券交易所", roster)[0], "malformed_code"),
        # summer: 08-13 20:30 ET = 08-14 08:30 HKT (the SMIC morning-call case)
        (et_to_hkt("2026-08-13", "20:30:00"), ("2026-08-14", "08:30")),
        # winter (EST, +13h): 01-15 17:00 ET = 01-16 06:00 HKT
        (et_to_hkt("2026-01-15", "17:00:00"), ("2026-01-16", "06:00")),
        # missing time → date passes through, no fake shift
        (et_to_hkt("2026-08-13", None), ("2026-08-13", None)),
        # name sanity: vendor mix-up (KURA→Empire style) is caught
        (name_sanity_ok("Empire State Realty",
                        {"name_en": "Kura Oncology"}), False),
        (name_sanity_ok("Innovent Biologics, Inc.",
                        {"name_en": "Innovent Biologics"}), True),
    ]
    bad = [(i, got, want) for i, (got, want) in enumerate(checks) if got != want]
    for i, got, want in bad:
        print(f"[selftest] FAIL #{i}: got {got!r}, want {want!r}")
    print(f"[selftest] {len(checks) - len(bad)}/{len(checks)} passed")
    return 1 if bad else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    key = os.environ.get("MINODATA_KEY", "")
    if not key:
        print("[error] MINODATA_KEY not set — refusing to run", file=sys.stderr)
        return 2
    today_hkt = datetime.now(HKT).strftime("%Y-%m-%d")
    # ET query range: pad 1 day both sides so HKT-window rows near midnight
    # (ET date ≠ HKT date) are never missed.
    sdate = (datetime.now(HKT) - timedelta(days=LOOKBACK_HKT_DAYS + 1)).strftime("%Y-%m-%d")
    edate = (datetime.now(HKT) + timedelta(days=LOOKAHEAD_HKT_DAYS + 1)).strftime("%Y-%m-%d")
    try:
        rows = fetch_list(key, sdate, edate)
    except Exception as e:  # noqa: BLE001 — fail loud, keep previous artifact
        # str(e) on requests errors contains the URL, never the auth header.
        print(f"[error] fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    payload = build(rows, load_roster(), today_hkt)
    try:
        validate(payload)
    except AssertionError as e:
        print(f"[error] payload validation failed: {e}", file=sys.stderr)
        return 1
    def _atomic_write(path: Path, obj: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        tmp.replace(path)                       # atomic: old file survives failure

    _atomic_write(FULL_PATH, payload)           # gitignored twin (keeps ipid)
    _atomic_write(OUT_PATH, to_public(payload))  # committed, calendar facts only
    # CI logs are public on a public repo → print our own counts only, never
    # the vendor's coverage tallies.
    q = payload["quarantine_counts"]
    print(f"[done] {payload['n_events']} events → {OUT_PATH} "
          f"(+ local twin → {FULL_PATH}); "
          f"dropped {q.get('preview_shadow', 0)} duplicate preview row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
