#!/usr/bin/env python3
"""
Main Methods overview examples for Hindsight.
Run: python examples/api/main-methods.py
"""
import os
import requests

HINDSIGHT_URL = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
from hindsight_client import Hindsight

client = Hindsight(base_url=HINDSIGHT_URL)

# =============================================================================
# Doc Examples - Retain Section
# =============================================================================

# [docs:main-retain]
# Store a single fact
client.retain(
    bank_id="my-bank",
    content="Alice joined Google in March 2024 as a Senior ML Engineer"
)

# Store a conversation
conversation = """
User: What did you work on today?
Assistant: I reviewed the new ML pipeline architecture.
User: How did it look?
Assistant: Promising, but needs better error handling.
"""

client.retain(
    bank_id="my-bank",
    content=conversation,
    context="Daily standup conversation"
)

# Batch retain multiple items
client.retain_batch(
    bank_id="my-bank",
    items=[
        {"content": "Bob prefers Python for data science"},
        {"content": "Alice recommends using pytest for testing"},
        {"content": "The team uses GitHub for code reviews"}
    ]
)
# [/docs:main-retain]


# =============================================================================
# Doc Examples - Recall Section
# =============================================================================

# [docs:main-recall]
# Basic search
results = client.recall(
    bank_id="my-bank",
    query="What does Alice do at Google?"
)

for result in results.results:
    print(f"- {result.text}")

# Search with options
results = client.recall(
    bank_id="my-bank",
    query="What happened last spring?",
    budget="high",  # More thorough graph traversal
    max_tokens=8192,  # Return more context
    types=["world"]  # Only world facts
)

# Include entity information
results = client.recall(
    bank_id="my-bank",
    query="Tell me about Alice",
    include_entities=True,
    max_entity_tokens=500
)

# Check entity details
for entity in results.entities or []:
    print(f"Entity: {entity.name}")
    print(f"Observations: {entity.observations}")
# [/docs:main-recall]


# =============================================================================
# Doc Examples - Reflect Section
# =============================================================================

# [docs:main-reflect]
# Basic reflect
response = client.reflect(
    bank_id="my-bank",
    query="Should we adopt TypeScript for our backend?"
)

print(response.text)
print("\nBased on:", len(response.based_on or []), "facts")

# Reflect with options
response = client.reflect(
    bank_id="my-bank",
    query="What are Alice's strengths for the team lead role?",
    budget="high"  # More thorough reasoning
)

# See which facts influenced the response
for fact in response.based_on or []:
    print(f"- {fact.text}")
# [/docs:main-reflect]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/my-bank")

print("main-methods.py: All examples passed")
