"""
constraint_engine.py
--------------------
The heart of WhollyFare's Sincere Strategy.

Filters a pool of available (on-sale) ingredients against a household's
complete dietary profile. Every exclusion is logged with a reason so the
dashboard can show users *exactly* why an ingredient was removed — no black boxes.
"""

from dataclasses import dataclass, field
from typing import Optional
from .profile_schema import HouseholdProfile, MemberProfile


@dataclass
class IngredientCandidate:
    name: str
    usda_fdc_id: Optional[str]
    allergens: list[str]          # e.g. ["milk", "soy"]
    nutrition: dict               # {"calories": 52, "protein_g": 1.2, ...}
    sale_price_per_unit: float
    unit: str                     # "lb", "oz", "each"
    standard_unit_weight_g: float # for per-100g nutrition math
    category: str                 # "produce", "protein", "grain", "dairy", "legume"
    tags: list[str]               # ["vegan", "gluten-free", "low-fodmap", ...]


@dataclass
class FilterResult:
    passed: list[IngredientCandidate] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)  # {ingredient, reason, member}

    def reject(self, ingredient: IngredientCandidate, reason: str, member: str):
        self.rejected.append({
            "ingredient": ingredient.name,
            "reason": reason,
            "triggered_by_member": member,
        })


class ConstraintEngine:
    """
    Applies the union of all household member constraints to a candidate
    ingredient pool. The MVP uses a rule-based approach; v2 will delegate
    to OR-Tools for combinatorial optimization.
    """

    # Top-14 EU allergens + common extras
    KNOWN_ALLERGENS = {
        "peanuts", "tree_nuts", "milk", "eggs", "wheat", "soy",
        "fish", "shellfish", "sesame", "mustard", "celery",
        "lupin", "molluscs", "sulphites",
    }

    # Diagnosis → ingredients/tags to exclude
    DIAGNOSIS_EXCLUSIONS: dict[str, dict] = {
        "celiac": {
            "tags_exclude": ["contains-gluten"],
            "allergens_exclude": ["wheat"],
            "reason": "Celiac disease requires strict gluten elimination",
        },
        "type2_diabetes": {
            "tags_exclude": ["high-glycemic", "added-sugar"],
            "reason": "Type 2 diabetes management requires low-GI foods",
        },
        "ckd": {
            "tags_exclude": ["high-potassium", "high-phosphorus", "high-sodium"],
            "reason": "Chronic Kidney Disease requires restricted minerals",
        },
        "pku": {
            "tags_exclude": ["high-phenylalanine"],
            "allergens_exclude": ["aspartame"],
            "reason": "PKU requires strict phenylalanine restriction",
        },
        "gerd": {
            "tags_exclude": ["acidic", "spicy", "high-fat"],
            "reason": "GERD management avoids acid/spice triggers",
        },
        "ibs_low_fodmap": {
            "tags_exclude": ["high-fodmap"],
            "reason": "IBS Low-FODMAP protocol",
        },
    }

    def __init__(self, household: HouseholdProfile):
        self.household = household
        # Merge all member constraints into unified sets
        self._merged_allergens: set[str] = set()
        self._merged_diagnosis_rules: list[dict] = []
        self._merged_exclusions: set[str] = set()  # free-text ingredient names
        self._merged_required_tags: set[str] = set()  # vegan, halal, etc.
        self._build_merged_constraints()

    def _build_merged_constraints(self):
        for member in self.household.members:
            self._merged_allergens.update(member.allergies)
            for diagnosis in member.diagnoses:
                rules = self.DIAGNOSIS_EXCLUSIONS.get(diagnosis)
                if rules:
                    self._merged_diagnosis_rules.append(
                        {"member": member.name, "diagnosis": diagnosis, **rules}
                    )
            self._merged_exclusions.update(
                ex.lower() for ex in member.custom_exclusions
            )
            self._merged_required_tags.update(member.lifestyle_tags)

    def filter(self, candidates: list[IngredientCandidate]) -> FilterResult:
        result = FilterResult()

        for ing in candidates:
            rejected = False

            # 1. Allergen check
            for allergen in ing.allergens:
                if allergen in self._merged_allergens:
                    triggering_member = self._find_allergen_owner(allergen)
                    result.reject(
                        ing,
                        reason=f"Contains allergen: {allergen}",
                        member=triggering_member,
                    )
                    rejected = True
                    break

            if rejected:
                continue

            # 2. Diagnosis-based tag exclusions
            for rule in self._merged_diagnosis_rules:
                excluded_tags = rule.get("tags_exclude", [])
                excluded_allergens = rule.get("allergens_exclude", [])
                tag_hit = any(t in ing.tags for t in excluded_tags)
                allergen_hit = any(a in ing.allergens for a in excluded_allergens)
                if tag_hit or allergen_hit:
                    result.reject(
                        ing,
                        reason=rule["reason"],
                        member=rule["member"],
                    )
                    rejected = True
                    break

            if rejected:
                continue

            # 3. Custom ingredient exclusions (free-text)
            if ing.name.lower() in self._merged_exclusions:
                result.reject(
                    ing,
                    reason="User-specified exclusion",
                    member="household",
                )
                continue

            # 4. Lifestyle / dietary tag requirements (vegan, halal, etc.)
            for required_tag in self._merged_required_tags:
                if required_tag not in ing.tags:
                    result.reject(
                        ing,
                        reason=f"Does not meet lifestyle requirement: {required_tag}",
                        member="household",
                    )
                    rejected = True
                    break

            if not rejected:
                result.passed.append(ing)

        return result

    def _find_allergen_owner(self, allergen: str) -> str:
        for member in self.household.members:
            if allergen in member.allergies:
                return member.name
        return "household"
