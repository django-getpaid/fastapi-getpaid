"""SQLAlchemy 2.0 async PaymentRepository implementation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_getpaid.contrib.sqlalchemy.models import PaymentModel


class SQLAlchemyPaymentRepository:
    """Payment repository backed by SQLAlchemy async sessions.

    Implements the PaymentRepository protocol from getpaid-core.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, payment_id: str) -> PaymentModel:
        """Get a payment by ID. Raises KeyError if not found."""
        async with self._session_factory() as session:
            result = await session.get(PaymentModel, payment_id)
            if result is None:
                raise KeyError(payment_id)
            # Expunge so object is usable outside session
            session.expunge(result)
            return result

    async def create(self, **kwargs) -> PaymentModel:
        """Create a new payment record."""
        async with self._session_factory() as session:
            payment = PaymentModel(**kwargs)
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            session.expunge(payment)
            return payment

    async def save(self, payment: PaymentModel) -> PaymentModel:
        """Save an existing payment (merge and commit)."""
        async with self._session_factory() as session:
            merged = await session.merge(payment)
            await session.commit()
            await session.refresh(merged)
            session.expunge(merged)
            return merged

    async def update_status(
        self,
        payment_id: str,
        status: str,
        **fields,
    ) -> PaymentModel:
        """Update payment status and optional extra fields."""
        async with self._session_factory() as session:
            payment = await session.get(PaymentModel, payment_id)
            if payment is None:
                raise KeyError(payment_id)
            payment.status = status
            for key, value in fields.items():
                if hasattr(payment, key):
                    setattr(payment, key, value)
            await session.commit()
            await session.refresh(payment)
            session.expunge(payment)
            return payment

    async def list_by_order(self, order_id: str) -> list[PaymentModel]:
        """List all payments for an order."""
        async with self._session_factory() as session:
            stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
            result = await session.execute(stmt)
            payments = list(result.scalars().all())
            for p in payments:
                session.expunge(p)
            return payments
