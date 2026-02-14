"""Tests for exception-to-HTTP-response mapping."""

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app():
    """Create a test app with exception handlers registered."""
    from fastapi_getpaid.exceptions import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
    return app


def test_getpaid_exception_returns_400():
    """GetPaidException maps to 400."""
    from getpaid_core.exceptions import GetPaidException

    app = _make_app()

    @app.get("/test")
    async def _():
        raise GetPaidException("bad request")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 400
    data = resp.json()
    assert data["detail"] == "bad request"
    assert data["code"] == "payment_error"


def test_communication_error_returns_502():
    """CommunicationError maps to 502."""
    from getpaid_core.exceptions import CommunicationError

    app = _make_app()

    @app.get("/test")
    async def _():
        raise CommunicationError("gateway down")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 502
    assert resp.json()["code"] == "communication_error"


def test_invalid_callback_returns_400():
    """InvalidCallbackError maps to 400."""
    from getpaid_core.exceptions import InvalidCallbackError

    app = _make_app()

    @app.get("/test")
    async def _():
        raise InvalidCallbackError("bad signature")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_callback"


def test_invalid_transition_returns_409():
    """InvalidTransitionError maps to 409."""
    from getpaid_core.exceptions import InvalidTransitionError

    app = _make_app()

    @app.get("/test")
    async def _():
        raise InvalidTransitionError("wrong state")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_transition"


def test_credentials_error_returns_500():
    """CredentialsError maps to 500."""
    from getpaid_core.exceptions import CredentialsError

    app = _make_app()

    @app.get("/test")
    async def _():
        raise CredentialsError("missing API key")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 500
    assert resp.json()["code"] == "credentials_error"


def test_charge_failure_returns_502():
    """ChargeFailure (subclass of CommunicationError) maps to 502."""
    from getpaid_core.exceptions import ChargeFailure

    app = _make_app()

    @app.get("/test")
    async def _():
        raise ChargeFailure("charge failed")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/test")
    assert resp.status_code == 502
    assert resp.json()["code"] == "communication_error"
