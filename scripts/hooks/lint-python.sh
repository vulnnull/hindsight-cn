#!/bin/bash
# Lint Python code with Ruff

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/hindsight-api"

echo "  Linting Python with Ruff..."

# Capture output and only show on failure
OUTPUT=$(uv run ruff check --fix . 2>&1)
if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    exit 1
fi

OUTPUT=$(uv run ruff format . 2>&1)
if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    exit 1
fi

echo "  Python lint complete"
