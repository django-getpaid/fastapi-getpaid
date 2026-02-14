"""FastAPI framework adapter for getpaid payment processing."""

from typing import TYPE_CHECKING

__version__ = "0.1.0"

__all__ = [
    "CallbackRetryStore",
    "CreatePaymentRequest",
    "CreatePaymentResponse",
    "ErrorResponse",
    "FastAPIPluginRegistry",
    "GetpaidConfig",
    "OrderResolver",
    "PaymentListResponse",
    "PaymentNotFoundError",
    "PaymentResponse",
    "PaymentWithHelpers",
    "__version__",
    "create_payment_router",
]

if TYPE_CHECKING:
    from fastapi_getpaid.config import GetpaidConfig
    from fastapi_getpaid.exceptions import PaymentNotFoundError
    from fastapi_getpaid.protocols import (
        CallbackRetryStore,
        OrderResolver,
        PaymentWithHelpers,
    )
    from fastapi_getpaid.registry import FastAPIPluginRegistry
    from fastapi_getpaid.router import create_payment_router
    from fastapi_getpaid.schemas import (
        CreatePaymentRequest,
        CreatePaymentResponse,
        ErrorResponse,
        PaymentListResponse,
        PaymentResponse,
    )


def __getattr__(name: str):
    # Lazy imports to avoid loading all submodules on package import.
    if name == "GetpaidConfig":
        from fastapi_getpaid.config import GetpaidConfig

        return GetpaidConfig
    if name == "create_payment_router":
        from fastapi_getpaid.router import create_payment_router

        return create_payment_router
    if name == "FastAPIPluginRegistry":
        from fastapi_getpaid.registry import FastAPIPluginRegistry

        return FastAPIPluginRegistry
    if name == "PaymentNotFoundError":
        from fastapi_getpaid.exceptions import PaymentNotFoundError

        return PaymentNotFoundError
    if name in ("PaymentWithHelpers", "OrderResolver", "CallbackRetryStore"):
        from fastapi_getpaid import protocols

        return getattr(protocols, name)
    if name in (
        "CreatePaymentRequest",
        "CreatePaymentResponse",
        "PaymentResponse",
        "PaymentListResponse",
        "ErrorResponse",
    ):
        from fastapi_getpaid import schemas

        return getattr(schemas, name)
    raise AttributeError(f"module 'fastapi_getpaid' has no attribute {name!r}")
