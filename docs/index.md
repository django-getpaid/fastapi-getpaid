# fastapi-getpaid

**FastAPI framework adapter for getpaid payment processing.**

fastapi-getpaid provides a ready-made payment processing integration for
[FastAPI](https://fastapi.tiangolo.com/) applications, built on top of the
[getpaid-core](https://github.com/django-getpaid/python-getpaid-core) engine.

:::{note}
This project has **nothing in common** with the Plone `getpaid` plugin.
It is part of the `django-getpaid` / `getpaid` ecosystem — a modern,
framework-agnostic payment processing toolkit for Python.
:::

```{warning}
**v0.1.0 (Alpha)** — This is a pre-release. The API may change before the
stable v1.0 release.
```

## Key features

- **Async-native** — fully asynchronous from routes to persistence
- **Multiple brokers** — use several payment gateways simultaneously
- **SQLAlchemy 2.0** — ready-to-use async models and repository
- **Webhook retry** — automatic callback retry with exponential backoff
- **Pydantic config** — typed configuration via `pydantic-settings` with env var support
- **Plugin registry** — discover and register payment backends at startup
- **REST endpoints** — payment CRUD, callbacks, and redirect handling out of the box

## Documentation

```{toctree}
:maxdepth: 2

quickstart
configuration
api
changelog
contributing
license
```
