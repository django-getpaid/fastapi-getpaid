# fastapi-getpaid

**FastAPI framework adapter for getpaid payment processing.**

fastapi-getpaid provides a ready-made payment processing integration for
[FastAPI](https://fastapi.tiangolo.com/) applications, built on top of the
[getpaid-core](https://github.com/django-getpaid/getpaid-core) engine.

:::{note}
This project has **nothing in common** with the Plone `getpaid` plugin.
It is part of the `django-getpaid` / `getpaid` ecosystem — a modern,
framework-agnostic payment processing toolkit for Python.
:::

## Key features

- **Async-native** — fully asynchronous from routes to persistence
- **SQLAlchemy 2.0** — ready-to-use async models and repository
- **Webhook retry** — automatic callback retry with exponential backoff
- **Pydantic config** — typed configuration via `pydantic-settings` with env var support
- **Plugin registry** — discover and register payment backends at startup

## Documentation

```{toctree}
:maxdepth: 2

quickstart
configuration
api
```
