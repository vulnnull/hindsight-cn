"""Memora MCP Server implementation using FastMCP."""

import json
import logging

from fastmcp import FastMCP
from memora import TemporalSemanticMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mcp_server(memory: TemporalSemanticMemory) -> FastMCP:
    """
    Create and configure the Memora MCP server.

    Args:
        memory: TemporalSemanticMemory instance (required)

    Returns:
        Configured FastMCP server instance
    """
    # Create FastMCP server
    mcp = FastMCP("memora-mcp-server")

    @mcp.tool()
    async def memora_put(agent_id: str, content: str, context: str, explanation: str = "") -> str:
        """
        **CRITICAL: Store important user information to long-term memory.**

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
            agent_id: The unique identifier for the agent/user storing the memory
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
                agent_id=agent_id,
                contents=[{"content": content, "context": context}]
            )
            return f"Fact stored successfully"
        except Exception as e:
            logger.error(f"Error storing fact: {e}", exc_info=True)
            return f"Error: {str(e)}"

    @mcp.tool()
    async def memora_search(agent_id: str, query: str, max_tokens: int = 4096, explanation: str = "") -> str:
        """
        **CRITICAL: Search user's memory to provide personalized, context-aware responses.**

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
            agent_id: The unique identifier for the agent/user whose memories to search
            query: Natural language search query to find relevant memories
            max_tokens: Maximum tokens for search context (default: 4096)
            explanation: Optional explanation for why this search is being performed
        """
        try:
            # Log all parameters for debugging
            logger.info(f"memora_search called with: query={query!r}, max_tokens={max_tokens}, explanation={explanation!r}")

            # Log explanation if provided
            if explanation:
                logger.debug(f"Explanation: {explanation}")

            # Search using search_async
            search_result = await memory.search_async(
                agent_id=agent_id,
                query=query,
                fact_type=["world", "agent", "opinion"],  # Search all fact types
                max_tokens=max_tokens,
                thinking_budget=100
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
