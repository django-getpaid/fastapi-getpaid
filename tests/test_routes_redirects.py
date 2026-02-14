"""Tests for success/failure redirect endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.exceptions import register_exception_handlers
from fastapi_getpaid.registry import FastAPIPluginRegistry


@pytest.fixture
def config():
    return GetpaidConfig(
        default_backend="dummy",
        success_url="https://shop.example.com/thank-you",
        failure_url="https://shop.example.com/payment-failed",
        backends={},
    )


@pytest.fixture
def mock_payment():
    payment = AsyncMock()
    payment.id = "pay-1"
    payment.status = "paid"
    payment.backend = "dummy"
    return payment


@pytest.fixture
def mock_repo(mock_payment):
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=mock_payment)
    return repo


@pytest.fixture
def app(config, mock_repo):
    from fastapi_getpaid.routes.redirects import router

    app = FastAPI()
    app.state.getpaid_config = config
    app.state.getpaid_repository = mock_repo
    app.state.getpaid_registry = FastAPIPluginRegistry()
    register_exception_handlers(app)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(
        app, raise_server_exceptions=False, follow_redirects=False
    )


def test_success_redirect(client):
    """GET /success/{id} redirects to success_url."""
    resp = client.get("/success/pay-1")
    assert resp.status_code == 307
    assert "thank-you" in resp.headers["location"]


def test_failure_redirect(client):
    """GET /failure/{id} redirects to failure_url."""
    resp = client.get("/failure/pay-1")
    assert resp.status_code == 307
    assert "payment-failed" in resp.headers["location"]


def test_success_payment_not_found(client, mock_repo):
    """GET /success/{id} returns 404 for unknown payment."""
    mock_repo.get_by_id = AsyncMock(side_effect=KeyError("pay-999"))
    resp = client.get("/success/pay-999")
    assert resp.status_code == 404


def test_failure_payment_not_found(client, mock_repo):
    """GET /failure/{id} returns 404 for unknown payment."""
    mock_repo.get_by_id = AsyncMock(side_effect=KeyError("pay-999"))
    resp = client.get("/failure/pay-999")
    assert resp.status_code == 404
