"""Tests for callback (PUSH) route handlers."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from getpaid_core.exceptions import CommunicationError
from getpaid_core.exceptions import InvalidCallbackError

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.exceptions import register_exception_handlers
from fastapi_getpaid.registry import FastAPIPluginRegistry


@pytest.fixture
def config():
    return GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {"sandbox": True}},
    )


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    payment = AsyncMock()
    payment.id = "pay-1"
    payment.order = AsyncMock()
    payment.amount_required = Decimal("100")
    payment.currency = "PLN"
    payment.status = "prepared"
    payment.backend = "dummy"
    payment.external_id = ""
    payment.description = "Test"
    payment.amount_paid = Decimal("0")
    payment.amount_locked = Decimal("0")
    payment.amount_refunded = Decimal("0")
    payment.fraud_status = ""
    payment.fraud_message = ""
    repo.get_by_id = AsyncMock(return_value=payment)
    repo.save = AsyncMock(return_value=payment)
    return repo


@pytest.fixture
def app(config, mock_repo):
    from fastapi_getpaid.routes.callbacks import router

    app = FastAPI()
    app.state.getpaid_config = config
    app.state.getpaid_repository = mock_repo
    app.state.getpaid_registry = FastAPIPluginRegistry()
    app.state.getpaid_retry_store = None
    register_exception_handlers(app)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def test_callback_endpoint_exists(client):
    """POST /callback/{payment_id} exists."""
    resp = client.post("/callback/pay-1", json={"status": "paid"})
    # Should not be 404/405
    assert resp.status_code != 404
    assert resp.status_code != 405


def test_callback_returns_200_on_success(client, mock_repo):
    """Successful callback returns 200."""
    with patch(
        "fastapi_getpaid.routes.callbacks.PaymentFlow",
    ) as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock()

        resp = client.post(
            "/callback/pay-1",
            json={"status": "paid"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    raw_body = instance.handle_callback.await_args.kwargs["raw_body"]
    assert isinstance(raw_body, bytes)
    assert b'"status":"paid"' in raw_body


def test_callback_payment_not_found(client, mock_repo):
    """404 when payment not found."""
    mock_repo.get_by_id = AsyncMock(side_effect=KeyError("pay-999"))

    resp = client.post(
        "/callback/pay-999",
        json={"status": "paid"},
    )
    assert resp.status_code == 404


def test_callback_stores_retry_on_failure(client, mock_repo):
    """Failed callback is stored for retry when retry store exists."""
    retry_store = AsyncMock()
    retry_store.store_failed_callback = AsyncMock(return_value="retry-1")

    from fastapi_getpaid.routes.callbacks import router

    app = FastAPI()
    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {}},
    )
    app.state.getpaid_config = config
    app.state.getpaid_repository = mock_repo
    app.state.getpaid_registry = FastAPIPluginRegistry()
    app.state.getpaid_retry_store = retry_store
    register_exception_handlers(app)
    app.include_router(router)

    with patch(
        "fastapi_getpaid.routes.callbacks.PaymentFlow",
    ) as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock(
            side_effect=CommunicationError("gateway error")
        )

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.post(
            "/callback/pay-1",
            json={"status": "paid"},
        )
    assert resp.status_code == 502
    retry_store.store_failed_callback.assert_called_once()


def test_invalid_callback_returns_400_and_skips_retry(config, mock_repo):
    """Invalid callback should not be queued for retry."""
    retry_store = AsyncMock()
    retry_store.store_failed_callback = AsyncMock(return_value="retry-1")

    from fastapi_getpaid.routes.callbacks import router

    app = FastAPI()
    app.state.getpaid_config = config
    app.state.getpaid_repository = mock_repo
    app.state.getpaid_registry = FastAPIPluginRegistry()
    app.state.getpaid_retry_store = retry_store
    register_exception_handlers(app)
    app.include_router(router)

    with patch(
        "fastapi_getpaid.routes.callbacks.PaymentFlow",
    ) as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock(
            side_effect=InvalidCallbackError("bad signature")
        )

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.post(
            "/callback/pay-1",
            json={"status": "paid"},
        )
    assert resp.status_code == 400
    retry_store.store_failed_callback.assert_not_called()
