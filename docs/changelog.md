# Changelog

## 3.0.0a4 (2026-03-25)

- Restore persisted order hydration and normalize router error responses.
- Add Docker-backed integration coverage and CI execution.

## 0.1.0 (2026-02-14)

Initial alpha release.

### Features

- `GetpaidConfig` — Pydantic settings model with `GETPAID_` env prefix
- `create_payment_router()` — factory producing a fully configured `APIRouter`
- REST endpoints: create payment, get payment, list payments, handle callback,
  success/failure redirects
- `Payment` protocol re-export from core for wrapper integrations
- `OrderResolver` protocol for pluggable order lookup
- `CallbackRetryStore` protocol for webhook retry persistence
- `FastAPIPluginRegistry` wrapping the core registry for FastAPI adapter usage
- Exception handlers mapping getpaid-core exceptions to HTTP responses
- Pydantic request/response schemas for all endpoints
- `fastapi_getpaid.contrib.sqlalchemy` package:
  - `PaymentModel` — SQLAlchemy 2.0 async mapped model
  - `CallbackRetryModel` — webhook retry queue model
  - `SQLAlchemyPaymentRepository` — async repository implementation
  - `SQLAlchemyRetryStore` — async retry store implementation
- Example application with fake payment gateway simulator
