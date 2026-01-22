"""Tests for directive functionality.

Directives are hard rules injected into prompts.
They are stored in the 'directives' table.
"""

import uuid

import pytest

from hindsight_api.engine.memory_engine import MemoryEngine


@pytest.fixture
async def memory_with_bank(memory: MemoryEngine, request_context):
    """Memory engine with a bank that has some data.

    Uses a unique bank_id to avoid conflicts between parallel tests.
    """
    # Use unique bank_id to avoid conflicts between parallel tests
    bank_id = f"test-directives-{uuid.uuid4().hex[:8]}"

    # Ensure bank exists
    await memory.get_bank_profile(bank_id, request_context=request_context)

    # Add some test data
    await memory.retain_batch_async(
        bank_id=bank_id,
        contents=[
            {"content": "The team has daily standups at 9am where everyone shares their progress."},
            {"content": "Alice is the frontend engineer and specializes in React."},
            {"content": "Bob is the backend engineer and owns the API services."},
        ],
        request_context=request_context,
    )

    # Wait for any background tasks from retain to complete
    await memory.wait_for_background_tasks()

    yield memory, bank_id

    # Cleanup
    await memory.delete_bank(bank_id, request_context=request_context)


class TestBankMission:
    """Test bank mission operations."""

    async def test_set_and_get_mission(self, memory: MemoryEngine, request_context):
        """Test setting and getting a bank's mission."""
        bank_id = f"test-mission-{uuid.uuid4().hex[:8]}"

        # Set mission
        result = await memory.set_bank_mission(
            bank_id=bank_id,
            mission="Track customer feedback",
            request_context=request_context,
        )

        assert result["bank_id"] == bank_id
        assert result["mission"] == "Track customer feedback"

        # Get mission via profile
        profile = await memory.get_bank_profile(bank_id=bank_id, request_context=request_context)
        assert profile["mission"] == "Track customer feedback"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestDirectives:
    """Test directive functionality."""

    async def test_create_directive(self, memory: MemoryEngine, request_context):
        """Test creating a directive."""
        bank_id = f"test-directive-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create a directive
        directive = await memory.create_directive(
            bank_id=bank_id,
            name="Competitor Policy",
            content="Never mention competitor product names directly. If asked about competitors, redirect to our features.",
            request_context=request_context,
        )

        assert directive["name"] == "Competitor Policy"
        assert "Never mention competitor" in directive["content"]
        assert directive["is_active"] is True
        assert directive["priority"] == 0

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    async def test_directive_crud(self, memory: MemoryEngine, request_context):
        """Test basic CRUD operations for directives."""
        bank_id = f"test-directive-crud-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create
        directive = await memory.create_directive(
            bank_id=bank_id,
            name="Test Directive",
            content="Follow this rule",
            request_context=request_context,
        )
        directive_id = directive["id"]

        # Read
        retrieved = await memory.get_directive(
            bank_id=bank_id,
            directive_id=directive_id,
            request_context=request_context,
        )
        assert retrieved is not None
        assert retrieved["name"] == "Test Directive"
        assert retrieved["content"] == "Follow this rule"

        # List
        directives = await memory.list_directives(
            bank_id=bank_id,
            request_context=request_context,
        )
        assert len(directives) == 1
        assert directives[0]["id"] == directive_id

        # Update
        updated = await memory.update_directive(
            bank_id=bank_id,
            directive_id=directive_id,
            content="Updated rule content",
            request_context=request_context,
        )
        assert updated["content"] == "Updated rule content"

        # Delete
        deleted = await memory.delete_directive(
            bank_id=bank_id,
            directive_id=directive_id,
            request_context=request_context,
        )
        assert deleted is True

        # Verify deletion
        retrieved_after = await memory.get_directive(
            bank_id=bank_id,
            directive_id=directive_id,
            request_context=request_context,
        )
        assert retrieved_after is None

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    async def test_directive_priority(self, memory: MemoryEngine, request_context):
        """Test that directive priority works correctly."""
        bank_id = f"test-directive-priority-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create directives with different priorities
        await memory.create_directive(
            bank_id=bank_id,
            name="Low Priority",
            content="Low priority rule",
            priority=1,
            request_context=request_context,
        )

        await memory.create_directive(
            bank_id=bank_id,
            name="High Priority",
            content="High priority rule",
            priority=10,
            request_context=request_context,
        )

        # List should order by priority (desc)
        directives = await memory.list_directives(
            bank_id=bank_id,
            request_context=request_context,
        )
        assert len(directives) == 2
        assert directives[0]["name"] == "High Priority"
        assert directives[1]["name"] == "Low Priority"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    async def test_directive_is_active(self, memory: MemoryEngine, request_context):
        """Test that inactive directives are filtered by default."""
        bank_id = f"test-directive-active-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create active and inactive directives
        await memory.create_directive(
            bank_id=bank_id,
            name="Active Rule",
            content="This is active",
            is_active=True,
            request_context=request_context,
        )

        await memory.create_directive(
            bank_id=bank_id,
            name="Inactive Rule",
            content="This is inactive",
            is_active=False,
            request_context=request_context,
        )

        # List active only (default)
        active_directives = await memory.list_directives(
            bank_id=bank_id,
            active_only=True,
            request_context=request_context,
        )
        assert len(active_directives) == 1
        assert active_directives[0]["name"] == "Active Rule"

        # List all
        all_directives = await memory.list_directives(
            bank_id=bank_id,
            active_only=False,
            request_context=request_context,
        )
        assert len(all_directives) == 2

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestDirectiveTags:
    """Test tags functionality for directives."""

    async def test_directive_with_tags(self, memory: MemoryEngine, request_context):
        """Test creating a directive with tags."""
        bank_id = f"test-directive-tags-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create a directive with tags
        directive = await memory.create_directive(
            bank_id=bank_id,
            name="Tagged Rule",
            content="Follow this rule",
            tags=["project-a", "team-x"],
            request_context=request_context,
        )

        assert directive["tags"] == ["project-a", "team-x"]

        # Retrieve and verify tags
        retrieved = await memory.get_directive(
            bank_id=bank_id,
            directive_id=directive["id"],
            request_context=request_context,
        )
        assert retrieved["tags"] == ["project-a", "team-x"]

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)

    async def test_list_directives_by_tags(self, memory: MemoryEngine, request_context):
        """Test listing directives filtered by tags."""
        bank_id = f"test-directive-tags-list-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Create directives with different tags
        await memory.create_directive(
            bank_id=bank_id,
            name="Rule A",
            content="Rule for project A",
            tags=["project-a"],
            request_context=request_context,
        )

        await memory.create_directive(
            bank_id=bank_id,
            name="Rule B",
            content="Rule for project B",
            tags=["project-b"],
            request_context=request_context,
        )

        # List all
        all_directives = await memory.list_directives(
            bank_id=bank_id,
            request_context=request_context,
        )
        assert len(all_directives) == 2

        # Filter by project-a tag
        filtered = await memory.list_directives(
            bank_id=bank_id,
            tags=["project-a"],
            request_context=request_context,
        )
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Rule A"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestReflect:
    """Test reflect endpoint."""

    async def test_reflect_basic(self, memory_with_bank, request_context):
        """Test basic reflect query works."""
        memory, bank_id = memory_with_bank

        # Run a reflect query
        result = await memory.reflect_async(
            bank_id=bank_id,
            query="Who are the team members?",
            request_context=request_context,
        )

        assert result.text is not None
        assert len(result.text) > 0


