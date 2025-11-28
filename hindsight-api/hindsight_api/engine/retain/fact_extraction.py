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
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator, ConfigDict
from ..llm_wrapper import OutputTooLongError, LLMConfig


class Entity(BaseModel):
    """An entity extracted from text."""
    text: str = Field(
        description="The specific, named entity as it appears in the fact. Must be a proper noun or specific identifier."
    )


class Fact(BaseModel):
    """
    Final fact model for storage - built from lenient parsing of LLM response.

    This is what fact_extraction returns and what the rest of the pipeline expects.
    Only includes fields with meaningful values - nulls/empties are omitted.
    """
    # Required fields
    fact: str = Field(description="Combined fact text from all dimensions")
    fact_type: Literal["world", "bank", "opinion"] = Field(description="Perspective: world/bank/opinion")

    # Optional dimension fields
    emotional_significance: Optional[str] = None
    reasoning_motivation: Optional[str] = None
    preferences_opinions: Optional[str] = None
    sensory_details: Optional[str] = None
    observations: Optional[str] = None

    # Optional temporal fields
    occurred_start: Optional[str] = None
    occurred_end: Optional[str] = None
    mentioned_at: Optional[str] = None

    # Optional structured data
    entities: Optional[List[Entity]] = None
    causal_relations: Optional[List['CausalRelation']] = None


class CausalRelation(BaseModel):
    """Causal relationship between facts."""
    target_fact_index: int = Field(
        description="Index of the related fact in the facts array (0-based). "
                   "This creates a directed causal link to another fact in the extraction."
    )
    relation_type: Literal["causes", "caused_by", "enables", "prevents"] = Field(
        description="Type of causal relationship: "
                   "'causes' = this fact directly causes the target fact, "
                   "'caused_by' = this fact was caused by the target fact, "
                   "'enables' = this fact enables/allows the target fact, "
                   "'prevents' = this fact prevents/blocks the target fact"
    )
    strength: float = Field(
        description="Strength of causal relationship (0.0 to 1.0). "
                   "1.0 = direct/strong causation, 0.5 = moderate, 0.3 = weak/indirect",
        ge=0.0,
        le=1.0,
        default=1.0
    )


