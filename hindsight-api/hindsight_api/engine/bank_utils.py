"""
bank profile utilities for personality and background management.
"""

import json
import logging
import re
from typing import Dict, Optional
from pydantic import BaseModel, Field
from .db_utils import acquire_with_retry

logger = logging.getLogger(__name__)

DEFAULT_PERSONALITY = {
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
    "bias_strength": 0.5,
}


class PersonalityTraits(BaseModel):
    """Big Five personality traits with bias strength (all values 0.0-1.0)."""
    openness: float = Field(description="Creativity, curiosity, openness to new ideas (0.0-1.0)")
    conscientiousness: float = Field(description="Organization, discipline, goal-directed (0.0-1.0)")
    extraversion: float = Field(description="Sociability, assertiveness, energy from others (0.0-1.0)")
    agreeableness: float = Field(description="Cooperation, empathy, consideration (0.0-1.0)")
    neuroticism: float = Field(description="Emotional sensitivity, anxiety, stress response (0.0-1.0)")
    bias_strength: float = Field(description="How much personality influences opinions (0.0-1.0)")


class BackgroundMergeResponse(BaseModel):
    """LLM response for background merge with personality inference."""
    background: str = Field(description="Merged background in first person perspective")
    personality: PersonalityTraits = Field(description="Inferred Big Five personality traits")


async def get_bank_profile(pool, bank_id: str) -> Dict:
    """
    Get bank profile (name, personality + background).
    Auto-creates bank with default values if not exists.

    Args:
        pool: Database connection pool
        bank_id: bank IDentifier

    Returns:
        Dict with 'name' (str), 'personality' (dict) and 'background' (str) keys
    """
    async with acquire_with_retry(pool) as conn:
        # Try to get existing bank
        row = await conn.fetchrow(
            """
            SELECT name, personality, background
            FROM banks WHERE bank_id = $1
            """,
            bank_id
        )

        if row:
            # asyncpg returns JSONB as a string, so parse it
            personality_data = row["personality"]
            if isinstance(personality_data, str):
                personality_data = json.loads(personality_data)

            return {
                "name": row["name"],
                "personality": personality_data,
                "background": row["background"]
            }

        # Bank doesn't exist, create with defaults
        await conn.execute(
            """
            INSERT INTO banks (bank_id, name, personality, background)
            VALUES ($1, $2, $3::jsonb, $4)
            ON CONFLICT (bank_id) DO NOTHING
            """,
            bank_id,
            bank_id,  # Default name is the bank_id
            json.dumps(DEFAULT_PERSONALITY),
            ""
        )

        return {
            "name": bank_id,
            "personality": DEFAULT_PERSONALITY.copy(),
            "background": ""
        }


async def update_bank_personality(
    pool,
    bank_id: str,
    personality: Dict[str, float]
) -> None:
    """
    Update bank personality traits.

    Args:
        pool: Database connection pool
        bank_id: bank IDentifier
        personality: Dict with Big Five traits + bias_strength (all 0-1)
    """
    # Ensure bank exists first
    await get_bank_profile(pool, bank_id)

    async with acquire_with_retry(pool) as conn:
        await conn.execute(
            """
            UPDATE banks
            SET personality = $2::jsonb,
                updated_at = NOW()
            WHERE bank_id = $1
            """,
            bank_id,
            json.dumps(personality)
        )


