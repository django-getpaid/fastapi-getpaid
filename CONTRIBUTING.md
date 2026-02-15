# Contributor Guide

Thank you for your interest in improving fastapi-getpaid.
This project is open-source under the [MIT license](https://github.com/django-getpaid/fastapi-getpaid/blob/main/LICENSE) and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

## Resources

- [Source Code](https://github.com/django-getpaid/fastapi-getpaid)
- [Documentation](https://fastapi-getpaid.readthedocs.io/)
- [Issue Tracker](https://github.com/django-getpaid/fastapi-getpaid/issues)

## How to report a bug

Report bugs on the [Issue Tracker](https://github.com/django-getpaid/fastapi-getpaid/issues).

When filing an issue, include:

- Operating system and Python version
- fastapi-getpaid version
- FastAPI and SQLAlchemy versions (if relevant)
- Steps to reproduce
- Expected vs actual behavior

## How to set up your development environment

You need Python 3.12+ and [uv](https://docs.astral.sh/uv/).

Clone and install:

```bash
git clone https://github.com/django-getpaid/fastapi-getpaid.git
cd fastapi-getpaid
uv sync
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

## How to submit changes

1. Fork the repository and create a feature branch
2. Write tests for your changes
3. Ensure all tests pass: `uv run pytest`
4. Ensure linting passes: `uv run ruff check src/ tests/`
5. Open a pull request

Your pull request needs to:

- Pass the test suite without errors
- Include tests for new functionality
- Update documentation if adding features
