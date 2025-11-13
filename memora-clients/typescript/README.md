# @memora/client

TypeScript client for Memora - Semantic memory system with personality-driven thinking.

**Auto-generated from OpenAPI spec** - provides type-safe access to all Memora API endpoints.

## Installation

```bash
npm install @memora/client
# or
yarn add @memora/client
```

## Quick Start

```typescript
import { OpenAPI, MemoryStorageService, ReasoningService } from '@memora/client';

// Configure API base URL
OpenAPI.BASE = 'http://localhost:8000';

// Store memory
await MemoryStorageService.putApiPutPost({
  agent_id: 'user123',
  content: 'Alice loves machine learning'
});

// Think (generate answer with personality)
const response = await ReasoningService.thinkApiThinkPost({
  agent_id: 'user123',
  query: 'What does Alice think about AI?',
  thinking_budget: 50
});

console.log(response.text);
```

## Available Services

- `MemoryStorageService` - Store and retrieve facts
- `SearchService` - Semantic and temporal search
- `ReasoningService` - Personality-driven thinking
- `VisualizationService` - Memory graphs and statistics
- `ManagementService` - Agent profiles and configuration
- `DocumentsService` - Document tracking

All services are fully typed with TypeScript interfaces.

## Development

Auto-generated from `openapi.json`. See [RELEASE.md](../../RELEASE.md) for regeneration instructions.

## Links

- [GitHub Repository](https://github.com/nicoloboschi/memora)
- [Full Documentation](https://github.com/nicoloboschi/memora/blob/main/README.md)
