# Configuration reference

All configuration is handled through the
{class}`~fastapi_getpaid.config.GetpaidConfig` class, which extends
`pydantic_settings.BaseSettings`.

## Settings

`default_backend`
: **str** — Slug of the default payment backend to use when none is
  explicitly specified.

`success_url`
: **str** — URL the user is redirected to after a successful payment.
  The `payment_id` query parameter is appended automatically.

`failure_url`
: **str** — URL the user is redirected to after a failed payment.
  The `payment_id` query parameter is appended automatically.

`backends`
: **dict[str, dict[str, Any]]** *(default: `{}`)* — Backend-specific
  configuration keyed by backend slug. Each value is a dict of settings
  passed to the corresponding backend plugin.

`retry_enabled`
: **bool** *(default: `True`)* — Whether webhook callback retry is
  enabled.

`retry_max_attempts`
: **int** *(default: `5`)* — Maximum number of retry attempts for a
  failed webhook callback before it is marked as exhausted.

`retry_backoff_seconds`
: **int** *(default: `60`)* — Base backoff interval in seconds.
  Actual delay grows exponentially: `backoff_seconds * 2^(attempt - 1)`.

## Environment variables

Because `GetpaidConfig` uses pydantic-settings with the prefix `GETPAID_`,
every setting can be overridden via environment variables:

| Setting               | Environment variable          |
|-----------------------|-------------------------------|
| `default_backend`     | `GETPAID_DEFAULT_BACKEND`     |
| `success_url`         | `GETPAID_SUCCESS_URL`         |
| `failure_url`         | `GETPAID_FAILURE_URL`         |
| `retry_enabled`       | `GETPAID_RETRY_ENABLED`       |
| `retry_max_attempts`  | `GETPAID_RETRY_MAX_ATTEMPTS`  |
| `retry_backoff_seconds` | `GETPAID_RETRY_BACKOFF_SECONDS` |

For example:

```bash
export GETPAID_DEFAULT_BACKEND=stripe
export GETPAID_SUCCESS_URL=https://mysite.com/thank-you
export GETPAID_FAILURE_URL=https://mysite.com/payment-error
export GETPAID_RETRY_MAX_ATTEMPTS=10
```

:::{note}
The `backends` dict is typically set programmatically rather than via
environment variables, because its structure is nested. You can still use
a JSON-encoded `GETPAID_BACKENDS` variable if your deployment requires it.
:::
