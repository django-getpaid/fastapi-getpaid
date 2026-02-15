"""SQLAlchemy models for the example application.

Defines Order and PaywallEntry models alongside the getpaid PaymentModel.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_getpaid.contrib.sqlalchemy.models import Base


class Order(Base):
    """A simple order that can be paid for."""

    __tablename__ = "example_order"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    buyer_email: Mapped[str] = mapped_column(
        String(255), default="buyer@example.com"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
    )

    def get_total_amount(self) -> Decimal:
        return self.amount

    def get_buyer_info(self) -> dict:
        return {"email": self.buyer_email}

    def get_description(self) -> str:
        return self.description

    def get_currency(self) -> str:
        return self.currency

    def get_items(self) -> list[dict]:
        return [
            {
                "name": self.description,
                "quantity": 1,
                "unit_price": self.amount,
            }
        ]

    def get_return_url(self, success: bool | None = None) -> str:
        if success:
            return f"http://127.0.0.1:8000/orders/{self.id}"
        return f"http://127.0.0.1:8000/orders/{self.id}"


class PaywallEntry(Base):
    """Simulated payment gateway record.

    The paywall app acts as a fake payment gateway. When a payment is
    initiated, a PaywallEntry is registered here and the user is
    redirected to the gateway authorization page.
    """

    __tablename__ = "paywall_entry"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    ext_id: Mapped[str] = mapped_column(
        String(100), index=True, default=lambda: str(uuid.uuid4())
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(Text, default="")
    callback: Mapped[str] = mapped_column(String(500), default="")
    success_url: Mapped[str] = mapped_column(String(500), default="")
    failure_url: Mapped[str] = mapped_column(String(500), default="")
    payment_status: Mapped[str] = mapped_column(String(50), default="new")
    fraud_status: Mapped[str] = mapped_column(String(50), default="unknown")
