#!/bin/bash
set -e

# Script to generate OpenAPI specification
# This runs the generate-openapi command from hindsight-dev

cd "$(dirname "$0")/.."

echo "Generating OpenAPI specification..."
cd hindsight-dev
uv run generate-openapi

echo "OpenAPI spec generated successfully!"
