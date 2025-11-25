"""
Web interface for memory system.

Provides FastAPI app and visualization interface.
"""
from hindsight_api.api import create_app

# Note: Don't import app from .server here to avoid circular import warnings
# when running with `python -m hindsight_api.web.server`
# If you need the app, import it directly: from hindsight_api.web.server import app

__all__ = ["create_app"]
