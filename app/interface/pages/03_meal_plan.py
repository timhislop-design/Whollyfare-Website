"""
03_meal_plan.py — Generate the week's meal plan using the loaded flyer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core_logic.budget_optimizer import BudgetOptimizer  # noqa: E402
from core_logic.constraint_engine import ConstraintEngine  # noqa: E402
from core_logic.meal_planner import MealPlanner  # noqa: E402
from core_logic.profile_schema import (  # noqa: E402
    Diagnosis,
    GrocerPreference,
    HouseholdProfile,
    LifestyleTag,
    MemberProfile,
)

st.set_page_config(page_title="My Meal Plan · WhollyFare", page_icon="🍽️", layout="wide")
st.title("🍽️ My Meal Plan")

household_dict = st.session_state.get("household")
candidates = st.session_state.get("candidates")

if not household_dict:
    st.warning("Please complete your Family Profile first.")
    st.page_link("pages/01_profile_setup.py", label="→ Family Profile")
    st.stop()
if not candidates:
    st.warning("Please load this week's grocer flyer first.")
    st.page_link("pages/02_grocer_connect.py", label="→ Connect Grocer")
    st.stop()

# ── Translate session-state dicts into typed schema objects ───────────────────

ALLERGEN_KEY_MAP = {
    "Peanuts": "peanuts", "Tree Nuts": "tree_nuts", "Milk": "milk",
    "Eggs": "eggs", "Wheat / Gluten": "wheat", "Soy": "soy",
    "Fish": "fish", "Shellfish": "shellfish", "Sesame": "sesame",
    "Mustard": "mustard", "Celery": "celery", "Lupin": "lupin",
    "Molluscs": "molluscs", "Sulphites": "sulphites",
    "Alpha-gal (mammalian meat)": "alpha_gal",
}
DIAGNOSIS_KEY_MAP = {
    "Celiac Disease": Diagnosis.CELIAC,
    "Type 1 Diabetes": Diagnosis.TYPE1_DIABETES,
    "Type 2 Diabetes": Diagnosis.TYPE2_DIABETES,
    "Chronic Kidney Disease (CKD)": Diagnosis.CKD,
    "PKU": Diagnosis.PKU,
    "GERD / Acid Reflux": Diagnosis.GERD,
    "IBS (Low-FODMAP)": Diagnosis.IBS_LOW_FODMAP,
    "Crohn's Disease": Diagnosis.CROHNS,
    "Hypertension": Diagnosis.HYPERTENSION,
}
LIFESTYLE_KEY_MAP = {
    "Vegan": LifestyleTag.VEGAN, "Vegetarian": LifestyleTag.VEGETARIAN,
    "Halal": LifestyleTag.HALAL, "Kosher": LifestyleTag.KOSHER,
    "Whole30": LifestyleTag.WHOLE30, "Low-FODMAP": LifestyleTag.LOW_FODMAP,
    "Paleo": LifestyleTag.PALEO, "Keto": LifestyleTag.KETO,
}

members: list[MemberProfile] = []
for m in household_dict["members"]:
    if not m.get("name"):
        continue
    members.append(MemberProfile(
        name=m["name"],
        age=int(m["age"]) if str(m.get("age", "")).isdigit() else None,
        allergies=[ALLERGEN_KEY_MAP.get(a, a.lower()) for a in m["allergies"]],
        diagnoses=[DIAGNOSIS_KEY_MAP[d] for d in m["diagnoses"] if d in DIAGNOSIS_KEY_MAP],
        lifestyle_tags=[LIFESTYLE_KEY_MAP[t] for t in m["lifestyle"] if t in LIFESTYLE_KEY_MAP],
        custom_exclusions=[s.strip() for s in m.get("exclusions", "").split(",") if s.strip()],
    ))

if not members:
    st.error("Add at least one named family member on the profile page first.")
    st.stop()

primary_grocer = next(
    (g for g in household_dict["grocers"] if g.get("is_primary")),
    household_dict["grocers"][0],
)

household = HouseholdProfile(
    household_name=household_dict.get("name") or "Your Household",
    weekly_budget_usd=household_dict["weekly_budget"],
    servings_per_meal=int(household_dict["servings"]),
    meals_per_week=int(household_dict["meals_per_week"]),
    members=members,
    grocer=GrocerPreference(
        chain_name=primary_grocer["chain"],
        store_id=primary_grocer.get("store_id_or_address") or None,
        rewards_program_enrolled=primary_grocer.get("rewards_enrolled", False),
        delivery_preferred=primary_grocer.get("delivery", False),
    ),
)

# ── Run the pipeline ──────────────────────────────────────────────────────────

engine = ConstraintEngine(household)
result = engine.filter(candidates)

st.subheader(f"Constraint Filter Results")
m1, m2 = st.columns(2)
m1.metric("Ingredients passed", len(result.passed))
m2.metric("Ingredients rejected", len(result.rejected))

if result.rejected:
    with st.expander("🔍 Why were items rejected? (Sincere Strategy: nothing is hidden)"):
        for r in result.rejected:
            st.markdown(
                f"- **{r['ingredient']}** — {r['reason']} "
                f"(triggered by: *{r['triggered_by_member']}*)"
            )

if not result.passed:
    st.error("No sale items match every household constraint this week.")
    st.stop()

optimizer = BudgetOptimizer(
    weekly_budget=household.weekly_budget_usd,
    servings_per_meal=household.servings_per_meal,
    meals_per_week=household.meals_per_week,
)
scored = optimizer.score(result.passed)
heroes = optimizer.select_ingredients(scored, min_count=5, max_count=7)

st.markdown("---")
st.subheader("🌟 This week's hero ingredients (5–7 modular blueprint)")
for h in heroes:
    st.markdown(
        f"- **{h.ingredient.name}** — value score `{h.value_score:.1f}` "
        f"(${h.ingredient.sale_price_per_unit:.2f}/{h.ingredient.unit}, "
        f"{h.sale_savings_pct}% off)"
    )

planner = MealPlanner(household)
plan = planner.assemble_week(
    heroes,
    flyer_week=getattr(candidates[0], "flyer_week", None) if candidates else None,
    grocer=primary_grocer["chain"],
)
st.session_state["plan"] = plan

st.markdown("---")
st.subheader("📅 Your week")
for meal in plan.meals:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### {meal.day} — {meal.name}")
            st.caption(meal.method_hint)
            st.markdown(
                "**From your pantry:** " + ", ".join(meal.pantry_seasonings)
            )
        with c2:
            st.metric("Cost / serving", f"${meal.cost_per_serving:.2f}")
            badge = " · ".join(f"✅ {n}" for n in meal.safety_attestation)
            st.caption(badge)

st.markdown("---")
st.success(
    f"**Weekly total: ${plan.total_cost:.2f}** across {len(plan.meals)} meals. "
    f"Head to the Sunday Buy-Off when you're ready to approve."
)
c_sl, c_so = st.columns(2)
with c_sl:
    st.page_link("pages/04_shopping_list.py", label="🛒 View Shopping List")
