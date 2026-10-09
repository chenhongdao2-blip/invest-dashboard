"""Export only the reviewed UI and structured research, never local evidence files.

Usage: python jobs/export_storage_research.py --source /path/to/local/preview
The existing public DRAM chart is the boundary for legacy numerical series.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "app" / "assets" / "storage_research"
LEGACY = ROOT / "docs/intelligence/2026-09-22-dram-cycles/dram-cycles.html"
UI_FILES = ("index.html", "styles.css", "research-polish.css", "app.js", "diagram.html")
MODULES = ("history", "routes", "finance", "research")
EXCLUDE_SOURCES = {"s-fin-factset", "s-fin-wind-probe"}


def constant(doc: str, name: str):
    match = re.search(r"\b" + re.escape(name) + "=", doc)
    if not match:
        raise ValueError(f"Missing chart series: {name}")
    return json.JSONDecoder().raw_decode(doc[match.end():])[0]


def clean_refs(value):
    if isinstance(value, dict):
        return {k: clean_refs(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_refs(v) for v in value if not isinstance(v, str) or v not in EXCLUDE_SOURCES]
    return value


def export(source: Path) -> dict:
    diagram = (source / "diagram.html").read_text()
    legacy = LEGACY.read_text()
    for name in ("MU_FY", "MU_Q", "HX", "MU_E", "HX_E", "MU_DD"):
        old, new = constant(legacy, name), constant(diagram, name)
        if name == "MU_DD":
            old = [[date, None if i < 35 else val] for i, (date, val) in enumerate(old)]
        if old != new:
            raise ValueError(f"{name}: new numbers require a separate source/publication review")

    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "data").mkdir(exist_ok=True)
    written = []
    for name in UI_FILES:
        text = (source / name).read_text()
        if name == "index.html":
            text = re.sub(r'<a class="reference-link".*?</a>', '', text)
            text = text.replace("正在载入本地研究数据", "正在载入研究数据").replace("本地研究原型", "研究专题")
        if name == "app.js":
            old = 'const response = await fetch(`data/${name}.json`);'
            new = 'const embedded = document.getElementById(`storage-data-${name}`); if (embedded) return JSON.parse(embedded.textContent); ' + old
            if text.count(old) != 1:
                raise ValueError("Research loader changed; update embedded-data adapter")
            text = text.replace(old, new)
            text = text.replace("请通过本地 HTTP 服务打开，资料就绪后刷新。", "请刷新页面；如仍不可用，请联系维护者。")
            text = text.replace("请检查本地数据与 DATA_CONTRACT.md；", "请联系维护者核对资料；")
        (DEST / name).write_text(text)
        written.append(name)

    counts = {"entities": 0, "sources": 0}
    for name in MODULES:
        data = clean_refs(json.loads((source / "data" / f"{name}.json").read_text()))
        data["sources"] = [s for s in data["sources"] if s["id"] not in EXCLUDE_SOURCES]
        for entry in data["sources"]:
            if not str(entry.get("url", "")).startswith("https://"):
                entry["url"] = None
                entry["scope"] = entry.get("scope", "") + " 阅读底稿仅本地留存；此处保留来源说明。"
        if name == "finance":
            data["channelNotes"][:3] = [
                "财务数值以所列SEC、交易所及发行人原始报表为准；保留原币、报告期及公开日期。",
                "Wind双通道复核未完成；本次采用公开披露核对值。各公司债务、现金和资本开支口径见逐项来源。",
            ]
        counts["entities"] += len(data.get("entities", []))
        counts["sources"] += len(data["sources"])
        rel = f"data/{name}.json"
        (DEST / rel).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        written.append(rel)

    for rel in written:
        content = (DEST / rel).read_text()
        if re.search(r"/Users/|file://|127\.0\.0\.1|localhost|metrics-audit\.json|wind-probe\.json|factset_pulls_", content):
            raise ValueError(f"Local/private reference in release: {rel}")
    manifest = {
        "edition": "2026-10-09", "dataAsOf": "2026-10-08", **counts,
        "legacySeries": "Identical to existing public chart; first 35 drawdown values suppressed for incomplete window.",
        "excluded": ["raw reports", "article/podcast full text", "vendor payloads", "local evidence URLs", "machine paths"],
        "files": {rel: hashlib.sha256((DEST / rel).read_bytes()).hexdigest() for rel in written},
    }
    (DEST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    print(json.dumps(export(parser.parse_args().source), ensure_ascii=False, indent=2))
