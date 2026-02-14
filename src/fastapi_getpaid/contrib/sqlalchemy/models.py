"""SQLAlchemy 2.0 async models for payment processing."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all getpaid models."""


class PaymentModel(Base):
    """Payment record implementing the Payment protocol."""

    __tablename__ = "getpaid_payment"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id: Mapped[str] = mapped_column(String(255), index=True)
    amount_required: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(50), default="new")
    backend: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    amount_locked: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    amount_refunded: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )
    fraud_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    fraud_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    def is_fully_paid(self) -> bool:
        """Check if the payment amount has been fully covered."""
        paid = self.amount_paid or Decimal("0")
        return paid >= self.amount_required

    def is_fully_refunded(self) -> bool:
        """Check if the paid amount has been fully refunded."""
        refunded = self.amount_refunded or Decimal("0")
        paid = self.amount_paid or Decimal("0")
        return refunded >= paid


class CallbackRetryModel(Base):
    """Webhook callback retry queue entry."""

    __tablename__ = "getpaid_callback_retry"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    payment_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    headers: Mapped[dict] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_error: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=UTC),
    )
