"""
Test that fact extraction correctly captures all information dimensions.

This test suite verifies that the fact extraction system properly preserves:
1. Emotional/Affective dimension
2. Sensory/Experiential dimension
3. Cognitive/Epistemic dimension
4. Intentional/Motivational dimension
5. Evaluative/Preferential dimension
6. Capability/Skill dimension
7. Attitudinal/Reactive dimension
8. Comparative/Relative dimension
9. Temporal dimension (with absolute date conversion)
"""
import pytest
from datetime import datetime
from memora.fact_extraction import extract_facts_from_text
from memora.llm_wrapper import LLMConfig


@pytest.mark.asyncio
async def test_emotional_dimension_preservation():
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

    # Check that emotional words are preserved
    all_facts_text = " ".join([f['fact'].lower() for f in facts])

    # Should preserve emotional intensity and specific emotions
    emotional_indicators = ["thrilled", "disappointed", "anxious", "positive feedback"]
    found_emotions = [word for word in emotional_indicators if word in all_facts_text]

    assert len(found_emotions) >= 2, (
        f"Should preserve emotional dimension. "
        f"Found: {found_emotions}, Expected at least 2 from: {emotional_indicators}"
    )


@pytest.mark.asyncio
async def test_temporal_absolute_conversion():
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

    # Event date is November 13, 2024
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

    # Should contain specific date references (either month names or dates)
    # For "yesterday" (Nov 12), "last week" (early Nov), "next month" (December)
    temporal_indicators = ["november", "12", "early november", "week of", "december"]
    found_temporal = [term for term in temporal_indicators if term in all_facts_text]

    assert len(found_temporal) >= 1, (
        f"Should convert relative dates to absolute. "
        f"Found: {found_temporal}, Expected month/date references"
    )


@pytest.mark.asyncio
async def test_sensory_dimension_preservation():
    """
    Test that sensory details (visual, auditory, etc.) are preserved.
    """
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

    # Should preserve sensory descriptors
    sensory_indicators = ["bitter", "burnt", "bright orange", "loud", "stunning"]
    found_sensory = [word for word in sensory_indicators if word in all_facts_text]

    assert len(found_sensory) >= 2, (
        f"Should preserve sensory details. "
        f"Found: {found_sensory}, Expected at least 2 from: {sensory_indicators}"
    )


@pytest.mark.asyncio
async def test_cognitive_epistemic_dimension():
    """
    Test that cognitive states and certainty levels are preserved.
    """
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

    # Should preserve cognitive/epistemic indicators
    cognitive_indicators = ["realized", "wasn't sure", "convinced", "maybe", "reconsider"]
    found_cognitive = [word for word in cognitive_indicators if word in all_facts_text]

    assert len(found_cognitive) >= 2, (
        f"Should preserve cognitive/epistemic dimension. "
        f"Found: {found_cognitive}"
    )


@pytest.mark.asyncio
async def test_capability_skill_dimension():
    """
    Test that capabilities, skills, and limitations are preserved.
    """
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

    # Should preserve capability indicators
    capability_indicators = ["can speak", "fluently", "struggles with", "expert in", "unable to"]
    found_capability = [word for word in capability_indicators if word in all_facts_text]

    assert len(found_capability) >= 2, (
        f"Should preserve capability/skill dimension. "
        f"Found: {found_capability}"
    )


@pytest.mark.asyncio
async def test_comparative_dimension():
    """
    Test that comparisons and contrasts are preserved.
    """
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

    # Should preserve comparative indicators
    comparative_indicators = ["better than", "worse than", "unlike", "ahead of"]
    found_comparative = [word for word in comparative_indicators if word in all_facts_text]

    assert len(found_comparative) >= 1, (
        f"Should preserve comparative dimension. "
        f"Found: {found_comparative}"
    )


@pytest.mark.asyncio
async def test_attitudinal_reactive_dimension():
    """
    Test that attitudes and reactions are preserved.
    """
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

    # Should preserve attitudinal/reactive indicators
    attitudinal_indicators = ["skeptical", "surprised", "rolled his eyes", "enthusiastic"]
    found_attitudinal = [word for word in attitudinal_indicators if word in all_facts_text]

    assert len(found_attitudinal) >= 2, (
        f"Should preserve attitudinal/reactive dimension. "
        f"Found: {found_attitudinal}"
    )


@pytest.mark.asyncio
async def test_intentional_motivational_dimension():
    """
    Test that goals, plans, and motivations are preserved.
    """
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

    # Should preserve intentional/motivational indicators
    intentional_indicators = ["want to", "aims to", "goal is", "planning to", "because"]
    found_intentional = [word for word in intentional_indicators if word in all_facts_text]

    assert len(found_intentional) >= 2, (
        f"Should preserve intentional/motivational dimension. "
        f"Found: {found_intentional}"
    )


@pytest.mark.asyncio
async def test_evaluative_preferential_dimension():
    """
    Test that preferences and values are preserved.
    """
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

    # Should preserve evaluative/preferential indicators
    evaluative_indicators = ["prefer", "values", "hates", "important", "above all"]
    found_evaluative = [word for word in evaluative_indicators if word in all_facts_text]

    assert len(found_evaluative) >= 2, (
        f"Should preserve evaluative/preferential dimension. "
        f"Found: {found_evaluative}"
    )


