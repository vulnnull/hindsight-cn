"""
Think operations for formulating answers based on agent and world facts.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from ..response_models import ThinkResult, MemoryFact

logger = logging.getLogger(__name__)


class ThinkOperationsMixin:
    """Mixin class for think operations."""

    async def think_async(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 50,
        context: str = None,
    ) -> ThinkResult:
        """
        Think and formulate an answer using agent identity, world facts, and opinions.

        This method:
        1. Retrieves agent facts (agent's identity and past actions)
        2. Retrieves world facts (general knowledge)
        3. Retrieves existing opinions (agent's formed perspectives)
        4. Uses LLM to formulate an answer
        5. Extracts and stores any new opinions formed during thinking
        6. Returns plain text answer and the facts used

        Args:
            agent_id: Agent identifier
            query: Question to answer
            thinking_budget: Number of memory units to explore
            context: Additional context string to include in LLM prompt (not used in search)

        Returns:
            ThinkResult containing:
                - text: Plain text answer (no markdown)
                - based_on: Dict with 'world', 'agent', and 'opinion' fact lists (MemoryFact objects)
                - new_opinions: List of newly formed opinions
        """
        # Use cached LLM config
        if self._llm_config is None:
            raise ValueError("Memory LLM API key not set. Set MEMORA_API_LLM_API_KEY environment variable.")

        # Steps 1-3: Run multi-fact-type search (12-way retrieval: 4 methods × 3 fact types)
        # This is more efficient than 3 separate searches as it merges and reranks all results together
        search_result = await self.search_async(
            agent_id=agent_id,
            query=query,
            thinking_budget=thinking_budget,
            max_tokens=4096,
            enable_trace=False,
            fact_type=['agent', 'world', 'opinion']
        )

        all_results = search_result.results
        logger.info(f"[THINK] Search returned {len(all_results)} results")

        # Split results by fact type for structured response
        agent_results = [r for r in all_results if r.fact_type == 'agent']
        world_results = [r for r in all_results if r.fact_type == 'world']
        opinion_results = [r for r in all_results if r.fact_type == 'opinion']

        logger.info(f"[THINK] Split results - agent: {len(agent_results)}, world: {len(world_results)}, opinion: {len(opinion_results)}")

        # Step 4: Format facts for LLM with full details as JSON
        import json

        def format_facts(facts):
            if not facts:
                return "[]"
            formatted = []
            for fact in facts:
                fact_obj = {
                    "text": fact.text
                }

                # Add context if available
                if fact.context:
                    fact_obj["context"] = fact.context

                # Add event_date if available
                if fact.event_date:
                    from datetime import datetime
                    event_date = fact.event_date
                    if isinstance(event_date, str):
                        fact_obj["event_date"] = event_date
                    elif isinstance(event_date, datetime):
                        fact_obj["event_date"] = event_date.strftime('%Y-%m-%d %H:%M:%S')

                # Add activation if available
                if fact.activation is not None:
                    fact_obj["score"] = fact.activation

                formatted.append(fact_obj)

            return json.dumps(formatted, indent=2)

        agent_facts_text = format_facts(agent_results)
        world_facts_text = format_facts(world_results)
        opinion_facts_text = format_facts(opinion_results)

        logger.info(f"[THINK] Formatted facts - agent: {len(agent_facts_text)} chars, world: {len(world_facts_text)} chars, opinion: {len(opinion_facts_text)} chars")

        # Step 4.5: Get agent profile (name, personality + background)
        profile = await self.get_agent_profile(agent_id)
        name = profile["name"]
        personality = profile["personality"]
        background = profile["background"]

        # Build personality description for prompt
        def describe_trait(name: str, value: float) -> str:
            """Convert trait value to descriptive text."""
            if value >= 0.8:
                return f"very high {name}"
            elif value >= 0.6:
                return f"high {name}"
            elif value >= 0.4:
                return f"moderate {name}"
            elif value >= 0.2:
                return f"low {name}"
            else:
                return f"very low {name}"

        personality_desc = f"""Your personality traits:
- {describe_trait('openness to new ideas', personality['openness'])}
- {describe_trait('conscientiousness and organization', personality['conscientiousness'])}
- {describe_trait('extraversion and sociability', personality['extraversion'])}
- {describe_trait('agreeableness and cooperation', personality['agreeableness'])}
- {describe_trait('emotional sensitivity', personality['neuroticism'])}

Personality influence strength: {int(personality['bias_strength'] * 100)}% (how much your personality shapes your opinions)"""

        name_section = f"""

Your name: {name}
"""

        background_section = ""
        if background:
            background_section = f"""

Your background:
{background}
"""

        # Step 5: Call LLM to formulate answer
        # Build the prompt with context if provided
        context_section = ""
        if context:
            context_section = f"""
ADDITIONAL CONTEXT:
{context}

"""

        prompt = f"""Here's what I know and have experienced:

MY IDENTITY & EXPERIENCES:
{agent_facts_text}

WHAT I KNOW ABOUT THE WORLD:
{world_facts_text}

MY EXISTING OPINIONS & BELIEFS:
{opinion_facts_text}

{context_section}{name_section}{personality_desc}{background_section}

QUESTION: {query}

Based on everything I know, believe, and who I am (including my name, personality and background), here's what I genuinely think about this question. I'll draw on my experiences, knowledge, opinions, and personal traits to give you my honest perspective."""

        logger.info(f"[THINK] Full prompt length: {len(prompt)} chars")
        logger.debug(f"[THINK] Prompt preview (first 500 chars): {prompt[:500]}")

        # Adjust system message based on bias_strength
        bias_strength = personality['bias_strength']
        if bias_strength >= 0.7:
            personality_instruction = "Your personality strongly influences your thinking. Let your traits guide how you interpret facts and form opinions. Don't be afraid to be biased based on your personality."
        elif bias_strength >= 0.4:
            personality_instruction = "Your personality moderately influences your thinking. Balance your personal traits with objective analysis."
        else:
            personality_instruction = "Your personality has minimal influence on your thinking. Focus primarily on facts while keeping your traits in mind."

        system_message = f"You are a person with your own thoughts, experiences, opinions, and personality. When asked a question, respond naturally like a human would - share what you genuinely think based on what you know and have experienced. {personality_instruction} Be direct, express your views confidently, and use 'I think', 'I believe', 'in my view', etc. Respond in plain text without markdown formatting."

        answer_text = await self._llm_config.call(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            scope="memory_think",
            temperature=0.9,
            max_tokens=1000
        )

        answer_text = answer_text.strip()

        # Step 6: Extract and store new opinions asynchronously (fire and forget)
        logger.debug(f"[THINK] Submitting form_opinion task for agent {agent_id}")
        await self._task_backend.submit_task({
            'type': 'form_opinion',
            'agent_id': agent_id,
            'answer_text': answer_text,
            'query': query
        })
        logger.debug(f"[THINK] form_opinion task submitted")

        # Step 7: Return response with facts split by type (don't wait for opinions)
        return ThinkResult(
            text=answer_text,
            based_on={
                "world": world_results,
                "agent": agent_results,
                "opinion": opinion_results
            },
            new_opinions=[]  # Opinions are being extracted asynchronously
        )

    async def _extract_and_store_opinions_async(
        self,
        agent_id: str,
        answer_text: str,
        query: str
    ):
        """
        Background task to extract and store opinions from think response.

        This runs asynchronously and does not block the think response.

        Args:
            agent_id: Agent identifier
            answer_text: The generated answer text
            query: The original query
        """
        try:
            logger.debug(f"[THINK] Extracting opinions from answer for agent {agent_id}")
            # Extract opinions from the answer
            new_opinions = await self._extract_opinions_from_text(text=answer_text, query=query)
            logger.debug(f"[THINK] Extracted {len(new_opinions)} opinions")

            # Store new opinions
            if new_opinions:
                current_time = datetime.now(timezone.utc)
                for opinion_dict in new_opinions:
                    await self.put_async(
                        agent_id=agent_id,
                        content=opinion_dict["text"],
                        context=f"formed during thinking about: {query}",
                        event_date=current_time,
                        fact_type_override='opinion',
                        confidence_score=opinion_dict["confidence"]
                    )

                logger.debug(f"[THINK] Extracted and stored {len(new_opinions)} new opinions")
        except Exception as e:
            logger.warning(f"[THINK] Failed to extract/store opinions: {str(e)}")

    async def _extract_opinions_from_text(
        self,
        text: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Extract opinions with reasons and confidence from text using LLM.

        Args:
            text: Text to extract opinions from
            query: The original query that prompted this response

        Returns:
            List of dicts with keys: 'text' (opinion with reasons), 'confidence' (score 0-1)
        """
        class Opinion(BaseModel):
            """An opinion formed by the agent."""
            opinion: str = Field(description="The opinion or perspective with reasoning included")
            confidence: float = Field(description="Confidence score for this opinion (0.0 to 1.0, where 1.0 is very confident)")

        class OpinionExtractionResponse(BaseModel):
            """Response containing extracted opinions."""
            opinions: List[Opinion] = Field(
                default_factory=list,
                description="List of opinions formed with their supporting reasons and confidence scores"
            )

        extraction_prompt = f"""Extract any NEW opinions or perspectives from the answer below and rewrite them in FIRST-PERSON as if YOU are stating the opinion directly.

ORIGINAL QUESTION:
{query}

ANSWER PROVIDED:
{text}

Your task: Find opinions in the answer and rewrite them AS IF YOU ARE THE ONE SAYING THEM.

An opinion is a judgment, viewpoint, or conclusion that goes beyond just stating facts.

IMPORTANT: Do NOT extract statements like:
- "I don't have enough information"
- "The facts don't contain information about X"
- "I cannot answer because..."

ONLY extract actual opinions about substantive topics.

CRITICAL FORMAT REQUIREMENTS:
1. **ALWAYS start with first-person phrases**: "I think...", "I believe...", "In my view...", "I've come to believe...", "Previously I thought... but now..."
2. **NEVER use third-person**: Do NOT say "The speaker thinks..." or "They believe..." - always use "I"
3. Include the reasoning naturally within the statement
4. Provide a confidence score (0.0 to 1.0)

CORRECT Examples (✓ FIRST-PERSON):
- "I think Alice is more reliable because she consistently delivers on time and writes clean code"
- "Previously I thought all engineers were equal, but now I feel that experience and track record really matter"
- "I believe reliability is best measured by consistent output over time"
- "I've come to believe that track records are more important than potential"

WRONG Examples (✗ THIRD-PERSON - DO NOT USE):
- "The speaker thinks Alice is more reliable"
- "They believe reliability matters"
- "It is believed that Alice is better"

If no genuine opinions are expressed (e.g., the response just says "I don't know"), return an empty list."""

        try:
            result = await self._llm_config.call(
                messages=[
                    {"role": "system", "content": "You are converting opinions from text into first-person statements. Always use 'I think', 'I believe', 'I feel', etc. NEVER use third-person like 'The speaker' or 'They'."},
                    {"role": "user", "content": extraction_prompt}
                ],
                response_format=OpinionExtractionResponse,
                scope="memory_extract_opinion"
            )

            # Format opinions with confidence score and convert to first-person
            formatted_opinions = []
            for op in result.opinions:
                # Convert third-person to first-person if needed
                opinion_text = op.opinion

                # Replace common third-person patterns with first-person
                import re

                # Remove "s" from verbs: believes -> believe, thinks -> think, etc.
                def singularize_verb(verb):
                    if verb.endswith('es'):
                        return verb[:-1]  # believes -> believe
                    elif verb.endswith('s'):
                        return verb[:-1]  # thinks -> think
                    return verb

                # Pattern: "The speaker/user [verb]..." -> "I [verb]..."
                match = re.match(r'^(The speaker|The user|They|It is believed) (believes?|thinks?|feels?|says|asserts?|considers?)(\s+that)?(.*)$', opinion_text, re.IGNORECASE)
                if match:
                    verb = singularize_verb(match.group(2))
                    that_part = match.group(3) or ""  # Keep " that" if present
                    rest = match.group(4)
                    opinion_text = f"I {verb}{that_part}{rest}"

                # If still doesn't start with first-person, prepend "I believe that "
                first_person_starters = ["I think", "I believe", "I feel", "In my view", "I've come to believe", "Previously I"]
                if not any(opinion_text.startswith(starter) for starter in first_person_starters):
                    opinion_text = "I believe that " + opinion_text[0].lower() + opinion_text[1:]

                formatted_opinions.append({
                    "text": opinion_text,
                    "confidence": op.confidence
                })

            return formatted_opinions

        except Exception as e:
            logger.warning(f"Failed to extract opinions: {str(e)}")
            return []
