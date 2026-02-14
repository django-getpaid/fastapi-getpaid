"""Webhook retry mechanism with exponential backoff."""

import logging
from datetime import UTC, datetime, timedelta

from getpaid_core.flow import PaymentFlow
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.protocols import CallbackRetryStore

logger = logging.getLogger(__name__)


def compute_next_retry_at(
    attempt: int,
    backoff_seconds: int,
) -> datetime:
    """Compute the next retry time with exponential backoff.

    delay = backoff_seconds * 2^(attempt - 1)
    """
    delay = backoff_seconds * (2 ** (attempt - 1))
    return datetime.now(tz=UTC) + timedelta(seconds=delay)


async def process_due_retries(
    *,
    retry_store: CallbackRetryStore,
    repository: PaymentRepository,
    config: GetpaidConfig,
) -> int:
    """Process all due callback retries.

    Returns the number of retries processed.
    """
    retries = await retry_store.get_due_retries(limit=10)
    processed = 0

    for retry in retries:
        retry_id = retry["id"]
        payment_id = retry["payment_id"]
        payload = retry["payload"]
        headers = retry["headers"]
        attempts = retry["attempts"]

        try:
            payment = await repository.get_by_id(payment_id)
        except KeyError:
            logger.error(
                "Retry %s: payment %s not found, marking exhausted",
                retry_id,
                payment_id,
            )
            await retry_store.mark_exhausted(retry_id)
            processed += 1
            continue

        flow = PaymentFlow(
            repository=repository,
            config=config.backends,
        )

        try:
            await flow.handle_callback(
                payment=payment,
                data=payload,
                headers=headers,
            )
            await retry_store.mark_succeeded(retry_id)
            logger.info(
                "Retry %s: callback for payment %s succeeded",
                retry_id,
                payment_id,
            )
        except Exception as exc:
            if attempts >= config.retry_max_attempts:
                await retry_store.mark_exhausted(retry_id)
                logger.warning(
                    "Retry %s: exhausted after %d attempts: %s",
                    retry_id,
                    attempts,
                    exc,
                )
            else:
                await retry_store.mark_failed(
                    retry_id,
                    error=str(exc),
                )
                logger.info(
                    "Retry %s: attempt %d failed: %s",
                    retry_id,
                    attempts,
                    exc,
                )

        processed += 1

    return processed
