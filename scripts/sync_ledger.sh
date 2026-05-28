#!/usr/bin/env bash
# M5 audit fix: sync ic-foundry ledger.db → derived v5_picks.csv (B1 IP scrub)
#
# Run weekly after IC-Foundry adds new catalyst-monitor picks.
# Output: data/external/v5_picks.csv (40+ rows of v5 biotech picks)
#
# Usage:  bash scripts/sync_ledger.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEDGER="${HOME}/ic-foundry/ledger.db"
OUT="${REPO_ROOT}/data/external/v5_picks.csv"

if [ ! -f "$LEDGER" ]; then
  echo "❌ ic-foundry ledger not found at $LEDGER"
  echo "   Run on the host Mac where ic-foundry lives."
  exit 1
fi

mkdir -p "$REPO_ROOT/data/external"

uv run --with pandas python3 - <<PY
import sqlite3, pandas as pd
conn = sqlite3.connect("$LEDGER")
df = pd.read_sql_query(
    'SELECT ticker, MIN(date_added) AS pick_date, MAX(price_at_decision) AS price_at_decision '
    'FROM picks_v2 WHERE source_skill="catalyst-monitor" GROUP BY ticker',
    conn,
)
conn.close()
df["source_skill"] = "catalyst-monitor"
df["benchmark"] = "XBI"
df["name"] = df["ticker"]
df["score"] = None
df["yf_sym"] = df["ticker"]
df = df[["ticker","name","score","pick_date","benchmark","yf_sym","price_at_decision","source_skill"]]
df.to_csv("$OUT", index=False)
print(f"✅ Wrote {len(df)} rows → $OUT")
PY

echo ""
echo "Next: git add data/external/v5_picks.csv && git commit -m 'data: refresh v5 picks'"
