#!/bin/bash
set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR/memora-control-plane" || exit 1

# Check if .env exists in workspace root
if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "⚠️  Warning: .env not found in workspace root at $ROOT_DIR/.env"
  echo "📝 Please create a .env file if you need to set MEMORA_CP_DATAPLANE_API_URL"
  echo "   Default will use http://localhost:8080"
  echo ""
fi

echo "🚀 Starting Control Plane (Next.js dev server)..."
if [ -f "$ROOT_DIR/.env" ]; then
  echo "📄 Loading environment from $ROOT_DIR/.env"
  # Load env vars from root .env file
  set -a
  source "$ROOT_DIR/.env"
  set +a
fi
PORT=3000
echo ""
echo "Control plane will be available at: http://localhost:${PORT}"
echo ""

# Map prefixed env vars to Next.js standard vars
export HOSTNAME="${MEMORA_CP_HOSTNAME:-0.0.0.0}"
export PORT="${MEMORA_CP_PORT:-$PORT}"

# Run dev server
npm run dev
