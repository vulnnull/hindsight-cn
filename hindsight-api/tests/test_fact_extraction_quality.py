"""
Test suite for fact extraction quality verification.

This comprehensive test suite validates that the fact extraction system:
1. Preserves all information dimensions (emotional, sensory, cognitive, etc.)
2. Correctly converts relative dates to absolute dates
3. Properly classifies facts as agent vs world
4. Makes logical inferences to connect related information
5. Correctly attributes statements to speakers
6. Filters out irrelevant content (podcast intros/outros)

These are quality/accuracy tests that verify the LLM-based extraction
produces semantically correct and complete facts.
"""
import pytest
import re
from datetime import datetime, timezone
from hindsight_api.engine.fact_extraction import extract_facts_from_text
from hindsight_api import LLMConfig


# =============================================================================
# DIMENSION PRESERVATION TESTS
# =============================================================================

class TestDimensionPreservation:
    """Tests that fact extraction preserves all information dimensions."""

    @pytest.mark.asyncio
    async def test_emotional_dimension_preservation(self):
        """
        Test that emotional states and feelings are preserved, not stripped away.

        Example: "I was thrilled to receive positive feedback"
        Should NOT become: "I received positive feedback"
        """
        text = """
I was absolutely thrilled when I received such positive feedback on my presentation!
Sarah seemed disappointed when she heard the news about the delay.
Marcus felt anxious about the upcoming interview.
"""

        context = "Personal journal entry"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        emotional_indicators = ["thrilled", "disappointed", "anxious", "positive feedback"]
        found_emotions = [word for word in emotional_indicators if word in all_facts_text]

        assert len(found_emotions) >= 2, (
            f"Should preserve emotional dimension. "
            f"Found: {found_emotions}, Expected at least 2 from: {emotional_indicators}"
        )

    @pytest.mark.asyncio
    async def test_sensory_dimension_preservation(self):
        """Test that sensory details (visual, auditory, etc.) are preserved."""
        text = """
The coffee tasted bitter and burnt.
She showed me her bright orange hair, which looked stunning under the lights.
The music was so loud I could barely hear myself think.
"""

        context = "Personal experience"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        sensory_indicators = ["bitter", "burnt", "bright orange", "loud", "stunning"]
        found_sensory = [word for word in sensory_indicators if word in all_facts_text]

        assert len(found_sensory) >= 2, (
            f"Should preserve sensory details. "
            f"Found: {found_sensory}, Expected at least 2 from: {sensory_indicators}"
        )

    @pytest.mark.asyncio
    async def test_cognitive_epistemic_dimension(self):
        """Test that cognitive states and certainty levels are preserved."""
        text = """
I realized that the approach wasn't working.
She wasn't sure if the meeting would happen.
He's convinced that AI will transform healthcare.
Maybe we should reconsider the timeline.
"""

        context = "Team discussion"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        cognitive_indicators = ["realized", "wasn't sure", "convinced", "maybe", "reconsider"]
        found_cognitive = [word for word in cognitive_indicators if word in all_facts_text]

        assert len(found_cognitive) >= 2, (
            f"Should preserve cognitive/epistemic dimension. "
            f"Found: {found_cognitive}"
        )

    @pytest.mark.asyncio
    async def test_capability_skill_dimension(self):
        """Test that capabilities, skills, and limitations are preserved."""
        text = """
I can speak French fluently.
Sarah struggles with public speaking.
He's an expert in machine learning.
I'm unable to attend the conference due to scheduling conflicts.
"""

        context = "Personal profile discussion"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        capability_indicators = ["can speak", "fluently", "struggles with", "expert in", "unable to"]
        found_capability = [word for word in capability_indicators if word in all_facts_text]

        assert len(found_capability) >= 2, (
            f"Should preserve capability/skill dimension. "
            f"Found: {found_capability}"
        )

    @pytest.mark.asyncio
    async def test_comparative_dimension(self):
        """Test that comparisons and contrasts are preserved."""
        text = """
This approach is much better than the previous one.
The new design is worse than expected.
Unlike last year, we're ahead of schedule.
"""

        context = "Project review"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        comparative_indicators = ["better than", "worse than", "unlike", "ahead of"]
        found_comparative = [word for word in comparative_indicators if word in all_facts_text]

        assert len(found_comparative) >= 1, (
            f"Should preserve comparative dimension. "
            f"Found: {found_comparative}"
        )

    @pytest.mark.asyncio
    async def test_attitudinal_reactive_dimension(self):
        """Test that attitudes and reactions are preserved."""
        text = """
She's very skeptical about the new technology.
I was surprised when he announced his resignation.
Marcus rolled his eyes when the topic came up.
She's enthusiastic about the opportunity.
"""

        context = "Team meeting"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        attitudinal_indicators = ["skeptical", "surprised", "rolled his eyes", "enthusiastic"]
        found_attitudinal = [word for word in attitudinal_indicators if word in all_facts_text]

        assert len(found_attitudinal) >= 2, (
            f"Should preserve attitudinal/reactive dimension. "
            f"Found: {found_attitudinal}"
        )

    @pytest.mark.asyncio
    async def test_intentional_motivational_dimension(self):
        """Test that goals, plans, and motivations are preserved."""
        text = """
I want to learn Mandarin before my trip to China.
She aims to complete her PhD within three years.
His goal is to build a sustainable business.
I'm planning to switch careers because I'm not fulfilled in my current role.
"""

        context = "Personal goals discussion"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        intentional_indicators = ["want to", "aims to", "goal is", "planning to", "because"]
        found_intentional = [word for word in intentional_indicators if word in all_facts_text]

        assert len(found_intentional) >= 2, (
            f"Should preserve intentional/motivational dimension. "
            f"Found: {found_intentional}"
        )

    @pytest.mark.asyncio
    async def test_evaluative_preferential_dimension(self):
        """Test that preferences and values are preserved."""
        text = """
I prefer working remotely to being in an office.
She values honesty above all else.
He hates being late to meetings.
Family is the most important thing to her.
"""

        context = "Personal values discussion"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        evaluative_indicators = ["prefer", "values", "hates", "important", "above all"]
        found_evaluative = [word for word in evaluative_indicators if word in all_facts_text]

        assert len(found_evaluative) >= 2, (
            f"Should preserve evaluative/preferential dimension. "
            f"Found: {found_evaluative}"
        )

    @pytest.mark.asyncio
    async def test_comprehensive_multi_dimension(self):
        """Test a realistic scenario with multiple dimensions in one fact."""
        text = """
I was thrilled to receive such positive feedback on my presentation yesterday!
I wasn't sure if my approach would resonate, but the audience seemed enthusiastic.
I prefer presenting in person rather than virtually because I can read the room better.
"""

        context = "Personal reflection"
        llm_config = LLMConfig.for_memory()

        event_date = datetime(2024, 11, 13)

        facts = await extract_facts_from_text(
            text=text,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        # Check emotional
        assert "thrilled" in all_facts_text or "positive feedback" in all_facts_text, \
            "Should preserve emotional dimension (thrilled)"

        # Check no vague temporal terms
        prohibited_terms = ["recently", "soon", "lately"]
        found_prohibited = [term for term in prohibited_terms if term in all_facts_text]
        assert len(found_prohibited) == 0, \
            f"Should NOT use vague temporal terms. Found: {found_prohibited}"

        # Check cognitive uncertainty
        assert "wasn't sure" in all_facts_text or "unsure" in all_facts_text or "uncertain" in all_facts_text, \
            "Should preserve cognitive uncertainty"

        # Check preference
        assert "prefer" in all_facts_text or "rather than" in all_facts_text, \
            "Should preserve preferential dimension"


# =============================================================================
# TEMPORAL CONVERSION TESTS
# =============================================================================

class TestTemporalConversion:
    """Tests for temporal extraction and date conversion."""

    @pytest.mark.asyncio
    async def test_temporal_absolute_conversion(self):
        """
        Test that relative temporal expressions are converted to absolute dates.

        Critical: "yesterday" should become "on November 12, 2024", NOT "recently"
        """
        text = """
Yesterday I went for a morning jog for the first time in a nearby park.
Last week I started a new project.
I'm planning to visit Tokyo next month.
"""

        context = "Personal conversation"
        llm_config = LLMConfig.for_memory()

        event_date = datetime(2024, 11, 13)

        facts = await extract_facts_from_text(
            text=text,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        # Should NOT contain vague temporal terms
        prohibited_terms = ["recently", "soon", "lately", "a while ago", "some time ago"]
        found_prohibited = [term for term in prohibited_terms if term in all_facts_text]

        assert len(found_prohibited) == 0, (
            f"Should NOT use vague temporal terms. Found: {found_prohibited}"
        )

        # Should contain specific date references
        temporal_indicators = ["november", "12", "early november", "week of", "december"]
        found_temporal = [term for term in temporal_indicators if term in all_facts_text]

        assert len(found_temporal) >= 1, (
            f"Should convert relative dates to absolute. "
            f"Found: {found_temporal}, Expected month/date references"
        )

    @pytest.mark.asyncio
    async def test_date_field_calculation_last_night(self):
        """
        Test that the date field is calculated correctly for "last night" events.

        CRITICAL: If conversation is on August 14, 2023 and text says "last night",
        the date field should be August 13, NOT August 14.
        """
        text = """
Melanie: Hey Caroline! Last night was amazing! We celebrated my daughter's birthday
with a concert surrounded by music, joy and the warm summer breeze.
"""

        context = "Conversation between Melanie and Caroline"
        llm_config = LLMConfig.for_memory()

        event_date = datetime(2023, 8, 14, 14, 24)

        facts = await extract_facts_from_text(
            text=text,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name="Melanie"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. Date: {f['occurred_start']} - {f['fact']}")

        birthday_fact = None
        for fact in facts:
            if "birthday" in fact['fact'].lower() or "concert" in fact['fact'].lower():
                birthday_fact = fact
                break

        assert birthday_fact is not None, "Should extract fact about birthday celebration"

        fact_date_str = birthday_fact['occurred_start']

        if 'T' in fact_date_str:
            fact_date = datetime.fromisoformat(fact_date_str.replace('Z', '+00:00'))
        else:
            fact_date = datetime.fromisoformat(fact_date_str)

        assert fact_date.year == 2023, "Year should be 2023"
        assert fact_date.month == 8, "Month should be August"
        assert fact_date.day == 13, (
            f"Day should be 13 (last night relative to Aug 14), but got {fact_date.day}. "
            f"Date field should be when FACT occurred, not when mentioned!"
        )

    @pytest.mark.asyncio
    async def test_date_field_calculation_yesterday(self):
        """Test that the date field is calculated correctly for "yesterday" events."""
        text = """
Yesterday I went for a morning jog for the first time in a nearby park.
"""

        context = "Personal diary"
        llm_config = LLMConfig.for_memory()

        event_date = datetime(2024, 11, 13)

        facts = await extract_facts_from_text(
            text=text,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. Date: {f['occurred_start']} - {f['fact']}")

        jogging_fact = facts[0]

        fact_date_str = jogging_fact['occurred_start']
        if 'T' in fact_date_str:
            fact_date = datetime.fromisoformat(fact_date_str.replace('Z', '+00:00'))
        else:
            fact_date = datetime.fromisoformat(fact_date_str)

        assert fact_date.year == 2024, "Year should be 2024"
        assert fact_date.month == 11, "Month should be November"
        assert fact_date.day == 12, (
            f"Day should be 12 (yesterday relative to Nov 13), but got {fact_date.day}. "
            f"Date field: {fact_date_str}"
        )

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        assert "first time" in all_facts_text or "first" in all_facts_text, \
            "Should preserve 'first time' qualifier"

        assert "recently" not in all_facts_text, \
            "Should NOT convert 'yesterday' to 'recently'"

        assert any(term in all_facts_text for term in ["november", "12", "nov"]), \
            "Should convert 'yesterday' to absolute date in fact text"

    @pytest.mark.asyncio
    async def test_extract_facts_with_relative_dates(self):
        """Test that relative dates are converted to absolute dates."""

        reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)
        llm_config = LLMConfig.for_memory()

        text = """
        Yesterday I went hiking in Yosemite.
        Last week I started my new job at Google.
        This morning I had coffee with Alice.
        """

        facts = await extract_facts_from_text(
            text=text,
            event_date=reference_date,
            llm_config=llm_config,
            agent_name="TestUser",
            context="Personal diary"
        )

        print(f"\nExtracted {len(facts)} facts:")
        for fact in facts:
            print(f"- {fact['fact']}")
            print(f"  Date: {fact['occurred_start']}")

        assert len(facts) > 0, "Should extract at least one fact"

        for fact in facts:
            assert 'fact' in fact, "Each fact should have 'fact' field"
            assert 'occurred_start' in fact, "Each fact should have 'occurred_start' field"
            assert fact['occurred_start'], f"Date should not be empty for fact: {fact['fact']}"

        dates = [f['occurred_start'] for f in facts]
        unique_dates = set(dates)
        if len(facts) >= 3:
            assert len(unique_dates) >= 2, "Should have different dates for different temporal facts"

        print(f"\n All facts have absolute dates")

    @pytest.mark.asyncio
    async def test_extract_facts_with_no_temporal_info(self):
        """Test that facts without temporal info use the reference date."""

        reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)
        llm_config = LLMConfig.for_memory()

        text = "Alice works at Google. She loves Python programming."

        facts = await extract_facts_from_text(
            text=text,
            event_date=reference_date,
            llm_config=llm_config,
            agent_name="TestUser",
            context="General info"
        )

        print(f"\nExtracted {len(facts)} facts:")
        for fact in facts:
            print(f"- {fact['fact']}")
            print(f"  Date: {fact['occurred_start']}")

        assert len(facts) > 0, "Should extract at least one fact"

        for fact in facts:
            assert fact['occurred_start'], f"Fact should have a date: {fact['fact']}"

    @pytest.mark.asyncio
    async def test_extract_facts_with_absolute_dates(self):
        """Test that absolute dates in text are preserved."""

        reference_date = datetime(2024, 3, 20, 14, 0, 0, tzinfo=timezone.utc)
        llm_config = LLMConfig.for_memory()

        text = """
        On March 15, 2024, Alice joined Google.
        Bob will start his vacation on April 1st.
        """

        facts = await extract_facts_from_text(
            text=text,
            event_date=reference_date,
            llm_config=llm_config,
            agent_name="TestUser",
            context="Calendar events"
        )

        print(f"\nExtracted {len(facts)} facts:")
        for fact in facts:
            print(f"- {fact['fact']}")
            print(f"  Date: {fact['occurred_start']}")

        assert len(facts) > 0, "Should extract at least one fact"

        for fact in facts:
            assert fact['occurred_start'], f"Fact should have a date: {fact['fact']}"


# =============================================================================
# LOGICAL INFERENCE TESTS
# =============================================================================

class TestLogicalInference:
    """Tests that the system makes logical inferences to connect related information."""

    @pytest.mark.asyncio
    async def test_logical_inference_identity_connection(self):
        """
        Test that the system makes logical inferences to connect related information.

        Example: "I lost a friend" + "this photo with Karlie" -> "I lost my friend Karlie"
        """
        text = """
Deborah: The roses and dahlias bring me peace. I lost a friend last week,
so I've been spending time in the garden to find some comfort.

Jolene: Sorry to hear about your friend, Deb. Losing someone can be really tough.
How are you holding up?

Deborah: Thanks for the kind words. It's been tough, but I'm comforted by
remembering our time together. It reminds me of how special life is.

Jolene: Memories can give us so much comfort and joy.

Deborah: Memories keep our loved ones close. This is the last photo with Karlie
which was taken last summer when we hiked. It was our last one. We had such a
great time! Every time I see it, I can't help but smile.
"""

        context = "Conversation between Deborah and Jolene"
        llm_config = LLMConfig.for_memory()

        event_date = datetime(2023, 2, 23)

        facts = await extract_facts_from_text(
            text=text,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name="Deborah"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        has_karlie = "karlie" in all_facts_text
        has_loss = any(word in all_facts_text for word in ["lost", "death", "passed", "died", "losing"])

        assert has_karlie, "Should mention Karlie in the extracted facts"
        assert has_loss, "Should mention the loss/death in the extracted facts"

        connected_fact_found = False
        for fact in facts:
            fact_text = fact['fact'].lower()
            if "karlie" in fact_text and any(word in fact_text for word in ["lost", "death", "passed", "died", "losing"]):
                connected_fact_found = True
                print(f"\n Found connected fact: {fact['fact']}")
                break

        assert connected_fact_found, (
            "Should connect 'lost a friend' with 'Karlie' in the same fact. "
            f"The inference should be: Karlie is the lost friend. "
            f"Facts: {[f['fact'] for f in facts]}"
        )

    @pytest.mark.asyncio
    async def test_logical_inference_pronoun_resolution(self):
        """
        Test that pronouns are resolved to their referents.

        Example: "I started a project" + "It's challenging" -> "The project is challenging"
        """
        text = """
I started a new machine learning project last month.
It's been really challenging but very rewarding.
I've learned so much from it.
"""

        context = "Personal update"
        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            context=context,
            llm_config=llm_config,
            agent_name="TestUser"
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. {f['fact']}")

        all_facts_text = " ".join([f['fact'].lower() for f in facts])

        has_project = "project" in all_facts_text
        has_qualities = any(word in all_facts_text for word in ["challenging", "rewarding", "learned"])

        assert has_project, "Should mention the project"
        assert has_qualities, "Should mention the qualities/learning"

        connected_fact_found = False
        for fact in facts:
            fact_text = fact['fact'].lower()
            if "project" in fact_text and any(word in fact_text for word in ["challenging", "rewarding"]):
                connected_fact_found = True
                print(f"\n Found connected fact: {fact['fact']}")
                break

        assert connected_fact_found, (
            "Should resolve 'it' to 'the project' and connect characteristics in the same fact. "
            f"Facts: {[f['fact'] for f in facts]}"
        )


# =============================================================================
# FACT CLASSIFICATION TESTS
# =============================================================================

class TestFactClassification:
    """Tests that facts are correctly classified as agent vs world."""

    @pytest.mark.asyncio
    async def test_agent_facts_from_podcast_transcript(self):
        """
        Test that when context identifies someone as 'you', their actions are classified as agent facts.

        This test addresses the issue where podcast transcripts with context like
        "this was podcast episode between you (Marcus) and Jamie" were extracting
        all facts as 'world' instead of properly identifying Marcus's statements as 'bank'.
        """

        transcript = """
Marcus: I've been working on AI safety research for the past six months.
Jamie: That's really interesting! What specifically are you focusing on?
Marcus: I'm investigating interpretability methods. I believe we need to understand
how models make decisions before we can trust them in critical applications.
Jamie: I completely agree with that approach.
Marcus: I published a paper on this topic last month, and I'm presenting it at
the conference next week.
Jamie: Congratulations! I'd love to read it.
"""

        context = "Podcast episode between you (Marcus) and Jamie discussing AI research"

        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=transcript,
            event_date=datetime(2024, 11, 13),
            llm_config=llm_config,
            agent_name="Marcus",
            context=context
        )

        assert len(facts) > 0, "Should extract at least one fact from the transcript"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. [{f['fact_type']}] {f['fact']}")

        agent_facts = [f for f in facts if f["fact_type"] == "agent"]

        assert len(agent_facts) > 0, \
            f"Should have at least one 'bank' fact when context identifies 'you (Marcus)'. " \
            f"Got facts: {[f['fact'] + ' [' + f['fact_type'] + ']' for f in facts]}"

        for agent_fact in agent_facts:
            fact_text = agent_fact["fact"]
            assert fact_text.startswith("I ") or " I " in fact_text, \
                f"Agent facts must use first person ('I'). Got: {fact_text}"

            third_person_pattern = r'\bMarcus\s+(said|worked|has|published|explained|believes|attended|completed)'
            match = re.search(third_person_pattern, fact_text)
            assert not match, \
                f"Agent facts should use first person, not third person. " \
                f"Found '{match.group()}' in: {fact_text}"

        print(f"\n All {len(agent_facts)} agent facts use first person ('I')")

        jamie_facts = [f for f in facts if "Jamie" in f["fact"] and "Jamie" == f["fact"].split()[0]]
        if jamie_facts:
            world_jamie_facts = [f for f in jamie_facts if f["fact_type"] == "world"]
            assert len(world_jamie_facts) > 0, \
                f"Jamie's statements should be 'world' facts. " \
                f"Jamie facts: {[f['fact'] + ' [' + f['fact_type'] + ']' for f in jamie_facts]}"

        print(f"\n Successfully classified {len(agent_facts)} agent facts and {len([f for f in facts if f['fact_type'] == 'world'])} world facts")

    @pytest.mark.asyncio
    async def test_agent_facts_without_explicit_context(self):
        """Test that when 'you' is used in the text itself, it gets properly classified."""

        text = """
I completed the project on machine learning interpretability last week.
My colleague Sarah helped me with the data analysis.
We presented our findings to the team yesterday.
"""

        context = "Personal work log"

        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=text,
            event_date=datetime(2024, 11, 13),
            llm_config=llm_config,
            agent_name="TestUser",
            context=context
        )

        assert len(facts) > 0, "Should extract facts"

        agent_facts = [f for f in facts if f["fact_type"] == "agent"]

        print(f"\n Extracted {len(facts)} total facts")
        print(f"Agent facts: {len(agent_facts)}")
        print(f"World facts: {len([f for f in facts if f['fact_type'] == 'world'])}")

        if agent_facts:
            print(f"\nAgent facts found:")
            for f in agent_facts:
                print(f"  - {f['fact']}")

    @pytest.mark.asyncio
    async def test_speaker_attribution_predictions(self):
        """
        Test that predictions made by different speakers are correctly attributed.

        This addresses the issue where Jamie's prediction of "Niners 27-13" was being
        incorrectly attributed to Marcus (the agent) in the extracted facts.
        """

        transcript = """
Marcus: [excited] I'm calling it now, Rams will win twenty seven to twenty four, their defense is too strong!
Jamie: [laughs] No way, I predict the Niners will win twenty seven to thirteen, comfy win at home.
Marcus: [angry] That's ridiculous, I stand by my Rams prediction.
Jamie: [teasing] We'll see who's right, my Niners pick is solid.
"""

        context = "podcast episode on match prediction of week 10 - Marcus (you) and Jamie - 14 nov"
        agent_name = "Marcus"

        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=transcript,
            event_date=datetime(2024, 11, 14),
            context=context,
            llm_config=llm_config,
            agent_name=agent_name
        )

        assert len(facts) > 0, "Should extract at least one fact"

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. [{f['fact_type']}] {f['fact']}")

        agent_facts = [f for f in facts if f["fact_type"] == "agent"]
        jamie_facts = [f for f in facts if f["fact_type"] == "world" and "Jamie" in f["fact"]]

        print(f"\nAgent facts (Marcus): {len(agent_facts)}")
        for f in agent_facts:
            print(f"  - {f['fact']}")

        print(f"\nWorld facts (Jamie): {len(jamie_facts)}")
        for f in jamie_facts:
            print(f"  - {f['fact']}")

        agent_facts_text = " ".join([f["fact"].lower() for f in agent_facts])

        assert "rams" in agent_facts_text or "twenty seven to twenty four" in agent_facts_text or "27" in agent_facts_text, \
            f"Agent facts should contain Marcus's Rams prediction. Agent facts: {[f['fact'] for f in agent_facts]}"

        has_niners_27_13 = False
        for fact in agent_facts:
            fact_lower = fact["fact"].lower()
            if ("niners" in fact_lower or "49ers" in fact_lower) and ("27" in fact_lower or "twenty seven") and ("13" in fact_lower or "thirteen"):
                has_niners_27_13 = True
                print(f"\n ERROR: Found Jamie's Niners 27-13 prediction in agent facts: {fact['fact']}")

        assert not has_niners_27_13, \
            f"Agent facts should NOT contain Jamie's Niners 27-13 prediction! " \
            f"Agent facts: {[f['fact'] for f in agent_facts]}"

        if jamie_facts:
            print(f"\n Jamie facts correctly classified as world facts")

        print(f"\n Speaker attribution test passed: Predictions correctly attributed to their speakers")

    @pytest.mark.asyncio
    async def test_skip_podcast_meta_commentary(self):
        """
        Test that podcast intros, outros, and calls to action are skipped.

        This addresses the issue where podcast outros like "that's all for today,
        don't forget to subscribe" were being extracted as facts.
        """

        transcript = """
Marcus: Welcome everyone to today's episode! Before we dive in, don't forget to
subscribe and leave a rating.

Marcus: Today I want to talk about my research on interpretability in AI systems.
I've been working on this for about a year now.

Jamie: That sounds really interesting! What made you focus on that area?

Marcus: I believe it's crucial for AI safety. We need to understand how these
models make decisions before we can trust them in critical applications.

Jamie: I completely agree with that approach.

Marcus: Well, I think that's gonna do it for us today! Thanks for listening everyone.
Don't forget to tap follow or subscribe, tell a friend, and drop a quick rating
so the algorithm learns to box out. See you next week!
"""

        context = "Podcast episode between you (Marcus) and Jamie about AI"

        llm_config = LLMConfig.for_memory()

        facts = await extract_facts_from_text(
            text=transcript,
            event_date=datetime(2024, 11, 13),
            llm_config=llm_config,
            agent_name="Marcus",
            context=context
        )

        print(f"\nExtracted {len(facts)} facts:")
        for i, f in enumerate(facts):
            print(f"{i+1}. [{f['fact_type']}] {f['fact']}")

        assert len(facts) > 0, "Should extract at least one fact"

        meta_phrases = [
            "subscribe",
            "leave a rating",
            "tap follow",
            "tell a friend",
            "that's gonna do it",
            "thanks for listening",
            "see you next week",
            "welcome everyone",
            "before we dive in"
        ]

        for fact in facts:
            fact_lower = fact["fact"].lower()
            for phrase in meta_phrases:
                assert phrase not in fact_lower, \
                    f"Fact should not contain meta-commentary phrase '{phrase}'. " \
                    f"Found in: {fact['fact']}"

        content_facts = [f for f in facts if "interpretability" in f["fact"].lower()]
        assert len(content_facts) > 0, \
            "Should extract facts about the actual content discussed (interpretability)"

        print(f"\n Successfully filtered out meta-commentary")
        print(f" Extracted {len(content_facts)} facts about actual content")


