"""
profile_schema.py
-----------------
Pydantic v2 models for household and member dietary profiles.
These are the first-class inputs to the constraint engine.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LifestyleTag(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    HALAL = "halal"
    KOSHER = "kosher"
    WHOLE30 = "whole30"
    LOW_FODMAP = "low-fodmap"
    PALEO = "paleo"
    KETO = "keto"


class Diagnosis(str, Enum):
    CELIAC = "celiac"
    TYPE1_DIABETES = "type1_diabetes"
    TYPE2_DIABETES = "type2_diabetes"
    CKD = "ckd"                    # Chronic Kidney Disease
    PKU = "pku"                    # Phenylketonuria
    GERD = "gerd"
    IBS_LOW_FODMAP = "ibs_low_fodmap"
    CROHNS = "crohns"
    HYPERTENSION = "hypertension"


class MemberProfile(BaseModel):
    name: str
    age: Optional[int] = None
    allergies: list[str] = Field(
        default_factory=list,
        description="Top-14 allergen keys, e.g. ['peanuts', 'milk']"
    )
    diagnoses: list[Diagnosis] = Field(
        default_factory=list,
        description="Medical diagnoses that require dietary accommodation"
    )
    lifestyle_tags: list[LifestyleTag] = Field(
        default_factory=list,
        description="Dietary lifestyle preferences (vegan, halal, etc.)"
    )
    custom_exclusions: list[str] = Field(
        default_factory=list,
        description="Free-text ingredient names this member won't eat"
    )


class GrocerPreference(BaseModel):
    chain_name: str                          # "Kroger", "Publix", "Aldi", etc.
    store_id: Optional[str] = None           # specific location ID if known
    rewards_program_enrolled: bool = False
    delivery_preferred: bool = False
    delivery_zip: Optional[str] = None


class HouseholdProfile(BaseModel):
    household_name: str
    members: list[MemberProfile]
    weekly_budget_usd: float = Field(gt=0)
    servings_per_meal: int = Field(default=4, ge=1)
    meals_per_week: int = Field(default=7, ge=1)
    grocer: Optional[GrocerPreference] = None

    @property
    def budget_per_meal(self) -> float:
        return self.weekly_budget_usd / self.meals_per_week

    @property
    def budget_per_serving(self) -> float:
        return self.budget_per_meal / self.servings_per_meal


# --- Example household for testing ---
EXAMPLE_HOUSEHOLD = HouseholdProfile(
    household_name="The Martinez Family",
    weekly_budget_usd=120.00,
    servings_per_meal=4,
    meals_per_week=7,
    members=[
        MemberProfile(
            name="Sofia",
            age=38,
            diagnoses=[Diagnosis.TYPE2_DIABETES],
            lifestyle_tags=[LifestyleTag.VEGETARIAN],
        ),
        MemberProfile(
            name="Marco",
            age=40,
            allergies=["peanuts", "tree_nuts"],
        ),
        MemberProfile(
            name="Lucia",
            age=9,
            allergies=["milk"],
            custom_exclusions=["Brussels sprouts", "mushrooms"],
        ),
    ],
    grocer=GrocerPreference(
        chain_name="Kroger",
        rewards_program_enrolled=True,
        delivery_preferred=False,
    ),
)
