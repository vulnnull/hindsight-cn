# Hindsight

[![CI](https://github.com/vectorize-io/hindsight/actions/workflows/test.yml/badge.svg)](https://github.com/vectorize-io/hindsight/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI - hindsight-client](https://img.shields.io/pypi/v/hindsight-client?label=hindsight-client)](https://pypi.org/project/hindsight-client/)
[![PyPI - hindsight-api](https://img.shields.io/pypi/v/hindsight-api?label=hindsight-api)](https://pypi.org/project/hindsight-api/)
[![PyPI - hindsight-all](https://img.shields.io/pypi/v/hindsight-all?label=hindsight-all)](https://pypi.org/project/hindsight-all/)
[![npm](https://img.shields.io/npm/v/@vectorize-io/hindsight-client)](https://www.npmjs.com/package/@vectorize-io/hindsight-client)

**Long-term memory for AI agents.**

## Why Hindsight?

AI assistants forget everything between sessions. Every conversation starts from zero—no context about who you are, what you've discussed, or what the memory bank has learned. This isn't just inconvenient; it fundamentally limits what AI memory banks can do.

**The problem is harder than it looks:**

- **Simple vector search isn't enough** — "What did Alice do last spring?" requires temporal reasoning, not just semantic similarity
- **Facts get disconnected** — Knowing "Alice works at Google" and "Google is in Mountain View" should let you answer "Where does Alice work?" even if you never stored that directly
- **Memory banks need opinions** — A coding assistant that remembers "the user prefers functional programming" should weigh that when making recommendations
- **Context matters** — The same information means different things to different memory banks with different personalities

Hindsight solves these problems with a memory system designed specifically for AI memory banks.


## Quick Start

### Option 1: Docker (recommended)

Get the full experience with the API and Control Plane UI:

```bash
export OPENAI_API_KEY=your-key
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight
```

- **API**: http://localhost:8888
- **Control Plane UI**: http://localhost:9999

Then use the Python client:

```bash
pip install hindsight-client
```

```python
from hindsight import HindsightClient

client = HindsightClient(base_url="http://localhost:8888")

# Store memories
client.retain(bank_id="my-agent", content="Alice works at Google as a software engineer")
client.retain(bank_id="my-agent", content="Alice mentioned she loves hiking in the mountains")

# Query with temporal reasoning
results = client.recall(bank_id="my-agent", query="What does Alice do for work?")

# Get a synthesized perspective
response = client.reflect(bank_id="my-agent", query="Tell me about Alice")
print(response.text)
```

### Option 2: Embedded (no docker/server required)

For quick prototyping, run everything in-process:

```bash
pip install hindsight-all
export OPENAI_API_KEY=your-key
```

```python
import os
from hindsight import HindsightServer, HindsightClient

with HindsightServer(llm_provider="openai", llm_model="gpt-4o-mini", llm_api_key=os.environ["OPENAI_API_KEY"]) as server:
    client = HindsightClient(base_url=server.url)

    client.retain(bank_id="my-user", content="User prefers functional programming")
    response = client.reflect(bank_id="my-user", query="What coding style should I use?")
    print(response.text)
```



## Documentation

Full documentation: [hindsight.vectorize.io](https://hindsight.vectorize.io)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT
