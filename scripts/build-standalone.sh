#!/bin/bash
set -e

# =============================================================================
# Hindsight-CN 独立发行包构建脚本（原生环境）
# =============================================================================
# 支持 Linux / macOS / Windows（Git Bash）
#
# 用法：
#   TARGET_PLATFORM=linux/amd64 VERSION=0.7.1 bash scripts/build-standalone.sh
# =============================================================================

VERSION="${VERSION:-0.0.0-dev}"
TARGET_PLATFORM="${TARGET_PLATFORM:-$(uname -s | tr '[:upper:]' '[:lower:]')/$(uname -m)}"
INCLUDE_MODELS="${INCLUDE_MODELS:-true}"
HF_ENDPOINT="${HF_ENDPOINT:-https://huggingface.co}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-BAAI/bge-small-zh-v1.5}"
RERANKER_MODEL="${RERANKER_MODEL:-cross-encoder/mmarco-mMiniLMv2-L12-H384-v1}"

# 解析平台
PLATFORM_OS="${TARGET_PLATFORM%%/*}"
PLATFORM_ARCH="${TARGET_PLATFORM##*/}"
case "$PLATFORM_ARCH" in
    x86_64|x64) PLATFORM_ARCH="amd64" ;;
    aarch64|arm64) PLATFORM_ARCH="arm64" ;;
esac

PKG_NAME="hindsight-cn-v${VERSION}-${PLATFORM_OS}-${PLATFORM_ARCH}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$SRC_DIR/dist/$PKG_NAME"

# Windows 兼容
IS_WINDOWS=false
if [[ "$PLATFORM_OS" == "windows" ]] || [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == MSYS* ]] || [[ "$(uname -s)" == CYGWIN* ]]; then
    IS_WINDOWS=true
fi

echo "============================================"
echo "构建 Hindsight-CN v${VERSION}"
echo "平台：${PLATFORM_OS}/${PLATFORM_ARCH}"
echo "包含模型：${INCLUDE_MODELS}"
echo "Windows：${IS_WINDOWS}"
echo "============================================"

# 检查工具
command -v python3 >/dev/null 2>&1 && PYTHON=python3 || PYTHON=python
command -v $PYTHON >/dev/null || { echo "❌ 需要 python"; exit 1; }
command -v node >/dev/null || { echo "❌ 需要 node"; exit 1; }

# 确保 uv 可用
if command -v uv >/dev/null; then
    UV="uv"
elif [ -f "$HOME/.local/bin/uv" ]; then
    UV="$HOME/.local/bin/uv"
elif [ -f "$LOCALAPPDATA/uv/uv.exe" ]; then
    UV="$LOCALAPPDATA/uv/uv.exe"
else
    echo "安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV="$HOME/.local/bin/uv"
fi

# 清理并创建构建目录
rm -rf "$SRC_DIR/dist/$PKG_NAME"
mkdir -p "$BUILD_DIR"

# =============================================================================
# 构建 API（Python venv）
# =============================================================================
echo ""
echo "📦 [1/4] 构建 API..."
API_DIR="$BUILD_DIR/hindsight-api"
cd "$SRC_DIR/hindsight-api-slim"

if [ "$IS_WINDOWS" = "true" ]; then
    # Windows: 使用 Scripts/ 而不是 bin/
    $UV venv "$API_DIR" --python 3.11
    $UV pip install --python "$API_DIR/Scripts/python.exe" ".[all]"
else
    $UV venv "$API_DIR" --python 3.11
    $UV pip install --python "$API_DIR/bin/python" ".[all]"
fi

echo "✅ API 构建完成"

# 预下载 tiktoken 编码（运行时必需）
PYTHON_BIN="$API_DIR/bin/python"
if [ "$IS_WINDOWS" = "true" ]; then
    PYTHON_BIN="$API_DIR/Scripts/python.exe"
fi
echo "  预下载 tiktoken 编码..."
"$PYTHON_BIN" -c "import tiktoken; tiktoken.get_encoding('cl100k_base')" 2>/dev/null || true

# =============================================================================
# 下载 ML 模型
# =============================================================================
if [ "$INCLUDE_MODELS" = "true" ]; then
    echo ""
    echo "🧠 [2/4] 下载 ML 模型..."
    MODELS_DIR="$BUILD_DIR/models"
    mkdir -p "$MODELS_DIR"
    export HF_HOME="$MODELS_DIR"

    PYTHON_BIN="$API_DIR/bin/python"
    if [ "$IS_WINDOWS" = "true" ]; then
        PYTHON_BIN="$API_DIR/Scripts/python.exe"
    fi

    for i in 1 2 3; do
        echo "  尝试 $i/3..."
        if "$PYTHON_BIN" -c "
import os
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'
os.environ['HF_ENDPOINT'] = '$HF_ENDPOINT'
from sentence_transformers import SentenceTransformer, CrossEncoder
print('  下载 Embedding 模型...')
SentenceTransformer('$EMBEDDING_MODEL', trust_remote_code=True)
print('  下载 Reranker 模型...')
CrossEncoder('$RERANKER_MODEL', trust_remote_code=True)
print('  模型下载完成')
"; then
            echo "✅ ML 模型下载完成"
            break
        fi
        if [ $i -lt 3 ]; then
            echo "  失败，10s 后重试..."
            sleep 10
        else
            echo "⚠️  模型下载失败，运行时将自动下载"
        fi
    done
else
    echo ""
    echo "⏭️  [2/4] 跳过 ML 模型下载"
fi

# =============================================================================
# 构建控制面板（Next.js standalone）
# =============================================================================
echo ""
echo "📦 [3/4] 构建控制面板..."
CP_DIR="$BUILD_DIR/control-plane"

