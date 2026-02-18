"""Example FastAPI application demonstrating fastapi-getpaid.

This app provides:
- A simple order management UI (create orders, view order details)
- Payment processing via fastapi-getpaid with multiple backends
- A fake payment gateway simulator (paywall) for interactive testing

Payment flow:
1. User creates an order on the home page
2. User clicks "Pay" on the order detail page
3. The app calls the fastapi-getpaid REST API to create a payment
4. For dummy backend: payment is registered with the fake gateway (paywall)
5. User is redirected to the payment authorization page
6. User approves or rejects the payment
7. The gateway sends a callback to the fastapi-getpaid callback endpoint
8. The payment status is updated via the FSM
9. User is redirected back to the order detail page

Supported backends:
- dummy: Built-in fake processor with paywall simulator
- payu: PayU payment gateway (sandbox keys by default)
- paynow: Paynow payment gateway (sandbox keys by default)
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from decimal import Decimal

import httpx
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from getpaid_core.backends.dummy import DummyProcessor
from getpaid_core.registry import registry as global_registry

try:
    from getpaid_payu.processor import PayUProcessor

    PAYU_AVAILABLE = True
except ImportError:
    PAYU_AVAILABLE = False

try:
    from getpaid_paynow.processor import PaynowProcessor

    PAYNOW_AVAILABLE = True
except ImportError:
    PAYNOW_AVAILABLE = False

from fastapi_getpaid.config import GetpaidConfig
from fastapi_getpaid.contrib.sqlalchemy.models import Base
from fastapi_getpaid.contrib.sqlalchemy.repository import (
    SQLAlchemyPaymentRepository,
)
from fastapi_getpaid.contrib.sqlalchemy.retry_store import SQLAlchemyRetryStore
from fastapi_getpaid.router import create_payment_router

from models import Order as OrderModel
from paywall import configure as configure_paywall
from paywall import router as paywall_router

logger = logging.getLogger(__name__)

# --- Database setup ---

engine = create_async_engine(
    "sqlite+aiosqlite:///example.db",
    echo=True,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

# --- Templates ---

templates = Jinja2Templates(directory="templates")


# --- Order resolver ---


class ExampleOrderResolver:
    """Resolves order IDs to Order model instances from the database."""

    async def resolve(self, order_id: str) -> OrderModel:
        async with session_factory() as session:
            order = await session.get(OrderModel, order_id)
            if order is None:
                raise KeyError(f"Order {order_id} not found")
            session.expunge(order)
            return order


# --- Configuration ---

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

config = GetpaidConfig(
    default_backend=os.environ.get("DEFAULT_BACKEND", "dummy"),
    success_url=f"{BASE_URL}/order-success",
    failure_url=f"{BASE_URL}/order-failure",
    backends={
        "dummy": {
            "module": "getpaid_core.backends.dummy",
            "gateway": f"{BASE_URL}/paywall/gateway",
            "confirmation_method": "push",
        },
        "payu": {
            "module": "getpaid_payu.processor",
            "pos_id": os.environ.get("PAYU_POS_ID", "300746"),
            "second_key": os.environ.get(
                "PAYU_SECOND_KEY", "b6ca15b0d1020e8094d9b5f8d163db54"
            ),
            "oauth_id": os.environ.get("PAYU_OAUTH_ID", "300746"),
            "oauth_secret": os.environ.get(
                "PAYU_OAUTH_SECRET", "2ee86a66e5d97e3fadc400c9f19b065d"
            ),
            "sandbox": os.environ.get("PAYU_SANDBOX", "true").lower() == "true",
            "confirmation_method": "push",
        },
        "paynow": {
            "module": "getpaid_paynow.processor",
            "api_key": os.environ.get(
                "PAYNOW_API_KEY", "d2e1d881-40b0-4b7e-9168-181bae3dc4e0"
            ),
            "signature_key": os.environ.get(
                "PAYNOW_SIGNATURE_KEY", "8e42a868-5562-440d-817c-4921632fb049"
            ),
            "sandbox": os.environ.get("PAYNOW_SANDBOX", "true").lower()
            == "true",
            "confirmation_method": "push",
        },
    },
)

# --- Payment router ---

repository = SQLAlchemyPaymentRepository(session_factory)
retry_store = SQLAlchemyRetryStore(session_factory)

global_registry.register(DummyProcessor)

if PAYU_AVAILABLE:
    global_registry.register(PayUProcessor)
    logger.info("PayU processor registered")
else:
    logger.warning("PayU processor not available (getpaid-payu not installed)")

if PAYNOW_AVAILABLE:
    global_registry.register(PaynowProcessor)
    logger.info("Paynow processor registered")
else:
    logger.warning(
        "Paynow processor not available (getpaid-paynow not installed)"
    )

payment_router = create_payment_router(
    config=config,
    repository=repository,
    order_resolver=ExampleOrderResolver(),
    retry_store=retry_store,
)


# --- App lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    configure_paywall(session_factory)
    yield


# --- App ---

app = FastAPI(
    title="fastapi-getpaid Example",
    description="Example application with fake payment gateway simulator",
    lifespan=lifespan,
)

app.include_router(payment_router, prefix="/api")
app.include_router(paywall_router)


# --- Order management views ---


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Home page: list orders and create new ones."""
    async with session_factory() as session:
        result = await session.execute(
            select(OrderModel).order_by(OrderModel.created_at.desc())
        )
        orders = list(result.scalars().all())
        for o in orders:
            session.expunge(o)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "orders": orders,
        },
    )


