"""SQLAlchemy-backed retry store for webhook callbacks."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_getpaid.contrib.sqlalchemy.models import CallbackRetryModel
from fastapi_getpaid.retry import compute_next_retry_at


class SQLAlchemyRetryStore:
    """Callback retry store backed by SQLAlchemy.

    Implements the CallbackRetryStore protocol.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        backoff_seconds: int = 60,
    ) -> None:
        self._session_factory = session_factory
        self._backoff_seconds = backoff_seconds

    async def store_failed_callback(
        self,
        payment_id: str,
        payload: dict,
        headers: dict,
    ) -> str:
        """Store a failed callback for later retry."""
        async with self._session_factory() as session:
            retry = CallbackRetryModel(
                payment_id=payment_id,
                payload=payload,
                headers=headers,
                attempts=0,
                next_retry_at=compute_next_retry_at(
                    attempt=1,
                    backoff_seconds=self._backoff_seconds,
                ),
                status="pending",
            )
            session.add(retry)
            await session.commit()
            await session.refresh(retry)
            return retry.id

    async def get_due_retries(self, limit: int = 10) -> list[dict]:
        """Get retries that are due for processing."""
        now = datetime.now(tz=UTC)
        async with self._session_factory() as session:
            stmt = (
                select(CallbackRetryModel)
                .where(CallbackRetryModel.status == "pending")
                .where(CallbackRetryModel.next_retry_at <= now)
                .limit(limit)
            )
            result = await session.execute(stmt)
            retries = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "payment_id": r.payment_id,
                    "payload": r.payload,
                    "headers": r.headers,
                    "attempts": r.attempts,
                }
                for r in retries
            ]

    async def mark_succeeded(self, retry_id: str) -> None:
        """Mark a retry as successfully processed."""
        async with self._session_factory() as session:
            retry = await session.get(CallbackRetryModel, retry_id)
            if retry is not None:
                retry.status = "succeeded"
                await session.commit()

    async def mark_failed(self, retry_id: str, error: str) -> None:
        """Mark a retry as failed and schedule next attempt."""
        async with self._session_factory() as session:
            retry = await session.get(CallbackRetryModel, retry_id)
            if retry is not None:
                retry.attempts += 1
                retry.last_error = error
                retry.next_retry_at = compute_next_retry_at(
                    attempt=retry.attempts + 1,
                    backoff_seconds=self._backoff_seconds,
                )
                retry.status = "pending"
                await session.commit()

    async def mark_exhausted(self, retry_id: str) -> None:
        """Mark a retry as exhausted (dead letter)."""
        async with self._session_factory() as session:
            retry = await session.get(CallbackRetryModel, retry_id)
            if retry is not None:
                retry.status = "exhausted"
                await session.commit()
