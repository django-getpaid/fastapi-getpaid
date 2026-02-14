"""FastAPI-aware plugin registry wrapper."""

from getpaid_core.registry import PluginRegistry


class FastAPIPluginRegistry(PluginRegistry):
    """Plugin registry with FastAPI-specific features.

    Wraps the core PluginRegistry and adds router mounting
    for backend-specific callback routes.
    """

    def __init__(self) -> None:
        super().__init__()
        self._backend_routers: dict = {}

    def register_backend_router(
        self,
        slug: str,
        router: object,
    ) -> None:
        """Register a FastAPI APIRouter for a backend's custom routes."""
        self._backend_routers[slug] = router

    def get_backend_router(self, slug: str) -> object | None:
        """Get a backend's custom APIRouter, if registered."""
        return self._backend_routers.get(slug)

    def get_all_backend_routers(self) -> dict:
        """Return all registered backend routers."""
        return dict(self._backend_routers)
