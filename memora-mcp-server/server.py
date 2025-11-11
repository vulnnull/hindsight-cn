"""Memora MCP Server implementation using FastMCP."""

import json
import logging
import os

from fastmcp import FastMCP

from config import Config
from client import MemoraClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
config = Config.from_env()
client = MemoraClient(
    api_url=config.api_url,
    agent_id=config.agent_id,
    api_key=config.api_key,
)

# Create FastMCP server
mcp = FastMCP("memora-mcp-server")


@mcp.tool()
async def memora_put(content: str, context: str) -> str:
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
        content: The fact/memory to store (be specific and include relevant details)
        context: Categorize the memory (e.g., 'personal_preferences', 'work_history', 'hobbies', 'family')
    """
    try:
        result = await client.remember(content=content, context=context)
        return f"Fact stored successfully: {result.get('message', 'Success')}"
    except Exception as e:
        logger.error(f"Error storing fact: {e}", exc_info=True)
        return f"Error: {str(e)}"


@mcp.tool()
async def memora_search(query: str, max_tokens: int = 4096) -> str:
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
        query: Natural language search query to find relevant memories
        max_tokens: Maximum tokens for search context (default: 4096)
    """
    try:
        result = await client.search(query=query, max_tokens=max_tokens)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching: {e}", exc_info=True)
        return f"Error: {str(e)}"


def main():
    """Main entry point."""
    port = int(os.getenv("PORT", "8765"))
    host = os.getenv("HOST", "127.0.0.1")

    logger.info(f"Starting Memora MCP Server for agent: {config.agent_id}")
    logger.info(f"MCP server starting on http://{host}:{port}")

    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
