"""Configuration for fastapi-getpaid using Pydantic Settings."""

from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class GetpaidConfig(BaseSettings):
    """Payment processing configuration.

    Reads from environment variables with GETPAID_ prefix.
    """

    model_config = SettingsConfigDict(env_prefix="GETPAID_")

    default_backend: str
    success_url: str
    failure_url: str

    backends: dict[str, dict[str, Any]] = {}

    # Retry settings
    retry_max_attempts: int = 5
    retry_backoff_seconds: int = 60
    retry_enabled: bool = True
