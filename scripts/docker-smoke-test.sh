#!/bin/bash
#
# Docker Smoke Test Script
#
# Tests that a Hindsight Docker image starts correctly and becomes healthy.
# Can be run locally or in CI pipelines.
#
# Usage:
#   ./scripts/docker-smoke-test.sh <image> [target]
#
# Arguments:
#   image   - Docker image to test (e.g., hindsight-api:test, ghcr.io/vectorize-io/hindsight:latest)
#   target  - Optional: 'cp-only' for control plane, otherwise assumes API image (default: api)
#
# Environment variables:
#   GROQ_API_KEY              - Required for API/standalone images (LLM verification)
#   HINDSIGHT_API_LLM_PROVIDER - LLM provider (default: groq)
#   HINDSIGHT_API_LLM_MODEL    - LLM model (default: llama-3.3-70b-versatile)
#   SMOKE_TEST_TIMEOUT        - Timeout in seconds (default: 120)
#   SMOKE_TEST_CONTAINER_NAME - Container name (default: hindsight-smoke-test)
#
# Examples:
#   # Test a locally built image
#   ./scripts/docker-smoke-test.sh hindsight-api:test
#
#   # Test a released image
#   ./scripts/docker-smoke-test.sh ghcr.io/vectorize-io/hindsight:latest
#
#   # Test control plane image
#   ./scripts/docker-smoke-test.sh hindsight-control-plane:test cp-only
#
# Exit codes:
#   0 - Success (container healthy)
#   1 - Failure (container not healthy within timeout)
#   2 - Invalid arguments
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE="${1:-}"
TARGET="${2:-api}"
TIMEOUT="${SMOKE_TEST_TIMEOUT:-120}"
CONTAINER_NAME="${SMOKE_TEST_CONTAINER_NAME:-hindsight-smoke-test}"
LLM_PROVIDER="${HINDSIGHT_API_LLM_PROVIDER:-groq}"
LLM_MODEL="${HINDSIGHT_API_LLM_MODEL:-llama-3.3-70b-versatile}"

# Validate arguments
if [ -z "$IMAGE" ]; then
    echo -e "${RED}Error: Image argument is required${NC}"
    echo ""
    echo "Usage: $0 <image> [target]"
    echo ""
    echo "Examples:"
    echo "  $0 hindsight-api:test"
    echo "  $0 ghcr.io/vectorize-io/hindsight:latest"
    echo "  $0 hindsight-control-plane:test cp-only"
    exit 2
fi

# Determine health endpoint based on target
if [ "$TARGET" = "cp-only" ]; then
    HEALTH_PORT=9999
    HEALTH_PATH="/api/health"
    NEEDS_LLM=false
else
    HEALTH_PORT=8888
    HEALTH_PATH="/health"
    NEEDS_LLM=true
fi

# Check for required environment variables
if [ "$NEEDS_LLM" = true ] && [ -z "${GROQ_API_KEY:-}" ]; then
    echo -e "${RED}Error: GROQ_API_KEY environment variable is required for API/standalone images${NC}"
    echo "Set it with: export GROQ_API_KEY=your-api-key"
    exit 2
fi

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo -e "${YELLOW}Starting smoke test for: ${IMAGE}${NC}"
echo "  Target: $TARGET"
echo "  Health endpoint: http://localhost:${HEALTH_PORT}${HEALTH_PATH}"
echo "  Timeout: ${TIMEOUT}s"
echo ""

# Remove any existing container with the same name
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Start container based on target type
echo "Starting container..."
if [ "$TARGET" = "cp-only" ]; then
    docker run -d --name "$CONTAINER_NAME" \
        -p "${HEALTH_PORT}:${HEALTH_PORT}" \
        "$IMAGE"
else
    docker run -d --name "$CONTAINER_NAME" \
        -e HINDSIGHT_API_LLM_PROVIDER="$LLM_PROVIDER" \
        -e HINDSIGHT_API_LLM_API_KEY="${GROQ_API_KEY}" \
        -e HINDSIGHT_API_LLM_MODEL="$LLM_MODEL" \
        -p "${HEALTH_PORT}:${HEALTH_PORT}" \
        "$IMAGE"
fi

# Wait for health endpoint
echo "Waiting for health endpoint at http://localhost:${HEALTH_PORT}${HEALTH_PATH}..."
start_time=$(date +%s)

for i in $(seq 1 "$TIMEOUT"); do
    if curl -sf "http://localhost:${HEALTH_PORT}${HEALTH_PATH}" > /dev/null 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo ""
        echo -e "${GREEN}Container is healthy after ${duration}s${NC}"
        echo ""
        echo "=== Health Response ==="
        curl -s "http://localhost:${HEALTH_PORT}${HEALTH_PATH}" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:${HEALTH_PORT}${HEALTH_PATH}"
        echo ""
        echo ""
        echo "=== Container Logs (last 50 lines) ==="
        docker logs "$CONTAINER_NAME" 2>&1 | tail -50
        echo ""
        echo -e "${GREEN}Smoke test PASSED${NC}"
        exit 0
    fi

    # Show progress every 10 seconds
    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting... (${i}s)"
    fi

    # Check if container is still running
    if ! docker ps -q -f "name=$CONTAINER_NAME" | grep -q .; then
        echo ""
        echo -e "${RED}Container exited unexpectedly!${NC}"
        echo ""
        echo "=== Container Logs ==="
        docker logs "$CONTAINER_NAME" 2>&1
        echo ""
        echo -e "${RED}Smoke test FAILED${NC}"
        exit 1
    fi

    sleep 1
done

# Timeout reached
echo ""
echo -e "${RED}Container failed to become healthy after ${TIMEOUT}s${NC}"
echo ""
echo "=== Container Logs ==="
docker logs "$CONTAINER_NAME" 2>&1
echo ""
echo -e "${RED}Smoke test FAILED${NC}"
exit 1
