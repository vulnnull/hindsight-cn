#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Parse arguments
ENV_MODE="local"
SERVER_ARGS=()

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
    --help|-h)
      echo "Usage: $0 [--env local|dev] [uvicorn options...]"
      echo ""
      echo "Options:"
      echo "  --env local    Use local environment (default)"
      echo "  --env dev      Use dev environment"
      echo ""
      echo "Uvicorn options (passed to server):"
      echo "  --host HOST              Host to bind to (default: 0.0.0.0)"
      echo "  --port PORT              Port to bind to (default: 8080)"
      echo "  --reload                 Enable auto-reload on code changes"
      echo "  --workers WORKERS        Number of worker processes (default: 1)"
      echo "  --log-level LEVEL        Log level: critical/error/warning/info/debug/trace"
      echo "  --access-log             Enable access log"
      echo "  --no-access-log          Disable access log"
      echo "  --proxy-headers          Enable X-Forwarded-Proto, X-Forwarded-For headers"
      echo "  --forwarded-allow-ips    Comma separated list of IPs to trust"
      echo "  --ssl-keyfile FILE       SSL key file"
      echo "  --ssl-certfile FILE      SSL certificate file"
      echo ""
      echo "Example:"
      echo "  $0 --env dev --reload --port 8000 --log-level debug"
      exit 0
      ;;
    *)
      # Pass all other arguments to the server
      SERVER_ARGS+=("$1")
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

echo "🚀 Starting Memory API Server with '${ENV_MODE}' environment..."
echo "📄 Loading environment from $ENV_FILE"
echo ""

# Export all variables from env file
set -a
source "$ENV_FILE"
set +a

# Extract port from SERVER_ARGS if provided, otherwise use default
PORT=8080
for ((i=0; i<${#SERVER_ARGS[@]}; i++)); do
  if [[ "${SERVER_ARGS[$i]}" == "--port" ]]; then
    PORT="${SERVER_ARGS[$((i+1))]}"
    break
  fi
done

echo "Server will be available at: http://localhost:${PORT}"
echo ""

# Set default arguments if not provided
if [[ ${#SERVER_ARGS[@]} -eq 0 ]]; then
  SERVER_ARGS=(--reload --host 0.0.0.0 --port 8080)
fi

uv run python -m memora.web.server "${SERVER_ARGS[@]}"
