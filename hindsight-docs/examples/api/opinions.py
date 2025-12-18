#!/usr/bin/env python3
"""
Opinions API examples for Hindsight.
Run: python examples/api/opinions.py
"""
import os
import requests

HINDSIGHT_URL = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
from hindsight_client import Hindsight

client = Hindsight(base_url=HINDSIGHT_URL)

# Seed some data about programming languages
client.retain(bank_id="my-bank", content="Python is widely used for data science and machine learning")
client.retain(bank_id="my-bank", content="Functional programming emphasizes immutability and pure functions")
client.retain(bank_id="my-bank", content="Rust has better memory safety than C++")
client.retain(bank_id="my-bank", content="C++ has a larger ecosystem and more libraries")

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:opinion-form]
# Ask a question - the system may form opinions based on stored facts
answer = client.reflect(
    bank_id="my-bank",
    query="What do you think about functional programming?"
)

print(answer.text)
# [/docs:opinion-form]


# [docs:opinion-search]
# Search for facts about a topic
results = client.recall(
    bank_id="my-bank",
    query="programming languages"
)

for result in results.results:
    print(f"- {result.text}")
# [/docs:opinion-search]


# [docs:opinion-disposition]
# Create two memory banks with different dispositions
client.create_bank(
    bank_id="open-minded",
    disposition={"skepticism": 2, "literalism": 2, "empathy": 4}
)

client.create_bank(
    bank_id="conservative",
    disposition={"skepticism": 5, "literalism": 5, "empathy": 2}
)

# Store the same facts to both
facts = [
    "Rust has better memory safety than C++",
    "C++ has a larger ecosystem and more libraries",
    "Rust compile times are longer than C++"
]
for fact in facts:
    client.retain(bank_id="open-minded", content=fact)
    client.retain(bank_id="conservative", content=fact)

# Ask both the same question - different dispositions lead to different responses
q = "Should we rewrite our C++ codebase in Rust?"

answer1 = client.reflect(bank_id="open-minded", query=q)
print("Open-minded response:", answer1.text[:100], "...")

answer2 = client.reflect(bank_id="conservative", query=q)
print("Conservative response:", answer2.text[:100], "...")
# [/docs:opinion-disposition]


# [docs:opinion-in-reflect]
answer = client.reflect(bank_id="my-bank", query="What language should I learn?")

print("Response:", answer.text)

# See which facts influenced the response
if answer.based_on:
    print("\nBased on these facts:")
    for fact in answer.based_on:
        print(f"  - {fact.text}")
# [/docs:opinion-in-reflect]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/my-bank")
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/open-minded")
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/conservative")

print("opinions.py: All examples passed")
