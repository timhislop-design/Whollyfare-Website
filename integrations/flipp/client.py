"""
client.py — Flipp Circular API Client
---------------------------------------
Uses Flipp's unofficial public JSON API to pull weekly sale circulars
for Food Lion, Harris Teeter, Aldi, and other chains.

POC CONTEXT
-----------
Flipp is a digital flyer aggregator used by most major US grocery chains.
Their app fetches JSON from a public (unauthenticated) endpoint — no API
key required. This is an unofficial/undocumented API that has been stable
for several years and is used by multiple open-source grocery projects.

PRODUCTION NOTE
---------------
In production (Phase 3+), replace with:
  1. Official Flipp Retail Data API (enterprise, requires contract)
  2. Direct chain EDI feeds (Kroger-style API per chain)
  3. Hybrid: Flipp for coverage, direct APIs where available
The unofficial API is fine for the 10-household pilot; it is not a
business relationship and Flipp can change or block it without notice.

Usage:
    from integrations.flipp import FlippClient

    client = FlippClient()
    candidates = client.get_weekly_sales(chain="Food Lion", postal_code="22901")
    # returns list[IngredientCandidate] — same as KrogerClient
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib import error, request

# ── Path bootstrap (works whether called directly or imported) ─────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core_logic.constraint_engine import IngredientCandidate
from integrations.food_lion.item_registry import lookup

logger = logging.getLogger(__name__)

# ── Flipp API endpoints ────────────────────────────────────────────────────────
# Endpoints reverse-engineered from the Flipp web app. No auth required.
_FLYERS_URL  = "https://flipp.com/api/flyers"
_ITEMS_URL   = "https://flipp.com/flyerkit/publications/{flyer_id}/items"

# Request headers that mimic a browser — Flipp returns 403 without a UA
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

# ── Merchant slug mapping ──────────────────────────────────────────────────────
# Maps WhollyFare chain names → substrings to match in Flipp's merchant field.
# Lowercase substring match, case-insensitive.
CHAIN_MATCH: dict[str, list[str]] = {
    "Food Lion":     ["food lion"],
    "Harris Teeter": ["harris teeter"],
    "Aldi":          ["aldi"],
    "Kroger":        ["kroger"],
    "Walmart":       ["walmart"],
    "Giant":         ["giant food"],
    "Wegmans":       ["wegmans"],
    "Publix":        ["publix"],
    "Lidl":          ["lidl"],
    "Trader Joe's":  ["trader joe"],
}

# ── Category inference ─────────────────────────────────────────────────────────
# Flipp returns a free-text category string. Map it to WhollyFare categories.
_CAT_MAP: list[tuple[list[str], str]] = [
    (["produce", "fruit", "vegetable", "fresh"],       "produce"),
    (["meat", "seafood", "poultry", "beef", "pork",
      "chicken", "fish", "deli"],                       "protein"),
    (["dairy", "cheese", "yogurt", "egg", "butter",
      "milk", "cream"],                                 "dairy"),
    (["bread", "bakery", "cereal", "grain", "pasta",
      "rice", "tortilla"],                              "grain"),
    (["bean", "lentil", "legume", "tofu"],              "legume"),
    (["frozen"],                                        "frozen"),
    (["beverage", "juice", "drink", "water", "soda",
      "coffee", "tea"],                                 "beverage"),
    (["bakery", "cake", "cookie", "pastry"],            "bakery"),
    (["pantry", "condiment", "sauce", "oil", "spice",
      "soup", "canned", "snack", "chip"],               "pantry"),
]

def _infer_category(name: str, flipp_category: str) -> str:
    """Best-effort category from item name + Flipp's category string."""
    combined = (name + " " + (flipp_category or "")).lower()
    for keywords, cat in _CAT_MAP:
        if any(k in combined for k in keywords):
            return cat
    return "other"


def _parse_price(price_text: str | None, current_price) -> float:
    """
    Extract a float price. Flipp gives both a numeric current_price and a
    formatted price_text like '$2.49', '2/$5.00', 'BOGO', etc.
    """
    if current_price is not None:
        try:
            return float(current_price)
        except (ValueError, TypeError):
            pass
    if price_text:
        # Handle multi-buy: '2/$5' → 2.50
        m = re.search(r'(\d+)\s*/\s*\$?([\d.]+)', str(price_text))
        if m:
            try:
                return round(float(m.group(2)) / float(m.group(1)), 2)
            except ZeroDivisionError:
                pass
        # Plain price: '$2.49'
        m = re.search(r'\$?([\d.]+)', str(price_text))
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return 0.0


