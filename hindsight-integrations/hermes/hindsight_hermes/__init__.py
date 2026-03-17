"""Hindsight-Hermes: Persistent memory tools for Hermes agents.

Provides Hindsight retain/recall/reflect as native Hermes tools via the
plugin system or manual ``register_tools()`` call.

Plugin usage (auto-discovery)::

    pip install hindsight-hermes
    export HINDSIGHT_API_URL=http://localhost:8888
    export HINDSIGHT_BANK_ID=my-agent

Manual usage::

    from hindsight_hermes import register_tools

    register_tools(
        bank_id="my-agent",
        hindsight_api_url="http://localhost:8888",
    )
"""

from .config import (
    HindsightHermesConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import HindsightError
from .tools import (
    get_tool_definitions,
    memory_instructions,
    register,
    register_tools,
)

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "HindsightHermesConfig",
    "HindsightError",
    "register_tools",
    "register",
    "memory_instructions",
    "get_tool_definitions",
]
