"""
3_Plan.py — This Week's Plan
=============================
The weekly planning ritual. Three phases on one page:

  1. PREFERENCES  — What does your family want this week?
                    Cuisine, dinners, nights out. 30 seconds.
  2. GENERATE     — Engine runs: constraint filter → budget optimizer → meal plan.
                    Triggered by the preferences form or a "Regenerate" button.
  3. PLAN DISPLAY — Five dinner cards with costs, stores, ingredients, savings.

POC vs. PRODUCTION
-------------------
POC:  Cuisine preference is stored but doesn't yet filter meal names — recipes
      aren't wired in yet. Phase 2 adds the recipe library and cuisine matching.
      Plan lives in session_state — lost on browser refresh.
PROD: Preferences + plan persisted to DB (weekly_prefs table, plan table).
      Cuisine drives recipe selection from the Recipe Library.
      Instacart/Shipt export from Shopping List page.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Plan · WhollyFare", page_icon="🍽️", layout="wide")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.inject()

household = st.session_state.get("household")
plan      = st.session_state.get("plan")
prefs     = st.session_state.get("weekly_prefs", {})

# Auto-expire preferences + plan when the flyer week rolls over.
# POC: flyer_week stored alongside prefs. PROD: weekly_prefs table has flyer_week column.
_active_week = st.session_state.get("active_week", "")
if prefs.get("flyer_week") and prefs["flyer_week"] != _active_week:
    st.session_state.pop("weekly_prefs", None)
    st.session_state.pop("plan", None)
    prefs = {}
    plan  = None

# ── Guard: household required ─────────────────────────────────────────────────
if not household:
    style.page_header("This Week's Plan", "Set up your household first.")
    st.warning("Complete your household profile before planning meals.", icon="⚠️")
    if st.button("→ Household Setup", type="primary"):
        st.switch_page("pages/1_Household.py")
    st.stop()

# ── Guard: store data required ────────────────────────────────────────────────
all_candidates = [c for v in st.session_state.get("flyer_data", {}).values() for c in v]
if not all_candidates and not plan:
    style.page_header("This Week's Plan", "Load store prices first.")
    st.info("Head to the Grocer Hub to pull this week's prices, then come back here.", icon="🏪")
    if st.button("→ Grocer Hub", type="primary"):
        st.switch_page("pages/2_Grocer_Hub.py")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# ENGINE — shared helper, called from preferences form and Regenerate button
# POC: synchronous, single-household. PROD: async Celery worker.
# ══════════════════════════════════════════════════════════════════════════════

def _run_engine(prefs: dict) -> bool:
    """
    Run constraint filter → budget optimizer → meal planner.
    Saves result to session_state["plan"]. Returns True on success.

    POC: Cuisine preference stored but not yet used for recipe selection —
         Phase 2 wires cuisine to the Recipe Library.
    PROD: preferences drive recipe filtering; plan persisted to DB.
    """
    candidates = [c for v in st.session_state.get("flyer_data", {}).values() for c in v]
    if not candidates or not st.session_state.get("household"):
        return False

    hh = st.session_state["household"]
    n_dinners = prefs.get("dinners", getattr(hh, "meals_per_week", 5))

    try:
        with st.spinner("Running constraint engine — checking dietary rules…"):
            from app.core_logic.constraint_engine import ConstraintEngine
            result = ConstraintEngine(hh).filter(candidates)
            st.session_state["filter_result"] = result

        with st.spinner(f"Optimising budget across {len(result.passed)} safe ingredients…"):
            from app.core_logic.budget_optimizer import BudgetOptimizer
            optimizer = BudgetOptimizer(
                weekly_budget=hh.weekly_budget_usd,
                servings_per_meal=hh.servings_per_meal,
                meals_per_week=n_dinners,
            )
            scored   = optimizer.score(result.passed)
            selected = optimizer.select_ingredients(scored)

        with st.spinner("Assembling your meal plan…"):
            from app.core_logic.meal_planner import MealPlanner
            raw_plan = MealPlanner(hh).assemble_week(
                hero_ingredients=selected,
                flyer_week=st.session_state["active_week"],
                n_meals=n_dinners,   # respects weekly preference, not profile default
            )

        plan_meals = []
        plan_total = 0.0
        for meal in raw_plan.meals:
            ing_list  = []
            meal_cost = 0.0
            for scored_ing in meal.ingredients:
                ing  = scored_ing.ingredient
                cost = ing.sale_price_per_unit
                ing_list.append({
                    "item":  ing.name,
                    "qty":   f"1 {ing.unit}",
                    "store": getattr(ing, "source_store", "—"),
                    "cost":  round(cost, 2),
                })
                meal_cost += cost
            plan_meals.append({
                "day":           meal.day,
                "name":          meal.name,
                "gluten_free":   False,
                "allergen_notes": "",
                "best_store":    "—",
                "ingredients":   ing_list,
                "meal_cost":     round(meal_cost, 2),
            })
            plan_total += meal_cost

        total_servings = len(plan_meals) * hh.servings_per_meal
        single_est     = round(plan_total * 1.18, 2)
        hf_equiv       = round(total_servings * 9.99, 2)

        st.session_state["plan"] = {
            "week":     st.session_state["active_week"],
            "servings": hh.servings_per_meal,
            "meals":    plan_meals,
            "prefs":    prefs,   # store alongside plan for display
            "totals": {
                "whollyfare_plan":   round(plan_total, 2),
                "single_store_best": single_est,
                "hellofresh_equiv":  hf_equiv,
                "found_money":       round(single_est - plan_total, 2),
                "vs_hellofresh":     round(hf_equiv - plan_total, 2),
            },
        }
        return True

    except Exception as e:
        st.error(f"Plan generation failed: {e}", icon="❌")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — WEEKLY PREFERENCES
# Shown when there's no plan yet (or user clicks "Change preferences")
# POC: Preferences stored in session_state with flyer_week expiration.
# PROD: persisted to weekly_prefs table; expires when new circular is loaded.
# ══════════════════════════════════════════════════════════════════════════════

_show_prefs = not plan or st.session_state.get("_show_prefs_form", False)

if _show_prefs:
    style.page_header(
        "What do you want this week?",
        f"Prices are current as of {st.session_state.get('active_week', 'this week')}. "
        "Set your preferences — your choices are saved until new sale prices load.",
    )

    # ── Step 1: How many dinners? (drives cuisine recommendation) ─────────────
    st.html("""
    <div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
                text-transform:uppercase;margin:4px 0 12px 0;'>
        Step 1 of 3 &nbsp;·&nbsp; This week's schedule
    </div>""")

    _sched_cols = st.columns([1, 1, 2])
    with _sched_cols[0]:
        _dinners = st.number_input(
            "Dinners to plan",
            min_value=2, max_value=7,
            value=prefs.get("dinners", getattr(household, "meals_per_week", 5)),
            step=1,
            help="WhollyFare builds this many dinners from sale prices.",
        )
    with _sched_cols[1]:
        _nights_out = st.number_input(
            "Nights eating out",
            min_value=0, max_value=5,
            value=prefs.get("nights_out", 0),
            step=1,
            help="Nights you'll eat out or order in — we skip those.",
        )
    with _sched_cols[2]:
        _occasion = st.selectbox(
            "Anything special this week?",
            options=["Nothing special", "Date night", "Family gathering",
                     "Kids choice", "Big batch / meal prep"],
            index=["Nothing special","Date night","Family gathering",
                   "Kids choice","Big batch / meal prep"].index(
                       prefs.get("occasion", "Nothing special")),
        )

    st.html("<div style='height:20px;'></div>")

    # ── Step 2: Cuisine — multi-select with smart recommendation ──────────────
    import math as _math
    _suggested_count = max(1, _math.ceil(int(_dinners) / 2))

    st.html(f"""
    <div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
                text-transform:uppercase;margin-bottom:6px;'>
        Step 2 of 3 &nbsp;·&nbsp; Cuisine mix
    </div>
    <div style='font-size:0.85rem;color:#3A8C4E;margin-bottom:14px;'>
        For {int(_dinners)} dinners we recommend picking
        <strong>{_suggested_count} cuisine{"s" if _suggested_count != 1 else ""}</strong>.
        Check as many as you like.
    </div>""")

    CUISINES = [
        ("🌮", "Mexican",       "Tacos, fajitas, rice bowls"),
        ("🍜", "Asian",         "Stir-fry, noodles, fried rice"),
        ("🍝", "Italian",       "Pasta, chicken, hearty sauces"),
        ("🍗", "American",      "Comfort food, BBQ, classics"),
        ("🥗", "Mediterranean", "Light, fresh, veggie-forward"),
        ("🌶️", "Mix it up",     "Best prices win this week"),
    ]

    # Restore saved cuisines or default to Match it up for new users
    _default_cuisines = prefs.get("cuisines", ["Mix it up"])
    if isinstance(_default_cuisines, str):           # back-compat single value
        _default_cuisines = [_default_cuisines]

    _c_cols = st.columns(6)
    _selected_cuisines = []

    for i, (icon, label, desc) in enumerate(CUISINES):
        with _c_cols[i]:
            _default_checked = label in _default_cuisines
            _checked = st.checkbox(label, value=_default_checked, key=f"c_{label}",
                                   label_visibility="collapsed")
            _bg     = "#D8EDD0" if _checked else "#FFFFFF"
            _border = "#2D6A4F" if _checked else "#C8DFC8"
            _fw     = "700"     if _checked else "500"
            _check  = "☑" if _checked else "☐"
            st.html(f"""<div style='background:{_bg};border:2px solid {_border};
                border-radius:10px;padding:10px 8px 10px 8px;text-align:center;
                margin-top:-8px;min-height:88px;'>
              <div style='font-size:0.7rem;color:#3A8C4E;text-align:left;
                          font-weight:700;padding:0 2px;'>{_check}</div>
              <div style='font-size:1.4rem;line-height:1;margin-top:-2px;'>{icon}</div>
              <div style='font-size:0.82rem;font-weight:{_fw};color:#1A2E1D;
                          margin-top:5px;'>{label}</div>
              <div style='font-size:0.68rem;color:#5A7A62;margin-top:3px;
                          line-height:1.3;'>{desc}</div>
            </div>""")
            if _checked:
                _selected_cuisines.append(label)

    # Warn if count differs from recommendation
    _n_selected = len(_selected_cuisines)
    if _n_selected == 0:
        st.warning("Pick at least one cuisine to continue.", icon="⚠️")
    elif _n_selected < _suggested_count:
        st.html(f"<div style='font-size:0.8rem;color:#BF5E00;margin-top:6px;'>💡 You've picked {_n_selected} — {_suggested_count} would give more variety across your {int(_dinners)} dinners.</div>")
    elif _n_selected > _suggested_count + 1:
        st.html(f"<div style='font-size:0.8rem;color:#5A7A62;margin-top:6px;'>ℹ️ {_n_selected} cuisines across {int(_dinners)} dinners — meals may repeat some styles.</div>")

    st.html("<div style='height:20px;'></div>")

    # ── Step 3: Notes ─────────────────────────────────────────────────────────
    st.html("""
    <div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
                text-transform:uppercase;margin-bottom:12px;'>
        Step 3 of 3 &nbsp;·&nbsp; Anything to avoid or request?
    </div>""")

    _notes = st.text_input(
        "Optional notes",
        value=prefs.get("notes", ""),
        placeholder="e.g. no fish this week · quick meals Thursday · Chas won't eat mushrooms",
        label_visibility="collapsed",
    )

    st.html("<div style='height:8px;'></div>")

    # POC transparency note
    st.html(
        "<div style='background:#FFF8E1;border-left:3px solid #FFD54F;"
        "border-radius:0 6px 6px 0;padding:8px 14px;font-size:0.78rem;"
        "color:#7A5C00;margin-bottom:20px;line-height:1.5;'>"
        "🧪 <strong>Pilot note:</strong> Cuisine selections are saved to your profile for this "
        "flyer week and will auto-reset when new sale prices load. Phase 2 wires cuisine to the "
        "full recipe library."
        "</div>"
    )

    _cuisine_display = " + ".join(_selected_cuisines) if _selected_cuisines else "no cuisines selected"

    if st.button(
        f"💾 Save to Profile & Build Plan  →  {_cuisine_display}",
        type="primary",
        use_container_width=True,
        disabled=(_n_selected == 0),
    ):
        new_prefs = {
            "cuisines":   _selected_cuisines,
            "cuisine":    _selected_cuisines[0] if _selected_cuisines else "Mix it up",  # back-compat
            "dinners":    int(_dinners),
            "nights_out": int(_nights_out),
            "occasion":   _occasion,
            "notes":      _notes,
            "flyer_week": st.session_state.get("active_week", ""),  # expiration key
        }
        st.session_state["weekly_prefs"] = new_prefs
        st.session_state["_show_prefs_form"] = False
        ok = _run_engine(new_prefs)
        if ok:
            st.rerun()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — PLAN DISPLAY
# ══════════════════════════════════════════════════════════════════════════════

plan  = st.session_state["plan"]
prefs = plan.get("prefs", st.session_state.get("weekly_prefs", {}))

cuisine   = prefs.get("cuisine", "")
cuisine_line = f" · {cuisine} week" if cuisine and cuisine != "Mix it up" else ""
occasion  = prefs.get("occasion", "")
notes     = prefs.get("notes", "")

style.page_header(
    f"This Week's Plan{cuisine_line}",
    f"Five dinners built from your stores' actual sale prices, filtered for your household.",
)

# Progress breadcrumb
st.html("""
<div style='display:flex;align-items:center;gap:0;margin-bottom:22px;'>
  <div style='background:#D8EDD0;color:#3A8C4E;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#D8EDD0;color:#3A8C4E;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#3A8C4E;color:white;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>3</div>
  <div style='margin-left:12px;font-size:0.82rem;color:#5A7A62;'>
    Household → Grocer Prices → <strong style='color:#1E5C32;'>This Week's Plan</strong>
  </div>
