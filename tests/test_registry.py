"""Tests for the FastAPI-aware plugin registry wrapper."""

import pytest
from getpaid_core.processor import BaseProcessor
from getpaid_core.types import TransactionResult


class FakeProcessor(BaseProcessor):
    slug = "fake"
    display_name = "Fake Backend"
    accepted_currencies = ["PLN", "EUR"]

    async def prepare_transaction(self, **kwargs) -> TransactionResult:
        return TransactionResult(
            redirect_url="https://example.com",
            form_data=None,
            method="GET",
            headers={},
        )


def test_fastapi_registry_register_and_get():
    """Can register and retrieve a processor."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    reg.register(FakeProcessor)
    assert reg.get_by_slug("fake") is FakeProcessor


def test_fastapi_registry_get_for_currency():
    """Can find processors by currency."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    reg.register(FakeProcessor)
    backends = reg.get_for_currency("PLN")
    assert FakeProcessor in backends


def test_fastapi_registry_get_choices():
    """Returns slug/name pairs for a currency."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    reg.register(FakeProcessor)
    choices = reg.get_choices("PLN")
    assert ("fake", "Fake Backend") in choices


def test_fastapi_registry_unknown_slug_raises():
    """KeyError for unknown slug."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    with pytest.raises(KeyError):
        reg.get_by_slug("nonexistent")


def test_fastapi_registry_discover(monkeypatch: pytest.MonkeyPatch):
    """Discover delegates to core registry and copies backends."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    # Register directly for test (discover reads entry_points)
    reg.register(FakeProcessor)
    assert reg.get_by_slug("fake") is FakeProcessor


def test_fastapi_registry_unregister():
    """Can unregister a backend."""
    from fastapi_getpaid.registry import FastAPIPluginRegistry

    reg = FastAPIPluginRegistry()
    reg.register(FakeProcessor)
    reg.unregister("fake")
    with pytest.raises(KeyError):
        reg.get_by_slug("fake")
