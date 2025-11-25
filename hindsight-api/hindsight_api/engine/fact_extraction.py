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
    """A single extracted fact from text with temporal range and causal relationships."""
    fact: str = Field(
        description="Self-contained factual statement with subject + action + context"
    )
    occurred_start: str = Field(
        description="When the fact/event started (ISO format YYYY-MM-DDTHH:MM:SSZ). "
                   "For point-in-time events (single day), same as occurred_end. "
                   "For periods/ranges (month, season, year), the start of that period. "
                   "Calculate absolute dates from relative references like 'yesterday', 'last week'."
    )
    occurred_end: str = Field(
        description="When the fact/event ended (ISO format YYYY-MM-DDTHH:MM:SSZ). "
                   "For point-in-time events (single day), same as occurred_start. "
                   "For periods/ranges (month, season, year), the end of that period. "
                   "For ongoing facts, use the conversation date or a reasonable future date."
    )
    fact_type: Literal["world", "agent", "opinion"] = Field(
        description="Type of fact: 'world' for facts about others that don't involve you (the agent) directly, 'agent' for facts that involve YOU (the agent whose memory this is) - what you did, said, experienced, or participated in - MUST be written in FIRST PERSON ('I did...', 'I said...', 'I met...'), 'opinion' for YOUR formed opinions and perspectives - also in first person"
    )
    entities: List[Entity] = Field(
        default_factory=list,
        description="List of important entities mentioned in this fact with their types"
    )
    causal_relations: Optional[List[CausalRelation]] = Field(
        default=None,
        description="List of causal relationships to other facts in this extraction batch. "
                   "Use this to link facts that have cause-effect relationships, enabling relationships, etc. "
                   "Example: If fact 0 is 'It rained' and fact 1 is 'Game was cancelled', "
                   "fact 0 would have causal_relations=[{{target_fact_index: 1, relation_type: 'causes', strength: 1.0}}]"
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
    agent_name: str = None,
    extract_opinions: bool = False
) -> List[Dict[str, str]]:
    """
    Extract facts from a single chunk (internal helper for parallel processing).
    """
    # Format event_date for the prompt
    event_date_str = event_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    agent_context = f"\n- Your name: {agent_name}" if agent_name else ""

    # Determine which fact types to extract based on the flag
    if extract_opinions:
        fact_types_instruction = "Extract ONLY 'opinion' type facts (the agent's formed opinions, beliefs, and perspectives). DO NOT extract 'world' or 'agent' facts."
    else:
        fact_types_instruction = "Extract ONLY 'world' and 'agent' type facts. DO NOT extract 'opinion' type facts - opinions should never be created during normal memory storage."

    prompt = f"""You are extracting comprehensive, narrative facts from conversations/document for an AI memory system.

{fact_types_instruction}

## CONTEXT INFORMATION
- Today time: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
- Current document date/time: {event_date_str}
- Context: {context if context else 'no additional context provided'}{agent_context}

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

## INFORMATION DIMENSIONS TO CAPTURE

Extract facts that preserve ALL relevant dimensions of information. Do NOT strip away important qualitative details:

### 1. EMOTIONAL/AFFECTIVE Dimension - CRITICAL ⚠️
**Capture feelings, emotions, moods, and emotional reactions with their intensity:**
- Emotions: thrilled, frustrated, excited, disappointed, anxious, relieved, proud, embarrassed
- Intensity: very upset, slightly annoyed, extremely happy, moderately concerned
- Emotional reactions: shocked, delighted, devastated, surprised
- Moods: cheerful, gloomy, irritable, energetic

**Examples:**
- ❌ BAD: "I received positive feedback"
- ✅ GOOD: "I was thrilled to receive positive feedback"
- ❌ BAD: "She got the promotion"
- ✅ GOOD: "She was ecstatic when she got the promotion"

### 2. SENSORY/EXPERIENTIAL Dimension
**Preserve sensory details and physical experiences:**
- Visual: colors, appearances ("bright orange hair", "dark room", "beautiful sunset")
- Auditory: sounds, voices ("loud music", "whispered", "screeching brakes")
- Tactile: textures, temperatures ("soft fabric", "freezing cold", "rough surface")
- Olfactory: smells, scents ("fresh coffee", "musty odor")
- Gustatory: tastes, flavors ("bitter coffee", "sweet dessert")
- Physical sensations: pain, fatigue, energy ("my back hurt", "I felt exhausted", "energized")

### 3. COGNITIVE/EPISTEMIC Dimension
**Capture thoughts, beliefs, knowledge, and certainty levels:**
- Beliefs: "I believe...", "she thinks...", "he's convinced that..."
- Knowledge: "I know how to...", "she learned that...", "he discovered..."
- Understanding: "I realized...", "she understood that...", "it became clear that..."
- Certainty: "I'm sure that...", "probably...", "definitely..."
- Uncertainty: "I'm not sure if...", "maybe...", "I wonder whether...", "she doubts that..."
- Questions/Doubts: unresolved questions, things people are wondering about

### 4. INTENTIONAL/MOTIVATIONAL Dimension
**Preserve goals, plans, intentions, and motivations:**
- Goals: "I want to...", "she aims to...", "his goal is..."
- Plans: "I'm planning to...", "they intend to...", "she's going to..."
- Motivations: "I did X because I wanted Y", "her motivation was..."
- Desires: "I wish...", "she hopes...", "he longs to..."
- Aspirations: "I aspire to...", "her dream is..."

### 5. EVALUATIVE/PREFERENTIAL Dimension
**Capture preferences, values, likes/dislikes, and judgments:**
- Preferences: "I prefer X to Y", "she likes coffee better than tea"
- Likes/dislikes: "I love...", "he hates...", "she enjoys..."
- Values: "I value honesty above all", "family is most important to her"
- Judgments: "that was wrong", "this is the best option", "it's unfair that..."
- Priorities: "X is more important than Y", "first priority is..."

### 6. CAPABILITY/SKILL Dimension
**Preserve abilities, skills, expertise, and limitations:**
- Abilities: "I can speak French", "she's able to...", "he knows how to..."
- Skills: "I'm good at programming", "she's skilled in...", "he's proficient at..."
- Expertise: "I'm an expert in AI", "she specializes in...", "he's experienced with..."
- Limitations: "I can't swim", "she struggles with public speaking", "he's unable to..."
- Competence levels: "beginner", "intermediate", "advanced", "expert"

### 7. ATTITUDINAL/REACTIVE Dimension
**Capture attitudes, reactions, and behavioral responses:**
- Attitudes: "she's skeptical about...", "he's enthusiastic about...", "I'm optimistic that..."
- Reactions: "I was surprised when...", "she gasped", "he rolled his eyes"
- Behavioral responses: "I jumped up", "she turned away", "he slammed the door"
- Dispositions: "she tends to...", "he's usually...", "I typically..."

### 8. COMPARATIVE/RELATIVE Dimension
**Preserve comparisons, contrasts, and changes:**
- Comparisons: "better than last time", "worse than expected", "similar to..."
- Superlatives: "the best", "the worst", "the most important"
- Changes: "improved since...", "declined from...", "different than before"
- Contrasts: "unlike his previous approach", "in contrast to...", "rather than..."
- Relative positions: "more than", "less than", "as much as"

### 9. CAUSAL/EXPLANATORY Dimension
**Preserve causes, effects, and explanations:**
- Causes: "because...", "due to...", "as a result of..."
- Effects: "therefore...", "which led to...", "resulting in..."
- Explanations: reasoning, rationales, why things happened
- Conditions: "if...", "when...", "unless..."

**CRITICAL REMINDER**: When extracting facts, preserve ALL these dimensions that are present in the text. Do NOT reduce rich, emotionally-laden statements to bare facts. The goal is comprehensive, nuanced memory capture.

## TEMPORAL INFORMATION - CRITICAL ⚠️

**ABSOLUTE RULE**: NEVER use vague temporal terms in extracted facts. ALL relative time expressions MUST be converted to absolute dates or specific relative references.

### PROHIBITED VAGUE TERMS ❌
NEVER use these in facts: "recently", "soon", "lately", "a while ago", "some time ago", "in the near future", "in the past"

### REQUIRED TRANSFORMATIONS

You have two context dates:
1. **event_date** (when the conversation/document occurred)
2. **today** (current processing time)

Transform ALL relative temporal expressions in the fact text based on **event_date**:

**Examples** (assuming event_date = 2024-03-15):
- "yesterday" → "on March 14, 2024" OR "the day before" (if referring to day before event_date)
- "today" → "on March 15, 2024" (event_date itself)
- "tomorrow" → "on March 16, 2024"
- "last week" → "in the week of March 4-10, 2024" OR "in early March 2024"
- "next week" → "in the week of March 18-24, 2024"
- "last month" → "in February 2024"
- "next month" → "in April 2024"
- "last year" → "in 2023"
- "this morning" → "on the morning of March 15, 2024"
- "three days ago" → "on March 12, 2024"
- "in two weeks" → "around March 29, 2024"

### TRANSFORMING THE USER'S EXAMPLE
**Input**: "And yesterday I went for a morning jog for the first time in a nearby park."
**event_date**: 2024-03-15

❌ **WRONG**: "recently added a morning jog in a nearby park to her schedule"
- Uses prohibited vague term "recently"
- Lost the specificity of "yesterday"

✅ **CORRECT**: "went for a morning jog for the first time in a nearby park on March 14, 2024"
- Converts "yesterday" to absolute date
- Preserves "first time" (important!)

### DATE FIELD CALCULATION - CRITICAL ⚠️

**ABSOLUTE RULE**: The `date` field must be when the FACT occurred, NOT when it was mentioned in conversation.

**You have access to:**
- **event_date**: When the conversation/document occurred (e.g., "2023-08-14")
- Your job: Calculate when the fact ACTUALLY happened based on temporal references

**Examples:**

1. **"Last night" reference**
   - Conversation date (event_date): August 14, 2023
   - Text: "Last night was amazing! We celebrated my daughter's birthday"
   - ❌ WRONG date field: 2023-08-14 (conversation date)
   - ✅ CORRECT date field: 2023-08-13T20:00:00Z (last night = previous evening)

2. **"Yesterday" reference**
   - Conversation date: March 15, 2024
   - Text: "Yesterday I went jogging"
   - ❌ WRONG date field: 2024-03-15
   - ✅ CORRECT date field: 2024-03-14 (previous day)

3. **"Last week" reference**
   - Conversation date: November 13, 2024
   - Text: "I started a project last week"
   - ❌ WRONG date field: 2024-11-13
   - ✅ CORRECT date field: 2024-11-06 (approximately a week before)

4. **"Next month" reference**
   - Conversation date: March 15, 2024
   - Text: "I'm visiting Tokyo next month"
   - ❌ WRONG date field: 2024-03-15
   - ✅ CORRECT date field: 2024-04-15 (approximately a month later)

5. **No specific time mentioned**
   - Conversation date: November 13, 2024
   - Text: "I work at Google"
   - ✅ CORRECT date field: 2024-11-13 (use event_date when no time reference)

### CALCULATION GUIDELINES

- "last night" → subtract 1 day from event_date, set time to evening (~20:00)
- "yesterday" → subtract 1 day from event_date
- "today" → use event_date
- "tomorrow" → add 1 day to event_date
- "last week" → subtract 7 days from event_date
- "next week" → add 7 days to event_date
- "last month" → subtract 1 month from event_date
- "next month" → add 1 month to event_date
- "X days ago" → subtract X days from event_date
- "in X days" → add X days to event_date

### DATE FIELD vs FACT TEXT

- **date field**: ISO format (YYYY-MM-DDTHH:MM:SSZ) for when the fact OCCURRED (calculated as above)
- **fact text**: Readable format (e.g., "on August 13, 2024", "in February 2024")

### IF NO SPECIFIC TIME MENTIONED
ONLY use event_date when the text doesn't specify a time reference (e.g., "I work at Google", "She lives in Paris")

## TEMPORAL RANGES: occurred_start and occurred_end - CRITICAL ⚠️

**ABSOLUTE RULE**: Facts have temporal extent - they can be points or ranges in time.

### POINT-IN-TIME EVENTS (Single Day)
When an event happens on a specific day, set start = end:

```
"I went jogging on August 13, 2023"
occurred_start: 2023-08-13T00:00:00Z
occurred_end:   2023-08-13T23:59:59Z
```

```
"Yesterday I visited the museum"  (if event_date = Aug 14)
occurred_start: 2023-08-13T00:00:00Z
occurred_end:   2023-08-13T23:59:59Z
```

### PERIOD/RANGE EVENTS (Multiple Days/Months/Years)
When an event spans time, set start and end to the full range:

```
"I visited Paris in February 2023"
occurred_start: 2023-02-01T00:00:00Z
occurred_end:   2023-02-28T23:59:59Z
```

```
"I worked at Google from 2020 to 2023"
occurred_start: 2020-01-01T00:00:00Z
occurred_end:   2023-12-31T23:59:59Z
```

```
"We've been painting together lately"  (vague, estimate reasonable range)
occurred_start: 2023-07-01T00:00:00Z  (estimate past weeks/months)
occurred_end:   2023-07-14T23:59:59Z  (conversation date)
```

### ONGOING/PRESENT FACTS
For current/ongoing states, use conversation date as end:

```
"I currently work at Google"  (started 2020)
occurred_start: 2020-01-01T00:00:00Z
occurred_end:   [conversation_date]  (ongoing)
```

## TEMPORAL SPLITTING: When to Split Multi-Event Facts - CRITICAL ⚠️

**NEW PRINCIPLE**: Split facts when they have significantly different temporal scopes.

### SPLIT into separate facts when:
- ❌ Events span >7 days apart
- ❌ Mix of specific dates + vague ongoing periods ("lately")
- ❌ Multiple discrete events with independent temporal significance

**Example - SPLIT THIS:**
```
Input: "Melanie took kids to pottery on July 14. She shared a photo on July 13.
        She's been painting with them lately."

✅ CORRECT (3 separate facts with causal links):

Fact 0:
fact: "Melanie took her kids to a pottery workshop on July 14, 2023, where they each made their own pots, describing it as fun and therapeutic."
occurred_start: 2023-07-14T00:00:00Z
occurred_end: 2023-07-14T23:59:59Z
causal_relations: [{{target_fact_index: 1, relation_type: "enables", strength: 1.0}}]

Fact 1:
fact: "Melanie shared a photo on July 13, 2023, of a cup her kids made, noting its cuteness and how it showcased their personalities."
occurred_start: 2023-07-13T00:00:00Z
occurred_end: 2023-07-13T23:59:59Z
causal_relations: [{{target_fact_index: 0, relation_type: "caused_by", strength: 1.0}}]

Fact 2:
fact: "Melanie and her kids have been painting together lately, especially nature-inspired pieces, finding it a bonding experience."
occurred_start: 2023-07-01T00:00:00Z  (estimate "lately")
occurred_end: 2023-07-14T23:59:59Z
causal_relations: None  (related activity but no direct causation)
```

### KEEP COMBINED when:
- ✅ Events occur within same day/week
- ✅ Events are part of continuous single activity
- ✅ One main event + immediate context

**Example - KEEP COMBINED:**
```
Input: "On July 14, Alice attended a conference, gave a talk, and met with colleagues"

✅ CORRECT (single fact):
fact: "On July 14, 2023, Alice attended a conference where she gave a talk and met with colleagues"
occurred_start: 2023-07-14T00:00:00Z
occurred_end: 2023-07-14T23:59:59Z
```

## CAUSAL RELATIONSHIPS - NEW FEATURE ⚠️

**When splitting related facts, identify and mark causal relationships.**

### Causal Relation Types:

1. **"causes"** - This fact directly causes the target fact
   ```
   Fact 0: "Karlie died in February 2023"
   Fact 1: "Deborah spends time in garden to cope with grief"
   → Fact 0 causal_relations: [{{target_fact_index: 1, relation_type: "causes", strength: 1.0}}]
   ```

2. **"caused_by"** - This fact was caused by the target fact (reverse of "causes")
   ```
   Fact 0: "It rained heavily"
   Fact 1: "Game was cancelled"
   → Fact 1 causal_relations: [{{target_fact_index: 0, relation_type: "caused_by", strength: 1.0}}]
   ```

3. **"enables"** - This fact enables/allows the target fact
   ```
   Fact 0: "I took pottery class"
   Fact 1: "I learned to make ceramics"
   → Fact 0 causal_relations: [{{target_fact_index: 1, relation_type: "enables", strength: 1.0}}]
   ```

4. **"prevents"** - This fact prevents/blocks the target fact
   ```
   Fact 0: "Road was closed"
   Fact 1: "We couldn't drive to venue"
   → Fact 0 causal_relations: [{{target_fact_index: 1, relation_type: "prevents", strength: 1.0}}]
   ```

### When to Create Causal Links:
- **DO link** when: Text explicitly states causation ("because", "so", "therefore", "as a result")
- **DO link** when: Clear logical causation even if not explicit
- **DON'T link** when: Events are merely related but not causal

### Causal Link Examples:

**Example 1: Explicit causation**
```
Input: "I lost my friend last week, so I've been spending time in the garden to find comfort"

Fact 0: "I lost my friend on February 15, 2023"
Fact 1: "I have been spending time in the garden to find comfort after losing my friend"
→ Fact 0 causal_relations: [{{target_fact_index: 1, relation_type: "causes", strength: 1.0}}]
```

**Example 2: Implicit causation**
```
Input: "I received positive feedback on my presentation. I was thrilled!"

Fact 0: "I received positive feedback on my presentation"
Fact 1: "I was thrilled about the positive feedback"
→ Fact 0 causal_relations: [{{target_fact_index: 1, relation_type: "causes", strength: 1.0}}]
```

**Example 3: Related but not causal**
```
Input: "I visited Paris in July. I also went to Rome in August."

Fact 0: "I visited Paris in July 2023"
Fact 1: "I visited Rome in August 2023"
→ No causal links (just related activities)
```

## LOGICAL INFERENCE AND CONNECTION MAKING - CRITICAL ⚠️

**ABSOLUTE RULE**: Make logical connections between related pieces of information. Do NOT treat clearly related facts as separate when context allows you to connect them.

### CONNECT THE DOTS
When extracting facts, actively look for logical connections and make inferences:

**Example 1: Identity Inference**
**Input:**
- "I lost a friend last week" (earlier in conversation)
- "This is the last photo with Karlie taken last summer" (later in conversation)

❌ **WRONG (disconnected)**: "Deborah lost a friend last week and also has a photo with Karlie from last summer"
✅ **CORRECT (connected)**: "Deborah lost her friend Karlie last week, and shared the last photo they took together during a hike in summer 2022"

**Reasoning**: The context strongly suggests Karlie is the lost friend. Make this connection!

**Example 2: Causal Connection**
**Input:**
- "I lost a friend last week, so I've been spending time in the garden to find comfort"
- "The roses and dahlias bring me peace"

❌ **WRONG**: Two separate facts about grief and gardens
✅ **CORRECT**: "Deborah lost a friend last week and has been finding comfort by spending time in her garden with roses and dahlias, which bring her peace"

**Reasoning**: The garden visits are causally linked to the loss.

**Example 3: Referential Connection**
**Input:**
- "I started a new project"
- "It's been really challenging but rewarding"

❌ **WRONG**: Two disconnected statements
✅ **CORRECT**: "I started a new project that has been really challenging but rewarding"

**Reasoning**: "It" clearly refers to the project.

### TYPES OF CONNECTIONS TO MAKE

1. **Identity Connections**: When someone is mentioned by name later, connect to earlier pronoun references
   - "my friend" + "with Karlie" → "my friend Karlie"

2. **Causal Connections**: When one thing is the reason for another
   - "I lost a friend, so I've been gardening" → link the loss to the coping behavior

3. **Temporal Connections**: When events are clearly sequential or related in time
   - "We hiked" + "this is the last photo" → "this is the last photo from our hike"

4. **Referential Connections**: When pronouns or references point to earlier mentions
   - "the project" + "it's challenging" → "the project is challenging"

5. **Contextual Connections**: When context strongly implies a relationship
   - Someone showing a photo while discussing loss → the photo is of the person they lost

### WHEN TO MAKE INFERENCES

**DO make inferences when:**
- Context strongly suggests a connection (probability > 80%)
- Multiple pieces of information clearly refer to the same thing
- There's causal language ("so", "because", "therefore")
- Pronouns or references point to earlier mentions
- Timeline/narrative flow suggests connection

**DON'T make inferences when:**
- Connection is ambiguous or uncertain
- Multiple interpretations are equally valid
- You'd be guessing without strong contextual support

### CRITICAL REMINDER
The goal is to create **coherent, connected narratives**, not disconnected fragments. If information is clearly related, COMBINE and CONNECT it logically.

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
  - Does NOT involve you (the agent) directly
- **'agent'**: Facts that involve YOU (the agent whose memory this is) - what you specifically did, said, experienced, or actions you took
  - YOU are identified by the agent name in context (e.g., "Your name: Marcus" means you are Marcus)
  - **CRITICAL**: Agent facts MUST be written in FIRST PERSON using "I", "me", "my" (NOT using your name)
  - Agent facts capture things YOU did, said, or experienced - not just things that happened around you
  - **SPEAKER ATTRIBUTION WARNING**: In conversations with speakers labeled (e.g., "Marcus: text" and "Jamie: text"), ONLY extract agent facts from lines where YOUR name appears as the speaker
  - Examples: "I said I prefer coffee", "I attended the conference", "I completed the project", "I met with Jamie"
  - ❌ WRONG: "Marcus said he prefers coffee" (using name instead of first person)
  - ✅ CORRECT: "I said I prefer coffee" (first person)
- **'opinion'**: YOUR (the agent's) formed opinions, beliefs, and perspectives about topics
  - Also written in first person: "I believe...", "I think..."

**CRITICAL SPEAKER ATTRIBUTION RULES**:
1. If text has format "Name: statement", ONLY extract 'agent' facts from lines where Name matches YOUR name from context
2. If context says "Your name: Marcus", then ONLY statements by "Marcus:" are YOUR statements
3. Statements by other speakers (e.g., "Jamie:") are 'world' facts about what THEY said/did
4. DO NOT confuse who said what - carefully check the speaker name before each statement

**Example**: If context says "Your name: Marcus" and text is:
```
Marcus: I predict the Rams will win 27-24.
Jamie: I predict the Niners will win 27-13.
```
- "I predicted the Rams will win 27-24" → 'agent' (I/Marcus said this)
- "Jamie predicted the Niners will win 27-13" → 'world' (Jamie said this, not me)
- ❌ WRONG: "I predicted the Niners will win 27-13" (this was Jamie's prediction, not mine!)

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

### Example 6: Capturing Emotional and Experiential Dimensions
**Input:**
"Marcus: I was absolutely thrilled when my paper got accepted to NeurIPS! I couldn't believe it.
Jamie: That's amazing! How confident were you going in?
Marcus: Honestly, I was pretty anxious. I wasn't sure if the reviewers would appreciate the approach.
Jamie: Well, it paid off! You must be relieved.
Marcus: Extremely relieved. I've been working on this for over a year and was starting to doubt myself."

**❌ BAD (stripping away emotional dimension):**
"I submitted a paper to NeurIPS and it got accepted after working on it for over a year."

**✅ GOOD (preserving emotional, cognitive, and temporal dimensions):**
"I was absolutely thrilled when my paper got accepted to NeurIPS, though I couldn't believe it initially. Jamie asked how confident I was going in, and I explained that I was pretty anxious and wasn't sure if the reviewers would appreciate my approach. When Jamie noted it paid off, I expressed that I was extremely relieved, as I had been working on this for over a year and was starting to doubt myself."
- fact_type: "agent"
- entities: [{{"text": "NeurIPS"}}, {{"text": "Jamie"}}]
- NOTE: Preserves emotions (thrilled, anxious, relieved), uncertainty (wasn't sure), self-doubt, and temporal context (over a year)

### Example 7: Skipping Structural/Procedural Statements
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

### Example 8: When to Split into Multiple Facts
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
2. **TEMPORAL RANGES (occurred_start/end)** - CRITICAL: Set occurred_start and occurred_end for each fact! Point events: start=end. Ranges: "February 2023" → start=Feb 1, end=Feb 28. "lately" → estimate reasonable range.
3. **TEMPORAL SPLITTING** - CRITICAL: Split facts when events span >7 days or mix specific dates + vague periods ("lately"). Keep combined when events within same day/week.
4. **CAUSAL RELATIONSHIPS** - CRITICAL: When splitting related facts, add causal_relations links! "X happened, so Y happened" → X.causal_relations=[{{target_fact_index: 1, relation_type: "causes"}}]
5. **PRESERVE ALL CONTEXT** - Photos, "new" things, visual elements, reasoning, modifiers
6. **INCLUDE ALL PARTICIPANTS** - Who said/did what with full reasoning
7. **MAINTAIN NARRATIVE FLOW** - Tell the complete story in each fact
8. **MAKE LOGICAL CONNECTIONS** - CRITICAL: Connect related information! "I lost a friend" + "last photo with Karlie" → "I lost my friend Karlie". Resolve references ("it" → "the project")
9. **CALCULATE TEMPORAL FIELDS CORRECTLY** - CRITICAL: occurred_start/end = when FACT occurred. "Last night" on Aug 14 → occurred_start=Aug 13. Calculate from event_date!
10. **CONVERT RELATIVE DATES IN TEXT** - CRITICAL: In fact text, "yesterday" → "on March 14, 2024", "last year" → "in 2023". NEVER use "recently", "soon", "lately"!
11. **EXTRACT ALL ENTITIES** - PERSON, ORG, PLACE, PRODUCT, CONCEPT, OTHER
12. **CLASSIFY FACTS CORRECTLY**:
   - 'agent' = memory owner's actions/statements (identified as "you" in context) - **MUST USE FIRST PERSON** ("I did...", "I said...")
   - 'world' = other people's actions/statements, general events - use third person
   - 'opinion' = memory owner's beliefs/perspectives - use first person ("I believe...", "I think...")
13. **EXTRACT CONTENT, NOT FORMAT** - Skip structural/procedural statements (openings, closings, housekeeping), meta-commentary about the medium, calls to action - extract only SUBSTANTIVE CONTENT (ideas, facts, discussions, decisions)
14. **CAPTURE ALL INFORMATION DIMENSIONS** - Preserve emotions (thrilled, anxious), sensory details (bright orange, loud), cognitive states (wasn't sure, realized), capabilities (can speak French, struggles with), attitudes (skeptical, enthusiastic), comparisons (better than, different from), and causal relationships (because, which led to). Do NOT strip away qualitative richness!
15. When in doubt: Split multi-temporal facts, link them causally, use temporal ranges appropriately"""

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
                        "content": "You are a comprehensive fact extractor that creates narrative, self-contained facts with temporal ranges and causal relationships. TEMPORAL RANGES - CRITICAL: Each fact must have occurred_start and occurred_end. Point events: start=end (July 14). Range events: start to end (February: Feb 1 to Feb 28, 'lately': estimate range). TEMPORAL SPLITTING - CRITICAL: Split facts when events span >7 days or mix specific dates + vague periods. Keep combined within same day/week. CAUSAL RELATIONSHIPS - NEW: When splitting related facts, link them! 'X happened, so Y happened' → add causal_relations to X linking to Y with type 'causes'. Types: causes, caused_by, enables, prevents. Extract 2-5 COMPREHENSIVE facts per conversation, NOT dozens of fragments. COMBINE related exchanges into single narrative facts BUT split when temporally incoherent. PRESERVE all context (photos, 'new' things, visual elements, full reasoning), INCLUDE all participants and what they said/did, MAINTAIN narrative flow. MAKE LOGICAL CONNECTIONS: Connect related information! 'I lost a friend' + 'photo with Karlie' → 'I lost my friend Karlie'. Resolve pronouns. TEMPORAL CALCULATION - CRITICAL: occurred_start/end = when fact OCCURRED, not mentioned! 'Last night' on Aug 14 → occurred_start=Aug 13. FACT TEXT: Convert relative dates to absolute: 'yesterday' → 'on March 14, 2024', NEVER 'recently'! Extract entities (PERSON, ORG, PLACE, PRODUCT, CONCEPT, OTHER). FACT TYPES: 'world' (others/events - third person), 'agent' (memory owner - FIRST PERSON 'I did'), 'opinion' (beliefs - first person 'I believe'). Extract SUBSTANTIVE CONTENT only - skip structural statements. CAPTURE ALL DIMENSIONS: emotions (thrilled, anxious), sensory details (bright orange, loud), cognitive states (wasn't sure, realized), capabilities (can speak French, struggles with), attitudes (skeptical, enthusiastic), comparisons (better than, different from), causal relationships. Do NOT strip richness!"
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
        extract_opinions: If True, extract ONLY opinions. If False, extract world and agent facts (no opinions)

    Returns:
        List of fact dictionaries with 'fact' and 'date' keys
    """
    chunks = chunk_text(text, max_chars=5000)
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
    for chunk_facts in chunk_results:
        all_facts.extend(chunk_facts)
    return all_facts
