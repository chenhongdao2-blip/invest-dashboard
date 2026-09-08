#!/usr/bin/env python3
"""Three-way-ish merge for data/refresh_manifest.json.

WHY THIS EXISTS
───────────────
`scripts/commit_data.sh` resolves rebase conflicts on the data artifacts by
keeping this run's copy (`git checkout --theirs`). That is right for
`data/snapshots.db` — a binary blob one lane rewrote wholesale — and WRONG for
the manifest.

The manifest is not one fact, it is a map of independent per-dataset facts with
independent writers. Two lanes racing on it are not editing the same value;
they are each editing their own key. Taking either side whole is a lost update,
and the update it loses is exactly the one the C4 fix added: the OTHER lane's
`failed` stamp, written moments earlier by its `if: failure()` step. The
dashboard would then go back to showing green over a dead source — the original
bug, reintroduced through the conflict path.

So: merge per key.

RESOLUTION RULE
───────────────
For each top-level key present on either side, keep the entry whose
`refreshed_at` is later. Ties, missing, or unparseable timestamps fall back to
THIS RUN's entry — this process just did the work and its stamp is the one most
likely to be current; a stale-looking upstream entry is never allowed to
overwrite a fresh local one on a technicality.

Note `refreshed_at` may legitimately be `null` (jobs/update_manifest.py --audit
registers datasets that have never run rather than inventing a timestamp), so a
missing value is normal input, not corruption.

A CORRUPT SIDE MUST NOT WEDGE THE PUSH
──────────────────────────────────────
If either side fails to parse, this exits 0 after writing a fallback and
warning on stderr. A failed merge here would abandon the rebase attempt and
throw away a full fetch cycle — the 2026-09-01 failure mode this whole file is
downstream of. Losing the merge is survivable; losing the data is not.

Usage (from commit_data.sh, during a stopped rebase):
    git show ":2:data/refresh_manifest.json" > upstream.json   # --ours   = origin/main
    git show ":3:data/refresh_manifest.json" > this_run.json   # --theirs = this run
    python3 scripts/merge_manifest.py \
        --upstream upstream.json --this-run this_run.json --out data/refresh_manifest.json

The flags are named `--upstream` / `--this-run` rather than ours/theirs on
purpose: those two words invert under rebase (see commit_data.sh's header) and
that inversion has already cost one incident.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Matches jobs/update_manifest.py's writer exactly (indent=2, insertion order).
# Key order is upstream's order with this run's new keys appended — the same
# order update_manifest.py itself produces — so the next job's rewrite is a
# no-op diff rather than a whole-file reorder.
_INDENT = 2


def _warn(msg: str) -> None:
    print(f"[merge_manifest] WARNING: {msg}", file=sys.stderr)


def _dump(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=_INDENT) + "\n"


def _parse_ts(entry: object) -> datetime | None:
    """`refreshed_at` → aware datetime, or None when absent/unusable."""
    if not isinstance(entry, dict):
        return None
    raw = entry.get("refreshed_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    # update_manifest.py always writes an offset, but a hand-edited manifest may
    # not — treat naive stamps as UTC rather than crashing the comparison.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def merge(upstream: dict, this_run: dict) -> dict:
    """Per-key union; later `refreshed_at` wins; this run breaks every tie."""
    out: dict = dict(upstream)
    for key, mine in this_run.items():
        theirs = upstream.get(key)
        if theirs is None:
            out[key] = mine
            continue
        t_mine, t_theirs = _parse_ts(mine), _parse_ts(theirs)
        if t_theirs is not None and t_mine is not None and t_theirs > t_mine:
            out[key] = theirs          # upstream is genuinely newer — keep it
        elif t_theirs is not None and t_mine is None:
            out[key] = theirs          # only upstream has a usable stamp
        else:
            out[key] = mine            # newer, or the documented fallback
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", required=True, type=Path,
                    help="the side already checked out during the rebase (origin/main)")
    ap.add_argument("--this-run", required=True, type=Path, dest="this_run",
                    help="the commit being replayed (the artifacts this run produced)")
    ap.add_argument("--out", required=True, type=Path, help="merged file to write")
    args = ap.parse_args()

    raw_mine = args.this_run.read_text(encoding="utf-8") if args.this_run.exists() else ""

    def _load(path: Path, label: str) -> dict | None:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            _warn(f"{label} side ({path}) is not readable JSON: {e}")
            return None
        if not isinstance(obj, dict):
            _warn(f"{label} side ({path}) is not a JSON object")
            return None
        return obj

    upstream = _load(args.upstream, "upstream")
    this_run = _load(args.this_run, "this-run")

    if this_run is None:
        # Nothing to merge INTO. Preferring a parseable upstream over unparseable
        # bytes keeps valid JSON in the tree; if both are corrupt we pass this
        # run's bytes through unchanged rather than inventing content.
        if upstream is not None:
            _warn("this run's manifest is unusable — keeping the upstream copy")
            args.out.write_text(_dump(upstream), encoding="utf-8")
        else:
            _warn("both manifests are unusable — writing this run's bytes verbatim")
            args.out.write_text(raw_mine, encoding="utf-8")
        return 0

    if upstream is None:
        _warn("upstream manifest is unusable — keeping this run's copy")
        args.out.write_text(_dump(this_run), encoding="utf-8")
        return 0

    merged = merge(upstream, this_run)
    args.out.write_text(_dump(merged), encoding="utf-8")
    only_upstream = sorted(set(upstream) - set(this_run))
    print(f"[merge_manifest] merged {len(merged)} datasets "
          f"(kept {len(only_upstream)} present only upstream: {only_upstream or '—'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
