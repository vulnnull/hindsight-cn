#!/bin/bash
# Lint Python code with Ruff (hindsight-api and hindsight packages only)

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Get staged Python files in hindsight-api or hindsight directories only
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^(hindsight-api|hindsight)/.*\.py$' || true)

if [ -z "$STAGED_PY_FILES" ]; then
    echo "  No Python files to lint"
    exit 0
fi

cd "$REPO_ROOT/hindsight-api"

# Check if ruff is available
if ! uv run ruff --version &> /dev/null; then
    echo "  Ruff not installed, skipping Python lint"
    exit 0
fi

echo "  Linting Python files with Ruff..."

# Convert to absolute paths
ABSOLUTE_FILES=""
for file in $STAGED_PY_FILES; do
    ABSOLUTE_FILES="$ABSOLUTE_FILES $REPO_ROOT/$file"
done

# Run ruff check with fix
uv run ruff check --fix $ABSOLUTE_FILES

# Run ruff format
uv run ruff format $ABSOLUTE_FILES

# Re-add fixed files to staging
cd "$REPO_ROOT"
for file in $STAGED_PY_FILES; do
    if [ -f "$file" ]; then
        git add "$file"
    fi
done

echo "  Python lint complete"
