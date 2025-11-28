#!/bin/bash
set -e

echo "🚀 Starting Hindsight..."
echo ""

# Start API (with embedded pg0)
echo "⚡ Starting Hindsight API (with embedded database)..."
cd /app/api
python -m hindsight_api.web.server &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API..."
for i in {1..30}; do
    if curl -sf http://localhost:8888/health &>/dev/null || curl -sf http://localhost:8888/docs &>/dev/null; then
        echo "✅ API is ready"
        break
    fi
    sleep 1
done

# Start Control Plane
echo "🎛️  Starting Control Plane..."
cd /app/control-plane
npm start &
CP_PID=$!

echo ""
echo "✅ Hindsight is running!"
echo ""
echo "📍 Access:"
echo "   Control Plane: http://localhost:3000"
echo "   API:           http://localhost:8888"
echo ""

# Wait for any process to exit
wait -n

# Exit with status of first exited process
exit $?