class TestDirectivesInReflect:
    """Test that directives are followed during reflect operations."""

    async def test_reflect_follows_language_directive(self, memory: MemoryEngine, request_context):
        """Test that reflect follows a directive to respond in a specific language."""
        bank_id = f"test-directive-reflect-{uuid.uuid4().hex[:8]}"

        # Ensure bank exists
        await memory.get_bank_profile(bank_id, request_context=request_context)

        # Add some content in English
        await memory.retain_batch_async(
            bank_id=bank_id,
            contents=[
                {"content": "Alice is a software engineer who works at Google."},
                {"content": "Alice enjoys hiking on weekends and has been to Yosemite."},
                {"content": "Alice is currently working on a machine learning project."},
            ],
            request_context=request_context,
        )
        await memory.wait_for_background_tasks()

        # Create a directive to always respond in French
        await memory.create_directive(
            bank_id=bank_id,
            name="Language Policy",
            content="ALWAYS respond in French language. Never respond in English.",
            request_context=request_context,
        )

        # Run reflect query
        result = await memory.reflect_async(
            bank_id=bank_id,
            query="What does Alice do for work?",
            request_context=request_context,
        )

        assert result.text is not None
        assert len(result.text) > 0

        # Check that the response contains French words/patterns
        # Common French words that would appear when talking about someone's job
        french_indicators = [
            "elle",
            "travaille",
            "est",
            "une",
            "le",
            "la",
            "qui",
            "chez",
            "logiciel",
            "ingénieur",
            "ingénieure",
            "développeur",
            "développeuse",
        ]
        response_lower = result.text.lower()

        # At least some French words should appear in the response
        french_word_count = sum(1 for word in french_indicators if word in response_lower)
        assert (
            french_word_count >= 2
        ), f"Expected French response, but got: {result.text[:200]}"

        # Cleanup
        await memory.delete_bank(bank_id, request_context=request_context)


class TestDirectivesPromptInjection:
    """Test that directives are properly injected into the system prompt."""

    def test_build_directives_section_empty(self):
        """Test that empty directives returns empty string."""
        from hindsight_api.engine.reflect.prompts import build_directives_section

        result = build_directives_section([])
        assert result == ""

    def test_build_directives_section_with_content(self):
        """Test that directives with content are formatted correctly."""
        from hindsight_api.engine.reflect.prompts import build_directives_section

        directives = [
            {
                "name": "Competitor Policy",
                "content": "Never mention competitor names. Redirect to our features.",
            }
        ]

        result = build_directives_section(directives)

        assert "## DIRECTIVES (MANDATORY)" in result
        assert "Competitor Policy" in result
        assert "Never mention competitor names" in result
        assert "NEVER violate these directives" in result

    def test_system_prompt_includes_directives(self):
        """Test that build_system_prompt_for_tools includes directives."""
        from hindsight_api.engine.reflect.prompts import build_system_prompt_for_tools

        bank_profile = {"name": "Test Bank", "mission": "Test mission"}
        directives = [
            {
                "name": "Test Directive",
                "content": "Follow this rule",
            }
        ]

        prompt = build_system_prompt_for_tools(
            bank_profile=bank_profile,
            directives=directives,
        )

        assert "## DIRECTIVES (MANDATORY)" in prompt
        assert "Follow this rule" in prompt
        # Directives should appear before CRITICAL RULES
        directives_pos = prompt.find("## DIRECTIVES")
        critical_rules_pos = prompt.find("## CRITICAL RULES")
        assert directives_pos < critical_rules_pos
