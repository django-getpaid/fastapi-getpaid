## Example Project for fastapi-getpaid

This example demonstrates the full payment processing lifecycle using
fastapi-getpaid with a built-in **fake payment gateway simulator** (paywall).

You can create orders, initiate payments, approve or reject them at the
simulated gateway, and see the callback-driven status updates — all without
needing a real payment provider.

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Running the example

1. Navigate to the `example` directory:

        cd example

2. Install dependencies:

        uv sync

3. Start the server:

        uv run uvicorn app:app --reload

4. Open `http://127.0.0.1:8000` in your browser.

### What the example does

1. **Home page** — create a new order with an amount and description.
2. **Order detail** — view the order and initiate a payment using the
   dummy backend.
3. **Fake gateway** — the paywall simulator presents an authorization
   page where you can approve or reject the payment.
4. **Callback** — on approval/rejection the simulator sends a callback
   to the payment endpoint, updating the payment status.
5. **Result** — you are redirected back to the order page showing the
   updated payment status.

### Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  Browser UI  │────▶│  FastAPI app       │────▶│  Paywall         │
│  (Jinja2)    │◀────│  (payment routes)  │◀────│  (fake gateway)  │
└──────────────┘     └───────────────────┘     └──────────────────┘
                              │
                     ┌────────┴────────┐
                     │  SQLite + SQLAlchemy  │
                     │  (orders & payments)  │
                     └─────────────────────┘
```
