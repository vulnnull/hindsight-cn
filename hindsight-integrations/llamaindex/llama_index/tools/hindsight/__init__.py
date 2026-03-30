"""Hindsight memory tools for LlamaIndex agents.

Provides a ``BaseToolSpec`` subclass and a convenience factory that give
LlamaIndex agents long-term memory via Hindsight's retain/recall/reflect APIs.

Usage::

    from llama_index.tools.hindsight import HindsightToolSpec, create_hindsight_tools
"""

from .base import HindsightToolSpec, create_hindsight_tools
from .config import (
    HindsightLlamaIndexConfig,
    configure,
    get_config,
    reset_config,
)
from .errors import HindsightError

__version__ = "0.1.0"

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "HindsightLlamaIndexConfig",
    "HindsightError",
    "HindsightToolSpec",
    "create_hindsight_tools",
]
