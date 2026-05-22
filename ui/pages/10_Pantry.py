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

st.set_page_config(page_title="My Pantry - WhollyFare", page_icon="🧂", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("My Pantry", "Items WhollyFare assumes you have on hand. Keep this accurate to keep your cost estimates real.")

# ── Load current pantry ───────────────────────────────────────────────────────
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

# ── Intro banner ──────────────────────────────────────────────────────────────
st.html(
    "<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;"
    "padding:12px 18px;margin-bottom:20px;font-size:0.9rem;color:#1E5C32;'>"
    "<strong>" + str(len(current_pantry)) + " items</strong> in your pantry &nbsp;·&nbsp; "
    "These are excluded from your shopping list and cost $0 in meal estimates."
    + (" &nbsp;<span style='color:#5A7A62;font-size:0.82rem;'>(using defaults)</span>" if using_defaults else "")
    + "</div>")

# ── Categorised pantry display ────────────────────────────────────────────────
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

# ── Custom items section ──────────────────────────────────────────────────────
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

# ── Add custom item ───────────────────────────────────────────────────────────
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

# ── Save changes ──────────────────────────────────────────────────────────────
if changed:
    st.session_state["household_pantry"] = current_pantry

    # Items that were in PANTRY_DEFAULTS but are now unchecked = "I ran out / don't have this."
    # Track them in session_state so the shopping list can surface them as
    # "also buy this week" items, keeping the cost comparison honest.
    # Phase 2: persisted to DB with a restock_flag so the app knows to watch for
    # a good price on this item in future circulars.
    default_items = state.PANTRY_DEFAULTS
    out_of_stock  = {item for item in default_items if item not in current_pantry}
    st.session_state["pantry_out_of_stock"] = out_of_stock

    # Pilot: persist to Supabase households row if authenticated.
    # Stores as a JSON array in the pantry_items column.
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
                pass   # Degrades gracefully -- session_state is the working store

    st.rerun()

# ── Reset to defaults ─────────────────────────────────────────────────────────
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

# ── How this works ────────────────────────────────────────────────────────────
with st.expander("How does the pantry work?", expanded=False):
    st.html(
        "<div style='font-size:0.88rem;color:#3A3A3A;line-height:1.6;'>"
        "<strong>Items in your pantry:</strong><br>"
        "- Are excluded from your shopping list's 'buy this week' section<br>"
        "- Cost $0 in per-serving meal estimates<br>"
        "- Appear in the collapsed 'Pantry check' section on your shopping list "
        "as a reminder to verify you have them before you shop<br><br>"
        "<strong>Keep it accurate:</strong><br>"
        "If you run out of something (e.g. olive oil), uncheck it so WhollyFare "
        "adds it to your shopping list this week. Check it again once you restock.<br><br>"
        "<strong>Coming in Phase 2:</strong><br>"
        "Restock alerts, 'I used this up' quick-tap, bulk import from a grocery receipt."
        "</div>")
