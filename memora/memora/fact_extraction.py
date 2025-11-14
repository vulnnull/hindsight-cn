"""
Fact extraction from text using LLM.

Extracts semantic facts, entities, and temporal information from text.
Uses the LLMConfig wrapper for all LLM calls.
"""
import logging
import os
import json
import re
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Literal
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from .llm_wrapper import OutputTooLongError, LLMConfig


class Entity(BaseModel):
    """An entity extracted from text."""
    text: str = Field(
        description="The entity name as it appears in the fact"
    )


class ExtractedFact(BaseModel):
    """A single extracted fact from text."""
    fact: str = Field(
        description="Self-contained factual statement with subject + action + context"
    )
    date: str = Field(
        description="Absolute date/time when this fact occurred in ISO format (YYYY-MM-DDTHH:MM:SSZ). If text mentions relative time (yesterday, last week, this morning), calculate absolute date from the provided context date."
    )
    fact_type: Literal["world", "agent", "opinion"] = Field(
        description="Type of fact: 'world' for general facts about the world (events, people, things others said/did), 'agent' for facts about what the memory owner (the person this memory belongs to, often identified as 'you' in context) specifically did, said, experienced, or actions they took - MUST be written in FIRST PERSON ('I did...', 'I said...'), 'opinion' for the memory owner's formed opinions and perspectives - also in first person"
    )
    entities: List[Entity] = Field(
        default_factory=list,
        description="List of important entities mentioned in this fact with their types"
    )


class FactExtractionResponse(BaseModel):
    """Response containing all extracted facts."""
    facts: List[ExtractedFact] = Field(
        description="List of extracted factual statements"
    )


def chunk_text(text: str, max_chars: int) -> List[str]:
    """
    Split text into chunks at sentence boundaries using LangChain's text splitter.

    Uses RecursiveCharacterTextSplitter which intelligently splits at sentence boundaries
    and allows chunks to slightly exceed max_chars to finish sentences naturally.

    Args:
        text: Input text to chunk
        max_chars: Maximum characters per chunk (default 120k ≈ 30k tokens)
                   Note: chunks may slightly exceed this to complete sentences

    Returns:
        List of text chunks, roughly under max_chars
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # If text is small enough, return as-is
    if len(text) <= max_chars:
        return [text]

    # Configure splitter to split at sentence boundaries first
    # Separators in order of preference: paragraphs, newlines, sentences, words
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=0,
        length_function=len,
        is_separator_regex=False,
        separators=[
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentence endings
            "! ",    # Exclamations
            "? ",    # Questions
            "; ",    # Semicolons
            ", ",    # Commas
            " ",     # Words
            "",      # Characters (last resort)
        ],
    )

    return splitter.split_text(text)


async def _extract_facts_from_chunk(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    event_date: datetime,
    context: str,
    llm_config: 'LLMConfig',
    agent_name: str = None
) -> List[Dict[str, str]]:
    """
    Extract facts from a single chunk (internal helper for parallel processing).
    """
    # Format event_date for the prompt
    event_date_str = event_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    agent_context = f"\n- Agent name (memory owner): {agent_name}" if agent_name else ""

    prompt = f"""You are extracting comprehensive, narrative facts from conversations for an AI memory system.

## CONTEXT INFORMATION
- Current reference date/time: {event_date_str}
- Context: {context if context else 'no context provided'}{agent_context}

## CORE PRINCIPLE: Extract FEWER, MORE COMPREHENSIVE Facts

**GOAL**: Extract 2-5 comprehensive facts per conversation, NOT dozens of small fragments.

Each fact should:
1. **CAPTURE ENTIRE CONVERSATIONS OR EXCHANGES** - Include the full back-and-forth discussion
2. **BE NARRATIVE AND COMPREHENSIVE** - Tell the complete story with all context
3. **BE SELF-CONTAINED** - Readable without the original text
4. **INCLUDE ALL PARTICIPANTS** - WHO said/did WHAT, with their reasoning
5. **PRESERVE THE FLOW** - Keep related exchanges together in one fact

