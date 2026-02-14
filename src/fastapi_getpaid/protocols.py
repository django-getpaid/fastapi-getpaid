"""Protocols for fastapi-getpaid.

Re-exports core protocols and defines FastAPI-specific ones.
"""

from typing import Protocol, runtime_checkable

from getpaid_core.protocols import Order, Payment, PaymentRepository

__all__ = [
    "CallbackRetryStore",
    "Order",
    "OrderResolver",
    "Payment",
    "PaymentRepository",
    "PaymentWithHelpers",
]


@runtime_checkable
class PaymentWithHelpers(Payment, Protocol):
    """Payment with FSM helper methods.

    The getpaid-core FSM guards require is_fully_paid() and
    is_fully_refunded() methods on payment objects. This protocol
    extends Payment to include them.
    """

    def is_fully_paid(self) -> bool: ...
    def is_fully_refunded(self) -> bool: ...


@runtime_checkable
class OrderResolver(Protocol):
    """Resolves an order_id string to an Order object.

    Users must provide an implementation that loads
    orders from their storage backend.
    """

    async def resolve(self, order_id: str) -> Order: ...


@runtime_checkable
class CallbackRetryStore(Protocol):
    """Storage abstraction for the webhook retry queue."""

    async def store_failed_callback(
        self,
        payment_id: str,
        payload: dict,
        headers: dict,
    ) -> str: ...

    async def get_due_retries(self, limit: int = 10) -> list[dict]: ...

    async def mark_succeeded(self, retry_id: str) -> None: ...

    async def mark_failed(
        self,
        retry_id: str,
        error: str,
    ) -> None: ...

    async def mark_exhausted(self, retry_id: str) -> None: ...
