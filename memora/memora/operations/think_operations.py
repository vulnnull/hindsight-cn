"""
Think operations for formulating answers based on agent and world facts.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ThinkOperationsMixin:
    """Mixin class for think operations."""

    async def think_async(
        self,
        agent_id: str,
        query: str,
        thinking_budget: int = 50,
    ) -> Dict[str, Any]:
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

        Returns:
            Dict with:
                - text: Plain text answer (no markdown)
                - based_on: Dict with 'world', 'agent', and 'opinion' fact lists
                - new_opinions: List of newly formed opinions
        """
        # Use cached LLM config
        if self._llm_config is None:
            raise ValueError("Memory LLM API key not set. Set MEMORY_LLM_API_KEY environment variable.")

        # Steps 1-3: Run multi-fact-type search (12-way retrieval: 4 methods × 3 fact types)
        # This is more efficient than 3 separate searches as it merges and reranks all results together
        all_results, _ = await self.search_async(
            agent_id=agent_id,
            query=query,
            thinking_budget=thinking_budget,
            max_tokens=4096,
            enable_trace=False,
            fact_type=['agent', 'world', 'opinion']
        )

        # Split results by fact type for structured response
        agent_results = [r for r in all_results if r.get('fact_type') == 'agent']
        world_results = [r for r in all_results if r.get('fact_type') == 'world']
        opinion_results = [r for r in all_results if r.get('fact_type') == 'opinion']

        # Step 4: Format facts for LLM with full details as JSON
        import json

        def format_facts(facts):
            if not facts:
                return "[]"
            formatted = []
            for fact in facts:
                fact_obj = {
                    "text": fact['text']
                }

                # Add context if available
                if fact.get('context'):
                    fact_obj["context"] = fact['context']

                # Add event_date if available
                if fact.get('event_date'):
                    from datetime import datetime
                    event_date = fact['event_date']
                    if isinstance(event_date, str):
                        fact_obj["event_date"] = event_date
                    elif isinstance(event_date, datetime):
                        fact_obj["event_date"] = event_date.strftime('%Y-%m-%d %H:%M:%S')

                # Add score if available
                if fact.get('score') is not None:
                    fact_obj["score"] = fact['score']

                formatted.append(fact_obj)

            return json.dumps(formatted, indent=2)

        agent_facts_text = format_facts(agent_results)
        world_facts_text = format_facts(world_results)
        opinion_facts_text = format_facts(opinion_results)

        # Step 5: Call Groq to formulate answer
        prompt = f"""You are an AI assistant answering a question based on retrieved facts provided in JSON format.

AGENT IDENTITY (what the agent has done):
{agent_facts_text}

WORLD FACTS (general knowledge):
{world_facts_text}

YOUR EXISTING OPINIONS (perspectives you've formed):
{opinion_facts_text}

QUESTION: {query}

The facts above are provided as JSON arrays. Each fact may include:
- text: The fact content
- context: Additional context information
- event_date: When the fact occurred
- score: Relevance score

Provide a helpful, accurate answer based on the facts above. Be consistent with your existing opinions. If the facts don't contain enough information to answer the question, say so clearly. Do not use markdown formatting - respond in plain text only.

If you form any new opinions while thinking about this question, state them clearly in your answer."""

        answer_text = await self._llm_config.call(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Always respond in plain text without markdown formatting. You can form and express opinions based on facts."},
                {"role": "user", "content": prompt}
            ],
            scope="memory_think",
            temperature=0.7,
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
        return {
            "text": answer_text,
            "based_on": {
                "world": world_results,
                "agent": agent_results,
                "opinion": opinion_results
            },
            "new_opinions": []  # Opinions are being extracted asynchronously
        }

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
            opinion: str = Field(description="The opinion or perspective formed")
            reasons: str = Field(description="The reasons supporting this opinion")
            confidence: float = Field(description="Confidence score for this opinion (0.0 to 1.0, where 1.0 is very confident)")

        class OpinionExtractionResponse(BaseModel):
            """Response containing extracted opinions."""
            opinions: List[Opinion] = Field(
                default_factory=list,
                description="List of opinions formed with their supporting reasons and confidence scores"
            )

        extraction_prompt = f"""Extract any NEW opinions or perspectives that were formed while answering the following question.

ORIGINAL QUESTION:
{query}

ANSWER PROVIDED:
{text}

An opinion is a judgment, viewpoint, or conclusion that goes beyond just stating facts. It represents a formed perspective or belief.

IMPORTANT: Do NOT extract statements like:
- "I don't have enough information"
- "The facts don't contain information about X"
- "I cannot answer because..."
- Simple acknowledgments or meta-statements about the query itself

ONLY extract actual opinions, judgments, or perspectives about substantive topics.

For each opinion found, provide:
1. The opinion itself (what the agent believes or concludes)
2. The reasons or facts that support it
3. A confidence score (0.0 to 1.0) indicating how confident the agent is in this opinion

If no genuine opinions are expressed (e.g., the response just says "I don't know"), return an empty list."""

        try:
            result = await self._llm_config.call(
                messages=[
                    {"role": "system", "content": "You extract opinions and perspectives from text."},
                    {"role": "user", "content": extraction_prompt}
                ],
                response_format=OpinionExtractionResponse,
                scope="memory_extract_opinion"
            )

            # Format opinions with reasons included in the text and confidence score
            formatted_opinions = []
            for op in result.opinions:
                # Combine opinion and reasons into a single statement
                opinion_with_reasons = f"{op.opinion} (Reasons: {op.reasons})"
                formatted_opinions.append({
                    "text": opinion_with_reasons,
                    "confidence": op.confidence
                })

            return formatted_opinions

        except Exception as e:
            logger.warning(f"Failed to extract opinions: {str(e)}")
            return []
