"""Tests for SQLAlchemy 2.0 async models."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_getpaid.contrib.sqlalchemy.models import (
    Base,
    CallbackRetryModel,
    PaymentModel,
)


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    session_factory = async_sessionmaker(engine, class_=AsyncSession)
    async with session_factory() as session:
        yield session


async def test_payment_model_create(session):
    """Can create a PaymentModel."""
    payment = PaymentModel(
        order_id="order-1",
        amount_required=Decimal("100.00"),
        currency="PLN",
        backend="dummy",
        description="Test payment",
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    assert payment.id is not None
    assert payment.status == "new"
    assert payment.amount_paid == Decimal("0")


async def test_payment_model_defaults(session):
    """PaymentModel has correct defaults."""
    payment = PaymentModel(
        order_id="order-1",
        amount_required=Decimal("50"),
        currency="EUR",
        backend="paynow",
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    assert payment.amount_locked == Decimal("0")
    assert payment.amount_refunded == Decimal("0")
    assert payment.external_id is None
    assert payment.fraud_status is None


async def test_payment_model_is_fully_paid(session):
    """is_fully_paid returns True when amount_paid >= amount_required."""
    payment = PaymentModel(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    assert payment.is_fully_paid() is False

    payment.amount_paid = Decimal("100")
    assert payment.is_fully_paid() is True


async def test_payment_model_is_fully_refunded(session):
    """is_fully_refunded returns True when amount_refunded >= amount_paid."""
    payment = PaymentModel(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    payment.amount_paid = Decimal("100")
    payment.amount_refunded = Decimal("0")
    assert payment.is_fully_refunded() is False

    payment.amount_refunded = Decimal("100")
    assert payment.is_fully_refunded() is True


async def test_callback_retry_model_create(session):
    """Can create a CallbackRetryModel."""
    # First create a payment to reference
    payment = PaymentModel(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    retry = CallbackRetryModel(
        payment_id=str(payment.id),
        payload={"status": "paid"},
        headers={"content-type": "application/json"},
    )
    session.add(retry)
    await session.commit()
    await session.refresh(retry)

    assert retry.id is not None
    assert retry.attempts == 0
    assert retry.status == "pending"
    assert retry.last_error is None


async def test_payment_model_table_name():
    """PaymentModel uses correct table name."""
    assert PaymentModel.__tablename__ == "getpaid_payment"


async def test_callback_retry_model_table_name():
    """CallbackRetryModel uses correct table name."""
    assert CallbackRetryModel.__tablename__ == "getpaid_callback_retry"
