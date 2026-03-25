"""Tests for payment CRUD REST API routes."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from getpaid_core.types import TransactionResult

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.exceptions import register_exception_handlers
from fastapi_getpaid.registry import FastAPIPluginRegistry


class DummyOrder:
    def __init__(self, order_id: str = "order-1") -> None:
        self.id = order_id
        self.description = "Test order"
        self.currency = "PLN"
        self.total = Decimal("100")

    def get_total_amount(self) -> Decimal:
        return self.total

    def get_buyer_info(self) -> dict:
        return {"email": "test@example.com"}

    def get_description(self) -> str:
        return self.description

    def get_currency(self) -> str:
        return self.currency

    def get_items(self) -> list[dict]:
        return []

    def get_return_url(self, success: bool | None = None) -> str:
        return "/return"


@pytest.fixture
def config():
    return GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {"sandbox": True}},
    )


@pytest.fixture
def mock_payment():
    payment = AsyncMock()
    payment.id = "pay-1"
    payment.order = DummyOrder()
    payment.order_id = "order-1"
    payment.amount_required = Decimal("100")
    payment.currency = "PLN"
    payment.status = "new"
    payment.backend = "dummy"
    payment.external_id = None
    payment.description = "Test payment"
    payment.amount_paid = Decimal("0")
    payment.amount_locked = Decimal("0")
    payment.amount_refunded = Decimal("0")
    payment.fraud_status = None
    payment.fraud_message = None
    payment.provider_data = {"customer_ip": "127.0.0.1"}
    return payment


@pytest.fixture
def mock_repo(mock_payment):
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=mock_payment)
    repo.list_by_order = AsyncMock(return_value=[mock_payment])
    repo.create = AsyncMock(return_value=mock_payment)
    repo.save = AsyncMock(return_value=mock_payment)
    return repo


@pytest.fixture
def mock_order():
    return DummyOrder()


@pytest.fixture
def app(config, mock_repo):
    from fastapi_getpaid.routes.payments import router

    app = FastAPI()
    app.state.getpaid_config = config
    app.state.getpaid_repository = mock_repo
    app.state.getpaid_registry = FastAPIPluginRegistry()
    app.state.getpaid_order_resolver = None
    register_exception_handlers(app)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def test_get_payment(client, mock_payment):
    """GET /payments/{id} returns payment data."""
    resp = client.get("/payments/pay-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "pay-1"
    assert data["status"] == "new"


def test_get_payment_not_found(client, mock_repo):
    """GET /payments/{id} returns 404 for unknown payment."""
    mock_repo.get_by_id = AsyncMock(side_effect=KeyError("pay-999"))
    resp = client.get("/payments/pay-999")
    assert resp.status_code == 404


def test_list_payments(client, mock_repo, mock_payment):
    """GET /payments/ returns list of payments."""
    mock_repo.list_by_order = AsyncMock(return_value=[mock_payment])
    resp = client.get("/payments/?order_id=order-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_create_payment(client, mock_repo, mock_payment, mock_order):
    """POST /payments/ creates a new payment."""
    resolver = AsyncMock()
    resolver.resolve = AsyncMock(return_value=mock_order)

    from fastapi_getpaid.routes.payments import router

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
    app.state.getpaid_order_resolver = resolver
    register_exception_handlers(app)
    app.include_router(router)

    with patch("fastapi_getpaid.routes.payments.PaymentFlow") as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.create_payment = AsyncMock(return_value=mock_payment)
        instance.prepare = AsyncMock(
            return_value=TransactionResult(
                redirect_url="https://gateway.example.com/pay",
                form_data=None,
                method="GET",
                external_id="ext-123",
                provider_data={"customer_ip": "127.0.0.1"},
            )
        )

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.post(
            "/payments/",
            json={
                "order_id": "order-1",
                "backend": "dummy",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["payment_id"] == "pay-1"
    assert data["redirect_url"] == "https://gateway.example.com/pay"
    assert data["provider_data"] == {"customer_ip": "127.0.0.1"}


def test_payment_response_includes_provider_data(client):
    resp = client.get("/payments/pay-1")
    assert resp.status_code == 200
    assert resp.json()["provider_data"] == {"customer_ip": "127.0.0.1"}


def test_create_payment_without_resolver(client):
    """POST /payments/ returns 500 when no order resolver configured."""
    resp = client.post(
        "/payments/",
        json={
            "order_id": "order-1",
            "backend": "dummy",
        },
    )
    assert resp.status_code == 500
