"""
1_Household.py — Household & Member Profile Setup
====================================================
First step of the WhollyFare setup flow.

This page must work for two audiences without explanation:
  1. Tim's own family — familiar, fast to complete
  2. Pilot friends — arriving cold, no briefing, first time on the app

Design principle: every label earns its place. If someone has to ask what
a field means, the field needs better copy or it shouldn't be there.

POC vs. PRODUCTION
-------------------
POC:  Profile stored in session_state. Reloading the browser loses it.
      Pilot users should complete setup and immediately proceed to the
      Grocer Hub in one sitting. Workaround: export/import via JSON is
      on the roadmap.
PROD: Profile persists to Postgres under user_id. Members have individual
      logins. Profile changes are versioned so the audit log stays accurate.
      Clinical constraint rulesets reviewed by registered dietitian annually.
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

st.set_page_config(page_title="Household Setup · WhollyFare", page_icon="👨‍👩‍👧", layout="wide")
state.init()

# ── DB load ───────────────────────────────────────────────────────────────────
# If authenticated and household not yet in session_state, load from DB.
# This restores the profile after a browser refresh.
# POC: runs on every page load but DB call is cheap (one row, indexed on user_id).
if state.is_authenticated() and st.session_state.get("household_db") is None:
    state.load_household()

# If DB returned data but session_state["household"] (HouseholdProfile) is missing,
# convert the dict back so the constraint engine and other pages work correctly.
if st.session_state.get("household_db") and st.session_state.get("household") is None:
    profile = state.db_dict_to_profile(st.session_state["household_db"])
    if profile:
        st.session_state["household"] = profile

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Household Setup",
    "Tell us who's at the table. Every constraint you enter is a hard rule — the engine will never violate it.",
)

# ── Setup stepper ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:0;margin-bottom:24px;'>
  <div style='background:#3A8C4E;color:white;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;
              font-size:0.8rem;font-weight:700;flex-shrink:0;'>1</div>
  <div style='height:2px;width:40px;background:#D8EDD0;'></div>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;
              font-size:0.8rem;font-weight:700;flex-shrink:0;'>2</div>
  <div style='height:2px;width:40px;background:#D8EDD0;'></div>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;
              font-size:0.8rem;font-weight:700;flex-shrink:0;'>3</div>
  <div style='margin-left:12px;font-size:0.82rem;color:#5A7A62;'>
    <strong style='color:#1E5C32;'>Household</strong> → Grocer Prices → Generate Plan
  </div>
</div>
""", unsafe_allow_html=True)


# ── What this page does (pilot-friend context) ────────────────────────────────
st.markdown("""
<div style='background:white;border:1px solid #D8EDD0;border-left:4px solid #3A8C4E;
            border-radius:8px;padding:16px 20px;margin-bottom:24px;'>
  <div style='font-weight:700;color:#1E5C32;font-size:0.95rem;margin-bottom:6px;'>
    Two minutes. That's all this takes.
  </div>
  <div style='font-size:0.85rem;color:#5A7A62;line-height:1.6;'>
    Enter your household name, weekly grocery budget, and one profile per person who
    eats your family dinners. For each person, flag any food allergies or medical
    conditions that affect what they can eat.<br><br>
    <strong>WhollyFare uses this to protect your family — not to market to them.</strong>
    Every allergy you enter becomes a permanent hard filter. Those ingredients will
    never appear in a plan, a suggestion, or a shopping list.
  </div>
</div>
""", unsafe_allow_html=True)

household = st.session_state.get("household")


# ── Household basics ──────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:10px;'>Your household</div>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    hh_name = st.text_input(
        "Household name",
        value=household.household_name if household else "",
        placeholder="e.g. The Johnson Family",
        help="Shown on your plan and Sunday Buy-Off screen",
    )
with col2:
    weekly_budget = st.number_input(
        "Weekly dinner budget ($)",
        min_value=30.0, max_value=600.0, step=5.0,
        value=float(household.weekly_budget_usd) if household else 120.0,
        help="How much you want to spend on groceries for dinners each week. "
             "WhollyFare optimises within this — it won't go over.",
    )
with col3:
    servings = st.number_input(
        "People eating each dinner",
        min_value=1, max_value=12, step=1,
        value=household.servings_per_meal if household else 4,
        help="How many people sit down to dinner most nights. "
             "Used to calculate cost per serving.",
    )

meals_per_week = st.slider(
    "How many dinners per week should WhollyFare plan?",
    min_value=3, max_value=7,
    value=household.meals_per_week if household else 5,
    help="3–5 is realistic for most families. 7 if you cook every night.",
)