</div>
""")

# Preference summary chip + change link
if prefs:
    _chip_parts = []
    if cuisine:             _chip_parts.append(cuisine)
    if prefs.get("dinners"): _chip_parts.append(f"{prefs['dinners']} dinners")
    if prefs.get("nights_out"): _chip_parts.append(f"{prefs['nights_out']} nights out")
    if occasion and occasion != "Nothing special": _chip_parts.append(occasion)
    _chip_str = " · ".join(_chip_parts)
    _pref_col, _btn_col = st.columns([5, 1])
    with _pref_col:
        st.html(f"<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:12px;'>"
                f"📋 This week: <strong style='color:#1E5C32;'>{_chip_str}</strong>"
                + (f" · <em>{notes}</em>" if notes else "")
                + "</div>")
    with _btn_col:
        if st.button("Change preferences", key="change_prefs"):
            st.session_state["_show_prefs_form"] = True
            st.rerun()

totals   = plan["totals"]
meals    = plan["meals"]
servings = plan["servings"]

# Summary metrics
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Plan cost", f"${totals['whollyfare_plan']:.2f}")
with c2:
    st.metric("Found Money 💚", f"${totals['found_money']:.2f}",
              delta="saved vs. one store", delta_color="normal")
with c3:
    st.metric("vs. HelloFresh", f"${totals['vs_hellofresh']:.2f}", delta="you keep this")
with c4:
    st.metric("Dinners planned", len(meals))

# Cross-store callout
STORE_NAMES = {
    "kroger_palmyra": "Kroger", "food_lion_palmyra": "Food Lion",
    "aldi_rio": "Aldi", "harris_teeter_barracks": "Harris Teeter",
    "Kroger": "Kroger", "Food Lion": "Food Lion",
    "Aldi": "Aldi", "Harris Teeter": "Harris Teeter",
}
store_counts: dict[str, int] = {}
for meal in meals:
    for ing in meal["ingredients"]:
        sid = ing["store"]
        store_counts[sid] = store_counts.get(sid, 0) + 1

num_stores  = len(store_counts)
store_parts = "  ·  ".join(
    f"🏪 {STORE_NAMES.get(sid, sid)}: {count} items"
    for sid, count in store_counts.items()
)
callout_text = (
    f"{store_parts}  &nbsp;·&nbsp;  "
    f"<strong style='color:#BF5E00;'>Shopping across {num_stores} stores "
    f"saves you ${totals['found_money']:.2f} this week</strong>"
) if num_stores > 1 else store_parts

if callout_text:
    st.html(f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                        padding:10px 16px;margin:12px 0 20px 0;font-size:0.9rem;color:#5A3A00;'>
      {callout_text}
    </div>""")

