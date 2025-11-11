#!/bin/bash
set -e

cd "$(dirname "$0")/../../memora-control-plane"

# Parse arguments
PORT=3000

while [[ $# -gt 0 ]]; do
  case $1 in
    --port|-p)
      PORT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --port, -p PORT    Port to run on (default: 3000)"
      echo "  --help, -h         Show this help message"
      echo ""
      echo "Example:"
      echo "  $0 --port 3001"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Check if .env exists in workspace root
ROOT_DIR="$(dirname "$0")/../.."
if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "⚠️  Warning: .env not found in workspace root"
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
echo ""
echo "Control plane will be available at: http://localhost:${PORT}"
echo ""

# Map prefixed env vars to Next.js standard vars
export HOSTNAME="${MEMORA_CP_HOSTNAME:-0.0.0.0}"
export PORT="${MEMORA_CP_PORT:-$PORT}"

# Run dev server
npm run dev
