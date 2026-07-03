#!/usr/bin/env bash
# Harness init.sh — one-shot smoke launch of the local dashboard for visual audit.
# Real-machine acceptance gate runs against this instance (claude-in-chrome :8599).
# China network: yfinance / browser fetch need the local proxy.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${PORT:-8599}"
export PYTHONPATH=app
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

# Kill any stale instance on the port (hot process caches lib modules → must reboot
# after a branch/lib change, per memory streamlit-cloud-reboot-after-lib-change).
if lsof -ti ":${PORT}" >/dev/null 2>&1; then
  lsof -ti ":${PORT}" | xargs kill 2>/dev/null || true
  sleep 1
fi

exec .venv/bin/python -m streamlit run app/streamlit_app.py \
  --server.port "${PORT}" --server.headless true --server.runOnSave false
