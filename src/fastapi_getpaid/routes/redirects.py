"""Success/failure redirect endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from getpaid_core.protocols import PaymentRepository

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.dependencies import get_config, get_repository
from fastapi_getpaid.exceptions import PaymentNotFoundError

router = APIRouter(tags=["redirects"])


@router.get("/success/{payment_id}")
async def success_redirect(
    payment_id: str,
    config: GetpaidConfig = Depends(get_config),  # noqa: B008
    repository: PaymentRepository = Depends(get_repository),  # noqa: B008
) -> RedirectResponse:
    """Redirect user to success URL after payment."""
    try:
        await repository.get_by_id(payment_id)
    except KeyError as exc:
        raise PaymentNotFoundError(payment_id) from exc

    url = config.success_url
    if "?" in url:
        url = f"{url}&payment_id={payment_id}"
    else:
        url = f"{url}?payment_id={payment_id}"

    return RedirectResponse(url=url)


@router.get("/failure/{payment_id}")
async def failure_redirect(
    payment_id: str,
    config: GetpaidConfig = Depends(get_config),  # noqa: B008
    repository: PaymentRepository = Depends(get_repository),  # noqa: B008
) -> RedirectResponse:
    """Redirect user to failure URL after payment."""
    try:
        await repository.get_by_id(payment_id)
    except KeyError as exc:
        raise PaymentNotFoundError(payment_id) from exc

    url = config.failure_url
    if "?" in url:
        url = f"{url}&payment_id={payment_id}"
    else:
        url = f"{url}?payment_id={payment_id}"

    return RedirectResponse(url=url)
