"""FastAPI-aware plugin registry wrapper."""

from getpaid_core.registry import PluginRegistry


class FastAPIPluginRegistry(PluginRegistry):
    """Plugin registry wrapper for FastAPI adapter code."""