## HOW TO COMBINE INFORMATION INTO COMPREHENSIVE FACTS

**✅ GOOD APPROACH**: One comprehensive fact capturing the entire discussion
"Alice and Bob discussed playlist names for the summer party. Bob suggested 'Summer Vibes' because it's catchy and seasonal. Alice liked it but wanted something more unique. They considered 'Sunset Sessions' and 'Beach Beats', with Alice favoring 'Beach Beats' for its playful tone. They ultimately decided on 'Beach Beats' as the final name."

**❌ BAD APPROACH**: Multiple fragmented facts
- "Bob suggested Summer Vibes"
- "Alice wanted something unique"
- "They considered Sunset Sessions"
- "Alice likes Beach Beats"
- "They chose Beach Beats"

## WHAT TO COMBINE INTO SINGLE FACTS

1. **FULL DISCUSSIONS** - Entire conversations about a topic (playlist names, travel plans, decisions)
2. **MULTI-STEP EVENTS** - Connected actions that form a complete story
3. **DECISIONS WITH REASONING** - The full decision-making process and rationale
4. **EXCHANGES WITH CONTEXT** - Questions, answers, and follow-up all together
5. **RELATED ACTIONS** - Multiple related activities in sequence

## ESSENTIAL DETAILS TO PRESERVE IN COMPREHENSIVE FACTS

While combining related content into comprehensive facts, you MUST preserve:

1. **ALL PARTICIPANTS** - Who said/did what
2. **FULL REASONING** - Why decisions were made, motivations, explanations
3. **TEMPORAL CONTEXT** - When things happened (transform relative dates like "last year" → "in 2023")
4. **VISUAL/MEDIA ELEMENTS** - Photos, images, videos shared
5. **MODIFIERS** - "new", "first", "old", "favorite" (critical context)
6. **POSSESSIVE RELATIONSHIPS** - "their kids" → "Person's kids"
7. **BIOGRAPHICAL DETAILS** - Origins, locations, jobs, family background
8. **SOCIAL DYNAMICS** - Nicknames, how people address each other, relationships

## TEMPORAL INFORMATION
- Extract the ABSOLUTE date/time for when the fact/conversation occurred
- Transform relative times in the fact text:
  - "last year" → "in [year]" (e.g., "in 2023")
  - "last month" → "in [month year]" (e.g., "in February 2024")
- Use ISO format for dates: YYYY-MM-DDTHH:MM:SSZ
- If no specific time mentioned, use the reference date

## WHEN TO SPLIT INTO SEPARATE FACTS

Only split into separate facts when topics are COMPLETELY UNRELATED:
- Different subjects discussed (playlist names vs. vacation plans)
- Biographical facts vs. events (where someone is from vs. what they did)
- Different time periods (something last year vs. today)

## What to SKIP
- Greetings, thank yous (unless they reveal information)
- Filler words ("um", "uh", "like")
- Pure reactions without content ("wow", "cool")
- Incomplete fragments with no meaning
- **Structural/procedural statements**: Openings, closings, transitions, housekeeping ("let's get started", "that's all", "moving on")
- **Meta-commentary about the medium itself**: References to the format/structure rather than content ("welcome to the show", "thanks for listening", "before we begin")
- **Calls to action unrelated to content**: Requests to subscribe, follow, rate, share, etc.
- **Generic sign-offs**: "See you next time", "Until later", "That wraps it up"
- **FOCUS PRINCIPLE**: Extract SUBSTANTIVE CONTENT (ideas, facts, discussions, decisions), NOT FORMAT/STRUCTURE

## FACT TYPE CLASSIFICATION

Classify each fact as 'world', 'agent', or 'opinion':

- **'world'**: Facts about other people, events, things that happened in the world, what others said/did
  - Written in third person (use names, "they", etc.)
