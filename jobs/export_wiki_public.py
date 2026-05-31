"""Sanitize ~/Documents/LLM Wiki/Wiki/companies/*.md → data/wiki/companies/*.md.

Strips CMSI compliance-sensitive content so the public Streamlit Cloud
deployment can render thesis-style memos without re-disseminating internal
research reports.

What gets STRIPPED:
  - `**Rating**: ... | **TP**: ...` frontmatter line (internal call)
  - `**Sources**: ...` frontmatter line (internal PDF file paths)
  - `## 管理层动态` section (analyst-only internal notes)
  - `## 矛盾与待验证` section (internal disagreements)
  - `## 自我进化追踪` section (analyst names in version history)
  - Inline `(来源: 20260130 研报)` citations
  - `> ⚠️ 系统性偏差提示: CMS HK ...` blocks (analyst bias warnings)
  - Standalone analyst-name lines (CMS HK, Jonah Chen, George Chen)

What is PRESERVED:
  - Title + Summary + Thesis
  - Sectors + Last updated (date only)
  - `## 财务快照` (yfinance-grade public data)
  - `## 核心投资逻辑` (publicly-known business thesis)
  - `## 催化剂` / `## 风险点` (publicly-known)
  - `## Related pages`

A banner is prepended explaining this is the public-sanitized version.

Usage:
    uv run python jobs/export_wiki_public.py [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INTERNAL_WIKI_DIR = Path.home() / "Documents" / "LLM Wiki" / "Wiki" / "companies"
INTERNAL_AI_WIKI_DIR = Path.home() / "Documents" / "LLM Wiki" / "Wiki" / "AI" / "companies"
PUBLIC_WIKI_DIR = REPO_ROOT / "data" / "wiki" / "companies"

# Section headers to STRIP entirely (heading + content until next ## or EOF).
STRIP_SECTIONS = {
    "管理层动态",
    "矛盾与待验证",
    "自我进化追踪",
    "Sources",   # If sections header used (rare)
}

# Patterns to strip in-place (regex). Order matters — earlier patterns run
# first, so put the most specific ones first.
INLINE_STRIPS = [
    # Rating + TP frontmatter line (whole line dropped)
    re.compile(r"^\*\*Rating\*\*[^\n]*$", re.MULTILINE),
    # Standalone Sources line
    re.compile(r"^\*\*Sources\*\*[^\n]*$", re.MULTILINE),
    # Sources segment appended to Last updated line: " | **Sources**: ..."
    # Keeps the Last updated date, drops the Sources part.
    re.compile(r"\s*\|\s*\*\*Sources\*\*[^\n]*"),
    # 市场数据 callout headers with internal TP (whole line)
    re.compile(r"^.*\*\*市场数据\*\*[^\n]*$", re.MULTILINE),
    # Inline TP price quotes that appear outside Rating line — e.g.
    # "股价：HKD19.2 | TP：HKD25 (+30%)" — strip from "TP：" through end of line
    # but keep the price context if it leads
    re.compile(r"\s*[|｜]\s*\*?\*?TP\*?\*?[：:][^|｜\n]*"),
    # CMS analyst bias warning blocks
    re.compile(r"^>\s*⚠️\s*系统性偏差提示[^\n]*(?:\n>[^\n]*)*", re.MULTILINE),
    # CMS HK Contradiction blockquotes
    re.compile(r"^>\s*⚠️\s*Contradiction[^\n]*(?:\n>[^\n]*)*", re.MULTILINE),
    # Source-tagged parens — Chinese or English, with various separators
    re.compile(r"\s*[（(]\s*来源\s*[:：][^)）]*[)）]"),
    re.compile(r"\s*[（(]\s*source\s*[:：][^)）]*[)）]", re.IGNORECASE),
    # CMS HK attribution parens — e.g. "（CMS HK, 2025-05-21）" / "(CMS HK, Jonah Chen, 2026-01-30)"
    re.compile(r"\s*[（(]\s*CMS\s*HK[^)）]*[)）]", re.IGNORECASE),
    re.compile(r"\s*[（(]\s*招商证券国际[^)）]*[)）]"),
    # CMSI analyst names that appear inline
    re.compile(r"(?:CMS HK|招商证券国际)[^,，。\n]*Jonah Chen[^,，。\n]*"),
    re.compile(r"(?:CMS HK|招商证券国际)[^,，。\n]*George Chen[^,，。\n]*"),
    # Bare analyst-name list (e.g. "Jonah Chen / George Chen / 2025-08-11")
    re.compile(r"Jonah Chen(?:\s*/\s*[\w ]+)*"),
    re.compile(r"George Chen(?:\s*/\s*[\w ]+)*"),
    # Dated internal report references — broad match for any of:
    #   "20260130 研报", "20260105 Outlook", "20250521 CMS report",
    #   "20260130 CSPC Flash Comment", "20250521 CMS HK"
    # 8-digit date + optional middle words + report-class keyword.
    re.compile(
        r"\d{8}(?:[\s\-_]+[^\s|（()）]+){0,4}\s+"
        r"(?:研报|Outlook|Flash(?:\s+Comment)?|Update|CMS\s*(?:report|HK)?|report)",
        re.IGNORECASE,
    ),
    # Bare "20260130 研报"-style without spaces (no middle word case)
    re.compile(r"\d{8}\s*(?:研报|Outlook|Flash|Update|report)", re.IGNORECASE),
    # Dated file references — 8-digit date + - + filename style, e.g.
    # "20250521-三生制药 1530 HK" or "20260130-CSPC Pharma (1093 HK)"
    re.compile(r"\d{8}[\-_][^\s|（(]+(?:\s+\(?\d{4}\s+HK\)?)?", re.IGNORECASE),
    # File-extension style citations
    re.compile(r"\d{8}[-_][^.\s]+\.(?:pdf|docx|xlsx|md)", re.IGNORECASE),
    # CMSI internal-only tags scattered in tables — full parens containing 来源
    re.compile(r"[（(]\s*来源\s*[:：][^)）]*[)）]"),
    # Mid-paren orphan "，来源：" left after dated-ref strip,
    # e.g. "（约 USD3.0bn，来源：）" → "（约 USD3.0bn）"
    re.compile(r"[，,]\s*来源\s*[:：]\s*(?=[）)])"),
    # Standalone orphan "来源：" with no content following
    re.compile(r"\bSources?[:：]\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"来源\s*[:：]\s*$", re.MULTILINE),
]

# Banner prepended to every public file.
PUBLIC_BANNER = """> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: {date} via jobs/export_wiki_public.py.

