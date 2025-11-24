---
sidebar_position: 3
---

# CLI Reference

The Memora CLI provides command-line access to memory operations and agent management.

## Installation

### Pre-built Binaries

Download from the releases page:

```bash
# macOS (Apple Silicon)
curl -L https://github.com/memora/memora/releases/latest/download/memora-macos-arm64 -o memora
chmod +x memora
sudo mv memora /usr/local/bin/
```

### Build from Source

```bash
cd memora-cli-rust
cargo build --release
cp target/release/memora /usr/local/bin/
```

## Configuration

Set environment variables or use command flags:

```bash
export MEMORA_API_URL=http://localhost:8080
export MEMORA_AGENT_ID=my-agent
```

## Commands

### Memory Operations

#### put

Store a memory:

```bash
memora put <agent_id> "Alice works at Google as a software engineer"

# With context
memora put <agent_id> "Bob loves hiking" --context "hobby discussion"

# With event date
memora put <agent_id> "Meeting with Carol" --date "2024-01-15"
```

#### put-files

Store file contents as memories:

```bash
# Store a single file
memora put-files <agent_id> notes.txt

# Store multiple files
memora put-files <agent_id> file1.txt file2.md file3.json

# With context
memora put-files <agent_id> meeting-notes.txt --context "team meeting"
```

#### search

Search memories:

```bash
memora search <agent_id> "What does Alice do?"

# With options
memora search <agent_id> "hiking recommendations" --budget 100 --top-k 5

# Verbose output
memora search <agent_id> "query" -v
```

#### think

Generate a response using memories and opinions:

```bash
memora think <agent_id> "What do you know about Alice?"

# Verbose mode shows reasoning
memora think <agent_id> "Should I recommend Python or Java?" -v
```

### Agent Management

#### agents

List all agents:

```bash
memora agents
```

Output:

```
Available agents:
  - alice-agent
  - bob-agent
  - tech-advisor
```

#### profile

View agent profile:

```bash
memora profile <agent_id>
```

Output:

```
Agent: my-agent

Personality:
  Openness:          0.80
  Conscientiousness: 0.60
  Extraversion:      0.50
  Agreeableness:     0.70
  Neuroticism:       0.30
  Bias Strength:     0.70

Background:
  I am a helpful AI assistant interested in technology.
```

#### set-personality

Update personality traits:

```bash
memora set-personality <agent_id> \
  --openness 0.8 \
  --conscientiousness 0.6 \
  --extraversion 0.5 \
  --agreeableness 0.7 \
  --neuroticism 0.3 \
  --bias-strength 0.7
```

#### background

Add or merge background:

```bash
# Set/merge background
memora background <agent_id> "I have expertise in distributed systems"
```

### MCP Server

Start the MCP server:

```bash
memora mcp-server

# With custom configuration
MEMORA_API_URL=http://api.example.com memora mcp-server
```

## Output Formats

### Pretty (Default)

Human-readable formatted output:

```bash
memora search <agent_id> "query"
```

### JSON

Machine-readable JSON output:

```bash
memora search <agent_id> "query" -o json
```

### YAML

YAML formatted output:

```bash
memora search <agent_id> "query" -o yaml
```

## Verbose Mode

Add `-v` or `--verbose` for detailed output:

```bash
memora search <agent_id> "query" -v
```

Shows:
- Request payload
- Response details
- Timing information

## Global Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Verbose output |
| `-o, --output <format>` | Output format: pretty, json, yaml |
| `--api-url <url>` | Override API URL |
| `--help` | Show help |
| `--version` | Show version |

## Examples

### Full Workflow

```bash
# Create an agent
curl -X PUT http://localhost:8080/api/agents/demo-agent \
  -H "Content-Type: application/json" \
  -d '{"background": "Demo agent"}'

# Store memories
memora put demo-agent "Alice works at Google"
memora put demo-agent "Bob is a data scientist"
memora put demo-agent "Alice and Bob are colleagues"

# Search
memora search demo-agent "Who works with Alice?"

# Think (with opinions)
memora think demo-agent "What do you know about the team?"

# Update personality
memora set-personality demo-agent \
  --openness 0.9 \
  --conscientiousness 0.7 \
  --extraversion 0.6 \
  --agreeableness 0.8 \
  --neuroticism 0.2 \
  --bias-strength 0.6

# Check profile
memora profile demo-agent
```
