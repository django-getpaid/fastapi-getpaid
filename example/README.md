## Example Project for fastapi-getpaid

This example demonstrates the full payment processing lifecycle using
fastapi-getpaid with **multiple payment backends** and a built-in
**fake payment gateway simulator** (paywall).

You can create orders, initiate payments with different backends
(Dummy, PayU, Paynow), approve or reject them at the simulated gateway,
and see the callback-driven status updates — all without needing real
payment provider credentials.

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Running the example

1. Navigate to the `example` directory:

        cd example

2. Install dependencies:

        uv sync

3. Start the server:

        uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000

4. Open `http://127.0.0.1:8000` in your browser.

### What the example does

1. **Home page** — create a new order with an amount and description.
2. **Order detail** — view the order and select a payment backend
   (dummy, payu, or paynow) to initiate payment.
3. **Payment flow** — for dummy backend, you're redirected to the
   paywall simulator; for real backends (payu/paynow), you would be
   redirected to their sandbox environments.
4. **Callback** — on approval/rejection the gateway sends a callback
   to the payment endpoint, updating the payment status.
5. **Result** — you are redirected back to the order page showing the
   updated payment status.

### Supported Backends

#### Dummy (Built-in Simulator)
- **Purpose**: Interactive testing without external dependencies
- **Gateway**: Built-in paywall simulator at `/paywall/gateway`
- **Configuration**: No credentials needed
- **Flow**: Create order → Pay → Approve/Reject at paywall → See result

#### PayU (Sandbox)
- **Purpose**: Integration testing with PayU sandbox
- **Gateway**: `https://secure.snd.payu.com/`
- **Configuration**: Uses PLN sandbox keys by default
- **Environment Variables**:
  - `PAYU_POS_ID` (default: `300746`)
  - `PAYU_SECOND_KEY` (default: `b6ca15b0d1020e8094d9b5f8d163db54`)
  - `PAYU_OAUTH_ID` (default: `300746`)
  - `PAYU_OAUTH_SECRET` (default: `2ee86a66e5d97e3fadc400c9f19b065d`)
  - `PAYU_SANDBOX` (default: `true`)

#### Paynow (Sandbox)
- **Purpose**: Integration testing with Paynow sandbox
- **Gateway**: `https://api.sandbox.paynow.pl`
- **Configuration**: Uses sandbox keys by default
- **Environment Variables**:
  - `PAYNOW_API_KEY` (default: `d2e1d881-40b0-4b7e-9168-181bae3dc4e0`)
  - `PAYNOW_SIGNATURE_KEY` (default: `8e42a868-5562-440d-817c-4921632fb049`)
  - `PAYNOW_SANDBOX` (default: `true`)

### Configuration

The example uses environment variables for configuration with sensible
defaults for local development:

- `BASE_URL` — Application base URL (default: `http://127.0.0.1:8000`)
- `DEFAULT_BACKEND` — Default payment backend (default: `dummy`)

For production use, override these with your real credentials:

```bash
export BASE_URL=https://your-domain.com
export DEFAULT_BACKEND=payu
export PAYU_POS_ID=your_pos_id
export PAYU_SECOND_KEY=your_second_key
export PAYU_OAUTH_ID=your_oauth_id
export PAYU_OAUTH_SECRET=your_oauth_secret
export PAYU_SANDBOX=false
```

### OpenAPI Documentation

The example includes auto-generated API documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

The payment API endpoints are documented under the `/api` prefix.

### Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  Browser UI  │────▶│  FastAPI app       │────▶│  Payment Gateway │
│  (Jinja2)    │◀────│  (payment routes)  │◀────│  (dummy/payu/    │
└──────────────┘     └───────────────────┘     │   paynow)        │
                              │                 └──────────────────┘
                     ┌────────┴────────┐
                     │  SQLite + SQLAlchemy  │
                     │  (orders & payments)  │
                     └─────────────────────┘
```

### Testing Different Backends

#### Testing with Dummy Backend
1. Create an order
2. Select "Dummy (Fake Gateway)" backend
3. Click "Pay"
4. At the paywall, click "Approve" or "Reject"
5. See the payment status update

#### Testing with PayU/Paynow (Sandbox)
1. Create an order
2. Select "PayU (Sandbox)" or "Paynow (Sandbox)"
3. Click "Pay"
4. You'll be redirected to the real sandbox environment
5. Complete the payment flow there
6. Return to see the status update

**Note**: PayU and Paynow sandbox testing requires valid sandbox
credentials. The defaults work for demonstration but may have
limited functionality without proper sandbox account setup.

### Error Handling

The example demonstrates proper error handling:

- **Invalid backend**: Returns HTTP 400 with available backends
- **Payment creation failure**: Returns HTTP error with details
- **Missing order**: Returns HTTP 404
- **Gateway communication failure**: Returns HTTP 500 with message

All errors are logged for debugging.
