"""Tests for the public API surface."""


def test_version():
    """Package exposes version."""
    from fastapi_getpaid import __version__

    assert __version__ == "0.1.0"


def test_create_payment_router_importable():
    """Main factory function is importable from package root."""
    from fastapi_getpaid import create_payment_router

    assert callable(create_payment_router)


def test_config_importable():
    """Config class is importable from package root."""
    from fastapi_getpaid import GetpaidConfig

    assert GetpaidConfig is not None


def test_schemas_importable():
    """Key schemas are importable from package root."""
    from fastapi_getpaid import (
        CreatePaymentRequest,
        CreatePaymentResponse,
        ErrorResponse,
        PaymentListResponse,
        PaymentResponse,
    )

    assert all(
        [
            CreatePaymentRequest,
            CreatePaymentResponse,
            PaymentResponse,
            PaymentListResponse,
            ErrorResponse,
        ]
    )


def test_protocols_importable():
    """Protocols are importable from package root."""
    from fastapi_getpaid import (
        CallbackRetryStore,
        OrderResolver,
        PaymentWithHelpers,
    )

    assert all([PaymentWithHelpers, OrderResolver, CallbackRetryStore])


def test_registry_importable():
    """Registry is importable from package root."""
    from fastapi_getpaid import FastAPIPluginRegistry

    assert FastAPIPluginRegistry is not None


def test_exception_importable():
    """Custom exception is importable."""
    from fastapi_getpaid import PaymentNotFoundError

    assert PaymentNotFoundError is not None
