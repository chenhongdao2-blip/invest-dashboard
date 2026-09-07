#!/usr/bin/env bash
# Reusable data commit+push for refresh jobs (CI cloud runner OR local Mac launchd).
#
# WHY — multiple refresh lanes (fetch_eod, fetch_sec, fetch_public_data, local Mac)
# all push data commits to the SAME branch (main). Naive `git push` races and one
# lane clobbers another. This does fetch → rebase → push with retry so concurrent
# lanes serialize safely instead of fighting.
#
# Usage:  scripts/commit_data.sh "<commit message>" [path ...]
#   - message: required commit message (append [skip ci] yourself if wanted)
#   - paths:   optional; defaults to the standard data artifact set
#
# Exits 0 (and is a no-op) when there is nothing to commit.
# Exits non-zero when the push could not be completed, so the caller's
# `if: failure()` step can stamp `failed` into data/refresh_manifest.json.
#
# ──────────────────────────────────────────────────────────────────────────
# 2026-09-01 FAILURE MODE — why the conflict handling below exists
# ──────────────────────────────────────────────────────────────────────────
# The `fetch_public_data` run of 2026-09-01 died and left NO trace in the
# manifest. Root cause, from the run log:
#
#   1. `git pull --rebase` replayed this run's data commit onto a main that had
#      moved. `data/snapshots.db` is a 67 MB BINARY blob, so git cannot merge it
#      hunk-wise — it stopped with `CONFLICT (content)` and left the file in the
#      unmerged (UU) state, with the rebase still IN PROGRESS.
#   2. The old retry loop was `for i in 1..5; do git pull --rebase && git push; done`
#      with no conflict handling. Every subsequent attempt re-entered `git pull`
#      while unmerged paths existed and died instantly on:
#         "Pulling is not possible because you have unmerged files."
#      All 5 attempts burned in under a second; the job exited non-zero having
#      thrown away a full fetch cycle of data.
#
# The fix has two halves:
#   • RESOLVE, don't discard. A `git reset --hard origin/main` would clear the
#     wedge but also destroy the freshly-fetched data this run just paid for.
#     Instead we keep OUR file and re-stage it.
#   • NEVER re-enter the loop mid-rebase. Any attempt that cannot be resolved
#     aborts the rebase first, so the next iteration starts from a clean tree —
#     that is what turns a transient race into a retry instead of a wedge.
#
# ⚠ `--ours` / `--theirs` ARE INVERTED DURING A REBASE. Verified empirically
#   2026-09-07 on a scratch repo, do not "fix" this from intuition:
#     git rebase checks out the UPSTREAM and replays your commits onto it, so
#       --ours   = origin/main's version   (the side already checked out)
#       --theirs = YOUR replayed commit    (this run's freshly-fetched data)
#   To keep the data this run produced we therefore want `--theirs`.
#   (Under `git merge` the two would mean the opposite; this script only rebases.)
set -euo pipefail

MSG="${1:?usage: commit_data.sh \"<message>\" [path ...]}"
shift || true

if [ "$#" -gt 0 ]; then
  PATHS=("$@")
else
  PATHS=(
    data/snapshots.db
    data/refresh_manifest.json
    data/external/hc_index_comparison.csv
  )
fi

git config user.email "${GIT_AUTHOR_EMAIL:-data-bot@github.com}"
git config user.name  "${GIT_AUTHOR_NAME:-data-bot}"

# Stage only the artifacts that actually exist (avoid `git add` aborting on a path
# a given lane didn't produce).
STAGED=0
for p in "${PATHS[@]}"; do
  if [ -e "$p" ]; then
    git add "$p" && STAGED=1
  fi
done
[ "$STAGED" -eq 0 ] && { echo "[commit_data] no artifact paths present — nothing to do"; exit 0; }

if git diff-index --quiet HEAD; then
  echo "[commit_data] no data changes to commit"
  exit 0
fi

git commit -m "$MSG"

# Determine the branch to push to (CI: the checked-out branch; local: current).
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# True while a rebase (either backend) is stopped mid-flight.
rebase_in_progress() {
  [ -d "$(git rev-parse --git-path rebase-merge)" ] || \
  [ -d "$(git rev-parse --git-path rebase-apply)" ]
}

# Leave the tree clean so the NEXT attempt can `git pull` instead of dying on
# "unmerged files" — the exact 2026-09-01 wedge.
abandon_attempt() {
  git rebase --abort 2>/dev/null || git merge --abort 2>/dev/null || true
}

# Resolve conflicts by keeping THIS RUN's freshly-produced artifacts.
# Returns 0 only when every conflicted path was one of ours and is now staged.
resolve_our_artifacts() {
  conflicted="$(git diff --name-only --diff-filter=U || true)"
  [ -z "$conflicted" ] && return 0
  old_ifs="$IFS"; IFS='
'
  for c in $conflicted; do
    ours=0
    for p in "${PATHS[@]}"; do
      [ "$c" = "$p" ] && ours=1 && break
    done
    if [ "$ours" -ne 1 ]; then
      # A conflict outside our artifact set (someone edited source under us) is
      # not ours to auto-resolve — bail out and let the retry/abort path run.
      echo "[commit_data] unexpected conflict in '$c' (not a data artifact) — abandoning attempt" >&2
      IFS="$old_ifs"; return 1
    fi
    # --theirs == the commit being replayed == this run's data. See the header.
    echo "[commit_data] binary conflict on '$c' — keeping this run's freshly-fetched copy"
    git checkout --theirs -- "$c" || { IFS="$old_ifs"; return 1; }
    git add -- "$c" || { IFS="$old_ifs"; return 1; }
  done
  IFS="$old_ifs"
  return 0
}

for i in 1 2 3 4 5; do
  if git pull --rebase --autostash origin "$BRANCH"; then
    if git push origin "HEAD:$BRANCH"; then
      echo "[commit_data] pushed on attempt $i"
      exit 0
    fi
    # Rebase clean, push rejected → someone landed between the two. Just retry.
  elif rebase_in_progress; then
    if resolve_our_artifacts && GIT_EDITOR=true git rebase --continue; then
      if git push origin "HEAD:$BRANCH"; then
        echo "[commit_data] pushed on attempt $i (after resolving a data conflict)"
        exit 0
      fi
    else
      abandon_attempt
    fi
  fi
  # Whatever happened, do not carry a half-finished rebase into the next attempt.
  if rebase_in_progress; then abandon_attempt; fi
  echo "[commit_data] push attempt $i failed — retrying after $((i * 5))s"
  sleep "$((i * 5))"
done

abandon_attempt
echo "[commit_data] ERROR: could not push after retries" >&2
exit 1
