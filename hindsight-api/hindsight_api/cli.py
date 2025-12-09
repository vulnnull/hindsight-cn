"""
Command-line interface for Hindsight API.

Run the server with:
    hindsight-api

Stop with Ctrl+C.
"""
import argparse
import asyncio
import atexit
import os
import signal
import sys
from typing import Optional

import uvicorn

from . import MemoryEngine
from .api import create_app


# Disable tokenizers parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Global reference for cleanup
_memory: Optional[MemoryEngine] = None


def _cleanup():
    """Synchronous cleanup function to stop resources on exit."""
    global _memory
    if _memory is not None and _memory._pg0 is not None:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_memory._pg0.stop())
            loop.close()
            print("\npg0 stopped.")
        except Exception as e:
            print(f"\nError stopping pg0: {e}")


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM to ensure cleanup."""
    print(f"\nReceived signal {signum}, shutting down...")
    _cleanup()
    sys.exit(0)


def main():
    """Main entry point for the CLI."""
    global _memory

    parser = argparse.ArgumentParser(
        prog="hindsight-api",
        description="Hindsight API Server",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8888,
        help="Port to bind to (default: 8888)"
    )
    parser.add_argument(
        "--log-level", default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--access-log", action="store_true",
        help="Enable access log"
    )

    args = parser.parse_args()

    # Register cleanup handlers
    atexit.register(_cleanup)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Get configuration from environment variables
    db_url = os.getenv("HINDSIGHT_API_DATABASE_URL", "pg0")
    llm_provider = os.getenv("HINDSIGHT_API_LLM_PROVIDER", "groq")
    llm_api_key = os.getenv("HINDSIGHT_API_LLM_API_KEY", "")
    llm_model = os.getenv("HINDSIGHT_API_LLM_MODEL", "openai/gpt-oss-20b")
    llm_base_url = os.getenv("HINDSIGHT_API_LLM_BASE_URL") or None

    # Create MemoryEngine
    _memory = MemoryEngine(
        db_url=db_url,
        memory_llm_provider=llm_provider,
        memory_llm_api_key=llm_api_key,
        memory_llm_model=llm_model,
        memory_llm_base_url=llm_base_url,
    )

    # Create FastAPI app
    app = create_app(
        memory=_memory,
        http_api_enabled=True,
        mcp_api_enabled=True,
        mcp_mount_path="/mcp",
        initialize_memory=True,
    )

    # Prepare uvicorn config
    uvicorn_config = {
        "app": app,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": args.access_log,
    }

    print(f"\nStarting Hindsight API...")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  Database: {db_url}")
    print(f"  LLM Provider: {llm_provider}")
    print()

    uvicorn.run(**uvicorn_config)


if __name__ == "__main__":
    main()
