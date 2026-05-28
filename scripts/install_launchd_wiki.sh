#!/bin/bash
# Install the weekly wiki-sync launchd job.
# Idempotent — safe to run multiple times.
#
# Usage:
#   bash scripts/install_launchd_wiki.sh           # install + load
#   bash scripts/install_launchd_wiki.sh --uninstall

set -euo pipefail

PLIST_SRC="/Users/gcc/invest-dashboard/scripts/com.gcc.invest-dashboard.wiki-sync.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.gcc.invest-dashboard.wiki-sync.plist"
LABEL="com.gcc.invest-dashboard.wiki-sync"

if [[ "${1:-}" == "--uninstall" ]]; then
    echo "Unloading $LABEL..."
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    rm -f "$PLIST_DST"
    echo "✓ Uninstalled."
    exit 0
fi

echo "Installing weekly wiki-sync launchd job..."
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "/Users/gcc/invest-dashboard/.omc/logs"

# If already loaded, unload first to pick up any plist changes.
launchctl unload "$PLIST_DST" 2>/dev/null || true

# Copy plist (LaunchAgents requires it under ~/Library/LaunchAgents/).
cp "$PLIST_SRC" "$PLIST_DST"

# Set strict perms expected by launchd.
chmod 644 "$PLIST_DST"

# Make script executable.
chmod +x /Users/gcc/invest-dashboard/scripts/wiki_weekly_sync.sh

# Load — runs on next schedule (Sunday 20:00). Use bootstrap (modern API) on
# macOS 10.10+; fall back to load on older systems.
if launchctl bootstrap "gui/$(id -u)" "$PLIST_DST" 2>/dev/null; then
    echo "✓ Loaded via launchctl bootstrap."
else
    launchctl load "$PLIST_DST"
    echo "✓ Loaded via launchctl load (legacy API)."
fi

echo ""
echo "Verify with:"
echo "  launchctl list | grep $LABEL"
echo ""
echo "Test run NOW (out-of-band, doesn't disturb the weekly schedule):"
echo "  bash /Users/gcc/invest-dashboard/scripts/wiki_weekly_sync.sh"
echo "  tail -f /Users/gcc/invest-dashboard/.omc/logs/wiki_weekly.log"
echo ""
echo "Uninstall later:"
echo "  bash /Users/gcc/invest-dashboard/scripts/install_launchd_wiki.sh --uninstall"
