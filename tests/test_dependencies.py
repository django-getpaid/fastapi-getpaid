"""Tests for FastAPI dependency providers."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class MockPaymentRepository:
    """In-memory mock repository."""

    def __init__(self) -> None:
        self.payments: dict[str, dict] = {}

    async def get_by_id(self, payment_id: str) -> dict:
        if payment_id not in self.payments:
            raise KeyError(payment_id)
        return self.payments[payment_id]

    async def create(self, **kwargs) -> dict:
        pid = f"pay-{len(self.payments) + 1}"
        self.payments[pid] = {"id": pid, **kwargs}
        return self.payments[pid]

    async def save(self, payment) -> dict:
        self.payments[payment["id"]] = payment
        return payment

    async def update_status(self, payment_id: str, status: str, **fields):
        self.payments[payment_id]["status"] = status
        return self.payments[payment_id]

    async def list_by_order(self, order_id: str) -> list:
        return [
            p for p in self.payments.values() if p.get("order_id") == order_id
        ]


def test_get_config_from_app_state():
    """get_config reads config from app.state."""
    from fastapi_getpaid.config import GetpaidConfig
    from fastapi_getpaid.dependencies import get_config

    app = FastAPI()
    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
    )
    app.state.getpaid_config = config

    @app.get("/test")
    async def handler(cfg: GetpaidConfig = Depends(get_config)):
        return {"backend": cfg.default_backend}

    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert resp.json()["backend"] == "dummy"


def test_get_repository_from_app_state():
    """get_repository reads repository from app.state."""
    from fastapi_getpaid.config import GetpaidConfig
    from fastapi_getpaid.dependencies import get_repository

    app = FastAPI()
    repo = MockPaymentRepository()
    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
    )
    app.state.getpaid_config = config
    app.state.getpaid_repository = repo

    @app.get("/test")
    async def handler(r=Depends(get_repository)):
        return {"type": type(r).__name__}

    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert resp.json()["type"] == "MockPaymentRepository"


def test_get_payment_flow():
    """get_payment_flow creates a PaymentFlow with deps."""
    from fastapi_getpaid.config import GetpaidConfig
    from fastapi_getpaid.dependencies import get_payment_flow

    app = FastAPI()
    repo = MockPaymentRepository()
    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {"sandbox": True}},
    )
    app.state.getpaid_config = config
    app.state.getpaid_repository = repo

    @app.get("/test")
    async def handler(flow=Depends(get_payment_flow)):
        return {"type": type(flow).__name__}

    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert resp.json()["type"] == "PaymentFlow"


def test_get_registry_from_app_state():
    """get_registry reads registry from app.state."""
    from fastapi_getpaid.dependencies import get_registry
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    app = FastAPI()
    reg = FastAPIPluginRegistry()
    app.state.getpaid_registry = reg

    @app.get("/test")
    async def handler(r=Depends(get_registry)):
        return {"type": type(r).__name__}

    client = TestClient(app)
    resp = client.get("/test")
    assert resp.status_code == 200
    assert resp.json()["type"] == "FastAPIPluginRegistry"
