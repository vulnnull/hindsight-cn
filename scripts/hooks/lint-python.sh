#!/bin/bash
# Lint Python code with Ruff

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/hindsight-api"

echo "  Linting Python with Ruff..."
uv run ruff check --fix .
uv run ruff format .

echo "  Python lint complete"