async def merge_bank_background(
    pool,
    llm_config,
    bank_id: str,
    new_info: str,
    update_personality: bool = True
) -> dict:
    """
    Merge new background information with existing background using LLM.
    Normalizes to first person ("I") and resolves conflicts.
    Optionally infers personality traits from the merged background.

    Args:
        pool: Database connection pool
        llm_config: LLM configuration for background merging
        bank_id: bank IDentifier
        new_info: New background information to add/merge
        update_personality: If True, infer Big Five traits from background (default: True)

    Returns:
        Dict with 'background' (str) and optionally 'personality' (dict) keys
    """
    # Get current profile
    profile = await get_bank_profile(pool, bank_id)
    current_background = profile["background"]

    # Use LLM to merge backgrounds and optionally infer personality
    result = await _llm_merge_background(
        llm_config,
        current_background,
        new_info,
        infer_personality=update_personality
    )

    merged_background = result["background"]
    inferred_personality = result.get("personality")

    # Update in database
    async with acquire_with_retry(pool) as conn:
        if inferred_personality:
            # Update both background and personality
            await conn.execute(
                """
                UPDATE banks
                SET background = $2,
                    personality = $3::jsonb,
                    updated_at = NOW()
                WHERE bank_id = $1
                """,
                bank_id,
                merged_background,
                json.dumps(inferred_personality)
            )
        else:
            # Update only background
            await conn.execute(
                """
                UPDATE banks
                SET background = $2,
                    updated_at = NOW()
                WHERE bank_id = $1
                """,
                bank_id,
                merged_background
            )

    response = {"background": merged_background}
    if inferred_personality:
        response["personality"] = inferred_personality

    return response


