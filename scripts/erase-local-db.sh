#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "🛑 Stopping and erasing local PostgreSQL..."
echo ""

# Stop and remove containers, networks, volumes
cd docker
docker-compose down -v

echo ""
echo "✅ Local database has been stopped and all data erased!"
echo ""
