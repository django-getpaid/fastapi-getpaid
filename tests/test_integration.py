"""Full-stack integration tests: router + real SQLAlchemy repo + retry store."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from getpaid_core.exceptions import CommunicationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.contrib.sqlalchemy.models import CallbackRetryModel
from fastapi_getpaid.contrib.sqlalchemy.repository import (
    SQLAlchemyPaymentRepository,
)
from fastapi_getpaid.contrib.sqlalchemy.retry_store import (
    SQLAlchemyRetryStore,
)
from fastapi_getpaid.exceptions import register_exception_handlers
from fastapi_getpaid.router import create_payment_router


def _make_full_app(
    *,
    config: GetpaidConfig,
    repo: SQLAlchemyPaymentRepository,
    retry_store: SQLAlchemyRetryStore | None = None,
    order_resolver: object | None = None,
) -> FastAPI:
    """Build a FastAPI app with the full getpaid router.

    Exception handlers are registered eagerly (before app startup)
    because Starlette builds its middleware stack before the lifespan
    runs, so handlers added inside a router lifespan are too late.
    """
    router = create_payment_router(
        config=config,
        repository=repo,
        retry_store=retry_store,
        order_resolver=order_resolver,
    )
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/pay")
    return app


def test_full_app_starts(
    getpaid_config: GetpaidConfig,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Full app with real repo + retry store starts and returns 404 for
    a nonexistent payment."""
    repo = SQLAlchemyPaymentRepository(
        session_factory=async_session_factory,
    )
    retry_store = SQLAlchemyRetryStore(
        session_factory=async_session_factory,
    )
    app = _make_full_app(
        config=getpaid_config,
        repo=repo,
        retry_store=retry_store,
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/pay/payments/nonexistent-id")

    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == "not_found"
    assert "nonexistent-id" in data["detail"]


def test_create_and_get_payment(
    getpaid_config: GetpaidConfig,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """POST creates a payment (mocked flow), response has payment_id
    and redirect_url."""
    repo = SQLAlchemyPaymentRepository(
        session_factory=async_session_factory,
    )
    order_resolver = AsyncMock()
    order_resolver.resolve = AsyncMock(return_value=AsyncMock())

    app = _make_full_app(
        config=getpaid_config,
        repo=repo,
        order_resolver=order_resolver,
    )

    mock_payment = AsyncMock()
    mock_payment.id = "test-pay-1"
    mock_payment.order_id = "order-1"
    mock_payment.amount_required = Decimal("100.00")
    mock_payment.currency = "PLN"
    mock_payment.status = "new"
    mock_payment.backend = "dummy"
    mock_payment.external_id = None
    mock_payment.description = "Integration test"
    mock_payment.amount_paid = Decimal("0")
    mock_payment.amount_locked = Decimal("0")
    mock_payment.amount_refunded = Decimal("0")
    mock_payment.fraud_status = None
    mock_payment.fraud_message = None

    with patch(
        "fastapi_getpaid.routes.payments.PaymentFlow",
    ) as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.create_payment = AsyncMock(return_value=mock_payment)
        instance.prepare = AsyncMock(
            return_value={
                "redirect_url": "https://gateway.example.com/pay",
                "form_data": None,
                "method": "GET",
                "headers": {},
            }
        )

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/pay/payments/",
                json={
                    "order_id": "order-1",
                    "backend": "dummy",
                },
            )

    assert resp.status_code == 201
    data = resp.json()
    assert data["payment_id"] == "test-pay-1"
    assert data["redirect_url"] == "https://gateway.example.com/pay"
    assert data["method"] == "GET"


def test_callback_with_retry_on_failure(
    getpaid_config: GetpaidConfig,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Failed callback returns 502 with callback_failed code
    and stores a retry entry in the real retry store."""
    repo = SQLAlchemyPaymentRepository(
        session_factory=async_session_factory,
    )
    retry_store = SQLAlchemyRetryStore(
        session_factory=async_session_factory,
        backoff_seconds=5,
    )

    # Pre-populate a payment in the DB so the callback route can find it.
    loop = asyncio.new_event_loop()
    payment = loop.run_until_complete(
        repo.create(
            order_id="order-cb-1",
            amount_required=Decimal("50.00"),
            currency="PLN",
            backend="dummy",
            description="Callback test",
        )
    )
    loop.close()

    app = _make_full_app(
        config=getpaid_config,
        repo=repo,
        retry_store=retry_store,
    )

    with patch(
        "fastapi_getpaid.routes.callbacks.PaymentFlow",
    ) as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock(
            side_effect=CommunicationError("gateway timeout"),
        )

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                f"/pay/callback/{payment.id}",
                json={"status": "paid"},
            )

    assert resp.status_code == 502
    data = resp.json()
    assert data["code"] == "callback_failed"
    assert "gateway timeout" in data["detail"]

    # Verify the retry was persisted in the real DB by querying
    # the model table directly (get_due_retries filters by
    # next_retry_at <= now, but the backoff pushes it into the future).
    async def _count_retries() -> list[CallbackRetryModel]:
        async with async_session_factory() as session:
            stmt = select(CallbackRetryModel).where(
                CallbackRetryModel.payment_id == payment.id,
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    loop = asyncio.new_event_loop()
    retries = loop.run_until_complete(_count_retries())
    loop.close()

    assert len(retries) == 1
    retry = retries[0]
    assert retry.payment_id == payment.id
    assert retry.payload["status"] == "paid"
    assert retry.payload["_raw_body"] == '{"status":"paid"}'
    assert retry.status == "pending"
    assert retry.attempts == 0


def test_success_redirect(
    getpaid_config: GetpaidConfig,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """GET /pay/success/{id} redirects to success_url with payment_id."""
    repo = SQLAlchemyPaymentRepository(
        session_factory=async_session_factory,
    )

    # Pre-populate a payment so the redirect route can find it.
    loop = asyncio.new_event_loop()
    payment = loop.run_until_complete(
        repo.create(
            order_id="order-redir-1",
            amount_required=Decimal("75.00"),
            currency="PLN",
            backend="dummy",
            description="Redirect test",
        )
    )
    loop.close()

    app = _make_full_app(
        config=getpaid_config,
        repo=repo,
    )

    with TestClient(
        app,
        raise_server_exceptions=False,
        follow_redirects=False,
    ) as client:
        resp = client.get(f"/pay/success/{payment.id}")

    assert resp.status_code == 307
    location = resp.headers["location"]
    assert location == f"/success?payment_id={payment.id}"
