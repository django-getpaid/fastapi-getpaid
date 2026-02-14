# API reference

## Router factory

### `create_payment_router()`

```python
from fastapi_getpaid.router import create_payment_router

create_payment_router(
    *,
    config: GetpaidConfig,
    repository: PaymentRepository,
    registry: FastAPIPluginRegistry | None = None,
    order_resolver: OrderResolver | None = None,
    retry_store: CallbackRetryStore | None = None,
) -> APIRouter
```

Creates and returns a fully configured `APIRouter` with all payment
endpoints. Accepts the configuration, a payment repository, and optional
components (plugin registry, order resolver, retry store).

## Configuration

### `GetpaidConfig`

```python
from fastapi_getpaid.config import GetpaidConfig
```

Pydantic settings model for all payment configuration. See
{doc}`configuration` for the full list of fields.

## Protocols

### `PaymentWithHelpers`

```python
from fastapi_getpaid.protocols import PaymentWithHelpers
```

Extends the core `Payment` protocol with `is_fully_paid()` and
`is_fully_refunded()` helper methods required by the FSM guards.

### `OrderResolver`

```python
from fastapi_getpaid.protocols import OrderResolver
```

Protocol for resolving an `order_id` string into an `Order` object.
Implementations must provide an async `resolve(order_id: str) -> Order`
method.

### `CallbackRetryStore`

```python
from fastapi_getpaid.protocols import CallbackRetryStore
```

Storage abstraction for the webhook retry queue. Methods:

- `store_failed_callback(payment_id, payload, headers) -> str`
- `get_due_retries(limit=10) -> list[dict]`
- `mark_succeeded(retry_id) -> None`
- `mark_failed(retry_id, error) -> None`
- `mark_exhausted(retry_id) -> None`

## Plugin registry

### `FastAPIPluginRegistry`

```python
from fastapi_getpaid.registry import FastAPIPluginRegistry
```

Wraps the core `PluginRegistry` and adds support for registering
per-backend `APIRouter` instances for custom callback routes.

## Exceptions

### `PaymentNotFoundError`

```python
from fastapi_getpaid.exceptions import PaymentNotFoundError
```

Raised when a payment lookup fails. Automatically mapped to a
`404 Not Found` HTTP response by the registered exception handlers.

## SQLAlchemy contrib

The `fastapi_getpaid.contrib.sqlalchemy` package provides ready-to-use
async models and implementations.

### `PaymentModel`

```python
from fastapi_getpaid.contrib.sqlalchemy.models import PaymentModel
```

SQLAlchemy 2.0 mapped model implementing the `PaymentWithHelpers` protocol.
Table name: `getpaid_payment`.

### `CallbackRetryModel`

```python
from fastapi_getpaid.contrib.sqlalchemy.models import CallbackRetryModel
```

SQLAlchemy model for the webhook callback retry queue.
Table name: `getpaid_callback_retry`.

### `SQLAlchemyPaymentRepository`

```python
from fastapi_getpaid.contrib.sqlalchemy.repository import (
    SQLAlchemyPaymentRepository,
)
```

Async `PaymentRepository` implementation backed by SQLAlchemy sessions.
Accepts an `async_sessionmaker` and provides `get_by_id`, `create`, `save`,
`update_status`, and `list_by_order` methods.

### `SQLAlchemyRetryStore`

```python
from fastapi_getpaid.contrib.sqlalchemy.retry_store import (
    SQLAlchemyRetryStore,
)
```

`CallbackRetryStore` implementation backed by SQLAlchemy. Handles
exponential backoff scheduling and retry lifecycle management.

## Schemas

### Request schemas

`CreatePaymentRequest`
: Fields: `order_id`, `backend`, `amount`, `currency`, `description` (optional).

### Response schemas

`CreatePaymentResponse`
: Fields: `payment_id`, `redirect_url`, `method`, `form_data`.

`PaymentResponse`
: Full payment data including amounts, status, backend, and fraud fields.

`PaymentListResponse`
: Paginated response with `items: list[PaymentResponse]` and `total: int`.

`ErrorResponse`
: Standard error body with `detail` and `code` fields.

`CallbackRetryResponse`
: Retry status with `id`, `payment_id`, `attempts`, `status`, `last_error`.

## REST endpoints

All endpoints are mounted under the prefix you pass to `include_router()`.

| Method | Path                       | Description                          |
|--------|----------------------------|--------------------------------------|
| GET    | `/payments/`               | List payments for an order (`?order_id=...`) |
| POST   | `/payments/`               | Create a new payment                 |
| GET    | `/payments/{payment_id}`   | Get a single payment by ID           |
| POST   | `/callback/{payment_id}`   | Handle a PUSH callback from a gateway |
| GET    | `/success/{payment_id}`    | Redirect to the configured success URL |
| GET    | `/failure/{payment_id}`    | Redirect to the configured failure URL |
