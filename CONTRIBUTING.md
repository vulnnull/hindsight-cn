# 贡献指南

感谢你对 Hindsight-CN 的关注！

## 快速开始

1. Fork 并克隆本仓库
   ```bash
   git clone https://github.com/vulnnull/hindsight-cn.git
   cd hindsight-cn
   ```

2. 配置环境：
   ```bash
   cp .env.example .env
   ```
   编辑 `.env` 文件，填入 LLM API 密钥和相关配置

3. 安装依赖：
   ```bash
   # Python 依赖
   uv sync --directory hindsight-api/

   # Node.js 依赖（使用 npm workspaces）
   npm install
   ```

## 本地开发

### 启动 API 服务

```bash
./scripts/dev/start-api.sh
```

### 启动控制面板

```bash
./scripts/dev/start-control-plane.sh
```

### 启动文档站

```bash
./scripts/dev/start-docs.sh
```

### 运行测试

```bash
cd hindsight-api
uv run pytest tests/
```

## 代码风格

Python 使用 [Ruff](https://docs.astral.sh/ruff/) 进行检查和格式化，TypeScript 使用 ESLint/Prettier。

### 配置 Git Hooks（推荐）

```bash
./scripts/setup-hooks.sh
```

这会配置 Git 在每次提交前自动运行 `.githooks/` 中的钩子脚本。Lint 钩子并行执行：
- **Python**：`ruff check --fix`、`ruff format`、`ty check`
- **TypeScript**：`eslint --fix`、`prettier`

### 手动检查和格式化

```bash
# 运行所有 lint（与 pre-commit 相同）
./scripts/hooks/lint.sh

# 或单独运行 Python 检查：
cd hindsight-api
uv run ruff check --fix .   # 检查并自动修复
uv run ruff format .        # 格式化代码
uv run ty check hindsight_api  # 类型检查
```

### 风格准则

- 使用 Python 类型注解
- 遵循现有代码模式
- 保持函数职责单一、命名清晰

## 提交 Pull Request

1. 从 `main` 创建功能分支
2. 进行修改
3. 运行测试确保无误
4. 提交 PR 并附上清晰的变更描述

## 报告问题

在 GitHub 上提交 Issue，包含以下信息：
- 问题描述
- 复现步骤
- 期望行为与实际行为
- 环境信息（操作系统、Python 版本等）

## 疑问？

在 GitHub 上发起 Discussion 或联系维护者。
