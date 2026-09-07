"""build_etf_panel.py — bake the Healthcare ETF panel data files.

Produces three committed artifacts the Streamlit app reads at render time:
    data/external/etf_hc_universe.csv   # 1 row / ETF: profile + perf windows
    data/external/etf_hc_holdings.csv   # long: 1 row / holding (rank/symbol/name/weight)
    data/external/etf_hc_meta.json      # as_of + source + per-ETF weight coverage

Why a job (not a runtime fetch): the deployed app cannot call the etf-data MCP
(it is session-bound), so — exactly like jobs/build_hk_ipo_tracker.py — a build
step bakes the data into CSV/JSON and the app stays a pure reader.

Data sources, after the 2026-09-07 swap:
  * profile + performance — the etf-data-mcp repo's own CLI (`cli.py profile|
    performance <ticker>`) through its pinned .venv, i.e. yfinance. Still healthy.
    Override the repo path with $ETF_DATA_MCP if it lives elsewhere.
  * holdings — FactSet Ownership `fund_holdings`, read from
    `data/external/_factset_raw/etf_holdings_<T>.json` with --from-factset-json.
    The CLI's own holdings path (stockanalysis → barchart) is DEAD: stockanalysis
    404s on every ETF and barchart returns "No Constituents" (both re-verified
    2026-09-07). Run without the flag and the job will simply refuse to write.

Holdings shape differs by source, and meta.holdings_cap_note records which one
produced the file. stockanalysis weighted only the top ~25 and returned the rest
symbol-only (rank/name/weight = None), so the UI's "+N more constituents" line was
literally all that was known about them. FactSet weights every constituent, so
there is no weightless tail at all and the page caps the table for readability
instead. Either way an unknown weight stays None — never 0.0, which would turn
"unknown" into "zero" (the bug Codex caught in the etf-data-mcp audit).

DEGRADATION GATE (R3 audit item 7). etf-data-mcp resolves holdings as
stockanalysis (weights) → barchart (symbols only, every row numbered 1..N, no
weights) → error envelope. The 2026-08-29 rebuild ran while stockanalysis was
returning 404 for every ETF, took the barchart fallback, and overwrote a good
weighted snapshot with a weightless one — while meta.json and the refresh
manifest both still said "ok". Nothing in the pipeline noticed.

So this job now REFUSES to write when an ETF comes back with zero weighted rows,
and records the upstream provenance (`_source` / `_partial` / `_reliability`) in
meta.json either way. Pass --allow-unweighted to persist a degraded fetch
deliberately; it is then labelled as degraded in meta, not silently.

Run:
    python jobs/build_etf_panel.py --from-factset-json    # the live path
    python jobs/build_etf_panel.py                        # legacy CLI holdings (dead)
    python jobs/build_etf_panel.py --tickers XLV,VHT   # subset
    python jobs/build_etf_panel.py --allow-unweighted  # persist a degraded fetch

Network: the etf-data-mcp CLI calls ensure_proxy_env() itself (China proxy 7897).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "external"
UNIVERSE_CSV = OUT_DIR / "etf_hc_universe.csv"
HOLDINGS_CSV = OUT_DIR / "etf_hc_holdings.csv"
META_JSON = OUT_DIR / "etf_hc_meta.json"

ETF_MCP_DIR = Path(os.environ.get("ETF_DATA_MCP", str(Path.home() / "projects" / "etf-data-mcp")))
ETF_MCP_PY = ETF_MCP_DIR / ".venv" / "bin" / "python"
ETF_MCP_CLI = ETF_MCP_DIR / "cli.py"

# Curated v1 Healthcare ETF universe. (ticker, sub_sector) — sub_sector groups the
# page; AUM sorts within a group. Extend by adding rows.
ETF_LIST: list[tuple[str, str]] = [
    ("XLV", "Broad"),
    ("VHT", "Broad"),
    ("IYH", "Broad"),
    ("IBB", "Biotech"),
    ("XBI", "Biotech"),
    ("XPH", "Pharma"),
    ("PPH", "Pharma"),
    ("IHI", "Devices"),
    ("IHF", "Providers"),
    ("ARKG", "Genomics"),
]

UNIVERSE_FIELDS = [
    "domain", "sub_sector", "ticker", "name", "aum", "expense_ratio",
    "price", "year_high", "year_low",
    "ret_1m", "ret_3m", "ret_ytd", "ret_1y", "ret_3y", "ret_5y",
    "vol", "max_dd",
]
HOLDINGS_FIELDS = ["etf_ticker", "rank", "symbol", "name", "weight_pct"]

_RET_KEYS = {"ret_1m": "1M", "ret_3m": "3M", "ret_ytd": "YTD",
             "ret_1y": "1Y", "ret_3y": "3Y", "ret_5y": "5Y"}


def _run_cli(tool: str, ticker: str) -> dict:
    """Invoke `cli.py <tool> <ticker>` in the etf-data-mcp venv; return parsed JSON."""
    if not ETF_MCP_PY.exists():
        sys.exit(f"etf-data-mcp venv python not found: {ETF_MCP_PY}\n"
                 f"Set $ETF_DATA_MCP to the repo path (with a built .venv).")
    proc = subprocess.run(
        [str(ETF_MCP_PY), str(ETF_MCP_CLI), tool, ticker],
        cwd=str(ETF_MCP_DIR), capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cli {tool} {ticker} failed (rc={proc.returncode}): "
                           f"{proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout)


def _num(v):
    """Pass numbers through, coerce '' / None to None (never 0)."""
    if v is None or v == "":
        return None
    return v


def _backup(path: Path) -> None:
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = path.with_name(path.name + f".bak-{ts}")
        shutil.copy2(path, bak)
        print(f"  backup: {bak.name}")


def _atomic_write(path: Path, write_fn) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        write_fn(fh)
    tmp.replace(path)


# ---- FactSet holdings adapter (R3 follow-up: stockanalysis died) ------------
# stockanalysis returns 404 for every ETF (verified 2026-09-07) and barchart
# comes back empty, so the only holdings source left is FactSet Ownership's
# `fund_holdings`. FactSet is a SESSION MCP: a local job cannot call it. So the
# split is the research-data Data-Fetcher pattern — a Claude session fetches and
# writes one JSON per ETF under `data/external/_factset_raw/`, and this job reads
# those files instead of calling the etf-data-mcp holdings tool. Profile and
# performance still come from that CLI: only stockanalysis broke, yfinance is fine.
#
# The raw files carry ONLY securityTicker / securityName / weightClose plus the
# holdings date. FactSet's internal identifiers (fsymId, fsymSecurityId,
# fsymRegionalId) and the position sizes (adjHolding, adjMarketValue) are
# licensed data and must never land in this public repo.
FACTSET_RAW_DIR = OUT_DIR / "_factset_raw"
_FACTSET_BANNED_KEYS = {"fsymId", "fsymSecurityId", "fsymRegionalId",
                        "adjHolding", "adjMarketValue"}

# Words FactSet writes in caps that title() would mangle back into caps-lite.
_NAME_KEEP_CAPS = {"ADR", "GDR", "REIT", "PLC", "NV", "SA", "AG", "AB", "USA",
                   "US", "UK", "II", "III", "AI"}
_NAME_FIXUPS = {"Abbvie": "AbbVie", "Biontech": "BioNTech", "Crispr": "CRISPR",
                "Genedx": "GeneDx", "Iqvia": "IQVIA", "Ge": "GE",
                "Cvs": "CVS", "Hca": "HCA", "Unitedhealth": "UnitedHealth",
                "Bioxcel": "BioXcel", "Biomarin": "BioMarin",
                "Incyte": "Incyte", "Idexx": "IDEXX", "Dexcom": "DexCom"}


def _factset_name(raw: str | None) -> str | None:
    """`ELI LILLY & CO  COM` → `Eli Lilly & Co Com`.

    FactSet ships security names in caps with doubled spaces. The old
    stockanalysis names were already mixed-case marketing names ("Eli Lilly and
    Company"); those cannot be refreshed any more, so the panel takes FactSet's
    and normalises it rather than blending two sources in one display column.
    Share-class suffixes (COM, CL A) are kept — they distinguish real rows.
    """
    if not raw:
        return None
    words = " ".join(str(raw).split()).split(" ")
    out = []
    for w in words:
        if w in _NAME_KEEP_CAPS or not w.isalpha():
            out.append(w)
            continue
        t = w.capitalize()
        out.append(_NAME_FIXUPS.get(t, t))
    return " ".join(out)


def _factset_symbol(raw: str | None) -> str | None:
    """`LLY-US` → `LLY`; a non-US line keeps its region (`AZN-GB`) so the symbol
    stays honest — the Ticker-Drill deep link would not resolve it either way."""
    if not raw:
        return None
    s = str(raw).strip()
    return s[:-3] if s.upper().endswith("-US") else s


def _read_factset_holdings(ticker: str, raw_dir: Path) -> dict:
    """Read one `etf_holdings_<TICKER>.json` and return the SAME envelope shape
    `_run_cli("holdings", …)` produces, so `build()` does not care which source
    it got. Raises on anything that would silently degrade the panel."""
    path = raw_dir / f"etf_holdings_{ticker.upper()}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"no FactSet holdings file for {ticker}: {path}\n"
            f"  A Claude session must fetch it first:\n"
            f"    FactSet_Ownership(data_type='fund_holdings', ids=['{ticker}-US'], topn='ALL')\n"
            f"  and write securityTicker / securityName / weightClose to that path."
        )
    doc = json.loads(path.read_text(encoding="utf-8"))

    rows_in = doc.get("holdings") or []
    if not rows_in:
        raise ValueError(f"{path.name}: 'holdings' is empty — refusing to build a weightless panel")
    leaked = _FACTSET_BANNED_KEYS.intersection(rows_in[0])
    if leaked:
        raise ValueError(
            f"{path.name}: licensed FactSet fields present ({', '.join(sorted(leaked))}). "
            "This repo is public — the raw files may carry ticker / name / weight only."
        )

    as_of = str(doc.get("as_of") or "")[:10]
    if len(as_of) != 10:
        raise ValueError(f"{path.name}: missing or malformed 'as_of' (got {doc.get('as_of')!r})")

    parsed: list[dict] = []
    seen: set[str] = set()
    for i, h in enumerate(rows_in):
        w = h.get("weightClose")
        sym = _factset_symbol(h.get("securityTicker"))
        if w is None or sym is None:
            raise ValueError(
                f"{path.name}: row {i} has no {'weight' if w is None else 'ticker'} "
                f"({h!r}). FactSet weights every line; a hole means a bad transcription."
            )
        if sym in seen:          # same security on two lines would double-count the weight
            raise ValueError(f"{path.name}: duplicate symbol {sym!r} at row {i}")
        seen.add(sym)
        parsed.append({"symbol": sym, "name": _factset_name(h.get("securityName")),
                       "weight_pct": round(float(w), 4)})

    parsed.sort(key=lambda r: r["weight_pct"], reverse=True)
    for i, r in enumerate(parsed, start=1):
        r["rank"] = i

    wsum = sum(r["weight_pct"] for r in parsed)
    if not 50.0 <= wsum <= 101.5:
        raise ValueError(
            f"{path.name}: weights sum to {wsum:.2f}% over {len(parsed)} rows — outside "
            "[50, 101.5]. Under 50 means the fetch was truncated (topn not ALL); over "
            "101.5 means rows were duplicated. Either way the panel would be wrong."
        )

    return {
        "holdings": parsed,
        "_source": "factset:fund_holdings",
        "_as_of": as_of,
        "_reliability": "HIGH",
        "_partial": False,
        "_error": None,
    }


def build(tickers: list[tuple[str, str]], *, allow_unweighted: bool = False,
          factset_dir: Path | None = None) -> None:
    universe_rows: list[dict] = []
    holdings_rows: list[dict] = []
    weight_sum_by_etf: dict[str, float] = {}
    weighted_rows_by_etf: dict[str, int] = {}
    provenance_by_etf: dict[str, dict] = {}
    holdings_as_of_by_etf: dict[str, str] = {}
    as_of_dates: list[str] = []

    for ticker, sub_sector in tickers:
        src = "FactSet json" if factset_dir else "etf-data-mcp"
        print(f"[{ticker}] profile / performance via etf-data-mcp; holdings via {src} …")
        prof = _run_cli("profile", ticker)
        perf = _run_cli("performance", ticker)
        hold = (_read_factset_holdings(ticker, factset_dir) if factset_dir
                else _run_cli("holdings", ticker))

        rets = perf.get("returns_pct", {}) or {}
        row = {
            "domain": "healthcare",
            "sub_sector": sub_sector,
            "ticker": ticker,
            "name": prof.get("name"),
            "aum": _num(prof.get("aum")),
            "expense_ratio": _num(prof.get("expense_ratio")),
            "price": _num(prof.get("price")),
            "year_high": _num(prof.get("year_high")),
            "year_low": _num(prof.get("year_low")),
            "vol": _num(perf.get("annualized_vol")),
            "max_dd": _num(perf.get("max_drawdown")),
        }
        for col, key in _RET_KEYS.items():
            row[col] = _num(rets.get(key))
        universe_rows.append(row)

        # Upstream provenance — the field that would have caught 2026-08-29 on the day.
        provenance_by_etf[ticker] = {
            "source": hold.get("_source"),
            "reliability": hold.get("_reliability"),
            "partial": bool(hold.get("_partial")),
            "error": hold.get("_error"),
        }

        wsum = 0.0
        n_weighted = 0
        for h in hold.get("holdings", []) or []:
            wpct = _num(h.get("weight_pct"))
            holdings_rows.append({
                "etf_ticker": ticker,
                "rank": _num(h.get("rank")),
                "symbol": h.get("symbol"),
                "name": h.get("name"),          # None for tail — kept as None, not ""
                "weight_pct": wpct,             # None for tail — never 0
            })
            if wpct is not None:
                wsum += float(wpct)
                n_weighted += 1
        weighted_rows_by_etf[ticker] = n_weighted
        # Coverage = sum of the weighted rows we actually persist, NOT the upstream
        # `weight_sum_pct` field. They disagree for some ETFs (e.g. IBB: field 63.49 vs
        # row-sum 64.80) — the upstream field is computed on a different basis. The
        # row-sum is internally consistent with the CSV and with the table the UI renders.
        weight_sum_by_etf[ticker] = round(wsum, 2)

        if hold.get("_as_of"):
            holdings_as_of_by_etf[ticker] = str(hold["_as_of"])[:10]
        for d in (perf.get("_as_of"), hold.get("_as_of")):
            if d:
                as_of_dates.append(str(d)[:10])

    # ---- degradation gate: never silently overwrite weights with no-weights ----
    degraded = sorted(t for t, n in weighted_rows_by_etf.items() if n == 0)
    if degraded:
        detail = "\n".join(
            f"    {t}: 0 weighted rows of {sum(1 for r in holdings_rows if r['etf_ticker'] == t)}"
            f"  source={provenance_by_etf[t]['source']!r}"
            f" reliability={provenance_by_etf[t]['reliability']!r}"
            + (f"\n        error: {provenance_by_etf[t]['error']}"
               if provenance_by_etf[t].get("error") else "")
            for t in degraded
        )
        msg = (
            f"REFUSING TO WRITE — {len(degraded)} ETF(s) came back with no weights at all:\n"
            f"{detail}\n"
            "  This is the symbols-only upstream fallback, not real data. Writing it would\n"
            "  overwrite the good weighted snapshot with a weightless one (see the module\n"
            "  docstring: that is exactly what happened on 2026-08-29).\n"
            "  Fix the upstream source, or re-run with --allow-unweighted to persist this\n"
            "  fetch deliberately (it will be labelled degraded in etf_hc_meta.json)."
        )
        if not allow_unweighted:
            sys.exit(msg)
        print(f"WARNING: {msg}\n  --allow-unweighted given: writing anyway, labelled degraded.")

    # ---- write (backup-before-overwrite, atomic) ----
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    _backup(UNIVERSE_CSV)
    def _w_uni(fh):
        w = csv.DictWriter(fh, fieldnames=UNIVERSE_FIELDS)
        w.writeheader()
        w.writerows(universe_rows)
    _atomic_write(UNIVERSE_CSV, _w_uni)
    print(f"wrote {UNIVERSE_CSV.name}: {len(universe_rows)} ETFs")

    _backup(HOLDINGS_CSV)
    def _w_hold(fh):
        w = csv.DictWriter(fh, fieldnames=HOLDINGS_FIELDS)
        w.writeheader()
        w.writerows(holdings_rows)
    _atomic_write(HOLDINGS_CSV, _w_hold)
    print(f"wrote {HOLDINGS_CSV.name}: {len(holdings_rows)} holding rows")

    # `as_of` is what jobs/update_manifest.py stamps on the `etf_hc_holdings` feed
    # and ages against its 45-day gate, so it must be the HOLDINGS date. Mixing in
    # the yfinance performance date (which is always ~today) made the feed look
    # fresh whatever state the holdings were in — the 2026-08-29 failure mode in
    # miniature. Keep the perf date, but as its own field.
    perf_as_of = max(as_of_dates) if as_of_dates else None
    if holdings_as_of_by_etf:
        as_of = max(holdings_as_of_by_etf.values())
    else:
        as_of = perf_as_of or datetime.now().strftime("%Y-%m-%d")
    meta = {
        "as_of": as_of,
        "holdings_as_of_oldest": (min(holdings_as_of_by_etf.values())
                                  if holdings_as_of_by_etf else None),
        "perf_as_of": perf_as_of,
        "source": (
            "holdings: FactSet Ownership fund_holdings (via a Claude session, baked to\n"
            "data/external/_factset_raw/); profile+perf: etf-data-mcp CLI (yfinance)"
            if factset_dir else
            "etf-data-mcp CLI (stockanalysis+barchart for holdings, yfinance for profile/perf)"
        ),
        "holdings_as_of_by_etf": holdings_as_of_by_etf,
        "n_etfs": len(universe_rows),
        "holdings_cap_note": (
            "FactSet weights EVERY constituent, so there is no symbol-only tail: "
            "weighted_rows == total rows. The page shows the top rows and lists the "
            "rest as '+N more'. Unknown weight is still None, never 0."
            if factset_dir else
            "Upstream caps weighted rows at top ~25; tail is symbol-only "
            "(rank/name/weight=None). Tail kept for '+N more'; unknown weight is None, never 0."
        ),
        "weight_sum_pct_by_etf": weight_sum_by_etf,
        "weighted_rows_by_etf": weighted_rows_by_etf,
        "upstream_by_etf": provenance_by_etf,
        "degraded_etfs": degraded,
        "built_at": datetime.now().isoformat(timespec="seconds"),
    }
    _backup(META_JSON)
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {META_JSON.name}: as_of={as_of}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Bake the Healthcare ETF panel data files.")
    ap.add_argument("--tickers", help="comma-separated subset (default: full curated list)")
    ap.add_argument(
        "--allow-unweighted", action="store_true",
        help="persist a fetch in which some ETF has zero weighted rows (default: refuse)",
    )
    ap.add_argument(
        "--from-factset-json", nargs="?", const=str(FACTSET_RAW_DIR), default=None,
        metavar="DIR",
        help=f"read holdings from FactSet json files instead of the etf-data-mcp "
             f"holdings tool (default dir: {FACTSET_RAW_DIR})",
    )
    args = ap.parse_args()
    if args.tickers:
        want = {t.strip().upper() for t in args.tickers.split(",")}
        sel = [(t, s) for t, s in ETF_LIST if t in want]
        # allow ad-hoc tickers not in the curated map (sub_sector='Other')
        sel += [(t, "Other") for t in want if t not in {x for x, _ in ETF_LIST}]
    else:
        sel = ETF_LIST
    build(sel, allow_unweighted=args.allow_unweighted,
          factset_dir=Path(args.from_factset_json) if args.from_factset_json else None)


if __name__ == "__main__":
    main()
