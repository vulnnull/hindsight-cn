#!/bin/bash
set -e

# Script to generate OpenAPI specification and update documentation
# This runs the generate-openapi command from hindsight-dev and regenerates docs

cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

echo "Generating OpenAPI specification..."
cd hindsight-dev
uv run generate-openapi

echo ""
echo "Copying OpenAPI spec to documentation..."
cp "$ROOT_DIR/openapi.json" "$ROOT_DIR/hindsight-docs/openapi.json"

echo ""
echo "Regenerating API reference documentation..."
cd "$ROOT_DIR/hindsight-docs"
npx docusaurus clean-api-docs hindsight
npx docusaurus gen-api-docs hindsight

echo ""
echo "OpenAPI spec and documentation generated successfully!"
