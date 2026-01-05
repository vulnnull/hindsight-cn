# Hindsight Integration Tests

E2E and integration tests for Hindsight API that require a running server.

## Running Tests

1. Start the API server:
   ```bash
   ./scripts/dev/start-api.sh
   ```

2. Run the tests:
   ```bash
   cd hindsight-integration-tests
   HINDSIGHT_API_URL=http://localhost:8888 uv run pytest tests/ -v
   ```

## Environment Variables

- `HINDSIGHT_API_URL` - Base URL of the running Hindsight API (default: `http://localhost:8888`)
