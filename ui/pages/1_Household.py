"""
1_Household.py — Household & Member Profile Setup
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

from app.core_logic.profile_schema import (
    HouseholdProfile, MemberProfile, GrocerPreference,
    LifestyleTag, Diagnosis,
)

st.set_page_config(page_title="Household · WhollyFare", page_icon="👨‍👩‍👧", layout="wide")
state.init()
style.page_header(
    "Household Setup",
    "Tell WhollyFare who's at the table. Every constraint you set here is a hard rule — the engine will never violate it.",
)

household = st.session_state.get("household")

# ── Household-level settings ──────────────────────────────────────────────────
st.subheader("Household")

col1, col2, col3 = st.columns(3)
with col1:
    hh_name = st.text_input(
        "Household name",
        value=household.household_name if household else "My Household",
        help="Used in plans and the Sunday Buy-Off screen",
    )
with col2:
    weekly_budget = st.number_input(
        "Weekly grocery budget ($)",
        min_value=40.0, max_value=500.0, step=5.0,
        value=float(household.weekly_budget_usd) if household else 120.0,
    )
with col3:
    servings = st.number_input(
        "Servings per meal",
        min_value=1, max_value=12, step=1,
        value=household.servings_per_meal if household else 4,
        help="How many people eat each dinner",
    )

meals_per_week = st.slider(
    "Dinners to plan per week",
    min_value=3, max_value=7, value=household.meals_per_week if household else 7,
)

st.divider()

# ── Members ───────────────────────────────────────────────────────────────────
st.subheader("Household members")
st.caption(
    "Add each person who eats these meals. Constraints are unioned across all members — "
    "if anyone has a peanut allergy, peanuts never appear in the plan."
)

# Pull existing members or start with one empty slot
if "member_list" not in st.session_state:
    existing = household.members if household else []
    st.session_state["member_list"] = [
        {
            "name":       m.name,
            "age":        m.age or 0,
            "allergies":  m.allergies,
            "diagnoses":  [d.value for d in m.diagnoses],
            "lifestyle":  [t.value for t in m.lifestyle_tags],
            "exclusions": "\n".join(m.custom_exclusions),
        }
        for m in existing
    ] or [{"name": "", "age": 0, "allergies": [], "diagnoses": [], "lifestyle": [], "exclusions": ""}]

ALL_ALLERGENS = [
    "peanuts", "tree_nuts", "milk", "eggs", "wheat", "soy",
    "fish", "shellfish", "sesame", "mustard", "celery",
    "lupin", "molluscs", "sulphites",
]
ALL_DIAGNOSES   = [d.value for d in Diagnosis]
ALL_LIFESTYLE   = [t.value for t in LifestyleTag]
DIAG_LABELS = {
    "celiac": "Celiac disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
    "ckd": "Chronic Kidney Disease (CKD)",
    "pku": "PKU",
    "gerd": "GERD / Acid reflux",
    "ibs_low_fodmap": "IBS (Low-FODMAP)",
    "crohns": "Crohn's disease",
    "hypertension": "Hypertension",
}

members_to_remove = []

for i, member in enumerate(st.session_state["member_list"]):
    with st.expander(
        f"👤 {member['name'] or f'Member {i+1}'}",
        expanded=(member["name"] == ""),
    ):
        c1, c2 = st.columns([2, 1])
        with c1:
            member["name"] = st.text_input("Name", value=member["name"], key=f"name_{i}")
        with c2:
            member["age"] = st.number_input("Age", min_value=0, max_value=120, value=member["age"] or 0, key=f"age_{i}")

        member["allergies"] = st.multiselect(
            "Food allergies (Top-14 + common extras)",
            options=ALL_ALLERGENS,
            default=member["allergies"],
            key=f"allergy_{i}",
        )
        member["diagnoses"] = st.multiselect(
            "Medical diagnoses requiring dietary accommodation",
            options=ALL_DIAGNOSES,
            format_func=lambda x: DIAG_LABELS.get(x, x),
            default=member["diagnoses"],
            key=f"diag_{i}",
        )
        member["lifestyle"] = st.multiselect(
            "Dietary lifestyle",
            options=ALL_LIFESTYLE,
            default=member["lifestyle"],
            key=f"lifestyle_{i}",
        )
        member["exclusions"] = st.text_area(
            "Additional ingredient exclusions (one per line)",
            value=member["exclusions"],
            height=68,
            placeholder="e.g.\nBrussels sprouts\nMushrooms",
            key=f"excl_{i}",
            help="Free-text ingredients this person won't eat. Not a safety constraint — just preference.",
        )

        if st.button("Remove member", key=f"remove_{i}", type="secondary"):
            members_to_remove.append(i)

for idx in reversed(members_to_remove):
    st.session_state["member_list"].pop(idx)
st.session_state["member_list"] = st.session_state["member_list"]  # trigger rerun

if st.button("＋ Add another member"):
    st.session_state["member_list"].append(
        {"name": "", "age": 0, "allergies": [], "diagnoses": [], "lifestyle": [], "exclusions": ""}
    )
    st.rerun()

st.divider()

# ── Save ──────────────────────────────────────────────────────────────────────
col_save, col_msg = st.columns([1, 3])
with col_save:
    if st.button("Save household profile", type="primary", use_container_width=True):
        members = []
        for m in st.session_state["member_list"]:
            if not m["name"].strip():
                continue
            members.append(MemberProfile(
                name=m["name"].strip(),
                age=m["age"] or None,
                allergies=m["allergies"],
                diagnoses=[Diagnosis(d) for d in m["diagnoses"]],
                lifestyle_tags=[LifestyleTag(t) for t in m["lifestyle"]],
                custom_exclusions=[
                    line.strip()
                    for line in m["exclusions"].splitlines()
                    if line.strip()
                ],
            ))

        if not members:
            st.error("Add at least one household member before saving.")
        else:
            st.session_state["household"] = HouseholdProfile(
                household_name=hh_name,
                members=members,
                weekly_budget_usd=weekly_budget,
                servings_per_meal=int(servings),
                meals_per_week=int(meals_per_week),
            )
            st.success("✅ Household saved.")

with col_msg:
    if household:
        constraint_count = sum(
            len(m.allergies) + len(m.diagnoses) + len(m.lifestyle_tags)
            for m in household.members
        )
        st.info(
            f"**{len(household.members)} member(s)** · "
            f"**{constraint_count} active constraints** · "
            f"Budget ${household.weekly_budget_usd:.0f}/week · "
            f"{household.meals_per_week} dinners · {household.servings_per_meal} servings each",
            icon="✅",
        )
