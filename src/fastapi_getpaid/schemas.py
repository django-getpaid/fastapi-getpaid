"""Pydantic request/response schemas for fastapi-getpaid."""

from decimal import Decimal

from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    """Request to create a new payment."""

    order_id: str
    backend: str


class PaymentResponse(BaseModel):
    """Payment data response."""

    id: str
    order_id: str
    amount_required: Decimal
    currency: str
    status: str
    backend: str
    external_id: str | None
    description: str | None
    amount_paid: Decimal
    amount_locked: Decimal
    amount_refunded: Decimal
    fraud_status: str | None
    fraud_message: str | None


class CreatePaymentResponse(BaseModel):
    """Response after creating a payment, includes redirect info."""

    payment_id: str
    redirect_url: str | None
    method: str
    form_data: dict | None = None


class PaymentListResponse(BaseModel):
    """Paginated list of payments."""

    items: list[PaymentResponse]
    total: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: str


class CallbackRetryResponse(BaseModel):
    """Callback retry status response."""

    id: str
    payment_id: str
    attempts: int
    status: str
    last_error: str | None = None
