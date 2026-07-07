"""Fetch 13F-HR holdings for ~12 large US healthcare-dedicated funds.

Feeds the Healthcare page "US HC funds 13F" section — the US-institutional
counterpart of the China-fund OW/UW positioning block. 13F is PUBLIC data
(SEC EDGAR, HIGH reliability): real fund names, no anonymisation needed.

Per fund: latest 2 quarters of 13F-HR (13F-HR/A amendment supersedes the
original for the same period) → holdings (SH only, put/call excluded) →
QoQ moves (NEW / EXITED / ADD / TRIM). Cross-fund aggregate: consensus
holdings (held-by-N-funds), hottest new buys, common exits.

Caveats (baked into the page caption, keep honest):
    - 13F covers US-listed LONG positions only (incl. ADRs); no shorts,
      no non-US lines, no swaps detail.
    - Filed up to 45 days after quarter end — this is POSITIONING as of the
      report date, not today.
    - `value` is USD (post-2023 rule; older filings were $000 — we only
      ever read the last 2 quarters so the USD rule holds).

Network (mirrors fetch_sec_facts.py):
    - User-Agent is MANDATORY (SEC 403s a missing/default UA). Override via SEC_UA.
    - Proxy OPTIONAL: SEC_PROXY=http://127.0.0.1:7897 from mainland China;
      unset on GitHub Actions.

Usage:
    SEC_PROXY=http://127.0.0.1:7897 python jobs/fetch_13f_hc_funds.py
    python jobs/fetch_13f_hc_funds.py --fund "Baker Bros"   # single fund (debug)
    python jobs/fetch_13f_hc_funds.py --prices-only         # refresh price series only

Price series: closes for the aggregate names (consensus + new buys + exits) are
baked INTO the JSON via yfinance — most 13F names sit outside universe_member,
so prices_daily can't serve them and Cloud can't fetch live. --prices-only is
the cheap daily pass (no SEC hit); the full run refreshes filings + prices.

Failure discipline: per-fund try/except; a failing fund keeps its previous
snapshot from the existing JSON (marked stale) — never blocks the others,
never retries forever.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "external" / "us_hc_funds_13f.json"

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json"
FILING_FILE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{name}"

UA = os.environ.get("SEC_UA", "invest-dashboard research (contact: research@invest-dashboard.local)")
PROXY = os.environ.get("SEC_PROXY")  # e.g. http://127.0.0.1:7897 (local CN); unset on Actions
if PROXY:  # yfinance reads the standard env proxies (requests-level), SEC uses session proxies
    os.environ.setdefault("HTTP_PROXY", PROXY)
    os.environ.setdefault("HTTPS_PROXY", PROXY)

PRICE_DAYS = 130   # ~6 months of trading days kept per ticker (spark + since-quarter-end)

RATE_SLEEP = 0.4
MAX_RETRY = 4
BACKOFF_BASE = 1.6
TIMEOUT = (10, 60)

TOP_N = 15            # holdings kept per fund in the JSON (aggregate uses ALL rows in-memory)
CHG_THRESHOLD = 0.03  # |shares QoQ| below this = UNCH (avoids rounding noise)

# CIKs verified against EDGAR company search 2026-07-06 (each has a live
# 13F-HR trail; OrbiMed's ACTIVE filer is Advisors LLC, not the dormant
# Advisers Inc/Capital LLC shells).
FUNDS: list[dict] = [
    {"name": "Baker Bros Advisors",       "cik": 1263508},
    {"name": "OrbiMed Advisors",          "cik": 1055951},
    {"name": "Perceptive Advisors",       "cik": 1224962},
    {"name": "RA Capital Management",     "cik": 1346824},
    {"name": "Avoro Capital Advisors",    "cik": 1633313},
    {"name": "RTW Investments",           "cik": 1493215},
    {"name": "Deep Track Capital",        "cik": 1856083},
    {"name": "EcoR1 Capital",             "cik": 1587114},
    {"name": "Redmile Group",             "cik": 1425738},
    {"name": "Logos Global Management",   "cik": 1792126},
    {"name": "Cormorant Asset Management","cik": 1583977},
    {"name": "Rock Springs Capital",      "cik": 1595725},
]


# ----- http (same conventions as fetch_sec_facts.py) -----
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    if PROXY:
        s.proxies.update({"http": PROXY, "https": PROXY})
    return s


def http_get(session: requests.Session, url: str) -> requests.Response:
    last = "unknown error"
    for attempt in range(MAX_RETRY):
        try:
            r = session.get(url, timeout=TIMEOUT)
            if r.status_code in (200, 404):
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r
        except requests.RequestException as e:
            last = str(e)
        time.sleep(BACKOFF_BASE ** attempt + 0.3)
    raise RuntimeError(f"GET failed after {MAX_RETRY} tries: {last} — {url}")


# ----- issuer-name → ticker (display only; CUSIP stays the join key) -----
_SUFFIX_RE = re.compile(
    r"\b(INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|PLC|LTD|LIMITED|LP|SA|NV|AG|SE|"
    r"HLDGS?|HOLDINGS?|GROUP|GRP|ADR|ADS|SPONSORED|COM|NEW|CL\s+[A-C]|CLASS\s+[A-C]|SHS|-)\b"
)


def _norm_name(name: str) -> str:
    s = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    s = _SUFFIX_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_name_ticker_map(session: requests.Session) -> dict[str, str]:
    """Normalized SEC company title → ticker. First occurrence wins (SEC lists
    primary listings first), so share-class dupes don't clobber the main line."""
    r = http_get(session, SEC_TICKERS_URL)
    m: dict[str, str] = {}
    for v in r.json().values():
        key = _norm_name(v.get("title", ""))
        if key and key not in m:
            m[key] = str(v["ticker"]).upper()
    return m


