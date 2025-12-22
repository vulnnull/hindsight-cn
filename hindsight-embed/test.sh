#!/bin/bash
#
# Simple smoke test for hindsight-embed CLI
# Tests retain and recall operations with embedded PostgreSQL
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Hindsight Embed Smoke Test ==="

# Check required environment
if [ -z "$HINDSIGHT_EMBED_LLM_API_KEY" ]; then
    echo "Error: HINDSIGHT_EMBED_LLM_API_KEY is required"
    exit 1
fi

# Use a unique bank ID for this test run
export HINDSIGHT_EMBED_BANK_ID="test-$$-$(date +%s)"
echo "Using bank ID: $HINDSIGHT_EMBED_BANK_ID"

# Test 1: Retain a memory
echo ""
echo "Test 1: Retaining a memory..."
OUTPUT=$(uv run --project "$SCRIPT_DIR" hindsight-embed retain "The user's favorite color is blue" 2>&1)
echo "$OUTPUT"
if ! echo "$OUTPUT" | grep -q "Stored memory"; then
    echo "FAIL: Expected 'Stored memory' in output"
    exit 1
fi
echo "PASS: Memory retained successfully"

# Test 2: Recall the memory
echo ""
echo "Test 2: Recalling memories..."
OUTPUT=$(uv run --project "$SCRIPT_DIR" hindsight-embed recall "What is the user's favorite color?" 2>&1)
echo "$OUTPUT"
if ! echo "$OUTPUT" | grep -qi "blue"; then
    echo "FAIL: Expected 'blue' in recall output"
    exit 1
fi
echo "PASS: Memory recalled successfully"

# Test 3: Retain with context
echo ""
echo "Test 3: Retaining memory with context..."
OUTPUT=$(uv run --project "$SCRIPT_DIR" hindsight-embed retain "User prefers Python over JavaScript" --context work 2>&1)
echo "$OUTPUT"
if ! echo "$OUTPUT" | grep -q "Stored memory"; then
    echo "FAIL: Expected 'Stored memory' in output"
    exit 1
fi
echo "PASS: Memory with context retained successfully"

# Test 4: Recall with budget
echo ""
echo "Test 4: Recalling with budget..."
OUTPUT=$(uv run --project "$SCRIPT_DIR" hindsight-embed recall "programming preferences" --budget mid 2>&1)
echo "$OUTPUT"
if ! echo "$OUTPUT" | grep -qi "python"; then
    echo "FAIL: Expected 'Python' in recall output"
    exit 1
fi
echo "PASS: Memory recalled with budget successfully"

echo ""
echo "=== All tests passed! ==="
