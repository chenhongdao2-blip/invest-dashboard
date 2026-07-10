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
# HC company pages were reorganized from Wiki/companies/ (flat, now gone) into
# Wiki/Healthcare/<subsector>/<code>-<name>.md (2026-07 restructure). The main
# company page lives at the subsector level; deeper per-company subdirs hold call
# transcripts/summaries + an index.md (NOT thesis pages) — excluded below.
INTERNAL_WIKI_DIR = Path.home() / "Documents" / "LLM Wiki" / "Wiki" / "Healthcare"
INTERNAL_AI_WIKI_DIR = Path.home() / "Documents" / "LLM Wiki" / "Wiki" / "AI" / "companies"
PUBLIC_WIKI_DIR = REPO_ROOT / "data" / "wiki" / "companies"

# Filenames that are directory indexes / call notes, never company thesis pages.
_SKIP_NAMES = {"index.md"}

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
    # 市场数据 / CMS Outlook / 估值参考 callout BLOCK — bold header line + its
    # following bullet body (which carries the internal TP/估值). The old rule only
    # dropped the header line and orphaned the "- TP：…" bullet below it (leak).
    re.compile(
        r"^[ \t]*\*\*[^\n]*(?:市场数据|CMS[^\n]*Outlook|Outlook[^\n]*估值|估值参考|"
        r"市场估值参考)[^\n]*\*\*[：:]?[ \t]*(?:\n[ \t]*[-*][^\n]*)+",
        re.MULTILINE,
    ),
    # 光秃 TP / 目标价 bullet = CMS 自己的目标价(无 broker 归属)。公开的卖方一致
    # 预期 TP 都在表格行(| 目标价 | … | 卖方一致预期 (broker) |),不以 "- TP：" 起头,
    # 不受此规则影响。
    re.compile(r"^[ \t]*[-*]\s*\*{0,2}(?:TP|目标价)\*{0,2}[：:][^\n]*$", re.MULTILINE),
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
    re.compile(r"Zhen Tan(?:\s*/\s*[\w ]+)*"),
    # Analyst-call parens carrying an internal rating + TP, e.g.
    # "（Zhen Tan/, 2026-04-22, BUY/TP USD613 维持）" or "（… TP HKD102 …）".
    re.compile(r"[（(][^）)]*(?:BUY|SELL|HOLD|Neutral)[^）)]*TP[^）)]*[）)]", re.IGNORECASE),
    re.compile(r"[（(][^）)]*TP\s*(?:USD|HKD|JPY|RMB|CNY)[^）)]*[）)]", re.IGNORECASE),
    # Bare "BUY/TP USD613 维持"-style rating+TP action (e.g. in a changelog line).
    re.compile(
        r"(?:BUY|SELL|HOLD|Neutral)\s*/\s*TP\s*(?:USD|HKD|JPY|RMB|CNY)?\s*[\d,]+"
        r"[^，。；\n]*", re.IGNORECASE),
    # CMS HK / CMSI internal-view CLAUSE strip — surgical (keeps the rest of the
    # sentence). Eats "，CMS HK 将 TP 从 HKD7.3 上调至 HKD16.9（+84%）" out of a Summary
    # while leaving the public thesis around it. Public consensus TPs never carry a
    # "CMS HK" / "CMSI" marker, so they survive.
    re.compile(r"[，,、；;：:]?\s*CMS\s?HK[^，。；\n]*"),
    re.compile(r"[，,、；;：:]?\s*CMSI[^，。；\n]*"),
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

# A page that carries this reliability disclaimer sources its rating/TP from
# SELL-SIDE research (public, intentionally shown) — do NOT strip its inline TP
# mentions. Absent it, a CMS-covered page's inline TP is the internal call → strip.
_SELLSIDE_DISCLAIMER_RE = re.compile(r"评级\s*/\s*目标价为卖方观点|基于卖方研报")

