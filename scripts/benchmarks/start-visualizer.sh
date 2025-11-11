#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

echo "🎨 Starting Benchmark Visualizer..."
echo ""
echo "Server will be available at: http://localhost:8001"
echo ""

uv run python memora-dev/benchmarks/visualizer/main.py
