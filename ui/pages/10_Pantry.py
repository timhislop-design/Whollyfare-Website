"""10_Pantry.py -- My Pantry

Shows the household's pantry: items WhollyFare assumes you have on hand.
These are excluded from the shopping list "buy this" section and cost $0
in meal estimates -- so keeping this list accurate keeps the cost math real.

Pilot vs. Production
---------------------
Pilot:  Pantry stored in session_state. Changes persist across pages in the
        same session but reset on browser refresh.
        Supabase persistence: saved to households.pantry_items JSONB column
        when authenticated (degrades gracefully if DB unavailable).
PROD:   Pantry syncs across devices. "I used this up" flow tracks depletion.
        Restock alerts when a recipe needs an item that's running low.
        Bulk import from a grocery receipt (scan your pantry).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="My Pantry - WhollyFare", page_icon="\U0001f9c2", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("My Pantry", "Dry pantry + fridge staples you have on hand. Uncheck anything you're out of — it goes on your shopping list.")

# -- Load current pantry -------------------------------------------------------
# If household_pantry is None, we're using PANTRY_DEFAULTS.
# Once the user makes any change, we copy the defaults into session_state
# and work from there.
raw = st.session_state.get("household_pantry")
if raw is None:
    current_pantry = set(state.PANTRY_DEFAULTS)
    using_defaults = True
else:
    current_pantry = set(raw)
    using_defaults = False

# -- Intro banner --------------------------------------------------------------
st.html(
    "<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;"
    "padding:12px 18px;margin-bottom:20px;font-size:0.9rem;color:#1E5C32;'>"
    "<strong>" + str(len(current_pantry)) + " items</strong> in your pantry &nbsp;·&nbsp; "
    "Dry pantry and fridge staples excluded from your shopping list — cost $0 in meal estimates."
    + (" &nbsp;<span style='color:#5A7A62;font-size:0.82rem;'>(using defaults)</span>" if using_defaults else "")
    + "</div>")

# -- Categorised pantry display ------------------------------------------------
CATEGORIES = {
    "Oils & Fats":        ["olive oil", "vegetable oil", "sesame oil", "butter", "cooking spray"],
    "Acids & Sauces":     ["soy sauce", "fish sauce", "worcestershire sauce", "hot sauce",
                           "apple cider vinegar", "white vinegar", "balsamic vinegar"],
    "Aromatics":          ["garlic", "onion", "shallot", "ginger"],
    "Dry Spices & Herbs": ["salt", "black pepper", "red pepper flakes", "paprika", "smoked paprika",
                           "cumin", "chili powder", "oregano", "thyme", "basil", "bay leaves",
                           "coriander", "turmeric", "cinnamon", "cayenne", "italian seasoning",
                           "garlic powder", "onion powder"],
    "Baking & Staples":   ["flour", "cornstarch", "sugar", "brown sugar", "honey",
                           "chicken broth", "beef broth", "vegetable broth"],
    "Condiments & Other": ["dijon mustard", "tomato paste", "lemon", "lime"],
    "Fridge & Condiments": ["ketchup", "mayonnaise", "yellow mustard", "ranch dressing",
                             "bbq sauce", "salsa", "cream cheese", "sour cream",
                             "jam", "pickles", "maple syrup", "peanut butter"],
}

# Collect any custom items (in pantry but not in any category)
all_default_items = set(item for items in CATEGORIES.values() for item in items)
custom_items = sorted(current_pantry - all_default_items)

changed = False

for category, items in CATEGORIES.items():
    with st.expander(category + " (" + str(sum(1 for i in items if i in current_pantry)) + "/" + str(len(items)) + ")", expanded=True):
        cols = st.columns(2)
        for idx, item in enumerate(items):
            col = cols[idx % 2]
            with col:
                in_pantry = item in current_pantry
                toggled = st.checkbox(
                    label=item.title(),
                    value=in_pantry,
                    key="pantry_chk_" + item.replace(" ", "_"),
                )
                if toggled != in_pantry:
                    if toggled:
                        current_pantry.add(item)
                    else:
                        current_pantry.discard(item)
                    changed = True

# -- Custom items section ------------------------------------------------------
st.divider()
st.markdown("**Your custom items**")

if custom_items:
    for item in custom_items:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.html(
                "<div style='padding:6px 0;font-size:0.95rem;color:#1A2E1D;'>"
                + item.title() + "</div>")
        with col2:
            if st.button("Remove", key="rm_" + item.replace(" ", "_"), use_container_width=True):
                current_pantry.discard(item)
                changed = True
                st.rerun()
else:
    st.html(
        "<div style='font-size:0.85rem;color:#9AA8A0;font-style:italic;padding:4px 0;'>"
        "No custom items yet.</div>")

# -- Add custom item -----------------------------------------------------------
with st.form("add_pantry_item", clear_on_submit=True):
    new_item = st.text_input("Add an item to your pantry",
                             placeholder="e.g. rice vinegar, tahini, miso paste...")
    submitted = st.form_submit_button("Add", use_container_width=True)
    if submitted and new_item.strip():
        clean = new_item.strip().lower()
        if clean not in current_pantry:
            current_pantry.add(clean)
            changed = True
            st.success(clean.title() + " added to pantry.")

# -- Out-of-stock summary + explicit save -------------------------------------
# Show items unchecked from defaults so the user sees what will hit their
# shopping list before committing the change.
out_of_stock_current = {item for item in state.PANTRY_DEFAULTS if item not in current_pantry}

if out_of_stock_current:
    st.divider()
    _oos_count = str(len(out_of_stock_current))
    _oos_names = " &nbsp;&middot;&nbsp; ".join(sorted(i.title() for i in out_of_stock_current))
    st.html(
        "<div style='font-size:0.9rem;font-weight:700;color:#BF5E00;margin-bottom:6px;'>"
        + "\U0001f6d2 Will be added to this week's shopping list (" + _oos_count + " items)</div>")
    st.html(
        "<div style='font-size:0.85rem;color:#5A3A00;background:#FFF8F0;"
        "border:1px solid #FFCC80;border-radius:8px;padding:10px 14px;line-height:1.8;'>"
        + _oos_names
        + "<br><span style='font-size:0.78rem;color:#9AA8A0;'>"
        "These will appear in the Also Needed section of your shopping list.</span>"
        "</div>")

if changed:
    st.divider()
    col_save, col_discard = st.columns([2, 1])
    with col_save:
        if st.button("Save pantry changes", type="primary", use_container_width=True):
            st.session_state["household_pantry"] = current_pantry

            # Track out-of-stock for shopping list
            st.session_state["pantry_out_of_stock"] = out_of_stock_current

            # Pilot: persist to Supabase if authenticated.
            # PROD: dedicated pantry table with quantity + restock_threshold per item.
            if state.is_authenticated():
                hid = st.session_state.get("household_id")
                if hid:
                    try:
                        state._sb_update(
                            "households",
                            {"pantry_items": sorted(current_pantry)},
                            "id", hid,
                        )
                    except Exception:
                        pass
            st.success("Pantry saved. Your shopping list is updated.")
            st.rerun()
    with col_discard:
        if st.button("Discard changes", use_container_width=True):
            st.rerun()

# -- Reset to defaults ---------------------------------------------------------
st.divider()
if not using_defaults:
    col_r1, col_r2 = st.columns([3, 1])
    with col_r1:
        st.html(
            "<div style='font-size:0.82rem;color:#9AA8A0;padding-top:6px;'>"
            "Reset to the WhollyFare default pantry list.</div>")
    with col_r2:
        if st.button("Reset to defaults", use_container_width=True):
            st.session_state["household_pantry"] = None
            st.rerun()


# ==============================================================================
# SECTION 2 -- WEEKLY REGULARS
# Items bought every week regardless of the meal plan: milk, eggs, cheese, etc.
# Separate from pantry staples and from meal-plan savings math.
#
# Sincere Strategy: shown as a separate cost line on the shopping list --
# not folded into WhollyFare Found Money. Honest accounting.
#
# Sale intelligence: if a regular matches this week's flyer, surface a hint
# ("eggs on sale at Kroger -- grab them there") to add value without confusion.
# ==============================================================================
st.divider()
st.html(
    "<div style='font-size:1.1rem;font-weight:700;color:#1E5C32;margin-bottom:4px;'>"
    "Weekly Regulars</div>"
    "<div style='font-size:0.85rem;color:#5A7A62;margin-bottom:16px;'>"
    "Items you buy every week regardless of the meal plan - milk, eggs, cold cuts, etc. "
    "Shown as a separate section on your shopping list so the savings math stays honest.</div>")

# Load current weekly regulars
current_regulars = list(
    st.session_state.get("weekly_regulars") or state.WEEKLY_REGULARS_DEFAULTS
)

# Check for sale hints -- if a regular matches this week's flyer, surface it
flyer_data = st.session_state.get("flyer_data", {})
STORE_DISPLAY = {
    "kroger_palmyra":           "Kroger",
    "food_lion_palmyra":        "Food Lion",
    "aldi_rio":                 "Aldi",
    "harris_teeter_barracks":   "Harris Teeter",
    "Kroger":                   "Kroger",
    "Food Lion":                "Food Lion",
    "Aldi":                     "Aldi",
    "Harris Teeter":            "Harris Teeter",
}

sale_hints = {}  # {regular_name: [{store, item_name, price}]}
for reg in current_regulars:
    reg_lower = reg["name"].lower()
    keywords  = [w for w in reg_lower.split() if len(w) > 3]
    for store_key, candidates in flyer_data.items():
        store_label = STORE_DISPLAY.get(store_key, store_key)
        for c in candidates:
            item_name = (getattr(c, "name", "") if hasattr(c, "name")
                         else c.get("name", "") if isinstance(c, dict) else "")
            if any(kw in item_name.lower() for kw in keywords):
                price = (getattr(c, "sale_price_per_unit", 0.0) if hasattr(c, "sale_price_per_unit")
                         else c.get("sale_price", 0.0) if isinstance(c, dict) else 0.0)
                sale_hints.setdefault(reg["name"], []).append({
                    "store":     store_label,
                    "item_name": item_name,
                    "price":     price,
                })
                break  # one match per store per regular

# Column headers
hdr1, hdr2, hdr3, hdr4 = st.columns([4, 1.5, 1.5, 0.8])
with hdr1:
    st.html("<div style='font-size:0.78rem;color:#9AA8A0;padding:2px 0;'>Item</div>")
with hdr2:
    st.html("<div style='font-size:0.78rem;color:#9AA8A0;padding:2px 0;'>Qty</div>")
with hdr3:
    st.html("<div style='font-size:0.78rem;color:#9AA8A0;padding:2px 0;'>Unit</div>")

# Display / edit weekly regulars
reg_changed = False
updated_regulars = []

for idx, reg in enumerate(current_regulars):
    col_name, col_qty, col_unit, col_rm = st.columns([4, 1.5, 1.5, 0.8])
    with col_name:
        new_name = st.text_input(
            "Item", value=reg["name"],
            key="wr_name_" + str(idx),
            label_visibility="collapsed",
        )
    with col_qty:
        new_qty = st.text_input(
            "Qty", value=reg["qty"],
            key="wr_qty_" + str(idx),
            label_visibility="collapsed",
        )
    with col_unit:
        new_unit = st.text_input(
            "Unit", value=reg["unit"],
            key="wr_unit_" + str(idx),
            label_visibility="collapsed",
        )
    with col_rm:
        remove = st.button("x", key="wr_rm_" + str(idx), help="Remove this item")

    if not remove:
        updated_regulars.append({
            "name":       (new_name.strip() or reg["name"]),
            "qty":        (new_qty.strip()  or reg["qty"]),
            "unit":       (new_unit.strip() or reg["unit"]),
            "store_pref": reg.get("store_pref"),
        })
        if (new_name.strip() != reg["name"] or
                new_qty.strip() != reg["qty"] or
                new_unit.strip() != reg["unit"]):
            reg_changed = True
    else:
        reg_changed = True

    # Sale hint for this item
    hints = sale_hints.get(reg["name"], [])
    if hints:
        hint_parts = []
        for h in hints:
            price_str = ("$" + "{:.2f}".format(h["price"])) if h["price"] else ""
            hint_parts.append(h["store"] + (" " + price_str if price_str else ""))
        _hint_text = " / ".join(hint_parts)
        st.html(
            "<div style='font-size:0.78rem;color:#1E5C32;background:#E3F4E8;"
            "border-radius:4px;padding:3px 8px;margin-top:-6px;margin-bottom:6px;'>"
            "On sale this week: " + _hint_text + "</div>")

# Add a new regular
with st.form("add_regular_form", clear_on_submit=True):
    nr_c1, nr_c2, nr_c3, nr_c4 = st.columns([4, 1.5, 1.5, 1])
    with nr_c1:
        nr_name = st.text_input("Item name", placeholder="e.g. Orange juice")
    with nr_c2:
        nr_qty = st.text_input("Qty", value="1")
    with nr_c3:
        nr_unit = st.text_input("Unit", value="each")
    with nr_c4:
        st.html("<div style='padding-top:28px;'></div>")
        nr_add = st.form_submit_button("Add", use_container_width=True)

    if nr_add and nr_name.strip():
        updated_regulars.append({
            "name":       nr_name.strip(),
            "qty":        nr_qty.strip() or "1",
            "unit":       nr_unit.strip() or "each",
            "store_pref": None,
        })
        reg_changed = True

# Persist changes immediately (no explicit save button needed -- list edits are low-stakes)
if reg_changed:
    st.session_state["weekly_regulars"] = updated_regulars
    st.rerun()


# -- How this works ------------------------------------------------------------
with st.expander("How does the pantry work?", expanded=False):
    st.html(
        "<div style='font-size:0.88rem;color:#3A3A3A;line-height:1.6;'>"
        "<strong>Pantry staples:</strong><br>"
        "- Are excluded from your shopping list's 'buy this week' section<br>"
        "- Cost $0 in per-serving meal estimates<br>"
        "- Appear in the collapsed 'Pantry check' section on your shopping list "
        "as a reminder to verify you have them before you shop<br><br>"
        "<strong>Weekly Regulars:</strong><br>"
        "- Shown as a separate section on your shopping list<br>"
        "- Cost is tracked separately (not mixed into WhollyFare Found Money)<br>"
        "- When a regular matches a store's sale this week, a hint appears above<br><br>"
        "<strong>Keep it accurate</strong> — the more honest your pantry is, the more precise your shopping list becomes.</div>"
    )