def guess_ticker(issuer: str, name_map: dict[str, str]) -> str:
    """Best-effort issuer→ticker. Unmapped = '' (page shows issuer name; never fabricate)."""
    key = _norm_name(issuer)
    if key in name_map:
        return name_map[key]
    # progressive right-trim: "IDEAYA BIOSCIENCES" missing → try shorter prefixes
    words = key.split()
    for i in range(len(words) - 1, 0, -1):
        k = " ".join(words[:i])
        if len(k) >= 4 and k in name_map:
            return name_map[k]
    return ""


# ----- filings -----
def latest_two_periods(session: requests.Session, cik: int) -> list[dict]:
    """Return [{period, accession, filed, form}] for the 2 most recent distinct
    periodOfReport, 13F-HR/A superseding 13F-HR for the same period."""
    r = http_get(session, SUBMISSIONS_URL.format(cik10=str(cik).zfill(10)))
    if r.status_code == 404:
        raise RuntimeError(f"CIK {cik}: submissions 404")
    recent = r.json().get("filings", {}).get("recent", {})
    best: dict[str, dict] = {}  # period → filing (latest filed wins; /A files later than original)
    for form, acc, filed, period in zip(
        recent.get("form", []), recent.get("accessionNumber", []),
        recent.get("filingDate", []), recent.get("reportDate", []),
    ):
        if form not in ("13F-HR", "13F-HR/A") or not period:
            continue
        cur = best.get(period)
        if cur is None or filed >= cur["filed"]:
            best[period] = {"period": period, "accession": acc, "filed": filed, "form": form}
    return [best[p] for p in sorted(best, reverse=True)[:2]]