st.divider()


# ── Household members ─────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:4px;'>Household members</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='font-size:0.84rem;color:#5A7A62;margin-bottom:14px;'>"
    "Add a profile for each person who eats these meals. "
    "Constraints are combined across the whole household — one peanut allergy means "
    "peanuts never appear, for anyone, ever."
    "</div>",
    unsafe_allow_html=True,
)

# Initialise member list
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
ALL_DIAGNOSES = [d.value for d in Diagnosis]
ALL_LIFESTYLE = [t.value for t in LifestyleTag]

DIAG_LABELS = {
    "celiac":          "Celiac disease (strict gluten-free)",
    "type1_diabetes":  "Type 1 Diabetes",
    "type2_diabetes":  "Type 2 Diabetes",
    "ckd":             "Chronic Kidney Disease (CKD)",
    "pku":             "PKU",
    "gerd":            "GERD / Acid reflux",
    "ibs_low_fodmap":  "IBS — Low FODMAP diet",
    "crohns":          "Crohn's disease",
    "hypertension":    "Hypertension (low sodium)",
    "mcas":            "MCAS (Mast Cell Activation Syndrome)",
    "eds":             "EDS (Ehlers-Danlos Syndrome)",
    "pots":            "POTS",
}

LIFESTYLE_LABELS = {
    "vegan":         "Vegan",
    "vegetarian":    "Vegetarian",
    "halal":         "Halal",
    "kosher":        "Kosher",
    "keto":          "Keto",
    "paleo":         "Paleo",
    "whole30":       "Whole30",
    "low_fodmap":    "Low FODMAP",
    "gluten_free":   "Gluten-free (preference, not celiac)",
    "dairy_free":    "Dairy-free",
}

members_to_remove = []

for i, member in enumerate(st.session_state["member_list"]):
    display_name = member["name"].strip() if member["name"].strip() else f"Member {i + 1}"
    constraints_count = len(member["allergies"]) + len(member["diagnoses"]) + len(member["lifestyle"])
    badge = f" · {constraints_count} constraint{'s' if constraints_count != 1 else ''}" if constraints_count else " · no restrictions"

    with st.expander(
        f"👤 {display_name}{badge}",
        expanded=(not member["name"].strip()),
    ):
        row1a, row1b = st.columns([3, 1])
        with row1a:
            member["name"] = st.text_input(
                "Name",
                value=member["name"],
                placeholder="First name or nickname",
                key=f"name_{i}",
            )
        with row1b:
            member["age"] = st.number_input(
                "Age",
                min_value=0, max_value=120,
                value=member["age"] or 0,
                key=f"age_{i}",
                help="Optional — used to adjust serving size guidance for young children",
            )

        # Allergies — most critical field, given most prominence
        member["allergies"] = st.multiselect(
            "Food allergies",
            options=ALL_ALLERGENS,
            default=member["allergies"],
            key=f"allergy_{i}",
            help="Select all allergens this person has. These become permanent hard filters — "
                 "the engine will never include these ingredients regardless of price or availability.",
        )
        if member["allergies"]:
            st.markdown(
                f"<div style='font-size:0.76rem;color:#3A8C4E;margin-top:-8px;margin-bottom:8px;'>"
                f"🛡️ {', '.join(member['allergies'])} will never appear in this household's plan."
                f"</div>",
                unsafe_allow_html=True,
            )

        # Medical conditions
        member["diagnoses"] = st.multiselect(
            "Medical conditions affecting diet",
            options=ALL_DIAGNOSES,
            format_func=lambda x: DIAG_LABELS.get(x, x),
            default=member["diagnoses"],
            key=f"diag_{i}",
            help="Each condition activates a specific set of ingredient exclusion rules. "
                 "WhollyFare does not make medical claims — these rules are a planning safety layer.",
        )

        # Lifestyle
        member["lifestyle"] = st.multiselect(
            "Dietary preference or lifestyle",
            options=ALL_LIFESTYLE,
            format_func=lambda x: LIFESTYLE_LABELS.get(x, x),
            default=member["lifestyle"],
            key=f"lifestyle_{i}",
            help="Lifestyle choices — not allergies or medical conditions. "
                 "These filter preferences, not safety constraints.",
        )

        # Freetext exclusions
        member["exclusions"] = st.text_area(
            "Anything else they won't eat (one per line)",
            value=member["exclusions"],
            height=60,
            placeholder="e.g.\nBrussels sprouts\nMushrooms\nLima beans",
            key=f"excl_{i}",
            help="Personal dislikes — not allergies. The engine will avoid these ingredients "
                 "where possible but may include them if the household has no safe alternatives.",
        )

        if st.button(f"Remove {display_name}", key=f"remove_{i}", type="secondary"):
            members_to_remove.append(i)

