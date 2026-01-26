#!/usr/bin/env python3
"""
Reflections API examples for Hindsight.
Run: python examples/api/reflections.py
"""
import os
import time
import requests

HINDSIGHT_URL = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
BANK_ID = "reflections-demo-bank"

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
from hindsight_client import Hindsight

client = Hindsight(base_url=HINDSIGHT_URL)

# Create bank and seed some data
client.create_bank(bank_id=BANK_ID, name="Reflections Demo")
client.retain(bank_id=BANK_ID, content="The team prefers async communication via Slack")
client.retain(bank_id=BANK_ID, content="For urgent issues, use the #incidents channel")
client.retain(bank_id=BANK_ID, content="Weekly syncs happen every Monday at 10am")

# Wait for data to be processed
time.sleep(2)

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:create-reflection]
# Create a reflection (runs reflect in background)
response = requests.post(
    f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections",
    json={
        "name": "Team Communication Preferences",
        "source_query": "How does the team prefer to communicate?",
        "tags": ["team", "communication"]
    }
)
result = response.json()

# Returns an operation_id - check operations endpoint for completion
print(f"Operation ID: {result['operation_id']}")
# [/docs:create-reflection]

# Wait for the reflection to be created
time.sleep(5)

# [docs:list-reflections]
# List all reflections in a bank
response = requests.get(f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections")
reflections = response.json()

for reflection in reflections["items"]:
    print(f"- {reflection['name']}: {reflection['source_query']}")
# [/docs:list-reflections]

# Get the reflection ID for subsequent examples
reflection_id = reflections["items"][0]["id"] if reflections["items"] else None

if reflection_id:
    # [docs:get-reflection]
    # Get a specific reflection
    response = requests.get(
        f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections/{reflection_id}"
    )
    reflection = response.json()

    print(f"Name: {reflection['name']}")
    print(f"Content: {reflection['content']}")
    print(f"Last refreshed: {reflection['last_refreshed_at']}")
    # [/docs:get-reflection]


    # [docs:refresh-reflection]
    # Refresh a reflection to update with current knowledge
    response = requests.post(
        f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections/{reflection_id}/refresh"
    )
    result = response.json()

    print(f"Refresh operation ID: {result['operation_id']}")
    # [/docs:refresh-reflection]


    # [docs:update-reflection]
    # Update a reflection's name
    response = requests.patch(
        f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections/{reflection_id}",
        json={"name": "Updated Team Communication Preferences"}
    )
    updated = response.json()

    print(f"Updated name: {updated['name']}")
    # [/docs:update-reflection]


    # [docs:delete-reflection]
    # Delete a reflection
    requests.delete(
        f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}/reflections/{reflection_id}"
    )
    # [/docs:delete-reflection]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/{BANK_ID}")

print("reflections.py: All examples passed")
