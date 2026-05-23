"""
item_registry.py
----------------
Lookup table that enriches a parsed item name with category, allergens,
dietary tags, and standard unit weight.

When the PDF parser extracts "Boneless Chicken Breast" and a price, it has
no idea whether the item contains gluten, how heavy a serving is, or whether
it's vegan-safe. This registry bridges that gap without a live API call.

Structure:
  KEY  — lowercase canonical name fragment that triggers the match
  VALUE — enrichment dict with the fields the constraint engine expects

Matching is substring-based (most specific match wins), so:
  "chicken breast" matches "boneless skinless chicken breast"
  "chicken" also matches, but "chicken breast" takes priority.

Maintainer note: add new entries alphabetically within each category block.
USDA FDC IDs sourced from https://fdc.nal.usda.gov/
"""

from __future__ import annotations

# ── Item registry ─────────────────────────────────────────────────────────────
# Each entry: { category, allergens, tags, standard_unit_weight_g, usda_fdc_id }
# standard_unit_weight_g = weight of one purchase unit (lb=453, each varies)

ITEM_REGISTRY: dict[str, dict] = {

    # ── Proteins ──────────────────────────────────────────────────────────────
    "chicken breast": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "331960",
    },
    "chicken thigh": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "331959",
    },
    "chicken drumstick": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "172868",
    },
    "whole chicken": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free"],
        "standard_unit_weight_g": 1814, "usda_fdc_id": "172868",
    },
    "ground turkey": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "171115",
    },
    "turkey breast": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "171115",
    },
    "ground beef": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "low-fodmap", "keto"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "174032",
    },
    "beef chuck": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "keto"],
        "standard_unit_weight_g": 1134, "usda_fdc_id": "174030",
    },
    "pork shoulder": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "keto"],
        "standard_unit_weight_g": 1814, "usda_fdc_id": "167903",
    },
    "pork chop": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "keto", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "167903",
    },
    "pork loin": {
        "category": "protein", "allergens": [],
        "tags": ["gluten-free", "keto"],
        "standard_unit_weight_g": 907, "usda_fdc_id": "167906",
    },
    "salmon": {
        "category": "protein", "allergens": ["fish"],
        "tags": ["gluten-free", "keto", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "175167",
    },
    "tilapia": {
        "category": "protein", "allergens": ["fish"],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "175177",
    },
    "cod fillet": {
        "category": "protein", "allergens": ["fish"],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "175126",
    },
    "shrimp": {
        "category": "protein", "allergens": ["shellfish"],
        "tags": ["gluten-free", "keto", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "175175",
    },
    "tuna": {
        "category": "protein", "allergens": ["fish"],
        "tags": ["gluten-free", "low-fodmap", "keto"],
        "standard_unit_weight_g": 142, "usda_fdc_id": "175159",
    },
    "eggs": {
        "category": "protein", "allergens": ["eggs"],
        "tags": ["vegetarian", "gluten-free", "low-fodmap", "keto"],
        "standard_unit_weight_g": 50, "usda_fdc_id": "748967",
    },

    # ── Produce ───────────────────────────────────────────────────────────────
    "broccoli": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170379",
    },
    "spinach": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 142, "usda_fdc_id": "168462",
    },
    "kale": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 142, "usda_fdc_id": "168421",
    },
    "sweet potato": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "168482",
    },
    "roma tomato": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170457",
    },
    "tomato": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170457",
    },
    "bell pepper": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170108",
    },
    "zucchini": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "169291",
    },
    "cucumber": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "168409",
    },
    "carrot": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170393",
    },
    "cabbage": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "low-glycemic"],
        "standard_unit_weight_g": 907, "usda_fdc_id": "169975",
    },
    "cauliflower": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "keto"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "169986",
    },
    "apple": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 182, "usda_fdc_id": "168203",
    },
    "banana": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 118, "usda_fdc_id": "173944",
    },
    "strawberr": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "167762",
    },
    "blueberr": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 148, "usda_fdc_id": "171711",
    },
    "avocado": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "keto", "low-fodmap"],
        "standard_unit_weight_g": 201, "usda_fdc_id": "171705",
    },
    "lettuce": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-fodmap", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "169248",
    },
    "onion": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170000",
    },
    "garlic": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 136, "usda_fdc_id": "169230",
    },
    "corn": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "169997",
    },
    "potato": {
        "category": "produce", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "170026",
    },

    # ── Grains ────────────────────────────────────────────────────────────────
    "brown rice": {
        "category": "grain", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 907, "usda_fdc_id": "169704",
    },
    "white rice": {
        "category": "grain", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 907, "usda_fdc_id": "169756",
    },
    "quinoa": {
        "category": "grain", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "168917",
    },
    "oatmeal": {
        "category": "grain", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "173904",
    },
    "oats": {
        "category": "grain", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "173904",
    },
    "pasta": {
        "category": "grain", "allergens": ["wheat"],
        "tags": ["vegan", "vegetarian", "contains-gluten"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "168936",
    },
    "bread": {
        "category": "grain", "allergens": ["wheat"],
        "tags": ["vegetarian", "contains-gluten"],
        "standard_unit_weight_g": 567, "usda_fdc_id": "172686",
    },
    "tortilla": {
        "category": "grain", "allergens": ["wheat"],
        "tags": ["vegan", "vegetarian", "contains-gluten"],
        "standard_unit_weight_g": 340, "usda_fdc_id": "168898",
    },

    # ── Legumes ───────────────────────────────────────────────────────────────
    "black bean": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "173735",
    },
    "kidney bean": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "173746",
    },
    "chickpea": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "173756",
    },
    "garbanzo": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "173756",
    },
    "lentil": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 453, "usda_fdc_id": "172420",
    },
    "pinto bean": {
        "category": "legume", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "173744",
    },
    "edamame": {
        "category": "legume", "allergens": ["soy"],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "168411",
    },

    # ── Dairy ─────────────────────────────────────────────────────────────────
    "whole milk": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free"],
        "standard_unit_weight_g": 3785, "usda_fdc_id": "336070",
    },
    "2% milk": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free"],
        "standard_unit_weight_g": 3785, "usda_fdc_id": "336075",
    },
    "milk": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free"],
        "standard_unit_weight_g": 3785, "usda_fdc_id": "336070",
    },
    "greek yogurt": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free", "low-glycemic"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "170903",
    },
    "yogurt": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "170901",
    },
    "cheddar": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free", "keto"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "173414",
    },
    "cheese": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "173414",
    },
    "butter": {
        "category": "dairy", "allergens": ["milk"],
        "tags": ["vegetarian", "gluten-free", "keto"],
        "standard_unit_weight_g": 454, "usda_fdc_id": "173430",
    },

    # ── Oils & Pantry ─────────────────────────────────────────────────────────
    "olive oil": {
        "category": "other", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free", "keto", "low-fodmap"],
        "standard_unit_weight_g": 500, "usda_fdc_id": "748608",
    },
    "vegetable oil": {
        "category": "other", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 946, "usda_fdc_id": "172336",
    },
    "canned tomato": {
        "category": "other", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "170456",
    },
    "tomato sauce": {
        "category": "other", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 425, "usda_fdc_id": "170456",
    },
    "chicken broth": {
        "category": "other", "allergens": [],
        "tags": ["gluten-free", "low-fodmap"],
        "standard_unit_weight_g": 946, "usda_fdc_id": "171150",
    },
    "vegetable broth": {
        "category": "other", "allergens": [],
        "tags": ["vegan", "vegetarian", "gluten-free"],
        "standard_unit_weight_g": 946, "usda_fdc_id": "171150",
    },
}

# ── Sorted keys for longest-match-first lookup ────────────────────────────────
# Pre-sort so longer/more-specific keys are checked before shorter ones.
_SORTED_KEYS: list[str] = sorted(ITEM_REGISTRY.keys(), key=len, reverse=True)


def lookup(name: str) -> dict | None:
    """Return registry entry for name (longest-match), or None."""
    lower = name.lower()
    for key in _SORTED_KEYS:
        if key in lower:
            return ITEM_REGISTRY[key]
    return None