# Process removals
for idx in reversed(members_to_remove):
    st.session_state["member_list"].pop(idx)

if st.button("＋ Add another person"):
    st.session_state["member_list"].append(
        {"name": "", "age": 0, "allergies": [], "diagnoses": [], "lifestyle": [], "exclusions": ""}
    )
    st.rerun()

st.divider()


# ── Save ──────────────────────────────────────────────────────────────────────
col_save, col_status = st.columns([1, 3])

with col_save:
    save_pressed = st.button(
        "Save household profile",
        type="primary",
        use_container_width=True,
    )

with col_status:
    if household:
        constraint_count = sum(
            len(m.allergies) + len(m.diagnoses) + len(m.lifestyle_tags)
            for m in household.members
        )
        member_names = ", ".join(m.name for m in household.members)
        st.info(
            f"**{member_names}** · "
            f"**{constraint_count} active constraint{'s' if constraint_count != 1 else ''}** · "
            f"${household.weekly_budget_usd:.0f}/week · "
            f"{household.meals_per_week} dinners · {household.servings_per_meal} per meal",
            icon="✅",
        )

if save_pressed:
    members = []
    for m in st.session_state["member_list"]:
        if not m["name"].strip():
            continue
        try:
            diagnoses   = [Diagnosis(d) for d in m["diagnoses"]]
            lifestyles  = [LifestyleTag(t) for t in m["lifestyle"]]
        except ValueError as e:
            st.error(f"Unrecognised value in profile — {e}. Please re-select and save again.")
            st.stop()

        members.append(MemberProfile(
            name=m["name"].strip(),
            age=m["age"] or None,
            allergies=m["allergies"],
            diagnoses=diagnoses,
            lifestyle_tags=lifestyles,
            custom_exclusions=[
                line.strip()
                for line in m["exclusions"].splitlines()
                if line.strip()
            ],
        ))

    if not members:
        st.error("Add at least one household member before saving.")
    elif not hh_name.strip():
        st.error("Give your household a name.")
    else:
        st.session_state["household"] = HouseholdProfile(
            household_name=hh_name.strip(),
            members=members,
            weekly_budget_usd=weekly_budget,
            servings_per_meal=int(servings),
            meals_per_week=int(meals_per_week),
        )

        # ── Persist to DB ─────────────────────────────────────────────────────
        # POC: save_household() degrades gracefully if not authenticated or DB down.
        # PROD: show a "not saved" indicator if DB write fails.
        db_ok, db_msg = state.save_household({
            "name":              hh_name.strip(),
            "weekly_budget_usd": weekly_budget,
            "servings_per_meal": int(servings),
            "meals_per_week":    int(meals_per_week),
            "members": [
                {
                    "name":       m.name,
                    "role":       "child" if (m.age or 99) < 18 else "adult",
                    "birth_year": None,  # profile stores age, not birth_year
                    "allergies":  m.allergies,
                    "diagnoses":  [d.value for d in m.diagnoses],
                    "lifestyle":  [t.value for t in m.lifestyle_tags],
                    "exclusions": m.custom_exclusions,
                }
                for m in members
            ],
        })

        # Clear member_list cache so it reloads from the saved profile
        if "member_list" in st.session_state:
            del st.session_state["member_list"]

        if db_ok:
            st.success(f"✅ {hh_name.strip()} saved — {len(members)} member(s), {meals_per_week} dinners/week.")
        else:
            st.warning(
                f"⚠️ Profile saved to this session, but could not save to database: {db_msg}  \n"
                "Sign in to save permanently."
            )
        st.rerun()


# ── Next step prompt ──────────────────────────────────────────────────────────
if st.session_state.get("household"):
    st.markdown("""
    <div style='background:#F4FAF5;border:1px solid #D8EDD0;border-radius:10px;
                padding:16px 20px;margin-top:8px;'>
      <div style='font-weight:600;color:#1E5C32;font-size:0.95rem;margin-bottom:4px;'>
        ✅ Profile saved
      </div>
      <div style='font-size:0.84rem;color:#5A7A62;'>
        Next: connect your grocery stores and load this week's sale prices.
        The engine does the rest.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if st.button("🏪 Continue to Grocer Hub →", type="primary"):
        st.switch_page("pages/2_Grocer_Hub.py")
