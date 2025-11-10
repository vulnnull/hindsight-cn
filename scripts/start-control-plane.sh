#!/bin/bash
set -e

cd "$(dirname "$0")/../control-plane"

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

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
  echo "⚠️  Warning: .env.local not found"
  echo "Creating from .env.local.example..."
  if [ -f ".env.local.example" ]; then
    cp .env.local.example .env.local
    echo "✅ Created .env.local"
    echo "📝 Please edit .env.local if you need to change the DATAPLANE_API_URL"
    echo ""
  else
    echo "❌ Error: .env.local.example not found"
    exit 1
  fi
fi

echo "🚀 Starting Control Plane (Next.js dev server)..."
echo "📄 Loading environment from .env.local"
echo ""
echo "Control plane will be available at: http://localhost:${PORT}"
echo ""

# Set the port and run dev server
PORT=$PORT npm run dev
