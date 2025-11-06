#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

# Parse --env argument to source the right env file
ENV_MODE="local"
ARGS=()

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
      ARGS+=("$1")
      shift
      ;;
  esac
done

# Source environment file
ENV_FILE=".env.${ENV_MODE}"
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE not found"
  exit 1
fi

echo "🚀 Starting LoComo Benchmark with '${ENV_MODE}' environment..."
echo "📄 Loading environment from $ENV_FILE"
echo ""

# Export all variables from env file
set -a
source "$ENV_FILE"
set +a

uv run python benchmarks/locomo/locomo_benchmark.py "${ARGS[@]}"
