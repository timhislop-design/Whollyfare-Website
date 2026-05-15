"""
client.py — Kroger Developer API Client
-----------------------------------------
Wraps the Kroger Developer API (developer.kroger.com) for WhollyFare.

Handles:
  - OAuth 2.0 Client Credentials flow (app-level, no user login required)
  - Product search with price data
  - Store location lookup
  - Digital coupon listing (requires user-level OAuth — see note below)
  - Output as WhollyFare FlyerResult (same format as Food Lion parser)

OAuth note:
  Product search + pricing uses the Client Credentials grant (just your
  client_id and client_secret — no household login required).
  Digital coupon CLIPPING requires Authorization Code flow (user logs in
  with their Kroger account). This client supports both; coupon listing
  is available under Client Credentials, clipping requires user tokens.

Setup:
  1. Register at https://developer.kroger.com — it's free.
  2. Create an application to get client_id and client_secret.
  3. Set environment variables:
       export KROGER_CLIENT_ID=your_client_id
       export KROGER_CLIENT_SECRET=your_client_secret
       export KROGER_LOCATION_ID=your_nearest_store_id  (optional, improves pricing)

Usage:
    from integrations.kroger import KrogerClient

    client = KrogerClient()

    # Find your nearest store
    stores = client.find_stores(zip_code="22963", limit=5)

    # Pull this week's sale items as a FlyerResult
    result = client.get_weekly_sales(
        location_id="01200441",    # your store's location ID
        flyer_week="2026-05-18",
        search_terms=["chicken", "ground beef", "broccoli", "eggs", "milk"]
    )
    # Save it like any other flyer
    from integrations.food_lion.parser import FoodLionParser
    FoodLionParser().save(result, "app/data/flyers/kroger_2026-05-18.json")
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
from urllib import request, parse, error

from integrations.food_lion.item_registry import lookup  # shared registry

logger = logging.getLogger(__name__)

_KROGER_BASE = "https://api.kroger.com/v1"
_TOKEN_URL   = "https://api.kroger.com/v1/connect/oauth2/token"


# ── Dataclass-lite for results (mirrors FlyerResult shape) ───────────────────

class FlyerResult:
    """Thin result container — same shape as food_lion.parser.FlyerResult."""

    def __init__(self, grocer: str, store_location: str, flyer_week: str):
        self.grocer = grocer
        self.store_location = store_location
        self.flyer_week = flyer_week
        self.parse_metadata: dict = {}
        self.items: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "grocer": self.grocer,
            "store_location": self.store_location,
            "flyer_week": self.flyer_week,
            "parse_metadata": self.parse_metadata,
            "items": self.items,
        }


class KrogerClient:
    """
    Client for the Kroger Developer API.

    Parameters
    ----------
    client_id : str | None
        Kroger API client_id. Falls back to KROGER_CLIENT_ID env var.
    client_secret : str | None
        Kroger API client_secret. Falls back to KROGER_CLIENT_SECRET env var.
    location_id : str | None
        Preferred store location ID. Falls back to KROGER_LOCATION_ID env var.
        If not set, pricing may be regional rather than store-specific.
    token_cache_path : Path | None
        Where to cache the access token between runs (avoids re-fetching).
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        location_id: str | None = None,
        token_cache_path: Path | None = Path(__file__).parent / ".kroger_token.json",
    ):
        self.client_id     = client_id or os.environ.get("KROGER_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("KROGER_CLIENT_SECRET", "")
        self.location_id   = location_id or os.environ.get("KROGER_LOCATION_ID", "")
        self.token_cache   = token_cache_path
        self._access_token: str = ""
        self._token_expiry: float = 0.0

        if not self.client_id or not self.client_secret:
            logger.warning(
                "Kroger API credentials not set. Set KROGER_CLIENT_ID and "
                "KROGER_CLIENT_SECRET environment variables. "
                "Register free at https://developer.kroger.com"
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def find_stores(
        self,
        zip_code: str,
        radius_miles: int = 10,
        limit: int = 5,
    ) -> list[dict]:
        """
        Return stores near a zip code.
        Result fields: locationId, name, address, distance.
        """
        params = {
            "filter.zipCode.near": zip_code,
            "filter.radiusInMiles": radius_miles,
            "filter.limit": limit,
        }
        data = self._get("/locations", params)
        locations = data.get("data", [])
        results = []
        for loc in locations:
            addr = loc.get("address", {})
            results.append({
                "locationId":   loc.get("locationId", ""),
                "name":         loc.get("name", ""),
                "address":      f"{addr.get('addressLine1', '')}, {addr.get('city', '')}, {addr.get('state', '')}",
                "distance_mi":  round(loc.get("geolocation", {}).get("distanceInMiles", 0), 1),
                "chain":        loc.get("chain", "Kroger"),
            })
        return results

    def get_weekly_sales(
        self,
        location_id: str | None = None,
        flyer_week: str | date | None = None,
        search_terms: list[str] | None = None,
        min_savings_pct: float = 5.0,
    ) -> FlyerResult:
        """
        Retrieve on-sale grocery items from Kroger for a given store.

        Kroger's API doesn't expose a "weekly ad" endpoint directly — instead
        we query the product search for each search term and filter to items
        with an active promotion price lower than the regular price.

        Parameters
        ----------
        location_id : str | None
            Kroger store location ID. Overrides the instance default.
        flyer_week : str | date | None
            Label for the output JSON. Defaults to next Sunday.
        search_terms : list[str] | None
            Food categories/items to search. Defaults to WhollyFare's core
            grocery staples. Extend this list to broaden coverage.
        min_savings_pct : float
            Minimum % off regular price to include an item (filters noise).
        """
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError(
                "location_id is required. Find yours with find_stores(zip_code=...)."
            )

        if isinstance(flyer_week, date):
            flyer_week = flyer_week.isoformat()
        flyer_week = flyer_week or self._next_sunday()

        if search_terms is None:
            search_terms = _DEFAULT_SEARCH_TERMS

        result = FlyerResult(
            grocer="Kroger",
            store_location=loc_id,
            flyer_week=flyer_week,
        )

        seen_upcs: set[str] = set()
        api_calls = 0
        total_found = 0

        for term in search_terms:
            products = self._search_products(term, loc_id)
            api_calls += 1
            for product in products:
                item = self._product_to_item(product, min_savings_pct)
                if item is None:
                    continue
                upc = item.get("upc", item["name"])
                if upc in seen_upcs:
                    continue
                seen_upcs.add(upc)
                total_found += 1
                result.items.append(item)
            time.sleep(0.2)  # stay well under rate limits

        result.parse_metadata = {
            "source": "Kroger Developer API",
            "location_id": loc_id,
            "search_terms": search_terms,
            "api_calls": api_calls,
            "total_items": total_found,
            "min_savings_pct_filter": min_savings_pct,
            "pulled_at": datetime.utcnow().isoformat() + "Z",
        }
        logger.info(f"Kroger: {total_found} sale items from {api_calls} queries.")
        return result

    def get_coupons(
        self,
        location_id: str | None = None,
        categories: list[str] | None = None,
    ) -> list[dict]:
        """
        Retrieve available digital coupons.

        Returns a list of dicts with fields:
          upc, description, discount_amount, expires_on, clippable

        Note: listing coupons works under Client Credentials (this client).
        Clipping them to a Kroger account requires Authorization Code flow
        (the user must log in). See README for the user-auth flow.
        """
        loc_id = location_id or self.location_id
        params: dict = {"filter.limit": 50}
        if loc_id:
            params["filter.locationId"] = loc_id
        if categories:
            params["filter.categories"] = ",".join(categories)

        try:
            data = self._get("/coupons", params)
        except Exception as e:
            logger.warning(f"Coupon fetch failed: {e}")
            return []

        coupons = []
        for c in data.get("data", []):
            coupons.append({
                "upc":             c.get("upc", ""),
                "description":     c.get("description", ""),
                "discount_amount": c.get("discountAmount", 0.0),
                "expires_on":      c.get("expirationDate", ""),
                "clippable":       True,  # all listed coupons are clippable
            })
        return coupons

    def save(self, result: FlyerResult, output_path: str | Path) -> Path:
        """Save FlyerResult to JSON (same interface as FoodLionParser.save)."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Saved Kroger flyer JSON → {output_path}")
        return output_path

    # ── OAuth 2.0 ─────────────────────────────────────────────────────────────

    def _ensure_token(self):
        """Ensure we have a valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return  # token still valid

        # Try loading from cache file
        if self.token_cache and self.token_cache.exists():
            try:
                cached = json.loads(self.token_cache.read_text())
                if time.time() < cached.get("expires_at", 0) - 60:
                    self._access_token = cached["access_token"]
                    self._token_expiry = cached["expires_at"]
                    return
            except Exception:
                pass  # cache corrupt — fetch fresh

        # Fetch new token
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        payload = parse.urlencode({
            "grant_type": "client_credentials",
            "scope": "product.compact",
        }).encode()

        req = request.Request(
            _TOKEN_URL,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
        )
        try:
            with request.urlopen(req, timeout=15) as resp:
                token_data = json.loads(resp.read())
        except error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(
                f"Kroger token request failed ({e.code}): {body}\n"
                "Check your KROGER_CLIENT_ID and KROGER_CLIENT_SECRET."
            )

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 1800)
        self._token_expiry = time.time() + expires_in

        # Cache it
        if self.token_cache:
            self.token_cache.parent.mkdir(parents=True, exist_ok=True)
            self.token_cache.write_text(json.dumps({
                "access_token": self._access_token,
                "expires_at": self._token_expiry,
            }))

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Authenticated GET request to the Kroger API."""
        self._ensure_token()
        url = _KROGER_BASE + endpoint
        if params:
            url += "?" + parse.urlencode(params)

        req = request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._access_token}",
            },
        )
        try:
            with request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except error.HTTPError as e:
            body = e.read().decode()
            logger.error(f"Kroger API {endpoint} failed ({e.code}): {body}")
            return {}

    # ── Product → Item ────────────────────────────────────────────────────────

    def _search_products(
        self,
        term: str,
        location_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Search Kroger products and return raw API product dicts."""
        params = {
            "filter.term":       term,
            "filter.locationId": location_id,
            "filter.limit":      limit,
        }
        data = self._get("/products", params)
        return data.get("data", [])

    def _product_to_item(
        self,
        product: dict,
        min_savings_pct: float,
    ) -> dict | None:
        """
        Convert a Kroger API product dict to a WhollyFare flyer item dict.
        Returns None if the product has no sale price or savings are below threshold.
        """
        name = product.get("description", "")
        if not name:
            return None

        # Pull pricing
        items = product.get("items", [{}])
        price_info = items[0].get("price", {}) if items else {}
        regular_price = price_info.get("regular", 0.0)
        promo_price   = price_info.get("promo", 0.0)

        # Only include if there's an active promotion
        if not promo_price or promo_price >= regular_price:
            return None

        savings_pct = round((1 - promo_price / regular_price) * 100, 1)
        if savings_pct < min_savings_pct:
            return None

        # Determine unit from size description
        size_desc = items[0].get("size", "") if items else ""
        unit = self._infer_unit(size_desc)

        # Enrich from item registry
        info = lookup(name)
        if info is None:
            return None  # skip items we can't categorise

        upc = product.get("upc", "")
        usda_id = info.get("usda_fdc_id")

        return {
            "name":                 name,
            "upc":                  upc,           # Kroger-specific; stripped before saving
            "usda_fdc_id":         usda_id,
            "allergens":           info.get("allergens", []),
            "category":            info.get("category", "other"),
            "tags":                info.get("tags", []),
            "sale_price_per_unit": round(promo_price, 2),
            "regular_price":       round(regular_price, 2),
            "unit":                unit,
            "standard_unit_weight_g": info.get("standard_unit_weight_g", 100.0),
            "nutrition": {
                "protein_g": 0, "fiber_g": 0, "saturated_fat_g": 0,
                "sodium_mg": 0, "added_sugar_g": 0, "iron_mg": 0,
                "calcium_mg": 0, "potassium_mg": 0, "vitamin_c_mg": 0,
                "sale_savings_pct": savings_pct,
            },
        }

    @staticmethod
    def _infer_unit(size_desc: str) -> str:
        size_lower = size_desc.lower()
        if "lb" in size_lower or "pound" in size_lower:
            return "lb"
        if "oz" in size_lower:
            return "oz"
        if "gal" in size_lower:
            return "gallon"
        if "ct" in size_lower or "count" in size_lower or "pk" in size_lower:
            return "each"
        if "bag" in size_lower:
            return "bag"
        return "each"

    @staticmethod
    def _next_sunday() -> str:
        today = date.today()
        days = (6 - today.weekday()) % 7
        return (today if days == 0 else date.fromordinal(today.toordinal() + days)).isoformat()


# ── Default search terms ──────────────────────────────────────────────────────
# These cover WhollyFare's four ingredient categories at a Kroger store.
# Extend or trim based on what your pilot household actually eats.

_DEFAULT_SEARCH_TERMS = [
    # Proteins
    "chicken breast", "chicken thigh", "ground turkey", "ground beef",
    "pork chop", "pork loin", "salmon", "tilapia", "shrimp", "eggs",
    # Produce
    "broccoli", "spinach", "sweet potato", "tomato", "bell pepper",
    "zucchini", "cauliflower", "carrot", "apple", "banana",
    # Grains
    "brown rice", "quinoa", "oats", "pasta",
    # Legumes
    "black beans", "lentils", "chickpeas",
    # Dairy
    "milk", "greek yogurt", "eggs", "butter",
    # Pantry staples
    "olive oil", "chicken broth", "canned tomatoes",
]
