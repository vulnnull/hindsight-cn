#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

echo "🎨 Starting Benchmark Visualizer..."
echo ""
echo "Server will be available at: http://localhost:8001"
echo ""

cd benchmarks/visualizer
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8001
