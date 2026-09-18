"""Verify a private trust-research release before it is uploaded.

This is intentionally read-only and prints only counts and hashes, never content.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(root: Path, release_id: str | None = None) -> dict:
    manifest_path = root / "releases" / (release_id or "current") / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema_version"] == 1
    assert release_id is None or manifest["release"] == release_id
    release = root / "releases" / manifest["release"]
    files = manifest["files"]
    assert files and "roster.json.gz" in files
    for rel, record in files.items():
        target = (release / rel).resolve()
        assert target.is_relative_to(release.resolve()), rel
        data = target.read_bytes()
        assert len(data) == record["bytes"], rel
        assert sha256(data) == record["sha256"], rel
        assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == record["blob_sha"], rel
    roster_bytes = gzip.decompress((release / "roster.json.gz").read_bytes())
    roster = json.loads(roster_bytes)
    assert roster["coverage"]["pools"] > 0
    assert roster["coverage"]["people"] == len(roster["people"])
    assert roster["coverage"]["watch_securities"] == len(roster["companies"])
    strong = [x for x in roster["people"] if x["residency_grade"] in ("strong", "medium")]
    assert roster["coverage"]["mainland_strong_medium_people"] == len(strong)
    assert roster["coverage"]["mainland_strong_medium_with_main_total"] == sum(x["combined_total_cny"] is not None for x in strong)
    assert len(roster_bytes) < 1_000_000
    assert len(set(x["id"] for x in roster["people"])) == len(roster["people"])
    assert len(set(x["code"] for x in roster["companies"])) == len(roster["companies"])
    if roster["companies"] and "market_cap_cny" in roster["companies"][0]:
        assert all("market_cap_cny" in row for row in roster["companies"])
        for row in roster["companies"]:
            cap = row["market_cap_cny"]
            if cap is None:
                assert row["s12_pct"] is None and row["total_pct"] is None, row["code"]
            else:
                assert cap > 0, row["code"]
                for numerator, ratio in ((row["s12_cny"], row["s12_pct"]),
                                         (row["total_cny"], row["total_pct"])):
                    assert (numerator is None) == (ratio is None), row["code"]
                    if numerator is not None:
                        assert math.isclose(ratio, numerator / cap * 100, rel_tol=1e-10), row["code"]
    assert all(f"people/{x['id']}.json.gz" in files for x in roster["people"])
    assert all(f"companies/{x['code']}.json.gz" in files for x in roster["companies"])
    for rel in files:
        if rel.endswith(".json.gz"):
            raw = gzip.decompress((release / rel).read_bytes())
            assert b"/Users/" not in raw and b"/private/var/" not in raw and b"localhost" not in raw, rel
    return {"release": manifest["release"], "files": len(files), "roster_bytes": len(roster_bytes),
            "source_model_sha256": manifest["source_model_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--release")
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve(), args.release), ensure_ascii=False))
