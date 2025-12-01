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
        description="Observations, inferences, and specific details/metrics as a COMPLETE SENTENCE. Include subject + observed fact. Use this to capture: background facts, achievements, metrics, personal records, skills. Examples: 'Calvin traveled to Miami for the shoot', 'Gina won dance trophies in competitions', 'She knows programming from previous projects', 'User's personal best 5K time is 25:50', 'Sarah has completed 15 marathons', 'He speaks three languages fluently'"
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
        description="WHEN THE EVENT ACTUALLY HAPPENED (not when mentioned). ISO timestamp. For datable events only (fact_kind='event'). Examples: 'went to Tokyo last spring' on June 10 → occurred_start='2024-03-01' (spring start), 'accident yesterday' on March 15 → occurred_start='2024-03-14' (yesterday). Leave null for general info (fact_kind='conversation')."
    )
    occurred_end: Optional[str] = Field(
        default=None,
        description="WHEN THE EVENT ACTUALLY ENDED (not when mentioned). ISO timestamp. For datable events with duration (fact_kind='event'). Examples: 'went to Tokyo last spring' → occurred_end='2024-05-31' (spring end). Can be same as occurred_start for single-day events. Leave null for general info."
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

    prompt = f"""Extract comprehensive facts from user text for an AI memory system.

{fact_types_instruction}

## CONTEXT
- Context: {context if context else 'none'}{agent_context}

═══════════════════════════════════════════════════════════════════════════════
SECTION 1: TEMPORAL HANDLING (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

### 1.1 DETECT TEMPORAL MARKERS
Watch for: "yesterday", "last week/month/year/summer", "ago", "tomorrow", "next", "happened", "occurred", past tense verbs ("went", "visited", "saw")

### 1.2 DUAL FACT CREATION (KEY RULE)
When text mentions a past/future event → Create TWO facts:
1. MENTION FACT: "On [context date], it was mentioned that..." (occurred_start = context date)
2. EVENT FACT: "[Action] in [absolute date]" (occurred_start = actual event date)

### 1.3 ABSOLUTE DATE CONVERSION
ALWAYS convert relative → absolute in factual_core text:
- "yesterday" → "on [date-1]"
- "last week" → "around [specific week]"
- "last summer" → "in summer [year] (June-August [year])"
- "next month" → "in [month name] [year]"

### 1.4 occurred_start/end FIELDS ⚠️ CRITICAL

**WHAT THEY REPRESENT:**
- occurred_start/end = WHEN THE EVENT ACTUALLY HAPPENED (NOT when it was mentioned!)
- These answer: "When did this event occur in reality?"

**WHEN TO SET THEM:**
✅ SET for datable events (fact_kind="event"):
   - "went to Tokyo last spring" → occurred_start = March 1, 2024 (spring started)
   - "accident yesterday" → occurred_start = context date - 1 day
   - "party next Saturday" → occurred_start = next Saturday's date

❌ LEAVE NULL for general info (fact_kind="conversation"):
   - "loves coffee" → no occurred dates (timeless preference)
   - "works as engineer" → no occurred dates (ongoing state)
   - "is expanding business" → no occurred dates (ongoing activity)

**KEY DISTINCTION:**
- occurred_start/end: When the event happened/will happen
- mentioned_at: When this was said/written (set automatically to context date)
- These are DIFFERENT! Example: On June 10, saying "went to Tokyo in March" → occurred_start=March, mentioned_at=June 10

**FORMAT:** ISO timestamps "2024-06-15T00:00:00Z"

### 1.5 EXAMPLES - STUDY THESE CAREFULLY

**Example 1: "yesterday" temporal detection**
Input (Context: March 15, 2024): "Hey Taylor! The volunteers were amazing yesterday. But something unexpected happened - a vehicle accident near the center. Everyone was okay though."

Output (3 facts):
1. factual_core: "On March 15, 2024, Alex told Taylor that the volunteers were amazing"
   occurred_start: "2024-03-15T00:00:00Z", entities: ["Alex", "Taylor"]

2. factual_core: "On March 15, 2024, Alex mentioned that something unexpected happened the previous day - a vehicle accident"
   occurred_start: "2024-03-15T00:00:00Z", entities: ["Alex"]

3. factual_core: "On March 14, 2024, a vehicle accident occurred near the center, but everyone was okay"
   occurred_start: "2024-03-14T00:00:00Z" ← THE ACTUAL EVENT DATE (yesterday from March 15)

**Example 2: "last spring" temporal detection**
Input (Context: June 10, 2024): "Casey went to Tokyo last spring. They had an incredible time visiting temples and trying authentic ramen."

Output (2 facts):
1. factual_core: "On June 10, 2024, it was mentioned that Casey went to Tokyo the previous spring"
   occurred_start: "2024-06-10T00:00:00Z", entities: ["Casey", "Tokyo"]

2. factual_core: "Casey went to Tokyo in spring 2024 (March-May 2024) and visited temples and tried authentic ramen"
   occurred_start: "2024-03-01T00:00:00Z", occurred_end: "2024-05-31T23:59:59Z" ← THE ACTUAL EVENT DATES
   emotional_significance: "Casey had an incredible time in Tokyo"
   entities: ["Casey", "Tokyo"]

═══════════════════════════════════════════════════════════════════════════════
SECTION 2: EXTRACTION RULES
═══════════════════════════════════════════════════════════════════════════════

### 2.1 WHAT TO EXTRACT
✅ User requests to assistant + assistant actions (extract separately)
✅ Preferences, recommendations, plans, activities, encouragement (with actual content)
✅ Possessions, achievements, metrics, skills, background facts

### 2.2 WHAT TO SKIP
❌ Greetings, filler ("thanks", "cool"), structural statements

### 2.3 Q&A HANDLING
- Combine simple informational Q&A into one fact
- Split user requests to assistant into two facts (request + response)

═══════════════════════════════════════════════════════════════════════════════
SECTION 3: STRUCTURED DIMENSIONS
═══════════════════════════════════════════════════════════════════════════════

### 3.1 REQUIRED FIELD
- **factual_core**: Capture WHAT was said, not just THAT something was said. Complete sentence.

### 3.2 OPTIONAL FIELDS (use when present in text)
- **emotional_significance**: Emotions, feelings, qualitative descriptors. Complete sentence with subject.
- **reasoning_motivation**: Why it happened, intentions, goals. Complete sentence with subject.
- **preferences_opinions**: Likes, dislikes, beliefs, values. Complete sentence with subject. Use for: "ideal", "favorite", "dream", "perfect"
- **sensory_details**: Visual, auditory, physical descriptions. Complete sentence. USE EXACT WORDS from text!
- **observations**: Background facts, possessions, achievements, metrics, skills. Complete sentence with subject.

### 3.3 FORMATTING RULE
Each dimension MUST be a complete, grammatically correct sentence with subject that can stand alone.

═══════════════════════════════════════════════════════════════════════════════
SECTION 4: FACT CLASSIFICATION
═══════════════════════════════════════════════════════════════════════════════

### 4.1 fact_kind (temporal nature)
- **conversation**: General info, ongoing activities (no occurred dates)
- **event**: Specific datable occurrence (MUST set occurred_start/end)
- **other**: Catch-all

### 4.2 fact_type (subject matter)
- **world**: Everything NOT involving assistant (user background, other people, events)
- **assistant**: Interactions BY or TO assistant (requests, recommendations, actions in THIS conversation)

Rule: If it would exist without this conversation → world. If only exists because of this conversation → assistant.

═══════════════════════════════════════════════════════════════════════════════
SECTION 5: ENTITIES & CAUSALITY
═══════════════════════════════════════════════════════════════════════════════

### 5.1 ENTITIES
Extract: People names, organizations, specific places, products
Skip: Generic relations (mom, friend), pronouns, common nouns

### 5.2 CAUSAL RELATIONS
Link facts when explicit causation: causes, caused_by, enables, prevents"""


    import logging
    from openai import BadRequestError

    logger = logging.getLogger(__name__)

    # Retry logic for JSON validation errors
    max_retries = 2
    last_error = None

    # inject all the chunk metadata for better reasoning
    chunk_data = json.dumps({
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "event_date": event_date.isoformat(),
        "context": context,
        "chunk_content": chunk
    })
    for attempt in range(max_retries):
        try:
            extraction_response_json = await llm_config.call(
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": chunk_data
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
                    f"Response: {extraction_response_json}"
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
                        # Handle case where LLM returns list instead of string
                        if isinstance(value, list):
                            value = '; '.join(str(v) for v in value)
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
