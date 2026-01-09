#!/bin/bash
set -e

# Script to start Prometheus and Grafana for Hindsight metrics
# This provides a single command for the full monitoring stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MONITORING_DATA_DIR="$PROJECT_ROOT/.monitoring"
API_PORT="${API_PORT:-8888}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-8889}"
GRAFANA_PORT="${GRAFANA_PORT:-8890}"

# Versions
PROMETHEUS_VERSION="2.48.0"
GRAFANA_VERSION="10.2.2"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$OS" in
    darwin) OS_NAME="darwin" ;;
    linux) OS_NAME="linux" ;;
    *) echo "Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
    x86_64) ARCH_NAME="amd64" ;;
    arm64|aarch64) ARCH_NAME="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Prometheus paths
PROMETHEUS_DIR="$MONITORING_DATA_DIR/prometheus"
PROMETHEUS_ARCHIVE="prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}.tar.gz"
PROMETHEUS_URL="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/${PROMETHEUS_ARCHIVE}"
PROMETHEUS_BIN="$PROMETHEUS_DIR/prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}/prometheus"

# Grafana paths
GRAFANA_DIR="$MONITORING_DATA_DIR/grafana"
GRAFANA_ARCHIVE="grafana-${GRAFANA_VERSION}.${OS_NAME}-${ARCH_NAME}.tar.gz"
GRAFANA_URL="https://dl.grafana.com/oss/release/${GRAFANA_ARCHIVE}"
GRAFANA_HOME="$GRAFANA_DIR/grafana-v${GRAFANA_VERSION}"
GRAFANA_BIN="$GRAFANA_HOME/bin/grafana"

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down monitoring stack..."

    if [ -n "$PROM_PID" ] && kill -0 "$PROM_PID" 2>/dev/null; then
        kill "$PROM_PID" 2>/dev/null || true
    fi

    if [ -n "$GRAFANA_PID" ] && kill -0 "$GRAFANA_PID" 2>/dev/null; then
        kill "$GRAFANA_PID" 2>/dev/null || true
    fi

    echo "Monitoring stack stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Download Prometheus if needed
if [ ! -f "$PROMETHEUS_BIN" ]; then
    echo "Downloading Prometheus ${PROMETHEUS_VERSION}..."
    mkdir -p "$PROMETHEUS_DIR"
    cd "$PROMETHEUS_DIR"
    curl -sL -o "$PROMETHEUS_ARCHIVE" "$PROMETHEUS_URL"
    tar xzf "$PROMETHEUS_ARCHIVE"
    rm "$PROMETHEUS_ARCHIVE"
    echo "Prometheus ready"
fi

# Download Grafana if needed
if [ ! -f "$GRAFANA_BIN" ]; then
    echo "Downloading Grafana ${GRAFANA_VERSION}..."
    mkdir -p "$GRAFANA_DIR"
    cd "$GRAFANA_DIR"
    curl -sL -o "$GRAFANA_ARCHIVE" "$GRAFANA_URL"
    tar xzf "$GRAFANA_ARCHIVE"
    rm "$GRAFANA_ARCHIVE"
    echo "Grafana ready"
fi

# Create Prometheus config
mkdir -p "$PROMETHEUS_DIR"
cat > "$PROMETHEUS_DIR/prometheus.yml" <<EOF
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'hindsight-api'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:$API_PORT']
    metrics_path: '/metrics'
EOF

# Create Grafana provisioning directories
GRAFANA_PROV_DIR="$GRAFANA_DIR/provisioning"
mkdir -p "$GRAFANA_PROV_DIR/datasources"
mkdir -p "$GRAFANA_PROV_DIR/dashboards"
mkdir -p "$GRAFANA_DIR/dashboards"
mkdir -p "$GRAFANA_DIR/data"

# Copy dashboards from project root monitoring directory
cp "$PROJECT_ROOT/monitoring/grafana/dashboards/"*.json "$GRAFANA_DIR/dashboards/"

# Create Grafana datasource config
cat > "$GRAFANA_PROV_DIR/datasources/prometheus.yaml" <<EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:$PROMETHEUS_PORT
    isDefault: true
    editable: false
    uid: prometheus
EOF

# Create Grafana dashboard provisioning config
cat > "$GRAFANA_PROV_DIR/dashboards/dashboards.yaml" <<EOF
apiVersion: 1
providers:
  - name: 'Hindsight'
    orgId: 1
    folder: 'Hindsight'
    folderUid: 'hindsight'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: $GRAFANA_DIR/dashboards
EOF

# Create Grafana config
cat > "$GRAFANA_DIR/grafana.ini" <<EOF
[server]
http_port = $GRAFANA_PORT
root_url = http://localhost:$GRAFANA_PORT

[security]
admin_user = admin
admin_password = admin
disable_initial_admin_creation = false

[auth.anonymous]
enabled = true
org_name = Main Org.
org_role = Viewer

[paths]
data = $GRAFANA_DIR/data
logs = $GRAFANA_DIR/logs
plugins = $GRAFANA_DIR/plugins
provisioning = $GRAFANA_PROV_DIR

[log]
mode = console
level = warn

[dashboards]
default_home_dashboard_path = $GRAFANA_DIR/dashboards/hindsight-operations.json
EOF

echo ""
echo "=================================="
echo "  Hindsight Monitoring Stack"
echo "=================================="
echo ""
echo "  Grafana:     http://localhost:$GRAFANA_PORT"
echo "  Prometheus:  http://localhost:$PROMETHEUS_PORT"
echo "  API Metrics: http://localhost:$API_PORT/metrics"
echo ""
echo "  Dashboards:"
echo "    - Hindsight Operations"
echo "    - Hindsight LLM Metrics"
echo "    - Hindsight API Service"
echo ""
echo "=================================="
echo ""

# Check if API is running
if ! curl -s "http://localhost:$API_PORT/metrics" > /dev/null 2>&1; then
    echo "WARNING: Hindsight API not detected at localhost:$API_PORT"
    echo "         Start the API first: ./scripts/dev/start-api.sh"
    echo ""
fi

# Start Prometheus in background
cd "$(dirname "$PROMETHEUS_BIN")"
"$PROMETHEUS_BIN" \
    --config.file="$PROMETHEUS_DIR/prometheus.yml" \
    --storage.tsdb.path="$PROMETHEUS_DIR/data" \
    --web.console.templates="$(dirname "$PROMETHEUS_BIN")/consoles" \
    --web.console.libraries="$(dirname "$PROMETHEUS_BIN")/console_libraries" \
    --web.listen-address="0.0.0.0:$PROMETHEUS_PORT" \
    --web.enable-lifecycle \
    --log.level=warn &
PROM_PID=$!

# Start Grafana in background
cd "$GRAFANA_HOME"
"$GRAFANA_BIN" server \
    --homepath="$GRAFANA_HOME" \
    --config="$GRAFANA_DIR/grafana.ini" &
GRAFANA_PID=$!

echo "Monitoring stack running. Press Ctrl+C to stop."
echo ""

# Wait for processes
wait "$PROM_PID" "$GRAFANA_PID" 2>/dev/null || true

# If we get here, clean up
cleanup
