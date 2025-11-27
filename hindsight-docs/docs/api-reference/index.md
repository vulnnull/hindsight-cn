---
sidebar_position: 1
---

# API Reference

Complete reference for Hindsight's HTTP and MCP APIs.

## HTTP API

The HTTP API reference is automatically generated from our OpenAPI specification. Browse the endpoints in the sidebar to see request/response details, parameters, and examples.

**Base URL:** `http://localhost:8888`

| Category | Endpoints |
|----------|-----------|
| **Memory Operations** | Store, search, list, delete memories |
| **Reasoning** | Think and generate personality-aware responses |
| **Memory bank Management** | Create, update, list memory banks and profiles |
| **Documents** | Manage document groupings |
| **Visualization** | Get entity graph data |

## MCP API

The MCP (Model Context Protocol) API exposes Hindsight tools for AI assistants like Claude Desktop.

| Tool | Description |
|------|-------------|
| `hindsight_search` | Search memories |
| `hindsight_think` | Generate personality-aware response |
| `hindsight_store` | Store new memory |
| `hindsight_agents` | List available memory banks |

[MCP Tools Reference →](/api-reference/mcp)

## OpenAPI / Swagger

Interactive API documentation available when the server is running:

- **Swagger UI:** [http://localhost:8888/docs](http://localhost:8888/docs)
- **OpenAPI JSON:** [http://localhost:8888/openapi.json](http://localhost:8888/openapi.json)
