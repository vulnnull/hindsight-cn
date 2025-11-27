---
sidebar_position: 1
slug: /
---

# Overview

## Why Hindsight?

AI assistants forget everything between sessions. Every conversation starts from zero—no context about who you are, what you've discussed, or what the memory bank has learned. This isn't just inconvenient; it fundamentally limits what AI memory banks can do.

**The problem is harder than it looks:**

- **Simple vector search isn't enough** — "What did Alice do last spring?" requires temporal reasoning, not just semantic similarity
- **Facts get disconnected** — Knowing "Alice works at Google" and "Google is in Mountain View" should let you answer "Where does Alice work?" even if you never stored that directly
- **Memory banks need opinions** — A coding assistant that remembers "the user prefers functional programming" should weigh that when making recommendations
- **Context matters** — The same information means different things to different memory banks with different personalities

Hindsight solves these problems with a memory system designed specifically for AI memory banks.

## What Hindsight Does

```mermaid
graph TB
    subgraph Your Application
        Agent[AI Agent]
    end

    subgraph Hindsight
        API[Hindsight API]

        subgraph Memory Bank
            Documents[Documents]
            Memories[Memories]
            Entities[Entities]
        end
    end

    Agent -->|retain| API
    Agent -->|recall| API
    Agent -->|reflect| API

    API --> Documents
    API --> Memories
    API --> Entities
```

**Your AI agent** stores information via `retain()`, searches with `recall()`, and reasons with `reflect()` — all interactions with its dedicated **memory bank**

## Key Components

### Three Memory Types

Hindsight separates memories by type for epistemic clarity:

| Type | What it stores | Example |
|------|----------------|---------|
| **World** | Objective facts received | "Alice works at Google" |
| **Bank** | Bank's own actions | "I recommended Python to Bob" |
| **Opinion** | Formed beliefs + confidence | "Python is best for ML" (0.85) |

### Multi-Strategy Retrieval (TEMPR)

Four search strategies run in parallel:

```mermaid
graph LR
    Q[Query] --> S[Semantic]
    Q --> K[Keyword]
    Q --> G[Graph]
    Q --> T[Temporal]

    S --> RRF[RRF Fusion]
    K --> RRF
    G --> RRF
    T --> RRF

    RRF --> CE[Cross-Encoder]
    CE --> R[Results]
```

| Strategy | Best for |
|----------|----------|
| **Semantic** | Conceptual similarity, paraphrasing |
| **Keyword (BM25)** | Names, technical terms, exact matches |
| **Graph** | Related entities, indirect connections |
| **Temporal** | "last spring", "in June", time ranges |

### Personality Framework (CARA)

Memory banks have Big Five personality traits that influence opinion formation:

| Trait | Low | High |
|-------|-----|------|
| **Openness** | Prefers proven methods | Embraces new ideas |
| **Conscientiousness** | Flexible, spontaneous | Systematic, organized |
| **Extraversion** | Independent | Collaborative |
| **Agreeableness** | Direct, analytical | Diplomatic, harmonious |
| **Neuroticism** | Calm, optimistic | Risk-aware, cautious |

The `bias_strength` parameter (0-1) controls how much personality influences opinions.

## Next Steps

### Getting Started
- [**Installation**](./api/installation) — Install Hindsight for Python, Node.js, or CLI
- [**Quick Start**](./api/quickstart) — Get up and running in 60 seconds

### Core Concepts
- [**Retain**](./retain) — How memories are stored with multi-dimensional facts
- [**Recall**](./retrieval) — How TEMPR's 4-way search retrieves memories
- [**Reflect**](./personality) — How personality influences reasoning and opinion formation

### API Methods
- [**Main Methods**](./api/main-methods) — Overview of retain, recall, reflect
- [**Memory Banks**](./api/memory-banks) — Configure personality and background
- [**Entities**](./api/entities) — Track people, places, and concepts
- [**Documents**](./api/documents) — Manage document sources
- [**Operations**](./api/operations) — Monitor async tasks

### Deployment
- [**Server Setup**](./server) — Deploy with Docker Compose, Helm, or pip
