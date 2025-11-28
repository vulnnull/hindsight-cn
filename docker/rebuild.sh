#!/bin/bash
# Rebuild Hindsight images from scratch

cd "$(dirname "$0")/standalone"

echo "🔨 Rebuilding Hindsight images (no cache)..."
echo ""

# Build with no cache to force complete rebuild
docker-compose build --no-cache

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "To start Hindsight:"
echo "  ./start.sh"
