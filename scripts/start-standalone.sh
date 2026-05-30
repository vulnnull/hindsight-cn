#!/bin/bash
set -e

# =============================================================================
# Hindsight-CN 启动脚本
# =============================================================================
# 使用方式：
#   1. 复制 hindsight.env.example 为 hindsight.env 并编辑配置
#   2. 运行 ./start.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载配置文件
if [ -f "$SCRIPT_DIR/hindsight.env" ]; then
    set -a
    source "$SCRIPT_DIR/hindsight.env"
    set +a
    echo "✅ 已加载配置文件 hindsight.env"
elif [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✅ 已加载配置文件 .env"
else
    echo "⚠️  未找到配置文件 hindsight.env，将使用环境变量或默认值"
    echo "   提示：cp hindsight.env.example hindsight.env && vim hindsight.env"
fi

# 服务开关
ENABLE_API="${HINDSIGHT_ENABLE_API:-true}"
ENABLE_CP="${HINDSIGHT_ENABLE_CP:-true}"

# 检测平台
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
esac

# pg0 数据目录
export HOME="${HOME:-$SCRIPT_DIR}"
PG0_DATA_DIR="${HOME}/.pg0"
if [ -d "$PG0_DATA_DIR" ]; then
    if compgen -G "$PG0_DATA_DIR"/*/PG_VERSION > /dev/null 2>&1; then
        echo "✅ 检测到已有的 pg0 数据目录：$PG0_DATA_DIR"
    elif [ "$(ls -A "$PG0_DATA_DIR" 2>/dev/null)" ]; then
        echo "⚠️  警告：pg0 数据目录存在但数据可能损坏"
    fi
fi

# =============================================================================
# 依赖等待
# =============================================================================
if [ "${HINDSIGHT_WAIT_FOR_DEPS:-false}" = "true" ]; then
    LLM_BASE_URL="${HINDSIGHT_API_LLM_BASE_URL:-http://localhost:1234/v1}"
    MAX_RETRIES="${HINDSIGHT_RETRY_MAX:-30}"
    RETRY_INTERVAL="${HINDSIGHT_RETRY_INTERVAL:-10}"

    check_db() {
        if [ -z "${HINDSIGHT_API_DATABASE_URL}" ]; then return 0; fi
        local host=$(echo "$HINDSIGHT_API_DATABASE_URL" | sed -E 's|.*@([^:/]+):[0-9]+/.*|\1|')
        local port=$(echo "$HINDSIGHT_API_DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
        python3 -c "import socket; s=socket.socket(); s.settimeout(5); exit(0 if s.connect_ex(('$host', $port)) == 0 else 1)" 2>/dev/null
    }

    check_llm() {
        curl -sf "${LLM_BASE_URL}/models" --connect-timeout 5 &>/dev/null
    }

    echo "⏳ 等待依赖服务就绪..."
    attempt=1
    while true; do
        db_ok=false; llm_ok=false
        check_db && db_ok=true
        check_llm && llm_ok=true
        if $db_ok && $llm_ok; then echo "✅ 依赖服务就绪！"; break; fi
        if [ "$MAX_RETRIES" -ne 0 ] && [ "$attempt" -ge "$MAX_RETRIES" ]; then
            echo "❌ 已达最大重试次数，依赖服务不可用"; exit 1
        fi
        echo "   第 $attempt 次尝试：数据库=$($db_ok && echo '就绪' || echo '等待中')，LLM=$($llm_ok && echo '就绪' || echo '等待中')"
        sleep "$RETRY_INTERVAL"
        ((attempt++))
    done
fi

# =============================================================================
# 优雅关闭
# =============================================================================
SHUTTING_DOWN=false
PIDS=()

cleanup() {
    if $SHUTTING_DOWN; then return; fi
    SHUTTING_DOWN=true
    echo ""
    echo "🛑 收到关闭信号，正在优雅停止服务..."
    for pid in "${PIDS[@]}"; do
        kill -0 "$pid" 2>/dev/null && kill -TERM "$pid" 2>/dev/null
    done
    for ((i=1; i<=30; i++)); do
        all_stopped=true
        for pid in "${PIDS[@]}"; do
            kill -0 "$pid" 2>/dev/null && { all_stopped=false; break; }
        done
        $all_stopped && echo "✅ 所有服务已正常停止" && exit 0
        sleep 1
    done
    echo "⚠️  等待超时，强制关闭..."
    for pid in "${PIDS[@]}"; do kill -9 "$pid" 2>/dev/null; done
    exit 1
}
trap cleanup SIGTERM SIGINT

# =============================================================================
# 启动 API 服务
# =============================================================================
if [ "$ENABLE_API" = "true" ]; then
    API_DIR="$SCRIPT_DIR/hindsight-api"
    API_HEALTH_URL="http://localhost:${HINDSIGHT_API_PORT:-8888}/health"
    API_STARTUP_WAIT="${HINDSIGHT_API_STARTUP_WAIT_SECONDS:-300}"

    if [ ! -d "$API_DIR" ]; then
        echo "❌ API 目录不存在：$API_DIR"
        echo "   请确认 hindsight-api/ 目录完整"
        exit 1
    fi

    cd "$API_DIR"
    # 设置模型缓存目录
    export HF_HOME="${HF_HOME:-$SCRIPT_DIR/models}"

    echo "🚀 正在启动 API 服务..."
    bin/hindsight-api &
    API_PID=$!
    PIDS+=($API_PID)

    # 等待 API 就绪
    api_ready=false
    for ((i=1; i<=API_STARTUP_WAIT; i++)); do
        if ! kill -0 "$API_PID" 2>/dev/null; then
            wait "$API_PID"; exit $?
        fi
        if curl -sf "$API_HEALTH_URL" &>/dev/null; then
            api_ready=true; break
        fi
        sleep 1
    done

    if [ "$api_ready" != "true" ]; then
        echo "❌ API 在 ${API_STARTUP_WAIT}s 内未就绪"
        exit 1
    fi
    echo "✅ API 服务已就绪"
else
    echo "📋 API 已禁用（HINDSIGHT_ENABLE_API=false）"
fi

# =============================================================================
# 启动控制面板
# =============================================================================
if [ "$ENABLE_CP" = "true" ]; then
    CP_DIR="$SCRIPT_DIR/control-plane"

    if [ ! -d "$CP_DIR" ]; then
        echo "❌ 控制面板目录不存在：$CP_DIR"
        echo "   请确认 control-plane/ 目录完整"
        exit 1
    fi

    cd "$CP_DIR"
    export HOSTNAME="${HINDSIGHT_CP_HOSTNAME:-0.0.0.0}"
    export PORT="${HINDSIGHT_CP_PORT:-9999}"

    echo "🎛️  正在启动控制面板..."
    node server.js &
    CP_PID=$!
    PIDS+=($CP_PID)
    echo "✅ 控制面板已启动"
else
    echo "📋 控制面板已禁用（HINDSIGHT_ENABLE_CP=false）"
fi

# =============================================================================
# 打印状态
# =============================================================================
echo ""
echo "✅ Hindsight-CN 已启动！"
echo ""
echo "📍 访问地址："
if [ "$ENABLE_CP" = "true" ]; then
    echo "   管理面板：http://localhost:${HINDSIGHT_CP_PORT:-9999}"
fi
if [ "$ENABLE_API" = "true" ]; then
    echo "   API 服务：http://localhost:${HINDSIGHT_API_PORT:-8888}"
fi
echo ""

if [ ${#PIDS[@]} -eq 0 ]; then
    echo "❌ 未启用任何服务！请设置 HINDSIGHT_ENABLE_API=true 或 HINDSIGHT_ENABLE_CP=true"
    exit 1
fi

# 等待任意子进程退出
while true; do
    wait -n && true
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null
            echo "⚠️  服务（PID $pid）已退出，退出码：$?"
            cleanup
        fi
    done
done
