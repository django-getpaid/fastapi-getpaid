# fastapi-getpaid

FastAPI framework adapter for getpaid payment processing.

> **Note:** This project has nothing in common with the `getpaid` Plone plugin.

## Overview

`fastapi-getpaid` provides a FastAPI integration for the
[getpaid](https://github.com/django-getpaid) payment processing ecosystem.
It builds on top of `python-getpaid-core` to offer a clean, async-first
payment processing experience within FastAPI applications.

## Installation

```bash
pip install fastapi-getpaid
```

With SQLAlchemy support:

```bash
pip install fastapi-getpaid[sqlalchemy]
```

For development:

```bash
pip install fastapi-getpaid[dev]
```

## Part of the getpaid ecosystem

This package is part of the **getpaid** family of libraries:

- **python-getpaid-core** — framework-agnostic payment processing core
- **django-getpaid** — Django integration
- **fastapi-getpaid** — FastAPI integration (this package)

## License

MIT
