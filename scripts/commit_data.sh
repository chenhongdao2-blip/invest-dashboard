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

for i in 1 2 3 4 5; do
  if git pull --rebase --autostash origin "$BRANCH" && git push origin "HEAD:$BRANCH"; then
    echo "[commit_data] pushed on attempt $i"
    exit 0
  fi
  echo "[commit_data] push attempt $i failed — retrying after $((i * 5))s"
  sleep "$((i * 5))"
done

echo "[commit_data] ERROR: could not push after retries" >&2
exit 1
