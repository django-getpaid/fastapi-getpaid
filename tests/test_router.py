"""Tests for the router factory function."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.registry import FastAPIPluginRegistry


@pytest.fixture
def config():
    return GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {}},
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


def test_create_payment_router_returns_router(config, mock_repo):
    """Factory returns an APIRouter."""
    from fastapi_getpaid.router import create_payment_router

    router = create_payment_router(
        config=config,
        repository=mock_repo,
    )
    assert router is not None
    # Should have routes
    assert len(router.routes) > 0


def test_create_payment_router_includes_all_route_groups(config, mock_repo):
    """Router includes payment, callback, and redirect routes."""
    from fastapi_getpaid.router import create_payment_router

    router = create_payment_router(
        config=config,
        repository=mock_repo,
    )

    paths = [r.path for r in router.routes if hasattr(r, "path")]
    # Should have callback, payments, and redirect routes
    path_str = " ".join(paths)
    assert "callback" in path_str
    assert "payment" in path_str or "payments" in path_str
    assert "success" in path_str
    assert "failure" in path_str


def test_create_payment_router_sets_app_state(config, mock_repo):
    """Including the router sets app state."""
    from fastapi_getpaid.router import create_payment_router

    router = create_payment_router(
        config=config,
        repository=mock_repo,
    )
    app = FastAPI(lifespan=router.lifespan_context)
    app.include_router(router)

    with TestClient(app):
        # After startup, app.state should have getpaid objects
        assert hasattr(app.state, "getpaid_config")
        assert hasattr(app.state, "getpaid_repository")
        assert hasattr(app.state, "getpaid_registry")


def test_create_payment_router_with_custom_registry(config, mock_repo):
    """Can pass a custom registry."""
    from fastapi_getpaid.router import create_payment_router

    custom_reg = FastAPIPluginRegistry()

    router = create_payment_router(
        config=config,
        repository=mock_repo,
        registry=custom_reg,
    )
    app = FastAPI(lifespan=router.lifespan_context)
    app.include_router(router)

    with TestClient(app):
        assert app.state.getpaid_registry is custom_reg


def test_create_payment_router_with_order_resolver(config, mock_repo):
    """Can pass an order resolver."""
    from fastapi_getpaid.router import create_payment_router

    resolver = AsyncMock()

    router = create_payment_router(
        config=config,
        repository=mock_repo,
        order_resolver=resolver,
    )
    app = FastAPI(lifespan=router.lifespan_context)
    app.include_router(router)

    with TestClient(app):
        assert app.state.getpaid_order_resolver is resolver
