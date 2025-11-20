"""
FastAPI server for memory graph visualization and API.

Provides REST API endpoints for memory operations and serves
the interactive visualization interface.
"""
import logging
import os
import argparse

from memora import TemporalSemanticMemory
from memora.api import create_app

# Disable tokenizers parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Create app at module level (required for uvicorn import string)
_memory = TemporalSemanticMemory(
    db_url=os.getenv("MEMORA_API_DATABASE_URL"),
    memory_llm_provider=os.getenv("MEMORA_API_LLM_PROVIDER", "groq"),
    memory_llm_api_key=os.getenv("MEMORA_API_LLM_API_KEY"),
    memory_llm_model=os.getenv("MEMORA_API_LLM_MODEL", "openai/gpt-oss-120b"),
    memory_llm_base_url=os.getenv("MEMORA_API_LLM_BASE_URL") or None,
)

# Check if MCP should be enabled
mcp_enabled = os.getenv("MEMORA_API_MCP_ENABLED", "true").lower() == "true"

# Create unified app with both HTTP and optionally MCP
app = create_app(
    memory=_memory,
    http_api_enabled=True,
    mcp_api_enabled=mcp_enabled,
    mcp_mount_path="/mcp"
)


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Memory Graph API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to (default: 8080)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    parser.add_argument("--log-level", default="info", choices=["critical", "error", "warning", "info", "debug", "trace"],
                        help="Log level (default: info)")
    parser.add_argument("--access-log", action="store_true", help="Enable access log")
    parser.add_argument("--no-access-log", dest="access_log", action="store_false", help="Disable access log")
    parser.add_argument("--proxy-headers", action="store_true", help="Enable X-Forwarded-Proto, X-Forwarded-For headers")
    parser.add_argument("--forwarded-allow-ips", default=None, help="Comma separated list of IPs to trust with proxy headers")
    parser.add_argument("--ssl-keyfile", default=None, help="SSL key file")
    parser.add_argument("--ssl-certfile", default=None, help="SSL certificate file")
    parser.set_defaults(access_log=False)

    args = parser.parse_args()

    app_ref = "memora.web.server:app"

    # Prepare uvicorn config
    uvicorn_config = {
        "app": app_ref,
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "workers": args.workers,
        "log_level": args.log_level,
        "access_log": args.access_log,
        "proxy_headers": args.proxy_headers,
    }

    # Add optional parameters if provided
    if args.forwarded_allow_ips:
        uvicorn_config["forwarded_allow_ips"] = args.forwarded_allow_ips
    if args.ssl_keyfile:
        uvicorn_config["ssl_keyfile"] = args.ssl_keyfile
    if args.ssl_certfile:
        uvicorn_config["ssl_certfile"] = args.ssl_certfile

    uvicorn.run(**uvicorn_config)