async def _llm_merge_background(
    llm_config,
    current: str,
    new_info: str,
    infer_personality: bool = False
) -> dict:
    """
    Use LLM to intelligently merge background information.
    Optionally infer Big Five personality traits from the merged background.

    Args:
        llm_config: LLM configuration to use
        current: Current background text
        new_info: New information to merge
        infer_personality: If True, also infer personality traits

    Returns:
        Dict with 'background' (str) and optionally 'personality' (dict) keys
    """
    if infer_personality:
        prompt = f"""You are helping maintain a memory bank's background/profile and infer their personality. You MUST respond with ONLY valid JSON.

Current background: {current if current else "(empty)"}

New information to add: {new_info}

Instructions:
1. Merge the new information with the current background
2. If there are conflicts (e.g., different birthplaces), the NEW information overwrites the old
3. Keep additions that don't conflict
4. Output in FIRST PERSON ("I") perspective
5. Be concise - keep merged background under 500 characters
6. Infer Big Five personality traits from the merged background:
   - Openness: 0.0-1.0 (creativity, curiosity, openness to new ideas)
   - Conscientiousness: 0.0-1.0 (organization, discipline, goal-directed)
   - Extraversion: 0.0-1.0 (sociability, assertiveness, energy from others)
   - Agreeableness: 0.0-1.0 (cooperation, empathy, consideration)
   - Neuroticism: 0.0-1.0 (emotional sensitivity, anxiety, stress response)
   - Bias Strength: 0.0-1.0 (how much personality influences opinions)

CRITICAL: You MUST respond with ONLY a valid JSON object. No markdown, no code blocks, no explanations. Just the JSON.

Format:
{{
  "background": "the merged background text in first person",
  "personality": {{
    "openness": 0.7,
    "conscientiousness": 0.6,
    "extraversion": 0.5,
    "agreeableness": 0.8,
    "neuroticism": 0.4,
    "bias_strength": 0.6
  }}
}}

Trait inference examples:
- "creative artist" → openness: 0.8+, bias_strength: 0.6
- "organized engineer" → conscientiousness: 0.8+, openness: 0.5-0.6
- "startup founder" → openness: 0.8+, extraversion: 0.7+, neuroticism: 0.3-0.4
- "risk-averse analyst" → openness: 0.3-0.4, conscientiousness: 0.8+, neuroticism: 0.6+
- "rational and diligent" → conscientiousness: 0.7+, openness: 0.6+
- "passionate and dramatic" → extraversion: 0.7+, neuroticism: 0.6+, openness: 0.7+"""
    else:
        prompt = f"""You are helping maintain a memory bank's background/profile.

Current background: {current if current else "(empty)"}

New information to add: {new_info}

Instructions:
1. Merge the new information with the current background
2. If there are conflicts (e.g., different birthplaces), the NEW information overwrites the old
3. Keep additions that don't conflict
4. Output in FIRST PERSON ("I") perspective
5. Be concise - keep it under 500 characters
6. Return ONLY the merged background text, no explanations

Merged background:"""

    try:
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]

        if infer_personality:
            # Use structured output with Pydantic model for personality inference
            try:
                parsed = await llm_config.call(
                    messages=messages,
                    response_format=BackgroundMergeResponse,
                    scope="bank_background",
                    temperature=0.3,
                    max_tokens=8192
                )
                logger.info(f"Successfully got structured response: background={parsed.background[:100]}")

                # Convert Pydantic model to dict format
                return {
                    "background": parsed.background,
                    "personality": parsed.personality.model_dump()
                }
            except Exception as e:
                logger.warning(f"Structured output failed, falling back to manual parsing: {e}")
                # Fall through to manual parsing below

        # Manual parsing fallback or non-personality merge
        content = await llm_config.call(
            messages=messages,
            scope="bank_background",
            temperature=0.3,
            max_tokens=8192
        )

        logger.info(f"LLM response for background merge (first 500 chars): {content[:500]}")

        if infer_personality:
            # Parse JSON response - try multiple extraction methods
            result = None

            # Method 1: Direct parse
            try:
                result = json.loads(content)
                logger.info("Successfully parsed JSON directly")
            except json.JSONDecodeError:
                pass

            # Method 2: Extract from markdown code blocks
            if result is None:
                # Remove markdown code blocks
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if code_block_match:
                    try:
                        result = json.loads(code_block_match.group(1))
                        logger.info("Successfully extracted JSON from markdown code block")
                    except json.JSONDecodeError:
                        pass

            # Method 3: Find nested JSON structure
            if result is None:
                # Look for JSON object with nested structure
                json_match = re.search(r'\{[^{}]*"background"[^{}]*"personality"[^{}]*\{[^{}]*\}[^{}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        logger.info("Successfully extracted JSON using nested pattern")
                    except json.JSONDecodeError:
                        pass

            # All parsing methods failed - use fallback
            if result is None:
                logger.warning(f"Failed to extract JSON from LLM response. Raw content: {content[:200]}")
                # Fallback: use new_info as background with default personality
                return {
                    "background": new_info if new_info else current if current else "",
                    "personality": DEFAULT_PERSONALITY.copy()
                }

            # Validate personality values
            personality = result.get("personality", {})
            for key in ["openness", "conscientiousness", "extraversion",
                       "agreeableness", "neuroticism", "bias_strength"]:
                if key not in personality:
                    personality[key] = 0.5  # Default to neutral
                else:
                    # Clamp to [0, 1]
                    personality[key] = max(0.0, min(1.0, float(personality[key])))

            result["personality"] = personality

            # Ensure background exists
            if "background" not in result or not result["background"]:
                result["background"] = new_info if new_info else ""

            return result
        else:
            # Just background merge
            merged = content
            if not merged or merged.lower() in ["(empty)", "none", "n/a"]:
                merged = new_info if new_info else ""
            return {"background": merged}

    except Exception as e:
        logger.error(f"Error merging background with LLM: {e}")
        # Fallback: just append new info
        if current:
            merged = f"{current} {new_info}".strip()
        else:
            merged = new_info

        result = {"background": merged}
        if infer_personality:
            result["personality"] = DEFAULT_PERSONALITY.copy()
        return result


async def list_banks(pool) -> list:
    """
    List all banks in the system.

    Args:
        pool: Database connection pool

    Returns:
        List of dicts with bank_id, name, personality, background, created_at, updated_at
    """
    async with acquire_with_retry(pool) as conn:
        rows = await conn.fetch(
            """
            SELECT bank_id, name, personality, background, created_at, updated_at
            FROM banks
            ORDER BY updated_at DESC
            """
        )

        result = []
        for row in rows:
            # asyncpg returns JSONB as a string, so parse it
            personality_data = row["personality"]
            if isinstance(personality_data, str):
                personality_data = json.loads(personality_data)

            result.append({
                "bank_id": row["bank_id"],
                "name": row["name"],
                "personality": personality_data,
                "background": row["background"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            })

        return result
