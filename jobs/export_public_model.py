"""Desensitize data/models/<TICKER>.json → data/models_public/<TICKER>.json.

Strips the valuation CONCLUSION (the firm's price-target / DCF "call" — the
compliance-sensitive IP) so the analyst model can ship to the PUBLIC Streamlit
Cloud deployment while the forecast/ratio analysis stays visible.

George's boundary (2026-06-02): 目标价 / DCF target / 隐含空间 / 目标价 vs 现价
脱敏; 其他预测信息保留, 全公开. Mirror of jobs/export_wiki_public.py.

What gets STRIPPED (physically removed from the file — the raw JSON is publicly
downloadable on Cloud, so hiding at render time is NOT enough):
  - whole `dcf` block → target_price, ev, sensitivity grid (WACC×TG implied-price
    matrix), ev_breakdown (segment NPVs), wacc/terminal_growth, scenario_note
  - `meta.source` ("CMSI analyst model + Visible Alpha") → genericized
  - `meta.source_file` (internal xlsx filename) → dropped

What is PRESERVED:
  - periods / revenue_total / revenue_breakdown / margins / forecast
  - ratios (multiples / profitability / efficiency / cash / operational)
  - gaap_bridge (company-disclosed non-GAAP add-backs)

The full model (with dcf/target) stays in data/models/ — gitignored, local-only.

Usage:
    uv run python jobs/export_public_model.py [--dry-run] [--show TICKER]
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FULL_MODELS_DIR = REPO_ROOT / "data" / "models"            # confidential, gitignored
PUBLIC_MODELS_DIR = REPO_ROOT / "data" / "models_public"   # desensitized, committed

# Top-level keys removed wholesale (each encodes the valuation conclusion).
STRIP_TOP_KEYS = ("dcf",)

# meta keys scrubbed (internal provenance) → replacement value or dropped.
PUBLIC_SOURCE_LABEL = "Analyst model (valuation desensitized for public view)"


def desensitize(model: dict, date_str: str) -> dict:
    """Return a deep-copied, public-safe version of a full model dict."""
    pub = copy.deepcopy(model)

    # 1. Drop valuation-conclusion blocks entirely.
    for k in STRIP_TOP_KEYS:
        pub.pop(k, None)

    # 2. Scrub internal provenance in meta.
    meta = pub.setdefault("meta", {})
    meta["source"] = PUBLIC_SOURCE_LABEL
    meta.pop("source_file", None)
    meta["public"] = True
    meta["desensitized_at"] = date_str

    return pub


def _stripped_summary(full: dict, pub: dict) -> str:
    """Human-readable note of what desensitize() removed (for the run log)."""
    notes = []
    if "dcf" in full and "dcf" not in pub:
        tp = full["dcf"].get("target_price")
        notes.append(f"dcf block dropped (target_price={tp})")
    if full.get("meta", {}).get("source") != pub.get("meta", {}).get("source"):
        notes.append("meta.source genericized")
    if "source_file" in full.get("meta", {}) and "source_file" not in pub.get("meta", {}):
        notes.append("meta.source_file dropped")
    return "; ".join(notes) or "(nothing stripped)"


def export_one(src: Path, dst: Path, date_str: str, *, dry_run: bool) -> tuple[dict, dict]:
    full = json.loads(src.read_text(encoding="utf-8"))
    pub = desensitize(full, date_str)
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # sort_keys=False to preserve authoring order; ensure_ascii=False for CN labels.
        dst.write_text(json.dumps(pub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return full, pub


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Show what would be written, don't touch disk")
    ap.add_argument("--show", type=str, default=None, help="Print desensitized JSON for one TICKER (no write)")
    args = ap.parse_args()

    if not FULL_MODELS_DIR.exists():
        print(f"❌ No full-model dir found: {FULL_MODELS_DIR}", file=sys.stderr)
        return 1

    date_str = datetime.date.today().isoformat()

    if args.show:
        src = FULL_MODELS_DIR / f"{args.show}.json"
        if not src.exists():
            print(f"❌ Not found: {src}", file=sys.stderr)
            return 1
        full = json.loads(src.read_text(encoding="utf-8"))
        pub = desensitize(full, date_str)
        print(f"===== DESENSITIZED {args.show} =====")
        print(f"# stripped: {_stripped_summary(full, pub)}")
        print(json.dumps(pub, ensure_ascii=False, indent=2))
        return 0

    files = sorted(FULL_MODELS_DIR.glob("*.json"))
    if not files:
        print(f"⚠️  No model .json under {FULL_MODELS_DIR}")
        return 0

    for src in files:
        dst = PUBLIC_MODELS_DIR / src.name
        full, pub = export_one(src, dst, date_str, dry_run=args.dry_run)
        tag = "[DRY]" if args.dry_run else "✓"
        print(f"{tag} {src.name}: {_stripped_summary(full, pub)}")

    print(f"---\n{len(files)} model(s) {'DRY-RUN' if args.dry_run else 'written'} → {PUBLIC_MODELS_DIR}")
    if not args.dry_run:
        print("Reminder: data/models/ stays gitignored (full); commit data/models_public/ (desensitized).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
