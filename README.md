<div align="center">

# Hindsight-CN

**AI 智能体长期记忆系统 · 中文优化版**

[![CI](https://github.com/vectorize-io/hindsight/actions/workflows/release.yml/badge.svg)](https://github.com/vectorize-io/hindsight/actions/workflows/release.yml)
[![许可证: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

让 AI 拥有像人类一样的工作记忆——不只是记住对话，而是真正**学习**和**成长**。

</div>

---

## 特性

- **中文优化** — 内嵌 `BAAI/bge-small-zh-v1.5` 中文 Embedding + `mmarco-mMiniLMv2` 多语言 Reranker
- **轻量高效** — 模型总占用约 550MB，NAS 等低性能设备也可流畅运行
- **全架构支持** — `linux/arm64` + `linux/amd64` 双架构镜像
- **开箱即用** — 模型内嵌镜像，无需联网下载，离线环境可用
- **Web 管理界面** — 全中文控制面板，可视化管理记忆库
- **自动同步上游** — 定时合并 [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) 更新

## 快速开始

### 一行命令启动

```bash
docker run --rm -it -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=你的API密钥 \
  -e HINDSIGHT_API_LLM_MODEL=MiniMax-M2.7 \
  -e HINDSIGHT_API_LLM_BASE_URL=https://api.minimaxi.com/v1 \
  -v hindsight-data:/home/hindsight/.pg0 \
  transnull/hindsight-cn:latest
```

| 服务 | 地址 |
|------|------|
| API | http://localhost:8888 |
| 管理面板 | http://localhost:9999/dashboard |

### Docker Compose

```bash
git clone https://github.com/vulnnull/hindsight-cn.git
cd hindsight-cn
cp .env.example .env   # 编辑填入 LLM 配置
docker compose up -d
```

### 支持的 LLM 提供商

| 提供商 | provider | 示例模型 |
|--------|----------|---------|
| OpenAI | `openai` | gpt-4o-mini |
| MiniMax | `openai` | MiniMax-M2.7 |
| DeepSeek | `deepseek` | deepseek-v4-flash |
| 智谱 AI | `zai` | glm-4.5-flash |
| Anthropic | `anthropic` | claude-sonnet-4-20250514 |
| Google Gemini | `gemini` | gemini-2.0-flash |
| Ollama / LM Studio | `ollama` | qwen3:8b |
| LiteLLM 代理 | `litellm` | 任意 |

## 记忆类型

Hindsight 模拟人类记忆的工作方式，将信息组织为四种类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| **世界常识** | 普遍知识 | "Python 是 Guido van Rossum 创建的" |
| **交互记录** | 个人经历 | "用户上周去了北京出差" |
| **观察** | 即时观察 | 从对话中提取的即时信息 |
| **思维模型** | 认知理解 | "用户偏好函数式编程风格" |

所有记忆存储在隔离的**记忆库**（Bank）中，每个智能体拥有独立的"大脑"。

---

## 智能体接入

Hindsight-CN 为 AI 智能体提供长期记忆能力——自动存储对话、智能检索历史上下文。以下展示三种主流智能体的接入方式。

### OpenClaw

通过官方插件一键接入，支持自动存储/检索、按智能体/频道/用户隔离记忆库。

```bash
# 1. 安装插件
openclaw plugins install @vectorize-io/hindsight-openclaw

# 2. 交互式配置（选择「外部 API」模式）
npx --package @vectorize-io/hindsight-openclaw hindsight-openclaw-setup
```

配置指向本地 Hindsight-CN 实例（`~/.openclaw/openclaw.json`）：

```json
{
  "plugins": {
    "entries": {
      "hindsight-openclaw": {
        "enabled": true,
        "config": {
          "hindsightApiUrl": "http://localhost:8888",
          "dynamicBankGranularity": ["agent", "channel", "user"],
          "autoRecall": true,
          "autoRetain": true
        }
      }
    }
  }
}
```

### Hermes Agent

Hermes 原生支持 Hindsight 作为记忆提供商，支持三种记忆模式。

```bash
# 1. 一行配置
hermes memory setup    # 选择「hindsight」

# 2. 禁用 Hermes 内置记忆工具（避免冲突）
hermes tools disable memory
```

手动配置指向本地 Hindsight-CN（`~/.hermes/hindsight/config.json`）：

```json
{
  "mode": "local_external",
  "api_url": "http://localhost:8888",
  "bank_id": "hermes",
  "memory_mode": "hybrid",
  "auto_recall": true,
  "auto_retain": true
}
```

| 模式 | 说明 |
|------|------|
| `hybrid`（推荐） | 自动注入记忆 + 手动工具并存 |
| `context` | 仅自动注入，不暴露工具给模型 |
| `tools` | 仅手动工具，模型自行决定何时检索 |

### Claude Code

通过 MCP 协议接入，支持 Hooks 自动存储/检索 + MCP 工具手动操作。

```bash
# 方式一：安装官方插件
claude plugin marketplace add vectorize-io/hindsight
claude plugin install hindsight-memory

# 方式二：手动配置 MCP 连接
claude mcp add --transport http hindsight http://localhost:8888/mcp
```

连接后可使用 `agent_knowledge_*` 系列工具管理记忆：

```bash
# 在 Claude Code 对话中使用
> 使用 agent_knowledge_recall 搜索"张三的技术方向"
> 使用 agent_knowledge_ingest 存储"项目使用 Vue 3 + TypeScript 技术栈"
```

---

## 中文模型配置

镜像默认内嵌以下轻量中文优化模型，总占用约 **550MB**：

| 组件 | 模型 | 维度 | 大小 | 特点 |
|------|------|------|------|------|
| Embedding | `BAAI/bge-small-zh-v1.5` | 512 | ~100MB | 中文专用，轻量高效 |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | — | ~450MB | 多语言（含中文），基于 MMARCO 训练 |

### 自定义模型

**构建时替换**（需重新构建镜像）：

```bash
# 英文版
docker build \
  --build-arg EMBEDDING_MODEL="BAAI/bge-small-en-v1.5" \
  --build-arg RERANKER_MODEL="cross-encoder/ms-marco-MiniLM-L-6-v2" \
  -t my-hindsight .

# 高质量中文版（需要更多资源）
docker build \
  --build-arg EMBEDDING_MODEL="BAAI/bge-m3" \
  --build-arg RERANKER_MODEL="BAAI/bge-reranker-v2-m3" \
  -t my-hindsight .
```

**运行时覆盖**（无需重新构建）：

```yaml
environment:
  - HINDSIGHT_API_EMBEDDINGS_PROVIDER=openai         # 改用远程 Embedding
  - HINDSIGHT_API_EMBEDDINGS_OPENAI_MODEL=text-embedding-3-small
  - HINDSIGHT_API_RERANKER_PROVIDER=none             # 关闭 Reranker
```

### 模型选型参考

| Embedding 模型 | 大小 | 维度 | 适用场景 |
|----------------|------|------|---------|
| `BAAI/bge-small-zh-v1.5` | ~100MB | 512 | 中文专用，轻量推荐 |
| `BAAI/bge-m3` | ~560MB | 1024 | 多语言，中文效果最好 |
| `BAAI/bge-small-en-v1.5` | ~80MB | 384 | 英文专用，原版默认 |

| Reranker 模型 | 大小 | 适用场景 |
|---------------|------|---------|
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | ~450MB | 多语言（含中文），推荐 |
| `BAAI/bge-reranker-v2-m3` | ~568MB | 高质量中文，需要更多资源 |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | ~80MB | 英文专用，原版默认 |

## 架构

![架构概览](./hindsight-docs/static/img/hindsight-overview.webp)

### 三大核心操作

| 操作 | 说明 |
|------|------|
| **Retain（存储）** | 存入信息，LLM 自动提取事实、实体和关系 |
| **Recall（检索）** | 四路并行搜索（语义 + 关键词 + 图谱 + 时间），经重排序后返回最相关结果 |
| **Reflect（反思）** | 基于记忆库生成带情境感知的深度分析 |

---

## 与原版的区别

| 特性 | 原版 (vectorize-io) | 中文版 (vulnnull) |
|------|--------------------|--------------------|
| UI 语言 | 英文 | 中文 |
| Embedding | `bge-small-en-v1.5`（英文，384维） | `bge-small-zh-v1.5`（中文，512维） |
| Reranker | `ms-marco-MiniLM-L-6-v2`（英文） | `mmarco-mMiniLMv2`（多语言含中文） |
| 模型总大小 | ~160MB | ~550MB |
| 镜像架构 | amd64 | arm64 + amd64 |
| LLM 适配 | OpenAI 为主 | 额外支持 MiniMax、DeepSeek、智谱 |
| HuggingFace | 默认源 | 支持 `hf-mirror.com` 镜像 |

## 上游同步

本仓库通过 GitHub Actions 每日自动同步 [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) 上游更新，同时保留所有中文汉化内容。合并冲突时自动优先使用本地版本。

## 资源

- [官方文档](https://hindsight.vectorize.io)
- [论文](https://arxiv.org/abs/2512.12818)
- [Python SDK](http://hindsight.vectorize.io/sdks/python) · [Node.js SDK](http://hindsight.vectorize.io/sdks/nodejs) · [CLI](https://hindsight.vectorize.io/sdks/cli)
- [Slack 社区](https://join.slack.com/t/hindsight-space/shared_invite/zt-3nhbm4w29-LeSJ5Ixi6j8PdiYOCPlOgg)

## 贡献

欢迎提交 Issue 和 Pull Request。详见 [贡献指南](./CONTRIBUTING.md)。

## 许可证

MIT 协议 — 参见 [LICENSE](./LICENSE)

---

原版由 [Vectorize.io](https://vectorize.io) 构建 · 中文版由 [vulnnull](https://github.com/vulnnull) 维护 · [Linux DO 社区](https://linux.do/)
