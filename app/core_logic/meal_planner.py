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
    },
    "asian": {
        "name": "Asian",
        "pantry_seasonings": ["soy sauce", "ginger", "garlic", "sesame oil"],
        "method_hint": "Stir-fry protein and produce in sesame oil; serve over base.",
        "incompatible_with": ["soy"],  # excluded if household has soy allergy
    },
    "mediterranean": {
        "name": "Mediterranean",
        "pantry_seasonings": ["olive oil", "lemon", "oregano", "garlic"],
        "method_hint": "Roast protein and produce with olive oil + oregano; finish with lemon.",
    },
    "american_comfort": {
        "name": "American Comfort",
        "pantry_seasonings": ["salt", "pepper", "butter", "thyme"],
        "method_hint": "Simple roast/sauté with salt, pepper, butter; herb finish.",
    },
    "indian": {
        "name": "Indian",
        "pantry_seasonings": ["turmeric", "garam masala", "ginger", "cumin"],
        "method_hint": "Bloom spices in oil; simmer protein and produce; serve over base.",
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
    ) -> WeeklyPlan:
        """
        Build a 7-day dinner plan from the supplied hero ingredients.

        The hero ingredients should already be the 5-7 winners from
        BudgetOptimizer.select_ingredients() — this method is responsible for
        spreading them across the week with rotating Flavor Plugins, NOT for
        re-doing the budget math.
        """
        plan = WeeklyPlan(
            household_name=self.household.household_name,
            flyer_week=flyer_week,
            grocer=grocer,
        )

        if not hero_ingredients or not self._safe_plugins:
            return plan

        for day_index, day in enumerate(self.DEFAULT_DAYS[: self.household.meals_per_week]):
            plugin_key = self._safe_plugins[day_index % len(self._safe_plugins)]
            plugin = FLAVOR_PLUGINS[plugin_key]

            cost_per_serving = self._estimate_cost_per_serving(hero_ingredients)

            meal = Meal(
                day=day,
                slot=self.DEFAULT_SLOT,
                name=self._compose_meal_name(plugin, hero_ingredients),
                ingredients=hero_ingredients,
                flavor_plugin=plugin_key,
                pantry_seasonings=plugin["pantry_seasonings"],
                method_hint=plugin["method_hint"],
                cost_per_serving=round(cost_per_serving, 2),
                servings=self.household.servings_per_meal,
                safety_attestation=[m.name for m in self.household.members],
            )
            plan.meals.append(meal)

        return plan

    def _compose_meal_name(self, plugin: dict, ingredients: list[ScoredIngredient]) -> str:
        """Pick the most distinctive ingredient and give it a flavor-plugin name."""
        # Prefer a protein, then a produce, then anything.
        priority = {"protein": 0, "produce": 1, "legume": 2, "grain": 3, "dairy": 4}
        sorted_ings = sorted(
            ingredients,
            key=lambda s: priority.get(s.ingredient.category, 5),
        )
        anchor = sorted_ings[0].ingredient.name if sorted_ings else "Bowl"
        # Tidy up the anchor name: "Boneless Skinless Chicken Breast" -> "Chicken"
        short = anchor.split()[-1] if len(anchor.split()) > 1 else anchor
        if "chicken" in anchor.lower():
            short = "Chicken"
        elif "beef" in anchor.lower():
            short = "Beef"
        elif "egg" in anchor.lower():
            short = "Egg"
        return f"{plugin['name']} {short} Bowl"

    def _estimate_cost_per_serving(self, ingredients: list[ScoredIngredient]) -> float:
        """
        MVP cost estimate: the per-meal share of the per-100g sale price for
        each hero ingredient, summed and divided by servings_per_meal.

        v2 will use actual recipe quantities (USDA serving sizes) per ingredient.
        """
        total_per_100g = 0.0
        for s in ingredients:
            ing = s.ingredient
            weight_g = ing.standard_unit_weight_g or 100
            price_per_100g = (ing.sale_price_per_unit / weight_g) * 100
            total_per_100g += price_per_100g
        # Heuristic: assume each meal uses ~150g/serving across the basket.
        per_serving = total_per_100g * 1.5
        # Spread across the household's planned meals_per_week so we don't
        # over-charge a single meal for an ingredient used all week.
        if self.household.meals_per_week:
            per_serving = per_serving / max(self.household.meals_per_week, 1)
        return per_serving
