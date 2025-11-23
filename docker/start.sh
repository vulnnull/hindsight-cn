#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🚀 Starting Memora Services"
echo "============================"
echo ""

# Check if .env file exists in root
if [ ! -f ../.env ]; then
    echo "⚠️  No .env file found in project root!"
    echo ""
    echo "Creating .env from .env.example..."
    cp ../.env.example ../.env
    echo ""
    echo "⚠️  Please edit .env and set your API keys:"
    echo "   - MEMORA_API_LLM_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose --env-file ../.env up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for PostgreSQL
echo "  Waiting for PostgreSQL..."
until docker exec memora-postgres pg_isready -U memora > /dev/null 2>&1; do
  sleep 1
done
echo "  ✅ PostgreSQL is ready"

# Wait for API
echo "  Waiting for API..."
until curl -f http://localhost:8080/api/v1/agents > /dev/null 2>&1; do
  sleep 2
done
echo "  ✅ API is ready"

# Wait for Control Plane
echo "  Waiting for Control Plane..."
until curl -f http://localhost:3000 > /dev/null 2>&1; do
  sleep 2
done
echo "  ✅ Control Plane is ready"

echo ""
echo "✅ All services are running!"
echo ""
echo "📊 Service URLs:"
echo "   Control Plane: http://localhost:3000"
echo "   API:           http://localhost:8080"
echo "   PostgreSQL:    localhost:5432"
echo ""
echo "🔍 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   ./stop.sh"
echo ""
