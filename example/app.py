"""Example FastAPI application demonstrating fastapi-getpaid.

This app provides:
- A simple order management UI (create orders, view order details)
- Payment processing via fastapi-getpaid with the dummy backend
- A fake payment gateway simulator (paywall) for interactive testing

Payment flow:
1. User creates an order on the home page
2. User clicks "Pay" on the order detail page
3. The app calls the fastapi-getpaid REST API to create a payment
4. The app registers the payment with the fake gateway (paywall)
5. User is redirected to the paywall authorization page
6. User approves or rejects the payment
7. The paywall sends a callback to the fastapi-getpaid callback endpoint
8. The payment status is updated via the FSM
9. User is redirected back to the order detail page
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from decimal import Decimal

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from getpaid_core.backends.dummy import DummyProcessor
from getpaid_core.registry import registry as global_registry

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

# The dummy backend is used for demonstration. In a real app you would
# configure a real payment gateway backend (e.g. PayU, Przelewy24).
config = GetpaidConfig(
    default_backend="dummy",
    success_url="http://127.0.0.1:8000/order-success",
    failure_url="http://127.0.0.1:8000/order-failure",
    backends={
        "dummy": {
            "module": "getpaid_core.backends.dummy",
            "gateway": "http://127.0.0.1:8000/paywall/gateway",
            "confirmation_method": "push",
        },
    },
)

# --- Payment router ---

repository = SQLAlchemyPaymentRepository(session_factory)
retry_store = SQLAlchemyRetryStore(session_factory)

# Manually register the dummy backend since it is not installed
# as a separate package with entry_points. The global registry
# is used by PaymentFlow internally.
global_registry.register(DummyProcessor)

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
) -> RedirectResponse:
    """Initiate a payment for an order.

    This demonstrates how a client application would use the
    fastapi-getpaid REST API:

    1. Call ``POST /api/payments/`` to create a payment and run
       the payment flow (create + prepare via the backend).
    2. The dummy backend returns a placeholder redirect URL, so
       we register the payment with the fake gateway (paywall)
       and redirect the user there.

    In a real application with a real payment backend, step 2
    would not be needed -- the redirect URL from ``prepare``
    would point to the actual payment gateway.
    """
    async with session_factory() as session:
        order = await session.get(OrderModel, order_id)
        if order is None:
            return RedirectResponse(url="/", status_code=303)
        session.expunge(order)

    # Step 1: Create payment via the library's REST API.
    # This runs PaymentFlow.create_payment() + PaymentFlow.prepare()
    # which transitions the payment to "prepared" via the FSM.
    base_url = str(request.base_url).rstrip("/")
    async with httpx.AsyncClient(base_url=base_url) as client:
        resp = await client.post(
            "/api/payments/",
            json={
                "order_id": order_id,
                "backend": "dummy",
                "amount": str(order.amount),
                "currency": order.currency,
                "description": order.description,
            },
        )
        if resp.status_code != 201:
            return RedirectResponse(url=f"/orders/{order_id}", status_code=303)
        payment_data = resp.json()

    payment_id = payment_data["payment_id"]

    # Step 2: Register with the paywall (fake gateway simulator).
    # The callback URL points to the library's callback endpoint
    # which runs PaymentFlow.handle_callback() and updates the
    # payment status via the FSM.
    callback_url = f"{base_url}/api/callback/{payment_id}"

    async with httpx.AsyncClient(base_url=base_url) as client:
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
        gateway_data = resp.json()

    # Redirect user to the fake gateway authorization page
    return RedirectResponse(url=gateway_data["url"], status_code=303)


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
