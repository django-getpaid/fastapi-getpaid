"""Tests for SQLAlchemy PaymentRepository implementation."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_getpaid.contrib.sqlalchemy.models import Base
from fastapi_getpaid.contrib.sqlalchemy.repository import (
    SQLAlchemyPaymentRepository,
)


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession)


@pytest.fixture
async def session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture
def repo(session_factory):
    return SQLAlchemyPaymentRepository(session_factory=session_factory)


async def test_create_payment(repo):
    """Repository creates a payment."""
    payment = await repo.create(
        order_id="order-1",
        amount_required=Decimal("100.00"),
        currency="PLN",
        backend="dummy",
        description="Test",
    )
    assert payment.id is not None
    assert payment.order_id == "order-1"
    assert payment.status == "new"


async def test_get_by_id(repo):
    """Repository retrieves a payment by ID."""
    created = await repo.create(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    fetched = await repo.get_by_id(created.id)
    assert fetched.id == created.id
    assert fetched.order_id == "order-1"


async def test_get_by_id_not_found(repo):
    """KeyError when payment not found."""
    with pytest.raises(KeyError):
        await repo.get_by_id("nonexistent")


async def test_save_payment(repo):
    """Repository saves updated payment fields."""
    payment = await repo.create(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    payment.external_id = "ext-123"
    saved = await repo.save(payment)
    assert saved.external_id == "ext-123"

    fetched = await repo.get_by_id(payment.id)
    assert fetched.external_id == "ext-123"


async def test_update_status(repo):
    """Repository updates payment status."""
    payment = await repo.create(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    updated = await repo.update_status(
        payment.id, "prepared", external_id="ext-456"
    )
    assert updated.status == "prepared"
    assert updated.external_id == "ext-456"


async def test_list_by_order(repo):
    """Repository lists payments for an order."""
    await repo.create(
        order_id="order-1",
        amount_required=Decimal("100"),
        currency="PLN",
        backend="dummy",
    )
    await repo.create(
        order_id="order-1",
        amount_required=Decimal("50"),
        currency="PLN",
        backend="paynow",
    )
    await repo.create(
        order_id="order-2",
        amount_required=Decimal("200"),
        currency="EUR",
        backend="dummy",
    )

    payments = await repo.list_by_order("order-1")
    assert len(payments) == 2
    assert all(p.order_id == "order-1" for p in payments)


async def test_list_by_order_empty(repo):
    """Empty list when no payments for order."""
    payments = await repo.list_by_order("nonexistent")
    assert payments == []
