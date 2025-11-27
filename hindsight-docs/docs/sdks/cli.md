---
sidebar_position: 3
---

# CLI Reference

The Hindsight CLI provides command-line access to memory operations and agent management.

## Installation

### Pre-built Binaries

Download from the releases page:

```bash
# macOS (Apple Silicon)
curl -L https://github.com/hindsight/hindsight/releases/latest/download/hindsight-macos-arm64 -o hindsight
chmod +x hindsight
sudo mv hindsight /usr/local/bin/
```

### Build from Source

```bash
cd hindsight-cli-rust
cargo build --release
cp target/release/hindsight /usr/local/bin/
```

## Configuration

Set environment variables or use command flags:

```bash
export HINDSIGHT_API_URL=http://localhost:8888
export HINDSIGHT_AGENT_ID=my-agent
```

## Commands

### Memory Operations

#### put

Store a memory:

```bash
hindsight put <agent_id> "Alice works at Google as a software engineer"

# With context
hindsight put <agent_id> "Bob loves hiking" --context "hobby discussion"

# With event date
hindsight put <agent_id> "Meeting with Carol" --date "2024-01-15"
```

#### put-files

Store file contents as memories:

```bash
# Store a single file
hindsight put-files <agent_id> notes.txt

# Store multiple files
hindsight put-files <agent_id> file1.txt file2.md file3.json

# With context
hindsight put-files <agent_id> meeting-notes.txt --context "team meeting"
```

#### search

Search memories:

```bash
hindsight search <agent_id> "What does Alice do?"

# With options
hindsight search <agent_id> "hiking recommendations" --budget 100 --top-k 5

# Verbose output
hindsight search <agent_id> "query" -v
```

#### think

Generate a response using memories and opinions:

```bash
hindsight think <agent_id> "What do you know about Alice?"

# Verbose mode shows reasoning
hindsight think <agent_id> "Should I recommend Python or Java?" -v
```

### Memory bank Management

#### memory banks

List all memory banks:

```bash
hindsight memory banks
```

Output:

```
Available memory banks:
  - alice-agent
  - bob-agent
  - tech-advisor
```

#### profile

View memory bank profile:

```bash
hindsight profile <agent_id>
```

Output:

```
Memory bank: my-agent

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
hindsight set-personality <agent_id> \
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
hindsight background <agent_id> "I have expertise in distributed systems"
```

### MCP Server

Start the MCP server:

```bash
hindsight mcp-server

# With custom configuration
HINDSIGHT_API_URL=http://api.example.com hindsight mcp-server
```

## Output Formats

### Pretty (Default)

Human-readable formatted output:

```bash
hindsight search <agent_id> "query"
```

### JSON

Machine-readable JSON output:

```bash
hindsight search <agent_id> "query" -o json
```

### YAML

YAML formatted output:

```bash
hindsight search <agent_id> "query" -o yaml
```

## Verbose Mode

Add `-v` or `--verbose` for detailed output:

```bash
hindsight search <agent_id> "query" -v
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
# Create a memory bank
curl -X PUT http://localhost:8888/api/memory banks/demo-agent \
  -H "Content-Type: application/json" \
  -d '{"background": "Demo agent"}'

# Store memories
hindsight put demo-agent "Alice works at Google"
hindsight put demo-agent "Bob is a data scientist"
hindsight put demo-agent "Alice and Bob are colleagues"

# Search
hindsight search demo-agent "Who works with Alice?"

# Think (with opinions)
hindsight think demo-agent "What do you know about the team?"

# Update personality
hindsight set-personality demo-agent \
  --openness 0.9 \
  --conscientiousness 0.7 \
  --extraversion 0.6 \
  --agreeableness 0.8 \
  --neuroticism 0.2 \
  --bias-strength 0.6

# Check profile
hindsight profile demo-agent
```
