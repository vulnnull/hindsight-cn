"""
Quick script to fix corrupted background data for ea_marcus agent.
The background field contains JSON instead of plain text.
"""
import asyncio
import json
import os
from memora import TemporalSemanticMemory


async def fix_background(agent_id: str):
    """Fix background by extracting text from JSON string."""
    # Initialize memory system from environment variables
    memory = TemporalSemanticMemory()

    try:
        # Get current profile
        profile = await memory.get_agent_profile(agent_id)
        background = profile["background"]

        print(f"Current background for {agent_id}:")
        print(f"  {background[:200]}")
        print()

        # Check if it's corrupted (contains JSON)
        if background.strip().startswith("{"):
            print("Background appears to be corrupted JSON. Attempting to extract text...")
            try:
                # Try to parse as JSON
                data = json.loads(background)
                if "background" in data:
                    clean_background = data["background"]
                    print(f"Extracted text: {clean_background}")

                    # Update with clean background (without personality inference to preserve current traits)
                    await memory.merge_agent_background(
                        agent_id,
                        clean_background,
                        update_personality=False
                    )
                    print(f"✓ Fixed background for {agent_id}")
                else:
                    print("✗ JSON doesn't have 'background' key")
            except json.JSONDecodeError:
                print("✗ Failed to parse as JSON")
        else:
            print("Background looks fine - no corruption detected")

    finally:
        await memory.close()


async def main():
    agent_id = "ea_marcus"
    print(f"Fixing background for agent: {agent_id}")
    print("=" * 60)
    await fix_background(agent_id)


if __name__ == "__main__":
    asyncio.run(main())
