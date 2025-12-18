#!/bin/bash
# Retain API examples for Hindsight CLI
# Run: bash examples/api/retain.sh

set -e

HINDSIGHT_URL="${HINDSIGHT_API_URL:-http://localhost:8888}"

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:retain-basic]
hindsight memory retain my-bank "Alice works at Google as a software engineer"
# [/docs:retain-basic]


# [docs:retain-with-context]
hindsight memory retain my-bank "Alice got promoted" \
    --context "career update"
# [/docs:retain-with-context]


# [docs:retain-async]
hindsight memory retain my-bank "Meeting notes" --async
# [/docs:retain-async]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
curl -s -X DELETE "${HINDSIGHT_URL}/v1/default/banks/my-bank" > /dev/null

echo "retain.sh: All examples passed"
