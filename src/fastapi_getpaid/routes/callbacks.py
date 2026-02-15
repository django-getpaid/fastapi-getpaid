"""Callback (PUSH) route handlers."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from getpaid_core.exceptions import CommunicationError, InvalidCallbackError
from getpaid_core.flow import PaymentFlow
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.dependencies import get_config, get_repository
from fastapi_getpaid.exceptions import PaymentNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["callbacks"])


@router.post("/callback/{payment_id}")
async def handle_callback(
    payment_id: str,
    request: Request,
    config: GetpaidConfig = Depends(get_config),  # noqa: B008
    repository: PaymentRepository = Depends(get_repository),  # noqa: B008
) -> JSONResponse:
    """Handle a PUSH callback from a payment gateway."""
    try:
        payment = await repository.get_by_id(payment_id)
    except (KeyError, Exception) as exc:
        if isinstance(exc, KeyError):
            raise PaymentNotFoundError(payment_id) from exc
        raise

    raw_body = await request.body()
    data = await request.json()
    headers = dict(request.headers)

    flow = PaymentFlow(
        repository=repository,
        config=config.backends,
    )

    try:
        await flow.handle_callback(
            payment=payment,
            data=data,
            headers=headers,
            raw_body=raw_body,
        )
    except InvalidCallbackError:
        raise
    except CommunicationError as exc:
        # Store for retry if retry store is available
        retry_store = getattr(request.app.state, "getpaid_retry_store", None)
        if retry_store is not None:
            retry_payload = dict(data)
            retry_payload["_raw_body"] = raw_body.decode("utf-8")
            await retry_store.store_failed_callback(
                payment_id=payment_id,
                payload=retry_payload,
                headers=headers,
            )
            logger.warning(
                "Callback for payment %s failed, queued for retry: %s",
                payment_id,
                exc,
            )
        return JSONResponse(
            status_code=502,
            content={
                "detail": f"Callback processing failed: {exc}",
                "code": "callback_failed",
            },
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
    )
