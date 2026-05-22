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

    def assemble_week(
        self,
        hero_ingredients: list[ScoredIngredient],
        flyer_week: Optional[str] = None,
        grocer: Optional[str] = None,
        n_meals: Optional[int] = None,
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

        plan = WeeklyPlan(
            household_name=self.household.household_name,
            flyer_week=flyer_week,
            grocer=grocer,
        )

        if not hero_ingredients or not self._safe_plugins:
            return plan

        # Sort hero ingredients into protein anchor + supporting cast
        priority = {"protein": 0, "produce": 1, "legume": 2, "grain": 3,
                    "dairy": 4, "pantry": 5, "frozen": 6, "other": 7}
        sorted_heroes = sorted(
            hero_ingredients,
            key=lambda s: priority.get(s.ingredient.category, 8),
        )
        proteins  = [s for s in sorted_heroes if s.ingredient.category == "protein"]
        supports  = [s for s in sorted_heroes if s.ingredient.category != "protein"]

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

            cost_per_serving = self._estimate_cost_per_serving(meal_ings, n)

            # Advance format index for this plugin to avoid duplicate names
            fmt_idx = _plugin_format_idx.get(plugin_key, 0)
            _plugin_format_idx[plugin_key] = fmt_idx + 1

            meal = Meal(
                day=day,
                slot=self.DEFAULT_SLOT,
                name=self._compose_meal_name(plugin, meal_ings, fmt_idx),
                ingredients=meal_ings,
                flavor_plugin=plugin_key,
                pantry_seasonings=plugin["pantry_seasonings"],
                method_hint=plugin["method_hint"],
                cost_per_serving=round(cost_per_serving, 2),
                servings=self.household.servings_per_meal,
                safety_attestation=[m.name for m in self.household.members],
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

    def _estimate_cost_per_serving(
        self,
        ingredients: list[ScoredIngredient],
        n_meals: int = 1,
    ) -> float:
        """
        Estimate cost per serving for a single meal's ingredient subset.

        Each ingredient in the list is assumed to be used primarily by this
        meal (protein) or shared across 2-3 meals (produce/grain). The
        n_meals parameter spreads shared-item cost across the week.

        POC: heuristic 150g/serving. PROD: USDA recipe quantities per item.
        """
        total = 0.0
        for s in ingredients:
            ing      = s.ingredient
            weight_g = ing.standard_unit_weight_g or 100
            price_per_100g = (ing.sale_price_per_unit / weight_g) * 100
            # Proteins are meal-specific (full cost this meal).
            # Produce/grain are shared — split across meals that use them.
            if ing.category == "protein":
                share = 1.0
            else:
                share = 1.0 / max(n_meals, 1)
            total += price_per_100g * 1.5 * share
        return total / max(self.household.servings_per_meal, 1)
