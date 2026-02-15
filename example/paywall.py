"""Fake payment gateway simulator (paywall).

Simulates a real payment broker for demonstration purposes:
- Register payment via REST API
- Display authorization form to the user
- Send callback to the payment system on approval/rejection
- Redirect user to success/failure URL
"""

import logging
from decimal import Decimal

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import PaywallEntry

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/paywall", tags=["paywall"])

# Will be set by the app on startup
session_factory: async_sessionmaker[AsyncSession] | None = None


def configure(sf: async_sessionmaker[AsyncSession]) -> None:
    """Set the session factory for the paywall module."""
    global session_factory  # noqa: PLW0603
    session_factory = sf


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    if session_factory is None:
        raise RuntimeError("Paywall session_factory not configured")
    return session_factory


@router.post("/register")
async def register_payment(request: Request) -> JSONResponse:
    """REST endpoint: register a payment and return the gateway URL.

    Accepts JSON body with:
        ext_id, value, currency, description, callback, success_url, failure_url
    """
    data = await request.json()
    legal_fields = {
        "ext_id",
        "value",
        "currency",
        "description",
        "callback",
        "success_url",
        "failure_url",
    }
    params = {k: v for k, v in data.items() if k in legal_fields}
    if "value" in params:
        params["value"] = Decimal(str(params["value"]))

    sf = _get_session_factory()
    async with sf() as session:
        entry = PaywallEntry(**params)
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        entry_id = entry.id

    gateway_url = (
        str(request.url_for("paywall_gateway")) + f"?pay_id={entry_id}"
    )
    return JSONResponse({"url": gateway_url})


@router.get("/gateway", response_class=HTMLResponse)
async def paywall_gateway(
    request: Request, pay_id: str | None = None
) -> HTMLResponse:
    """Display the fake gateway authorization page."""
    context: dict = {"request": request}

    if pay_id:
        sf = _get_session_factory()
        async with sf() as session:
            entry = await session.get(PaywallEntry, pay_id)
        if entry:
            context.update(
                {
                    "ext_id": entry.ext_id,
                    "value": entry.value,
                    "currency": entry.currency,
                    "description": entry.description,
                    "callback": entry.callback,
                    "success_url": entry.success_url,
                    "failure_url": entry.failure_url,
                    "message": "Presenting pre-registered payment",
                }
            )
        else:
            context["message"] = "Payment entry not found"
    else:
        context.update(
            {
                "ext_id": request.query_params.get("ext_id", ""),
                "value": request.query_params.get("value", ""),
                "currency": request.query_params.get("currency", ""),
                "description": request.query_params.get("description", ""),
                "callback": request.query_params.get("callback", ""),
                "success_url": request.query_params.get("success_url", ""),
                "failure_url": request.query_params.get("failure_url", ""),
                "message": "Presenting directly requested payment",
            }
        )

    return templates.TemplateResponse("paywall_gateway.html", context)


@router.post("/authorize", response_class=RedirectResponse)
async def paywall_authorize(
    request: Request,
    authorize_payment: str = Form(...),
    callback: str = Form(""),
    success_url: str = Form(""),
    failure_url: str = Form(""),
) -> RedirectResponse:
    """Handle the authorization form submission.

    Sends a callback to the payment system and redirects the user.
    """
    if callback:
        # Build absolute URL if callback is relative
        if callback.startswith("/"):
            callback_url = str(request.base_url).rstrip("/") + callback
        else:
            callback_url = callback

        if authorize_payment == "1":
            # Approved: send confirm_payment FSM trigger via callback
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json={"new_status": "confirm_payment"},
                )
            return RedirectResponse(url=success_url, status_code=303)
        else:
            # Rejected: send fail FSM trigger via callback
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json={"new_status": "fail"},
                )
            return RedirectResponse(url=failure_url, status_code=303)

    # No callback configured -- just redirect
    if authorize_payment == "1":
        return RedirectResponse(url=success_url or "/", status_code=303)
    return RedirectResponse(url=failure_url or "/", status_code=303)


@router.get("/status/{entry_id}")
async def paywall_status(entry_id: str) -> JSONResponse:
    """Get the status of a paywall entry."""
    sf = _get_session_factory()
    async with sf() as session:
        entry = await session.get(PaywallEntry, entry_id)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Entry not found"},
        )
    return JSONResponse(
        {
            "payment_status": entry.payment_status,
            "fraud_status": entry.fraud_status,
        }
    )
