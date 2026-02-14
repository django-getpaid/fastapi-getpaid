"""Shared test fixtures."""

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.contrib.sqlalchemy.models import Base


@pytest.fixture
async def async_engine():
    """In-memory SQLite async engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session_factory(async_engine):
    """Async session factory."""
    return async_sessionmaker(async_engine, class_=AsyncSession)


@pytest.fixture
def getpaid_config():
    """Standard test config."""
    return GetpaidConfig(
        default_backend="dummy",
        success_url="/success",
        failure_url="/failure",
        backends={"dummy": {"sandbox": True}},
        retry_max_attempts=3,
        retry_backoff_seconds=5,
    )