- **'agent'**: Facts about what the MEMORY OWNER (the person this memory belongs to) specifically did, said, experienced, or actions they took
  - The memory owner is typically identified in the context (e.g., "you (Marcus)" means Marcus is the memory owner)
  - **CRITICAL**: MUST be written in FIRST PERSON using "I", "me", "my" (NOT the person's name)
  - Examples: "I said I prefer coffee", "I attended the conference", "I completed the project"
  - ❌ WRONG: "Marcus said he prefers coffee"
  - ✅ CORRECT: "I said I prefer coffee"
- **'opinion'**: The memory owner's formed opinions, beliefs, and perspectives about topics
  - Also written in first person: "I believe...", "I think..."

**CRITICAL**: If the context identifies someone as "you" or specifies whose memory this is, then facts about that person's actions/statements are 'agent' facts written in FIRST PERSON.

**Example**: If context says "podcast between you (Marcus) and Jamie":
- "I explained my approach to AI safety" → 'agent' (first person, my action)
- "Jamie asked about neural networks" → 'world' (someone else's action, third person)
- "Jamie and I discussed transformer architectures" → 'world' (general conversation - could use first person here since it includes both)
- "I believe interpretability is crucial" → 'opinion' (first person belief)

## ENTITY EXTRACTION
Extract ALL important entities (names of people, places, organizations, products, concepts, etc).

Extract proper nouns and key identifying terms. Skip pronouns and generic terms.

## EXAMPLES - COMPREHENSIVE VS FRAGMENTED FACTS:

### Example 1: Playlist Discussion
**Input Conversation:**
"Alice: Hey, what should we name our summer party playlist?
Bob: How about 'Summer Vibes'? It's catchy and seasonal.
Alice: I like it, but want something more unique.
Bob: What about 'Sunset Sessions' or 'Beach Beats'?
Alice: Ooh, I love 'Beach Beats'! It's playful and fun.
Bob: Perfect, let's go with that!"

**❌ BAD (fragmented into many small facts):**
1. "Alice asked about playlist names"
2. "Bob suggested Summer Vibes"
3. "Alice wanted something unique"
4. "Bob suggested Sunset Sessions"
5. "Bob suggested Beach Beats"
6. "Alice likes Beach Beats"
7. "They chose Beach Beats"

**✅ GOOD (one comprehensive fact):**
"Alice and Bob discussed naming their summer party playlist. Bob suggested 'Summer Vibes' because it's catchy and seasonal, but Alice wanted something more unique. Bob then proposed 'Sunset Sessions' and 'Beach Beats', with Alice favoring 'Beach Beats' for its playful and fun tone. They ultimately decided on 'Beach Beats' as the final name."
- fact_type: "world"
- entities: [{{"text": "Alice"}}, {{"text": "Bob"}}]

### Example 2: Photo Sharing with Context
**Input:**
"Nate: Here's a photo of my new hair!
Friend: Whoa! Why that color?
Nate: I picked bright orange because it's bold and makes me feel confident. Plus it matches my personality!"

**❌ BAD (loses context):**
"Nate chose orange hair because it's bold"

**✅ GOOD (comprehensive with all context):**
"Nate shared a photo of his new bright orange hair. When asked why he chose that color, Nate explained he picked it because it's bold and makes him feel confident, and it matches his personality."
- fact_type: "world"
- entities: [{{"text": "Nate"}}]
- NOTE: Preserves that it's a PHOTO, it's NEW hair, the COLOR, and the FULL reasoning

### Example 3: Travel Planning
**Input:**
"Sarah: I'm thinking of visiting Japan next spring.
Mike: That's perfect timing for cherry blossoms! You should definitely visit Kyoto.
Sarah: Why Kyoto specifically?
Mike: It has the most beautiful temples and the cherry blossoms there are spectacular. I went in 2019.
Sarah: Sounds amazing! I'll add it to my itinerary."

**❌ BAD (fragmented):**
1. "Sarah is planning to visit Japan"
2. "Mike suggested Kyoto"
3. "Kyoto has beautiful temples"
4. "Mike visited in 2019"

**✅ GOOD (comprehensive conversation):**
"Sarah is planning to visit Japan next spring, and Mike recommended Kyoto as the perfect destination for cherry blossom season. Mike explained that Kyoto has the most beautiful temples and spectacular cherry blossoms, based on his visit there in 2019. Sarah decided to add Kyoto to her itinerary."
- fact_type: "world"
- date: Next spring from reference date
- entities: [{{"text": "Sarah"}}, {{"text": "Mike"}}, {{"text": "Japan"}}, {{"text": "Kyoto"}}]

### Example 4: Job News
**Input:**
"Alice mentioned she works at Google in Mountain View. She joined the AI team last year and loves the culture there."

**✅ GOOD (combined into one comprehensive fact):**
"Alice works at Google in Mountain View on the AI team, which she joined in 2023, and she loves the company culture there."
- fact_type: "world"
- date: 2023 (if reference is 2024)
- entities: [{{"text": "Alice"}}, {{"text": "Google"}}, {{"text": "Mountain View"}}, {{"text": "AI team"}}]

### Example 5: Agent vs World Facts (CRITICAL FOR CLASSIFICATION)
**Context:** "Podcast episode between you (Marcus) and Jamie about AI"
**Input:**
"Marcus: I've been working on interpretability research for the past year.
Jamie: That's fascinating! What made you focus on that?
Marcus: I believe it's crucial for AI safety. Without understanding how models work, we can't trust them.
Jamie: I agree. Have you published any papers?
Marcus: Yes, I published a paper on attention visualization in March."

**✅ GOOD CLASSIFICATION:**
1. "I have been working on interpretability research for the past year because I believe it's crucial for AI safety and think that without understanding how models work, we can't trust them. Jamie found this fascinating and asked about publications. I published a paper on attention visualization in March 2024."
   - fact_type: "agent" (written in FIRST PERSON - my work and statements)
   - entities: [{{"text": "Jamie"}}, {{"text": "interpretability research"}}, {{"text": "attention visualization"}}]
   - NOTE: Uses "I" not "Marcus" - first person for agent facts

2. "Jamie agrees that understanding how AI models work is crucial for trust"
   - fact_type: "world" (Jamie's statement - third person, not the memory owner)
   - entities: [{{"text": "Jamie"}}]

**❌ BAD CLASSIFICATION:**
- Using "Marcus has been working..." instead of "I have been working..." for agent facts
- Marking my actions as 'world' facts
- Marking Jamie's statements as 'agent' facts

### Example 6: Skipping Structural/Procedural Statements
**Input (could be podcast, meeting, lecture, etc.):**
"Marcus: So in my research on AI safety, I've found that interpretability is key.
Jamie: That's fascinating! Tell us more.
Marcus: Well, it's all about understanding how models make decisions...
Marcus: I think that's gonna do it for us today! Don't forget to subscribe and leave a rating. See you next week!"

**✅ GOOD (extract only substantive content):**
1. "I have found that interpretability is key in my AI safety research because it's all about understanding how models make decisions, and Jamie found this fascinating."
   - fact_type: "agent"
   - entities: [{{"text": "Jamie"}}, {{"text": "AI safety"}}, {{"text": "interpretability"}}]

**❌ BAD (extracting procedural/structural statements):**
- "I think that's gonna do it for us today and I encourage listeners to subscribe and leave a rating" ← This is structural boilerplate about the format, NOT substantive content!

### Example 7: When to Split into Multiple Facts
**Input:**
"Caroline said 'This necklace is from my grandma in Sweden. I'm planning to visit Stockholm next month for a tech conference.'"

**✅ GOOD (split into 2 facts - different topics):**
1. "Caroline received a necklace from her grandmother in Sweden"
   - entities: [{{"text": "Caroline"}}, {{"text": "Sweden"}}]
2. "Caroline is planning to visit Stockholm next month to attend a tech conference"
   - date: Next month from reference
   - entities: [{{"text": "Caroline"}}, {{"text": "Stockholm"}}]
- NOTE: Split because one is about the past (necklace) and one is future plans (conference) - completely different topics

## TEXT TO EXTRACT FROM:
{chunk}

## CRITICAL REMINDERS:
1. **EXTRACT 2-5 COMPREHENSIVE FACTS** - Not dozens of fragments
2. **COMBINE RELATED EXCHANGES** - Keep full discussions together in one fact
3. **PRESERVE ALL CONTEXT** - Photos, "new" things, visual elements, reasoning, modifiers
4. **INCLUDE ALL PARTICIPANTS** - Who said/did what with full reasoning
5. **MAINTAIN NARRATIVE FLOW** - Tell the complete story in each fact
6. **ONLY SPLIT** when topics are completely unrelated or different time periods
7. **TRANSFORM RELATIVE DATES** - "last year" → "in 2023" in the fact text
8. **EXTRACT ALL ENTITIES** - PERSON, ORG, PLACE, PRODUCT, CONCEPT, OTHER
9. **CLASSIFY FACTS CORRECTLY**:
   - 'agent' = memory owner's actions/statements (identified as "you" in context) - **MUST USE FIRST PERSON** ("I did...", "I said...")
   - 'world' = other people's actions/statements, general events - use third person
   - 'opinion' = memory owner's beliefs/perspectives - use first person ("I believe...", "I think...")
10. **EXTRACT CONTENT, NOT FORMAT** - Skip structural/procedural statements (openings, closings, housekeeping), meta-commentary about the medium, calls to action - extract only SUBSTANTIVE CONTENT (ideas, facts, discussions, decisions)
11. When combining, prefer MORE comprehensive facts over fragmenting"""

    import time
    import logging
    from openai import BadRequestError

    logger = logging.getLogger(__name__)

    # Retry logic for JSON validation errors
    max_retries = 2
    last_error = None

    for attempt in range(max_retries):
        try:
            extraction_response = await llm_config.call(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a comprehensive fact extractor that creates narrative, self-contained facts. CRITICAL: Extract 2-5 COMPREHENSIVE facts per conversation, NOT dozens of fragments. COMBINE related exchanges into single narrative facts that tell the complete story. For example, a discussion about playlist names should be ONE fact capturing the entire back-and-forth with all reasoning, not multiple small facts. PRESERVE all context (photos, 'new' things, visual elements, full reasoning), INCLUDE all participants and what they said/did, MAINTAIN narrative flow. ONLY SPLIT into separate facts when topics are completely unrelated or different time periods. Transform relative dates in fact text ('last year' → 'in 2023'). Extract entities (PERSON, ORG, PLACE, PRODUCT, CONCEPT, OTHER). FACT TYPES: Classify as 'world' (facts about others/events - third person), 'agent' (facts about the memory owner's actions/statements - identified as 'you' in context - MUST USE FIRST PERSON 'I did...', 'I said...'), or 'opinion' (memory owner's beliefs - first person 'I believe...'). CRITICAL: If context says 'you (Name)', write Name's actions in FIRST PERSON as 'agent' facts ('I attended...' NOT 'Name attended...'). Extract SUBSTANTIVE CONTENT only - skip structural/procedural statements (openings, closings, housekeeping), meta-commentary about format/medium, and calls to action. Focus on IDEAS, FACTS, DISCUSSIONS, DECISIONS - not structure. When in doubt, prefer MORE COMPREHENSIVE over fragmenting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=FactExtractionResponse,
                scope="memory_extract_facts",
                temperature=0.1,
                max_tokens=65000,
                extra_body={"service_tier": "auto"}
            )
            chunk_facts = [fact.model_dump() for fact in extraction_response.facts]
            return chunk_facts

        except BadRequestError as e:
            last_error = e
            if "json_validate_failed" in str(e):
                logger.warning(f"          [1.3.{chunk_index + 1}] Attempt {attempt + 1}/{max_retries} failed with JSON validation error: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"          [1.3.{chunk_index + 1}] Retrying...")
                    continue
            # If it's not a JSON validation error or we're out of retries, re-raise
            raise

    # If we exhausted all retries, raise the last error
    raise last_error


async def _extract_facts_with_auto_split(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    event_date: datetime,
    context: str,
    llm_config: LLMConfig,
    agent_name: str = None
) -> List[Dict[str, str]]:
    """
    Extract facts from a chunk with automatic splitting if output exceeds token limits.

    If the LLM output is too long (OutputTooLongError), this function automatically
    splits the chunk in half and processes each half recursively.

    Args:
        chunk: Text chunk to process
        chunk_index: Index of this chunk in the original list
        total_chunks: Total number of original chunks
        event_date: Reference date for temporal information
        context: Context about the conversation/document
        llm_config: LLM configuration to use
        agent_name: Optional agent name (memory owner)

    Returns:
        List of fact dictionaries extracted from the chunk (possibly from sub-chunks)
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Try to extract facts from the full chunk
        return await _extract_facts_from_chunk(
            chunk=chunk,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name=agent_name
        )
    except OutputTooLongError as e:
        # Output exceeded token limits - split the chunk in half and retry
        logger.warning(
            f"Output too long for chunk {chunk_index + 1}/{total_chunks} "
            f"({len(chunk)} chars). Splitting in half and retrying..."
        )

        # Split at the midpoint, preferring sentence boundaries
        mid_point = len(chunk) // 2

        # Try to find a sentence boundary near the midpoint
        # Look for ". ", "! ", "? " within 20% of midpoint
        search_range = int(len(chunk) * 0.2)
        search_start = max(0, mid_point - search_range)
        search_end = min(len(chunk), mid_point + search_range)

        sentence_endings = ['. ', '! ', '? ', '\n\n']
        best_split = mid_point

        for ending in sentence_endings:
            pos = chunk.rfind(ending, search_start, search_end)
            if pos != -1:
                best_split = pos + len(ending)
                break

        # Split the chunk
        first_half = chunk[:best_split].strip()
        second_half = chunk[best_split:].strip()

        logger.info(
            f"Split chunk {chunk_index + 1} into two sub-chunks: "
            f"{len(first_half)} chars and {len(second_half)} chars"
        )

        # Process both halves recursively (in parallel)
        sub_tasks = [
            _extract_facts_with_auto_split(
                chunk=first_half,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                event_date=event_date,
                context=context,
                llm_config=llm_config,
                agent_name=agent_name
            ),
            _extract_facts_with_auto_split(
                chunk=second_half,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                event_date=event_date,
                context=context,
                llm_config=llm_config,
                agent_name=agent_name
            )
        ]

        sub_results = await asyncio.gather(*sub_tasks)

        # Combine results from both halves
        all_facts = []
        for sub_result in sub_results:
            all_facts.extend(sub_result)

        logger.info(
            f"Successfully extracted {len(all_facts)} facts from split chunk {chunk_index + 1}"
        )

        return all_facts


async def extract_facts_from_text(
    text: str,
    event_date: datetime,
    llm_config: LLMConfig,
    agent_name: str,
    context: str = "",
) -> List[Dict[str, str]]:
    """
    Extract semantic facts from conversational or narrative text using LLM.

    For large texts (>chunk_size chars), automatically chunks at sentence boundaries
    to avoid hitting output token limits. Processes ALL chunks in PARALLEL for speed.

    If a chunk produces output that exceeds token limits (OutputTooLongError), it is
    automatically split in half and retried recursively until successful.

    Args:
        text: Input text (conversation, article, etc.)
        event_date: Reference date for resolving relative times
        context: Context about the conversation/document
        llm_config: LLM configuration to use (if None, uses default from environment)
        chunk_size: Maximum characters per chunk
        agent_name: Optional agent name (memory owner)

    Returns:
        List of fact dictionaries with 'fact' and 'date' keys
    """
    chunks = chunk_text(text, max_chars=50_000)
    logging.info(f"created {len(chunks)} chunks from text {len(text)}")
    tasks = [
        _extract_facts_with_auto_split(
            chunk=chunk,
            chunk_index=i,
            total_chunks=len(chunks),
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name=agent_name
        )
        for i, chunk in enumerate(chunks)
    ]
    chunk_results = await asyncio.gather(*tasks)
    all_facts = []
    for chunk_facts in chunk_results:
        all_facts.extend(chunk_facts)
    return all_facts