class FlippClient:
    """
    Pulls current sale items from Flipp for a given chain and postal code.

    POC: uses Flipp's unofficial public API — no credentials required.
    PRODUCTION: replace with official Flipp Retail Data API or direct chain EDI.
    """

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get(self, url: str, params: dict | None = None) -> object:
        """GET url with params, return parsed JSON. Raises RuntimeError on failure."""
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"
        req = request.Request(url, headers=_HEADERS)
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return json.loads(body)
        except error.HTTPError as e:
            raise RuntimeError(f"Flipp HTTP {e.code} for {url}: {e.reason}") from e
        except error.URLError as e:
            raise RuntimeError(f"Flipp network error for {url}: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Flipp returned non-JSON from {url}: {e}") from e

    def _match_chain(self, merchant_name: str, chain: str) -> bool:
        """True if the Flipp merchant name matches the requested chain."""
        slugs = CHAIN_MATCH.get(chain, [chain.lower()])
        mn = merchant_name.lower()
        return any(s in mn for s in slugs)

    def _item_to_candidate(self, item: dict) -> Optional[IngredientCandidate]:
        """
        Convert a Flipp item dict to an IngredientCandidate.
        Returns None if the item has no usable name or price.
        """
        name = (item.get("name") or "").strip()
        if not name or len(name) < 3:
            return None

        price = _parse_price(item.get("price_text"), item.get("current_price"))
        if price <= 0:
            # Flipp sometimes has BOGO or items priced at 0 — keep but flag
            price = 0.01   # nominal; buyer will see the price_text in description

        # Enrich from item registry (same registry used by Kroger + Food Lion parser)
        enrichment = lookup(name) or {
            "category": "other",
            "allergens": [],
            "tags": [],
            "standard_unit_weight_g": 100.0,
            "usda_fdc_id": None,
        }

        # Try to infer a better category if registry returns "other"
        flipp_cat = item.get("category", "") or ""
        if enrichment["category"] == "other":
            enrichment["category"] = _infer_category(name, flipp_cat)

        # Build unit from description (e.g. "per lb", "16 oz pkg")
        desc = (item.get("description") or item.get("size") or "").lower()
        unit = "each"
        if "lb" in desc or "per lb" in desc:
            unit = "lb"
        elif "oz" in desc:
            unit = "oz"
        elif "gal" in desc or "gallon" in desc:
            unit = "gal"
        elif "qt" in desc or "quart" in desc:
            unit = "qt"
        elif "pkg" in desc or "pack" in desc:
            unit = "pkg"
        elif "bag" in desc:
            unit = "bag"
        elif "bunch" in desc or "ct" in desc:
            unit = "bunch"

        return IngredientCandidate(
            name=name,
            usda_fdc_id=enrichment.get("usda_fdc_id"),
            allergens=enrichment.get("allergens", []),
            nutrition={},          # POC: full nutrition from USDA API in production
            sale_price_per_unit=price,
            unit=unit,
            standard_unit_weight_g=enrichment.get("standard_unit_weight_g", 100.0),
            category=enrichment.get("category", "other"),
            tags=enrichment.get("tags", []),
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def find_flyers(self, chain: str, postal_code: str) -> list[dict]:
        """
        Return a list of active Flipp flyer metadata dicts for `chain`
        near `postal_code`. Each dict has: id, merchant, valid_from, valid_to.
        """
        data = self._get(_FLYERS_URL, {
            "locale": "en-US",
            "postal_code": postal_code,
        })

        if not isinstance(data, list):
            logger.warning("Flipp /api/flyers returned unexpected type: %s", type(data))
            return []

        matched = []
        for flyer in data:
            merchant = flyer.get("merchant") or flyer.get("merchant_name") or ""
            if self._match_chain(merchant, chain):
                matched.append({
                    "id":          flyer.get("id"),
                    "merchant":    merchant,
                    "valid_from":  flyer.get("valid_from") or flyer.get("start_date"),
                    "valid_to":    flyer.get("valid_to")   or flyer.get("end_date"),
                })
        return matched

    def get_flyer_items(self, flyer_id: int | str) -> list[dict]:
        """Fetch raw item dicts for a single flyer."""
        url = _ITEMS_URL.format(flyer_id=flyer_id)
        data = self._get(url, {"locale": "en-US"})
        if isinstance(data, list):
            return data
        # Some flyers wrap in {"items": [...]}
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        logger.warning("Unexpected Flipp items response shape: %s", type(data))
        return []

    def get_weekly_sales(
        self,
        chain: str,
        postal_code: str = "22901",
    ) -> tuple[list[IngredientCandidate], dict]:
        """
        Pull this week's sale items for `chain` near `postal_code`.

        Returns:
            candidates  — list[IngredientCandidate]
            metadata    — {chain, flyer_id, valid_from, valid_to, raw_total,
                           skipped_no_price, method}
        """
        meta: dict = {
            "chain": chain,
            "flyer_id": None,
            "valid_from": None,
            "valid_to": None,
            "raw_total": 0,
            "skipped_no_price": 0,
            "method": "flipp_api",   # POC marker
        }

        # 1. Find the flyer
        flyers = self.find_flyers(chain, postal_code)
        if not flyers:
            raise RuntimeError(
                f"No active Flipp flyer found for '{chain}' near {postal_code}. "
                f"Check that the chain name matches exactly (e.g. 'Food Lion', "
                f"'Harris Teeter') and that the store publishes on Flipp."
            )

        # Pick the most recent flyer if there are duplicates
        flyer = flyers[0]
        meta["flyer_id"]   = flyer["id"]
        meta["valid_from"] = flyer["valid_from"]
        meta["valid_to"]   = flyer["valid_to"]

        # 2. Fetch items
        raw_items = self.get_flyer_items(flyer["id"])
        meta["raw_total"] = len(raw_items)

        # 3. Convert to IngredientCandidates
        candidates: list[IngredientCandidate] = []
        skipped = 0
        seen: set[str] = set()

        for item in raw_items:
            candidate = self._item_to_candidate(item)
            if candidate is None:
                skipped += 1
                continue
            # Deduplicate by name (case-insensitive)
            key = candidate.name.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)

        meta["skipped_no_price"] = skipped
        return candidates, meta

    def list_supported_chains(self, postal_code: str = "22901") -> list[str]:
        """
        Return a list of chain names available on Flipp near postal_code.
        Useful for discovering what's available in a new market.
        """
        try:
            data = self._get(_FLYERS_URL, {
                "locale": "en-US",
                "postal_code": postal_code,
            })
        except RuntimeError as e:
            logger.error("Could not list Flipp chains: %s", e)
            return []

        if not isinstance(data, list):
            return []

        seen: set[str] = set()
        merchants = []
        for flyer in data:
            m = flyer.get("merchant") or flyer.get("merchant_name") or ""
            if m and m not in seen:
                seen.add(m)
                merchants.append(m)
        return sorted(merchants)


# ── CLI diagnostic ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, pprint

    parser = argparse.ArgumentParser(description="Flipp circular diagnostic")
    parser.add_argument("--chain", default="Food Lion",
                        help="Chain name e.g. 'Food Lion', 'Harris Teeter'")
    parser.add_argument("--zip", default="22901",
                        help="US postal code (default: 22901 = Charlottesville)")
    parser.add_argument("--list-chains", action="store_true",
                        help="List all chains available near --zip")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    client = FlippClient()

    if args.list_chains:
        chains = client.list_supported_chains(args.zip)
        print(f"\nFlipp chains near {args.zip}:")
        for c in chains:
            print(f"  {c}")
        sys.exit(0)

    print(f"\nPulling {args.chain} flyer for zip {args.zip}...")
    try:
        candidates, meta = client.get_weekly_sales(chain=args.chain, postal_code=args.zip)
        print(f"\nMetadata: {json.dumps(meta, indent=2, default=str)}")
        print(f"\nFirst 10 items:")
        for c in candidates[:10]:
            print(f"  [{c.category:8s}] {c.name:<40s} ${c.sale_price_per_unit:.2f}/{c.unit}")
        print(f"\nTotal: {len(candidates)} candidates from {meta['raw_total']} raw items")
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)
