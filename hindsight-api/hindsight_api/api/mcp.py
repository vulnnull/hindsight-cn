"""Hindsight MCP Server implementation using FastMCP."""

import json
import logging

from fastmcp import FastMCP
from hindsight_api import MemoryEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mcp_server(memory: MemoryEngine) -> FastMCP:
    """
    Create and configure the Hindsight MCP server.

    Args:
        memory: MemoryEngine instance (required)

    Returns:
        Configured FastMCP server instance
    """
    # Create FastMCP server
    mcp = FastMCP("hindsight-mcp-server")

    @mcp.tool()
    async def hindsight_put(bank_id: str, content: str, context: str, explanation: str = "") -> str:
        """
        **CRITICAL: Store important user information to long-term memory.**

        **⚠️ PER-USER TOOL - REQUIRES USER IDENTIFICATION:**
        - This tool is STRICTLY per-user. Each user MUST have a unique `bank_id`.
        - ONLY use this tool if you have a valid user identifier (user ID, email, session ID, etc.) to map to `bank_id`.
        - DO NOT use this tool if you cannot identify the specific user.
        - DO NOT share memories between different users - each user's memories are isolated by their `bank_id`.
        - If you don't have a user identifier, DO NOT use this tool at all.

        Use this tool PROACTIVELY whenever the user shares:
        - Personal facts, preferences, or interests (e.g., "I love hiking", "I'm a vegetarian")
        - Important events or milestones (e.g., "I got promoted", "My birthday is June 15")
        - User history, experiences, or background (e.g., "I used to work at Google", "I studied CS at MIT")
        - Decisions, opinions, or stated preferences (e.g., "I prefer Python over JavaScript")
        - Goals, plans, or future intentions (e.g., "I'm planning to visit Japan next year")
        - Relationships or people mentioned (e.g., "My manager Sarah", "My wife Alice")
        - Work context, projects, or responsibilities
        - Any other information the user would want remembered for future conversations

        **When to use**: Immediately after user shares personal information. Don't ask permission - just store it naturally.

        **Context guidelines**: Use descriptive contexts like "personal_preferences", "work_history", "family", "hobbies",
        "career_goals", "project_details", etc. This helps organize and retrieve related memories later.

        Args:
            bank_id: **REQUIRED** - The unique, persistent identifier for this specific user (e.g., user_id, email, session_id).
                     This MUST be consistent across all interactions with the same user.
                     Example: "user_12345", "alice@example.com", "session_abc123"
            content: The fact/memory to store (be specific and include relevant details)
            context: Categorize the memory (e.g., 'personal_preferences', 'work_history', 'hobbies', 'family')
            explanation: Optional explanation for why this memory is being stored
        """
        try:
            # Log explanation if provided
            if explanation:
                logger.debug(f"Explanation: {explanation}")

            # Store memory using put_batch_async
            await memory.put_batch_async(
                bank_id=bank_id,
                contents=[{"content": content, "context": context}]
            )
            return f"Fact stored successfully"
        except Exception as e:
            logger.error(f"Error storing fact: {e}", exc_info=True)
            return f"Error: {str(e)}"

    @mcp.tool()
    async def hindsight_search(bank_id: str, query: str, max_tokens: int = 4096, explanation: str = "") -> str:
        """
        **CRITICAL: Search user's memory to provide personalized, context-aware responses.**

        **⚠️ PER-USER TOOL - REQUIRES USER IDENTIFICATION:**
        - This tool is STRICTLY per-user. Each user MUST have a unique `bank_id`.
        - ONLY use this tool if you have a valid user identifier (user ID, email, session ID, etc.) to map to `bank_id`.
        - DO NOT use this tool if you cannot identify the specific user.
        - DO NOT search across multiple users - each user's memories are isolated by their `bank_id`.
        - If you don't have a user identifier, DO NOT use this tool at all.

        Use this tool PROACTIVELY at the start of conversations or when making recommendations to:
        - Check user's preferences before making suggestions (e.g., "what foods does the user like?")
        - Recall user's history to provide continuity (e.g., "what projects has the user worked on?")
        - Remember user's goals and context (e.g., "what is the user trying to accomplish?")
        - Avoid repeating information or asking questions you should already know
        - Personalize responses based on user's background, interests, and past interactions
        - Reference past conversations or events the user mentioned

        **When to use**:
        - Start of conversation: Search for relevant context about the user
        - Before recommendations: Check user preferences and past experiences
        - When user asks about something they may have mentioned before
        - To provide continuity across conversations

        **Search tips**: Use natural language queries like "user's programming language preferences",
        "user's work experience", "user's dietary restrictions", "what does the user know about X?"

        Args:
            bank_id: **REQUIRED** - The unique, persistent identifier for this specific user (e.g., user_id, email, session_id).
                     This MUST be consistent across all interactions with the same user.
                     Example: "user_12345", "alice@example.com", "session_abc123"
            query: Natural language search query to find relevant memories
            max_tokens: Maximum tokens for search context (default: 4096)
            explanation: Optional explanation for why this search is being performed
        """
        try:
            # Log all parameters for debugging
            logger.info(f"hindsight_search called with: query={query!r}, max_tokens={max_tokens}, explanation={explanation!r}")

            # Log explanation if provided
            if explanation:
                logger.debug(f"Explanation: {explanation}")

            # Search using recall_async
            from hindsight_api.engine.memory_engine import Budget
            search_result = await memory.recall_async(
                bank_id=bank_id,
                query=query,
                fact_type=["world", "bank", "opinion"],  # Search all fact types
                max_tokens=max_tokens,
                budget=Budget.LOW
            )

            # Convert results to dict format
            results = [
                {
                    "id": fact.id,
                    "text": fact.text,
                    "type": fact.fact_type,
                    "context": fact.context,
                    "event_date": fact.event_date,  # Already a string from the database
                    "document_id": fact.document_id
                }
                for fact in search_result.results
            ]

            return json.dumps({"results": results}, indent=2)
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return json.dumps({"error": str(e), "results": []})

    return mcp
