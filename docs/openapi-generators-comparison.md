# OpenAPI Client Generator Comparison

## Current: openapi-python-client
**Pros:**
- Python-native (no Java required)
- Lightweight
- Good type hints
- Uses httpx (modern)

**Cons:**
- Functional style (not OOP)
- Verbose imports
- Awkward API (need to pass client everywhere)

## Option 1: openapi-generator (Recommended)
**Command:** `openapi-generator-cli generate -i openapi.json -g python -o memora-clients/python`

**Pros:**
- ✅ **OOP style** - generates `client.search_memories()` not `search_memories.sync(client=...)`
- ✅ Widely used (industry standard)
- ✅ Active development
- ✅ Generates proper SDK with clean imports
- ✅ Built-in retry, timeout handling

**Cons:**
- Requires Java Runtime (but can use Docker)
- Larger generated code
- Some boilerplate

**Example Generated Code:**
```python
from memora_client import ApiClient, Configuration, MemoryOperationsApi

config = Configuration(host="http://localhost:8000")
client = ApiClient(config)
api = MemoryOperationsApi(client)

# Clean method calls!
results = api.search_memories(
    agent_id="alice",
    search_request=SearchRequest(query="...")
)
```

## Option 2: fern
**Command:** `fern generate`

**Pros:**
- ✅ Modern, best-in-class DX
- ✅ Beautiful generated code
- ✅ Excellent type hints
- ✅ Async-first
- ✅ Pydantic v2 models

**Cons:**
- Requires `fern.config.yml` setup
- Less mature than openapi-generator
- Config-heavy

**Example:**
```python
from memora import Memora

client = Memora(base_url="http://localhost:8000")
results = client.search_memories(agent_id="alice", query="...")
```

## Option 3: speakeasy
**Command:** `speakeasy generate sdk`

**Pros:**
- ✅ Very clean generated code
- ✅ Great DX
- ✅ SDK versioning built-in

**Cons:**
- Commercial (free tier available)
- Requires account
- Less control

## Recommendation: openapi-generator

Use **openapi-generator** because it:
1. Generates proper OOP-style APIs
2. Industry standard with great support
3. Can run via Docker (no Java install needed)
4. Will give you `api.search_memories()` style calls

### Migration Steps:

1. **Install via Docker:**
```bash
alias openapi-generator='docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli'
```

2. **Generate config:**
```bash
openapi-generator config-help -g python
```

3. **Create config file:** `openapi-generator-config.yaml`
```yaml
packageName: memora_client
projectName: memora-client
packageVersion: 0.0.7
library: urllib3  # or 'asyncio' for async
```

4. **Generate:**
```bash
openapi-generator generate \
  -i openapi.json \
  -g python \
  -o memora-clients/python \
  -c openapi-generator-config.yaml
```

This will generate code like:
```python
import memora_client
from memora_client.api import memory_operations_api

config = memora_client.Configuration(host="http://localhost:8000")
with memora_client.ApiClient(config) as api_client:
    api = memory_operations_api.MemoryOperationsApi(api_client)
    response = api.search_memories(
        agent_id="alice",
        search_request=SearchRequest(query="...")
    )
```

Then we add our thin `Memora` wrapper on top for even simpler usage!
