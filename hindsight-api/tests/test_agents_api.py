"""
Tests for agent management API (profile, personality, background).
"""
import pytest
import uuid
from hindsight_api import MemoryEngine
from hindsight_api.api import CreateBankRequest, DispositionTraits
from hindsight_api.engine.memory_engine import Budget


def unique_agent_id(prefix: str) -> str:
    """Generate a unique agent ID for testing."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestAgentProfile:
    """Tests for agent profile management."""

    @pytest.mark.asyncio
    async def test_get_agent_profile_creates_default(self, memory: MemoryEngine):
        """Test that getting a profile for a new agent creates default personality."""
        bank_id = unique_agent_id("test_profile_default")

        profile = await memory.get_bank_profile(bank_id)

        assert profile is not None
        assert "personality" in profile
        assert "background" in profile

        personality = profile["personality"]
        assert personality.openness == 0.5
        assert personality.conscientiousness == 0.5
        assert personality.extraversion == 0.5
        assert personality.agreeableness == 0.5
        assert personality.neuroticism == 0.5
        assert personality.bias_strength == 0.5

        assert profile["background"] == ""

    @pytest.mark.asyncio
    async def test_update_agent_personality(self, memory: MemoryEngine):
        """Test updating agent personality traits."""
        bank_id = unique_agent_id("test_profile_update")

        profile = await memory.get_bank_profile(bank_id)
        assert profile["personality"].openness == 0.5

        new_personality = {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.4,
            "neuroticism": 0.3,
            "bias_strength": 0.9,
        }
        await memory.update_bank_personality(bank_id, new_personality)

        updated_profile = await memory.get_bank_profile(bank_id)
        personality = updated_profile["personality"]
        assert abs(personality.openness - new_personality["openness"]) < 0.001
        assert abs(personality.conscientiousness - new_personality["conscientiousness"]) < 0.001
        assert abs(personality.extraversion - new_personality["extraversion"]) < 0.001
        assert abs(personality.agreeableness - new_personality["agreeableness"]) < 0.001
        assert abs(personality.neuroticism - new_personality["neuroticism"]) < 0.001
        assert abs(personality.bias_strength - new_personality["bias_strength"]) < 0.001

    @pytest.mark.asyncio
    async def test_list_agents(self, memory: MemoryEngine):
        """Test listing all agents."""
        agent_id_1 = unique_agent_id("test_list")
        agent_id_2 = unique_agent_id("test_list")
        agent_id_3 = unique_agent_id("test_list")

        await memory.get_bank_profile(agent_id_1)
        await memory.get_bank_profile(agent_id_2)
        await memory.get_bank_profile(agent_id_3)

        agents = await memory.list_banks()

        agent_ids = [a["bank_id"] for a in agents]
        assert agent_id_1 in agent_ids
        assert agent_id_2 in agent_ids
        assert agent_id_3 in agent_ids

        for agent in agents:
            assert "bank_id" in agent
            assert "personality" in agent
            assert "background" in agent
            assert "created_at" in agent
            assert "updated_at" in agent


class TestAgentBackground:
    """Tests for agent background management."""

    @pytest.mark.asyncio
    async def test_merge_agent_background(self, memory: MemoryEngine):
        """Test merging agent background information."""
        bank_id = unique_agent_id("test_profile_merge")

        profile = await memory.get_bank_profile(bank_id)
        assert profile["background"] == ""

        result1 = await memory.merge_bank_background(
            bank_id,
            "I was born in Texas",
            update_personality=False
        )
        assert "Texas" in result1["background"]

        result2 = await memory.merge_bank_background(
            bank_id,
            "I have 10 years of startup experience",
            update_personality=False
        )
        assert "Texas" in result2["background"] or "startup" in result2["background"]

        final_profile = await memory.get_bank_profile(bank_id)
        assert final_profile["background"] != ""

    @pytest.mark.asyncio
    async def test_merge_background_handles_conflicts(self, memory: MemoryEngine):
        """Test that merging background handles conflicts (new overwrites old)."""
        bank_id = unique_agent_id("test_profile_conflict")

        result1 = await memory.merge_bank_background(
            bank_id,
            "I was born in Colorado",
            update_personality=False
        )
        assert "Colorado" in result1["background"]

        result2 = await memory.merge_bank_background(
            bank_id,
            "You were born in Texas",
            update_personality=False
        )
        assert "Texas" in result2["background"]


class TestAgentEndpoint:
    """Tests for agent PUT endpoint logic."""

    @pytest.mark.asyncio
    async def test_put_agent_create(self, memory: MemoryEngine):
        """Test creating an agent via PUT endpoint."""
        bank_id = unique_agent_id("test_put_create")

        request = CreateBankRequest(
            personality=DispositionTraits(
                openness=0.8,
                conscientiousness=0.6,
                extraversion=0.5,
                agreeableness=0.7,
                neuroticism=0.3,
                bias_strength=0.7
            ),
            background="I am a creative software engineer"
        )

        profile = await memory.get_bank_profile(bank_id)

        if request.personality is not None:
            await memory.update_bank_personality(
                bank_id,
                request.personality.model_dump()
            )

        if request.background is not None:
            pool = await memory._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE banks
                    SET background = $2,
                        updated_at = NOW()
                    WHERE bank_id = $1
                    """,
                    bank_id,
                    request.background
                )

        final_profile = await memory.get_bank_profile(bank_id)

        assert final_profile["personality"].openness == 0.8
        assert final_profile["personality"].bias_strength == 0.7
        assert final_profile["background"] == "I am a creative software engineer"

    @pytest.mark.asyncio
    async def test_put_agent_partial_update(self, memory: MemoryEngine):
        """Test updating only background."""
        bank_id = unique_agent_id("test_put_partial")

        request = CreateBankRequest(
            background="I am a data scientist"
        )

        profile = await memory.get_bank_profile(bank_id)

        if request.background is not None:
            pool = await memory._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE banks
                    SET background = $2,
                        updated_at = NOW()
                    WHERE bank_id = $1
                    """,
                    bank_id,
                    request.background
                )

        final_profile = await memory.get_bank_profile(bank_id)

        assert final_profile["personality"].openness == 0.5
        assert final_profile["background"] == "I am a data scientist"


class TestAgentPersonalityIntegration:
    """Tests for personality integration with other features."""

    @pytest.mark.asyncio
    async def test_think_uses_personality(self, memory: MemoryEngine):
        """Test that THINK operation uses agent personality."""
        bank_id = unique_agent_id("test_think")

        personality = {
            "openness": 0.9,
            "conscientiousness": 0.2,
            "extraversion": 0.8,
            "agreeableness": 0.1,
            "neuroticism": 0.7,
            "bias_strength": 0.9,
        }
        await memory.update_bank_personality(bank_id, personality)

        await memory.merge_bank_background(
            bank_id,
            "I am a creative artist who values innovation over tradition",
            update_personality=False
        )

        await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {"content": "Traditional painting techniques have been used for centuries"},
                {"content": "Modern digital art is changing the art world"}
            ],
            document_id="art_facts"
        )

        result = await memory.reflect_async(
            bank_id=bank_id,
            query="What do you think about traditional vs modern art?",
            budget=Budget.LOW
        )

        assert result.text is not None
        assert len(result.text) > 0
