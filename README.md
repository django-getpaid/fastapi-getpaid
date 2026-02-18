# fastapi-getpaid

[![PyPI version](https://img.shields.io/pypi/v/fastapi-getpaid.svg)](https://pypi.org/project/fastapi-getpaid/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-getpaid.svg)](https://pypi.org/project/fastapi-getpaid/)
[![FastAPI versions](https://img.shields.io/badge/FastAPI-%3E%3D0.115.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/pypi/l/fastapi-getpaid.svg)](https://github.com/django-getpaid/fastapi-getpaid/blob/main/LICENSE)

FastAPI framework adapter for [getpaid-core](https://github.com/django-getpaid/python-getpaid-core) payment processing ecosystem.

## Features

- **Standardized API**: Unified REST endpoints for creating and managing payments across different backends.
- **OpenAPI Integration**: Automatically generated interactive documentation for all payment endpoints.
- **Dependency Injection**: Seamlessly integrates with FastAPI's dependency injection system.
- **Backend Agnostic**: Supports all `getpaid` processors (PayU, Paynow, Bitpay, Przelewy24, etc.).
- **Async First**: Fully asynchronous implementation for high performance.
- **Pluggable Persistence**: Support for SQLAlchemy (built-in) or custom repositories.
- **FSM Driven**: Reliable payment status management via Finite State Machine.

## Installation

```bash
pip install fastapi-getpaid
```

To use with SQLAlchemy:

```bash
pip install "fastapi-getpaid[sqlalchemy]"
```

## Quick Start

### 1. Configure Backends

Define your backends and general settings using `GetpaidConfig`:

```python
from fastapi_getpaid import GetpaidConfig

config = GetpaidConfig(
    default_backend="dummy",
    success_url="https://example.com/payment/success",
    failure_url="https://example.com/payment/failure",
    backends={
        "dummy": {
            "module": "getpaid_core.backends.dummy",
            "gateway": "https://example.com/paywall",
        },
        # Add real backends here
    }
)
```

### 2. Implement Order Resolver

The wrapper needs to know how to resolve your domain's order IDs:

```python
from fastapi_getpaid import OrderResolver

class MyOrderResolver(OrderResolver):
    async def resolve(self, order_id: str):
        # Fetch order from your database
        return await my_db.get_order(order_id)
```

### 3. Mount Payment Router

```python
from fastapi import FastAPI
from fastapi_getpaid import create_payment_router
from fastapi_getpaid.contrib.sqlalchemy.repository import SQLAlchemyPaymentRepository

app = FastAPI()

# Setup repository (SQLAlchemy example)
repository = SQLAlchemyPaymentRepository(session_factory)

# Create and include the router
payment_router = create_payment_router(
    config=config,
    repository=repository,
    order_resolver=MyOrderResolver(),
)

app.include_router(payment_router, prefix="/api/payments", tags=["payments"])
```

## OpenAPI Integration

Once mounted, `fastapi-getpaid` automatically adds documented endpoints to your FastAPI app. Visit `/docs` or `/redoc` to see the full API specification, including:

- `POST /api/payments/`: Initiate a new payment.
- `GET /api/payments/{payment_id}`: Check payment status.
- `POST /api/payments/callback/{payment_id}`: Standardized callback handler.

## Example Application

A comprehensive example showing multiple backends (Dummy, PayU, Paynow), SQLAlchemy integration, and a fake payment gateway simulator is available in the [example/](https://github.com/django-getpaid/fastapi-getpaid/tree/main/example) directory.

To run it:

```bash
cd example
pip install -r requirements.txt
uvicorn app:app --reload
```

## Ecosystem

`fastapi-getpaid` is part of the `getpaid` ecosystem:

- **Core**: [getpaid-core](https://github.com/django-getpaid/python-getpaid-core)
- **Other Wrappers**: [django-getpaid](https://github.com/django-getpaid/django-getpaid), [litestar-getpaid](https://github.com/django-getpaid/litestar-getpaid)
- **Supported Processors**: 
  - [getpaid-payu](https://github.com/django-getpaid/getpaid-payu)
  - [getpaid-paynow](https://github.com/django-getpaid/getpaid-paynow)
  - [getpaid-bitpay](https://github.com/django-getpaid/getpaid-bitpay)
  - [getpaid-przelewy24](https://github.com/django-getpaid/getpaid-przelewy24)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
