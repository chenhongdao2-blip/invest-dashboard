#!/usr/bin/env bash
# etf_init.sh — one-shot smoke for the ETF panel data + loader.
# Asserts the three baked files load and the loader returns sane shapes.
# Usage: bash scripts/etf_init.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# App deps are provided ephemerally by uv (see README run command).
uv run --with streamlit --with pandas --with pyyaml python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("app").resolve()))

from lib import etf_panel as ep

uni = ep.load_etf_universe()
hold = ep.load_etf_holdings()
meta = ep.etf_meta()

assert not uni.empty, "universe empty — run jobs/build_etf_panel.py"
assert not hold.empty, "holdings empty — run jobs/build_etf_panel.py"
assert meta.get("as_of"), "meta missing as_of"

print(f"universe: {len(uni)} ETFs  cols={list(uni.columns)}")
print(f"holdings: {len(hold)} rows over {hold['etf_ticker'].nunique()} ETFs")
print(f"meta as_of={meta['as_of']}  n_etfs={meta.get('n_etfs')}")

for tkr in ("XLV", "XBI"):
    w, tail = ep.holdings_for(hold, tkr)
    cov = meta.get("weight_sum_pct_by_etf", {}).get(tkr)
    print(f"  {tkr}: weighted={len(w)} tail={len(tail)} top25_cov={cov}%")

print("OK — ETF panel smoke passed")
PY
