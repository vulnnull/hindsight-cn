#!/bin/bash

# Start the Hindsight documentation server
# This script starts a local Docusaurus development server for the documentation

set -e

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/hindsight-docs"

echo "Starting documentation server..."
echo "Documentation directory: $DOCS_DIR"

# Check if node_modules exists
if [ ! -d "$DOCS_DIR/node_modules" ]; then
    echo "Installing documentation dependencies..."
    cd "$DOCS_DIR"
    npm install
fi

# Start the Docusaurus dev server
cd "$DOCS_DIR"
echo ""
echo "Starting Docusaurus development server..."
echo "Documentation will be available at: http://localhost:3000"
echo ""
npm run start