class ExtractedFact(BaseModel):
    """A single extracted fact with structured dimensions for comprehensive capture."""

    model_config = ConfigDict(
        json_schema_mode="validation",
        # Only require truly critical fields - be lenient with everything else
        json_schema_extra={
            "required": ["factual_core", "fact_type"]
        }
    )

    # Core factual dimension (CRITICAL - required)
    factual_core: str = Field(
        description="ACTUAL FACTS - what literally happened/was said. MUST be a complete, grammatically correct sentence with subject and verb. Capture WHAT was said, not just THAT something was said! 'Gina said Jon is the perfect mentor with positivity and determination' NOT 'Jon received encouragement'. Preserve: compliments, assessments, descriptions, key phrases. Be specific!"
    )

    # Optional dimensions - only include if present in the text
    # CRITICAL: Each dimension MUST be a complete, standalone sentence that reads naturally
    emotional_significance: Optional[str] = Field(
        default=None,
        description="Emotions, feelings, personal meaning as a COMPLETE SENTENCE. Include subject + emotion/feeling. Examples: 'Sarah felt thrilled about the promotion', 'This was her favorite memory from childhood', 'The experience was magical for everyone involved', 'John found the loss devastating', 'She considers this her proudest moment'"
    )
    reasoning_motivation: Optional[str] = Field(
        default=None,
        description="WHY it happened as a COMPLETE SENTENCE. Include subject + motivation/reason. Examples: 'She did this because she wanted to celebrate', 'He wrote the book to cope with grief', 'She was motivated by curiosity about the topic'"
    )
    preferences_opinions: Optional[str] = Field(
        default=None,
        description="Likes, dislikes, beliefs, values as a COMPLETE SENTENCE. Include subject + preference/opinion. Examples: 'Sarah loves coffee and drinks it daily', 'He thinks AI is transformative technology', 'She prefers working remotely over office work'"
    )
    sensory_details: Optional[str] = Field(
        default=None,
        description="Visual, auditory, physical descriptions as a COMPLETE SENTENCE. Include subject + descriptive details. USE EXACT WORDS from text! Examples: 'She has bright orange hair', 'The dancer moved so gracefully on stage', 'The beach was awesome', 'The movie had epic visuals', 'The water was freezing cold'"
    )
    observations: Optional[str] = Field(
        default=None,
        description="Observations and inferences as a COMPLETE SENTENCE. Include subject + observed/inferred fact. Examples: 'Calvin traveled to Miami for the shoot', 'Gina won dance trophies in competitions', 'She knows programming from previous projects'"
    )

    # Fact kind - optional hint for LLM thinking, not critical for extraction
    # We don't strictly validate this since it's just guidance for temporal handling
    fact_kind: Optional[str] = Field(
        default="conversation",
        description="Optional hint: 'conversation' = general info, 'event' = specific datable occurrence, 'other' = anything else. Helps determine if occurred dates should be set, but not critical."
    )

    # Temporal fields - optional
    occurred_start: Optional[str] = Field(
        default=None,
        description="Optional: ISO format timestamp for when event started. Only needed for specific events."
    )
    occurred_end: Optional[str] = Field(
        default=None,
        description="Optional: ISO format timestamp for when event ended. Only needed for specific events."
    )

    # Classification (CRITICAL - required)
    # Note: LLM uses "assistant" but we convert to "bank" for storage
    fact_type: Literal["world", "assistant"] = Field(
        description="REQUIRED: 'world' = everything NOT involving the assistant (user's background, skills, experiences, other people's lives, events). 'assistant' = interactions BY or TO the assistant (user asked assistant, assistant recommended, assistant helped user, etc.)"
    )

    # Entities and relations
    entities: Optional[List[Entity]] = Field(
        default=None,
        description="ONLY specific, named entities worth tracking: people's names (e.g., 'Sarah', 'Dr. Smith'), organizations (e.g., 'Google', 'MIT'), specific places (e.g., 'Paris', 'Central Park'). DO NOT include: generic relations (mom, friend, boss, colleague), common nouns (apple, car, house), pronouns (he, she), or vague references (someone, a guy). Can be null or empty list [] if no entities."
    )
    causal_relations: Optional[List[CausalRelation]] = Field(
        default=None,
        description="Causal links to other facts in this batch. Example: fact about rain causes fact about cancelled game. Can be null or empty list [] if no causal relations."
    )

    @field_validator('entities', mode='before')
    @classmethod
    def ensure_entities_list(cls, v):
        """Ensure entities is always a list (convert None to empty list)."""
        if v is None:
            return []
        return v

    @field_validator('causal_relations', mode='before')
    @classmethod
    def ensure_causal_relations_list(cls, v):
        """Ensure causal_relations is always a list (convert None to empty list)."""
        if v is None:
            return []
        return v

    def build_fact_text(self) -> str:
        """Combine all dimensions into a single comprehensive fact string."""
        parts = [self.factual_core]

        if self.emotional_significance:
            parts.append(self.emotional_significance)
        if self.reasoning_motivation:
            parts.append(self.reasoning_motivation)
        if self.preferences_opinions:
            parts.append(self.preferences_opinions)
        if self.sensory_details:
            parts.append(self.sensory_details)
        if self.observations:
            parts.append(self.observations)

        # Join with appropriate connectors
        if len(parts) == 1:
            return parts[0]

        # Combine: "Core fact - emotional/significance context"
        return f"{parts[0]} - {' - '.join(parts[1:])}"


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
    agent_name: str = None,
    extract_opinions: bool = False
) -> List[Dict[str, str]]:
    """
    Extract facts from a single chunk (internal helper for parallel processing).

    Note: event_date parameter is kept for backward compatibility but not used in prompt.
    The LLM extracts temporal information from the context string instead.
    """
    agent_context = f"\n- Your name: {agent_name}" if agent_name else ""

    # Determine which fact types to extract based on the flag
    # Note: We use "assistant" in the prompt but convert to "bank" for storage
    if extract_opinions:
        # Opinion extraction uses a separate prompt (not this one)
        fact_types_instruction = "Extract ONLY 'opinion' type facts (formed opinions, beliefs, and perspectives). DO NOT extract 'world' or 'assistant' facts."
    else:
        fact_types_instruction = "Extract ONLY 'world' and 'assistant' type facts. DO NOT extract opinions - those are extracted separately."

    prompt = f"""You are extracting comprehensive, narrative facts from conversations/document for an AI memory system.

{fact_types_instruction}

## CONTEXT INFORMATION
- Context: {context if context else 'no additional context provided'}{agent_context}

**TEMPORAL EXTRACTION **:
- **occurred_start/end** (OPTIONAL): Only extract these for specific events mentioned within the conversation
  - Example: "I'm hosting a party next month" - extract when the party will happen (resolve to absolute dates using the reference date)
  - Leave empty if no specific event timing is mentioned
  - Use the reference date (event_date) to resolve relative time expressions to absolute ISO timestamps

## CORE PRINCIPLE: Extract ALL Meaningful Information Efficiently

**GOAL**: Capture ALL meaningful information, but combine related exchanges efficiently. Don't create separate facts for questions - merge Q&A into single facts.

Each fact should:
1. **CAPTURE ALL MEANINGFUL CONTENT** - Activities, projects, preferences, recommendations, encouragement WITH specific content
2. **BE SELF-CONTAINED** - Readable without the original text
3. **PRESERVE SPECIFIC CONTENT** - Capture WHAT was said, not just THAT something was said
4. **COMBINE Q&A** - A question and its answer = ONE fact, not two separate facts

## Q&A HANDLING - CRITICAL!

### WHEN TO COMBINE (simple informational questions):

**❌ BAD (2 separate facts):**
- "James asks what projects John is working on"
- "John is working on a website for a local small business"

**✅ GOOD (1 combined fact):**
- "John is working on a website for a local small business; it's his first professional project outside of class"

### WHEN TO SPLIT (user requests/instructions to assistant):

**CRITICAL**: When user asks assistant to DO something, extract BOTH facts separately!

**✅ GOOD (2 separate BANK facts):**
1. "User requested a children's book about dinosaurs with image placeholders in '::title:: == ::description::' format"
2. "I wrote a children's book titled 'The Amazing Adventures of Dinosaurs' with chapters about T-Rex, Pterodactyl, Plesiosaur, and Triceratops, including image descriptions"

**❌ BAD (missing user request):**
- Only extracting: "I wrote a children's book about dinosaurs..."

**Rule**: If user says "write...", "create...", "help me...", "explain...", etc. → Extract user's request AND assistant's response as SEPARATE bank facts!

## WHAT TO SKIP (only these!)

- **Pure filler with no content** - "Always happy to help", "Sounds good", "Thanks!"
- **Greetings** - "Hey!", "What's up?"
- **Standalone simple questions that are answered** - merge informational Q&A, but DON'T skip user requests!

## WHAT TO ALWAYS EXTRACT

- **USER REQUESTS** (CRITICAL!): "User requested a children's book about dinosaurs", "User asked for help with debugging"
- **ASSISTANT ACTIONS**: "I wrote a story", "I recommended meditation", "I explained the concept"
- Specific encouragement WITH content: "James says hiccups are normal, use them to learn and grow, push through"
- Reactions that reveal preferences: "John says the art is awesome, takes him back to reading fantasy books"
- Recommendations: "John recommends 'The Name of the Wind' - great novel with awesome writing"
- Plans/intentions: "James will check out 'The Name of the Wind'"
- All activities, projects, purchases, events with details

## ESSENTIAL DETAILS TO PRESERVE - NEVER LOSE THESE

When extracting facts, you MUST preserve:

1. **ALL PARTICIPANTS** - Who said/did what
2. **INDIVIDUAL PREFERENCES** - Each person's specific likes/favorites! "Jon's favorite is contemporary because it's expressive" - DO NOT LOSE THIS!
3. **FULL REASONING** - Why decisions were made, motivations, explanations
4. **TEMPORAL CONTEXT - CRITICAL** - ALWAYS convert relative time references to SPECIFIC ABSOLUTE dates in the fact text!
   - "last week" (doc date Aug 23) → "around August 16, 2023" (NOT just "in August 2023"!)
   - "last month" (doc date Aug 2023) → "in July 2023"
   - "yesterday" (doc date Aug 19) → "on August 18, 2023"
   - "next week" (doc date Aug 19) → "around August 26, 2023"
   - "three days ago" (doc date Aug 19) → "on August 16, 2023"
   - "last year" → "in 2022"
   - BE SPECIFIC! "last week" is NOT "in August" - calculate the actual week!
5. **VISUAL/MEDIA ELEMENTS** - Photos, images, videos shared
6. **MODIFIERS** - "new", "first", "old", "favorite" (critical context)
7. **POSSESSIVE RELATIONSHIPS** - "their kids" → "Person's kids"
8. **BIOGRAPHICAL DETAILS** - Origins, locations, jobs, family background
9. **SOCIAL DYNAMICS** - Nicknames, how people address each other, relationships

## STRUCTURED FACT DIMENSIONS - CRITICAL ⚠️

Each fact MUST be extracted into structured dimensions. This ensures no important context is lost.

**CRITICAL FORMATTING RULE**: Each dimension MUST be a complete, grammatically correct sentence that includes the subject and can stand alone. These dimensions will be combined with " - " separators, so they must read naturally together.

### Required field:
- **factual_core**: ACTUAL FACTS - capture WHAT was said, not just THAT something was said!
  - ❌ BAD: "Jon received encouragement from Gina" (loses what Gina actually said)
  - ✅ GOOD: "Gina said Jon is the perfect mentor with positivity and determination; his studio will be a hit"
  - ❌ BAD: "Jon supports Gina" (generic)
  - ✅ GOOD: "Gina found the perfect spot for her store; Jon says her hard work is paying off"
  - Preserve: compliments, assessments, descriptions, predictions, key phrases

### Optional fields (include when present in text):
- **emotional_significance**: Emotions, feelings, personal meaning, AND qualitative descriptors - COMPLETE SENTENCE with subject
  - ❌ BAD: "felt thrilled" (fragment, missing subject)
  - ✅ GOOD: "Sarah felt thrilled about the opportunity"
  - ❌ BAD: "was her favorite memory" (vague subject)
  - ✅ GOOD: "This was her favorite memory from childhood"
  - More examples: "The experience was magical for everyone involved", "John found the loss devastating", "She considers this her proudest moment"
  - Captures: emotions, intensity, personal significance, AND experiential descriptors ("magical", "wonderful", "amazing", "thrilling", "beautiful")

- **reasoning_motivation**: WHY it happened, intentions, goals, causes - COMPLETE SENTENCE with subject
  - ❌ BAD: "because she wanted to celebrate" (fragment, no subject)
  - ✅ GOOD: "She did this because she wanted to celebrate with friends"
  - More examples: "He wrote the book to cope with grief", "She was motivated by curiosity about the topic", "They moved there to be closer to family"
  - Captures: reasons, intentions, goals, causal explanations

- **preferences_opinions**: Likes, dislikes, beliefs, values, ideals - COMPLETE SENTENCE with subject
  - ❌ BAD: "loves coffee" (fragment)
  - ✅ GOOD: "Sarah loves coffee and drinks it every morning"
  - ❌ BAD: "prefers remote work" (fragment)
  - ✅ GOOD: "He prefers working remotely over office work"
  - More examples: "Jon's ideal dance studio would be located by the water", "Jon's favorite dance style is contemporary because it's expressive", "She thinks AI is transformative technology"
  - Captures: preferences, opinions, beliefs, judgments, ideals, dreams
  - PREFERENCE INDICATORS: "ideal", "favorite", "dream", "perfect", "love", "hate", "prefer" → MUST capture in this dimension!
  - CRITICAL: Never lose individual preferences! Always include who has the preference!

- **sensory_details**: Visual, auditory, physical descriptions AND all descriptive adjectives - COMPLETE SENTENCE with subject - USE EXACT WORDS!
  - ❌ BAD: "bright orange hair" (fragment)
  - ✅ GOOD: "She has bright orange hair"
  - ❌ BAD: "so graceful" (fragment)
  - ✅ GOOD: "The dancer moved so gracefully across the stage"
  - More examples: "The music was very loud", "The water was freezing cold", "The beach was awesome", "The movie had epic visuals"
  - Captures: colors, sounds, textures, temperatures, appearances, AND adjectives describing people/things/performances
  - CRITICAL: Use the EXACT adjectives from the text! If they said "awesome" don't write "amazing". If they said "epic" don't write "perfect"!

- **observations**: Things that can be inferred/deduced from the conversation - COMPLETE SENTENCE with subject
  - ❌ BAD: "traveled to Miami" (fragment)
  - ✅ GOOD: "Calvin traveled to Miami for the photo shoot"
  - ❌ BAD: "won dance trophies" (fragment)
  - ✅ GOOD: "Gina won dance trophies in past competitions"
  - More examples: "She knows programming from previous projects", "They own a house in the suburbs", "He has experience with public speaking"
  - TRAVEL: "doing the shoot in Miami" → "Calvin traveled to Miami for the shoot"
  - POSSESSION: "my trophy" → "She won the trophy"
  - CAPABILITIES: "she coded it" → "She knows programming"

### Example extraction:

**Input**: "I used to compete in dance competitions - my fav memory was when my team won first place at regionals at age fifteen. It was an awesome feeling of accomplishment!"

**Output**:
```
factual_core: "Gina's team won first place at a regional dance competition when she was 15"
emotional_significance: "This was Gina's favorite memory; she felt an awesome sense of accomplishment"
reasoning_motivation: null
preferences_opinions: null
sensory_details: null
```

**Combined result**: "Gina's team won first place at a regional dance competition when she was 15 - This was Gina's favorite memory; she felt an awesome sense of accomplishment"

### CRITICAL: Never strip away dimensions!
- ❌ BAD: Only extracting factual_core and ignoring emotional context
- ✅ GOOD: Capturing ALL dimensions present in the text
- ❌ BAD: Using fragments like "felt happy" or "loves pizza"
- ✅ GOOD: Using complete sentences like "She felt happy about the news" or "John loves pizza and orders it weekly"

## TEMPORAL CLASSIFICATION (fact_kind field) - About WHEN/TIMING

⚠️ **WARNING**: Do NOT confuse fact_kind with fact_type (see below)! These are DIFFERENT fields!

### fact_kind determines if occurred dates are set:

**`conversation`** - General info, activities, preferences, ongoing things
- NO occurred_start/end (leave null)
- Examples: "Jon is expanding his studio", "Jon loves dance", "Gina's ideal studio is by water"

**`event`** - Specific datable occurrence (competition, wedding, meeting, trip, loss, start/end of something)
- MUST set occurred_start/end
- Ask: "Is this a SPECIFIC EVENT with a DATE?"
- Examples: "Dance competition on May 15", "Lost job in January 2023", "Wedding next Saturday"

**`other`** - Anything else that doesn't fit above
- NO occurred_start/end (leave null)
- Catch-all to not lose information

### Rules:
1. **ALWAYS include dates in fact text** - "in January 2023", "on May 15, 2024"
2. **Only 'event' gets occurred dates** - conversation and other = null
3. **SPLIT events from conversation facts** - "Jon is expanding his studio (conversation) and hosting a competition next month (event)" → 2 separate facts!

## CAUSAL RELATIONSHIPS

When splitting related facts, link them with causal_relations:
- **causes**: This fact causes the target
- **caused_by**: This fact was caused by target
- **enables/prevents**: This fact enables/prevents the target

Only link when there's explicit or clear implicit causation ("because", "so", "therefore").

## FACT TYPE CLASSIFICATION - The Simple Rule

⚠️ **WARNING**: Do NOT confuse fact_type with fact_kind (see above)! These are DIFFERENT fields!
- fact_kind = temporal nature (conversation/event/other)
- fact_type = who/what this is about (world/assistant)

### The Rule: Everything NOT involving the assistant = 'world'

- **'world'**: Facts about people, places, events, things that exist independently of assistant interactions
  - **User's background/experience**: "User worked as marketing specialist at startup", "User has 5 years of Python experience"
  - **User's skills/knowledge**: "User has used Trello", "User is familiar with Kanban methodology", "User knows React"
  - **User's preferences/interests**: "User prefers async communication", "User is interested in exploring project management tools"
  - **Other people's lives**: "Sarah got promoted", "John traveled to Paris", "Mom retired last year"
  - **Events and facts**: "The meeting was cancelled", "The project launched in 2023"
  - **RULE**: If it would still be true even if this conversation never happened → **world**

- **'assistant'**: Interactions BY or TO the assistant (what happened in THIS conversation)
  - **User's questions/requests TO assistant**: "User asked about ClickUp features", "User requested comparison between tools", "User wanted to know strengths and weaknesses"
  - **Assistant's actions/responses**: "I recommended trying meditation", "I explained the difference between Trello and ClickUp", "I suggested exploring alternatives"
  - **Conversational events**: "User thanked me for the suggestion", "I clarified the technical details"
  - Use "user" or their name for user's questions/requests
  - Use FIRST PERSON ("I") for assistant's actions
  - **RULE**: If this only exists because of this conversation with the assistant → **assistant**

**CRITICAL EXAMPLES**:
- "User worked at startup" → **world** (would be true even without this conversation)
- "User asked me about ClickUp" → **assistant** (only exists because of this conversation)
- "User has experience with Trello" → **world** (independent fact about user)
- "User wanted to explore options" → Could be either:
  - **world** if it's a general preference: "User is interested in exploring project management alternatives"
  - **assistant** if it's what they expressed in this conversation: "User asked me to help explore other options"

**Real Example**:
User says: "I've used Trello in my previous role as a marketing specialist at a small startup and I'm familiar with its features. But I'm interested in exploring other options as well. Could you tell me more about ClickUp?"

Extract these facts:
1. **world**: "User worked as marketing specialist at small startup"
2. **world**: "User has used Trello in previous role"
3. **world**: "User is familiar with Trello features"
4. **world**: "User is interested in exploring project management alternatives"
5. **assistant**: "User asked me about ClickUp and how it differs from Trello"

**Speaker attribution**: If context says "Your name: Marcus", extract 'assistant' facts from both "Marcus:" and "Assistant:" lines.

## WHAT TO SKIP
- Greetings, filler words, pure reactions ("wow", "cool")
- Structural statements ("let's get started", "see you next time")
- Calls to action ("subscribe", "follow")

## EXAMPLE: SPLITTING CONVERSATION VS EVENT FACTS

**Input (conversation date: April 3, 2023):**
"I'm expanding my dance studio's social media presence and offering workshops to local schools. I'm also hosting a dance competition next month to showcase local talent. The dancers are so excited!"

**Output (2 facts - conversation + event):**

**Fact 1 (kind=conversation - ongoing activities, no occurred dates):**
```
fact_kind: "conversation"
factual_core: "Jon is expanding his dance studio's social media presence in April 2023; offering workshops and classes to local schools and centers; seeing progress and dancers are excited"
emotional_significance: "excited and proud of progress"
preferences_opinions: "Jon loves giving dancers a place to express themselves"
observations: "Jon owns/runs a dance studio"
occurred_start: null  ← conversation kind = no occurred dates
occurred_end: null
```

**Fact 2 (kind=event - specific datable occurrence):**
```
fact_kind: "event"
factual_core: "Jon will host a dance competition in May 2023 to showcase local talent and bring attention to his studio"
emotional_significance: "excited about the event"
occurred_start: "2023-05-01T00:00:00Z"  ← event kind = HAS occurred dates
occurred_end: "2023-05-31T23:59:59Z"
```

**❌ BAD:** Combining both into one fact with occurred=May (makes ongoing activities look like they happened in May!)

## TEXT TO EXTRACT FROM:
{chunk}

## CRITICAL REMINDERS:
1. **NEVER MISS USER REQUESTS** - If user asks assistant to do something ("write...", "create...", "help me..."), extract BOTH the request AND the response as separate BANK facts!
2. **BANK FACT PERSPECTIVE** - Use "I" for assistant actions ("I recommended", "I wrote"), use "user" or their name for user actions ("User requested", "Marcus said")
3. **COMBINE SIMPLE Q&A** - Merge simple informational questions with answers. But don't merge user requests - extract them separately!
4. **CAPTURE ALL MEANINGFUL CONTENT** - Activities, encouragement (with specific words!), recommendations, reactions, preferences
5. **CONVERT RELATIVE DATES TO SPECIFIC DATES** - "last week" → "around August 16" (NOT "in August"!), "yesterday" → "on August 18". Be precise!
6. **CAPTURE WHAT WAS SAID** - "Gina said Jon is perfect mentor with determination" NOT "Jon received encouragement". Preserve the actual content!
7. **FACT_KIND DETERMINES OCCURRED DATES** - Only 'event' gets occurred_start/end. 'conversation' and 'other' = null
8. **CAPTURE PREFERENCES** - "ideal", "favorite", "love" → preferences_opinions
9. **CAPTURE EXACT ADJECTIVES** - Use the EXACT words! "awesome" not "amazing", "epic" not "perfect" → sensory_details
10. **CAPTURE OBSERVATIONS** - "shooting in Miami" → observations: "traveled to Miami". Infer travel, achievements, capabilities!"""

    import logging
    from openai import BadRequestError

    logger = logging.getLogger(__name__)

    # Retry logic for JSON validation errors
    max_retries = 2
    last_error = None

    for attempt in range(max_retries):
        try:
            # Get raw JSON response without strict Pydantic validation
            # We'll handle the data leniently to be resilient to LLM weirdness
            extraction_response_json = await llm_config.call(
                messages=[
                    {
                        "role": "system",
                        "content": "Extract ALL meaningful content. NEVER MISS USER REQUESTS - if user asks assistant to do something ('write...', 'create...', 'help me...'), extract BOTH request AND response as separate BANK facts! COMBINE simple informational Q&A. BANK facts: use 'I' for assistant actions ('I recommended'), use 'user'/name for user actions ('User requested', 'Marcus said'). CONVERT RELATIVE DATES TO SPECIFIC DATES ('last week' → 'around Aug 16' NOT 'in August'!). factual_core = WHAT was said, not THAT something was said! fact_kind: 'conversation'/'event'/'other'. Only 'event' gets occurred dates. Optional fields: include 'entities', 'causal_relations', 'occurred_start', 'occurred_end', 'emotional_significance', 'reasoning_motivation', 'preferences_opinions', 'sensory_details', 'observations' only if they have meaningful values (can omit if not applicable)."
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
                skip_validation=True,  # Get raw JSON, we'll validate leniently
            )

            # Lenient parsing of facts from raw JSON
            chunk_facts = []

            # Handle malformed LLM responses
            if not isinstance(extraction_response_json, dict):
                logger.warning(
                    f"LLM returned non-dict JSON: {type(extraction_response_json).__name__}. "
                    f"Raw: {str(extraction_response_json)[:500]}"
                )
                return []

            raw_facts = extraction_response_json.get('facts', [])
            if not raw_facts:
                logger.warning(
                    f"LLM response missing 'facts' field or returned empty list. "
                    f"Keys: {list(extraction_response_json.keys())}"
                )

            for i, llm_fact in enumerate(raw_facts):
                # Skip non-dict entries
                if not isinstance(llm_fact, dict):
                    logger.warning(f"Skipping non-dict fact at index {i}")
                    continue

                # Critical field: factual_core (MUST have this)
                factual_core = llm_fact.get('factual_core')
                if not factual_core:
                    logger.warning(f"Skipping fact {i}: missing factual_core")
                    continue

                # Critical field: fact_type
                # LLM uses "assistant" but we convert to "bank" for storage
                fact_type = llm_fact.get('fact_type')

                # Convert "assistant" → "bank" for storage
                if fact_type == 'assistant':
                    fact_type = 'bank'

                # Validate fact_type (after conversion)
                if fact_type not in ['world', 'bank', 'opinion']:
                    # Try to fix common mistakes - check if they swapped fact_type and fact_kind
                    fact_kind = llm_fact.get('fact_kind')
                    if fact_kind == 'assistant':
                        fact_type = 'bank'
                    elif fact_kind in ['world', 'bank', 'opinion']:
                        fact_type = fact_kind
                    else:
                        # Default to 'world' if we can't determine
                        fact_type = 'world'
                        logger.warning(f"Fact {i}: defaulting to fact_type='world'")

                # Get fact_kind for temporal handling (but don't store it)
                fact_kind = llm_fact.get('fact_kind', 'conversation')
                if fact_kind not in ['conversation', 'event', 'other']:
                    fact_kind = 'conversation'

                # Build combined fact text from dimensions
                dimension_parts = []
                fact_data = {}

                # Helper to get non-empty value
                def get_value(field_name):
                    value = llm_fact.get(field_name)
                    if value and value != '' and value != [] and value != {}:
                        return value
                    return None

                # Collect dimension fields
                for field in ['emotional_significance', 'reasoning_motivation', 'preferences_opinions',
                              'sensory_details', 'observations']:
                    value = get_value(field)
                    if value:
                        fact_data[field] = value
                        dimension_parts.append(value)

                # Build combined fact text
                combined_parts = [factual_core] + dimension_parts
                if len(combined_parts) == 1:
                    combined_text = combined_parts[0]
                else:
                    combined_text = f"{combined_parts[0]} - {' - '.join(combined_parts[1:])}"

                # Add temporal fields
                # For events: occurred_start/occurred_end (when the event happened)
                if fact_kind == 'event':
                    occurred_start = get_value('occurred_start')
                    occurred_end = get_value('occurred_end')
                    if occurred_start:
                        fact_data['occurred_start'] = occurred_start
                    if occurred_end:
                        fact_data['occurred_end'] = occurred_end

                # Add entities if present (validate as Entity objects)
                # LLM sometimes returns strings instead of {"text": "..."} format
                entities = get_value('entities')
                if entities:
                    # Validate and normalize each entity
                    validated_entities = []
                    for ent in entities:
                        if isinstance(ent, str):
                            # Normalize string to Entity object
                            validated_entities.append(Entity(text=ent))
                        elif isinstance(ent, dict) and 'text' in ent:
                            try:
                                validated_entities.append(Entity.model_validate(ent))
                            except Exception as e:
                                logger.warning(f"Invalid entity {ent}: {e}")
                    if validated_entities:
                        fact_data['entities'] = validated_entities

                # Add causal relations if present (validate as CausalRelation objects)
                # Filter out invalid relations (missing required fields)
                causal_relations = get_value('causal_relations')
                if causal_relations:
                    validated_relations = []
                    for rel in causal_relations:
                        if isinstance(rel, dict) and 'target_fact_index' in rel and 'relation_type' in rel:
                            try:
                                validated_relations.append(CausalRelation.model_validate(rel))
                            except Exception as e:
                                logger.warning(f"Invalid causal relation {rel}: {e}")
                    if validated_relations:
                        fact_data['causal_relations'] = validated_relations

                # Always set mentioned_at to the event_date (when the conversation/document occurred)
                fact_data['mentioned_at'] = event_date.isoformat()

                # Build Fact model instance
                try:
                    fact = Fact(
                        fact=combined_text,
                        fact_type=fact_type,
                        **fact_data
                    )
                    chunk_facts.append(fact)
                except Exception as e:
                    logger.error(f"Failed to create Fact model for fact {i}: {e}")
                    continue
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
    agent_name: str = None,
    extract_opinions: bool = False
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
        extract_opinions: If True, extract ONLY opinions. If False, extract world and agent facts (no opinions)

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
            agent_name=agent_name,
            extract_opinions=extract_opinions
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
                agent_name=agent_name,
                extract_opinions=extract_opinions
            ),
            _extract_facts_with_auto_split(
                chunk=second_half,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                event_date=event_date,
                context=context,
                llm_config=llm_config,
                agent_name=agent_name,
                extract_opinions=extract_opinions
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
    extract_opinions: bool = False,
) -> tuple[List[Fact], List[tuple[str, int]]]:
    """
    Extract semantic facts from conversational or narrative text using LLM.

    For large texts (>3000 chars), automatically chunks at sentence boundaries
    to avoid hitting output token limits. Processes ALL chunks in PARALLEL for speed.

    If a chunk produces output that exceeds token limits (OutputTooLongError), it is
    automatically split in half and retried recursively until successful.

    Args:
        text: Input text (conversation, article, etc.)
        event_date: Reference date for resolving relative times
        context: Context about the conversation/document
        llm_config: LLM configuration to use
        agent_name: Agent name (memory owner)
        extract_opinions: If True, extract ONLY opinions. If False, extract world and bank facts (no opinions)

    Returns:
        Tuple of (facts, chunks) where:
        - facts: List of Fact model instances
        - chunks: List of tuples (chunk_text, fact_count) for each chunk
    """
    chunks = chunk_text(text, max_chars=3000)
    tasks = [
        _extract_facts_with_auto_split(
            chunk=chunk,
            chunk_index=i,
            total_chunks=len(chunks),
            event_date=event_date,
            context=context,
            llm_config=llm_config,
            agent_name=agent_name,
            extract_opinions=extract_opinions
        )
        for i, chunk in enumerate(chunks)
    ]
    chunk_results = await asyncio.gather(*tasks)
    all_facts = []
    chunk_metadata = []  # [(chunk_text, fact_count), ...]
    for chunk, chunk_facts in zip(chunks, chunk_results):
        all_facts.extend(chunk_facts)
        chunk_metadata.append((chunk, len(chunk_facts)))
    return all_facts, chunk_metadata


# ============================================================================
# ORCHESTRATION LAYER
# ============================================================================

# Import types for the orchestration layer (note: ExtractedFact here is different from the Pydantic model above)
from .types import RetainContent, ExtractedFact as ExtractedFactType, ChunkMetadata, CausalRelation as CausalRelationType
from typing import Tuple

logger = logging.getLogger(__name__)

# Each fact gets 10 seconds offset to preserve ordering within a document
SECONDS_PER_FACT = 10


async def extract_facts_from_contents(
    contents: List[RetainContent],
    llm_config,
    agent_name: str,
    extract_opinions: bool = False
) -> Tuple[List[ExtractedFactType], List[ChunkMetadata]]:
    """
    Extract facts from multiple content items in parallel.

    This function:
    1. Extracts facts from all contents in parallel using the LLM
    2. Tracks which facts came from which chunks
    3. Adds time offsets to preserve fact ordering within each content
    4. Returns typed ExtractedFact and ChunkMetadata objects

    Args:
        contents: List of RetainContent objects to process
        llm_config: LLM configuration for fact extraction
        agent_name: Name of the agent (for agent-related fact detection)
        extract_opinions: If True, extract only opinions; otherwise world/bank facts

    Returns:
        Tuple of (extracted_facts, chunks_metadata)
    """
    if not contents:
        return [], []

    # Step 1: Create parallel fact extraction tasks
    fact_extraction_tasks = []
    for item in contents:
        # Call extract_facts_from_text directly (defined earlier in this file)
        # to avoid circular import with utils.extract_facts
        task = extract_facts_from_text(
            text=item.content,
            event_date=item.event_date,
            context=item.context,
            llm_config=llm_config,
            agent_name=agent_name,
            extract_opinions=extract_opinions
        )
        fact_extraction_tasks.append(task)

    # Step 2: Wait for all fact extractions to complete
    all_fact_results = await asyncio.gather(*fact_extraction_tasks)

    # Step 3: Flatten and convert to typed objects
    extracted_facts: List[ExtractedFactType] = []
    chunks_metadata: List[ChunkMetadata] = []

    global_chunk_idx = 0
    global_fact_idx = 0

    for content_index, (content, (facts_from_llm, chunks_from_llm)) in enumerate(zip(contents, all_fact_results)):
        chunk_start_idx = global_chunk_idx

        # Convert chunk tuples to ChunkMetadata objects
        for chunk_index_in_content, (chunk_text, chunk_fact_count) in enumerate(chunks_from_llm):
            chunk_metadata = ChunkMetadata(
                chunk_text=chunk_text,
                fact_count=chunk_fact_count,
                content_index=content_index,
                chunk_index=global_chunk_idx
            )
            chunks_metadata.append(chunk_metadata)
            global_chunk_idx += 1

        # Convert facts to ExtractedFact objects with proper indexing
        fact_idx_in_content = 0
        for chunk_idx_in_content, (chunk_text, chunk_fact_count) in enumerate(chunks_from_llm):
            chunk_global_idx = chunk_start_idx + chunk_idx_in_content

            for _ in range(chunk_fact_count):
                if fact_idx_in_content < len(facts_from_llm):
                    fact_from_llm = facts_from_llm[fact_idx_in_content]

                    # Convert Fact model from LLM to ExtractedFactType dataclass
                    # mentioned_at is always the event_date (when the conversation/document occurred)
                    extracted_fact = ExtractedFactType(
                        fact_text=fact_from_llm.fact,
                        fact_type=fact_from_llm.fact_type,
                        entities=[e.text for e in (fact_from_llm.entities or [])],
                        # occurred_start/end: from LLM only, leave None if not provided
                        occurred_start=_parse_datetime(fact_from_llm.occurred_start) if fact_from_llm.occurred_start else None,
                        occurred_end=_parse_datetime(fact_from_llm.occurred_end) if fact_from_llm.occurred_end else None,
                        causal_relations=_convert_causal_relations(
                            fact_from_llm.causal_relations or [],
                            global_fact_idx
                        ),
                        content_index=content_index,
                        chunk_index=chunk_global_idx,
                        context=content.context,
                        # mentioned_at: always the event_date (when the conversation/document occurred)
                        mentioned_at=content.event_date,
                        metadata=content.metadata
                    )

                    extracted_facts.append(extracted_fact)
                    global_fact_idx += 1
                    fact_idx_in_content += 1

    # Step 4: Add time offsets to preserve ordering within each content
    _add_temporal_offsets(extracted_facts, contents)

    return extracted_facts, chunks_metadata


def _parse_datetime(date_str: str):
    """Parse ISO datetime string."""
    from dateutil import parser as date_parser
    try:
        return date_parser.isoparse(date_str)
    except Exception:
        return None


def _convert_causal_relations(relations_from_llm, fact_start_idx: int) -> List[CausalRelationType]:
    """
    Convert causal relations from LLM format to ExtractedFact format.

    Adjusts target_fact_index from content-relative to global indices.
    """
    causal_relations = []
    for rel in relations_from_llm:
        causal_relation = CausalRelationType(
            relation_type=rel.relation_type,
            target_fact_index=fact_start_idx + rel.target_fact_index,
            strength=rel.strength
        )
        causal_relations.append(causal_relation)
    return causal_relations


def _add_temporal_offsets(facts: List[ExtractedFactType], contents: List[RetainContent]) -> None:
    """
    Add time offsets to preserve fact ordering within each content.

    This allows retrieval to distinguish between facts that happened earlier vs later
    in the same conversation, even when the base event_date is the same.

    Modifies facts in place.
    """
    # Group facts by content_index
    current_content_idx = 0
    content_fact_start = 0

    for i, fact in enumerate(facts):
        if fact.content_index != current_content_idx:
            # Moved to next content
            current_content_idx = fact.content_index
            content_fact_start = i

        # Calculate position within this content
        fact_position = i - content_fact_start
        offset = timedelta(seconds=fact_position * SECONDS_PER_FACT)

        # Apply offset to all temporal fields
        if fact.occurred_start:
            fact.occurred_start = fact.occurred_start + offset
        if fact.occurred_end:
            fact.occurred_end = fact.occurred_end + offset
        if fact.mentioned_at:
            fact.mentioned_at = fact.mentioned_at + offset
