"""Build the private trust-research release from an already verified local snapshot.

Run with explicit --source and --output. The generated release is never part of
this public repository. No data is fetched or recomputed from market providers.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def amount(values):
    items = [x for x in values if isinstance(x, (int, float)) and not isinstance(x, bool)]
    return sum(items) if items else None


def clean(value, root: Path):
    if isinstance(value, str):
        prefix = str(root) + "/"
        if value.startswith(prefix):
            return value[len(prefix):]
        if value.startswith("/Users/") or value.startswith("/private/"):
            return "[本机路径已省略]"
        return value
    if isinstance(value, list):
        return [clean(x, root) for x in value]
    if isinstance(value, dict):
        return {k: clean(v, root) for k, v in value.items()}
    return value


def build(source: Path, output: Path, release_id: str, reports_dir: Path | None = None) -> dict:
    if not re.fullmatch(r"[0-9]{8}-[0-9]{4}", release_id):
        raise ValueError("release_id must be YYYYMMDD-HHMM")
    snapshot_bytes = (source / "watchboard/data/snapshot.json").read_bytes()
    model_bytes = (source / "market_data/tax/person_estimates.json").read_bytes()
    snap = json.loads(snapshot_bytes)
    model = snap["person_estimates"]
    if not model["cases"] or not model["people"]:
        raise ValueError("Empty research population; review before publishing")
    if digest(json.dumps(model, ensure_ascii=False, separators=(",", ":")).encode()) != digest(model_bytes):
        # The published model may have different JSON spacing; compare semantic data.
        if json.loads(model_bytes) != model:
            raise ValueError("Snapshot and source tax model disagree")

    release_root = output / "releases" / release_id
    if release_root.exists():
        raise FileExistsError(f"Release already exists: {release_root}")
    files = {}

    def put(rel: str, data: bytes):
        target = release_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files[rel] = {"sha256": digest(data), "blob_sha": git_blob(data), "bytes": len(data)}

    def json_gz(rel: str, obj):
        raw = json.dumps(clean(obj, source), ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        put(rel, gzip.compress(raw, mtime=0))

    by_code = defaultdict(list)
    for case in model["cases"]:
        by_code[case["code"]].append(case)
    caps = model["fx"]
    views = []
    for company in snap["companies"]:
        if not company.get("display_candidate") or company.get("market") == "HISTORY":
            continue
        code = company["code"]
        included = [c["scenario_profile"] for c in by_code[code]
                    if c.get("scenario_profile") and c["scenario_profile"].get("applicability") in ("applicable", "potentially_applicable")
                    and c["scenario_profile"].get("combined_total_cny") is not None]
        s12 = amount(amount([p["S1"].get("amount_cny"), p["S1"].get("disposal_tax_2026_cny"), p["S2"].get("amount_cny")]) for p in included)
        total = amount(p.get("combined_total_cny") for p in included)
        cap_currency = company.get("market_cap_currency") or company.get("currency")
        fx = caps.get(cap_currency)
        cap = company.get("market_cap")
        cap_cny = (cap * fx if isinstance(cap, (int, float)) and cap > 0 and isinstance(fx, (int, float)) and fx > 0
                   and company.get("market_cap_asof") == snap["market_asof"].get(company["market"]) else None)
        row = {"code": code, "name": company.get("name"), "market": company["market"],
               "industry": company.get("industry"), "status": company.get("assessment", {}).get("status"),
               "s12_cny": s12, "total_cny": total, "s12_pct": (s12 / cap_cny * 100 if s12 is not None and cap_cny else None),
               "total_pct": (total / cap_cny * 100 if total is not None and cap_cny else None),
               "policy_return": company.get("metrics", {}).get("ret_policy"),
               "price_asof": company.get("metrics", {}).get("price_date"),
               "market_cap_asof": company.get("market_cap_asof"),
               "residency_scope": "大陆居民披露证据强/中；仅按已计入股池"}
        views.append(row)
        json_gz(f"companies/{code}.json.gz", {"company": company, "cases": by_code[code],
                                             "research_note": snap.get("research_notes", {}).get("companies", {}).get(code)})

    people_views = []
    for person in model["people"]:
        profile = person.get("scenario_profile") or {}
        row = {"id": person["id"], "name": person["name"], "company": person.get("company"),
               "company_codes": person.get("company_codes") or [],
               "residency_grade": (person.get("residency_evidence") or {}).get("grade"),
               "combined_total_cny": profile.get("combined_total_cny"),
               "s1_cny": (profile.get("S1") or {}).get("amount_cny"),
               "s2_cny": (profile.get("S2") or {}).get("amount_cny"),
               "s3_realized_cny": (profile.get("S3") or {}).get("realized_tax_cny"),
               "s3_exposure_cny": (profile.get("S3") or {}).get("tax_stepped_up_cny") or (profile.get("S3") or {}).get("tax_zero_cost_cny")}
        people_views.append(row)
        ids = set((person.get("direct_case_ids") or []) + (person.get("shared_case_ids") or []))
        json_gz(f"people/{person['id']}.json.gz", {"person": person, "cases": [c for c in model["cases"] if c["id"] in ids],
                                                    "research_notes": {k: v for k, v in snap.get("research_notes", {}).get("companies", {}).items()
                                                                       if person["name"] in (v.get("associated_people") or [])}})

    strong = [p for p in people_views if p["residency_grade"] in ("strong", "medium")]
    hdl_views = {item["broker"]: item for item in snap["research_notes"]["companies"]["6862.HK"]["broker_views"]}
    broker_insights = [{"broker": hdl_views[name]["broker"], "date": hdl_views[name]["date"],
                        "source_id": hdl_views[name]["id"], "text": hdl_views[name]["view"]}
                       for name in ("国金证券", "国信证券", "摩根士丹利")]
    display = {"schema_version": 1, "release": release_id, "market_asof": snap["market_asof"],
               "scan_asof": snap["fullmarket_review"]["summary"]["asof"], "model_built_at": model["built_at"],
               "price_asof": snap["asof"], "fx": caps, "companies": views, "people": people_views,
               "coverage": {"watch_securities": len(views), "pools": len(model["cases"]), "people": len(people_views),
                            "mainland_strong_medium_people": len(strong),
                            "mainland_strong_medium_with_main_total": sum(p["combined_total_cny"] is not None for p in strong),
                            "hk_universe_codes": snap["fullmarket_review"]["summary"]["universe_hk"]},
               "insights": broker_insights,
               "disclaimer": "条件试算，非核定税单；缺失不等于零，税籍及已缴金额待核。"}
    json_gz("roster.json.gz", display)
    old_csv = source / "deliverables/个人三情形试算_全926人.csv"
    if old_csv.is_file():
        put("exports/个人三情形试算_全926人.csv", old_csv.read_bytes())
    # Keep the publisher's selected offline source files in the private release.
    evidence_dir = source / "deliverables/补税看板_20260918_1123_分享版/evidence"
    if not evidence_dir.is_dir():
        raise FileNotFoundError(evidence_dir)
    for item in evidence_dir.iterdir():
        if item.is_file() and item.suffix in (".pdf", ".html"):
            raw = item.read_bytes()
            put(f"evidence/{item.name}.gz", gzip.compress(raw, mtime=0))
            files[f"evidence/{item.name}.gz"]["original_sha256"] = digest(raw)

    if reports_dir:
        for item in reports_dir.glob("*.md"):
            if not item.stem.isdecimal():
                raise ValueError(f"Report filename must be its source ID: {item.name}")
            put(f"reports/{item.stem}.md.gz", gzip.compress(item.read_bytes(), mtime=0))

    manifest = {"schema_version": 1, "release": release_id, "source_model_sha256": digest(model_bytes),
                "source_snapshot_sha256": digest(snapshot_bytes), "price_asof": snap["asof"],
                "model_built_at": model["built_at"], "files": files}
    (release_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    current = output / "releases/current/manifest.json"
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"release": release_id, "files": len(files), "bytes": sum(r["bytes"] for r in files.values()),
            "roster_bytes": files["roster.json.gz"]["bytes"], "pools": len(model["cases"]), "people": len(people_views),
            "coverage": display["coverage"]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--release", required=True)
    p.add_argument("--reports", type=Path, help="Private downloaded analyst-report directory")
    args = p.parse_args()
    print(json.dumps(build(args.source.resolve(), args.output.resolve(), args.release, args.reports.resolve() if args.reports else None), ensure_ascii=False))


if __name__ == "__main__":
    main()