# =============================================================================
# PERSONALITY INFERENCE TESTS
# =============================================================================

class TestPersonalityInference:
    """Tests for LLM-based personality trait inference from background."""

    @pytest.mark.asyncio
    async def test_background_merge_with_personality_inference(self, memory):
        """Test that background merge infers personality traits by default."""
        import uuid
        bank_id = f"test_infer_{uuid.uuid4().hex[:8]}"

        result = await memory.merge_bank_background(
            bank_id,
            "I am a creative software engineer who loves innovation and trying new technologies",
            update_personality=True
        )

        assert "background" in result
        assert "personality" in result

        background = result["background"]
        personality = result["personality"]

        assert "creative" in background.lower() or "innovation" in background.lower()

        assert "openness" in personality
        assert personality["openness"] > 0.5
        assert 0.0 <= personality["openness"] <= 1.0

        required_traits = ["openness", "conscientiousness", "extraversion",
                          "agreeableness", "neuroticism", "bias_strength"]
        for trait in required_traits:
            assert trait in personality
            assert 0.0 <= personality[trait] <= 1.0

    @pytest.mark.asyncio
    async def test_background_merge_without_personality_inference(self, memory):
        """Test that background merge skips personality inference when disabled."""
        import uuid
        bank_id = f"test_no_infer_{uuid.uuid4().hex[:8]}"

        initial_profile = await memory.get_bank_profile(bank_id)
        initial_personality = initial_profile["personality"]

        result = await memory.merge_bank_background(
            bank_id,
            "I am a data scientist",
            update_personality=False
        )

        assert "background" in result
        assert "personality" not in result

        final_profile = await memory.get_bank_profile(bank_id)
        final_personality = final_profile["personality"]

        assert initial_personality == final_personality

    @pytest.mark.asyncio
    async def test_personality_inference_for_organized_engineer(self, memory):
        """Test personality inference for organized/conscientious profile."""
        import uuid
        bank_id = f"test_organized_{uuid.uuid4().hex[:8]}"

        result = await memory.merge_bank_background(
            bank_id,
            "I am a methodical engineer who values organization and systematic planning",
            update_personality=True
        )

        personality = result["personality"]

        assert personality["conscientiousness"] > 0.5

    @pytest.mark.asyncio
    async def test_personality_inference_for_startup_founder(self, memory):
        """Test personality inference for entrepreneurial profile."""
        import uuid
        bank_id = f"test_founder_{uuid.uuid4().hex[:8]}"

        result = await memory.merge_bank_background(
            bank_id,
            "I am a startup founder who thrives on risk and social interaction",
            update_personality=True
        )

        personality = result["personality"]

        assert personality["openness"] > 0.5
        assert personality["extraversion"] > 0.5

    @pytest.mark.asyncio
    async def test_personality_updates_in_database(self, memory):
        """Test that inferred personality is actually stored in database."""
        import uuid
        bank_id = f"test_db_update_{uuid.uuid4().hex[:8]}"

        result = await memory.merge_bank_background(
            bank_id,
            "I am an innovative designer",
            update_personality=True
        )

        inferred_personality = result["personality"]

        profile = await memory.get_bank_profile(bank_id)
        db_personality = profile["personality"]

        assert db_personality == inferred_personality

    @pytest.mark.asyncio
    async def test_multiple_background_merges_update_personality(self, memory):
        """Test that each background merge can update personality."""
        import uuid
        bank_id = f"test_multi_merge_{uuid.uuid4().hex[:8]}"

        result1 = await memory.merge_bank_background(
            bank_id,
            "I am a software engineer",
            update_personality=True
        )
        personality1 = result1["personality"]

        result2 = await memory.merge_bank_background(
            bank_id,
            "I love creative problem solving and innovation",
            update_personality=True
        )
        personality2 = result2["personality"]

        assert "engineer" in result2["background"].lower() or "software" in result2["background"].lower()
        assert "creative" in result2["background"].lower() or "innovation" in result2["background"].lower()

    @pytest.mark.asyncio
    async def test_background_merge_conflict_resolution_with_personality(self, memory):
        """Test that conflicts are resolved and personality reflects final background."""
        import uuid
        bank_id = f"test_conflict_{uuid.uuid4().hex[:8]}"

        await memory.merge_bank_background(
            bank_id,
            "I was born in Colorado and prefer stability",
            update_personality=True
        )

        result = await memory.merge_bank_background(
            bank_id,
            "You were born in Texas and love taking risks",
            update_personality=True
        )

        background = result["background"]
        personality = result["personality"]

        assert "texas" in background.lower()
        assert personality["openness"] > 0.5