# Meal cards
DAY_COLORS = ["#1E5C32", "#3A8C4E", "#5DAA6A", "#F28B30", "#BF5E00"]
card_cols  = st.columns(min(len(meals), 5))

for idx, meal in enumerate(meals):
    color       = DAY_COLORS[idx % len(DAY_COLORS)]
    cost        = meal["meal_cost"]
    per_serving = cost / servings if servings else 0
    raw_store   = meal.get("best_store", "")
    store_label = STORE_NAMES.get(raw_store, raw_store) if raw_store and raw_store != "—" else ""
    gf_badge    = (
        "<span style='background:#E3F4E8;color:#1E5C32;border-radius:10px;"
        "padding:2px 7px;font-size:10px;font-weight:600;'>GF</span> "
        if meal.get("gluten_free") else ""
    )
    store_line = (
        f"<div style='font-size:11px;color:#5A7A62;margin-bottom:4px;'>🏪 {store_label}</div>"
        if store_label else ""
    )
    with card_cols[idx % len(card_cols)]:
        st.html(f"""<div style='background:#FFFFFF;border-radius:10px;
                        box-shadow:0 1px 6px rgba(0,0,0,0.08);
                        border-top:4px solid {color};padding:14px 12px;margin-bottom:8px;'>
          <div style='font-size:11px;font-weight:700;color:{color};
                      letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px;'>{meal['day']}</div>
          <div style='font-size:13px;font-weight:700;color:#1E5C32;line-height:1.3;margin-bottom:8px;'>{meal['name']}</div>
          <div style='font-size:1.25rem;font-weight:800;color:#1E5C32;'>${cost:.2f}</div>
          <div style='font-size:11px;color:#5A7A62;margin-bottom:6px;'>${per_serving:.2f}/serving</div>
          {store_line}<div>{gf_badge}</div>
        </div>""")

