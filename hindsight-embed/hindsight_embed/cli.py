"""
Hindsight Embedded CLI.

A simple CLI for local memory operations using embedded PostgreSQL (pg0).
No external server required - runs everything locally.

Usage:
    hindsight-embed configure              # Interactive setup
    hindsight-embed retain "User prefers dark mode"
    hindsight-embed recall "What are user preferences?"

Environment variables:
    HINDSIGHT_EMBED_LLM_API_KEY: Required. API key for LLM provider.
    HINDSIGHT_EMBED_LLM_PROVIDER: Optional. LLM provider (default: "openai").
    HINDSIGHT_EMBED_LLM_MODEL: Optional. LLM model (default: "gpt-4o-mini").
    HINDSIGHT_EMBED_BANK_ID: Optional. Memory bank ID (default: "default").
    HINDSIGHT_EMBED_LOG_LEVEL: Optional. Log level (default: "warning").
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".hindsight"
CONFIG_FILE = CONFIG_DIR / "embed"


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level_str = os.environ.get("HINDSIGHT_EMBED_LOG_LEVEL", "warning").lower()
    if verbose:
        level_str = "debug"

    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    level = level_map.get(level_str, logging.WARNING)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stderr,
    )
    return logging.getLogger(__name__)


def load_config_file():
    """Load configuration from file if it exists."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    # Handle 'export VAR=value' format
                    if line.startswith("export "):
                        line = line[7:]
                    key, value = line.split("=", 1)
                    if key not in os.environ:  # Don't override env vars
                        os.environ[key] = value


def get_config():
    """Get configuration from environment variables."""
    load_config_file()
    return {
        "llm_api_key": os.environ.get("HINDSIGHT_EMBED_LLM_API_KEY")
            or os.environ.get("HINDSIGHT_API_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY"),
        "llm_provider": os.environ.get("HINDSIGHT_EMBED_LLM_PROVIDER")
            or os.environ.get("HINDSIGHT_API_LLM_PROVIDER", "openai"),
        "llm_model": os.environ.get("HINDSIGHT_EMBED_LLM_MODEL")
            or os.environ.get("HINDSIGHT_API_LLM_MODEL", "gpt-4o-mini"),
        "bank_id": os.environ.get("HINDSIGHT_EMBED_BANK_ID", "default"),
    }


