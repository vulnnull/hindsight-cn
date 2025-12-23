---
sidebar_position: 3
---

# Skills

Hindsight provides an Agent Skill that gives AI coding assistants persistent memory across sessions. Skills are reusable prompt templates that agents can load when needed to gain specialized capabilities.

## Supported Platforms

| Platform | Skills Directory |
|----------|-----------------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `~/.claude/skills/` |
| [OpenCode](https://github.com/opencode-ai/opencode) | `~/.opencode/skills/` |
| [Codex CLI](https://github.com/openai/codex) | `~/.codex/skills/` |

## Quick Install

```bash
curl -fsSL https://hindsight.vectorize.io/get-skill | bash
```

The installer will:
1. Prompt you to select your AI coding assistant
2. Run the LLM provider configuration
3. Install the skill to the appropriate directory

### Install for a Specific Platform

```bash
# Claude Code
curl -fsSL https://hindsight.vectorize.io/get-skill | bash -s -- --app claude

# OpenCode
curl -fsSL https://hindsight.vectorize.io/get-skill | bash -s -- --app opencode

# Codex CLI
curl -fsSL https://hindsight.vectorize.io/get-skill | bash -s -- --app codex
```

## What the Skill Provides

Once installed, your AI assistant gains the ability to:

- **Retain** - Store user preferences, learnings, and procedure outcomes
- **Recall** - Search for relevant context before starting tasks
- **Reflect** - Synthesize memories into contextual answers

The skill uses the `hindsight-embed` CLI which runs a lightweight local daemon with an embedded database.

## How Skills Work

Skills are **model-invoked**, meaning the AI assistant automatically decides when to use them based on the context of your conversation. You don't need to explicitly trigger the skill.

The assistant will:
- **Store** when you share preferences, when tasks succeed/fail, or when learnings emerge
- **Recall** before starting non-trivial tasks to get relevant context

### What Gets Stored

The skill is optimized to store:

| Category | Examples |
|----------|----------|
| **User Preferences** | Coding style, tool preferences, language choices |
| **Procedure Outcomes** | Commands that worked, configurations that resolved issues |
| **Learnings** | Bug solutions, workarounds, architecture decisions |

## Architecture

```
AI Coding Assistant
    │
    ▼
Hindsight Skill (SKILL.md)
    │
    ▼
hindsight-embed CLI
    │
    ▼
Local Daemon (auto-started)
    │
    ▼
Embedded PostgreSQL (~/.pg0/hindsight-embed/)
```

All data stays on your machine. The daemon auto-starts when needed and shuts down after inactivity.

## Configuration

The skill uses configuration stored in `~/.hindsight/config.env`. Reconfigure anytime:

```bash
uvx hindsight-embed configure
```

## Troubleshooting

### Skill not activating

The skill activates based on its description matching your request. Try being explicit:
- "Remember that..." triggers storage
- "What do you know about..." triggers recall

### Daemon issues

```bash
uvx hindsight-embed daemon status
uvx hindsight-embed daemon logs
```

### Reconfigure

```bash
uvx hindsight-embed configure
```

## Requirements

- Python 3.10+ (for `uvx`)
- An LLM API key (OpenAI, Anthropic, Groq, etc.)