"""

_SECTION_HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def strip_sections(text: str) -> str:
    """Remove '## SectionName' blocks listed in STRIP_SECTIONS."""
    # Find all H2 headings with their positions.
    matches = list(_SECTION_HEAD_RE.finditer(text))
    if not matches:
        return text
    out = []
    last_end = 0
    for i, m in enumerate(matches):
        section_name = m.group(1).strip()
        section_start = m.start()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if section_name in STRIP_SECTIONS:
            # Emit content up to this section, skip the section itself.
            out.append(text[last_end:section_start])
            last_end = section_end
    out.append(text[last_end:])
    return "".join(out)


def sanitize(content: str) -> str:
    """Apply all strip rules to a wiki page's text."""
    # 1. Section-level strips.
    content = strip_sections(content)
    # 2. Inline regex strips.
    for pat in INLINE_STRIPS:
        content = pat.sub("", content)
    # 3. Collapse 3+ consecutive blank lines to 2.
    content = re.sub(r"\n{3,}", "\n\n", content)
    # 4. Strip trailing whitespace on each line.
    content = "\n".join(line.rstrip() for line in content.splitlines())
    # 5. Ensure final newline.
    if not content.endswith("\n"):
        content += "\n"
    return content


def export_one(src: Path, dst: Path, date_str: str) -> tuple[int, int]:
    """Returns (original_bytes, sanitized_bytes)."""
    original = src.read_text(encoding="utf-8")
    sanitized = sanitize(original)
    banner = PUBLIC_BANNER.format(date=date_str)
    final = banner + sanitized
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(final, encoding="utf-8")
    return len(original), len(final)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Show what would be written, don't touch disk")
    ap.add_argument("--limit", type=int, default=None, help="Only process first N files (for review)")
    ap.add_argument("--show", type=str, default=None, help="Print sanitized output for one filename (no write)")
    args = ap.parse_args()

    if not INTERNAL_WIKI_DIR.exists() and not INTERNAL_AI_WIKI_DIR.exists():
        print(f"❌ No internal wiki dir found: {INTERNAL_WIKI_DIR} nor {INTERNAL_AI_WIKI_DIR}",
              file=sys.stderr)
        return 1
    if not INTERNAL_WIKI_DIR.exists():
        # HC internal dir is a non-resident sync drive that can be offline. Don't bail —
        # the existing data/wiki/companies HC mirror stays (export_one never wipes the dst),
        # and we still export the AI pages so cloud gets them.
        print(f"⚠️  HC wiki dir absent (sync drive offline?) — exporting AI only: {INTERNAL_WIKI_DIR}")

    # Collect HC files (flat) + AI files (nested, recursive).
    # Use stem (filename without suffix) as dedup key; AI files won't collide with
    # HC files since the code namespaces are disjoint (NVDA vs 01093-, etc.).
    seen_stems: set[str] = set()
    all_files: list[Path] = []

    for src in sorted(INTERNAL_WIKI_DIR.glob("*.md")):
        if src.stem not in seen_stems:
            seen_stems.add(src.stem)
            all_files.append(src)

    if INTERNAL_AI_WIKI_DIR.exists():
        for src in sorted(INTERNAL_AI_WIKI_DIR.rglob("*.md")):
            if src.stem not in seen_stems:
                seen_stems.add(src.stem)
                all_files.append(src)
    else:
        print(f"⚠️  AI wiki dir not found (skipping): {INTERNAL_AI_WIKI_DIR}")

    files = all_files
    if args.limit:
        files = files[: args.limit]
    if not files:
        print(f"⚠️  No .md files found under {INTERNAL_WIKI_DIR} or {INTERNAL_AI_WIKI_DIR}")
        return 0

    if args.show:
        # Search HC dir first, then AI dir recursively.
        target = INTERNAL_WIKI_DIR / args.show
        if not target.exists():
            matches = list(INTERNAL_WIKI_DIR.glob(f"*{args.show}*"))
            if not matches and INTERNAL_AI_WIKI_DIR.exists():
                matches = list(INTERNAL_AI_WIKI_DIR.rglob(f"*{args.show}*"))
            if not matches:
                print(f"❌ Not found: {args.show}")
                return 1
            target = matches[0]
        original = target.read_text(encoding="utf-8")
        print(f"===== SANITIZED OUTPUT FOR {target.name} =====")
        print(PUBLIC_BANNER.format(date="DRYRUN") + sanitize(original))
        return 0

    import datetime
    date_str = datetime.date.today().isoformat()

    total_orig = 0
    total_san = 0
    for src in files:
        # All exports land flat in PUBLIC_WIKI_DIR regardless of source subdir.
        dst = PUBLIC_WIKI_DIR / src.name
        if args.dry_run:
            original = src.read_text(encoding="utf-8")
            sanitized = sanitize(original)
            shrink = (1 - len(sanitized) / max(1, len(original))) * 100
            print(f"[DRY] {src.name}: {len(original)} → {len(sanitized)} bytes ({shrink:+.1f}%)")
            total_orig += len(original)
            total_san += len(sanitized)
        else:
            orig, san = export_one(src, dst, date_str)
            total_orig += orig
            total_san += san
            print(f"✓ {src.name}: {orig} → {san} bytes")

    print(f"---\n{len(files)} files {'DRY-RUN' if args.dry_run else 'written'}: "
          f"{total_orig} → {total_san} bytes "
          f"({(1 - total_san / max(1, total_orig)) * 100:+.1f}% shrink)")
    if not args.dry_run:
        print(f"Public wiki at: {PUBLIC_WIKI_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
