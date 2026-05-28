"""LLM Wiki resolver — map a yfinance ticker to a wiki company page.

LLM Wiki at `~/Documents/LLM Wiki/Wiki/companies/*.md`.

Filename conventions observed:
- HK: zero-padded 5-digit code, e.g. `01093-cspc-pharma.md` for `1093.HK`
- US: lowercase ticker prefix, e.g. `lly-eli-lilly.md` for `LLY`
- CN: 6-digit code, e.g. `300760-mindray.md` for `300760.SZ`

Returns parsed structure: frontmatter (Summary / Thesis / Rating / TP / Sources /
Last updated) + body sections (财务快照, 核心投资逻辑, 催化剂, 风险点, 管理层动态,
矛盾与待验证, Related pages).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

WIKI_ROOT = Path.home() / "Documents" / "LLM Wiki" / "Wiki" / "companies"


@dataclass
class WikiPage:
    """Parsed wiki company page."""
    ticker: str
    file_path: Path
    title: str = ""
    summary: str = ""
    thesis: str = ""
    rating: str = ""
    tp: str = ""
    sectors: list[str] = field(default_factory=list)
    last_updated: str = ""
    sources: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    raw: str = ""

    @property
    def exists(self) -> bool:
        return self.file_path.exists()


def _candidate_stems(ticker: str) -> list[str]:
    """Return list of filename-prefix candidates to glob for.

    Examples:
        1093.HK   → ['01093-', '1093-']
        300760.SZ → ['300760-']
        LLY       → ['lly-']
        688575.SS → ['688575-']
    """
    if not ticker:
        return []
    candidates: list[str] = []
    if "." in ticker:
        code, suffix = ticker.split(".", 1)
        if suffix == "HK":
            # HK Bloomberg style uses 4-digit; wiki uses zero-padded 5-digit.
            candidates.append(f"{code.zfill(5)}-")
            candidates.append(f"{code}-")
        elif suffix in ("SZ", "SS"):
            candidates.append(f"{code}-")
        else:
            candidates.append(f"{code.lower()}-")
    else:
        candidates.append(f"{ticker.lower()}-")
    return candidates


def _resolve_path(ticker: str) -> Path | None:
    if not WIKI_ROOT.exists():
        return None
    for stem in _candidate_stems(ticker):
        matches = sorted(WIKI_ROOT.glob(f"{stem}*.md"))
        if matches:
            return matches[0]
    return None


_FRONTMATTER_KEYS = {
    "Summary": "summary",
    "Thesis": "thesis",
    "Rating": "rating",
    "TP": "tp",
    "Last updated": "last_updated",
    "Sources": "sources",
}


def _parse_frontmatter_line(line: str, page: WikiPage) -> None:
    """Match lines like `**Summary**: xxx` or `**Rating**: BUY | **TP**: USD 964`."""
    # Multiple key/value tokens may share one line (Rating + TP).
    for label, attr in _FRONTMATTER_KEYS.items():
        # Match `**Label**: value` up to next `**` or end of line.
        pattern = rf"\*\*{re.escape(label)}\*\*\s*:\s*([^*]+?)(?=\s*\*\*|\s*$)"
        match = re.search(pattern, line)
        if match:
            current = getattr(page, attr) or ""
            value = match.group(1).strip().rstrip("|").strip()
            if not current and value:
                setattr(page, attr, value)
    # Sectors: `**Sectors**: [[a]], [[b]]`
    sec_match = re.search(r"\*\*Sectors\*\*\s*:\s*(.+)", line)
    if sec_match and not page.sectors:
        page.sectors = [s.strip("[]` ") for s in re.findall(r"\[\[([^\]]+)\]\]", sec_match.group(1))]


def _parse_page(ticker: str, path: Path) -> WikiPage:
    page = WikiPage(ticker=ticker, file_path=path)
    text = path.read_text(encoding="utf-8")
    page.raw = text
    lines = text.splitlines()

    # Title is the first `# ...` line.
    for line in lines[:5]:
        if line.startswith("# "):
            page.title = line.lstrip("# ").strip()
            break

    # Frontmatter region: from start until the first `---` separator (or first `## ` section).
    in_frontmatter = True
    body_lines: list[str] = []
    current_section: str | None = None
    section_buf: dict[str, list[str]] = {}

    for line in lines:
        stripped = line.strip()
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
                continue
            if stripped.startswith("## "):
                in_frontmatter = False
                # fall through to section handling
            else:
                if stripped.startswith("**"):
                    _parse_frontmatter_line(line, page)
                continue
        if not in_frontmatter:
            if stripped.startswith("## "):
                current_section = stripped[3:].strip()
                section_buf[current_section] = []
            elif current_section is not None:
                section_buf[current_section].append(line)
            body_lines.append(line)

    page.sections = {k: "\n".join(v).strip() for k, v in section_buf.items()}
    return page


@lru_cache(maxsize=256)
def find_wiki(ticker: str) -> WikiPage | None:
    """Return parsed WikiPage for ticker, or None if no wiki entry exists."""
    if not ticker:
        return None
    path = _resolve_path(ticker)
    if path is None:
        return None
    try:
        return _parse_page(ticker, path)
    except Exception:
        # Wiki parse should never crash the page.
        return None


def has_wiki(ticker: str) -> bool:
    return _resolve_path(ticker) is not None