def fetch_infotable(session: requests.Session, cik: int, accession: str) -> list[dict]:
    """Download + parse the infotable XML of one 13F filing → holding rows
    aggregated by CUSIP (a fund may report multiple rows per CUSIP across
    discretion buckets). SH only; put/call rows excluded."""
    acc = accession.replace("-", "")
    idx = http_get(session, FILING_INDEX_URL.format(cik=cik, acc=acc)).json()
    xml_names = [
        it["name"] for it in idx.get("directory", {}).get("item", [])
        if it["name"].lower().endswith(".xml") and "primary_doc" not in it["name"].lower()
    ]
    if not xml_names:
        raise RuntimeError(f"no infotable xml in {accession}")
    time.sleep(RATE_SLEEP)
    xml = http_get(session, FILING_FILE_URL.format(cik=cik, acc=acc, name=xml_names[0])).content

    root = ET.fromstring(xml)
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    by_cusip: dict[str, dict] = {}
    for it in root.iter(f"{ns}infoTable"):
        def g(tag: str, node=it) -> str:
            el = node.find(f"{ns}{tag}")
            return (el.text or "").strip() if el is not None and el.text else ""

        if g("putCall"):
            continue  # options row — not a share position
        shrs = it.find(f"{ns}shrsOrPrnAmt")
        stype = g("sshPrnamtType", shrs) if shrs is not None else ""
        if stype and stype != "SH":
            continue  # principal-amount (debt) rows out of scope
        cusip = g("cusip").upper()
        if not cusip:
            continue
        row = by_cusip.setdefault(
            cusip, {"issuer": g("nameOfIssuer"), "cusip": cusip, "value": 0.0, "shares": 0.0}
        )
        try:
            row["value"] += float(g("value") or 0)
            row["shares"] += float(g("sshPrnamt", shrs) or 0) if shrs is not None else 0.0
        except ValueError:
            continue
    return list(by_cusip.values())


# ----- QoQ + aggregate -----
def qoq_tag(latest: dict[str, dict], prior: dict[str, dict], cusip: str) -> tuple[str, float | None]:
    """(tag, shares_chg_pct) — NEW / ADD / TRIM / UNCH; EXITED handled separately."""
    if cusip not in prior:
        return "NEW", None
    s0, s1 = prior[cusip]["shares"], latest[cusip]["shares"]
    if s0 <= 0:
        return "UNCH", None
    chg = (s1 - s0) / s0
    if chg > CHG_THRESHOLD:
        return "ADD", chg
    if chg < -CHG_THRESHOLD:
        return "TRIM", chg
    return "UNCH", chg


def build_fund_entry(name: str, cik: int, filings: list[dict],
                     holdings: list[list[dict]], name_map: dict[str, str]) -> tuple[dict, dict]:
    """→ (json entry for one fund, full latest-holdings dict for the aggregate)."""
    latest = {h["cusip"]: h for h in holdings[0]}
    prior = {h["cusip"]: h for h in holdings[1]} if len(holdings) > 1 else {}
    total = sum(h["value"] for h in latest.values()) or 1.0

    rows = []
    for h in sorted(latest.values(), key=lambda x: -x["value"]):
        tag, chg = qoq_tag(latest, prior, h["cusip"])
        rows.append({
            "issuer": h["issuer"], "ticker": guess_ticker(h["issuer"], name_map),
            "cusip": h["cusip"], "value": round(h["value"]), "shares": round(h["shares"]),
            "weight": round(h["value"] / total, 4), "qoq": tag,
            "shares_chg_pct": round(chg, 4) if chg is not None else None,
        })
    exited = [
        {"issuer": h["issuer"], "ticker": guess_ticker(h["issuer"], name_map),
         "cusip": c, "prior_value": round(h["value"])}
        for c, h in sorted(prior.items(), key=lambda kv: -kv[1]["value"]) if c not in latest
    ]
    entry = {
        "name": name, "cik": str(cik).zfill(10), "status": "ok",
        "period": filings[0]["period"], "filed": filings[0]["filed"], "form": filings[0]["form"],
        "prior_period": filings[1]["period"] if len(filings) > 1 else None,
        "total_value": round(total), "n_positions": len(latest),
        "top_holdings": rows[:TOP_N],
        "new_buys": [r for r in rows if r["qoq"] == "NEW"][:10],
        "exited": exited[:10],
    }
    # full rows (with tags) for the cross-fund aggregate — NOT persisted per fund
    full = {r["cusip"]: r for r in rows}
    return entry, full


