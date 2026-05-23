"""
01_profile_setup.py — Comprehensive Family Profile Builder
-----------------------------------------------------------
This is the foundational data-collection page for WhollyFare. The constraint
engine, budget optimizer, and meal planner all depend on what gets captured
here, so this page intentionally collects *everything* in one place rather
than scattering it across the wizard.

Sections:
  1. Household basics (name, budget, household size)
  2. Local grocers (primary + backups, with rewards program enrollment)
  3. Family members (per-person dietary preferences, restrictions, health
     conditions, custom exclusions, optional supporting document upload)

Output: a fully-populated `st.session_state["household"]` dict that the
downstream pages (grocer connect, meal plan, sunday buy-off) consume.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Make the package importable when running `streamlit run interface/app.py`
# from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


st.set_page_config(page_title="Family Profile · WhollyFare", page_icon="👨‍👩‍👧", layout="wide")

st.title("👨‍👩‍👧 Family Profile")
st.markdown(
    "Tell us everything we need to plan safely for your household. "
    "**Nothing here is shared, sold, or used to train models** — see the "
    "[Sincere Strategy](/) for our data commitments."
)

# ── Reference option lists ────────────────────────────────────────────────────

GROCER_OPTIONS = [
    "Food Lion", "Kroger", "Publix", "Harris Teeter", "Aldi", "Lidl",
    "Walmart", "Target", "Wegmans", "Whole Foods", "Trader Joe's",
    "Giant", "Safeway", "ShopRite", "H-E-B", "Meijer", "Other",
]

REWARDS_PROGRAMS = {
    "Food Lion": "MVP / Shop & Earn",
    "Kroger": "Plus Card / Boost",
    "Publix": "Club Publix",
    "Harris Teeter": "VIC / e-VIC",
    "Walmart": "Walmart+",
    "Target": "Circle / RedCard",
    "Wegmans": "Shoppers Club",
    "Whole Foods": "Prime (Amazon)",
    "Giant": "Giant Flexible Rewards",
    "Safeway": "Safeway for U",
    "ShopRite": "Price Plus Club",
    "H-E-B": "H-E-B Digital Coupons",
    "Meijer": "mPerks",
}

ALLERGEN_OPTIONS = [
    "Peanuts", "Tree Nuts", "Milk", "Eggs", "Wheat / Gluten", "Soy",
    "Fish", "Shellfish", "Sesame", "Mustard", "Celery", "Lupin",
    "Molluscs", "Sulphites", "Alpha-gal (mammalian meat)",
]

DIAGNOSIS_OPTIONS = [
    "Celiac Disease", "Type 1 Diabetes", "Type 2 Diabetes",
    "Chronic Kidney Disease (CKD)", "PKU", "GERD / Acid Reflux",
    "IBS (Low-FODMAP)", "Crohn's Disease", "Hypertension",
    "MCAS (Mast Cell Activation Syndrome)",
    "POTS (Postural Orthostatic Tachycardia Syndrome)",
    "EDS (Ehlers-Danlos Syndrome)",
    "Heart Disease", "High Cholesterol",
]

LIFESTYLE_OPTIONS = [
    "Vegan", "Vegetarian", "Pescatarian", "Halal", "Kosher",
    "Whole30", "Low-FODMAP", "Paleo", "Keto", "Mediterranean",
    "DASH", "Low-Sodium", "Low-Histamine",
]

CUISINE_PREFERENCES = [
    "American Comfort", "Mexican", "Italian", "Mediterranean",
    "Asian (Chinese)", "Asian (Thai)", "Asian (Japanese)",
    "Indian", "Middle Eastern", "Caribbean", "Soul / Southern",
]

# ── Initialise session state ──────────────────────────────────────────────────

st.session_state.setdefault(
    "members",
    [{"name": "", "age": "", "allergies": [], "diagnoses": [],
      "lifestyle": [], "cuisines": [], "exclusions": "", "notes": "",
      "supporting_docs": []}],
)
st.session_state.setdefault(
    "grocers",
    [{"chain": "Food Lion", "store_id_or_address": "", "rewards_enrolled": False,
      "rewards_id": "", "delivery": False, "is_primary": True}],
)

# ── Section 1: Household basics ───────────────────────────────────────────────

st.header("1. Household basics")
col1, col2 = st.columns(2)
with col1:
    household_name = st.text_input(
        "Household name (optional)",
        placeholder="The Hislop Family",
        key="household_name",
    )
    weekly_budget = st.number_input(
        "Weekly grocery budget ($)",
        min_value=20.0, max_value=1500.0, value=120.0, step=5.0,
        key="weekly_budget",
        help="The engine will never propose a plan that exceeds this number.",
    )
with col2:
    servings = st.number_input(
        "Servings per meal",
        min_value=1, max_value=12, value=4, key="servings",
    )
    meals_per_week = st.number_input(
        "Meals to plan per week",
        min_value=1, max_value=21, value=7, key="meals_per_week",
        help="MVP plans dinners only. v2 adds breakfast and lunch.",
    )

st.markdown("---")

# ── Section 2: Local grocers + rewards ────────────────────────────────────────

st.header("2. Local grocers & rewards programs")
st.caption(
    "Add the stores you actually shop at. The engine will pull this week's "
    "real circular for your **primary** grocer and treat backups as fallback "
    "sources for unavailable items."
)

for i, grocer in enumerate(st.session_state.grocers):
    with st.expander(
        f"🏪 {grocer['chain']}{' (Primary)' if grocer.get('is_primary') else ''}",
        expanded=(i == 0),
    ):
        gc1, gc2 = st.columns([2, 2])
        with gc1:
            st.session_state.grocers[i]["chain"] = st.selectbox(
                "Grocer chain", GROCER_OPTIONS,
                index=GROCER_OPTIONS.index(grocer["chain"]) if grocer["chain"] in GROCER_OPTIONS else 0,
                key=f"grocer_chain_{i}",
            )
            st.session_state.grocers[i]["store_id_or_address"] = st.text_input(
                "Store ID, address, or ZIP",
                value=grocer.get("store_id_or_address", ""),
                key=f"grocer_addr_{i}",
                placeholder="e.g. Palmyra VA 22963 or store #1234",
            )
        with gc2:
            chain = st.session_state.grocers[i]["chain"]
            program_name = REWARDS_PROGRAMS.get(chain, "Rewards / Loyalty card")
            st.session_state.grocers[i]["rewards_enrolled"] = st.checkbox(
                f"Enrolled in {program_name}",
                value=grocer.get("rewards_enrolled", False),
                key=f"rewards_enroll_{i}",
            )
            st.session_state.grocers[i]["rewards_id"] = st.text_input(
                f"{program_name} number (optional)",
                value=grocer.get("rewards_id", ""),
                key=f"rewards_id_{i}",
                help="Used to surface coupon offers tied to your account. "
                     "Stored only on this device.",
            )
            st.session_state.grocers[i]["delivery"] = st.checkbox(
                "Use home delivery when available",
                value=grocer.get("delivery", False),
                key=f"delivery_{i}",
            )
            st.session_state.grocers[i]["is_primary"] = st.checkbox(
                "Set as primary grocer",
                value=grocer.get("is_primary", False),
                key=f"primary_{i}",
            )

g_add, g_remove = st.columns([1, 1])
with g_add:
    if st.button("➕ Add another grocer"):
        st.session_state.grocers.append({
            "chain": "Other", "store_id_or_address": "", "rewards_enrolled": False,
            "rewards_id": "", "delivery": False, "is_primary": False,
        })
        st.rerun()
with g_remove:
    if len(st.session_state.grocers) > 1 and st.button("➖ Remove last grocer"):
        st.session_state.grocers.pop()
        st.rerun()

st.markdown("---")

# ── Section 3: Family members (the constraint inputs) ─────────────────────────

st.header("3. Family members")
st.caption(
    "Add one profile per person in the household. The engine takes the "
    "**union** of every member's restrictions — if anyone is allergic to soy, "
    "no meal will contain soy. Health conditions and lifestyle choices are "
    "treated as **hard constraints**, never relaxed for budget or variety."
)

for i, member in enumerate(st.session_state.members):
    label = f"👤 {member['name']}" if member["name"] else f"Family Member {i+1}"
    with st.expander(label, expanded=(i == 0)):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.session_state.members[i]["name"] = st.text_input(
                "Name", value=member["name"], key=f"name_{i}")
        with c2:
            st.session_state.members[i]["age"] = st.text_input(
                "Age", value=member.get("age", ""), key=f"age_{i}")

        st.markdown("**Dietary restrictions & allergies**")
        st.session_state.members[i]["allergies"] = st.multiselect(
            "Food allergies (the engine will never include these)",
            ALLERGEN_OPTIONS, default=member["allergies"], key=f"allergy_{i}",
        )

        st.markdown("**Health conditions**")
        st.session_state.members[i]["diagnoses"] = st.multiselect(
            "Medical diagnoses requiring dietary accommodation",
            DIAGNOSIS_OPTIONS, default=member["diagnoses"], key=f"diag_{i}",
            help="Each condition maps to a built-in constraint set "
                 "(e.g. CKD → low potassium / phosphorus / sodium).",
        )

        st.markdown("**Dietary preferences & lifestyle**")
        pc1, pc2 = st.columns(2)
        with pc1:
            st.session_state.members[i]["lifestyle"] = st.multiselect(
                "Lifestyle / dietary pattern",
                LIFESTYLE_OPTIONS, default=member["lifestyle"], key=f"life_{i}",
            )
        with pc2:
            st.session_state.members[i]["cuisines"] = st.multiselect(
                "Preferred cuisines (we'll bias the rotation)",
                CUISINE_PREFERENCES, default=member.get("cuisines", []),
                key=f"cuisine_{i}",
            )

        st.session_state.members[i]["exclusions"] = st.text_area(
            "Other ingredients to avoid (comma-separated)",
            value=member.get("exclusions", ""),
            placeholder="e.g. cilantro, Brussels sprouts, mushrooms",
            key=f"excl_{i}",
        )

        st.session_state.members[i]["notes"] = st.text_area(
            "Notes for the planner (optional)",
            value=member.get("notes", ""),
            placeholder="e.g. Working on increasing iron; can tolerate small amounts of dairy if cooked.",
            key=f"notes_{i}",
        )

        uploaded = st.file_uploader(
            "Upload supporting documents (allergist note, dietitian plan, lab results)",
            type=["pdf", "png", "jpg", "jpeg", "txt"],
            accept_multiple_files=True,
            key=f"docs_{i}",
            help="Stored only in this session. WhollyFare never uploads "
                 "supporting documents to a server.",
        )
        if uploaded:
            st.session_state.members[i]["supporting_docs"] = [u.name for u in uploaded]
            st.success(f"Attached: {', '.join(u.name for u in uploaded)}")

m_add, m_remove = st.columns([1, 1])
with m_add:
    if st.button("➕ Add family member"):
        st.session_state.members.append({
            "name": "", "age": "", "allergies": [], "diagnoses": [],
            "lifestyle": [], "cuisines": [], "exclusions": "", "notes": "",
            "supporting_docs": [],
        })
        st.rerun()
with m_remove:
    if len(st.session_state.members) > 1 and st.button("➖ Remove last member"):
        st.session_state.members.pop()
        st.rerun()

st.markdown("---")

# ── Save & continue ───────────────────────────────────────────────────────────

if st.button("💾 Save Profile & Connect Grocer →", type="primary", use_container_width=True):
    st.session_state["household"] = {
        "name": household_name,
        "weekly_budget": weekly_budget,
        "servings": servings,
        "meals_per_week": meals_per_week,
        "grocers": st.session_state.grocers,
        "members": st.session_state.get("members", []),
    }
