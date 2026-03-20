"""Tests for FastAPI-specific protocol definitions."""

from decimal import Decimal


def test_callback_retry_store_is_protocol():
    """CallbackRetryStore is a runtime-checkable protocol."""
    from fastapi_getpaid.protocols import CallbackRetryStore

    assert hasattr(CallbackRetryStore, "__protocol_attrs__") or hasattr(
        CallbackRetryStore, "__abstractmethods__"
    )


def test_payment_protocol_reexport():
    from fastapi_getpaid.protocols import Payment

    class MockPayment:
        id = "p1"
        order = None  # type: ignore[assignment]
        amount_required = Decimal("100")
        currency = "PLN"
        status = "new"
        backend = "dummy"
        external_id = ""
        description = ""
        amount_paid = Decimal("0")
        amount_locked = Decimal("0")
        amount_refunded = Decimal("0")
        fraud_status = ""
        fraud_message = ""
        provider_data = {}

    p = MockPayment()
    assert isinstance(p, Payment)


def test_order_resolver_protocol():
    """OrderResolver resolves an order_id to an Order object."""
    from fastapi_getpaid.protocols import OrderResolver

    class MockResolver:
        async def resolve(self, order_id: str):
            return None

    assert isinstance(MockResolver(), OrderResolver)