# NDR = CMS non-deal-roadshow internal notes — the source ref (and any analyst
# name / date riding in the same paren) is internal. Safe to strip everywhere.
_NDR_STRIPS = [
    re.compile(r"[（(][^）)]*NDR[^）)]*[）)]"),                        # （2026-04-13 NDR 更新）
    re.compile(r"[，,、；;]?\s*来源[：:][^，。；\n]*NDR[^，。；\n]*"),   # 来源：… NDR …
    re.compile(r"[，,、；;]?\s*[^，。；\n]*\bNDR\b[^，。；\n]*"),        # any residual NDR clause
]
# Internal target-price action in PROSE (only stripped on non-sell-side pages via
# the page-level gate). Eats "TP 从 HKD82 上调至 HKD102.6" / "目标价从 … 上调至 …".
_INTERNAL_TP_PROSE = re.compile(
    r"[，,、；;。]?\s*(?:TP|目标价)\s*从\s*[A-Za-z$]{0,4}\s?[\d,.]+"
    r"[^，。；\n]*?(?:上调|下调|升|降)至[^，。；\n]*"
)

_SECTION_HEAD_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
# Any H2 whose heading names the internal desk / analysis is stripped whole —
# e.g. "CMS HK view vs 外部 broker", "2025-11-27 CMSI NDR takeaway",
# "外部 broker baseline … 与 CMS HK view 的分歧". Over-strips the external-broker
# framing too, but that's the safe direction for a public deployment.
_CMS_HEADING_RE = re.compile(r"CMS\s?HK|CMSI|招商证券国际", re.IGNORECASE)


def strip_sections(text: str) -> str:
    """Remove '## SectionName' blocks in STRIP_SECTIONS or whose heading names the
    internal desk (CMS HK / CMSI). Strips heading + body until the next H2/EOF."""
    matches = list(_SECTION_HEAD_RE.finditer(text))
    if not matches:
        return text
    out = []
    last_end = 0
    for i, m in enumerate(matches):
        section_name = m.group(1).strip()
        section_start = m.start()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if section_name in STRIP_SECTIONS or _CMS_HEADING_RE.search(section_name):
            out.append(text[last_end:section_start])
            last_end = section_end
    out.append(text[last_end:])
    return "".join(out)


def _cleanup_orphans(text: str) -> str:
    """After clause/line strips, tidy orphans that would otherwise read oddly:
    empty bullets ('- ' / '* '), table rows gone all-empty, and 3+ blank lines."""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if s in ("-", "*", "•"):                       # bullet emptied by a clause strip
            continue
        if s.startswith("|") and s.replace("|", "").replace("-", "").replace(":", "").strip() == "":
            # keep genuine markdown separator rows (---|---); drop all-blank data rows
            if "-" not in s:
                continue
        lines.append(ln)
    return "\n".join(lines)


def sanitize(content: str) -> str:
    """Apply all strip rules to a wiki page's text."""
    # Page-level gate: sell-side-disclaimered pages keep their (public) broker TPs;
    # CMS-covered pages get inline internal-TP prose stripped too.
    is_sellside = bool(_SELLSIDE_DISCLAIMER_RE.search(content))
    # 1. Section-level strips.
    content = strip_sections(content)
    # 2. Inline regex strips.
    for pat in INLINE_STRIPS:
        content = pat.sub("", content)
    # 2a. NDR internal-source refs (safe everywhere).
    for pat in _NDR_STRIPS:
        content = pat.sub("", content)
    # 2a'. Inline internal TP action — only on CMS-covered (non-sell-side) pages.
    if not is_sellside:
        content = _INTERNAL_TP_PROSE.sub("", content)
    # 2b. Tidy orphans left by clause/line strips (empty bullets / blank table rows).
    content = _cleanup_orphans(content)
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

    # Collect HC files + AI files. Use stem (filename without suffix) as dedup key;
    # AI files won't collide with HC files (code namespaces disjoint: NVDA vs 01093-).
    seen_stems: set[str] = set()
    all_files: list[Path] = []

    # HC: subsector-level company pages only — Healthcare/<subsector>/<code>-<name>.md.
    # `*/*.md` matches exactly that depth: it skips Healthcare/index.md (too shallow)
    # AND the deeper per-company transcript subdirs (Healthcare/<sub>/<co>/date.md).
    for src in sorted(INTERNAL_WIKI_DIR.glob("*/*.md")):
        if src.name in _SKIP_NAMES:
            continue
        if src.stem not in seen_stems:
            seen_stems.add(src.stem)
            all_files.append(src)

    if INTERNAL_AI_WIKI_DIR.exists():
        for src in sorted(INTERNAL_AI_WIKI_DIR.rglob("*.md")):
            if src.name in _SKIP_NAMES:
                continue
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
            matches = [p for p in INTERNAL_WIKI_DIR.rglob(f"*{args.show}*")
                       if p.is_file() and p.name not in _SKIP_NAMES]
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
