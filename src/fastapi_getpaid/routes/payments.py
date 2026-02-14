"""Payment CRUD REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from getpaid_core.flow import PaymentFlow
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.dependencies import get_config, get_repository
from fastapi_getpaid.exceptions import PaymentNotFoundError
from fastapi_getpaid.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentListResponse,
    PaymentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


def _payment_to_response(payment: Any) -> PaymentResponse:
    """Convert a Payment protocol object to a response schema."""
    return PaymentResponse(
        id=str(payment.id),
        order_id=str(
            getattr(payment, "order_id", "") or getattr(payment.order, "id", "")
        ),
        amount_required=payment.amount_required,
        currency=payment.currency,
        status=payment.status,
        backend=payment.backend,
        external_id=payment.external_id,
        description=payment.description,
        amount_paid=payment.amount_paid,
        amount_locked=payment.amount_locked,
        amount_refunded=payment.amount_refunded,
        fraud_status=payment.fraud_status,
        fraud_message=payment.fraud_message,
    )


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    repository: PaymentRepository = Depends(get_repository),
) -> PaymentResponse:
    """Get a single payment by ID."""
    try:
        payment = await repository.get_by_id(payment_id)
    except KeyError as exc:
        raise PaymentNotFoundError(payment_id) from exc
    return _payment_to_response(payment)


@router.get("/")
async def list_payments(
    order_id: str = Query(..., description="Filter by order ID"),
    repository: PaymentRepository = Depends(get_repository),
) -> PaymentListResponse:
    """List payments for an order."""
    payments = await repository.list_by_order(order_id)
    items = [_payment_to_response(p) for p in payments]
    return PaymentListResponse(items=items, total=len(items))


@router.post("/", status_code=201)
async def create_payment(
    body: CreatePaymentRequest,
    request: Request,
    config: GetpaidConfig = Depends(get_config),
    repository: PaymentRepository = Depends(get_repository),
) -> CreatePaymentResponse:
    """Create a new payment and prepare it for processing."""
    order_resolver = getattr(request.app.state, "getpaid_order_resolver", None)
    if order_resolver is None:
        return JSONResponse(  # type: ignore[return-value]
            status_code=500,
            content={
                "detail": "No order resolver configured",
                "code": "configuration_error",
            },
        )

    order = await order_resolver.resolve(body.order_id)

    flow = PaymentFlow(
        repository=repository,
        config=config.backends,
    )

    payment = await flow.create_payment(
        order=order,
        backend_slug=body.backend,
        amount=body.amount,
        currency=body.currency,
        description=body.description,
    )

    result = await flow.prepare(payment)

    return CreatePaymentResponse(
        payment_id=str(payment.id),
        redirect_url=result.get("redirect_url"),
        method=result.get("method", "GET"),
        form_data=result.get("form_data"),
    )
