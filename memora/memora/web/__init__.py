"""
Web interface for memory system.

Provides FastAPI app and visualization interface.
"""
from memora.api import create_app
from .server import app

__all__ = ["app", "create_app"]
