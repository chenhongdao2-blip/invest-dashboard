"""build_etf_panel.py — bake the Healthcare ETF panel data files.

Produces three committed artifacts the Streamlit app reads at render time:
    data/external/etf_hc_universe.csv   # 1 row / ETF: profile + perf windows
    data/external/etf_hc_holdings.csv   # long: 1 row / holding (rank/symbol/name/weight)
    data/external/etf_hc_meta.json      # as_of + source + per-ETF weight coverage

Why a job (not a runtime fetch): the deployed app cannot call the etf-data MCP
(it is session-bound), so — exactly like jobs/build_hk_ipo_tracker.py — a build
step bakes the data into CSV/JSON and the app stays a pure reader.

Data source: the etf-data-mcp repo's own CLI (`cli.py profile|performance|holdings
<ticker>`), invoked through its pinned .venv so we reuse the identical fetch +
merge logic the MCP tools use (stockanalysis + barchart for holdings, yfinance for
profile/perf). Override the repo path with $ETF_DATA_MCP if it lives elsewhere.

Holdings caveat (baked into meta.holdings_cap_note): the upstream caps weighted
rows at the top ~25; the long tail comes back symbol-only (rank/name/weight = None).
We persist the tail rows as-is so the UI can show "+N more constituents". We never
fill an unknown weight as 0.0 (that would turn "unknown" into "zero" — the exact
bug Codex caught in the etf-data-mcp audit).

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
    python jobs/build_etf_panel.py
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


def build(tickers: list[tuple[str, str]], *, allow_unweighted: bool = False) -> None:
    universe_rows: list[dict] = []
    holdings_rows: list[dict] = []
    weight_sum_by_etf: dict[str, float] = {}
    weighted_rows_by_etf: dict[str, int] = {}
    provenance_by_etf: dict[str, dict] = {}
    as_of_dates: list[str] = []

    for ticker, sub_sector in tickers:
        print(f"[{ticker}] fetching profile / performance / holdings …")
        prof = _run_cli("profile", ticker)
        perf = _run_cli("performance", ticker)
        hold = _run_cli("holdings", ticker)

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

    as_of = max(as_of_dates) if as_of_dates else datetime.now().strftime("%Y-%m-%d")
    meta = {
        "as_of": as_of,
        "source": "etf-data-mcp CLI (stockanalysis+barchart for holdings, yfinance for profile/perf)",
        "n_etfs": len(universe_rows),
        "holdings_cap_note": "Upstream caps weighted rows at top ~25; tail is symbol-only "
                             "(rank/name/weight=None). Tail kept for '+N more'; unknown weight "
                             "is None, never 0.",
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
    args = ap.parse_args()
    if args.tickers:
        want = {t.strip().upper() for t in args.tickers.split(",")}
        sel = [(t, s) for t, s in ETF_LIST if t in want]
        # allow ad-hoc tickers not in the curated map (sub_sector='Other')
        sel += [(t, "Other") for t in want if t not in {x for x, _ in ETF_LIST}]
    else:
        sel = ETF_LIST
    build(sel, allow_unweighted=args.allow_unweighted)


if __name__ == "__main__":
    main()
