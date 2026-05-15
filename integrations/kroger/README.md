# Kroger Developer API Client

Pulls on-sale grocery items from Kroger (and all Kroger-family chains:
Harris Teeter, Fred Meyer, Ralphs, King Soopers, etc.) into WhollyFare
flyer JSON format.

---

## Setup (one-time, ~10 minutes)

### 1. Register for the Kroger Developer API

Go to https://developer.kroger.com and create a free account.
Create a new Application — pick "Web App" type.
You'll receive a **client_id** and **client_secret**.

### 2. Set environment variables

```bash
export KROGER_CLIENT_ID=your_client_id
export KROGER_CLIENT_SECRET=your_client_secret
```

### 3. Find your store's location ID

```python
from integrations.kroger import KrogerClient

client = KrogerClient()
stores = client.find_stores(zip_code="22963", limit=5)
for s in stores:
    print(s["locationId"], s["name"], s["address"], s["distance_mi"], "mi")
```

Copy the `locationId` of your nearest Kroger store and set it:

```bash
export KROGER_LOCATION_ID=01200441   # example
```

---

## Weekly workflow

```python
from integrations.kroger import KrogerClient

client = KrogerClient()

result = client.get_weekly_sales(
    flyer_week="2026-05-18",
    # Optionally override search terms:
    search_terms=["chicken breast", "broccoli", "brown rice", "eggs", "milk"],
)

# Enrich nutrition via USDA (optional but recommended)
from integrations.food_lion.usda_enricher import USDAEnricher
USDAEnricher().enrich(result)

# Save in the same format as any other flyer
client.save(result, "app/data/flyers/kroger_2026-05-18.json")
```

---

## Digital coupons

```python
# List available coupons (no user login required)
coupons = client.get_coupons()
for c in coupons:
    print(c["description"], f"  -${c['discount_amount']:.2f}", c["expires_on"])
```

**Clipping coupons** to a Kroger loyalty account requires the user to log
in via OAuth Authorization Code flow. This is out of scope for Phase 1
(we list what's available) but is the Phase 2/3 upgrade path:
the Kroger API fully supports it once you add the `cart.basic:write` scope
and implement the redirect flow.

---

## What the client does / doesn't do

**Does:**
- OAuth 2.0 Client Credentials (automatic token refresh, local cache)
- Product search by food category term
- Sale price detection (promo price < regular price)
- Savings % calculation
- Output in WhollyFare flyer JSON format (same schema as Food Lion parser)

**Doesn't (yet):**
- Authorization Code flow for user-level coupon clipping
- Cart push (requires `cart.basic:write` scope + user auth)
- Real-time inventory check

---

## Coverage note

The Kroger API covers all Kroger-banner stores. If your pilot households
shop at Harris Teeter, Fred Meyer, Ralphs, or King Soopers — the same
client works with those `locationId`s.
