"""
meal_planner.py
---------------
Assembles weekly meal plans from constraint-cleared, scored ingredients.

This bridges the gap between "ranked ingredients" (BudgetOptimizer's output)
and "an actual menu the family can cook." It implements the 5-7 ingredient
modular architecture from the SML strategy docs, using "Flavor Plugins" to
keep variety high while keeping the shopping list tight.

Sincere Strategy invariants:
  - Every meal is built ONLY from ingredients that already passed the
    ConstraintEngine. Safety is never relaxed for variety or budget.
  - Every meal carries a `safety_attestation` listing which household members
    it is verified safe for — surfaced in the dashboard as the Safety Badge.
  - Every meal carries a `cost_per_serving` so the user can audit budget math.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .budget_optimizer import ScoredIngredient
from .profile_schema import HouseholdProfile

# Recipe library — graceful fallback if path not resolved
try:
    from ..data.recipe_library import (
        recipes_for_sale_items, get_recipe_shopping_items, query_recipes
    )
    _RECIPE_LIB = True
except ImportError:
    _RECIPE_LIB = False


# ── Flavor Plugins ────────────────────────────────────────────────────────────
# Each plugin is a "voice" the same base ingredients can be cooked in. The
# plugin doesn't add ingredients to the shopping list — it directs how the
# core ingredients are seasoned from the household's existing pantry.
#
# This is what keeps the 5-7 ingredient architecture from feeling repetitive:
# the same chicken + rice + broccoli becomes Mexican on Monday, Asian on
# Wednesday, Mediterranean on Friday.

FLAVOR_PLUGINS: dict[str, dict] = {
    "mexican": {
        "name": "Mexican",
        "pantry_seasonings": ["cumin", "chili powder", "lime", "cilantro"],
        "method_hint": "Sear protein with cumin + chili; serve over base with lime.",
        # meal_formats: {protein} replaced with anchor ingredient name
        "meal_formats": ["{protein} Tacos", "{protein} Fajitas",
                         "{protein} Burrito Bowl", "Mexican {protein} & Rice"],
    },
    "asian": {
        "name": "Asian",
        "pantry_seasonings": ["soy sauce", "ginger", "garlic", "sesame oil"],
        "method_hint": "Stir-fry protein and produce in sesame oil; serve over base.",
        "incompatible_with": ["soy"],  # excluded if household has soy allergy
        "meal_formats": ["{protein} Stir-Fry", "{protein} Fried Rice",
                         "{protein} Noodle Bowl", "Asian {protein} & Veg"],
    },
    "mediterranean": {
        "name": "Mediterranean",
        "pantry_seasonings": ["olive oil", "lemon", "oregano", "garlic"],
        "method_hint": "Roast protein and produce with olive oil + oregano; finish with lemon.",
        "meal_formats": ["Mediterranean {protein}", "Roasted {protein} & Veg",
                         "{protein} with Lemon & Herbs", "Greek-Style {protein}"],
    },
    "american_comfort": {
        "name": "American",
        "pantry_seasonings": ["salt", "pepper", "butter", "thyme"],
        "method_hint": "Simple roast/sauté with salt, pepper, butter; herb finish.",
        "meal_formats": ["Roasted {protein} Dinner", "{protein} with Roasted Veg",
                         "Classic {protein} Plate", "Herb-Butter {protein}"],
    },
    "italian": {
        "name": "Italian",
        "pantry_seasonings": ["olive oil", "basil", "garlic", "parmesan"],
        "method_hint": "Sauté with olive oil and garlic; finish with basil.",
        "meal_formats": ["Italian {protein}", "{protein} Pasta Night",
                         "{protein} Piccata", "Tuscan {protein}"],
    },
}


# ── Dietary Identity → Protein Pool ──────────────────────────────────────────
# Maps lifestyle identity to the protein keyword families valid for that household.
# Keywords matched against ingredient.name (lowercase) from the sale flyer.
# Omnivore (no identity tag) is absent — all protein-category sale items are valid.
#
# Architecture note: the planner reads household.lifestyle_tags and filters the
# protein pool BEFORE the round-robin. When a household is pescatarian, only
# fish/seafood sale items become meal anchors. When vegan, plant proteins from
# the flyer (rarely present) or pantry fallback are used.
# Phase 2: USDA FDC category mapping replaces keyword matching.
PROTEIN_POOL_FOR_IDENTITY: dict[str, set[str]] = {
    "vegan": {
        "tofu", "tempeh", "lentil", "chickpea", "bean", "edamame",
        "legume", "seitan", "jackfruit", "falafel",
    },
    "vegetarian": {
        "tofu", "tempeh", "lentil", "chickpea", "bean", "edamame",
        "legume", "egg", "paneer", "cheese", "seitan", "halloumi",
    },
    "pescatarian": {
        "salmon", "shrimp", "cod", "tilapia", "fish", "tuna",
        "halibut", "scallop", "crab", "lobster", "trout", "mahi",
        "prawn", "clam", "mussel", "anchovy",
    },
    "keto": {
        "chicken", "beef", "pork", "salmon", "bacon", "egg",
        "turkey", "lamb", "shrimp", "tuna",
    },
    "paleo": {
        "chicken", "beef", "pork", "salmon", "shrimp", "turkey",
        "lamb", "bison", "tuna", "cod",
    },
    # whole30 + low-fodmap: protein-agnostic (restrictions apply to produce/grains)
    # halal/kosher: protein-agnostic here; constraint engine handles preparation rules
}

# Plant-based pantry fallback proteins injected when a vegan/vegetarian household
# has no matching plant protein on sale this week. These are common staples.
# Pilot: static list with median grocery prices. Phase 2: cross-reference
# pantry_items() and current flyer for on-sale plant proteins first.
PLANT_PROTEIN_PANTRY_FALLBACK: dict[str, list[dict]] = {
    "vegan": [
        {"name": "Canned Chickpeas",   "price": 1.29, "unit": "15oz can",   "category": "legumes"},
        {"name": "Canned Black Beans", "price": 0.99, "unit": "15oz can",   "category": "legumes"},
        {"name": "Firm Tofu",          "price": 2.49, "unit": "14oz block", "category": "protein"},
        {"name": "Red Lentils",        "price": 1.79, "unit": "1 lb bag",   "category": "legumes"},
    ],
    "vegetarian": [
        {"name": "Eggs",               "price": 3.99, "unit": "dozen",      "category": "protein"},
        {"name": "Firm Tofu",          "price": 2.49, "unit": "14oz block", "category": "protein"},
        {"name": "Canned Chickpeas",   "price": 1.29, "unit": "15oz can",   "category": "legumes"},
        {"name": "Canned Black Beans", "price": 0.99, "unit": "15oz can",   "category": "legumes"},
    ],
}


# ── Meal & WeeklyPlan dataclasses ─────────────────────────────────────────────


@dataclass
class Meal:
    day: str                              # "Monday", "Tuesday", ...
    slot: str                             # "breakfast", "lunch", "dinner"
    name: str                             # e.g. "Mexican Chicken & Rice Bowl"
    ingredients: list[ScoredIngredient]   # the actual sourced items
    flavor_plugin: str                    # key into FLAVOR_PLUGINS
    pantry_seasonings: list[str]
    method_hint: str
    cost_per_serving: float               # for the dashboard budget audit
    servings: int
    safety_attestation: list[str]         # member names this meal is verified safe for
    recipe_id: Optional[str] = None       # recipe_library ID if matched
    recipe_ingredients: list = field(default_factory=list)  # non-pantry items from library

    @property
    def total_cost(self) -> float:
        return self.cost_per_serving * self.servings


@dataclass
class WeeklyPlan:
    household_name: str
    meals: list[Meal] = field(default_factory=list)
    flyer_week: Optional[str] = None
    grocer: Optional[str] = None

    @property
    def total_cost(self) -> float:
        return sum(m.total_cost for m in self.meals)

    @property
    def shopping_list(self) -> list[ScoredIngredient]:
        """Deduplicated set of ingredients across the week."""
        seen: dict[str, ScoredIngredient] = {}
        for meal in self.meals:
            for ing in meal.ingredients:
                seen.setdefault(ing.ingredient.name, ing)
        return list(seen.values())


# ── MealPlanner ───────────────────────────────────────────────────────────────


class MealPlanner:
    """
    Assembles a weekly plan from a pool of constraint-cleared scored ingredients.

    MVP strategy: pick a small set of "hero" ingredients (5-7), then rotate
    them through Flavor Plugins across the week so each day's meal feels
    different despite drawing from the same shopping list. This is the core
    SML "Modular Architecture" — minimize the shopping list, maximize the menu.
    """

    DEFAULT_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    DEFAULT_SLOT = "dinner"  # MVP: dinner-only. v2: breakfast/lunch/dinner.

    def __init__(self, household: HouseholdProfile):
        self.household = household
        self._safe_plugins = self._compatible_flavor_plugins()

    def _compatible_flavor_plugins(self) -> list[str]:
        """Drop any flavor plugin that conflicts with a household allergen."""
        all_allergens: set[str] = set()
        for member in self.household.members:
            all_allergens.update(member.allergies)

        compatible = []
        for key, plugin in FLAVOR_PLUGINS.items():
            blocked = set(plugin.get("incompatible_with", []))
            if blocked & all_allergens:
                continue
            compatible.append(key)
        return compatible

    def _dietary_flags(self) -> dict:
        """Translate household allergies/lifestyle_tags to recipe_library dietary_flags format."""
        flags: dict = {}
        for member in self.household.members:
            for allergy in getattr(member, "allergies", []):
                al = allergy.lower()
                if any(k in al for k in ["gluten", "wheat", "celiac"]):
                    flags["gluten_free"] = True
                if any(k in al for k in ["dairy", "milk", "lactose"]):
                    flags["dairy_free"] = True
                if any(k in al for k in ["nut", "peanut"]):
                    flags["nut_free"] = True
            # lifestyle_tags drives vegan/vegetarian recipe filtering
            # (was incorrectly reading "dietary_preferences" which doesn't exist)
            for tag in getattr(member, "lifestyle_tags", []):
                tl = tag.value if hasattr(tag, "value") else str(tag)
                if tl == "vegan":       flags["vegan"]      = True; flags["vegetarian"] = True
                if tl == "vegetarian":  flags["vegetarian"] = True
                if tl == "keto":        flags["low_carb"]   = True
        return flags

    def _household_dietary_identity(self) -> Optional[str]:
        """
        Return the most restrictive dietary identity across all household members.

        Priority (most → least restrictive): vegan > vegetarian > pescatarian
        > keto > paleo > whole30 > None (omnivore).

        If any member is vegan the whole plan becomes vegan — safety-first. This
        matches the Sincere Strategy: the strictest valid constraint always wins.

        Phase 2: per-member meal differentiation (different meals per member)
        will support mixed-identity households. Pilot: one plan fits all.
        """
        PRIORITY = ["vegan", "vegetarian", "pescatarian", "keto", "paleo", "whole30"]
        all_tags: set[str] = set()
        for member in self.household.members:
            for tag in getattr(member, "lifestyle_tags", []):
                all_tags.add(tag.value if hasattr(tag, "value") else str(tag))
        for identity in PRIORITY:
            if identity in all_tags:
                return identity
        return None   # omnivore — all protein-category sale items are valid

    def _sale_affinity_score(self, recipe: dict, sale_names_lower: set[str]) -> int:
        """
        Count how many non-pantry recipe ingredients are currently on sale.

        Higher score = better alignment with this week's flyer = preferred choice.
        Used as tiebreaker when multiple recipes pass protein + cuisine filters.

        Pilot: substring matching (same heuristic as _build_cart).
        Phase 2: USDA FDC ID matching for exact ingredient-to-sale-item alignment.
        """
        score = 0
        for ing in recipe.get("ingredients", []):
            if ing.get("pantry_stable"):
                continue   # pantry items don't affect sale affinity
            name = ing.get("name", "").lower()
            if any(name in sn or sn in name for sn in sale_names_lower):
                score += 1
        return score

    def assemble_week(
        self,
        hero_ingredients: list[ScoredIngredient],
        flyer_week: Optional[str] = None,
        grocer: Optional[str] = None,
        n_meals: Optional[int] = None,
        cuisine_prefs: Optional[list] = None,
        protein_prefs: Optional[list] = None,
        exclude_recipe_ids: Optional[list] = None,
    ) -> WeeklyPlan:
        """
        Build a weekly dinner plan from the supplied hero ingredients.

        n_meals overrides household.meals_per_week so the plan respects the
        user's weekly preference (e.g. 3 dinners vs 5) rather than the profile
        default.

        Ingredient distribution: each meal gets a focused subset (protein +
        2 sides) rather than the full hero pool. This keeps per-meal shopping
        lists tight. The full basket is still only bought once — shared
        ingredients appear across multiple meals.

        POC: ingredient subsets are heuristic (top protein + top 2 by value).
        PROD: recipe library assigns exact quantities per meal.
        """
        n = n_meals or self.household.meals_per_week or 5

        # Pantry: try to import from ui.state so the live household pantry
        # (including user customisations) informs cost calculations.
        # Falls back to an empty set so the heuristic path still works when
        # running the engine outside the Streamlit UI (tests, scripts, etc.).
        try:
            from ui.state import pantry_items as _pantry_items
            _pantry: frozenset = _pantry_items()
        except Exception:
            _pantry: frozenset = frozenset()

        plan = WeeklyPlan(
            household_name=self.household.household_name,
            flyer_week=flyer_week,
            grocer=grocer,
        )

        if not hero_ingredients or not self._safe_plugins:
            return plan

        # ── Query recipe library for this week ─────────────────────────────
        # Grab names of all sale items so we can match recipe proteins to what
        # is actually on sale. Dietary flags from the household profile apply
        # as hard filters (Sincere Strategy: safety before savings, always).
        candidate_recipes: list = []
        if _RECIPE_LIB:
            try:
                sale_names  = [s.ingredient.name for s in hero_ingredients]
                hh_flags    = self._dietary_flags()
                candidate_recipes = recipes_for_sale_items(
                    sale_item_names=sale_names,
                    proteins=protein_prefs or None,
                    cuisines=cuisine_prefs or None,
                    dietary_flags=hh_flags if hh_flags else None,
                    exclude_ids=exclude_recipe_ids or [],
                )
            except Exception:
                candidate_recipes = []

        # Sort hero ingredients into protein anchor + supporting cast
        priority = {"protein": 0, "produce": 1, "legume": 2, "grain": 3,
                    "dairy": 4, "pantry": 5, "frozen": 6, "other": 7}
        sorted_heroes = sorted(
            hero_ingredients,
            key=lambda s: priority.get(s.ingredient.category, 8),
        )
        proteins  = [s for s in sorted_heroes if s.ingredient.category == "protein"]
        supports  = [s for s in sorted_heroes if s.ingredient.category != "protein"]

        # ── Dietary identity protein pool filter ──────────────────────────────
        # For restricted identities (vegan, pescatarian, etc.) only sale proteins
        # whose names match the allowed keyword set become meal anchors.
        # Vegan/vegetarian households get a pantry fallback when no plant protein
        # is on sale this week (common — most flyers skew animal protein).
        identity = self._household_dietary_identity()
        if identity and identity in PROTEIN_POOL_FOR_IDENTITY:
            allowed_kws = PROTEIN_POOL_FOR_IDENTITY[identity]
            proteins = [
                s for s in proteins
                if any(kw in s.ingredient.name.lower() for kw in allowed_kws)
            ]
            # Pantry fallback for vegan/vegetarian when no on-sale plant protein
            if not proteins and identity in PLANT_PROTEIN_PANTRY_FALLBACK:
                try:
                    from .constraint_engine import IngredientCandidate
                    for fb in PLANT_PROTEIN_PANTRY_FALLBACK[identity]:
                        fake_ing = IngredientCandidate(
                            name=fb["name"],
                            usda_fdc_id=None,
                            allergens=[],
                            nutrition={},
                            sale_price_per_unit=fb["price"],
                            unit=fb["unit"],
                            standard_unit_weight_g=0.0,
                            category=fb["category"],
                            tags=["pantry_fallback"],
                        )
                        proteins.append(ScoredIngredient(
                            ingredient=fake_ing,
                            nutrition_score=0.0,
                            value_score=0.5,     # lower than real sale items
                            sale_savings_pct=0.0,
                            score_breakdown={"source": "pantry_fallback"},
                        ))
                except Exception:
                    pass   # fallback silently skipped if import fails

        # Pre-compute once — these are plan-level constants, not per-meal
        sale_names_lower    = {s.ingredient.name.lower() for s in hero_ingredients}
        cuisine_prefs_lower = {c.lower() for c in (cuisine_prefs or [])}

        # Track used format indices per plugin to avoid repeating names
        _plugin_format_idx: dict[str, int] = {}

        for day_index, day in enumerate(self.DEFAULT_DAYS[:n]):
            plugin_key = self._safe_plugins[day_index % len(self._safe_plugins)]
            plugin     = FLAVOR_PLUGINS[plugin_key]

            # Rotate protein anchor across meals; fall back to top hero
            anchor_ing = proteins[day_index % len(proteins)] if proteins else sorted_heroes[0]

            # Each meal: 1 protein + up to 2 support items (rotated so later
            # meals see different produce/grain pairs)
            offset     = day_index % max(len(supports), 1)
            meal_ings  = [anchor_ing]
            for k in range(2):
                idx = (offset + k) % len(supports) if supports else None
                if idx is not None and supports[idx] not in meal_ings:
                    meal_ings.append(supports[idx])

            # Advance format index for this plugin to avoid duplicate names
            fmt_idx = _plugin_format_idx.get(plugin_key, 0)
            _plugin_format_idx[plugin_key] = fmt_idx + 1

            # ── Recipe library match — 4-pass selection ────────────────────
            # Priority order:
            #   Pass 1: protein match + preferred cuisine + unused cuisine rotation
            #   Pass 2: protein match + unused cuisine (any cuisine)
            #   Pass 3: protein match, any cuisine (all cuisines exhausted)
            #   Pass 4 REMOVED: no longer fall back to arbitrary recipe match.
            #     If no protein match exists, use plugin/heuristic name instead.
            #     Reason: Pass 4 paired unrelated items (chimichangas → Mediterranean
            #     Chicken) which erodes user trust. Better to show a heuristic
            #     meal name than a wrong recipe match.
            #     POC. PROD: expand protein synonym table to catch edge cases.
            #
            # Sale affinity (how many recipe ingredients are on sale this week)
            # is used as a tiebreaker within each pass — same protein/cuisine
            # match prefers the recipe that costs less to execute this week.
            recipe      = None
            recipe_ings: list = []
            used_ids      = {m.recipe_id for m in plan.meals if m.recipe_id}
            used_cuisines = {m.flavor_plugin for m in plan.meals}
            anchor_name   = anchor_ing.ingredient.name.lower()

            def _protein_match(r: dict) -> bool:
                pp = r.get("primary_protein", "").lower()
                return pp in anchor_name or anchor_name in pp or any(
                    w in pp for w in anchor_name.split()
                )

            def _cuisine_preferred(r: dict) -> bool:
                """True when the recipe's cuisine is in the household's preference list."""
                if not cuisine_prefs_lower:
                    return True   # no preference set → all cuisines are welcome
                return r.get("cuisine", "").lower() in cuisine_prefs_lower

            if candidate_recipes:
                # Sort unused candidates by sale affinity descending so earlier
                # passes automatically pick the most on-sale-aligned recipe first.
                unused = [
                    r for r in candidate_recipes if r["id"] not in used_ids
                ]
                unused.sort(
                    key=lambda r: -self._sale_affinity_score(r, sale_names_lower)
                )

                # Pass 1: protein match + preferred cuisine + unused cuisine rotation
                for r in unused:
                    if _protein_match(r) and _cuisine_preferred(r)                             and r.get("cuisine", "").lower() not in used_cuisines:
                        recipe = r
                        break

                # Pass 2: protein match + unused cuisine (any cuisine)
                if recipe is None:
                    for r in unused:
                        if _protein_match(r)                                 and r.get("cuisine", "").lower() not in used_cuisines:
                            recipe = r
                            break

                # Pass 3: protein match, any cuisine (all cuisine slots exhausted)
                if recipe is None:
                    for r in unused:
                        if _protein_match(r):
                            recipe = r
                            break

                # Pass 4 removed — if no protein match, fall through to plugin heuristic
                # if recipe is None and unused: recipe = unused[0]  # REMOVED

            if recipe is not None:
                meal_name   = recipe["name"]
                recipe_id   = recipe["id"]
                recipe_ings = get_recipe_shopping_items(recipe) if _RECIPE_LIB else []
            else:
                meal_name   = self._compose_meal_name(plugin, meal_ings, fmt_idx)
                recipe_id   = None
                recipe_ings = []

            # Cost calculation runs after recipe match so we have real quantities.
            # Passes matched recipe (or None) and household pantry to the cost engine.
            cost_per_serving = self._estimate_cost_per_serving(
                meal_ings, n,
                recipe=recipe,
                pantry=_pantry,
            )

            meal = Meal(
                day=day,
                slot=self.DEFAULT_SLOT,
                name=meal_name,
                ingredients=meal_ings,
                flavor_plugin=plugin_key,
                pantry_seasonings=plugin["pantry_seasonings"],
                method_hint=plugin["method_hint"],
                cost_per_serving=round(cost_per_serving, 2),
                servings=self.household.servings_per_meal,
                safety_attestation=[m.name for m in self.household.members],
                recipe_id=recipe_id,
                recipe_ingredients=recipe_ings,
            )
            plan.meals.append(meal)

        return plan

    def _compose_meal_name(
        self,
        plugin: dict,
        ingredients: list[ScoredIngredient],
        fmt_idx: int = 0,
    ) -> str:
        """
        Compose a varied meal name from the plugin's format templates.
        Uses fmt_idx to rotate through templates so the same plugin doesn't
        repeat the same name twice in a week.
        """
        anchor = ingredients[0].ingredient.name if ingredients else "Dinner"

        # Shorten long ingredient names to a recognisable word
        short = anchor
        name_lower = anchor.lower()
        if "chicken" in name_lower:   short = "Chicken"
        elif "beef"   in name_lower:  short = "Beef"
        elif "pork"   in name_lower:  short = "Pork"
        elif "salmon" in name_lower:  short = "Salmon"
        elif "shrimp" in name_lower:  short = "Shrimp"
        elif "turkey" in name_lower:  short = "Turkey"
        elif "egg"    in name_lower:  short = "Egg"
        elif "tofu"   in name_lower:  short = "Tofu"
        elif len(anchor.split()) > 2: short = anchor.split()[-1].capitalize()

        formats = plugin.get("meal_formats", ["{protein} Dinner"])
        template = formats[fmt_idx % len(formats)]
        return template.format(protein=short)

    # ── Category price estimates for non-sale recipe ingredients ─────────────
    # These are conservative national averages used when a recipe ingredient
    # isn't on sale at any configured store this week.
    # Pilot: hard-coded estimates. Phase 2: live prices from Kroger API / Flipp.
    # Sale-weighted estimates for non-hero ingredients — based on typical
    # Charlottesville store pricing (Kroger/Food Lion/Aldi on a normal week).
    # Hero proteins are anchored by the actual sale circular price, so these
    # estimates only cover supporting cast: veg, grains, canned goods, dairy.
    # Pilot: validated against real Charlottesville receipts May 2026.
    # Phase 2: replace with live Kroger API prices for every ingredient.
    CATEGORY_PRICE_ESTIMATES: dict[str, float] = {
        "protein":  3.50,   # $/lb — store brand / sale avg (chicken ~$1.49-2.99, pork ~$2.49)
        "produce":  0.99,   # $/unit or bunch — Aldi/Food Lion typical
        "grain":    1.50,   # $/package — rice, pasta, store brand
        "dairy":    2.00,   # $/unit — eggs, milk, butter store brand
        "canned":   0.89,   # $/can — store brand beans, tomatoes, broth
        "legume":   1.00,   # $/can or bag
        "frozen":   2.50,   # $/package — store brand veg, etc.
        "pantry":   0.05,   # per-use — oil, vinegar, soy sauce splash
        "spice":    0.02,   # per-use — salt, pepper, garlic powder pinch
        "other":    1.25,
    }

    def _estimate_cost_per_serving(
        self,
        hero_ingredients: list[ScoredIngredient],
        n_meals: int = 1,
        recipe: Optional[dict] = None,
        pantry: Optional[frozenset] = None,
    ) -> float:
        """
        Estimate cost per serving for a single meal.

        When a recipe is matched:
          - pantry_stable ingredients → $0 (assumed on hand)
          - ingredients matching a sale hero → use actual sale price × recipe qty
          - remaining ingredients → CATEGORY_PRICE_ESTIMATES lookup
        When no recipe matched (flavor-plugin fallback):
          - heuristic 150g/serving against sale prices, shared across n_meals

        Pilot: recipe quantity conversion uses g as the common unit.
               Non-gram quantities (tbsp, tsp, cup) use fixed gram conversions.
        Phase 2: USDA density table replaces the fixed conversion map.
        """
        servings = max(self.household.servings_per_meal, 1)
        pantry_set = pantry or frozenset()

        # ── Recipe-based cost (accurate path) ─────────────────────────────
        if recipe:
            # Build a lookup of sale items by normalised name for quick matching
            sale_lookup: dict[str, ScoredIngredient] = {}
            for s in hero_ingredients:
                sale_lookup[s.ingredient.name.lower()] = s
                # Also index by the first word (e.g. "chicken" matches "chicken thighs")
                first = s.ingredient.name.lower().split()[0]
                sale_lookup.setdefault(first, s)

            # Unit → approximate grams conversion for cost normalisation
            UNIT_TO_G: dict[str, float] = {
                "g": 1.0, "kg": 1000.0, "oz": 28.35, "lb": 453.6,
                "ml": 1.0, "l": 1000.0,
                "tbsp": 15.0, "tsp": 5.0, "cup": 240.0,
                "clove": 5.0, "piece": 100.0, "whole": 150.0,
                "can": 400.0, "bunch": 100.0, "stalk": 60.0,
                "slice": 30.0, "sprig": 2.0, "pinch": 1.0,
            }

            total = 0.0
            for ing_dict in recipe.get("ingredients", []):
                name       = ing_dict.get("name", "").lower().strip()
                qty        = float(ing_dict.get("qty", 1))
                unit       = ing_dict.get("unit", "g").lower()
                is_pantry  = ing_dict.get("pantry_stable", False)
                category   = ing_dict.get("category", "other")

                # Pantry items cost nothing — household already has them
                if is_pantry or name in pantry_set:
                    continue

                # Try to match against a sale hero ingredient
                matched_sale = None
                for key in (name, name.split()[0] if name else ""):
                    if key in sale_lookup:
                        matched_sale = sale_lookup[key]
                        break

                if matched_sale is not None:
                    # Use actual sale price scaled to recipe quantity
                    ing       = matched_sale.ingredient
                    weight_g  = ing.standard_unit_weight_g or 453.6  # default 1 lb
                    qty_g     = qty * UNIT_TO_G.get(unit, 100.0)
                    cost      = (ing.sale_price_per_unit / weight_g) * qty_g
                else:
                    # Estimate from category — scale by a notional 200g portion
                    qty_g     = qty * UNIT_TO_G.get(unit, 100.0)
                    price_per_g = self.CATEGORY_PRICE_ESTIMATES.get(category, 2.0) / 453.6
                    cost      = price_per_g * qty_g

                total += cost

            return round(total / servings, 2)

        # ── Heuristic fallback (no recipe matched) ─────────────────────────
        # Used when the recipe library has no match for this week's hero ingredients.
        # Same logic as before: 150g/serving, shared items split across meals.
        total = 0.0
        for s in hero_ingredients:
            ing            = s.ingredient
            weight_g       = ing.standard_unit_weight_g or 100
            price_per_100g = (ing.sale_price_per_unit / weight_g) * 100
            if ing.category == "protein":
                share = 1.0
            else:
                share = 1.0 / max(n_meals, 1)
            total += price_per_100g * 1.5 * share
        return round(total / servings, 2)