def build_aggregate(per_fund_full: dict[str, dict[str, dict]],
                    exits_by_fund: dict[str, list[dict]]) -> dict:
    cons: dict[str, dict] = {}
    for fund, holdings in per_fund_full.items():
        for c, r in holdings.items():
            a = cons.setdefault(c, {
                "issuer": r["issuer"], "ticker": r["ticker"], "cusip": c,
                "n_funds": 0, "total_value": 0, "funds": [],
                "n_new": 0, "n_add": 0, "n_trim": 0,
                "by_fund": {},   # fund → {value, qoq} — powers the holder×company matrix
            })
            a["n_funds"] += 1
            a["total_value"] += r["value"]
            a["funds"].append(fund)
            a["by_fund"][fund] = {"value": r["value"], "qoq": r["qoq"]}
            if r["qoq"] == "NEW":
                a["n_new"] += 1
            elif r["qoq"] == "ADD":
                a["n_add"] += 1
            elif r["qoq"] == "TRIM":
                a["n_trim"] += 1

    exit_counts: dict[str, dict] = {}
    for fund, exits in exits_by_fund.items():
        for e in exits:
            x = exit_counts.setdefault(e["cusip"], {
                "issuer": e["issuer"], "ticker": e["ticker"], "cusip": e["cusip"],
                "n_exits": 0, "funds": []})
            x["n_exits"] += 1
            x["funds"].append(fund)

    consensus = sorted(cons.values(), key=lambda a: (-a["n_funds"], -a["total_value"]))
    return {
        "consensus": consensus[:30],
        "top_new_buys": sorted([a for a in cons.values() if a["n_new"] > 0],
                               key=lambda a: (-a["n_new"], -a["total_value"]))[:15],
        "top_exits": sorted(exit_counts.values(), key=lambda x: -x["n_exits"])[:15],
    }


# ----- price series for the aggregate names (spark + since-quarter-end move) -----
def aggregate_tickers(out: dict) -> list[str]:
    """Every mapped ticker the page's aggregate blocks can show (consensus +
    new buys + exits). Unmapped issuers have no ticker → no price line (page
    shows an em-dash, never fabricates)."""
    agg = out.get("aggregate") or {}
    tks = {r.get("ticker") for k in ("consensus", "top_new_buys", "top_exits") for r in agg.get(k) or []}
    return sorted(t for t in tks if t)


