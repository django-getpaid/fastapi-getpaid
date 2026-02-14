"""Router factory for fastapi-getpaid."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.exceptions import register_exception_handlers
from fastapi_getpaid.protocols import CallbackRetryStore, OrderResolver
from fastapi_getpaid.registry import FastAPIPluginRegistry
from fastapi_getpaid.routes.callbacks import router as callback_router
from fastapi_getpaid.routes.payments import router as payment_router
from fastapi_getpaid.routes.redirects import router as redirect_router


def create_payment_router(
    *,
    config: GetpaidConfig,
    repository: PaymentRepository,
    registry: FastAPIPluginRegistry | None = None,
    order_resolver: OrderResolver | None = None,
    retry_store: CallbackRetryStore | None = None,
) -> APIRouter:
    """Create a configured payment router.

    Args:
        config: Payment processing configuration.
        repository: Payment persistence backend.
        registry: Plugin registry. Creates a new one if not provided.
        order_resolver: Resolves order IDs to Order objects.
        retry_store: Storage for webhook retry queue.

    Returns:
        An APIRouter with all payment endpoints.
    """
    actual_registry = registry or FastAPIPluginRegistry()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.getpaid_config = config
        app.state.getpaid_repository = repository
        app.state.getpaid_registry = actual_registry
        app.state.getpaid_order_resolver = order_resolver
        app.state.getpaid_retry_store = retry_store
        register_exception_handlers(app)
        actual_registry.discover()
        yield

    router = APIRouter(lifespan=lifespan)
    router.include_router(callback_router)
    router.include_router(payment_router)
    router.include_router(redirect_router)

    return router
