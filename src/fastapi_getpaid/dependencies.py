"""FastAPI dependency providers for getpaid components."""

from fastapi import Request
from getpaid_core.flow import PaymentFlow
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.registry import FastAPIPluginRegistry


def get_config(request: Request) -> GetpaidConfig:
    """Read getpaid config from app state."""
    return request.app.state.getpaid_config


def get_repository(request: Request) -> PaymentRepository:
    """Read payment repository from app state."""
    return request.app.state.getpaid_repository


def get_registry(request: Request) -> FastAPIPluginRegistry:
    """Read plugin registry from app state."""
    return request.app.state.getpaid_registry


def get_payment_flow(request: Request) -> PaymentFlow:
    """Create a PaymentFlow with the configured repository and config."""
    config: GetpaidConfig = request.app.state.getpaid_config
    repo: PaymentRepository = request.app.state.getpaid_repository
    return PaymentFlow(
        repository=repo,
        config=config.backends,
    )
