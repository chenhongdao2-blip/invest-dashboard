"""HK healthcare IPO — pipeline + BD detail transform (PharmCube).

Two-stage, because PharmCube data is only reachable via the PharmCube MCP, which lives in a
Claude Code session — NOT in this job's process and NOT in the Streamlit app process. So:

  Stage 1 (collection, in a Claude session):  for each IPO name, call
      mcp__pharmcube__pharmcube-mcp-drugBaseLiteCN(companyName=<cleaned>, pageNo=0, pageSize=50)
      mcp__pharmcube__pharmcube-mcp-drugDeal(transferor=<cleaned>, dateFrom=..., dateTo=..., pageNo=0)
    and dump the raw `.data` arrays (+ `.total`) into
      data/external/hk_ipo_pharma_detail_raw.json
    keyed by IPO code:  {code: {name_cleaned, pipeline_raw, pipeline_total, bd_raw, bd_total}}

  Stage 2 (this job, pure/offline):  read the raw dump, rank + trim, write the display JSON
      data/external/hk_ipo_pharma_detail.json
    which the app reads on disk (lib/ipo_tracker.load_ipo_pharma_detail). No runtime MCP.

Run:
    python3 jobs/build_ipo_pharma_detail.py          # transform existing raw dump
The company-name cleaner (strip -B/-P and any listing suffix) is exported so the collector uses
the exact same normalisation the transform expects.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXT = REPO_ROOT / "data" / "external"
RAW_JSON = EXT / "hk_ipo_pharma_detail_raw.json"
OUT_JSON = EXT / "hk_ipo_pharma_detail.json"

# Global development phase, most-advanced first. Used to rank a company's assets so the top few
# shown in the expander are the lead programs, not an arbitrary slice.
PHASE_ORDER = [
    "批准上市", "申请上市", "III期临床", "II/III期临床", "II期临床",
    "I/II期临床", "I期临床", "申报临床", "临床前",
]
PHASE_RANK = {p: i for i, p in enumerate(PHASE_ORDER)}
TOP_PIPELINE = 6   # lead assets to surface per company (full count kept as pipeline_total)
TOP_BD = 8         # most-recent out-licensing deals to surface


def clean_company_name(name: str) -> str:
    """Normalise an IPO short name to the PharmCube company key.

    CSV names carry HKEX listing suffixes ('迈威生物-B', '剂泰科技-P') that PharmCube does not use.
    Strip a trailing '-B'/'-P' (18A/18C weighted-voting tags) so the company matches.
    """
    n = str(name).strip()
    for suf in ("-B", "-P"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    return n.strip()


def rank_pipeline(drugs: list[dict]) -> list[dict]:
    """Rank a company's drugs by most-advanced global phase, keep the lead assets, trim fields."""
    def key(d: dict) -> tuple[int, str]:
        return (PHASE_RANK.get(str(d.get("latest_phase", "")), len(PHASE_ORDER)),
                str(d.get("name_short", "")))
    ranked = sorted(drugs, key=key)
    out = []
    for d in ranked[:TOP_PIPELINE]:
        out.append({
            "name": str(d.get("name_short", "") or "—"),
            "phase": str(d.get("latest_phase", "") or "—"),
            "phase_cn": str(d.get("latest_phase_cn", "") or ""),
            "target": str(d.get("targets", "") or ""),
            "disease": str(d.get("diseases", "") or ""),
            "drug_type": str(d.get("drug_type_1", "") or ""),
        })
    return out


def format_bd(deals: list[dict]) -> list[dict]:
    """Out-licensing deals (this company as transferor), most recent first, key fields only.

    deal_total_value_usd is in USD millions in the PharmCube schema; carry it through as-is and let
    the display layer format (e.g. $412.5M or $0.60B).
    """
    ranked = sorted(deals, key=lambda d: str(d.get("deal_date", "")), reverse=True)
    out = []
    for d in ranked[:TOP_BD]:
        partner = str(d.get("transferee", "") or "").strip()
        if partner in ("--", ""):
            partner = "—"
        out.append({
            "date": str(d.get("deal_date", "") or "—"),
            "partner": partner,
            "asset": str(d.get("deal_projects", "") or "").strip(),
            "value_usd_m": d.get("deal_total_value_usd"),  # may be None (undisclosed)
            "type": str(d.get("deal_type1", "") or ""),
            "region": str(d.get("transferee_region", "") or ""),
        })
    return out


def main() -> None:
    if not RAW_JSON.exists():
        raise SystemExit(
            f"[missing] {RAW_JSON.name} not found. Collect it first in a Claude session "
            f"(see module docstring, Stage 1)."
        )
    raw = json.loads(RAW_JSON.read_text())
    out: dict[str, dict] = {}
    for code, rec in raw.items():
        pipeline_raw = rec.get("pipeline_raw", []) or []
        bd_raw = rec.get("bd_raw", []) or []
        out[code] = {
            "name_cleaned": rec.get("name_cleaned", ""),
            "pipeline_total": int(rec.get("pipeline_total", len(pipeline_raw)) or 0),
            "pipeline": rank_pipeline(pipeline_raw),
            "bd_total": int(rec.get("bd_total", len(bd_raw)) or 0),
            "bd": format_bd(bd_raw),
        }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    n_pipe = sum(1 for v in out.values() if v["pipeline"])
    n_bd = sum(1 for v in out.values() if v["bd"])
    print(f"[done] {len(out)} companies | {n_pipe} with pipeline | {n_bd} with BD | wrote {OUT_JSON.name}")


if __name__ == "__main__":
    main()
