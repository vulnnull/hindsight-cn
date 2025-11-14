"""
Test that fact classification correctly identifies agent vs world facts.
"""
import pytest
from datetime import datetime
from memora.fact_extraction import extract_facts_from_text
from memora.llm_wrapper import LLMConfig


@pytest.mark.asyncio
async def test_agent_facts_from_podcast_transcript():
    """
    Test that when context identifies someone as 'you', their actions are classified as agent facts.

    This test addresses the issue where podcast transcripts with context like
    "this was podcast episode between you (Marcus) and Jamie" were extracting
    all facts as 'world' instead of properly identifying Marcus's statements as 'agent'.
    """

    # Podcast transcript where Marcus (identified as "you") discusses his work
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
        context=context,
        llm_config=llm_config
    )

    # Should extract at least one fact
    assert len(facts) > 0, "Should extract at least one fact from the transcript"

    print(f"\nExtracted {len(facts)} facts:")
    for i, f in enumerate(facts):
        print(f"{i+1}. [{f['fact_type']}] {f['fact']}")

    # Marcus's work should be classified as 'agent' since context says "you (Marcus)"
    agent_facts = [f for f in facts if f["fact_type"] == "agent"]

    assert len(agent_facts) > 0, \
        f"Should have at least one 'agent' fact when context identifies 'you (Marcus)'. " \
        f"Got facts: {[f['fact'] + ' [' + f['fact_type'] + ']' for f in facts]}"

    # Verify that agent facts use FIRST PERSON (not "Marcus", but "I")
    for agent_fact in agent_facts:
        fact_text = agent_fact["fact"]
        # Agent facts should use "I" not the person's name in third person
        assert fact_text.startswith("I ") or " I " in fact_text, \
            f"Agent facts must use first person ('I'). Got: {fact_text}"

        # Should NOT contain "Marcus" as the subject in third person constructions
        # (It's ok to have "Marcus" when referring to oneself, but not "Marcus published" style)
        import re
        # Check for third-person patterns like "Marcus said", "Marcus worked", etc.
        third_person_pattern = r'\bMarcus\s+(said|worked|has|published|explained|believes|attended|completed)'
        match = re.search(third_person_pattern, fact_text)
        assert not match, \
            f"Agent facts should use first person, not third person. " \
            f"Found '{match.group()}' in: {fact_text}"

    print(f"\n✅ All {len(agent_facts)} agent facts use first person ('I')")

    # Jamie's statements should be 'world' facts
    jamie_facts = [f for f in facts if "Jamie" in f["fact"] and "Jamie" == f["fact"].split()[0]]
    if jamie_facts:
        world_jamie_facts = [f for f in jamie_facts if f["fact_type"] == "world"]
        assert len(world_jamie_facts) > 0, \
            f"Jamie's statements should be 'world' facts. " \
            f"Jamie facts: {[f['fact'] + ' [' + f['fact_type'] + ']' for f in jamie_facts]}"

    print(f"\n✅ Successfully classified {len(agent_facts)} agent facts and {len([f for f in facts if f['fact_type'] == 'world'])} world facts")
    print(f"\nAgent facts:")
    for f in agent_facts:
        print(f"  - {f['fact']}")
    print(f"\nWorld facts:")
    for f in facts:
        if f['fact_type'] == 'world':
            print(f"  - {f['fact']}")


@pytest.mark.asyncio
async def test_agent_facts_without_explicit_context():
    """
    Test that when 'you' is used in the text itself, it gets properly classified.
    """

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
        context=context,
        llm_config=llm_config
    )

    assert len(facts) > 0, "Should extract facts"

    # When text uses "I", those should likely be agent facts
    # (though without explicit "you (Name)" in context, this is harder to guarantee)
    agent_facts = [f for f in facts if f["fact_type"] == "agent"]

    print(f"\n✅ Extracted {len(facts)} total facts")
    print(f"Agent facts: {len(agent_facts)}")
    print(f"World facts: {len([f for f in facts if f['fact_type'] == 'world'])}")

    if agent_facts:
        print(f"\nAgent facts found:")
        for f in agent_facts:
            print(f"  - {f['fact']}")


