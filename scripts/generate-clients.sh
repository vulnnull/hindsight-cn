#!/usr/bin/env bash
set -e

# Script to generate Python and TypeScript clients from OpenAPI spec
# Usage: ./scripts/generate-clients.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLIENTS_DIR="$PROJECT_ROOT/memora-clients"
OPENAPI_SPEC="$PROJECT_ROOT/openapi.json"

echo "=================================================="
echo "Memora API Client Generator"
echo "=================================================="
echo "Project root: $PROJECT_ROOT"
echo "Clients directory: $CLIENTS_DIR"
echo "OpenAPI spec: $OPENAPI_SPEC"
echo ""

# Check if OpenAPI spec exists
if [ ! -f "$OPENAPI_SPEC" ]; then
    echo "❌ Error: OpenAPI spec not found at $OPENAPI_SPEC"
    echo ""
    echo "Please generate the OpenAPI spec first:"
    echo "  cd memora && uv run python -c 'from memora.api import create_app; import json; app = create_app(); print(json.dumps(app.openapi(), indent=2))' > ../openapi.json"
    exit 1
fi
echo "✓ OpenAPI spec found"
echo ""

# Check for required tools
echo "Checking required tools..."

# Check Python client generator
if ! command -v openapi-python-client &> /dev/null; then
    echo "Installing openapi-python-client..."
    pip install openapi-python-client
fi
echo "✓ openapi-python-client available"

# Check TypeScript client generator (we'll use npx, no global install needed)
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx not found. Please install Node.js"
    exit 1
fi
echo "✓ npx available (will use for openapi-typescript-codegen)"
echo ""

# Generate Python client
echo "=================================================="
echo "Generating Python client..."
echo "=================================================="

PYTHON_CLIENT_DIR="$CLIENTS_DIR/python"

# Remove old generated client code (but keep pyproject.toml)
if [ -d "$PYTHON_CLIENT_DIR/agent_memory_api_client" ]; then
    echo "Removing old Python client code..."
    rm -rf "$PYTHON_CLIENT_DIR/agent_memory_api_client"
fi

# Generate new client
# Use --meta none to avoid overwriting pyproject.toml after first generation
echo "Generating from $OPENAPI_SPEC..."
cd "$CLIENTS_DIR/python"

# Check if pyproject.toml exists (already customized)
if [ -f "pyproject.toml" ]; then
    echo "Note: Using --meta none to preserve your custom pyproject.toml"
    openapi-python-client generate --path "$OPENAPI_SPEC" --output-path . --overwrite --meta none
else
    echo "First time generation: Creating pyproject.toml with uv"
    openapi-python-client generate --path "$OPENAPI_SPEC" --output-path . --overwrite --meta uv
fi

# The generator creates a directory with the project name, we need to move it
if [ -d "memora-api-client" ]; then
    mv memora-api-client/* .
    rm -rf memora-api-client
fi

echo "✓ Python client generated at $PYTHON_CLIENT_DIR"
echo ""

# Generate TypeScript client
echo "=================================================="
echo "Generating TypeScript client..."
echo "=================================================="

TYPESCRIPT_CLIENT_DIR="$CLIENTS_DIR/typescript"

# Remove old generated client
if [ -d "$TYPESCRIPT_CLIENT_DIR/src" ]; then
    echo "Removing old TypeScript client..."
    rm -rf "$TYPESCRIPT_CLIENT_DIR/src"
fi

# Generate new client
echo "Generating from $OPENAPI_SPEC..."
npx --yes openapi-typescript-codegen \
    --input "$OPENAPI_SPEC" \
    --output "$TYPESCRIPT_CLIENT_DIR" \
    --client axios \
    --useOptions \
    --useUnionTypes \
    --exportCore true \
    --exportServices true \
    --exportModels true

echo "✓ TypeScript client generated at $TYPESCRIPT_CLIENT_DIR"
echo ""

echo "=================================================="
echo "✅ Client generation complete!"
echo "=================================================="
echo ""
echo "Python client:     $PYTHON_CLIENT_DIR"
echo "TypeScript client: $TYPESCRIPT_CLIENT_DIR"
echo ""
echo "Next steps:"
echo "  1. Review the generated clients"
echo "  2. Update package versions if needed"
echo "  3. Test the clients"
echo "  4. Publish to package registries"
echo ""
