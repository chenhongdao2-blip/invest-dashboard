"""One-shot migration: extract CN/EN names from YAML inline comments and
rewrite each sector YAML to carry `name_cn` / `name_en` as structured fields.

Before:
    - ticker: TMO          # 赛默飞世尔 Thermo Fisher
      region: US
After:
    - ticker: TMO
      name_cn: 赛默飞世尔
      name_en: Thermo Fisher
      region: US

Idempotent — entries that already have name_cn / name_en are left alone.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UNIVERSE_DIR = REPO_ROOT / "config" / "universes"

# Match CJK-leading prefix then the rest. Hyphen / dot tolerated inside names.
_CN_PREFIX_RE = re.compile(r"^([一-鿿㐀-䶿·\-]+)\s*(.*)$")
_TICKER_LINE_RE = re.compile(
    r"^(\s*-\s*ticker:\s*[^\s#]+)\s*#\s*(.+?)\s*$"
)
_INDENT_RE = re.compile(r"^(\s*)-\s*ticker:")


_META_PAREN_RE = re.compile(
    r"\s*\((?:cross[^)]*|原[^)]*|formerly[^)]*|primary[^)]*|Nasdaq[^)]*|ADR)\)\s*",
    re.IGNORECASE,
)


def split_comment(comment: str) -> tuple[str, str]:
    """Parse e.g. '赛默飞世尔 Thermo Fisher' -> ('赛默飞世尔', 'Thermo Fisher').

    No CJK → ('', cleaned comment).

    Strips trailing meta parens like '(cross: hc_ai)' / '(ADR)' / '(原 BeiGene/BGNE)'
    so they don't end up in name_en.
    """
    comment = comment.strip()
    # Strip trailing meta parens first.
    comment = _META_PAREN_RE.sub("", comment).strip()
    m = _CN_PREFIX_RE.match(comment)
    if not m:
        return "", comment
    cn = m.group(1).strip().rstrip("-·")
    en = m.group(2).strip()
    if not cn:
        return "", en
    return cn, en


def migrate_file(path: Path, write: bool) -> int:
    """Returns number of entries updated."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    n_updated = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        m_ticker = _TICKER_LINE_RE.match(line)
        if not m_ticker:
            out.append(line)
            i += 1
            continue

        ticker_part = m_ticker.group(1).rstrip()
        comment = m_ticker.group(2)
        # Read forward to see if name_cn / name_en already exist for this entry.
        indent = _INDENT_RE.match(line).group(1)
        # Sibling-field indent = `indent` + len("- ").
        field_indent = indent + "  "
        j = i + 1
        has_name = False
        sibling_lines: list[str] = []
        while j < len(lines):
            nxt = lines[j]
            if not nxt.strip():
                break
            if not nxt.startswith(field_indent) or nxt.startswith(indent + "- "):
                break
            sibling_lines.append(nxt)
            stripped = nxt.strip()
            if stripped.startswith("name_cn:") or stripped.startswith("name_en:"):
                has_name = True
            j += 1

        cn, en = split_comment(comment)
        if has_name or (not cn and not en):
            # Already migrated, or no name info to extract — pass through.
            out.append(line)
            out.extend(sibling_lines)
            i = j
            continue

        # Write the structured form. Drop the inline comment to avoid duplication.
        out.append(ticker_part)
        if cn:
            out.append(f"{field_indent}name_cn: {cn}")
        if en:
            out.append(f"{field_indent}name_en: {en}")
        out.extend(sibling_lines)
        n_updated += 1
        i = j

    if write and n_updated > 0:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n_updated


def main(argv: list[str]) -> int:
    write = "--write" in argv
    total = 0
    for yml in sorted(UNIVERSE_DIR.glob("hc_*.yml")):
        n = migrate_file(yml, write=write)
        total += n
        print(f"{yml.name}: {n} entry(ies) {'updated' if write else 'WOULD update'}")
    print(f"---\nTotal: {total} entries ({'written to disk' if write else 'dry-run'})")
    if not write:
        print("Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