st.divider()

# Meal detail expanders
st.subheader("Meal details")
st.caption("Tap any meal to see exactly which ingredients the engine chose and where to buy them.")

for meal in meals:
    with st.expander(f"**{meal['day']}** — {meal['name']}", expanded=False):
        if meal.get("allergen_notes"):
            st.info(f"⚠️ **Allergen notes:** {meal['allergen_notes']}", icon="🛡️")

        ings = meal.get("ingredients", [])
        if ings:
            h1, h2, h3, h4 = st.columns([3, 1, 2, 1])
            with h1: st.html("**Item**")
            with h2: st.markdown("**Qty**")
            with h3: st.markdown("**Store**")
            with h4: st.markdown("**Cost**")

            for ing in ings:
                c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
                sname = STORE_NAMES.get(ing.get("store",""), ing.get("store","")) or "—"
                with c1: st.caption(ing["item"])
                with c2: st.caption(ing["qty"])
                with c3: st.caption(sname)
                with c4: st.caption(f"${ing['cost']:.2f}")

        st.markdown(
            f"<div style='text-align:right;font-size:13px;font-weight:700;"
            f"color:#1E5C32;margin-top:8px;border-top:1px solid #D8EDD0;padding-top:6px;'>"
            f"Meal total: ${meal['meal_cost']:.2f}</div>")

