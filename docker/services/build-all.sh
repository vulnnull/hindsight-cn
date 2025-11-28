#!/bin/bash
set -e

echo "Building Hindsight service images..."

cd "$(dirname "$0")/../.."

echo ""
echo "Building hindsight-api..."
docker build -f docker/services/api.Dockerfile -t hindsight/api:latest .

echo ""
echo "Building hindsight-control-plane..."
docker build -f docker/services/control-plane.Dockerfile -t hindsight/control-plane:latest .

echo ""
echo "✅ All service images built successfully!"
echo ""
echo "Available images:"
echo "  - hindsight/api:latest"
echo "  - hindsight/control-plane:latest"
echo ""
echo "To start all services:"
echo "  cd docker && docker-compose up"
