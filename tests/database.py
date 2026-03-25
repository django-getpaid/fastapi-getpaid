"""Shared test database helpers."""

from __future__ import annotations

import os


DEFAULT_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def get_test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
