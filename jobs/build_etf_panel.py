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

Run:
    python jobs/build_etf_panel.py
    python jobs/build_etf_panel.py --tickers XLV,VHT   # subset

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


def build(tickers: list[tuple[str, str]]) -> None:
    universe_rows: list[dict] = []
    holdings_rows: list[dict] = []
    weight_sum_by_etf: dict[str, float] = {}
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

        wsum = 0.0
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
        # Coverage = sum of the weighted rows we actually persist, NOT the upstream
        # `weight_sum_pct` field. They disagree for some ETFs (e.g. IBB: field 63.49 vs
        # row-sum 64.80) — the upstream field is computed on a different basis. The
        # row-sum is internally consistent with the CSV and with the table the UI renders.
        weight_sum_by_etf[ticker] = round(wsum, 2)

        for d in (perf.get("_as_of"), hold.get("_as_of")):
            if d:
                as_of_dates.append(str(d)[:10])

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
        "built_at": datetime.now().isoformat(timespec="seconds"),
    }
    _backup(META_JSON)
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {META_JSON.name}: as_of={as_of}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Bake the Healthcare ETF panel data files.")
    ap.add_argument("--tickers", help="comma-separated subset (default: full curated list)")
    args = ap.parse_args()
    if args.tickers:
        want = {t.strip().upper() for t in args.tickers.split(",")}
        sel = [(t, s) for t, s in ETF_LIST if t in want]
        # allow ad-hoc tickers not in the curated map (sub_sector='Other')
        sel += [(t, "Other") for t in want if t not in {x for x, _ in ETF_LIST}]
    else:
        sel = ETF_LIST
    build(sel)


if __name__ == "__main__":
    main()
