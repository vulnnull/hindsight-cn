# Configuration

Complete reference for configuring Hindsight server through environment variables and configuration files.

## Environment Variables

Hindsight is configured entirely through environment variables, making it easy to deploy across different environments and container orchestration platforms.

### LLM Provider Configuration

Configure the LLM provider used for fact extraction, entity resolution, and reasoning operations.

#### Common LLM Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_LLM_PROVIDER` | LLM provider: `groq`, `openai`, `ollama` | `groq` | Yes |
| `HINDSIGHT_API_LLM_API_KEY` | API key for LLM provider | - | Yes (except ollama) |
| `HINDSIGHT_API_LLM_MODEL` | Model name | Provider-specific | No |
| `HINDSIGHT_API_LLM_BASE_URL` | Custom LLM endpoint | Provider default | No |

#### Provider-Specific Examples

**Groq (Recommended for Fast Inference)**

```bash
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-20b
```

**OpenAI**

```bash
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_API_KEY=sk-xxxxxxxxxxxx
export HINDSIGHT_API_LLM_MODEL=gpt-4o
```

**Ollama (Local, No API Key)**

```bash
export HINDSIGHT_API_LLM_PROVIDER=ollama
export HINDSIGHT_API_LLM_BASE_URL=http://localhost:11434/v1
export HINDSIGHT_API_LLM_MODEL=llama3.1
```

**OpenAI-Compatible Endpoints**

```bash
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_BASE_URL=https://your-endpoint.com/v1
export HINDSIGHT_API_LLM_API_KEY=your-api-key
export HINDSIGHT_API_LLM_MODEL=your-model-name
```

### Database Configuration

Configure the PostgreSQL database connection and behavior.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_DATABASE_URL` | PostgreSQL connection string | - | Yes* |

**\*Note**: If `DATABASE_URL` is not provided, the server will use embedded `pg0` (embedded PostGRE).

### MCP Server Configuration

Configure the Model Context Protocol (MCP) server for AI assistant integrations.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HINDSIGHT_API_MCP_ENABLED` | Enable MCP server | `true` | No |

```bash
# Enable MCP server (default)
export HINDSIGHT_API_MCP_ENABLED=true

# Disable MCP server
export HINDSIGHT_API_MCP_ENABLED=false
```

## Configuration Files

### .env File

The Hindisight API will look for a `.env` file:

```bash
# .env

HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight_dev@localhost:5432/hindsight

HINDSIGHT_API_LLM_PROVIDER=groq
HINDSIGHT_API_LLM_API_KEY=gsk_xxxxxxxxxxxx
```

---

For configuration issues not covered here, please [open an issue](https://github.com/your-repo/hindsight/issues) on GitHub.
