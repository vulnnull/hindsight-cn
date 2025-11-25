# @hindsight/client

TypeScript client for Hindsight - Semantic memory system with personality-driven thinking.

**Auto-generated from OpenAPI spec** - provides type-safe access to all Hindsight API endpoints.

## Installation

```bash
npm install @hindsight/client
# or
yarn add @hindsight/client
```

## Quick Start

```typescript
import { OpenAPI, MemoryStorageService, ReasoningService } from '@hindsight/client';

// Configure API base URL
OpenAPI.BASE = 'http://localhost:8888';

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

- [GitHub Repository](https://github.com/vectorize-io/hindsight)
- [Full Documentation](https://github.com/vectorize-io/hindsight/blob/main/README.md)