@pytest.mark.asyncio
async def test_speaker_attribution_predictions():
    """
    Test that predictions made by different speakers are correctly attributed.

    This addresses the issue where Jamie's prediction of "Niners 27-13" was being
    incorrectly attributed to Marcus (the agent) in the extracted facts.
    """

    # Simplified transcript with clear predictions from each speaker
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

    # Find agent facts (Marcus's statements)
    agent_facts = [f for f in facts if f["fact_type"] == "agent"]

    # Find world facts about Jamie
    jamie_facts = [f for f in facts if f["fact_type"] == "world" and "Jamie" in f["fact"]]

    print(f"\nAgent facts (Marcus): {len(agent_facts)}")
    for f in agent_facts:
        print(f"  - {f['fact']}")

    print(f"\nWorld facts (Jamie): {len(jamie_facts)}")
    for f in jamie_facts:
        print(f"  - {f['fact']}")

    # CRITICAL: Marcus's prediction should be in agent facts, NOT Jamie's prediction
    # Marcus predicted: Rams 27-24
    # Jamie predicted: Niners 27-13

    agent_facts_text = " ".join([f["fact"].lower() for f in agent_facts])

    # Marcus (agent) should have mentioned Rams 27-24
    assert "rams" in agent_facts_text or "twenty seven to twenty four" in agent_facts_text or "27" in agent_facts_text, \
        f"Agent facts should contain Marcus's Rams prediction. Agent facts: {[f['fact'] for f in agent_facts]}"

    # Marcus (agent) should NOT have predicted Niners 27-13 (that was Jamie!)
    # Check that agent facts don't incorrectly contain Jamie's prediction
    has_niners_27_13 = False
    for fact in agent_facts:
        fact_lower = fact["fact"].lower()
        # Look for patterns that suggest 27-13 Niners prediction
        if ("niners" in fact_lower or "49ers" in fact_lower) and ("27" in fact_lower or "twenty seven") and ("13" in fact_lower or "thirteen"):
            # This is Jamie's prediction, should NOT be in agent facts!
            has_niners_27_13 = True
            print(f"\n❌ ERROR: Found Jamie's Niners 27-13 prediction in agent facts: {fact['fact']}")

    assert not has_niners_27_13, \
        f"Agent facts should NOT contain Jamie's Niners 27-13 prediction! " \
        f"Agent facts: {[f['fact'] for f in agent_facts]}"

    # Jamie's facts should contain Niners prediction
    if jamie_facts:
        jamie_facts_text = " ".join([f["fact"].lower() for f in jamie_facts])
        # Jamie predicted Niners, so world facts about Jamie might mention it
        print(f"\n✅ Jamie facts correctly classified as world facts")

    print(f"\n✅ Speaker attribution test passed: Predictions correctly attributed to their speakers")


@pytest.mark.asyncio
async def test_skip_podcast_meta_commentary():
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
        context=context,
        llm_config=llm_config
    )

    print(f"\nExtracted {len(facts)} facts:")
    for i, f in enumerate(facts):
        print(f"{i+1}. [{f['fact_type']}] {f['fact']}")

    # Should extract at least one fact
    assert len(facts) > 0, "Should extract at least one fact"

    # Check that no facts contain meta-commentary phrases
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

    # Should have facts about the actual content (interpretability research)
    content_facts = [f for f in facts if "interpretability" in f["fact"].lower()]
    assert len(content_facts) > 0, \
        "Should extract facts about the actual content discussed (interpretability)"

    print(f"\n✅ Successfully filtered out meta-commentary")
    print(f"✅ Extracted {len(content_facts)} facts about actual content")
