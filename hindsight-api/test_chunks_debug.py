"""
Debug script to test chunk extraction.
"""
import asyncio
from datetime import datetime
from hindsight_api.engine.utils import extract_facts
from hindsight_api.engine.llm_wrapper import LLMConfig
import os

async def main():
    # Set up LLM config
    llm_config = LLMConfig.for_memory()

    # Test content
    long_content = """
    Alice is a senior software engineer at TechCorp. She has been working there for 5 years.
    Alice specializes in distributed systems and has led the development of the company's
    microservices architecture. She is known for writing clean, well-documented code.

    Bob joined the team last month as a junior developer. He is learning React and Node.js.
    Bob is enthusiastic and asks great questions during code reviews. He recently completed
    his first feature, which was a user authentication flow.

    The team uses Kubernetes for container orchestration and deploys to AWS. They follow
    agile methodologies with two-week sprints. Code reviews are mandatory before merging.
    """

    # Extract facts and chunks
    facts, chunks = await extract_facts(
        text=long_content,
        event_date=datetime(2024, 1, 15),
        context="team overview",
        llm_config=llm_config
    )

    print(f"\n=== Extracted {len(facts)} facts ===")
    for i, fact in enumerate(facts):
        print(f"{i+1}. {fact.fact[:100]}...")

    print(f"\n=== Extracted {len(chunks)} chunks ===")
    for i, (chunk_text, fact_count) in enumerate(chunks):
        print(f"Chunk {i}: {fact_count} facts, {len(chunk_text)} chars")
        print(f"  Text: {chunk_text[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