# 从根目录安装 workspace 依赖（含 @vectorize-io/hindsight-client）
cd "$SRC_DIR"
if [ "$IS_WINDOWS" = "true" ]; then
    npm ci --quiet --ignore-scripts
else
    npm ci --quiet
fi

# 构建 TypeScript client（dist/ 被 .gitignore 忽略）
npm run build --workspace=hindsight-clients/typescript

# 修复跨平台原生模块（lightningcss/tailwindcss）
rm -rf node_modules/lightningcss node_modules/@tailwindcss 2>/dev/null || true
npm install lightningcss @tailwindcss/postcss @tailwindcss/node 2>/dev/null || true

cd "$SRC_DIR/hindsight-control-plane"
INCLUDE_CP=true npm run build

# npm run build 已执行 build:standalone，直接使用 standalone/ 目录
if [ ! -f standalone/server.js ]; then
    echo "❌ standalone 构建失败：找不到 standalone/server.js"
    exit 1
fi

cp -r standalone "$CP_DIR"

echo "✅ 控制面板构建完成"

# =============================================================================
# 打包
# =============================================================================
echo ""
echo "📋 [4/4] 打包..."

# 复制启动脚本和配置
if [ "$IS_WINDOWS" = "true" ]; then
    # Windows 用 .bat 启动脚本
    cat > "$BUILD_DIR/start.bat" << 'BATCH'
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM 加载配置文件
if exist "%~dp0hindsight.env" (
    echo ✅ 已加载配置文件 hindsight.env
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0hindsight.env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
) else if exist "%~dp0.env" (
    echo ✅ 已加载配置文件 .env
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
) else (
    echo ⚠️  未找到配置文件 hindsight.env
    echo    提示：copy hindsight.env.example hindsight.env ^& edit hindsight.env
)

REM 设置默认值
if "%HINDSIGHT_ENABLE_API%"=="" set HINDSIGHT_ENABLE_API=true
if "%HINDSIGHT_ENABLE_CP%"=="" set HINDSIGHT_ENABLE_CP=true
if "%HINDSIGHT_API_PORT%"=="" set HINDSIGHT_API_PORT=8888
if "%HINDSIGHT_CP_PORT%"=="" set HINDSIGHT_CP_PORT=9999
if "%HF_HOME%"=="" set HF_HOME=%~dp0models

echo.
echo ✅ Hindsight-CN 已启动！
echo.
echo 📍 访问地址：
echo    管理面板：http://localhost:%HINDSIGHT_CP_PORT%
echo    API 服务：http://localhost:%HINDSIGHT_API_PORT%
echo.

REM 启动 API
if "%HINDSIGHT_ENABLE_API%"=="true" (
    echo 🚀 正在启动 API 服务...
    start /b "" "%~dp0hindsight-api\Scripts\python.exe" -m hindsight_api.main
)

REM 启动控制面板
if "%HINDSIGHT_ENABLE_CP%"=="true" (
    echo 🎛️  正在启动控制面板...
    cd /d "%~dp0control-plane"
    set HOSTNAME=0.0.0.0
    start /b "" node server.js
)

REM 等待
echo.
echo 按 Ctrl+C 停止所有服务...
pause
BATCH
else
    cp "$SRC_DIR/scripts/start-standalone.sh" "$BUILD_DIR/start.sh"
    chmod +x "$BUILD_DIR/start.sh"
fi

cp "$SRC_DIR/hindsight.env.example" "$BUILD_DIR/hindsight.env.example"

cat > "$BUILD_DIR/README.txt" << EOF
Hindsight-CN v${VERSION} — AI 智能体长期记忆系统（中文优化版）
====================================================

快速开始：
  $(if [ "$IS_WINDOWS" = "true" ]; then echo "1. 复制配置文件：copy hindsight.env.example hindsight.env"; else echo "1. 复制配置文件：cp hindsight.env.example hindsight.env"; fi)
  2. 编辑 hindsight.env，填入 LLM API 密钥等配置
  $(if [ "$IS_WINDOWS" = "true" ]; then echo "3. 双击 start.bat 或在命令行运行 start.bat"; else echo "3. 启动服务：./start.sh"; fi)

访问地址：
  管理面板：http://localhost:\${HINDSIGHT_CP_PORT:-9999}
  API 服务：http://localhost:\${HINDSIGHT_API_PORT:-8888}

更多配置项请参考 hindsight.env.example 中的注释。
EOF

# 打包
cd "$SRC_DIR/dist"
if [ "$IS_WINDOWS" = "true" ]; then
    # Windows 用 zip
    if command -v zip >/dev/null; then
        zip -r -q "$SRC_DIR/${PKG_NAME}.zip" "$PKG_NAME"
        SIZE=$(du -sh "$SRC_DIR/${PKG_NAME}.zip" | cut -f1)
        echo ""
        echo "✅ 构建完成！"
        echo "   文件：${PKG_NAME}.zip（${SIZE}）"
    else
        # PowerShell fallback
        powershell -Command "Compress-Archive -Path '$PKG_NAME' -DestinationPath '$SRC_DIR/${PKG_NAME}.zip'"
        echo ""
        echo "✅ 构建完成！"
        echo "   文件：${PKG_NAME}.zip"
    fi
else
    tar czf "$SRC_DIR/${PKG_NAME}.tar.gz" "$PKG_NAME"
    SIZE=$(du -sh "$SRC_DIR/${PKG_NAME}.tar.gz" | cut -f1)
    echo ""
    echo "✅ 构建完成！"
    echo "   文件：${PKG_NAME}.tar.gz（${SIZE}）"
fi
echo "   路径：$SRC_DIR/"
