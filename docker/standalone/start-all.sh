#!/bin/bash
set -e

# =============================================================================
# 内嵌 pg0 数据完整性检查 (#675)
#
# 使用内嵌 pg0 时，在启动前检查数据目录是否包含有效的 PostgreSQL 数据。
# 如果目录存在但为空或损坏（缺少 PG_VERSION 文件），输出警告。
# 这有助于诊断容器重启导致数据目录被清空的问题。
# =============================================================================
PG0_DATA_DIR="${HOME}/.pg0"
if [ -d "$PG0_DATA_DIR" ]; then
    # 查找实际的 PostgreSQL 数据目录（pg0 为每个实例创建子目录）
    if compgen -G "$PG0_DATA_DIR"/*/PG_VERSION > /dev/null 2>&1; then
        echo "✅ 检测到已有的 pg0 数据目录：$PG0_DATA_DIR"
    elif [ "$(ls -A "$PG0_DATA_DIR" 2>/dev/null)" ]; then
        echo "⚠️  警告：pg0 数据目录存在（$PG0_DATA_DIR），但未找到 PG_VERSION 文件。"
        echo "   这可能意味着数据损坏或上次未正常关闭。"
        echo "   如果后续看到所有迁移从头开始运行，说明数据可能已丢失。"
        echo "   参见：https://github.com/vectorize-io/hindsight/issues/675"
    fi

    return 0
}

if [ "${HINDSIGHT_START_ALL_SOURCE_ONLY:-false}" = "true" ]; then
    return 0 2>/dev/null || exit 0
fi

# 服务开关（默认全部启用）
ENABLE_API="${HINDSIGHT_ENABLE_API:-true}"
ENABLE_CP="${HINDSIGHT_ENABLE_CP:-true}"

# =============================================================================
# 依赖等待（需设置 HINDSIGHT_WAIT_FOR_DEPS=true 启用）
#
# 使用 LM Studio 等本地 LLM 时，模型加载需要时间。
# 如果 Hindsight 在 LLM 就绪前启动，LLM 验证会失败。
# 此等待循环确保依赖服务就绪后再启动。
# =============================================================================
if [ "${HINDSIGHT_WAIT_FOR_DEPS:-false}" = "true" ]; then
    LLM_BASE_URL="${HINDSIGHT_API_LLM_BASE_URL:-http://host.docker.internal:1234/v1}"
    MAX_RETRIES="${HINDSIGHT_RETRY_MAX:-0}"  # 0 = 无限重试
    RETRY_INTERVAL="${HINDSIGHT_RETRY_INTERVAL:-10}"

    # 检查是否配置了外部数据库（内嵌 pg0 无需检查）
    SKIP_DB_CHECK=false
    if [ -z "${HINDSIGHT_API_DATABASE_URL}" ]; then
        SKIP_DB_CHECK=true
    else
        DB_CHECK_HOST=$(echo "$HINDSIGHT_API_DATABASE_URL" | sed -E 's|.*@([^:/]+):([0-9]+)/.*|\1 \2|')
    fi

    check_db() {
        if $SKIP_DB_CHECK; then
            return 0
        fi
        if command -v pg_isready &> /dev/null; then
            pg_isready -h $(echo $DB_CHECK_HOST | cut -d' ' -f1) -p $(echo $DB_CHECK_HOST | cut -d' ' -f2) &>/dev/null
        else
            python3 -c "import socket; s=socket.socket(); s.settimeout(5); exit(0 if s.connect_ex(('$(echo $DB_CHECK_HOST | cut -d' ' -f1)', $(echo $DB_CHECK_HOST | cut -d' ' -f2))) == 0 else 1)" 2>/dev/null
        fi
    }

    check_llm() {
        curl -sf "${LLM_BASE_URL}/models" --connect-timeout 5 &>/dev/null
    }

    echo "⏳ 等待依赖服务就绪..."
    attempt=1

    while true; do
        db_ok=false
        llm_ok=false

        if check_db; then
            db_ok=true
        fi

        if check_llm; then
            llm_ok=true
        fi

        if $db_ok && $llm_ok; then
            echo "✅ 依赖服务就绪！"
            break
        fi

        if [ "$MAX_RETRIES" -ne 0 ] && [ "$attempt" -ge "$MAX_RETRIES" ]; then
            echo "❌ 已达最大重试次数（$MAX_RETRIES），依赖服务不可用。"
            exit 1
        fi

        echo "   第 $attempt 次尝试：数据库=$( $db_ok && echo '就绪' || echo '等待中' )，LLM=$( $llm_ok && echo '就绪' || echo '等待中' )"
        sleep "$RETRY_INTERVAL"
        ((attempt++))
    done
fi

# =============================================================================
# 优雅关闭处理 (#675)
#
# Docker 在执行 docker stop/docker restart 时发送 SIGTERM。
# 如果不设置 trap，子进程（hindsight-api + pg0、控制面板）会被强制终止。
# 对内嵌的 pg0 数据库来说，这可能导致 Docker 卷重新挂载后的数据丢失。
#
# 此 trap 将 SIGTERM 转发给所有子进程，确保：
#   - hindsight-api 执行自己的关闭钩子
#   - pg0 执行干净的 PostgreSQL 关闭（checkpoint + WAL 刷盘）
#   - 控制面板 Node.js 进程正常退出
# =============================================================================
# 防止并发清理（例如子进程崩溃和 SIGTERM 同时到达）
SHUTTING_DOWN=false

cleanup() {
    if $SHUTTING_DOWN; then return; fi
    SHUTTING_DOWN=true

    echo ""
    echo "🛑 收到关闭信号，正在优雅停止服务..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    # 等待进程干净关闭（pg0 需要刷盘 WAL）
    # 注意：Docker 默认 stop_grace_period 为 10 秒。
    # 请在 compose 文件中设置 stop_grace_period: 30s，或使用 docker stop -t 30，
    # 否则 Docker 会在超时后发送 SIGKILL 强制终止。
    local timeout=30
    for ((i=1; i<=timeout; i++)); do
        local all_stopped=true
        for pid in "${PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                all_stopped=false
                break
            fi
        done
        if $all_stopped; then
            echo "✅ 所有服务已正常停止"
            exit 0
        fi
        sleep 1
    done
    # 超时后强制终止
    echo "⚠️  等待超时，强制关闭..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
    done
    exit 1
}
trap cleanup SIGTERM SIGINT

# 跟踪子进程 PID
PIDS=()

# 启动 API 服务
if [ "$ENABLE_API" = "true" ]; then
    cd /app/api
    API_HEALTH_URL="${HINDSIGHT_API_HEALTH_URL:-http://localhost:${HINDSIGHT_API_PORT:-8888}/health}"
    API_STARTUP_WAIT_SECONDS="${HINDSIGHT_API_STARTUP_WAIT_SECONDS:-300}"

    # 直接运行 API，Python 的 PYTHONUNBUFFERED=1 负责处理输出缓冲
    hindsight-api &
    API_PID=$!
    PIDS+=($API_PID)

    # 等待 API 就绪
    api_ready=false
    for ((i=1; i<=API_STARTUP_WAIT_SECONDS; i++)); do
        if ! kill -0 "$API_PID" 2>/dev/null; then
            wait "$API_PID"
            exit $?
        fi
        if curl -sf "$API_HEALTH_URL" &>/dev/null; then
            api_ready=true
            break
        fi
        sleep 1
    done

    if [ "$api_ready" != "true" ]; then
        echo "❌ API 在 ${API_STARTUP_WAIT_SECONDS}s 内未就绪"
        exit 1
    fi
else
    echo "API 已禁用（HINDSIGHT_ENABLE_API=false）"
fi

# 启动控制面板
if [ "$ENABLE_CP" = "true" ]; then
    echo "🎛️  正在启动控制面板..."
    cd /app/control-plane
    export HOSTNAME="${HINDSIGHT_CP_HOSTNAME:-0.0.0.0}"
    PORT="${HINDSIGHT_CP_PORT:-9999}" node server.js &
    CP_PID=$!
    PIDS+=($CP_PID)
else
    echo "控制面板已禁用（HINDSIGHT_ENABLE_CP=false）"
fi

# 打印状态
echo ""
echo "✅ Hindsight-CN 已启动！"
echo ""
echo "📍 访问地址："
if [ "$ENABLE_CP" = "true" ]; then
    echo "   管理面板：http://localhost:${HINDSIGHT_CP_PORT:-9999}"
fi
if [ "$ENABLE_API" = "true" ]; then
    echo "   API 服务：http://localhost:8888"
fi
echo ""

# 检查是否有服务在运行
if [ ${#PIDS[@]} -eq 0 ]; then
    echo "❌ 未启用任何服务！请设置 HINDSIGHT_ENABLE_API=true 或 HINDSIGHT_ENABLE_CP=true"
    exit 1
fi

# 等待任意子进程退出
while true; do
    # wait -n 在任意子进程退出或信号到达时返回
    # trap 处理器会执行并退出，此循环仅用于健壮性保障
    # `&& true` 防止 set -e 在 wait -n 返回非零时终止脚本
    wait -n && true
    # 检查已跟踪的 PID 是否退出
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null
            exit_code=$?
            echo "⚠️  服务（PID $pid）已退出，退出码：$exit_code"
            # 触发剩余服务的清理
            cleanup
        fi
    done
done
