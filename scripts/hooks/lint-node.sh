#!/bin/bash
# Lint Node/TypeScript code with ESLint and Prettier

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/hindsight-control-plane"

echo "  Linting Node/TS with ESLint and Prettier..."

# Capture output and only show on failure
OUTPUT=$(npx eslint --fix "src/**/*.{ts,tsx}" 2>&1)
if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    exit 1
fi

OUTPUT=$(npx prettier --write "src/**/*.{ts,tsx}" 2>&1)
if [ $? -ne 0 ]; then
    echo "$OUTPUT"
    exit 1
fi

echo "  Node lint complete"
