#!/bin/bash
# Lint and format Node/TypeScript code (hindsight-control-plane only)

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Get staged JS/TS files in control-plane only
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^hindsight-control-plane/.*\.(js|jsx|ts|tsx)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "  No Node/TS files to lint"
    exit 0
fi

cd "$REPO_ROOT/hindsight-control-plane"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  node_modules not found, skipping Node lint"
    exit 0
fi

echo "  Linting and formatting Node/TS files..."

# Convert to relative paths
RELATIVE_FILES=""
for file in $STAGED_FILES; do
    RELATIVE_FILES="$RELATIVE_FILES ${file#hindsight-control-plane/}"
done

# Run ESLint with --fix
npx eslint --fix $RELATIVE_FILES || true

# Run Prettier for formatting
npx prettier --write $RELATIVE_FILES || true

# Re-add fixed files to staging
cd "$REPO_ROOT"
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        git add "$file"
    fi
done

echo "  Node lint complete"