def do_configure(args):
    """Interactive configuration setup with beautiful TUI."""
    import questionary
    from questionary import Style

    # Custom style for the prompts
    custom_style = Style([
        ('qmark', 'fg:cyan bold'),
        ('question', 'fg:white bold'),
        ('answer', 'fg:cyan'),
        ('pointer', 'fg:cyan bold'),
        ('highlighted', 'fg:cyan bold'),
        ('selected', 'fg:green'),
        ('text', 'fg:white'),
    ])

    print()
    print("\033[1m\033[36m  ╭─────────────────────────────────────╮\033[0m")
    print("\033[1m\033[36m  │   Hindsight Embed Configuration    │\033[0m")
    print("\033[1m\033[36m  ╰─────────────────────────────────────╯\033[0m")
    print()

    # Check existing config
    if CONFIG_FILE.exists():
        if not questionary.confirm(
            "Existing configuration found. Reconfigure?",
            default=False,
            style=custom_style,
        ).ask():
            print("\n\033[32m✓\033[0m Keeping existing configuration.")
            return 0
        print()

    # Provider selection with descriptions
    providers = [
        questionary.Choice("OpenAI (recommended)", value=("openai", "o3-mini", "OpenAI")),
        questionary.Choice("Groq (fast & free tier)", value=("groq", "openai/gpt-oss-20b", "Groq")),
        questionary.Choice("Google Gemini", value=("google", "gemini-2.0-flash", "Google")),
        questionary.Choice("Ollama (local, no API key)", value=("ollama", "llama3.2", None)),
    ]

    result = questionary.select(
        "Select your LLM provider:",
        choices=providers,
        style=custom_style,
    ).ask()

    if result is None:  # User cancelled
        print("\n\033[33m⚠\033[0m Configuration cancelled.")
        return 1

    provider, default_model, key_name = result

    # API key
    api_key = ""
    if key_name:
        env_keys = {
            "OpenAI": "OPENAI_API_KEY",
            "Groq": "GROQ_API_KEY",
            "Google": "GOOGLE_API_KEY",
        }
        env_key = env_keys.get(key_name, "")
        existing = os.environ.get(env_key, "")

        if existing:
            masked = existing[:8] + "..." + existing[-4:] if len(existing) > 12 else "***"
            if questionary.confirm(
                f"Found {key_name} key in ${env_key} ({masked}). Use it?",
                default=True,
                style=custom_style,
            ).ask():
                api_key = existing

        if not api_key:
            api_key = questionary.password(
                f"Enter your {key_name} API key:",
                style=custom_style,
            ).ask()

            if not api_key:
                print("\n\033[31m✗\033[0m API key is required.", file=sys.stderr)
                return 1

    # Model selection
    model = questionary.text(
        "Model name:",
        default=default_model,
        style=custom_style,
    ).ask()

    if model is None:
        return 1

    # Bank ID
    bank_id = questionary.text(
        "Memory bank ID:",
        default="default",
        style=custom_style,
    ).ask()

    if bank_id is None:
        return 1

    # Save configuration
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        f.write("# Hindsight Embed Configuration\n")
        f.write(f"# Generated by hindsight-embed configure\n\n")
        f.write(f"HINDSIGHT_EMBED_LLM_PROVIDER={provider}\n")
        f.write(f"HINDSIGHT_EMBED_LLM_MODEL={model}\n")
        f.write(f"HINDSIGHT_EMBED_BANK_ID={bank_id}\n")
        if api_key:
            f.write(f"HINDSIGHT_EMBED_LLM_API_KEY={api_key}\n")

    CONFIG_FILE.chmod(0o600)

    print()
    print("\033[32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[32m  ✓ Configuration saved!\033[0m")
    print("\033[32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print()
    print(f"  \033[2mConfig:\033[0m {CONFIG_FILE}")
    print()
    print("  \033[2mTest with:\033[0m")
    print('    \033[36mhindsight-embed retain "Test memory"\033[0m')
    print('    \033[36mhindsight-embed recall "test"\033[0m')
    print()

    return 0


async def _create_engine(config: dict, logger):
    """Create and initialize the memory engine."""
    logger.debug("Setting up environment variables...")

    # Set hindsight-api environment variables from our config
    if config["llm_api_key"]:
        os.environ["HINDSIGHT_API_LLM_API_KEY"] = config["llm_api_key"]
    if config["llm_provider"]:
        os.environ["HINDSIGHT_API_LLM_PROVIDER"] = config["llm_provider"]
    if config["llm_model"]:
        os.environ["HINDSIGHT_API_LLM_MODEL"] = config["llm_model"]

    logger.debug("Importing MemoryEngine...")

    # Import after setting env vars
    from hindsight_api import MemoryEngine
    from hindsight_api.engine.task_backend import SyncTaskBackend

    # Use pg0 embedded database
    db_name = f"hindsight-embed-{config['bank_id']}"
    logger.debug(f"Creating MemoryEngine with pg0://{db_name}")

    # Use SyncTaskBackend to avoid background workers that prevent clean exit
    memory = MemoryEngine(
        db_url=f"pg0://{db_name}",
        task_backend=SyncTaskBackend(),
    )

    logger.debug("Initializing engine...")
    await memory.initialize()

    logger.debug("Engine initialized")
    return memory


async def do_retain(args, config: dict, logger):
    """Execute retain command."""
    from hindsight_api.models import RequestContext

    logger.info(f"Retaining memory: {args.content[:50]}...")

    memory = await _create_engine(config, logger)

    try:
        logger.debug("Calling retain_batch_async...")
        await memory.retain_batch_async(
            bank_id=config["bank_id"],
            contents=[{
                "content": args.content,
                "context": args.context or "general",
            }],
            request_context=RequestContext(),
        )
        msg = f"Stored memory: {args.content[:50]}..." if len(args.content) > 50 else f"Stored memory: {args.content}"
        print(msg, flush=True)
        return 0
    except Exception as e:
        logger.error(f"Retain failed: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def do_recall(args, config: dict, logger):
    """Execute recall command."""
    from hindsight_api.engine.memory_engine import Budget
    from hindsight_api.engine.response_models import VALID_RECALL_FACT_TYPES
    from hindsight_api.models import RequestContext

    logger.info(f"Recalling with query: {args.query}")

    memory = await _create_engine(config, logger)

    try:
        budget_map = {"low": Budget.LOW, "mid": Budget.MID, "high": Budget.HIGH}
        budget_enum = budget_map.get(args.budget.lower(), Budget.LOW)

        logger.debug(f"Calling recall_async with budget={budget_enum}...")
        result = await memory.recall_async(
            bank_id=config["bank_id"],
            query=args.query,
            fact_type=list(VALID_RECALL_FACT_TYPES),
            budget=budget_enum,
            max_tokens=args.max_tokens,
            request_context=RequestContext(),
        )

        logger.debug(f"Recall returned {len(result.results)} results")

        if result.results:
            print("Memories found:", flush=True)
            print("-" * 40, flush=True)
            for fact in result.results:
                print(f"- {fact.text}", flush=True)
                if args.verbose and fact.occurred_start:
                    print(f"  (Date: {fact.occurred_start})", flush=True)
            print("-" * 40, flush=True)
            print(f"Total: {len(result.results)} memories", flush=True)
        else:
            print("No relevant memories found.", flush=True)

        return 0
    except Exception as e:
        logger.error(f"Recall failed: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hindsight Embedded CLI - local memory operations without a server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    hindsight-embed configure                              # Interactive setup
    hindsight-embed retain "User prefers dark mode"
    hindsight-embed retain "Meeting on Monday" -c work
    hindsight-embed recall "user preferences"
    hindsight-embed recall "meetings" --budget high
        """
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Configure command
    subparsers.add_parser("configure", help="Interactive configuration setup")

    # Retain command
    retain_parser = subparsers.add_parser("retain", help="Store a memory")
    retain_parser.add_argument("content", help="The memory content to store")
    retain_parser.add_argument(
        "--context", "-c",
        help="Category for the memory (e.g., 'preferences', 'work')",
        default="general"
    )

    # Recall command
    recall_parser = subparsers.add_parser("recall", help="Search memories")
    recall_parser.add_argument("query", help="Search query")
    recall_parser.add_argument(
        "--budget", "-b",
        choices=["low", "mid", "high"],
        default="low",
        help="Search budget level (default: low)"
    )
    recall_parser.add_argument(
        "--max-tokens", "-m",
        type=int,
        default=4096,
        help="Maximum tokens in results (default: 4096)"
    )
    recall_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show additional details"
    )

    args = parser.parse_args()

    # Setup logging
    verbose = getattr(args, 'verbose', False)
    logger = setup_logging(verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle configure separately (no config needed)
    if args.command == "configure":
        exit_code = do_configure(args)
        sys.exit(exit_code)

    config = get_config()

    # Check for LLM API key
    if not config["llm_api_key"]:
        print("Error: LLM API key is required.", file=sys.stderr)
        print("Run 'hindsight-embed configure' to set up.", file=sys.stderr)
        sys.exit(1)

    # Run the appropriate command
    exit_code = 1
    try:
        if args.command == "retain":
            exit_code = asyncio.run(do_retain(args, config, logger))
        elif args.command == "recall":
            exit_code = asyncio.run(do_recall(args, config, logger))
        else:
            parser.print_help()
            exit_code = 1
    except KeyboardInterrupt:
        logger.debug("Interrupted")
        exit_code = 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
