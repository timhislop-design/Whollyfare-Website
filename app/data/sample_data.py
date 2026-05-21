"""
sample_data.py — Demo / pilot data for WhollyFare.

Provides six loader functions that populate the UI without requiring a live
database or API connection.  All prices reflect realistic 2026 grocery costs.
"""

# ── Profile schema import (degrades gracefully if not on path) ────────────────
try:
    from app.core_logic.profile_schema import (
        HouseholdProfile,
        MemberProfile,
        Diagnosis,
        LifestyleTag,
    )
    _SCHEMA_AVAILABLE = True
except ImportError:
    HouseholdProfile = None
    MemberProfile = None
    Diagnosis = None
    LifestyleTag = None
    _SCHEMA_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# 1. Household
# ─────────────────────────────────────────────────────────────────────────────

def load_demo_household():
    """Return the Hislop pilot household (Tim, Abby, Chas).

    Returns a HouseholdProfile if the schema module is available,
    otherwise a plain dict with the same logical structure.
    """
    if _SCHEMA_AVAILABLE:
        tim = MemberProfile(
            name="Tim",
            age=45,
            allergies=[],
            diagnoses=[],
            lifestyle_tags=[],
            custom_exclusions=[],
        )
        abby = MemberProfile(
            name="Abby",
            age=44,
            allergies=["wheat"],
            diagnoses=[Diagnosis.CELIAC],
            lifestyle_tags=[],
            custom_exclusions=[],
        )
        chas = MemberProfile(
            name="Chas",
            age=16,
            allergies=["peanuts", "tree_nuts"],
            diagnoses=[],
            lifestyle_tags=[],
            custom_exclusions=[],
        )
        return HouseholdProfile(
            household_name="The Hislop Household",
            members=[tim, abby, chas],
            weekly_budget_usd=150.00,
            servings_per_meal=4,
            meals_per_week=5,
        )
    else:
        # Graceful fallback — plain dict mirrors the schema structure
        return {
            "household_name": "The Hislop Household",
            "members": [
                {"name": "Tim",  "age": 45, "allergies": [],                      "diagnoses": [],       "lifestyle_tags": [], "custom_exclusions": []},
                {"name": "Abby", "age": 44, "allergies": ["wheat"],               "diagnoses": ["celiac"], "lifestyle_tags": [], "custom_exclusions": []},
                {"name": "Chas", "age": 16, "allergies": ["peanuts","tree_nuts"], "diagnoses": [],       "lifestyle_tags": [], "custom_exclusions": []},
            ],
            "weekly_budget_usd": 150.00,
            "servings_per_meal": 4,
            "meals_per_week": 5,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Grocers
# ─────────────────────────────────────────────────────────────────────────────

def load_demo_grocers():
    """Return a list of grocer configuration dicts for the pilot."""
    return [
        {
            "id": "kroger_palmyra",
            "name": "Kroger",
            "location": "Palmyra, VA",
            "source_type": "api",
            "api_key_configured": True,
            "last_sync": "2026-05-14T08:30:00",
            "status": "ok",
            "notes": "Kroger Marketplace — full API integration",
        },
        {
            "id": "food_lion_palmyra",
            "name": "Food Lion",
            "location": "Palmyra, VA",
            "source_type": "pdf",
            "api_key_configured": False,
            "last_sync": "2026-05-12T14:00:00",
            "status": "ok",
            "notes": "Weekly flyer PDF, parsed automatically",
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Flyer data
# ─────────────────────────────────────────────────────────────────────────────

def load_demo_flyer_data():
    """Return parsed weekly sale data for both stores (week of 2026-05-11)."""
    return {
        "week": "2026-05-11",
        "stores": {
            "kroger_palmyra": {
                "store_name": "Kroger",
                "items": [
                    {"name": "Boneless Skinless Chicken Breasts", "unit": "lb",  "sale_price": 3.49, "regular_price": 5.99},
                    {"name": "93% Lean Ground Beef",              "unit": "lb",  "sale_price": 4.99, "regular_price": 6.49},
                    {"name": "Atlantic Salmon Fillets",           "unit": "lb",  "sale_price": 7.99, "regular_price": 11.99},
                    {"name": "Jasmine Rice",                      "unit": "2 lb","sale_price": 2.79, "regular_price": 3.99},
                    {"name": "Penne Pasta (gluten-free)",         "unit": "12 oz","sale_price": 2.49, "regular_price": 3.49},
                    {"name": "Canned Crushed Tomatoes",           "unit": "28 oz","sale_price": 1.29, "regular_price": 1.89},
                    {"name": "Baby Spinach",                      "unit": "5 oz", "sale_price": 2.99, "regular_price": 3.99},
                    {"name": "Bell Peppers (3-pack)",             "unit": "pack","sale_price": 3.49, "regular_price": 4.99},
                    {"name": "Broccoli Crowns",                   "unit": "lb",  "sale_price": 1.49, "regular_price": 2.29},
                    {"name": "Roma Tomatoes",                     "unit": "lb",  "sale_price": 1.19, "regular_price": 1.79},
                    {"name": "White Corn Tortillas (30 ct)",      "unit": "pkg", "sale_price": 2.99, "regular_price": 3.99},
                    {"name": "Shredded Mexican Cheese Blend",     "unit": "8 oz","sale_price": 2.49, "regular_price": 3.29},
                    {"name": "Sour Cream",                        "unit": "16 oz","sale_price": 1.99, "regular_price": 2.79},
                    {"name": "Olive Oil",                         "unit": "16 oz","sale_price": 5.49, "regular_price": 7.99},
                ],
            },
            "food_lion_palmyra": {
                "store_name": "Food Lion",
                "items": [
                    {"name": "Boneless Skinless Chicken Breasts", "unit": "lb",  "sale_price": 3.79, "regular_price": 5.99},
                    {"name": "93% Lean Ground Beef",              "unit": "lb",  "sale_price": 4.79, "regular_price": 6.29},
                    {"name": "Atlantic Salmon Fillets",           "unit": "lb",  "sale_price": 8.49, "regular_price": 11.99},
                    {"name": "Black Beans (canned)",              "unit": "15 oz","sale_price": 0.89, "regular_price": 1.29},
                    {"name": "Jasmine Rice",                      "unit": "2 lb","sale_price": 2.99, "regular_price": 3.99},
                    {"name": "Frozen Broccoli",                   "unit": "12 oz","sale_price": 1.29, "regular_price": 1.99},
                    {"name": "Zucchini",                          "unit": "lb",  "sale_price": 1.09, "regular_price": 1.69},
                    {"name": "Cherry Tomatoes",                   "unit": "10 oz","sale_price": 2.49, "regular_price": 3.29},
                    {"name": "Limes (5-pack)",                    "unit": "pack","sale_price": 1.49, "regular_price": 2.19},
                    {"name": "Garlic Bulbs (3 ct)",               "unit": "pkg", "sale_price": 1.29, "regular_price": 1.99},
                    {"name": "Canned Diced Tomatoes",             "unit": "14.5 oz","sale_price": 0.99, "regular_price": 1.49},
                    {"name": "White Corn Tortillas (30 ct)",      "unit": "pkg", "sale_price": 3.19, "regular_price": 3.99},
                ],
            },
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Weekly plan
# ─────────────────────────────────────────────────────────────────────────────

def load_demo_plan():
    """Return a 5-dinner optimized plan for the week of 2026-05-11.

    Comparisons:
      - WhollyFare cross-store plan: ~$82
      - Single best store (Kroger):  ~$108
      - HelloFresh equivalent:       ~$200
    """
    return {
        "week": "2026-05-11",
        "servings": 4,
        "meals": [
            {
                "day": "Monday",
                "name": "Sheet Pan Chicken & Veggies",
                "gluten_free": True,
                "allergen_notes": "No peanuts/tree nuts. Use GF tamari if desired.",
                "best_store": "kroger_palmyra",
                "ingredients": [
                    {"item": "Boneless Skinless Chicken Breasts", "qty": "2 lb",  "store": "kroger_palmyra", "cost": 6.98},
                    {"item": "Bell Peppers (3-pack)",             "qty": "1 pack","store": "kroger_palmyra", "cost": 3.49},
                    {"item": "Broccoli Crowns",                   "qty": "1 lb",  "store": "kroger_palmyra", "cost": 1.49},
                    {"item": "Zucchini",                          "qty": "1 lb",  "store": "food_lion_palmyra","cost": 1.09},
                    {"item": "Olive Oil",                         "qty": "portion","store": "kroger_palmyra","cost": 0.60},
                    {"item": "Garlic Bulbs (3 ct)",               "qty": "portion","store": "food_lion_palmyra","cost": 0.43},
                ],
                "meal_cost": 14.08,
            },
            {
                "day": "Tuesday",
                "name": "Beef Taco Bowls",
                "gluten_free": True,
                "allergen_notes": "Use corn tortillas (GF). No peanuts/tree nuts.",
                "best_store": "food_lion_palmyra",
                "ingredients": [
                    {"item": "93% Lean Ground Beef",          "qty": "1.5 lb","store": "food_lion_palmyra","cost": 7.19},
                    {"item": "Black Beans (canned)",          "qty": "2 cans","store": "food_lion_palmyra","cost": 1.78},
                    {"item": "White Corn Tortillas (30 ct)",  "qty": "1 pkg", "store": "kroger_palmyra",   "cost": 2.99},
                    {"item": "Roma Tomatoes",                 "qty": "1 lb",  "store": "kroger_palmyra",   "cost": 1.19},
                    {"item": "Shredded Mexican Cheese Blend", "qty": "8 oz",  "store": "kroger_palmyra",   "cost": 2.49},
                    {"item": "Sour Cream",                    "qty": "8 oz",  "store": "kroger_palmyra",   "cost": 1.00},
                    {"item": "Limes (5-pack)",                "qty": "portion","store": "food_lion_palmyra","cost": 0.60},
                ],
                "meal_cost": 17.24,
            },
            {
                "day": "Wednesday",
                "name": "Salmon with Jasmine Rice",
                "gluten_free": True,
                "allergen_notes": "No peanuts/tree nuts. Naturally GF.",
                "best_store": "kroger_palmyra",
                "ingredients": [
                    {"item": "Atlantic Salmon Fillets", "qty": "1.5 lb","store": "kroger_palmyra",    "cost": 11.99},
                    {"item": "Jasmine Rice",            "qty": "1 lb",  "store": "kroger_palmyra",    "cost": 1.40},
                    {"item": "Baby Spinach",            "qty": "5 oz",  "store": "kroger_palmyra",    "cost": 2.99},
                    {"item": "Cherry Tomatoes",         "qty": "10 oz", "store": "food_lion_palmyra", "cost": 2.49},
                    {"item": "Olive Oil",               "qty": "portion","store": "kroger_palmyra",   "cost": 0.60},
                    {"item": "Garlic Bulbs (3 ct)",     "qty": "portion","store": "food_lion_palmyra","cost": 0.43},
                ],
                "meal_cost": 19.90,
            },
            {
                "day": "Thursday",
                "name": "Black Bean Quesadillas",
                "gluten_free": True,
                "allergen_notes": "Corn tortillas are GF. No peanuts/tree nuts.",
                "best_store": "food_lion_palmyra",
                "ingredients": [
                    {"item": "Black Beans (canned)",         "qty": "2 cans","store": "food_lion_palmyra","cost": 1.78},
                    {"item": "White Corn Tortillas (30 ct)", "qty": "portion","store": "kroger_palmyra", "cost": 1.00},
                    {"item": "Shredded Mexican Cheese Blend","qty": "8 oz",  "store": "kroger_palmyra",  "cost": 2.49},
                    {"item": "Bell Peppers (3-pack)",        "qty": "portion","store": "kroger_palmyra", "cost": 1.16},
                    {"item": "Sour Cream",                   "qty": "8 oz",  "store": "kroger_palmyra",  "cost": 1.00},
                    {"item": "Canned Diced Tomatoes",        "qty": "1 can", "store": "food_lion_palmyra","cost": 0.99},
                ],
                "meal_cost": 8.42,
            },
            {
                "day": "Friday",
                "name": "Chicken Penne Arrabbiata",
                "gluten_free": True,
                "allergen_notes": "Use GF penne. No peanuts/tree nuts.",
                "best_store": "kroger_palmyra",
                "ingredients": [
                    {"item": "Boneless Skinless Chicken Breasts","qty": "1.5 lb","store": "kroger_palmyra",   "cost": 5.24},
                    {"item": "Penne Pasta (gluten-free)",        "qty": "12 oz", "store": "kroger_palmyra",   "cost": 2.49},
                    {"item": "Canned Crushed Tomatoes",          "qty": "28 oz", "store": "kroger_palmyra",   "cost": 1.29},
                    {"item": "Canned Diced Tomatoes",            "qty": "14.5 oz","store": "food_lion_palmyra","cost": 0.99},
                    {"item": "Olive Oil",                        "qty": "portion","store": "kroger_palmyra",  "cost": 0.60},
                    {"item": "Garlic Bulbs (3 ct)",              "qty": "portion","store": "food_lion_palmyra","cost": 0.43},
                    {"item": "Baby Spinach",                     "qty": "portion","store": "kroger_palmyra",  "cost": 1.00},
                ],
                "meal_cost": 12.04,
            },
        ],
        "totals": {
            "whollyfare_plan":   81.68,
            "single_store_best": 107.95,
            "hellofresh_equiv":  199.80,
            "found_money":       26.27,   # single_store_best - whollyfare_plan
            "vs_hellofresh":    118.12,   # hellofresh_equiv  - whollyfare_plan
            "currency": "USD",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Found Money ledger
# ─────────────────────────────────────────────────────────────────────────────

def load_demo_ledger():
    """Return 4 weeks of Found Money history showing a positive trend."""
    return [
        {
            "week":              "2026-04-20",
            "whollyfare_cost":   88.42,
            "single_store_cost": 106.31,
            "found_money":       17.89,
            "vs_hellofresh":    111.38,
            "meals_planned":     5,
            "stores_used":       2,
        },
        {
            "week":              "2026-04-27",
            "whollyfare_cost":   84.17,
            "single_store_cost": 107.04,
            "found_money":       22.87,
            "vs_hellofresh":    115.63,
            "meals_planned":     5,
            "stores_used":       2,
        },
        {
            "week":              "2026-05-04",
            "whollyfare_cost":   86.93,
            "single_store_cost": 107.88,
            "found_money":       20.95,
            "vs_hellofresh":    112.87,
            "meals_planned":     5,
            "stores_used":       2,
        },
        {
            "week":              "2026-05-11",
            "whollyfare_cost":   81.68,
            "single_store_cost": 107.95,
            "found_money":       26.27,
            "vs_hellofresh":    118.12,
            "meals_planned":     5,
            "stores_used":       2,
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 6. All demo data
# ─────────────────────────────────────────────────────────────────────────────

def load_all_demo_data():
    """Return a single dict containing all demo data, keyed for easy access."""
    return {
        "household":     load_demo_household(),
        "grocers":       load_demo_grocers(),
        "flyer_data":    load_demo_flyer_data(),
        "plan":          load_demo_plan(),
        "ledger_history": load_demo_ledger(),
        "active_week":   "2026-05-11",
    }