@pytest.mark.asyncio
async def test_comprehensive_multi_dimension():
    """
    Test a realistic scenario with multiple dimensions in one fact.
    """
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

    # Should preserve multiple dimensions:
    # 1. Emotional: "thrilled"
    # 2. Temporal: "yesterday" → absolute date (not "recently")
    # 3. Cognitive: "wasn't sure"
    # 4. Attitudinal: "enthusiastic"
    # 5. Preferential: "prefer"
    # 6. Comparative: "better"

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


@pytest.mark.asyncio
async def test_logical_inference_identity_connection():
    """
    Test that the system makes logical inferences to connect related information.

    Example: "I lost a friend" + "this photo with Karlie" → "I lost my friend Karlie"
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

    # Event date is February 23, 2023
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

    # CRITICAL: Should make the logical connection that Karlie is the lost friend
    # The fact should mention both "lost" (or similar) AND "Karlie" together
    has_karlie = "karlie" in all_facts_text
    has_loss = any(word in all_facts_text for word in ["lost", "death", "passed", "died", "losing"])

    assert has_karlie, "Should mention Karlie in the extracted facts"
    assert has_loss, "Should mention the loss/death in the extracted facts"

    # Ideally, they should be in the same fact (connected)
    # Check if any single fact contains both Karlie and loss-related terms
    connected_fact_found = False
    for fact in facts:
        fact_text = fact['fact'].lower()
        if "karlie" in fact_text and any(word in fact_text for word in ["lost", "death", "passed", "died", "losing"]):
            connected_fact_found = True
            print(f"\n✓ Found connected fact: {fact['fact']}")
            break

    assert connected_fact_found, (
        "Should connect 'lost a friend' with 'Karlie' in the same fact. "
        f"The inference should be: Karlie is the lost friend. "
        f"Facts: {[f['fact'] for f in facts]}"
    )


@pytest.mark.asyncio
async def test_logical_inference_pronoun_resolution():
    """
    Test that pronouns are resolved to their referents.

    Example: "I started a project" + "It's challenging" → "The project is challenging"
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

    # Should connect the project with its characteristics
    # The fact should mention "project" AND the qualities (challenging, rewarding)
    has_project = "project" in all_facts_text
    has_qualities = any(word in all_facts_text for word in ["challenging", "rewarding", "learned"])

    assert has_project, "Should mention the project"
    assert has_qualities, "Should mention the qualities/learning"

    # Check if a single fact connects the project with its characteristics
    connected_fact_found = False
    for fact in facts:
        fact_text = fact['fact'].lower()
        if "project" in fact_text and any(word in fact_text for word in ["challenging", "rewarding"]):
            connected_fact_found = True
            print(f"\n✓ Found connected fact: {fact['fact']}")
            break

    assert connected_fact_found, (
        "Should resolve 'it' to 'the project' and connect characteristics in the same fact. "
        f"Facts: {[f['fact'] for f in facts]}"
    )


@pytest.mark.asyncio
async def test_date_field_calculation_last_night():
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

    # Conversation happened on August 14, 2023
    event_date = datetime(2023, 8, 14, 14, 24)  # 2:24 PM on Aug 14

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
        print(f"{i+1}. Date: {f['date']} - {f['fact']}")

    # Find the fact about the birthday celebration
    birthday_fact = None
    for fact in facts:
        if "birthday" in fact['fact'].lower() or "concert" in fact['fact'].lower():
            birthday_fact = fact
            break

    assert birthday_fact is not None, "Should extract fact about birthday celebration"

    # The date field should be August 13, 2023 (last night), NOT August 14
    fact_date_str = birthday_fact['date']

    # Parse the date
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
async def test_date_field_calculation_yesterday():
    """
    Test that the date field is calculated correctly for "yesterday" events.
    """
    text = """
Yesterday I went for a morning jog for the first time in a nearby park.
"""

    context = "Personal diary"
    llm_config = LLMConfig.for_memory()

    # Conversation on November 13, 2024
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
        print(f"{i+1}. Date: {f['date']} - {f['fact']}")

    # Get the jogging fact
    jogging_fact = facts[0]

    # Parse the date
    fact_date_str = jogging_fact['date']
    if 'T' in fact_date_str:
        fact_date = datetime.fromisoformat(fact_date_str.replace('Z', '+00:00'))
    else:
        fact_date = datetime.fromisoformat(fact_date_str)

    # Should be November 12, 2024 (yesterday)
    assert fact_date.year == 2024, "Year should be 2024"
    assert fact_date.month == 11, "Month should be November"
    assert fact_date.day == 12, (
        f"Day should be 12 (yesterday relative to Nov 13), but got {fact_date.day}. "
        f"Date field: {fact_date_str}"
    )

    # Check fact text
    all_facts_text = " ".join([f['fact'].lower() for f in facts])

    # Should preserve "first time"
    assert "first time" in all_facts_text or "first" in all_facts_text, \
        "Should preserve 'first time' qualifier"

    # Should NOT use "recently"
    assert "recently" not in all_facts_text, \
        "Should NOT convert 'yesterday' to 'recently'"

    # Should have absolute date in text (November 12 or specific date)
    assert any(term in all_facts_text for term in ["november", "12", "nov"]), \
        "Should convert 'yesterday' to absolute date in fact text"
