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

# ── Temporary debug panel — remove after diagnosis ───────────────────────────
with st.expander("🔍 Debug: session state (remove after fix)", expanded=False):
    import ui.state as _s
    st.write({
        "is_authenticated":  _s.is_authenticated(),
        "user_id":           _s.current_user_id(),
        "household_id":      st.session_state.get("household_id"),
        "household_db_name": (st.session_state.get("household_db") or {}).get("name"),
        "household_db_members": len((st.session_state.get("household_db") or {}).get("members", [])),
        "household_type":    type(st.session_state.get("household")).__name__,
        "household_none":    st.session_state.get("household") is None,
        "grocers_count":     len(st.session_state.get("grocers", [])),
        "member_list_count": len(st.session_state.get("member_list", [])),
        "_DB_AVAILABLE":     _s._DB_AVAILABLE,
    })

# ── DB load ───────────────────────────────────────────────────────────────────
# Load from DB when:
#   a) household_db is None (first visit / browser refresh), OR
#   b) household (HouseholdProfile) is None even though we're authenticated —
#      this happens when navigating back from the Grocer Hub after adding stores,
#      which can clear the profile object without clearing household_db.
# POC: DB call is cheap (one row, indexed on user_id) so double-loading is fine.
# PROD: add an in-memory TTL cache to avoid redundant round trips.
# Always reload from DB when authenticated — ensures the profile is current
# regardless of navigation path (e.g. returning from Grocer Hub after adding stores).
# POC: single indexed query, cheap enough to run on every page load.
# PROD: add TTL cache (e.g. 60s) to avoid redundant round trips at scale.
if state.is_authenticated():
    state.load_household()

# Convert the DB dict into a typed HouseholdProfile if still missing after load.
if st.session_state.get("household_db") and st.session_state.get("household") is None:
    profile = state.db_dict_to_profile(st.session_state["household_db"])
    if profile:
        st.session_state["household"] = profile

# If DB has members but member_list is empty or just the blank default placeholder,
# clear it so it rebuilds from the freshly loaded household.members below.
# POC: member_list is initialized before sign-in by state.init(); without this,
# the guard at "if member_list not in session_state" skips the rebuild after sign-in.
if st.session_state.get("household_db"):
    _db_members = st.session_state["household_db"].get("members", [])
    _ml = st.session_state.get("member_list", [])
    _ml_is_empty_default = (
        len(_ml) == 0
        or (len(_ml) == 1 and not _ml[0].get("name", "").strip())
    )
    if _db_members and _ml_is_empty_default:
        st.session_state.pop("member_list", None)

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Household Setup",
    "Tell us who's at the table. Every constraint you enter is a hard rule — the engine will never violate it.",
)

# ── Setup stepper ─────────────────────────────────────────────────────────────
st.html("""
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
""")


# ── What this page does (pilot-friend context) ────────────────────────────────
st.html("""
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
""")

# ── Your Store Profile ───────────────────────────────────────────────────────
# Stores are a permanent household profile setting, not a weekly choice.
# Showing them here so the user sees their full profile at a glance and can
# navigate directly to the Grocer Hub to add or remove stores at any time.
_grocers = st.session_state.get("grocers", [])
_tier_colors = {
    "discount": "#BF5E00", "mainstream": "#1E5C32",
    "specialty": "#1565C0", "local": "#5D4037",
}
_tier_icons = {
    "discount": "\U0001f4b0", "mainstream": "\U0001f3ea",
    "specialty": "\U0001f33f", "local": "\U0001f4cd",
}

if _grocers:
    _pills = "".join(
        "<span style='background:#E3F4E8;"
        "color:" + _tier_colors.get(g.get("tier", ""), "#1E5C32") + ";"
        "border:1px solid #D8EDD0;border-radius:20px;"
        "padding:3px 11px;font-size:0.76rem;font-weight:600;"
        "margin:0 5px 5px 0;display:inline-block;'>"
        + _tier_icons.get(g.get("tier", ""), "\U0001f3ea") + " " + g["chain"]
        + (" &middot; " + str(round(g["distance_miles"], 1)) + "mi"
           if g.get("distance_miles") else "")
        + ("&nbsp;&#11088;" if g.get("is_primary") else "")
        + "</span>"
        for g in _grocers
    )
    _n = len(_grocers)
    _label = f"{_n} store" + ("s" if _n != 1 else "") + " saved"
    st.html(
        "<div style=\'background:#F0FAF2;border:1px solid #D8EDD0;border-radius:12px;"
        "padding:16px 20px 14px;margin-bottom:22px;\'>"
        "<div style=\'display:flex;justify-content:space-between;align-items:flex-start;"
        "flex-wrap:wrap;gap:8px;margin-bottom:10px;\'>"
        "<div style=\'font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
        "text-transform:uppercase;color:#3A8C4E;\'>"
        "Your Store Profile \u2014 " + _label + "</div>"
        "<a href=\'/Grocer_Hub\' target=\'_self\'"
        " style=\'font-size:0.78rem;font-weight:600;color:#3A8C4E;text-decoration:none;\'>"
        "\u270f\ufe0f Edit stores \u2192</a></div>"
        "<div style=\'display:flex;flex-wrap:wrap;\'>" + _pills + "</div>"
        "<div style=\'font-size:0.75rem;color:#9AA8A0;margin-top:8px;\'>"
        "Your stores are saved to your profile \u2014 you won\u2019t need to pick them again each week."
        "</div></div>"
    )
