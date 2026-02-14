"""Tests for FastAPI-specific protocol definitions."""

from decimal import Decimal


def test_callback_retry_store_is_protocol():
    """CallbackRetryStore is a runtime-checkable protocol."""
    from fastapi_getpaid.protocols import CallbackRetryStore

    assert hasattr(CallbackRetryStore, "__protocol_attrs__") or hasattr(
        CallbackRetryStore, "__abstractmethods__"
    )


def test_payment_with_helpers_protocol():
    """Payment objects need is_fully_paid and is_fully_refunded for FSM."""
    from fastapi_getpaid.protocols import PaymentWithHelpers

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

        def is_fully_paid(self) -> bool:
            return self.amount_paid >= self.amount_required

        def is_fully_refunded(self) -> bool:
            return self.amount_refunded >= self.amount_paid

    p = MockPayment()
    assert isinstance(p, PaymentWithHelpers)


def test_order_resolver_protocol():
    """OrderResolver resolves an order_id to an Order object."""
    from fastapi_getpaid.protocols import OrderResolver

    class MockResolver:
        async def resolve(self, order_id: str):
            return None

    assert isinstance(MockResolver(), OrderResolver)
