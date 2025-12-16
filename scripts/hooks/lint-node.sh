#!/bin/bash
# Lint Node/TypeScript code with ESLint and Prettier

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/hindsight-control-plane"

echo "  Linting Node/TS with ESLint and Prettier..."
npx eslint --fix "src/**/*.{ts,tsx}"
npx prettier --write "src/**/*.{ts,tsx}"

echo "  Node lint complete"