else:
    st.html(
        "<div style=\'background:#FFF8F0;border:1px solid #FFCC80;border-radius:12px;"
        "padding:16px 20px;margin-bottom:22px;\'>"
        "<div style=\'font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
        "text-transform:uppercase;color:#BF5E00;margin-bottom:6px;\'>"
        "Your Store Profile</div>"
        "<div style=\'font-size:0.85rem;color:#5A7A62;line-height:1.6;\'>"
        "No stores saved yet. Once you\u2019ve set up your household below, head to the "
        "<strong>Grocer Hub</strong> to pick your stores \u2014 you\u2019ll only need to do this once."
        "</div>"
        "<a href=\'/Grocer_Hub\' target=\'_self\'"
        " style=\'display:inline-block;margin-top:10px;font-size:0.82rem;"
        "font-weight:600;color:#BF5E00;text-decoration:none;\'>"
        "Set up your stores \u2192</a></div>"
    )

household = st.session_state.get("household")
# Guard: if a previous failed save left a plain dict in session_state,
# convert it to a HouseholdProfile or clear it so the form renders safely.
if isinstance(household, dict):
    _converted = state.db_dict_to_profile(household)
    if _converted:
        st.session_state["household"] = _converted
        household = _converted
    else:
        st.session_state["household"] = None
        household = None


# ── Household basics ──────────────────────────────────────────────────────────
st.html(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:10px;'>Your household</div>")

col1, col2, col3 = st.columns(3)
# Show any save result that survived the rerun
if "_hh_save_msg" in st.session_state:
    _msg_type, _msg_text = st.session_state.pop("_hh_save_msg")
    if _msg_type == "success":
        st.success(_msg_text)
    else:
        st.warning(_msg_text)

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
st.html(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:4px;'>Household members</div>")
st.html(
    "<div style='font-size:0.84rem;color:#5A7A62;margin-bottom:14px;'>"
    "Add a profile for each person who eats these meals. "
    "Constraints are combined across the whole household — one peanut allergy means "
    "peanuts never appear, for anyone, ever."
    "</div>")

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
            st.html(
                f"<div style='font-size:0.76rem;color:#3A8C4E;margin-top:-8px;margin-bottom:8px;'>"
                f"🛡️ {', '.join(member['allergies'])} will never appear in this household's plan."
                f"</div>")

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


# ── Auth debug panel (remove after persistence is confirmed working) ──────────
with st.expander("🔧 Debug: auth state", expanded=False):
    _tok = st.session_state.get("_sb_access_token")
    try:
        _svc = st.secrets["supabase"].get("service_role_key", "")
    except Exception:
        _svc = ""
    st.write({
        "authenticated":        state.is_authenticated(),
        "user_id":              state.current_user_id(),
        "user_jwt_present":     bool(_tok),
        "user_jwt_preview":     (_tok[:24] + "…") if _tok else "MISSING",
        "service_role_present": bool(_svc),
        "service_role_len":     len(_svc) if _svc else 0,
        "session_state_keys":   [k for k in st.session_state if not k.startswith("_FormData")],
    })

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
        # PROD: show a "not         # POC: save_household() degrades gracefully if not authenticated or DB down.
        # PROD: show a "not signed in" prompt and require auth before saving.
        household_dict = {
            "name":              hh_name.strip(),
            "weekly_budget_usd": weekly_budget,
            "servings_per_meal": int(servings),
            "meals_per_week":    int(meals_per_week),
            "zip_code":          st.session_state.get("home_zip", ""),
            "city":              (st.session_state.get("household_db") or {}).get("city", ""),
            "state":             (st.session_state.get("household_db") or {}).get("state", "VA"),
            "members": [
                {
                    "name":       m["name"].strip(),
                    "age":        m.get("age") or None,
                    "allergies":  m.get("allergies", []),
                    "diagnoses":  [d.value if hasattr(d, "value") else d for d in
                                   [Diagnosis(x) for x in m.get("diagnoses", [])]],
                    "lifestyle":  [t.value if hasattr(t, "value") else t for t in
                                   [LifestyleTag(x) for x in m.get("lifestyle", [])]],
                    "exclusions": [
                        line.strip()
                        for line in m.get("exclusions", "").splitlines()
                        if line.strip()
                    ],
                }
                for m in st.session_state["member_list"]
                if m["name"].strip()
            ],
        }

        db_ok, db_msg = state.save_household(household_dict)
        if db_ok and "session only" not in db_msg:
            st.session_state["_hh_save_msg"] = ("success", "Household profile saved. Head to the Grocer Hub to set up your stores →")
        elif not db_ok:
            # Exception inside save_household — db_msg contains the actual Supabase error
            st.session_state["_hh_save_msg"] = ("warning", f"DB error (session saved): {db_msg}")
        else:
            # Early exit — not authenticated or DB unavailable
            _auth_status = "signed in" if state.is_authenticated() else "NOT signed in"
            _db_status = "available" if state._DB_AVAILABLE else "unavailable"
            st.session_state["_hh_save_msg"] = ("warning",
                f"Not written to DB — Auth: {_auth_status} | DB: {_db_status} | "
                f"user: {st.session_state.get('user')}"
            )
        st.rerun()