def fetch_prices(tickers: list[str]) -> dict:
    """yfinance closes → {ticker: {"dates": [...], "closes": [...]}}.

    INVARIANTS (skills/CLAUDE.md protected patterns): yf.download() not
    Ticker().history(); sleep between requests; droplevel for MultiIndex.
    Batch download keeps it to a handful of requests for ~50 names.
    """
    import pandas as pd
    import yfinance as yf

    prices: dict[str, dict] = {}
    CHUNK = 25
    for i in range(0, len(tickers), CHUNK):
        batch = tickers[i:i + CHUNK]
        try:
            df = yf.download(batch, period="7mo", interval="1d",
                             auto_adjust=True, progress=False, threads=False)
        except Exception as e:  # noqa: BLE001 — price layer is best-effort garnish
            print(f"[13f] price batch failed ({batch[0]}..): {e}")
            time.sleep(2)
            continue
        closes = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]].rename(
            columns={"Close": batch[0]})
        for tk in batch:
            if tk not in closes.columns:
                continue
            s = closes[tk].dropna().tail(PRICE_DAYS)
            if len(s) < 2:
                continue
            prices[tk] = {
                "dates": [d.strftime("%Y-%m-%d") for d in s.index],
                "closes": [round(float(v), 4) for v in s.values],
            }
        time.sleep(2)  # protected pattern: rate-limit between yfinance requests
    return prices


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--fund", type=str, default="", help="Only funds whose name contains this (debug).")
    p.add_argument("--prices-only", action="store_true",
                   help="Skip SEC; refresh the baked price series on the existing JSON.")
    p.add_argument("--no-prices", action="store_true", help="Skip the yfinance price pass (debug).")
    args = p.parse_args()

    if args.prices_only:
        if not OUT_PATH.exists():
            raise SystemExit("no existing JSON — run the full job first")
        out = json.loads(OUT_PATH.read_text())
        prices = fetch_prices(aggregate_tickers(out))
        out["prices"] = prices
        out["prices_as_of"] = max((v["dates"][-1] for v in prices.values()), default=None)
        OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1))
        print(f"[13f] prices refreshed: {len(prices)} tickers, as_of {out['prices_as_of']}")
        return

    funds = [f for f in FUNDS if args.fund.lower() in f["name"].lower()] if args.fund else FUNDS
    session = make_session()
    name_map = load_name_ticker_map(session)
    print(f"[13f] ticker map: {len(name_map)} names")

    # previous output = per-fund fallback when a fetch fails today
    prev_by_name: dict[str, dict] = {}
    if OUT_PATH.exists():
        try:
            prev_by_name = {f["name"]: f for f in json.loads(OUT_PATH.read_text())["funds"]}
        except Exception:
            pass

    entries: list[dict] = []
    per_fund_full: dict[str, dict[str, dict]] = {}
    exits_by_fund: dict[str, list[dict]] = {}
    failures: list[str] = []

    for f in funds:
        name, cik = f["name"], f["cik"]
        try:
            filings = latest_two_periods(session, cik)
            if not filings:
                raise RuntimeError("no 13F-HR filings found")
            time.sleep(RATE_SLEEP)
            holdings = []
            for fl in filings:
                holdings.append(fetch_infotable(session, cik, fl["accession"]))
                time.sleep(RATE_SLEEP)
            entry, full = build_fund_entry(name, cik, filings, holdings, name_map)
            entries.append(entry)
            per_fund_full[name] = full
            exits_by_fund[name] = entry["exited"]
            print(f"[13f] ok    {name}: {entry['n_positions']} pos, "
                  f"${entry['total_value']/1e9:.1f}bn @ {entry['period']}")
        except Exception as e:  # noqa: BLE001 — per-fund isolation is the point
            failures.append(name)
            stale = prev_by_name.get(name)
            if stale:
                stale = {**stale, "status": "stale"}
                entries.append(stale)
                print(f"[13f] STALE {name}: {e} (kept previous snapshot)")
            else:
                entries.append({"name": name, "cik": str(cik).zfill(10), "status": "failed"})
                print(f"[13f] FAIL  {name}: {e}")

    ok = [e for e in entries if e.get("status") == "ok"]
    periods = sorted({e["period"] for e in ok}, reverse=True)
    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "domain": "healthcare",
        "source": "SEC EDGAR 13F-HR",
        "latest_period": periods[0] if periods else None,
        "funds": entries,
        "aggregate": build_aggregate(per_fund_full, exits_by_fund),
    }
    if not args.no_prices:
        prices = fetch_prices(aggregate_tickers(out))
        out["prices"] = prices
        out["prices_as_of"] = max((v["dates"][-1] for v in prices.values()), default=None)
        print(f"[13f] prices: {len(prices)} tickers, as_of {out.get('prices_as_of')}")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"[13f] wrote {OUT_PATH} — {len(ok)}/{len(funds)} funds ok, period {out['latest_period']}")
    if failures and not ok:
        raise SystemExit(f"all funds failed: {failures}")


if __name__ == "__main__":
    main()
