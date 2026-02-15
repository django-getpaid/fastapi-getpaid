# fastapi-getpaid

[![PyPI](https://img.shields.io/pypi/v/fastapi-getpaid.svg)](https://pypi.org/project/fastapi-getpaid/)
[![Python Version](https://img.shields.io/pypi/pyversions/fastapi-getpaid)](https://pypi.org/project/fastapi-getpaid/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/pypi/l/fastapi-getpaid)](https://pypi.org/project/fastapi-getpaid/)

Multi-broker payment processing framework for FastAPI, built on
[getpaid-core](https://github.com/django-getpaid/python-getpaid-core).

> **v0.1.0 (Alpha)** — This is a pre-release. The API may change before the
> stable v1.0 release.

## Features

- Async-native from routes to persistence
- Multiple payment brokers at the same time
- Flexible plugin architecture via getpaid-core
- SQLAlchemy 2.0 async models and repository (optional)
- Webhook callback retry with exponential backoff
- Typed configuration via `pydantic-settings` with env var support
- Plugin discovery and registration at startup
- REST endpoints for payment CRUD, callbacks, and redirects

## Installation

```bash
pip install fastapi-getpaid
```

With SQLAlchemy support:

```bash
pip install fastapi-getpaid[sqlalchemy]
```

Or with uv:

```bash
uv add fastapi-getpaid
```

Then install a payment backend plugin (check that the plugin supports
getpaid-core v3 before installing):

```bash
pip install python-getpaid-payu
```

## Quick Start

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.contrib.sqlalchemy.repository import (
    SQLAlchemyPaymentRepository,
)
from fastapi_getpaid.contrib.sqlalchemy.retry_store import SQLAlchemyRetryStore
from fastapi_getpaid.router import create_payment_router

config = GetpaidConfig(
    default_backend="dummy",
    success_url="https://example.com/thank-you",
    failure_url="https://example.com/payment-failed",
    backends={
        "dummy": {"module": "getpaid_core.backends.dummy"},
    },
)

engine = create_async_engine("sqlite+aiosqlite:///payments.db")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

repository = SQLAlchemyPaymentRepository(session_factory)
retry_store = SQLAlchemyRetryStore(session_factory)

payment_router = create_payment_router(
    config=config,
    repository=repository,
    retry_store=retry_store,
)

app = FastAPI(title="My Payment Service")
app.include_router(payment_router, prefix="/api")
```

Start the server:

```bash
uvicorn myapp:app --reload
```

The payment endpoints will be available under `/api/payments/`.

See the [example app](https://github.com/django-getpaid/fastapi-getpaid/tree/main/example)
for a fully working project with a built-in payment broker simulator.

## Supported Versions

- **Python:** 3.12+
- **FastAPI:** 0.115+
- **SQLAlchemy:** 2.0+ (optional)

## Running Tests

```bash
uv sync
uv run pytest
```

Or with ruff for linting:

```bash
uv run ruff check src/ tests/
```

## Part of the getpaid ecosystem

This package is part of the **getpaid** family of libraries:

- **[python-getpaid-core](https://github.com/django-getpaid/python-getpaid-core)** — framework-agnostic payment processing core
- **[django-getpaid](https://github.com/django-getpaid/django-getpaid)** — Django integration
- **[fastapi-getpaid](https://github.com/django-getpaid/fastapi-getpaid)** — FastAPI integration (this package)

Payment gateway plugins:

- **[python-getpaid-payu](https://github.com/django-getpaid/python-getpaid-payu)** — PayU
- **[python-getpaid-paynow](https://github.com/django-getpaid/python-getpaid-paynow)** — mBank Paynow
- **[python-getpaid-przelewy24](https://github.com/django-getpaid/python-getpaid-przelewy24)** — Przelewy24

## Credits

Created by [Dominik Kozaczko](https://github.com/dekoza).

## Disclaimer

This project has nothing in common with the
[getpaid](https://code.google.com/archive/p/getpaid/) plone project.

## License

MIT
