#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Parse arguments
ENV_MODE="local"

while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENV_MODE="$2"
      if [[ "$ENV_MODE" != "local" && "$ENV_MODE" != "dev" ]]; then
        echo "Error: --env must be 'local' or 'dev'"
        exit 1
      fi
      shift 2
      ;;
    *)
      echo "Usage: $0 [--env local|dev]"
      echo ""
      echo "Options:"
      echo "  --env local    Use local environment (default)"
      echo "  --env dev      Use dev environment"
      exit 1
      ;;
  esac
done

# Source environment file
ENV_FILE=".env.${ENV_MODE}"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE not found"
  exit 1
fi

echo "🚀 Starting Memory API Server with '${ENV_MODE}' environment..."
echo "📄 Loading environment from $ENV_FILE"
echo ""

# Export all variables from env file
set -a
source "$ENV_FILE"
set +a

echo "Server will be available at: http://localhost:8080"
echo ""

open http://localhost:8080
uv run uvicorn memora.web.server:app --reload --host 0.0.0.0 --port 8080
