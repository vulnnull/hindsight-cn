"""
Tests for LLM-based personality trait inference from background.
"""
import pytest
import uuid
from memora import TemporalSemanticMemory


def unique_agent_id(prefix: str) -> str:
    """Generate a unique agent ID for testing."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_background_merge_with_personality_inference(memory: TemporalSemanticMemory):
    """Test that background merge infers personality traits by default."""
    agent_id = unique_agent_id("test_infer")

    # Add background with creative/artistic traits
    result = await memory.merge_agent_background(
        agent_id,
        "I am a creative software engineer who loves innovation and trying new technologies",
        update_personality=True
    )

    assert "background" in result
    assert "personality" in result

    background = result["background"]
    personality = result["personality"]

    # Check background was merged
    assert "creative" in background.lower() or "innovation" in background.lower()

    # Check personality was inferred (should have high openness due to "creative" and "innovation")
    assert "openness" in personality
    assert personality["openness"] > 0.5  # Should be higher than neutral
    assert 0.0 <= personality["openness"] <= 1.0

    # Check all required traits are present
    required_traits = ["openness", "conscientiousness", "extraversion",
                      "agreeableness", "neuroticism", "bias_strength"]
    for trait in required_traits:
        assert trait in personality
        assert 0.0 <= personality[trait] <= 1.0


@pytest.mark.asyncio
async def test_background_merge_without_personality_inference(memory: TemporalSemanticMemory):
    """Test that background merge skips personality inference when disabled."""
    agent_id = unique_agent_id("test_no_infer")

    # Get initial personality
    initial_profile = await memory.get_agent_profile(agent_id)
    initial_personality = initial_profile["personality"]

    # Add background WITHOUT personality inference
    result = await memory.merge_agent_background(
        agent_id,
        "I am a data scientist",
        update_personality=False
    )

    assert "background" in result
    assert "personality" not in result  # Should NOT have personality in response

    # Check personality unchanged in database
    final_profile = await memory.get_agent_profile(agent_id)
    final_personality = final_profile["personality"]

    assert initial_personality == final_personality


@pytest.mark.asyncio
async def test_personality_inference_for_organized_engineer(memory: TemporalSemanticMemory):
    """Test personality inference for organized/conscientious profile."""
    agent_id = unique_agent_id("test_organized")

    result = await memory.merge_agent_background(
        agent_id,
        "I am a methodical engineer who values organization and systematic planning",
        update_personality=True
    )

    personality = result["personality"]

    # Should have high conscientiousness
    assert personality["conscientiousness"] > 0.5


@pytest.mark.asyncio
async def test_personality_inference_for_startup_founder(memory: TemporalSemanticMemory):
    """Test personality inference for entrepreneurial profile."""
    agent_id = unique_agent_id("test_founder")

    result = await memory.merge_agent_background(
        agent_id,
        "I am a startup founder who thrives on risk and social interaction",
        update_personality=True
    )

    personality = result["personality"]

    # Should have high openness (risk-taking) and extraversion (social)
    assert personality["openness"] > 0.5
    assert personality["extraversion"] > 0.5


@pytest.mark.asyncio
async def test_personality_updates_in_database(memory: TemporalSemanticMemory):
    """Test that inferred personality is actually stored in database."""
    agent_id = unique_agent_id("test_db_update")

    # Merge with personality inference
    result = await memory.merge_agent_background(
        agent_id,
        "I am an innovative designer",
        update_personality=True
    )

    inferred_personality = result["personality"]

    # Retrieve from database
    profile = await memory.get_agent_profile(agent_id)
    db_personality = profile["personality"]

    # Should match
    assert db_personality == inferred_personality


@pytest.mark.asyncio
async def test_multiple_background_merges_update_personality(memory: TemporalSemanticMemory):
    """Test that each background merge can update personality."""
    agent_id = unique_agent_id("test_multi_merge")

    # First merge - neutral background
    result1 = await memory.merge_agent_background(
        agent_id,
        "I am a software engineer",
        update_personality=True
    )
    personality1 = result1["personality"]

    # Second merge - add creative aspect
    result2 = await memory.merge_agent_background(
        agent_id,
        "I love creative problem solving and innovation",
        update_personality=True
    )
    personality2 = result2["personality"]

    # Personality should have evolved (likely higher openness now)
    # Background should contain both pieces
    assert "engineer" in result2["background"].lower() or "software" in result2["background"].lower()
    assert "creative" in result2["background"].lower() or "innovation" in result2["background"].lower()


@pytest.mark.asyncio
async def test_background_merge_conflict_resolution_with_personality(memory: TemporalSemanticMemory):
    """Test that conflicts are resolved and personality reflects final background."""
    agent_id = unique_agent_id("test_conflict")

    # First background
    await memory.merge_agent_background(
        agent_id,
        "I was born in Colorado and prefer stability",
        update_personality=True
    )

    # Conflicting background
    result = await memory.merge_agent_background(
        agent_id,
        "You were born in Texas and love taking risks",
        update_personality=True
    )

    background = result["background"]
    personality = result["personality"]

    # Should have Texas (new info), not Colorado
    assert "texas" in background.lower()
    # Personality should reflect risk-taking
    assert personality["openness"] > 0.5
