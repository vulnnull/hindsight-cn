#!/bin/bash
set -e

echo "🚀 Starting Memora Standalone Container..."
echo "==========================================="

# Start PostgreSQL temporarily for initialization
echo "📦 Starting PostgreSQL for initialization..."
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/data -l /tmp/postgresql-init.log start"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if su - postgres -c "psql -lqt" &>/dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start"
        cat /tmp/postgresql-init.log
        exit 1
    fi
    sleep 1
done

# Create database if it doesn't exist
echo "📊 Setting up database..."
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname = 'memora'\" | grep -q 1 || psql -c 'CREATE DATABASE memora;'"

# Run initial migrations
# Note: The API also runs migrations automatically on startup.
# We run them here during initialization to ensure the database
# schema is ready before handing off to supervisord.
echo "🔄 Running initial database migrations..."
cd /app/memora

# Export environment variables
set -a
source /app/.env
set +a

/app/.venv/bin/python -m alembic upgrade head

# Stop PostgreSQL so supervisord can start it cleanly
echo "🔄 Stopping PostgreSQL to hand off to supervisord..."
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/data stop -m fast"
sleep 2

echo "✅ Initialization complete"
echo ""
echo "Starting services via supervisord..."
echo "  - PostgreSQL: localhost:5432"
echo "  - Dataplane API: http://localhost:8080"
echo "  - Control Plane: http://localhost:3000"
echo ""

# Start supervisor to manage all services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
