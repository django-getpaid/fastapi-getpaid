import pytest
from pydantic import ValidationError


def test_config_with_all_fields():
    """Config accepts all fields."""
    from fastapi_getpaid.config import GetpaidConfig

    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/success",
        failure_url="/failure",
        backends={"dummy": {"api_key": "test"}},
    )
    assert config.default_backend == "dummy"
    assert config.success_url == "/success"
    assert config.failure_url == "/failure"
    assert config.backends == {"dummy": {"api_key": "test"}}


def test_config_defaults():
    """Config has sensible defaults."""
    from fastapi_getpaid.config import GetpaidConfig

    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
    )
    assert config.backends == {}
    assert config.retry_max_attempts == 5
    assert config.retry_backoff_seconds == 60
    assert config.retry_enabled is True


def test_config_missing_required_fields():
    """Config requires default_backend, success_url, failure_url."""
    from fastapi_getpaid.config import GetpaidConfig

    with pytest.raises(ValidationError):
        GetpaidConfig()  # type: ignore[call-arg]


def test_config_env_prefix(monkeypatch: pytest.MonkeyPatch):
    """Config reads from GETPAID_ env vars."""
    from fastapi_getpaid.config import GetpaidConfig

    monkeypatch.setenv("GETPAID_DEFAULT_BACKEND", "paynow")
    monkeypatch.setenv("GETPAID_SUCCESS_URL", "/ok")
    monkeypatch.setenv("GETPAID_FAILURE_URL", "/fail")
    config = GetpaidConfig()  # type: ignore[call-arg]
    assert config.default_backend == "paynow"


def test_config_retry_disabled():
    """Retry can be disabled."""
    from fastapi_getpaid.config import GetpaidConfig

    config = GetpaidConfig(
        default_backend="dummy",
        success_url="/ok",
        failure_url="/fail",
        retry_enabled=False,
    )
    assert config.retry_enabled is False
