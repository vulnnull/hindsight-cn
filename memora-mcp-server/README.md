# Memora MCP Server

Remote MCP server for integrating Memora memory capabilities with Claude Desktop and other MCP clients.

## Configuration

Required environment variables:
- `MEMORA_AGENT_ID`: The agent ID to use for all operations
- `MEMORA_API_URL`: Memora API endpoint (default: http://localhost:8080)
- `MEMORA_API_KEY`: API key for authentication (optional)

## Usage

### Start the HTTP/SSE Server
```bash
export MEMORA_AGENT_ID=your-agent-id
export MEMORA_API_URL=http://localhost:8080
export PORT=8765  # optional, default is 8765
export HOST=127.0.0.1  # optional, default is 127.0.0.1
uv run memora-mcp-server
```

The server will start on `http://127.0.0.1:8765`

### Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "memora": {
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

Make sure the Memora MCP server is running before starting Claude Desktop.

## Available Tools

- `memora_put`: Store facts/memories with required context
- `memora_search`: Search through memories using semantic search
