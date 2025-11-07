"""
Web interface for memory system.

Provides FastAPI app and visualization interface.
"""
from .server import create_app

# Lazy import of app to avoid initialization issues
def __getattr__(name):
    if name == "app":
        from .server import _get_app
        return _get_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["app", "create_app"]
