# Hindsight Python Client

Python client library for the Hindsight API.

## Installation

```bash
pip install hindsight-client
```

## Usage

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Retain information
client.retain(
    bank_id="my-bank",
    content="Alice works at Google in Mountain View."
)

# Recall memories
results = client.recall(
    bank_id="my-bank",
    query="Where does Alice work?"
)

# Reflect and get an opinion
response = client.reflect(
    bank_id="my-bank",
    query="What do you think about Alice's career?"
)
```

## Documentation

For full documentation, visit [hindsight.dev](https://hindsight.dev).
