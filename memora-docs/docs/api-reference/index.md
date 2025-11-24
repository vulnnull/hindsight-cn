---
sidebar_position: 1
---

# API Reference

Complete reference for Memora's HTTP and MCP APIs.

## HTTP API

The HTTP API reference is automatically generated from our OpenAPI specification. Browse the endpoints in the sidebar to see request/response details, parameters, and examples.

**Base URL:** `http://localhost:8080`

| Category | Endpoints |
|----------|-----------|
| **Memory Operations** | Store, search, list, delete memories |
| **Reasoning** | Think and generate personality-aware responses |
| **Agent Management** | Create, update, list agents and profiles |
| **Documents** | Manage document groupings |
| **Visualization** | Get entity graph data |

## MCP API

The MCP (Model Context Protocol) API exposes Memora tools for AI assistants like Claude Desktop.

| Tool | Description |
|------|-------------|
| `memora_search` | Search memories |
| `memora_think` | Generate personality-aware response |
| `memora_store` | Store new memory |
| `memora_agents` | List available agents |

[MCP Tools Reference →](./mcp)

## OpenAPI / Swagger

Interactive API documentation available when the server is running:

- **Swagger UI:** [http://localhost:8080/docs](http://localhost:8080/docs)
- **OpenAPI JSON:** [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)
