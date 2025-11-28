#!/bin/bash
set -e

# Script to download and start Prometheus for Hindsight metrics
# This creates a local Prometheus instance that scrapes metrics from the Hindsight API

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMETHEUS_DIR="$PROJECT_ROOT/.prometheus"
PROMETHEUS_VERSION="2.48.0"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$OS" in
    darwin)
        OS_NAME="darwin"
        ;;
    linux)
        OS_NAME="linux"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

case "$ARCH" in
    x86_64)
        ARCH_NAME="amd64"
        ;;
    arm64|aarch64)
        ARCH_NAME="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

PROMETHEUS_ARCHIVE="prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}.tar.gz"
PROMETHEUS_URL="https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/${PROMETHEUS_ARCHIVE}"
PROMETHEUS_BIN="$PROMETHEUS_DIR/prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}/prometheus"

echo "🔧 Setting up Prometheus for Hindsight metrics..."
echo ""

# Create prometheus directory
mkdir -p "$PROMETHEUS_DIR"
cd "$PROMETHEUS_DIR"

# Download Prometheus if not exists
if [ ! -f "$PROMETHEUS_BIN" ]; then
    echo "📥 Downloading Prometheus ${PROMETHEUS_VERSION} for ${OS_NAME}-${ARCH_NAME}..."
    curl -L -o "$PROMETHEUS_ARCHIVE" "$PROMETHEUS_URL"

    echo "📦 Extracting..."
    tar xzf "$PROMETHEUS_ARCHIVE"

    echo "✅ Prometheus downloaded successfully"
    echo ""
else
    echo "✅ Prometheus already downloaded"
    echo ""
fi

# Create prometheus.yml configuration
echo "📝 Creating Prometheus configuration..."
cat > "$PROMETHEUS_DIR/prometheus.yml" <<EOF
# Prometheus configuration for Hindsight API metrics
global:
  scrape_interval: 15s      # Scrape metrics every 15 seconds
  evaluation_interval: 15s  # Evaluate rules every 15 seconds

# Scrape configuration
scrape_configs:
  - job_name: 'hindsight-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']  # Hindsight API endpoint
    metrics_path: '/metrics'         # Metrics endpoint path

    # Optional: Add labels to all metrics from this job
    # relabeling_configs:
    #   - source_labels: [__address__]
    #     target_label: instance
    #     replacement: 'hindsight-api'
EOF

echo "✅ Configuration created at $PROMETHEUS_DIR/prometheus.yml"
echo ""

# Check if Hindsight API is running
echo "🔍 Checking if Hindsight API is running..."
if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
    echo "✅ Hindsight API is running and serving metrics"
    echo ""
else
    echo "⚠️  WARNING: Hindsight API is not reachable at http://localhost:8000/metrics"
    echo "   Make sure to start the API before Prometheus can scrape metrics"
    echo ""
fi

# Start Prometheus
echo "🚀 Starting Prometheus..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Prometheus UI:  http://localhost:9090"
echo "  Metrics source: http://localhost:8000/metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Example queries to try in the UI:"
echo ""
echo "  p95 latency (all operations):"
echo "    histogram_quantile(0.95, rate(hindsight_operation_duration_seconds_bucket[5m]))"
echo ""
echo "  p95 latency by bank:"
echo "    histogram_quantile(0.95, sum by (bank_id, le) (rate(hindsight_operation_duration_seconds_bucket{operation=\"recall\"}[5m])))"
echo ""
echo "  Operations per second:"
echo "    rate(hindsight_operation_total[5m])"
echo ""
echo "  Token usage rate:"
echo "    rate(hindsight_tokens_input_total[5m]) + rate(hindsight_tokens_output_total[5m])"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop Prometheus"
echo ""

# Start Prometheus with config
cd "$(dirname "$PROMETHEUS_BIN")"
exec "$PROMETHEUS_BIN" \
    --config.file="$PROMETHEUS_DIR/prometheus.yml" \
    --storage.tsdb.path="$PROMETHEUS_DIR/data" \
    --web.console.templates="$PROMETHEUS_DIR/prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}/consoles" \
    --web.console.libraries="$PROMETHEUS_DIR/prometheus-${PROMETHEUS_VERSION}.${OS_NAME}-${ARCH_NAME}/console_libraries"
