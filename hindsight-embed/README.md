# hindsight-embed

Hindsight embedded CLI - local memory operations without a server.

This package provides a simple CLI for storing and recalling memories using Hindsight's memory engine with an embedded PostgreSQL database (pg0). No external server or database setup required.

## Installation

```bash
pip install hindsight-embed
# or with uvx (no install needed)
uvx hindsight-embed --help
```

## Quick Start

```bash
# Set your LLM API key
export OPENAI_API_KEY=sk-...

# Store a memory
hindsight-embed retain "User prefers dark mode"

# Recall memories
hindsight-embed recall "What are user preferences?"
```

## Commands

### retain

Store a memory:

```bash
hindsight-embed retain "User prefers dark mode"
hindsight-embed retain "Meeting on Monday" --context work
```

### recall

Search memories:

```bash
hindsight-embed recall "user preferences"
hindsight-embed recall "upcoming events" --budget high
hindsight-embed recall "project details" -v  # verbose output
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_EMBED_LLM_API_KEY` | LLM API key (or use `OPENAI_API_KEY`) | Required |
| `HINDSIGHT_EMBED_LLM_PROVIDER` | LLM provider (`openai`, `anthropic`, `google`, `ollama`) | `openai` |
| `HINDSIGHT_EMBED_LLM_MODEL` | LLM model | `gpt-4o-mini` |
| `HINDSIGHT_EMBED_BANK_ID` | Memory bank ID | `default` |

## Use with AI Coding Assistants

This CLI is designed to work with AI coding assistants like Claude Code, OpenCode, and Codex CLI. Install the Hindsight skill:

```bash
curl -fsSL https://hindsight.vectorize.io/get-skill | bash
```

This will configure the LLM provider and install the skill to your assistant's skills directory.

## License

Apache 2.0
