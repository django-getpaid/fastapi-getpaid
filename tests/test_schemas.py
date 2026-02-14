from decimal import Decimal


def test_create_payment_request_valid():
    """CreatePaymentRequest accepts valid data."""
    from fastapi_getpaid.schemas import CreatePaymentRequest

    req = CreatePaymentRequest(
        order_id="order-123",
        backend="paynow",
        amount=Decimal("99.99"),
        currency="PLN",
        description="Test payment",
    )
    assert req.order_id == "order-123"
    assert req.backend == "paynow"
    assert req.amount == Decimal("99.99")


def test_create_payment_request_optional_fields():
    """CreatePaymentRequest has optional description."""
    from fastapi_getpaid.schemas import CreatePaymentRequest

    req = CreatePaymentRequest(
        order_id="order-1",
        backend="dummy",
        amount=Decimal("10.00"),
        currency="PLN",
    )
    assert req.description is None


def test_payment_response_serialization():
    """PaymentResponse serializes correctly."""
    from fastapi_getpaid.schemas import PaymentResponse

    resp = PaymentResponse(
        id="pay-1",
        order_id="order-1",
        amount_required=Decimal("100.00"),
        currency="PLN",
        status="new",
        backend="dummy",
        external_id=None,
        description="Test",
        amount_paid=Decimal("0"),
        amount_locked=Decimal("0"),
        amount_refunded=Decimal("0"),
        fraud_status=None,
        fraud_message=None,
    )
    data = resp.model_dump()
    assert data["id"] == "pay-1"
    assert data["status"] == "new"


def test_create_payment_response():
    """CreatePaymentResponse includes redirect info."""
    from fastapi_getpaid.schemas import CreatePaymentResponse

    resp = CreatePaymentResponse(
        payment_id="pay-1",
        redirect_url="https://gateway.example.com/pay",
        method="GET",
        form_data=None,
    )
    assert resp.redirect_url == "https://gateway.example.com/pay"
    assert resp.method == "GET"


def test_error_response():
    """ErrorResponse has detail and code."""
    from fastapi_getpaid.schemas import ErrorResponse

    err = ErrorResponse(detail="Not found", code="not_found")
    assert err.detail == "Not found"
    assert err.code == "not_found"


def test_payment_list_response():
    """PaymentListResponse wraps a list of payments with pagination."""
    from fastapi_getpaid.schemas import PaymentListResponse, PaymentResponse

    payments = [
        PaymentResponse(
            id="p1",
            order_id="o1",
            amount_required=Decimal("10"),
            currency="PLN",
            status="new",
            backend="dummy",
            external_id=None,
            description=None,
            amount_paid=Decimal("0"),
            amount_locked=Decimal("0"),
            amount_refunded=Decimal("0"),
            fraud_status=None,
            fraud_message=None,
        )
    ]
    resp = PaymentListResponse(items=payments, total=1)
    assert resp.total == 1
    assert len(resp.items) == 1


def test_callback_retry_response():
    """CallbackRetryResponse has retry metadata."""
    from fastapi_getpaid.schemas import CallbackRetryResponse

    resp = CallbackRetryResponse(
        id="retry-1",
        payment_id="pay-1",
        attempts=3,
        status="pending",
        last_error="Connection timeout",
    )
    assert resp.attempts == 3
    assert resp.status == "pending"
