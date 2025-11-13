"""
Test for PUT /api/agents/{agent_id} endpoint.
"""
import pytest


@pytest.mark.asyncio
async def test_put_agent_create(memory):
    """Test creating an agent via PUT endpoint."""
    from memora.api import CreateAgentRequest, PersonalityTraits

    agent_id = "test_put_create"

    # Create request
    request = CreateAgentRequest(
        personality=PersonalityTraits(
            openness=0.8,
            conscientiousness=0.6,
            extraversion=0.5,
            agreeableness=0.7,
            neuroticism=0.3,
            bias_strength=0.7
        ),
        background="I am a creative software engineer"
    )

    # Simulate the endpoint logic
    # Get existing profile or create with defaults
    profile = await memory.get_agent_profile(agent_id)

    # Update personality if provided
    if request.personality is not None:
        await memory.update_agent_personality(
            agent_id,
            request.personality.model_dump()
        )

    # Update background if provided
    if request.background is not None:
        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agents
                SET background = $2,
                    updated_at = NOW()
                WHERE agent_id = $1
                """,
                agent_id,
                request.background
            )

    # Get final profile
    final_profile = await memory.get_agent_profile(agent_id)

    # Verify
    assert final_profile["personality"]["openness"] == 0.8
    assert final_profile["personality"]["bias_strength"] == 0.7
    assert final_profile["background"] == "I am a creative software engineer"


@pytest.mark.asyncio
async def test_put_agent_partial_update(memory):
    """Test updating only background."""
    from memora.api import CreateAgentRequest

    agent_id = "test_put_partial"

    # Create with just background
    request = CreateAgentRequest(
        background="I am a data scientist"
    )

    # Simulate endpoint logic
    profile = await memory.get_agent_profile(agent_id)

    if request.background is not None:
        pool = await memory._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agents
                SET background = $2,
                    updated_at = NOW()
                WHERE agent_id = $1
                """,
                agent_id,
                request.background
            )

    final_profile = await memory.get_agent_profile(agent_id)

    # Should have default personality (0.5 for all)
    assert final_profile["personality"]["openness"] == 0.5
    assert final_profile["background"] == "I am a data scientist"
