#!/usr/bin/env python3
"""
Memory Banks API examples for Hindsight.
Run: python examples/api/memory-banks.py
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
# Doc Examples
# =============================================================================

# [docs:create-bank]
client.create_bank(
    bank_id="my-bank",
    name="Research Assistant",
    background="I am a research assistant specializing in machine learning",
    disposition={
        "skepticism": 4,
        "literalism": 3,
        "empathy": 3
    }
)
# [/docs:create-bank]


# [docs:bank-background]
client.create_bank(
    bank_id="financial-advisor",
    background="""I am a conservative financial advisor with 20 years of experience.
    I prioritize capital preservation over aggressive growth.
    I have seen multiple market crashes and believe in diversification."""
)
# [/docs:bank-background]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/my-bank")
requests.delete(f"{HINDSIGHT_URL}/v1/default/banks/financial-advisor")

print("memory-banks.py: All examples passed")
