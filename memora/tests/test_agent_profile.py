"""
Tests for agent profile management (personality and background).
"""
import pytest
import uuid
from datetime import datetime, timezone
from memora import TemporalSemanticMemory


def unique_agent_id(prefix: str) -> str:
    """Generate a unique agent ID for testing."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_get_agent_profile_creates_default(memory: TemporalSemanticMemory):
    """Test that getting a profile for a new agent creates default personality."""
    agent_id = unique_agent_id("test_profile_default")

    # Get profile for non-existent agent (should auto-create)
    profile = await memory.get_agent_profile(agent_id)

    assert profile is not None
    assert "personality" in profile
    assert "background" in profile

    # Check default personality values (all 0.5)
    personality = profile["personality"]
    assert personality["openness"] == 0.5
    assert personality["conscientiousness"] == 0.5
    assert personality["extraversion"] == 0.5
    assert personality["agreeableness"] == 0.5
    assert personality["neuroticism"] == 0.5
    assert personality["bias_strength"] == 0.5

    # Background should be empty
    assert profile["background"] == ""


@pytest.mark.asyncio
async def test_update_agent_personality(memory: TemporalSemanticMemory):
    """Test updating agent personality traits."""
    agent_id = unique_agent_id("test_profile_update")

    # Create agent with defaults
    profile = await memory.get_agent_profile(agent_id)
    assert profile["personality"]["openness"] == 0.5

    # Update personality
    new_personality = {
        "openness": 0.8,
        "conscientiousness": 0.6,
        "extraversion": 0.7,
        "agreeableness": 0.4,
        "neuroticism": 0.3,
        "bias_strength": 0.9,
    }
    await memory.update_agent_personality(agent_id, new_personality)

    # Retrieve and verify
    updated_profile = await memory.get_agent_profile(agent_id)
    for key in new_personality:
        assert abs(updated_profile["personality"][key] - new_personality[key]) < 0.001


@pytest.mark.asyncio
async def test_merge_agent_background(memory: TemporalSemanticMemory):
    """Test merging agent background information."""
    agent_id = unique_agent_id("test_profile_merge")

    # Create agent with defaults
    profile = await memory.get_agent_profile(agent_id)
    assert profile["background"] == ""

    # Add first background
    result1 = await memory.merge_agent_background(
        agent_id,
        "I was born in Texas",
        update_personality=False
    )
    assert "Texas" in result1["background"]

    # Add more background (should merge)
    result2 = await memory.merge_agent_background(
        agent_id,
        "I have 10 years of startup experience",
        update_personality=False
    )
    assert "Texas" in result2["background"] or "startup" in result2["background"]

    # Retrieve profile and verify
    final_profile = await memory.get_agent_profile(agent_id)
    assert final_profile["background"] != ""


@pytest.mark.asyncio
async def test_merge_background_handles_conflicts(memory: TemporalSemanticMemory):
    """Test that merging background handles conflicts (new overwrites old)."""
    agent_id = unique_agent_id("test_profile_conflict")

    # Add first background
    result1 = await memory.merge_agent_background(
        agent_id,
        "I was born in Colorado",
        update_personality=False
    )
    assert "Colorado" in result1["background"]

    # Add conflicting background (should overwrite)
    result2 = await memory.merge_agent_background(
        agent_id,
        "You were born in Texas",
        update_personality=False
    )
    # Should have Texas (new info), not Colorado (old info)
    assert "Texas" in result2["background"]


@pytest.mark.asyncio
async def test_list_agents(memory: TemporalSemanticMemory):
    """Test listing all agents."""
    # Create a few agents with unique IDs
    agent_id_1 = unique_agent_id("test_list")
    agent_id_2 = unique_agent_id("test_list")
    agent_id_3 = unique_agent_id("test_list")

    await memory.get_agent_profile(agent_id_1)
    await memory.get_agent_profile(agent_id_2)
    await memory.get_agent_profile(agent_id_3)

    # List all agents
    agents = await memory.list_agents()

    # Should have at least our 3 test agents
    agent_ids = [a["agent_id"] for a in agents]
    assert agent_id_1 in agent_ids
    assert agent_id_2 in agent_ids
    assert agent_id_3 in agent_ids

    # Each agent should have personality and background
    for agent in agents:
        assert "agent_id" in agent
        assert "personality" in agent
        assert "background" in agent
        assert "created_at" in agent
        assert "updated_at" in agent


@pytest.mark.asyncio
async def test_think_uses_personality(memory: TemporalSemanticMemory):
    """Test that THINK operation uses agent personality."""
    agent_id = unique_agent_id("test_think")

    # Set strong personality with high bias
    personality = {
        "openness": 0.9,  # Very open to new ideas
        "conscientiousness": 0.2,  # Low organization
        "extraversion": 0.8,  # Very extraverted
        "agreeableness": 0.1,  # Low agreeableness (more critical)
        "neuroticism": 0.7,  # High emotional sensitivity
        "bias_strength": 0.9,  # Strong personality influence
    }
    await memory.update_agent_personality(agent_id, personality)

    # Add background (without personality inference since we set it explicitly above)
    await memory.merge_agent_background(
        agent_id,
        "I am a creative artist who values innovation over tradition",
        update_personality=False
    )

    # Store some facts
    await memory.put_batch_async(
        agent_id=agent_id,
        contents=[
            {"content": "Traditional painting techniques have been used for centuries"},
            {"content": "Modern digital art is changing the art world"}
        ],
        document_id="art_facts"
    )

    # Wait a bit for facts to be stored
    import asyncio
    await asyncio.sleep(1)

    # Think about art (personality should influence the response)
    result = await memory.think_async(
        agent_id=agent_id,
        query="What do you think about traditional vs modern art?",
        thinking_budget=50
    )

    # Should have a response
    assert result.text is not None
    assert len(result.text) > 0

    # The response should reflect high openness and creative background
    # (though we can't assert exact content, the personality was used)
