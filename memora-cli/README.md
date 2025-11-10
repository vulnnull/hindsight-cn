# Memora CLI

Modern command-line interface for the Memora Temporal Semantic Memory System.

## Installation

```bash
pip install memora-cli
```

## Configuration

Set the API endpoint URL (defaults to `http://localhost:8080`):

```bash
export MEMORA_API_URL="http://localhost:8080"
```

## Commands

### Search Memories

```bash
memora search alice "What did she say about AI?"
memora search alice "hiking activities" --type world --max-tokens 8000
memora search alice "recent events" --budget 150 --trace
```

### Think (Generate Answers)

```bash
memora think alice "What do you think about machine learning?"
```

### Store Memories

Store a single memory:

```bash
memora put alice "Alice loves machine learning and AI"
memora put alice "Today we discussed neural networks" --context "team meeting"

# Async mode - returns immediately, processes in background
memora put alice "Important note" --async
```

### Import Files

Import memories from local files (.txt and .md):

```bash
# Import a single file
memora put-files alice meeting-notes.txt

# Import all files from a directory
memora put-files alice ./documents/

# Async mode - queue files for background processing
memora put-files alice ./documents/ --async
```

### List Agents

```bash
memora agents
```

## Features

- Beautiful TUI with Rich formatting (panels, tables, syntax highlighting)
- Color-coded fact types (cyan=world, magenta=agent, yellow=opinion)
- Progress bars and spinners for async operations
- Tree views for file hierarchies
- HTTP client (no direct database access needed)

## Requirements

- Python >= 3.11
- Memora API server running
