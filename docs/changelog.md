# Changelog

## 0.1.0 (2026-02-14)

Initial alpha release.

### Features

- `GetpaidConfig` — Pydantic settings model with `GETPAID_` env prefix
- `create_payment_router()` — factory producing a fully configured `APIRouter`
- REST endpoints: create payment, get payment, list payments, handle callback,
  success/failure redirects
- `PaymentWithHelpers` protocol extending core `Payment` with FSM guards
- `OrderResolver` protocol for pluggable order lookup
- `CallbackRetryStore` protocol for webhook retry persistence
- `FastAPIPluginRegistry` wrapping core registry with per-backend router support
- Exception handlers mapping getpaid-core exceptions to HTTP responses
- Pydantic request/response schemas for all endpoints
- `fastapi_getpaid.contrib.sqlalchemy` package:
  - `PaymentModel` — SQLAlchemy 2.0 async mapped model
  - `CallbackRetryModel` — webhook retry queue model
  - `SQLAlchemyPaymentRepository` — async repository implementation
  - `SQLAlchemyRetryStore` — async retry store implementation
- Example application with fake payment gateway simulator
