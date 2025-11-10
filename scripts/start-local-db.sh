#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting local PostgreSQL..."
echo ""

# Start docker compose
cd local-db
docker-compose up -d

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec memora-postgres pg_isready -U memora > /dev/null 2>&1; do
  sleep 1
done

echo ""
echo "✅ PostgreSQL is ready!"
echo ""

# Initialize database schema
cd ..
export DATABASE_URL="postgresql://memora:memora_dev@localhost:5432/memora"

echo "📊 Running database migrations..."
cd memora
uv run alembic upgrade head
cd ..

echo ""
echo "✅ Database initialized successfully!"
echo ""
echo "📊 Connection Info:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: memora"
echo "  User: memora"
echo "  Password: memora_dev"
echo ""
echo "🛑 To stop and clean up:"
echo "  ./scripts/erase-local-db.sh"
echo ""
