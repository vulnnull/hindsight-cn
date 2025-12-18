#!/bin/bash
# Reflect API examples for Hindsight CLI
# Run: bash examples/api/reflect.sh

set -e

HINDSIGHT_URL="${HINDSIGHT_API_URL:-http://localhost:8888}"

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
hindsight memory retain my-bank "Alice works at Google as a software engineer"
hindsight memory retain my-bank "Alice has been working there for 5 years"

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:reflect-basic]
hindsight memory reflect my-bank "What do you know about Alice?"
# [/docs:reflect-basic]


# [docs:reflect-with-context]
hindsight memory reflect my-bank "Should I learn Python?" --context "career advice"
# [/docs:reflect-with-context]


# [docs:reflect-high-budget]
hindsight memory reflect my-bank "Summarize my week" --budget high
# [/docs:reflect-high-budget]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
curl -s -X DELETE "${HINDSIGHT_URL}/v1/default/banks/my-bank" > /dev/null

echo "reflect.sh: All examples passed"
