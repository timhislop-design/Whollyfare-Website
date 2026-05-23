"""12_Recipes.py — WhollyFare® Recipe Library

Browse all 150 recipes by cuisine, save favorites, add family recipes,
apply dietary substitutions, and spin the roulette for a random pick.

Pilot vs. Production
--------------------
Pilot:  Favorites and family recipes saved to Supabase household_recipes table.
        Substitution rules are hardcoded for three pilot constraint sets:
        gluten-free, dairy-free, low-sodium.
PROD:   Substitution engine driven by household health profile automatically.
        Recipe library expanded via web search at 50+ households.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import random
import json
from datetime import datetime

import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="Recipe Library · WhollyFare",
    page_icon="📖",
    layout="wide",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

style.inject()
style.maybe_scroll_to_top()

# ── Load recipe library ────────────────────────────────────────────────────────
try:
    from app.data.recipe_library import ALL_RECIPES
    _lib_ok = True
except ImportError:
    ALL_RECIPES = []
    _lib_ok = False

# ── Session state keys ─────────────────────────────────────────────────────────
if "recipe_favorites"   not in st.session_state: st.session_state["recipe_favorites"]   = set()
if "recipe_subs_active" not in st.session_state: st.session_state["recipe_subs_active"] = []
if "roulette_result"    not in st.session_state: st.session_state["roulette_result"]     = None
if "recipe_view"        not in st.session_state: st.session_state["recipe_view"]         = "browse"
if "_add_recipe_open"   not in st.session_state: st.session_state["_add_recipe_open"]    = False
if "_family_recipes"    not in st.session_state: st.session_state["_family_recipes"]     = []

# ── Supabase helpers ───────────────────────────────────────────────────────────
def _hh_id():
    hh = st.session_state.get("household")
    return getattr(hh, "id", None) or st.session_state.get("household_db", {}).get("id")

def _load_favorites_from_db() -> set:
    if not state.is_authenticated():
        return set()
    hid = _hh_id()
    if not hid:
        return set()
    rows = state._sb_select("household_recipes",
                            filters={"household_id": hid, "is_favorite": True})
    return {r["recipe_id"] for r in rows} if rows else set()

def _toggle_favorite_db(recipe_id: str, name: str) -> bool:
    if not state.is_authenticated():
        return False
    hid = _hh_id()
    if not hid:
        return False
    favs: set = st.session_state["recipe_favorites"]
    now_fav = recipe_id not in favs
    state._sb_insert("household_recipes", {
        "household_id": hid,
        "recipe_id":    recipe_id,
        "recipe_name":  name,
        "is_favorite":  now_fav,
        "source":       "library",
        "created_at":   datetime.utcnow().isoformat(),
    })
    if now_fav:
        favs.add(recipe_id)
    else:
        favs.discard(recipe_id)
    st.session_state["recipe_favorites"] = favs
    return now_fav

def _save_family_recipe(recipe: dict) -> bool:
    if not state.is_authenticated():
        return False
    hid = _hh_id()
    if not hid:
        return False
    state._sb_insert("household_recipes", {
        "household_id":  hid,
        "recipe_id":     recipe["id"],
        "recipe_name":   recipe["name"],
        "is_favorite":   True,
        "source":        "family",
        "recipe_data":   json.dumps(recipe),
        "created_at":    datetime.utcnow().isoformat(),
    })
    return True

# Load favorites from DB once per session
if state.is_authenticated() and not st.session_state.get("_favs_loaded"):
    st.session_state["recipe_favorites"] = _load_favorites_from_db()
    st.session_state["_favs_loaded"] = True

# ── Dietary substitution rules ─────────────────────────────────────────────────
SUBSTITUTIONS = {
    "gluten_free": {
        "label": "🌾 Gluten-Free",
        "rules": {
            "all-purpose flour": "Bob's Red Mill 1:1 GF flour",
            "flour":             "Bob's Red Mill 1:1 GF flour",
            "flour tortillas":   "corn tortillas",
            "pasta":             "gluten-free pasta",
            "soy sauce":         "tamari (GF soy sauce)",
            "breadcrumbs":       "GF breadcrumbs",
            "panko":             "GF panko",
            "beer":              "GF beer or chicken broth",
            "barley":            "quinoa",
            "couscous":          "quinoa or rice",
            "wheat":             "GF flour blend",
        }
    },
    "dairy_free": {
        "label": "🥛 Dairy-Free",
        "rules": {
            "butter":        "vegan butter or olive oil",
            "milk":          "oat milk or almond milk",
            "heavy cream":   "full-fat coconut milk",
            "cream":         "coconut cream",
            "sour cream":    "coconut yogurt",
            "cheese":        "nutritional yeast or dairy-free cheese",
            "parmesan":      "nutritional yeast",
            "mozzarella":    "dairy-free mozzarella",
            "cheddar":       "dairy-free cheddar",
            "cream cheese":  "dairy-free cream cheese",
            "yogurt":        "coconut yogurt",
            "half and half": "oat milk",
            "ricotta":       "tofu ricotta",
        }
    },
    "low_sodium": {
        "label": "🧂 Low-Sodium",
        "rules": {
            "salt":             "reduce by half",
            "soy sauce":        "low-sodium soy sauce",
            "tamari":           "low-sodium tamari",
            "broth":            "unsalted broth",
            "chicken broth":    "unsalted chicken broth",
            "beef broth":       "unsalted beef broth",
            "vegetable broth":  "unsalted vegetable broth",
            "canned tomatoes":  "no-salt-added canned tomatoes",
            "tomato paste":     "no-salt-added tomato paste",
            "olives":           "rinse well before using",
            "capers":           "rinse well before using",
            "bacon":            "low-sodium turkey bacon",
            "ham":              "low-sodium ham",
            "feta":             "reduce other salt entirely",
        }
    }
}

def _apply_subs(ingredients: list, active_subs: list) -> list:
    """Return ingredient list with active substitutions applied."""
    if not active_subs:
        return ingredients
    result = []
    for ing in ingredients:
        lower = ing["name"].lower()
        sub_note = None
        for sub_key in active_subs:
            for original, replacement in SUBSTITUTIONS[sub_key]["rules"].items():
                if original in lower:
                    sub_note = replacement
                    break
            if sub_note:
                break
        result.append({**ing, "_sub": sub_note})
    return result

# ── Cuisine config ─────────────────────────────────────────────────────────────
CUISINE_META = {
    "mexican":       ("🌮", "Mexican",       "#FFF3E0", "#F28B30"),
    "italian":       ("🍝", "Italian",       "#FFF9C4", "#F4A600"),
    "asian":         ("🍜", "Asian",         "#E8F5E9", "#3A8C4E"),
    "american":      ("🍗", "American",      "#FBE9E7", "#E64A19"),
    "mediterranean": ("🥗", "Mediterranean", "#E3F2FD", "#1976D2"),
}

COMPLEXITY_BADGE = {
    "weeknight": ("⚡", "#E8F5E9", "#2E7D32"),
    "weekend":   ("👨‍🍳", "#FFF3E0", "#E65100"),
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS — defined before the view logic
# ══════════════════════════════════════════════════════════════════════════════

def _pin_recipe_to_plan(recipe: dict) -> None:
    """Pin a recipe as a preference hint for the next plan generation."""
    pinned = st.session_state.get("pinned_recipes", [])
    if recipe["id"] not in [r["id"] for r in pinned]:
        pinned.append(recipe)
        st.session_state["pinned_recipes"] = pinned

def _add_to_shopping(recipe: dict, active_subs: list) -> None:
    """Add recipe ingredients (with subs applied) to the session shopping list."""
    ings = _apply_subs(recipe.get("ingredients", []), active_subs)
    cart = st.session_state.get("shopping_cart", [])
    existing = {i.get("item", "").lower() for i in cart}
    for ing in ings:
        sub  = ing.get("_sub")
        name = sub if sub and "reduce" not in sub else ing["name"]
        if name.lower() not in existing:
            cart.append({
                "item":   name,
                "qty":    f"{ing['qty']} {ing['unit']}",
                "store":  "—",
                "cost":   0.0,
                "source": "recipe_library",
            })
            existing.add(name.lower())
    st.session_state["shopping_cart"] = cart

def _render_recipe_card(recipe: dict, active_subs: list, favs: set,
                        expanded: bool = False, show_fav: bool = True) -> None:
    """Render a single recipe as a collapsible card with substitution highlights."""
    rid    = recipe["id"]
    name   = recipe["name"]
    protein = recipe.get("primary_protein", "")
    mins   = recipe.get("active_minutes", 0)
    serves = recipe.get("serves", 4)
    cplx   = recipe.get("complexity", "weeknight")
    flags  = recipe.get("dietary_flags", {})
    tags   = recipe.get("tags", [])

    is_fav   = rid in favs
    fav_icon = "⭐" if is_fav else "☆"

    cplx_icon, _, _ = COMPLEXITY_BADGE.get(cplx, ("", "", ""))
    meta_line = f"{cplx_icon} {mins} min · serves {serves} · {protein}"

    badge_parts = []
    if flags.get("gluten_free"):  badge_parts.append("GF")
    if flags.get("dairy_free"):   badge_parts.append("DF")
    if flags.get("vegetarian"):   badge_parts.append("Veg")
    if flags.get("vegan"):        badge_parts.append("Vegan")
    if flags.get("low_carb"):     badge_parts.append("LC")
    badge_html = " ".join(
        f"<span style='background:#E8F5E9;color:#1E5C32;font-size:0.7rem;"
        f"padding:1px 6px;border-radius:8px;font-weight:600;'>{b}</span>"
        for b in badge_parts
    )

    with st.expander(f"{name}  ·  {meta_line}", expanded=expanded):
        hdr_c1, hdr_c2 = st.columns([5, 1])
        with hdr_c1:
            if badge_html:
                st.html(f"<div style='margin-bottom:6px;'>{badge_html}</div>")
            if tags:
                st.html(f"<div style='font-size:0.75rem;color:#9AA8A0;"
                        f"margin-bottom:8px;'>{' · '.join(tags)}</div>")
        with hdr_c2:
            if show_fav:
                help_text = "Remove from favorites" if is_fav else "Save to favorites"
                if st.button(fav_icon, key=f"fav_{rid}", help=help_text):
                    _toggle_favorite_db(rid, name)
                    st.rerun()

        ings = _apply_subs(recipe.get("ingredients", []), active_subs)
        if ings:
            st.html("<div style='font-size:0.78rem;font-weight:700;color:#5A7A62;"
                    "letter-spacing:0.08em;text-transform:uppercase;"
                    "margin-bottom:6px;'>Ingredients</div>")
            rows_html = ""
            for ing in ings:
                qty_str  = f"{ing['qty']} {ing['unit']}"
                ing_name = ing["name"]
                sub      = ing.get("_sub")
                stable   = ing.get("pantry_stable", False)
                if sub:
                    name_cell = (
                        f"<span style='text-decoration:line-through;color:#9AA8A0;'>{ing_name}</span>"
                        f" → <span style='color:#BF5E00;font-weight:600;'>{sub}</span>"
                    )
                else:
                    name_cell = ing_name
                stable_badge = (
                    "<span style='font-size:0.7rem;color:#9AA8A0;margin-left:4px;'>pantry</span>"
                    if stable else ""
                )
                rows_html += (
                    f"<tr>"
                    f"<td style='padding:5px 10px 5px 0;font-size:0.85rem;"
                    f"border-bottom:1px solid #F0F9F2;white-space:nowrap;color:#5A7A62;'>{qty_str}</td>"
                    f"<td style='padding:5px 0;font-size:0.85rem;"
                    f"border-bottom:1px solid #F0F9F2;'>{name_cell}{stable_badge}</td>"
                    f"</tr>"
                )
            st.html(
                "<table style='width:100%;border-collapse:collapse;'>"
                "<tbody>" + rows_html + "</tbody></table>"
            )

        st.html("<div style='height:8px;'></div>")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📋 Add to this week's plan", key=f"plan_{rid}",
                         use_container_width=True):
                _pin_recipe_to_plan(recipe)
                st.success(f"{name} pinned to this week's plan.")
        with c2:
            if st.button("🛒 Add ingredients to shopping list",
                         key=f"shop_{rid}", use_container_width=True):
                _add_to_shopping(recipe, active_subs)
                st.success("Ingredients added to shopping list.")


def _render_add_recipe_form() -> None:
    """Form for adding a family recipe."""
    st.html("<div style='background:#F0F7F1;border:1px solid #C8E6C9;"
            "border-radius:10px;padding:18px 20px;margin:12px 0 20px 0;'>")
    with st.form("add_family_recipe"):
        st.html("<div style='font-size:1rem;font-weight:700;color:#1E5C32;"
                "margin-bottom:12px;'>Add a Family Recipe</div>")
        r_name    = st.text_input("Recipe name *", placeholder="e.g. Grandma's Chicken Soup")
        r_cuisine = st.selectbox("Cuisine", ["American", "Mexican", "Italian",
                                             "Asian", "Mediterranean", "Other"])
        r_protein = st.text_input("Main protein", placeholder="e.g. chicken, beef, none")
        c1, c2 = st.columns(2)
        with c1:
            r_serves = st.number_input("Serves", min_value=1, max_value=12, value=4, step=1)
        with c2:
            r_mins = st.number_input("Active minutes", min_value=5, max_value=240, value=30, step=5)
        st.html("<div style='font-size:0.85rem;font-weight:600;color:#5A7A62;"
                "margin:10px 0 4px 0;'>Ingredients (one per line: qty unit name)"
                "<br><span style='font-weight:400;'>e.g. 2 lbs chicken thighs</span></div>")
        r_ings_raw = st.text_area("Ingredients", height=140,
                                  placeholder="2 lbs chicken thighs\n3 cups chicken broth\n2 medium carrots\n...",
                                  label_visibility="collapsed")
        st.html("<div style='font-size:0.85rem;font-weight:600;color:#5A7A62;"
                "margin:10px 0 6px 0;'>Dietary flags</div>")
        df_cols = st.columns(6)
        with df_cols[0]: gf  = st.checkbox("GF")
        with df_cols[1]: dff = st.checkbox("Dairy-free")
        with df_cols[2]: veg = st.checkbox("Vegetarian")
        with df_cols[3]: vgn = st.checkbox("Vegan")
        with df_cols[4]: lc  = st.checkbox("Low-carb")
        with df_cols[5]: nf  = st.checkbox("Nut-free", value=True)
        r_notes = st.text_input("Notes (optional)", placeholder="e.g. Chas loves this, add extra garlic")
        submitted = st.form_submit_button("💾 Save family recipe", type="primary",
                                          use_container_width=True)
        if submitted:
            if not r_name.strip():
                st.error("Recipe name is required.")
            else:
                parsed_ings = []
                for line in r_ings_raw.strip().split("\n"):
                    parts = line.strip().split(None, 2)
                    if len(parts) >= 3:
                        try:
                            qty      = float(parts[0])
                            unit     = parts[1]
                            ing_name = parts[2]
                        except ValueError:
                            qty, unit, ing_name = 1.0, "each", line.strip()
                        parsed_ings.append({"name": ing_name, "qty": qty, "unit": unit,
                                            "category": "other", "pantry_stable": False})
                    elif line.strip():
                        parsed_ings.append({"name": line.strip(), "qty": 1.0, "unit": "each",
                                            "category": "other", "pantry_stable": False})
                new_recipe = {
                    "id":              f"FAM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "name":            r_name.strip(),
                    "cuisine":         r_cuisine.lower(),
                    "primary_protein": r_protein.strip(),
                    "ingredients":     parsed_ings,
                    "serves":          int(r_serves),
                    "active_minutes":  int(r_mins),
                    "complexity":      "weeknight",
                    "dietary_flags": {
                        "gluten_free": gf,  "dairy_free": dff,
                        "vegetarian":  veg, "vegan":      vgn,
                        "low_carb":    lc,  "nut_free":   nf,
                    },
                    "tags": ["family recipe"] + (["notes: " + r_notes] if r_notes else []),
                    "source": "family",
                }
                fam = st.session_state.get("_family_recipes", [])
                fam.append(new_recipe)
                st.session_state["_family_recipes"] = fam
                st.session_state["recipe_favorites"].add(new_recipe["id"])
                _save_family_recipe(new_recipe)
                st.session_state["_add_recipe_open"] = False
                st.success(f"✅ {r_name.strip()} saved to your family recipes!")
                st.rerun()
    st.html("</div>")


# ── Page header ────────────────────────────────────────────────────────────────
style.page_header("Recipe Library", "150 recipes across 5 cuisines · favorites · family recipes · substitutions")

# ── Top toolbar: view toggle ───────────────────────────────────────────────────
tb_col1, tb_col2, tb_col3, tb_col4 = st.columns([2, 2, 2, 2])
with tb_col1:
    if st.button("📖 Browse All", use_container_width=True,
                 type="primary" if st.session_state["recipe_view"] == "browse" else "secondary"):
        st.session_state["recipe_view"] = "browse"
        st.session_state["roulette_result"] = None
        st.rerun()
with tb_col2:
    if st.button("⭐ My Favorites", use_container_width=True,
                 type="primary" if st.session_state["recipe_view"] == "favorites" else "secondary"):
        st.session_state["recipe_view"] = "favorites"
        st.session_state["roulette_result"] = None
        st.rerun()
with tb_col3:
    if st.button("👨‍👩‍👧 Family Recipes", use_container_width=True,
                 type="primary" if st.session_state["recipe_view"] == "family" else "secondary"):
        st.session_state["recipe_view"] = "family"
        st.session_state["roulette_result"] = None
        st.rerun()
with tb_col4:
    if st.button("🎰 Recipe Roulette", use_container_width=True,
                 type="primary" if st.session_state["recipe_view"] == "roulette" else "secondary"):
        st.session_state["recipe_view"] = "roulette"
        st.rerun()

st.html("<div style='height:12px;'></div>")

# ── Substitution toggles ───────────────────────────────────────────────────────
st.html("<div style='font-size:0.78rem;font-weight:700;color:#5A7A62;"
        "letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>"
        "Dietary Substitutions — applies to all recipes below</div>")
sub_cols = st.columns(3)
for i, (sub_key, sub_data) in enumerate(SUBSTITUTIONS.items()):
    with sub_cols[i]:
        active  = sub_key in st.session_state["recipe_subs_active"]
        checked = st.checkbox(sub_data["label"], value=active, key=f"sub_{sub_key}")
        if checked and sub_key not in st.session_state["recipe_subs_active"]:
            st.session_state["recipe_subs_active"].append(sub_key)
            st.rerun()
        elif not checked and sub_key in st.session_state["recipe_subs_active"]:
            st.session_state["recipe_subs_active"].remove(sub_key)
            st.rerun()

active_subs = st.session_state["recipe_subs_active"]
if active_subs:
    sub_labels = " + ".join(SUBSTITUTIONS[s]["label"] for s in active_subs)
    st.html(f"<div style='background:#F0F7F1;border-left:3px solid #5DAA6A;"
            f"padding:8px 14px;border-radius:0 6px 6px 0;font-size:0.82rem;color:#1E5C32;"
            f"margin:8px 0;'>✅ Substitutions active: <strong>{sub_labels}</strong> — "
            f"ingredients shown with swaps highlighted in orange.</div>")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# RECIPE ROULETTE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["recipe_view"] == "roulette":
    st.html("<div style='font-size:1.1rem;font-weight:700;color:#1E5C32;"
            "margin-bottom:16px;'>🎰 Recipe Roulette</div>")
    pool = ALL_RECIPES[:]
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        r_cuisine = st.selectbox("Cuisine", ["Any"] + [v[1] for v in CUISINE_META.values()],
                                 key="roulette_cuisine")
    with r_col2:
        r_complexity = st.selectbox("Complexity", ["Any", "Weeknight ⚡", "Weekend 👨‍🍳"],
                                    key="roulette_complexity")
    with r_col3:
        r_protein = st.selectbox("Protein", ["Any", "Chicken", "Beef", "Pork",
                                             "Turkey", "Seafood", "Vegetarian"],
                                 key="roulette_protein")

    if r_cuisine != "Any":
        pool = [r for r in pool if r["cuisine"] == r_cuisine.lower()]
    if r_complexity == "Weeknight ⚡":
        pool = [r for r in pool if r["complexity"] == "weeknight"]
    elif r_complexity == "Weekend 👨‍🍳":
        pool = [r for r in pool if r["complexity"] == "weekend"]
    if r_protein != "Any":
        pool = [r for r in pool if r_protein.lower() in r["primary_protein"].lower()]

    if st.button("🎲 Spin the wheel", type="primary", use_container_width=True):
        if pool:
            st.session_state["roulette_result"] = random.choice(pool)
        else:
            st.warning("No recipes match those filters — try loosening them.")

    result = st.session_state.get("roulette_result")
    if result:
        _render_recipe_card(result, active_subs,
                            st.session_state["recipe_favorites"],
                            expanded=True, show_fav=True)


# ══════════════════════════════════════════════════════════════════════════════
# FAVORITES VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["recipe_view"] == "favorites":
    favs = st.session_state["recipe_favorites"]
    if not favs:
        st.html("<div style='font-size:0.95rem;color:#9AA8A0;font-style:italic;"
                "padding:32px 0;text-align:center;'>"
                "No favorites yet — browse the library and tap ⭐ to save recipes.</div>")
    else:
        fav_recipes = [r for r in ALL_RECIPES if r["id"] in favs]
        count = len(fav_recipes)
        st.html(f"<div style='font-size:0.88rem;color:#5A7A62;margin-bottom:16px;'>"
                f"{count} saved recipe{'s' if count != 1 else ''}</div>")
        for recipe in fav_recipes:
            _render_recipe_card(recipe, active_subs, favs, show_fav=True)


# ══════════════════════════════════════════════════════════════════════════════
# FAMILY RECIPES VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state["recipe_view"] == "family":
    st.html("<div style='font-size:1.1rem;font-weight:700;color:#1E5C32;"
            "margin-bottom:4px;'>👨‍👩‍👧 Family Recipes</div>")
    st.html("<div style='font-size:0.85rem;color:#5A7A62;margin-bottom:16px;'>"
            "Your household's go-to rotation. Saved recipes appear in your plan "
            "suggestions and shopping list.</div>")

    if st.button("+ Add a family recipe", type="primary"):
        st.session_state["_add_recipe_open"] = True

    if st.session_state["_add_recipe_open"]:
        _render_add_recipe_form()

    family_recipes = st.session_state.get("_family_recipes", [])
    if family_recipes:
        st.html("<div style='font-size:0.88rem;font-weight:700;color:#5A7A62;"
                "margin:16px 0 8px 0;'>Your family recipes</div>")
        for recipe in family_recipes:
            _render_recipe_card(recipe, active_subs,
                                st.session_state["recipe_favorites"], show_fav=True)
    elif not st.session_state["_add_recipe_open"]:
        st.html("<div style='font-size:0.88rem;color:#9AA8A0;font-style:italic;"
                "padding:16px 0;'>No family recipes added yet.</div>")


# ══════════════════════════════════════════════════════════════════════════════
# BROWSE ALL — grouped by cuisine
# ══════════════════════════════════════════════════════════════════════════════
else:
    search = st.text_input("🔍 Search recipes",
                           placeholder="e.g. chicken, pasta, quick...",
                           label_visibility="collapsed",
                           key="recipe_search")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        filter_complexity = st.selectbox("Complexity", ["All", "Weeknight ⚡", "Weekend 👨‍🍳"],
                                         key="filter_complexity")
    with f_col2:
        filter_protein = st.selectbox("Protein", ["All", "Chicken", "Beef", "Pork",
                                                   "Turkey", "Seafood", "Vegetarian"],
                                      key="filter_protein")
    with f_col3:
        filter_dietary = st.selectbox("Dietary",
                                      ["All", "Already GF", "Already Dairy-Free",
                                       "Vegetarian", "Vegan", "Low-Carb"],
                                      key="filter_dietary")

    filtered = ALL_RECIPES[:]
    if search:
        q = search.lower()
        filtered = [r for r in filtered if
                    q in r["name"].lower() or
                    q in r["primary_protein"].lower() or
                    any(q in i["name"].lower() for i in r["ingredients"])]
    if filter_complexity == "Weeknight ⚡":
        filtered = [r for r in filtered if r["complexity"] == "weeknight"]
    elif filter_complexity == "Weekend 👨‍🍳":
        filtered = [r for r in filtered if r["complexity"] == "weekend"]
    if filter_protein != "All":
        filtered = [r for r in filtered
                    if filter_protein.lower() in r["primary_protein"].lower()]
    if filter_dietary == "Already GF":
        filtered = [r for r in filtered if r["dietary_flags"].get("gluten_free")]
    elif filter_dietary == "Already Dairy-Free":
        filtered = [r for r in filtered if r["dietary_flags"].get("dairy_free")]
    elif filter_dietary == "Vegetarian":
        filtered = [r for r in filtered if r["dietary_flags"].get("vegetarian")]
    elif filter_dietary == "Vegan":
        filtered = [r for r in filtered if r["dietary_flags"].get("vegan")]
    elif filter_dietary == "Low-Carb":
        filtered = [r for r in filtered if r["dietary_flags"].get("low_carb")]

    total  = len(filtered)
    suffix = " — filtered" if total < len(ALL_RECIPES) else " across all cuisines"
    st.html(f"<div style='font-size:0.82rem;color:#5A7A62;margin:8px 0 16px 0;'>"
            f"Showing <strong>{total}</strong> recipe{'s' if total != 1 else ''}"
            + suffix + "</div>")

    favs = st.session_state["recipe_favorites"]
    by_cuisine: dict = {}
    for r in filtered:
        by_cuisine.setdefault(r["cuisine"], []).append(r)

    for cuisine_key, meta in CUISINE_META.items():
        recipes = by_cuisine.get(cuisine_key, [])
        if not recipes:
            continue
        icon, label, bg, accent = meta
        fav_count = sum(1 for r in recipes if r["id"] in favs)
        fav_note  = f" · {fav_count} ⭐" if fav_count else ""
        with st.expander(f"{icon} {label}  —  {len(recipes)} recipes{fav_note}",
                         expanded=(len(by_cuisine) == 1)):
            for recipe in recipes:
                _render_recipe_card(recipe, active_subs, favs, show_fav=True)
