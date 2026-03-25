"""Tests for test database configuration helpers."""

import pytest


def test_get_test_database_url_defaults_to_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.database import get_test_database_url

    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    assert get_test_database_url() == "sqlite+aiosqlite:///:memory:"


def test_get_test_database_url_uses_environment_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.database import get_test_database_url

    database_url = (
        "postgresql+asyncpg://test_user:test_password@testdb:5432/test_db"
    )
    monkeypatch.setenv("TEST_DATABASE_URL", database_url)

    assert get_test_database_url() == database_url
