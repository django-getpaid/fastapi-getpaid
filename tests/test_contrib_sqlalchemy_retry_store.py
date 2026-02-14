"""Tests for SQLAlchemy retry store implementation."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_getpaid.contrib.sqlalchemy.models import (
    Base,
    CallbackRetryModel,
)
from fastapi_getpaid.contrib.sqlalchemy.retry_store import (
    SQLAlchemyRetryStore,
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
def store(session_factory):
    return SQLAlchemyRetryStore(
        session_factory=session_factory,
        backoff_seconds=10,
    )


async def test_store_failed_callback(store):
    """Stores a failed callback and returns an ID."""
    retry_id = await store.store_failed_callback(
        payment_id="pay-1",
        payload={"status": "paid"},
        headers={"content-type": "application/json"},
    )
    assert retry_id is not None
    assert isinstance(retry_id, str)


async def test_get_due_retries_empty(store):
    """No retries when store is empty."""
    retries = await store.get_due_retries()
    assert retries == []


async def test_get_due_retries_finds_due(store, session_factory):
    """Finds retries that are past their next_retry_at."""
    async with session_factory() as session:
        retry = CallbackRetryModel(
            payment_id="pay-1",
            payload={"status": "paid"},
            headers={},
            attempts=1,
            next_retry_at=datetime.now(tz=timezone.utc) - timedelta(minutes=1),
            status="pending",
        )
        session.add(retry)
        await session.commit()

    retries = await store.get_due_retries()
    assert len(retries) == 1
    assert retries[0]["payment_id"] == "pay-1"


async def test_get_due_retries_skips_future(store, session_factory):
    """Skips retries that aren't due yet."""
    async with session_factory() as session:
        retry = CallbackRetryModel(
            payment_id="pay-1",
            payload={"status": "paid"},
            headers={},
            attempts=1,
            next_retry_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
            status="pending",
        )
        session.add(retry)
        await session.commit()

    retries = await store.get_due_retries()
    assert retries == []


async def test_mark_succeeded(store, session_factory):
    """Marks a retry as succeeded."""
    retry_id = await store.store_failed_callback(
        payment_id="pay-1",
        payload={},
        headers={},
    )
    await store.mark_succeeded(retry_id)

    async with session_factory() as session:
        retry = await session.get(CallbackRetryModel, retry_id)
        assert retry is not None
        assert retry.status == "succeeded"


async def test_mark_failed(store, session_factory):
    """Marks a retry as failed with error and increments attempts."""
    retry_id = await store.store_failed_callback(
        payment_id="pay-1",
        payload={},
        headers={},
    )
    await store.mark_failed(retry_id, error="Connection timeout")

    async with session_factory() as session:
        retry = await session.get(CallbackRetryModel, retry_id)
        assert retry is not None
        assert retry.status == "pending"  # Still pending for next retry
        assert retry.attempts == 1
        assert retry.last_error == "Connection timeout"
        assert retry.next_retry_at is not None


async def test_mark_exhausted(store, session_factory):
    """Marks a retry as exhausted (dead letter)."""
    retry_id = await store.store_failed_callback(
        payment_id="pay-1",
        payload={},
        headers={},
    )
    await store.mark_exhausted(retry_id)

    async with session_factory() as session:
        retry = await session.get(CallbackRetryModel, retry_id)
        assert retry is not None
        assert retry.status == "exhausted"
