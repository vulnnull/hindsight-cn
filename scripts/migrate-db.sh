#!/bin/bash
set -e

cd "$(dirname "$0")/../memora"

echo "🔄 Database Migration Script"
echo "============================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
  echo "⚠️  DATABASE_URL environment variable is not set!"
  echo ""
  echo "Please set DATABASE_URL to your PostgreSQL connection string."
  echo "Example:"
  echo "  export DATABASE_URL=\"postgresql://user:password@localhost:5432/dbname\""
  echo ""
  echo "For local development:"
  echo "  export DATABASE_URL=\"postgresql://memora:memora_dev@localhost:5432/memora\""
  echo ""
  exit 1
fi

echo "📊 Database: $DATABASE_URL"
echo ""

# Check current migration status
echo "📋 Current migration status:"
echo "----------------------------"
uv run alembic current || true
echo ""

# Show pending migrations
echo "🔍 Checking for pending migrations..."
echo "-------------------------------------"
PENDING=$(uv run alembic heads 2>&1)
CURRENT=$(uv run alembic current 2>&1 | grep -o '[a-f0-9]\{12\}' | head -n 1 || echo "none")

if echo "$CURRENT" | grep -q "none"; then
  echo "⚠️  Database is not initialized. Running all migrations..."
else
  echo "Current revision: $CURRENT"
fi
echo ""

# Run migrations
echo "🚀 Running migrations to latest version..."
echo "-------------------------------------------"
uv run alembic upgrade head

echo ""
echo "✅ Database migrations completed successfully!"
echo ""

# Show final status
echo "📊 Final migration status:"
echo "--------------------------"
uv run alembic current
echo ""

echo "✨ Database is now up to date!"
echo ""
