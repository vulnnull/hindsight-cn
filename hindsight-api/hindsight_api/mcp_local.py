"""
Local MCP server for use with Claude Code (stdio transport).

This runs a fully local Hindsight instance with embedded PostgreSQL (pg0).
No external database or server required.

Run with:
    hindsight-local-mcp

Or with uvx:
    uvx hindsight-api@latest hindsight-local-mcp

Configure in Claude Code's MCP settings:
    {
        "mcpServers": {
            "hindsight": {
                "command": "uvx",
                "args": ["hindsight-api@latest", "hindsight-local-mcp"],
                "env": {
                    "HINDSIGHT_API_LLM_API_KEY": "your-openai-key"
                }
            }
        }
    }

Environment variables:
    HINDSIGHT_API_LLM_API_KEY: Required. API key for LLM provider.
    HINDSIGHT_API_LLM_PROVIDER: Optional. LLM provider (default: "openai").
    HINDSIGHT_API_LLM_MODEL: Optional. LLM model (default: "gpt-4o-mini").
    HINDSIGHT_API_MCP_LOCAL_BANK_ID: Optional. Memory bank ID (default: "mcp").
    HINDSIGHT_API_LOG_LEVEL: Optional. Log level (default: "info").
"""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from hindsight_api.config import (
    ENV_MCP_LOCAL_BANK_ID,
    DEFAULT_MCP_LOCAL_BANK_ID,
)

# Configure logging - default to info
_log_level_str = os.environ.get("HINDSIGHT_API_LOG_LEVEL", "info").lower()
_log_level_map = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}
logging.basicConfig(
    level=_log_level_map.get(_log_level_str, logging.WARNING),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stderr,  # MCP uses stdout for protocol, logs go to stderr
)
logger = logging.getLogger(__name__)


def create_local_mcp_server(bank_id: str, memory=None) -> FastMCP:
    """
    Create a stdio MCP server with retain/recall tools.

    Args:
        bank_id: The memory bank ID to use for all operations.
        memory: Optional MemoryEngine instance. If not provided, creates one with pg0.

    Returns:
        Configured FastMCP server instance.
    """
    # Import here to avoid slow startup if just checking --help
    from hindsight_api import MemoryEngine
    from hindsight_api.engine.memory_engine import Budget
    from hindsight_api.engine.response_models import VALID_RECALL_FACT_TYPES

    # Create memory engine with pg0 embedded database if not provided
    if memory is None:
        memory = MemoryEngine(db_url="pg0://hindsight-mcp")

    mcp = FastMCP("hindsight")

    @mcp.tool()
    async def retain(content: str, context: str = "general") -> dict:
        """
        Store important information to long-term memory.

        Use this tool PROACTIVELY whenever the user shares:
        - Personal facts, preferences, or interests
        - Important events or milestones
        - User history, experiences, or background
        - Decisions, opinions, or stated preferences
        - Goals, plans, or future intentions
        - Relationships or people mentioned
        - Work context, projects, or responsibilities

        Args:
            content: The fact/memory to store (be specific and include relevant details)
            context: Category for the memory (e.g., 'preferences', 'work', 'hobbies', 'family'). Default: 'general'
        """
        import asyncio

        async def _retain():
            try:
                await memory.retain_batch_async(
                    bank_id=bank_id,
                    contents=[{"content": content, "context": context}]
                )
            except Exception as e:
                logger.error(f"Error storing memory: {e}", exc_info=True)

        # Fire and forget - don't block on memory storage
        asyncio.create_task(_retain())
        return {"status": "accepted", "message": "Memory storage initiated"}

    @mcp.tool()
    async def recall(query: str, max_tokens: int = 4096, budget: str = "low") -> dict:
        """
        Search memories to provide personalized, context-aware responses.

        Use this tool PROACTIVELY to:
        - Check user's preferences before making suggestions
        - Recall user's history to provide continuity
        - Remember user's goals and context
        - Personalize responses based on past interactions

        Args:
            query: Natural language search query (e.g., "user's food preferences", "what projects is user working on")
            max_tokens: Maximum tokens to return in results (default: 4096)
            budget: Search budget level - "low", "mid", or "high" (default: "low")
        """
        try:
            # Map string budget to enum
            budget_map = {"low": Budget.LOW, "mid": Budget.MID, "high": Budget.HIGH}
            budget_enum = budget_map.get(budget.lower(), Budget.LOW)

            search_result = await memory.recall_async(
                bank_id=bank_id,
                query=query,
                fact_type=list(VALID_RECALL_FACT_TYPES),
                budget=budget_enum,
                max_tokens=max_tokens
            )

            return search_result.model_dump()
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return {"error": str(e), "results": []}

    return mcp


async def _initialize_and_run(bank_id: str):
    """Initialize memory and run the MCP server."""
    from hindsight_api import MemoryEngine

    # Create and initialize memory engine with pg0 embedded database
    print("Initializing memory engine...", file=sys.stderr)
    memory = MemoryEngine(db_url="pg0://hindsight-mcp")
    await memory.initialize()
    print("Memory engine initialized.", file=sys.stderr)

    # Create and run the server
    mcp = create_local_mcp_server(bank_id, memory=memory)
    await mcp.run_stdio_async()


def main():
    """Main entry point for the stdio MCP server."""
    import asyncio
    from hindsight_api.config import get_config, ENV_LLM_API_KEY

    # Check for required environment variables
    config = get_config()
    if not config.llm_api_key:
        print(f"Error: {ENV_LLM_API_KEY} environment variable is required", file=sys.stderr)
        print("Set it in your MCP configuration or shell environment", file=sys.stderr)
        sys.exit(1)

    # Get bank ID from environment, default to "mcp"
    bank_id = os.environ.get(ENV_MCP_LOCAL_BANK_ID, DEFAULT_MCP_LOCAL_BANK_ID)

    # Print startup message to stderr (stdout is reserved for MCP protocol)
    print(f"Hindsight MCP server starting (bank_id={bank_id})...", file=sys.stderr)

    # Run the async initialization and server
    asyncio.run(_initialize_and_run(bank_id))


if __name__ == "__main__":
    main()
