"""
usda_enricher.py — USDA FoodData Central Nutrition Enricher
------------------------------------------------------------
Fills in real nutrition data for parsed flyer items by querying the free
USDA FoodData Central API (https://fdc.nal.usda.gov/).

The parser outputs items with stub nutrition (all zeros). Run the enricher
as a post-processing step to replace those stubs with real values before
saving the final flyer JSON.

API key: Free from https://api.data.gov/signup/
Set it as env variable USDA_API_KEY or pass directly to the enricher.

Usage:
    from integrations.food_lion.usda_enricher import USDAEnricher

    enricher = USDAEnricher(api_key="YOUR_KEY_HERE")
    result = parser.parse_pdf("circular.pdf")           # FlyerResult
    enriched_result = enricher.enrich(result)           # fills nutrition
    parser.save(enriched_result, "app/data/flyers/food_lion_2026-05-18.json")

Rate limits: 1,000 requests/hour for free tier. A typical 14-item flyer uses
14 requests. The enricher caches lookups in a local JSON file so repeated
runs don't re-fetch known items.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Nutrient IDs in FDC API responses that map to our schema
_FDC_NUTRIENT_MAP = {
    1003: "protein_g",           # Protein
    1079: "fiber_g",             # Fiber, total dietary
    1258: "saturated_fat_g",     # Fatty acids, total saturated
    1093: "sodium_mg",           # Sodium, Na
    2000: "added_sugar_g",       # Sugars, added  (not always present → 0)
    1089: "iron_mg",             # Iron, Fe
    1087: "calcium_mg",          # Calcium, Ca
    1092: "potassium_mg",        # Potassium, K
    1162: "vitamin_c_mg",        # Vitamin C, total ascorbic acid
}

_FDC_BASE = "https://api.nal.usda.gov/fdc/v1"
_DEFAULT_CACHE = Path(__file__).parent / ".usda_cache.json"


class USDAEnricher:
    """
    Enriches a FlyerResult's item list with real nutrition data from USDA FDC.

    Parameters
    ----------
    api_key : str | None
        Your api.data.gov key. Falls back to env var USDA_API_KEY.
    cache_path : Path | str | None
        Path to a local JSON cache file. Defaults to .usda_cache.json next to
        this file. Pass None to disable caching.
    request_delay : float
        Seconds to wait between API requests (default 0.3 to stay well
        under the 1,000/hour rate limit).
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_path: Path | str | None = _DEFAULT_CACHE,
        request_delay: float = 0.3,
    ):
        self.api_key = api_key or os.environ.get("USDA_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "No USDA_API_KEY set. Nutrition enrichment will be skipped. "
                "Get a free key at https://api.data.gov/signup/"
            )
        self.request_delay = request_delay
        self.cache_path = Path(cache_path) if cache_path else None
        self._cache: dict[str, dict] = {}
        if self.cache_path and self.cache_path.exists():
            with open(self.cache_path) as f:
                self._cache = json.load(f)

    # ── Public API ────────────────────────────────────────────────────────────

    def enrich(self, result) -> object:
        """
        Enrich a FlyerResult in-place with real USDA nutrition data.
        Returns the same FlyerResult object.
        """
        if not self.api_key:
            logger.info("Skipping USDA enrichment — no API key.")
            return result

        enriched_count = 0
        for item in result.items:
            fdc_id = item.get("usda_fdc_id")
            name = item.get("name", "")

            nutrition = self._fetch_nutrition(fdc_id=fdc_id, name=name)
            if nutrition:
                # Preserve sale_savings_pct from parser
                nutrition["sale_savings_pct"] = item["nutrition"].get(
                    "sale_savings_pct", 0.0
                )
                item["nutrition"] = nutrition
                enriched_count += 1

        # Save cache after run
        self._save_cache()
        result.parse_metadata["usda_enriched_count"] = enriched_count
        logger.info(f"USDA enriched {enriched_count}/{len(result.items)} items.")
        return result

    def fetch_by_name(self, name: str) -> dict | None:
        """
        Convenience: look up nutrition data for a food name without a
        full FlyerResult (useful for testing individual items).
        """
        return self._fetch_nutrition(fdc_id=None, name=name)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _fetch_nutrition(
        self,
        fdc_id: str | None,
        name: str,
    ) -> dict | None:
        """Fetch nutrition data, using cache when available."""
        cache_key = fdc_id or name.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        nutrition = None
        if fdc_id:
            nutrition = self._fetch_by_fdc_id(fdc_id)
        if nutrition is None and name:
            nutrition = self._search_by_name(name)

        if nutrition:
            self._cache[cache_key] = nutrition
        return nutrition

    def _fetch_by_fdc_id(self, fdc_id: str) -> dict | None:
        """Direct FDC food detail lookup."""
        try:
            import urllib.request, urllib.error
            url = f"{_FDC_BASE}/food/{fdc_id}?api_key={self.api_key}"
            time.sleep(self.request_delay)
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            return self._extract_nutrients(data.get("foodNutrients", []))
        except Exception as e:
            logger.debug(f"FDC ID lookup failed for {fdc_id}: {e}")
            return None

    def _search_by_name(self, name: str) -> dict | None:
        """Search FDC by food name, use first SR Legacy or Foundation result."""
        try:
            import urllib.request, urllib.parse
            query = urllib.parse.urlencode({
                "query": name,
                "api_key": self.api_key,
                "dataType": "SR Legacy,Foundation",
                "pageSize": 3,
            })
            url = f"{_FDC_BASE}/foods/search?{query}"
            time.sleep(self.request_delay)
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())

            foods = data.get("foods", [])
            if not foods:
                return None
            # Use the first result's nutrients
            return self._extract_nutrients(foods[0].get("foodNutrients", []))
        except Exception as e:
            logger.debug(f"FDC search failed for {name!r}: {e}")
            return None

    def _extract_nutrients(self, food_nutrients: list) -> dict:
        """Map FDC nutrient list to our schema keys."""
        result: dict = {v: 0.0 for v in _FDC_NUTRIENT_MAP.values()}
        for nutrient in food_nutrients:
            # FDC API v1 uses either 'nutrientId' (detail) or 'nutrientId' (search)
            nid = (
                nutrient.get("nutrient", {}).get("id")
                or nutrient.get("nutrientId")
                or nutrient.get("nutrient_id")
            )
            value = nutrient.get("amount") or nutrient.get("value") or 0.0
            if nid in _FDC_NUTRIENT_MAP:
                result[_FDC_NUTRIENT_MAP[nid]] = round(float(value), 2)
        return result

    def _save_cache(self):
        """Persist the in-memory cache to disk."""
        try:
            with open(self._cache_path, 'w') as f:
                import json as _j; _j.dump(self._cache, f)
        except Exception:
            pass