st.divider()

# Constraint compliance
_constraint_parts = []
if household:
    try:
        _allergens, _diagnoses, _lifestyle = set(), set(), set()
        for _m in household.members:
            _allergens.update(_m.allergies)
            _diagnoses.update(d.value for d in _m.diagnoses)
            _lifestyle.update(t.value for t in _m.lifestyle_tags)
        if "celiac"      in _diagnoses: _constraint_parts.append("Gluten-free compliant")
        if _allergens:
            _constraint_parts.append(f"No {', '.join(a.replace('_',' ').capitalize() for a in sorted(_allergens))}")
        if "type1_diabetes" in _diagnoses or "type2_diabetes" in _diagnoses: _constraint_parts.append("Diabetes-aware")
        if "ibs_low_fodmap" in _diagnoses: _constraint_parts.append("Low-FODMAP")
        if "ckd"            in _diagnoses: _constraint_parts.append("CKD-safe")
        if "hypertension"   in _diagnoses: _constraint_parts.append("Low-sodium")
        for _t in sorted(_lifestyle): _constraint_parts.append(_t.replace("_","-").capitalize())
    except AttributeError:
        pass

_constraint_str = " · ".join(_constraint_parts) if _constraint_parts else "Standard filtering applied"
st.html(f"""<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
               padding:14px 18px;margin-bottom:20px;'>
  <span style='font-size:1rem;font-weight:700;color:#1E5C32;'>
    ✅ All {len(meals)} meals are safe for your household
  </span>
  <span style='font-size:0.85rem;color:#3A8C4E;margin-left:12px;'>{_constraint_str}</span>
</div>""")

# CTAs
_c1, _c2 = st.columns(2)
with _c1:
    if st.button("✅ Go to Sunday Buy-Off — confirm this week →", type="primary", use_container_width=True):
        st.switch_page("pages/4_Sunday_BuyOff.py")
with _c2:
    if st.button("🔄 Regenerate with different preferences", use_container_width=True):
        st.session_state["_show_prefs_form"] = True
        st.rerun()
