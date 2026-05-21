"""
core_logic — The constraint engine, scorer, and meal assembler.

This is the heart of WhollyFare's "Sincere Strategy": every recommendation
that comes out of this package is auditable and free of commercial influence.
"""

from .profile_schema import (
    HouseholdProfile,
    MemberProfile,
    GrocerPreference,
    Diagnosis,
    LifestyleTag,
)
from .constraint_engine import (
    ConstraintEngine,
    IngredientCandidate,
    FilterResult,
)
from .budget_optimizer import BudgetOptimizer, ScoredIngredient
from .meal_planner import MealPlanner, Meal, WeeklyPlan

__all__ = [
    "HouseholdProfile",
    "MemberProfile",
    "GrocerPreference",
    "Diagnosis",
    "LifestyleTag",
    "ConstraintEngine",
    "IngredientCandidate",
    "FilterResult",
    "BudgetOptimizer",
    "ScoredIngredient",
    "MealPlanner",
    "Meal",
    "WeeklyPlan",
]
