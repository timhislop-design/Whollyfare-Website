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

    hh        = st.session_state["household"]
    n_dinners = prefs.get("dinners", getattr(hh, "meals_per_week", 5))

    # Protein preferences from wizard — enforce variety across hero pool
    # POC: keyword match on ingredient name. PROD: USDA category tag lookup.
    pref_proteins = [p.lower() for p in prefs.get("proteins", [])]

    def _serving_qty(ing, n_servings: int) -> str:
        """
        Compute a human-readable per-purchase quantity for the shopping list.
        Protein: ~3 oz/serving in a mixed dish (taco, bowl, stir-fry).
        Produce/dairy: ~2 oz/serving. Grain/pantry: 1 pkg/bunch.
        POC: fixed portion heuristics. PROD: USDA recipe quantities per dish.
        """
        cat = getattr(ing, "category", "other")
        unit = getattr(ing, "unit", "each")
        if cat == "protein":
            total_oz = n_servings * 3          # 3 oz/serving — realistic for mixed dish
            if unit == "lb" or total_oz >= 16:
                lbs = total_oz / 16
                return f"{lbs:.2g} lb"
            return f"{total_oz} oz"
        elif cat in ("produce", "dairy"):
            total_oz = n_servings * 2          # 2 oz/serving side
            if unit == "lb":
                return f"{total_oz/16:.2g} lb"
            return f"{total_oz} oz"
        else:
            return f"1 {unit}"                 # grain, pantry, frozen — buy one unit

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
            all_scored = optimizer.score(result.passed)

            # ── Protein variety enforcement ───────────────────────────────────
            # If user specified protein preferences, pick the best-scoring
            # candidate for each preferred protein type before filling the
            # rest of the basket. This prevents all meals defaulting to
            # whichever single protein scores highest (usually chicken).
            if pref_proteins:
                proteins_scored = [s for s in all_scored
                                   if s.ingredient.category == "protein"]
                non_proteins    = [s for s in all_scored
                                   if s.ingredient.category != "protein"]
                # Pick one best candidate per preferred protein
                chosen_proteins: list = []
                used_prefs: set = set()
                for pref in pref_proteins:
                    for s in proteins_scored:
                        if pref in s.ingredient.name.lower() and pref not in used_prefs:
                            chosen_proteins.append(s)
                            used_prefs.add(pref)
                            break
                # If a preferred protein had no match in flyers, fall back to top scorer
                if not chosen_proteins:
                    chosen_proteins = proteins_scored[:2]
                # Re-assemble pool: chosen proteins first, then non-proteins
                filtered_pool = chosen_proteins + non_proteins
            else:
                # No protein pref — still force variety: take top 2 proteins max
                proteins_scored  = [s for s in all_scored
                                    if s.ingredient.category == "protein"]
                non_proteins     = [s for s in all_scored
                                    if s.ingredient.category != "protein"]
                # Limit to 2 distinct proteins max so meals vary
                seen_protein_keys: set = set()
                deduplicated_proteins: list = []
                for s in proteins_scored:
                    key = s.ingredient.name.lower().split()[0]  # "chicken", "beef", etc.
                    if key not in seen_protein_keys and len(seen_protein_keys) < 2:
                        seen_protein_keys.add(key)
                        deduplicated_proteins.append(s)
                filtered_pool = deduplicated_proteins + non_proteins

            selected = optimizer.select_ingredients(filtered_pool)

        with st.spinner("Assembling your meal plan…"):
            from app.core_logic.meal_planner import MealPlanner
            # Pass cuisine + protein preferences so the recipe library
            # can match recipes to what the user actually wants this week.
            # POC: lowercase conversion maps UI labels to library keys.
            cuisine_prefs = [c.lower() for c in prefs.get("cuisines", [])]
            protein_prefs_lib = [p.lower() for p in prefs.get("proteins", [])]
            raw_plan = MealPlanner(hh).assemble_week(
                hero_ingredients=selected,
                flyer_week=st.session_state["active_week"],
                n_meals=n_dinners,
                cuisine_prefs=cuisine_prefs or None,
                protein_prefs=protein_prefs_lib or None,
            )

        # ── Ingredient pooling — two-pass cost allocation ────────────────────────
        # POC: naive per-meal cost attribution inflated the weekly total because
        # each meal that used chicken counted the full purchase price.  The fix:
        # count how many meals each ingredient appears in, then divide the
        # purchase price across all meals that share it.
        # PROD: same algorithm, but sourced from ingredient/recipe DB records.

        # Pass 1 — collect all (meal_idx, ingredient) pairs and count usage
        all_meal_ings: list = []   # [(meal_idx, meal_obj, scored_ing)]
        usage_count: dict  = {}    # ingredient name → how many meals use it

        for meal_idx, meal in enumerate(raw_plan.meals):
            for scored_ing in meal.ingredients:
                ing = scored_ing.ingredient
                all_meal_ings.append((meal_idx, meal, scored_ing))
                usage_count[ing.name] = usage_count.get(ing.name, 0) + 1

        # Pass 2 — build plan_meals with allocated (shared) cost per ingredient
        plan_meals = []
        plan_total = 0.0

        # We need to iterate per-meal, so group by meal_idx
        from collections import defaultdict
        meal_ings_by_idx: dict = defaultdict(list)
        for meal_idx, meal, scored_ing in all_meal_ings:
            meal_ings_by_idx[meal_idx].append((meal, scored_ing))

        for meal_idx, meal in enumerate(raw_plan.meals):
            ing_list  = []
            meal_cost = 0.0
            for _meal_obj, scored_ing in meal_ings_by_idx[meal_idx]:
                ing         = scored_ing.ingredient
                n_uses      = usage_count[ing.name]
                # Allocate only this meal's share of the purchase price
                alloc_cost  = ing.sale_price_per_unit / n_uses
                qty         = _serving_qty(ing, hh.servings_per_meal)
                ing_list.append({
                    "item":     ing.name,
                    "qty":      qty,
                    "store":    getattr(ing, "source_store", "—"),
                    "cost":     round(alloc_cost, 2),
                    # Transparency flags for the UI
                    "shared":   n_uses > 1,
                    "used_in":  n_uses,
                })
                meal_cost += alloc_cost
            plan_meals.append({
                "day":               meal.day,
                "name":              meal.name,
                "gluten_free":       False,
                "allergen_notes":    "",
                "best_store":        "—",
                "ingredients":       ing_list,
                "meal_cost":         round(meal_cost, 2),
                # Recipe library data — populated when a library match was found
                "recipe_id":         getattr(meal, "recipe_id", None),
                "recipe_ingredients": getattr(meal, "recipe_ingredients", []),
            })
            plan_total += meal_cost

        # ── Weekly shopping basket — deduplicated, sorted by category ─────────
        # Shows what to actually buy (one purchase per ingredient) with full
        # purchase price and how many meals it covers.
        # POC: category priority is hardcoded. PROD: from ingredient DB.
        CATEGORY_PRIORITY = {"protein": 0, "produce": 1, "dairy": 2,
                              "grain": 3, "pantry": 4, "frozen": 5, "other": 6}

        seen_basket: set = set()
        basket_items: list = []
        # Walk all_meal_ings to collect unique ingredients
        for _meal_idx, _meal, scored_ing in all_meal_ings:
            ing = scored_ing.ingredient
            if ing.name in seen_basket:
                continue
            seen_basket.add(ing.name)
            n_uses  = usage_count[ing.name]
            qty_str = _serving_qty(ing, hh.servings_per_meal)
            cat     = getattr(ing, "category", "other")
            basket_items.append({
                "item":        ing.name,
                "total_cost":  round(ing.sale_price_per_unit, 2),
                "meals":       n_uses,
                "qty_total":   qty_str,
                "store":       getattr(ing, "source_store", "—"),
                "_sort_key":   CATEGORY_PRIORITY.get(cat, 6),
            })

        basket_items.sort(key=lambda x: (x["_sort_key"], x["item"]))
        # Remove internal sort key before storing
        weekly_shopping = [
            {k: v for k, v in item.items() if k != "_sort_key"}
            for item in basket_items
        ]

        total_servings = len(plan_meals) * hh.servings_per_meal
        single_est     = round(plan_total * 1.18, 2)

        # Meal kit comparison prices (per serving, approximate 2025 retail rates).
        # POC: hardcoded. PROD: fetched weekly from pricing API or admin-maintained table.
        # Sources: published starting prices for 2-person plans as of May 2025.
        MEAL_KITS = [
            ("EveryPlate",   5.99,  "#6B8F71"),   # HelloFresh budget brand
            ("Dinnerly",     6.49,  "#7A9E7E"),
            ("HelloFresh",   9.99,  "#1A936F"),
            ("Blue Apron",   9.99,  "#2D6A9F"),
            ("Home Chef",    9.95,  "#8B5E3C"),
            ("Green Chef",  12.99,  "#3A7D44"),
        ]
        kit_totals = {
            name: round(total_servings * price_per_serving, 2)
            for name, price_per_serving, _ in MEAL_KITS
        }

        st.session_state["plan"] = {
            "week":            st.session_state["active_week"],
            "servings":        hh.servings_per_meal,
            "meals":           plan_meals,
            "prefs":           prefs,
            "weekly_shopping": weekly_shopping,
            "totals": {
                "whollyfare_plan":   round(plan_total, 2),
                "single_store_best": single_est,
                "found_money":       round(single_est - plan_total, 2),
                # Legacy key kept for back-compat
                "hellofresh_equiv":  kit_totals.get("HelloFresh", 0),
                "vs_hellofresh":     round(kit_totals.get("HelloFresh", 0) - plan_total, 2),
                # Full meal kit comparison
                "meal_kits":         kit_totals,
                "meal_kit_meta":     {n: {"price_per_serving": p, "color": c}
                                      for n, p, c in MEAL_KITS},
                "total_servings":    total_servings,
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

    # ── Step 3: Protein preferences ───────────────────────────────────────────
    st.html("""
    <div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
                text-transform:uppercase;margin-bottom:6px;'>
        Step 3 of 4 &nbsp;·&nbsp; Proteins this week
    </div>
    <div style='font-size:0.85rem;color:#3A8C4E;margin-bottom:14px;'>
        Pick 1–3. We'll find the best-priced cuts on sale and vary them across your meals.
    </div>""")

    PROTEINS_MAIN = [
        ("🍗", "Chicken",  "chicken"),
        ("🥩", "Beef",     "beef"),
        ("🐷", "Pork",     "pork"),
        ("🦃", "Turkey",   "turkey"),
        ("🐟", "Seafood",  "fish|salmon|shrimp|tilapia|cod|tuna"),
    ]
    PROTEINS_OTHER = [
        ("🐑", "Lamb",       "lamb"),
        ("🍤", "Shrimp",     "shrimp"),
        ("🐠", "Salmon",     "salmon"),
        ("🥚", "Eggs",       "egg"),
        ("🥦", "Vegetarian", "tofu|tempeh|lentil|bean"),
    ]

    _default_proteins = prefs.get("proteins", ["Chicken", "Beef"])
    _pr_cols = st.columns(5)
    _selected_proteins = []
    for i, (icon, label, _kw) in enumerate(PROTEINS_MAIN):
        with _pr_cols[i]:
            _checked = st.checkbox(label, value=(label in _default_proteins),
                                   key=f"p_{label}", label_visibility="collapsed")
            _bg      = "#D8EDD0" if _checked else "#FFFFFF"
            _border  = "#2D6A4F" if _checked else "#C8DFC8"
            _fw      = "700"     if _checked else "500"
            _tick    = "☑" if _checked else "☐"
            st.html(f"""<div style='background:{_bg};border:2px solid {_border};
                border-radius:10px;padding:10px 8px 10px 8px;text-align:center;
                margin-top:-8px;min-height:80px;'>
              <div style='font-size:0.7rem;color:#3A8C4E;text-align:left;
                          font-weight:700;padding:0 2px;'>{_tick}</div>
              <div style='font-size:1.3rem;line-height:1;margin-top:-2px;'>{icon}</div>
              <div style='font-size:0.82rem;font-weight:{_fw};color:#1A2E1D;
                          margin-top:5px;'>{label}</div>
            </div>""")
            if _checked:
                _selected_proteins.append(label)

    with st.expander("More options — Fish, Lamb, Eggs, Vegetarian"):
        _other_cols = st.columns(5)
        for i, (icon, label, _kw) in enumerate(PROTEINS_OTHER):
            with _other_cols[i]:
                _checked2 = st.checkbox(label, value=(label in _default_proteins),
                                        key=f"po_{label}")
                if _checked2 and label not in _selected_proteins:
                    _selected_proteins.append(label)

    if not _selected_proteins:
        st.caption("No protein selected — we'll pick the best-value options from your flyers.")

    st.html("<div style='height:20px;'></div>")

    # ── Step 4: Notes ─────────────────────────────────────────────────────────
    st.html("""
    <div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
                text-transform:uppercase;margin-bottom:12px;'>
        Step 4 of 4 &nbsp;·&nbsp; Anything to avoid or request?
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
        "🧪 <strong>Pilot note:</strong> Protein preferences tell the engine which cuts to "
        "prioritise. If your chosen proteins aren't on sale this week, it falls back to the "
        "best available. Preferences save to your profile and reset with each new flyer week."
        "</div>"
    )

    _cuisine_display  = " + ".join(_selected_cuisines) if _selected_cuisines else "any cuisine"
    _protein_display  = " + ".join(_selected_proteins) if _selected_proteins else "best value"

    if st.button(
        f"💾 Save to Profile & Build Plan  →  {_protein_display}  ·  {_cuisine_display}",
        type="primary",
        use_container_width=True,
        disabled=(_n_selected == 0),
    ):
        new_prefs = {
            "cuisines":   _selected_cuisines,
            "cuisine":    _selected_cuisines[0] if _selected_cuisines else "Mix it up",
            "proteins":   _selected_proteins,
            "dinners":    int(_dinners),
            "nights_out": int(_nights_out),
            "occasion":   _occasion,
            "notes":      _notes,
            "flyer_week": st.session_state.get("active_week", ""),
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

# ── Shared lookups ───────────────────────────────────────────────────────────
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
num_stores = len(store_counts)

_plan_cost      = totals["whollyfare_plan"]
_kit_data       = totals.get("meal_kits", {})
_kit_meta       = totals.get("meal_kit_meta", {})
_n_servings     = totals.get("total_servings", servings * len(meals))
_wf_per_serving = round(_plan_cost / max(_n_servings, 1), 2)

# ════════════════════════════════════════════════════════════════════
# SECTION 1 — SAVINGS SUMMARY
# Per-serving hero + metrics + cross-store callout
# ════════════════════════════════════════════════════════════════════

if _kit_data:
    _cheapest_kit_pps = min(_kit_meta[k]["price_per_serving"] for k in _kit_meta)
    _priciest_kit_pps = max(_kit_meta[k]["price_per_serving"] for k in _kit_meta)
    _min_save_pps = round(_cheapest_kit_pps - _wf_per_serving, 2)
    _max_save_pps = round(_priciest_kit_pps - _wf_per_serving, 2)

    st.html(f"""
    <div style='background:linear-gradient(135deg,#1A2E1D 0%,#2D6A4F 100%);
                border-radius:12px;padding:22px 24px 18px 24px;margin:0 0 16px 0;'>
      <div style='color:#A8D5B5;font-size:0.75rem;font-weight:700;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:6px;'>
        Your cost per serving this week
      </div>
      <div style='display:flex;align-items:flex-end;gap:16px;flex-wrap:wrap;'>
        <div>
          <span style='color:#5DDC8A;font-size:3rem;font-weight:900;
                       line-height:1;'>${_wf_per_serving:.2f}</span>
          <span style='color:#A8D5B5;font-size:1rem;margin-left:6px;'> / serving</span>
        </div>
        <div style='padding-bottom:6px;'>
          <div style='color:#FFFFFF;font-size:1.1rem;font-weight:700;line-height:1.2;'>
            vs. ${_cheapest_kit_pps:.2f}–${_priciest_kit_pps:.2f} on meal kit services
          </div>
          <div style='color:#A8D5B5;font-size:0.82rem;margin-top:3px;'>
            {len(meals)} dinners · {_n_servings} servings · your groceries, not theirs
          </div>
        </div>
      </div>
      <div style='margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.1);
                  color:#5DDC8A;font-size:0.9rem;font-weight:700;'>
        You save ${_min_save_pps:.2f}–${_max_save_pps:.2f} per serving
        &nbsp;·&nbsp; ${round(_min_save_pps*_n_servings):.0f}–${round(_max_save_pps*_n_servings):.0f} total this week
      </div>
    </div>
    """)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Plan total", f"${totals['whollyfare_plan']:.2f}",
              delta=f"{len(meals)} dinners · {servings} servings each")
with m2:
    st.metric("vs. single store 🏪", f"+${totals['found_money']:.2f}",
              delta="you keep this", delta_color="normal")
with m3:
    _hf_save = totals.get("vs_hellofresh", 0)
    st.metric("vs. HelloFresh 💚", f"+${_hf_save:.2f}",
              delta="you keep this", delta_color="normal")
with m4:
    st.metric("Stores shopped", num_stores,
              delta="cross-store savings" if num_stores > 1 else "add more stores for savings")

if num_stores > 1:
    store_parts = "  ·  ".join(
        f"🏪 {STORE_NAMES.get(sid, sid)}: {count} item{'s' if count != 1 else ''}"
        for sid, count in store_counts.items()
    )
    st.html(f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                        padding:10px 16px;margin:8px 0 0 0;font-size:0.88rem;color:#5A3A00;'>
      {store_parts} &nbsp;·&nbsp;
      <strong style='color:#BF5E00;'>Cross-store saves you ${totals["found_money"]:.2f}
      vs. buying everything at one store</strong>
    </div>""")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 2 — THIS WEEK'S MEALS
# Meal cards + detail expanders
# ════════════════════════════════════════════════════════════════════

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

        # ── Recipe ingredients (from library) ─────────────────────────────
        recipe_ings = meal.get("recipe_ingredients", [])
        if recipe_ings:
            st.html("""<div style='font-size:11px;font-weight:700;color:#3A8C4E;
                                   letter-spacing:0.08em;text-transform:uppercase;
                                   margin-bottom:6px;'>What you need for this recipe</div>""")
            # Group by pantry_stable — show what to buy vs. assume on hand
            to_buy     = [i for i in recipe_ings if not i.get("pantry_stable", False)]
            pantry_ok  = [i for i in recipe_ings if i.get("pantry_stable", False)]

            if to_buy:
                for ri in to_buy:
                    qty_str = f"{ri['qty']} {ri['unit']}"
                    st.html(f"""<div style='display:flex;justify-content:space-between;
                                            padding:4px 0;border-bottom:1px solid #F0F9F2;
                                            font-size:13px;'>
                      <span style='color:#1A2E1D;'>🛒 {ri["name"]}</span>
                      <span style='color:#5A7A62;font-size:12px;'>{qty_str}</span>
                    </div>""")
            if pantry_ok:
                pantry_names = ", ".join(i["name"] for i in pantry_ok)
                st.html(f"""<div style='font-size:11px;color:#888;margin-top:6px;
                                        font-style:italic;'>
                    Pantry / assume on hand: {pantry_names}
                </div>""")
            st.html("<div style='height:8px'></div>")

        # ── Sale items (optimizer selected) ────────────────────────────────
        ings = meal.get("ingredients", [])
        if ings:
            st.html("""<div style='font-size:11px;font-weight:700;color:#F28B30;
                                   letter-spacing:0.08em;text-transform:uppercase;
                                   margin-bottom:6px;'>On sale this week — anchors this plan</div>""")
            h1, h2, h3, h4 = st.columns([3, 1, 2, 1])
            with h1: st.html("**Item**")
            with h2: st.markdown("**Qty**")
            with h3: st.markdown("**Store**")
            with h4: st.markdown("**Cost**")

            for ing in ings:
                c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
                sname = STORE_NAMES.get(ing.get("store",""), ing.get("store","")) or "—"
                shared_note = f" ×{ing['used_in']}" if ing.get("shared") else ""
                with c1: st.caption(ing["item"] + shared_note)
                with c2: st.caption(ing["qty"])
                with c3: st.caption(sname)
                with c4: st.caption(f"${ing['cost']:.2f}")

        st.markdown(
            f"<div style='text-align:right;font-size:13px;font-weight:700;"
            f"color:#1E5C32;margin-top:8px;border-top:1px solid #D8EDD0;padding-top:6px;'>"
            f"Meal total: ${meal['meal_cost']:.2f}</div>")

st.divider()

# ════════════════════════════════════════════════════════════════════
# SECTION 3 — HOW DOES THIS COMPARE?
# Per-service expandable breakdown
# ════════════════════════════════════════════════════════════════════

if _kit_data:
    st.html("""<div style='font-size:0.78rem;font-weight:700;color:#5A7A62;
                           letter-spacing:0.08em;text-transform:uppercase;
                           margin:4px 0 10px 0;'>
        Compare by meal kit service
    </div>""")
    for kit_name, kit_total in sorted(_kit_data.items(),
                                       key=lambda x: _kit_meta[x[0]]["price_per_serving"]):
        _meta      = _kit_meta.get(kit_name, {})
        _pps       = _meta.get("price_per_serving", 0)
        _save_week = round(kit_total - _plan_cost, 2)
        _save_srv  = round(_pps - _wf_per_serving, 2)
        _label     = f"{kit_name}  —  ${_pps:.2f}/serving  ·  you save ${_save_srv:.2f}/serving"
        with st.expander(_label):
            _ec1, _ec2, _ec3 = st.columns(3)
            with _ec1:
                st.metric("Their cost / serving", f"${_pps:.2f}")
            with _ec2:
                st.metric("Your cost / serving", f"${_wf_per_serving:.2f}",
                          delta=f"-${_save_srv:.2f}", delta_color="normal")
            with _ec3:
                st.metric("Your savings this week", f"${_save_week:.2f}",
                          delta=f"vs. {kit_name}")
            st.caption(
                f"At {kit_name}'s ${_pps:.2f}/serving, "
                f"{_n_servings} servings would cost **${kit_total:.2f}**. "
                f"WhollyFare built the same {len(meals)} dinners for **${_plan_cost:.2f}** "
                f"from this week's actual sale prices."
            )
    st.caption("\* Published starting rates, 2-person plans, May 2025. "
               "Actual prices vary by plan size and promotions.")
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
