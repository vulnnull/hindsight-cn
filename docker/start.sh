#!/bin/bash
# Start Hindsight (standalone all-in-one)

cd "$(dirname "$0")"

# Check for --build flag
BUILD_FLAG=""
if [[ "$1" == "--build" ]] || [[ "$1" == "-b" ]]; then
  BUILD_FLAG="--build"
  echo "🔨 Forcing rebuild of images..."
  echo ""
fi

echo "🚀 Starting Hindsight..."
echo ""

# Load .env file from project root if it exists
if [ -f ../.env ]; then
  echo "📝 Loading environment variables from .env file..."
  export $(grep -v '^#' ../.env | grep -v '^$' | xargs)
fi

# Check for required HINDSIGHT_API_LLM_API_KEY
if [ -z "$HINDSIGHT_API_LLM_API_KEY" ]; then
  echo "⚠️  Warning: HINDSIGHT_API_LLM_API_KEY is not set"
  echo ""
  echo "Set it by either:"
  echo "  1. Creating a .env file in the project root with: HINDSIGHT_API_LLM_API_KEY=your-key"
  echo "  2. Exporting: export HINDSIGHT_API_LLM_API_KEY=your-key"
  echo ""
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

cd standalone

# Run docker-compose with optional --build flag
docker-compose up $BUILD_FLAG