@app.post("/orders/create", response_class=RedirectResponse)
async def create_order(
    request: Request,
    description: str = Form(...),
    amount: str = Form(...),
    currency: str = Form("PLN"),
) -> RedirectResponse:
    """Create a new order and redirect to its detail page."""
    async with session_factory() as session:
        order = OrderModel(
            description=description,
            amount=Decimal(amount),
            currency=currency,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        order_id = order.id

    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)


@app.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_detail(request: Request, order_id: str) -> HTMLResponse:
    """Order detail page: show order info and its payments."""
    async with session_factory() as session:
        order = await session.get(OrderModel, order_id)
        if order is None:
            return templates.TemplateResponse(
                "404.html",
                {
                    "request": request,
                    "message": "Order not found",
                },
                status_code=404,
            )
        session.expunge(order)

    # Fetch payments for this order via the repository
    payments = await repository.list_by_order(order_id)

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "payments": payments,
        },
    )


@app.post("/orders/{order_id}/pay", response_class=RedirectResponse)
async def initiate_payment(
    request: Request,
    order_id: str,
    backend: str = Form("dummy"),
) -> RedirectResponse:
    """Initiate a payment for an order.

    This demonstrates how a client application would use the
    fastapi-getpaid REST API:

    1. Call ``POST /api/payments/`` to create a payment and run
       the payment flow (create + prepare via the backend).
    2. For dummy backend: register with paywall and redirect.
       For real backends (payu/paynow): redirect to their gateway.

    In a real application, the backend selection would typically
    be done via user preference or business logic, not a form field.
    """
    async with session_factory() as session:
        order = await session.get(OrderModel, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        session.expunge(order)

    if backend not in config.backends:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid backend: {backend}. Available: {list(config.backends.keys())}",
        )

    base_url = str(request.base_url).rstrip("/")

    async with httpx.AsyncClient(base_url=base_url) as client:
        try:
            resp = await client.post(
                "/api/payments/",
                json={
                    "order_id": order_id,
                    "backend": backend,
                    "amount": str(order.amount),
                    "currency": order.currency,
                    "description": order.description,
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Payment creation failed: %s - %s",
                e.response.status_code,
                e.response.text,
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Payment creation failed: {e.response.text}",
            ) from e
        except httpx.RequestError as e:
            logger.error("Payment request error: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Payment service unavailable",
            ) from e

        payment_data = resp.json()

    payment_id = payment_data["payment_id"]

    if backend == "dummy":
        callback_url = f"{base_url}/api/callback/{payment_id}"

        async with httpx.AsyncClient(base_url=base_url) as client:
            try:
                resp = await client.post(
                    "/paywall/register",
                    json={
                        "ext_id": payment_id,
                        "value": str(order.amount),
                        "currency": order.currency,
                        "description": order.description,
                        "callback": callback_url,
                        "success_url": f"{base_url}/orders/{order_id}",
                        "failure_url": f"{base_url}/orders/{order_id}",
                    },
                )
                resp.raise_for_status()
                gateway_data = resp.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error("Paywall registration failed: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail="Payment gateway registration failed",
                ) from e

        return RedirectResponse(url=gateway_data["url"], status_code=303)
    else:
        redirect_url = payment_data.get("redirect_url")
        if not redirect_url:
            logger.error(
                "No redirect URL in payment response for backend %s: %s",
                backend,
                payment_data,
            )
            raise HTTPException(
                status_code=500,
                detail="Payment gateway did not return redirect URL",
            )

        return RedirectResponse(url=redirect_url, status_code=303)


@app.get("/order-success", response_class=HTMLResponse)
async def order_success(request: Request, payment_id: str = "") -> HTMLResponse:
    """Success landing page after payment."""
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "status": "success",
            "payment_id": payment_id,
        },
    )


@app.get("/order-failure", response_class=HTMLResponse)
async def order_failure(request: Request, payment_id: str = "") -> HTMLResponse:
    """Failure landing page after payment."""
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "status": "failure",
            "payment_id": payment_id,
        },
    )
