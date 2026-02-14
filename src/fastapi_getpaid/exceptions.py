"""Exception handlers mapping getpaid-core exceptions to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from getpaid_core.exceptions import (
    CommunicationError,
    CredentialsError,
    GetPaidException,
    InvalidCallbackError,
    InvalidTransitionError,
)


class PaymentNotFoundError(Exception):
    """Payment with given ID was not found."""

    def __init__(self, payment_id: str) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment {payment_id} not found")


def register_exception_handlers(app: FastAPI) -> None:
    """Register getpaid exception handlers on a FastAPI app.

    More specific handlers must be registered first so FastAPI
    matches them before the generic GetPaidException handler.
    """

    @app.exception_handler(CommunicationError)
    async def _communication_error(
        request: Request,
        exc: CommunicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "detail": str(exc),
                "code": "communication_error",
            },
        )

    @app.exception_handler(InvalidCallbackError)
    async def _invalid_callback(
        request: Request,
        exc: InvalidCallbackError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "code": "invalid_callback",
            },
        )

    @app.exception_handler(InvalidTransitionError)
    async def _invalid_transition(
        request: Request,
        exc: InvalidTransitionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "code": "invalid_transition",
            },
        )

    @app.exception_handler(CredentialsError)
    async def _credentials_error(
        request: Request,
        exc: CredentialsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "code": "credentials_error",
            },
        )

    @app.exception_handler(PaymentNotFoundError)
    async def _not_found(
        request: Request,
        exc: PaymentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "code": "not_found",
            },
        )

    @app.exception_handler(GetPaidException)
    async def _getpaid_error(
        request: Request,
        exc: GetPaidException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "code": "payment_error",
            },
        )
