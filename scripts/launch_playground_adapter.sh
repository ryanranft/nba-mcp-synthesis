#!/usr/bin/env bash
set -euo pipefail

# Defaults (override via environment)
export PLAYGROUND_ADAPTER_HOST="${PLAYGROUND_ADAPTER_HOST:-0.0.0.0}"
export PLAYGROUND_ADAPTER_PORT="${PLAYGROUND_ADAPTER_PORT:-5055}"
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:3000}"
export PLAYGROUND_PROJECT_CONFIG="${PLAYGROUND_PROJECT_CONFIG:-project_configs/nba_mcp_synthesis.json}"
export PLAYGROUND_INVENTORY_REPORT="${PLAYGROUND_INVENTORY_REPORT:-data_inventory_report.json}"
export PLAYGROUND_INVENTORY_ENABLED="${PLAYGROUND_INVENTORY_ENABLED:-true}"

echo "Starting Playground Adapter on ${PLAYGROUND_ADAPTER_HOST}:${PLAYGROUND_ADAPTER_PORT} ..."
python scripts/run_playground_adapter.py &
PID=$!

cleanup() {
  echo "Stopping Playground Adapter (pid=${PID}) ..."
  kill "${PID}" >/dev/null 2>&1 || true
  wait "${PID}" >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

# Wait for health
ATTEMPTS=40
SLEEP=0.25
URL="http://localhost:${PLAYGROUND_ADAPTER_PORT}/health"

for i in $(seq 1 ${ATTEMPTS}); do
  if curl -s "${URL}" >/dev/null 2>&1; then
    echo "✅ Adapter is up: ${URL}"
    echo "Health:"
    curl -s "${URL}" | python - <<'PY'
import sys, json
print(json.dumps(json.load(sys.stdin), indent=2))
PY
    echo
    echo "Endpoints:"
    echo "  - Health         : ${URL}"
    echo "  - List Tools     : http://localhost:${PLAYGROUND_ADAPTER_PORT}/mcp/tools"
    echo "  - Inventory      : http://localhost:${PLAYGROUND_ADAPTER_PORT}/inventory/summary"
    echo
    echo "Press Ctrl+C to stop."
    break
  fi
  sleep "${SLEEP}"
done

if ! curl -s "${URL}" >/dev/null 2>&1; then
  echo "❌ Adapter failed to become healthy at ${URL}"
  exit 1
fi

wait "${PID}"
