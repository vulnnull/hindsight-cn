#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env to pick up HINDSIGHT_API_PORT if set
ROOT_DIR="$(git rev-parse --show-toplevel)"
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi
API_PORT="${HINDSIGHT_API_PORT:-8888}"

PIDS=()

kill_tree() {
    local pid=$1
    local children
    children=$(pgrep -P "$pid" 2>/dev/null) || true
    for child in $children; do
        kill_tree "$child"
    done
    kill "$pid" 2>/dev/null || true
}

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill_tree "$pid"
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Start API
echo "Starting API server..."
"$SCRIPT_DIR/start-api.sh" &
API_PID=$!
PIDS+=($API_PID)

# Wait for API to be ready
echo "Waiting for API to be ready..."
API_READY=false
for i in {1..60}; do
    if curl -sf "http://localhost:${API_PORT}/health" &>/dev/null; then
        echo "API is ready"
        API_READY=true
        break
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "API process exited unexpectedly"
        exit 1
    fi
    sleep 1
done
if [ "$API_READY" = false ]; then
    echo "API did not become ready in time"
    exit 1
fi

# Start Control Plane
echo ""
"$SCRIPT_DIR/start-control-plane.sh" &
CP_PID=$!
PIDS+=($CP_PID)

echo ""
echo "Hindsight is running!"
echo ""
echo "  API: http://localhost:${API_PORT}"
echo "  Control Plane: http://localhost:9999"
echo ""
echo "Press Ctrl+C to stop both services."
echo ""

# Poll until any service exits (wait -n requires bash 4.3+, not available on macOS)
while true; do
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "A service exited unexpectedly (PID $pid)"
            exit 1
        fi
    done
    sleep 2
done
