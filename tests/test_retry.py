"""Tests for the webhook retry mechanism."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_retry_store():
    store = AsyncMock()
    store.get_due_retries = AsyncMock(return_value=[])
    store.mark_succeeded = AsyncMock()
    store.mark_failed = AsyncMock()
    store.mark_exhausted = AsyncMock()
    return store


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def config():
    from fastapi_getpaid.config import GetpaidConfig

    return GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        backends={"dummy": {}},
        retry_max_attempts=3,
        retry_backoff_seconds=10,
        retry_enabled=True,
    )


def test_compute_backoff():
    """Backoff increases exponentially."""
    from fastapi_getpaid.retry import compute_next_retry_at

    base = 10
    t1 = compute_next_retry_at(attempt=1, backoff_seconds=base)
    t2 = compute_next_retry_at(attempt=2, backoff_seconds=base)
    t3 = compute_next_retry_at(attempt=3, backoff_seconds=base)

    now = datetime.now(tz=UTC)
    # Each attempt should be further in the future
    assert t1 > now
    assert t2 > t1
    assert t3 > t2


def test_compute_backoff_first_attempt():
    """First attempt backoff is base_seconds."""
    from fastapi_getpaid.retry import compute_next_retry_at

    now = datetime.now(tz=UTC)
    result = compute_next_retry_at(attempt=1, backoff_seconds=60)
    expected_min = now + timedelta(seconds=55)
    expected_max = now + timedelta(seconds=65)
    assert expected_min < result < expected_max


async def test_process_retries_empty(mock_retry_store, mock_repo, config):
    """No retries to process — does nothing."""
    from fastapi_getpaid.retry import process_due_retries

    processed = await process_due_retries(
        retry_store=mock_retry_store,
        repository=mock_repo,
        config=config,
    )
    assert processed == 0


async def test_process_retries_success(mock_retry_store, mock_repo, config):
    """Successful retry marks as succeeded."""
    from fastapi_getpaid.retry import process_due_retries

    payment = AsyncMock()
    payment.id = "pay-1"
    payment.backend = "dummy"
    mock_repo.get_by_id = AsyncMock(return_value=payment)

    mock_retry_store.get_due_retries = AsyncMock(
        return_value=[
            {
                "id": "retry-1",
                "payment_id": "pay-1",
                "payload": {"status": "paid"},
                "headers": {},
                "attempts": 1,
            }
        ]
    )

    with patch("fastapi_getpaid.retry.PaymentFlow") as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock()

        processed = await process_due_retries(
            retry_store=mock_retry_store,
            repository=mock_repo,
            config=config,
        )

    assert processed == 1
    mock_retry_store.mark_succeeded.assert_called_once_with("retry-1")


async def test_process_retries_failure_under_max(
    mock_retry_store, mock_repo, config
):
    """Failed retry under max_attempts marks as failed."""
    from fastapi_getpaid.retry import process_due_retries

    payment = AsyncMock()
    payment.id = "pay-1"
    payment.backend = "dummy"
    mock_repo.get_by_id = AsyncMock(return_value=payment)

    mock_retry_store.get_due_retries = AsyncMock(
        return_value=[
            {
                "id": "retry-1",
                "payment_id": "pay-1",
                "payload": {"status": "paid"},
                "headers": {},
                "attempts": 1,
            }
        ]
    )

    with patch("fastapi_getpaid.retry.PaymentFlow") as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock(
            side_effect=Exception("still failing")
        )

        processed = await process_due_retries(
            retry_store=mock_retry_store,
            repository=mock_repo,
            config=config,
        )

    assert processed == 1
    mock_retry_store.mark_failed.assert_called_once()


async def test_process_retries_exhausted(mock_retry_store, mock_repo, config):
    """Failed retry at max_attempts marks as exhausted."""
    from fastapi_getpaid.retry import process_due_retries

    payment = AsyncMock()
    payment.id = "pay-1"
    payment.backend = "dummy"
    mock_repo.get_by_id = AsyncMock(return_value=payment)

    # attempts == max (3) means this is the last try
    mock_retry_store.get_due_retries = AsyncMock(
        return_value=[
            {
                "id": "retry-1",
                "payment_id": "pay-1",
                "payload": {"status": "paid"},
                "headers": {},
                "attempts": 3,
            }
        ]
    )

    with patch("fastapi_getpaid.retry.PaymentFlow") as mock_flow_cls:
        instance = AsyncMock()
        mock_flow_cls.return_value = instance
        instance.handle_callback = AsyncMock(
            side_effect=Exception("still failing")
        )

        processed = await process_due_retries(
            retry_store=mock_retry_store,
            repository=mock_repo,
            config=config,
        )

    assert processed == 1
    mock_retry_store.mark_exhausted.assert_called_once_with("retry-1")
