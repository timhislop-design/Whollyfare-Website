"""
budget_optimizer.py
-------------------
Scores and ranks constraint-cleared ingredients by nutrition value per
sale dollar. The goal: maximize dietary quality within the weekly budget.

Scoring philosophy (Sincere Strategy):
  - We never boost an ingredient's score because of a commercial relationship.
  - Score is purely a function of nutrition density and current sale price.
  - Users can inspect every ingredient's score breakdown in the dashboard.
"""

from dataclasses import dataclass
from core_logic.constraint_engine import IngredientCandidate


@dataclass
class ScoredIngredient:
    ingredient: IngredientCandidate
    nutrition_score: float       # composite nutrient density (0–100)
    value_score: float           # nutrition_score / sale_price_per_100g
    sale_savings_pct: float      # % savings vs. estimated regular price
    score_breakdown: dict        # transparent breakdown for dashboard display


# Nutrient weights for composite score (MVP — will be tunable per diagnosis in v2)
NUTRIENT_WEIGHTS = {
    "protein_g": 2.0,
    "fiber_g": 1.8,
    "vitamin_c_mg": 0.8,
    "iron_mg": 1.0,
    "calcium_mg": 0.7,
    "potassium_mg": 0.6,
    "saturated_fat_g": -1.5,    # penalty
    "added_sugar_g": -2.0,      # penalty
    "sodium_mg": -0.5,          # mild penalty
}

# Per-100g reference maxes for normalization (rough USDA population averages)
NUTRIENT_REF_MAX = {
    "protein_g": 30,
    "fiber_g": 10,
    "vitamin_c_mg": 100,
    "iron_mg": 5,
    "calcium_mg": 300,
    "potassium_mg": 500,
    "saturated_fat_g": 15,
    "added_sugar_g": 25,
    "sodium_mg": 800,
}


class BudgetOptimizer:
    def __init__(self, weekly_budget: float, servings_per_meal: int, meals_per_week: int):
        self.weekly_budget = weekly_budget
        self.servings_per_meal = servings_per_meal
        self.meals_per_week = meals_per_week

    def score(self, ingredients: list[IngredientCandidate]) -> list[ScoredIngredient]:
        scored = []
        for ing in ingredients:
            nutrition_score, breakdown = self._nutrition_score(ing)
            price_per_100g = self._price_per_100g(ing)
            value_score = nutrition_score / max(price_per_100g, 0.01)
            scored.append(ScoredIngredient(
                ingredient=ing,
                nutrition_score=round(nutrition_score, 2),
                value_score=round(value_score, 2),
                sale_savings_pct=ing.nutrition.get("sale_savings_pct", 0.0),
                score_breakdown=breakdown,
            ))
        return sorted(scored, key=lambda s: s.value_score, reverse=True)

    def _nutrition_score(self, ing: IngredientCandidate) -> tuple[float, dict]:
        score = 0.0
        breakdown = {}
        nutrition = ing.nutrition

        for nutrient, weight in NUTRIENT_WEIGHTS.items():
            value = nutrition.get(nutrient, 0.0)
            ref_max = NUTRIENT_REF_MAX.get(nutrient, 1)
            normalized = min(value / ref_max, 1.0)
            contribution = normalized * weight * 10  # scale to ~0-100 space
            score += contribution
            breakdown[nutrient] = round(contribution, 3)

        return max(score, 0), breakdown

    def _price_per_100g(self, ing: IngredientCandidate) -> float:
        weight_g = ing.standard_unit_weight_g
        if weight_g <= 0:
            return ing.sale_price_per_unit
        return (ing.sale_price_per_unit / weight_g) * 100

    def select_ingredients(
        self,
        scored: list[ScoredIngredient],
        min_count: int = 5,
        max_count: int = 7,
        category_balance: bool = True,
    ) -> list[ScoredIngredient]:
        """
        Select 5–7 ingredients for a weekly plan, respecting category balance
        so a plan isn't all produce or all protein.
        """
        if not category_balance:
            return scored[:max_count]

        # Target category distribution (MVP heuristic)
        targets = {
            "produce": 2,
            "protein": 2,
            "grain": 1,
            "legume": 1,
            "other": 1,
        }
        selected = []
        category_counts: dict[str, int] = {}

        for s in scored:
            cat = s.ingredient.category
            bucket = cat if cat in targets else "other"
            current = category_counts.get(bucket, 0)
            if current < targets.get(bucket, 1):
                selected.append(s)
                category_counts[bucket] = current + 1
            if len(selected) >= max_count:
                break

        # Backfill if we couldn't hit min_count with balanced selection
        if len(selected) < min_count:
            remaining = [s for s in scored if s not in selected]
            selected.extend(remaining[: min_count - len(selected)])

        return selected
