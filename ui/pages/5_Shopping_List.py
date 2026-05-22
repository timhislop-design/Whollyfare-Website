"""5_Shopping_List.py -- Shopping list by store and item.

Design bar: usable on a phone in a grocery store aisle.
- Centered layout (not wide) so it fits a phone without horizontal scrolling
- Large text and generous tap targets
- Interactive checkboxes so you can tick off items as you shop
- Three sections: sale items by store -> also-needed recipe items -> pantry check
- Download as text file for offline use

Pilot vs. Production
---------------------
Pilot:  Checked-off items stored in session_state -- cleared on browser refresh.
        "Also needed" items costed at category estimates; no store assigned.
PROD:   Checked state persisted to DB per household + week + item.
        Push notification when all items for a store are checked.
        PWA manifest so the list can be added to the home screen.
        "Also needed" items matched to nearest store via Kroger API / Flipp.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Shopping List - WhollyFare", page_icon="🛒", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("Shopping List", "Everything you need this week, organised by store.")

# -- Setup check --
plan = st.session_state.get("plan")

if not plan:
    st.warning("No plan yet. Generate a plan first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="-> Go to Grocer Hub", icon="🏪")
    st.stop()

STORE_NAMES = {
    "kroger_palmyra":           "Kroger",
    "food_lion_palmyra":        "Food Lion",
    "aldi_rio":                 "Aldi",
    "harris_teeter_barracks":   "Harris Teeter",
    "Kroger":                   "Kroger",
    "Food Lion":                "Food Lion",
    "Aldi":                     "Aldi",
    "Harris Teeter":            "Harris Teeter",
}

meals    = plan["meals"]
totals   = plan["totals"]
week     = plan["week"]
servings = plan["servings"]

# -- Resolve household pantry --
pantry = state.pantry_items()

# -- Section 1: sale items by store --
store_items: dict = {}
sale_item_names: set = set()

for meal in meals:
    for ing in meal.get("ingredients", []):
        sid  = ing["store"]
        key  = ing["item"]
        sale_item_names.add(key.lower())
        store_items.setdefault(sid, {})
        if key in store_items[sid]:
            store_items[sid][key]["cost"]  += ing["cost"]
            store_items[sid][key]["meals"].append(meal["day"])
            store_items[sid][key]["shared"] = True
        else:
            store_items[sid][key] = {
                "qty":    ing["qty"],
                "cost":   ing["cost"],
                "meals":  [meal["day"]],
                "shared": False,
            }

# -- Section 2: recipe extras (non-pantry items not in sale list) --
recipe_extras: dict = {}

for meal in meals:
    meal_day = meal.get("day", "")
    for ri in meal.get("recipe_ingredients", []):
        name       = ri.get("name", "")
        name_lower = name.lower().strip()
        is_pantry  = ri.get("pantry_stable", False)
        if is_pantry or name_lower in pantry:
            continue
        if any(name_lower in sn or sn in name_lower for sn in sale_item_names):
            continue
        qty_label = (str(ri.get("qty", "")) + " " + str(ri.get("unit", ""))).strip()
        if name not in recipe_extras:
            recipe_extras[name] = {
                "qty_label": qty_label,
                "meals":     [meal_day],
                "category":  ri.get("category", "other"),
            }
        else:
            if meal_day and meal_day not in recipe_extras[name]["meals"]:
                recipe_extras[name]["meals"].append(meal_day)

# -- Section 3: pantry check --
pantry_check: dict = {}

for meal in meals:
    for ri in meal.get("recipe_ingredients", []):
        if not ri.get("pantry_stable", False):
            continue
        name = ri.get("name", "")
        if name:
            pantry_check.setdefault(name, [])
            day = meal.get("day", "")
            if day and day not in pantry_check[name]:
                pantry_check[name].append(day)

# -- Progress tracking --
sale_count  = sum(len(items) for items in store_items.values())
extra_count = len(recipe_extras)
total_items = sale_count + extra_count

total_checked = sum(
    1 for sid, items in store_items.items()
    for item_name in items
    if st.session_state.get("check_" + sid + "_" + item_name, False)
) + sum(
    1 for item_name in recipe_extras
    if st.session_state.get("check_extra_" + item_name, False)
)

# -- Week header + progress bar --
st.html(
    "<div style='font-size:0.95rem;color:#3A8C4E;margin-bottom:4px;'>"
    "<strong>Week of " + week + "</strong> - " + str(total_items) + " items - "
    + str(len(meals)) + " dinners - " + str(servings) + " servings each"
    "</div>")

if total_items > 0:
    pct = int(total_checked / total_items * 100)
    st.progress(pct / 100, text=str(total_checked) + " of " + str(total_items) + " items checked off")

st.divider()


# -- Helper: render one item row --
def _item_row(check_key, item_name, qty_label, meals_list, cost=None):
    checked   = st.session_state.get(check_key, False)
    meals_str = ", ".join(meals_list)
    col_check, col_info, col_cost = st.columns([0.5, 5, 1.5])

    with col_check:
        st.checkbox(label=item_name, value=checked, key=check_key,
                    label_visibility="collapsed")
    with col_info:
        now        = st.session_state.get(check_key, False)
        name_style = "text-decoration:line-through;color:#9AA8A0;" if now else "color:#1A2E1D;"
        meta_style = "color:#9AA8A0;" if now else "color:#5A7A62;"
        st.html(
            "<div style='padding:6px 0;'>"
            "<div style='font-size:1rem;font-weight:600;" + name_style + "'>" + item_name + "</div>"
            "<div style='font-size:0.78rem;" + meta_style + "'>" + qty_label + " - " + meals_str + "</div>"
            "</div>")
    with col_cost:
        now        = st.session_state.get(check_key, False)
        cost_style = "color:#9AA8A0;text-decoration:line-through;" if now else "color:#1E5C32;font-weight:700;"
        cost_str   = ("$" + "{:.2f}".format(cost)) if cost is not None else "est."
        st.html("<div style='padding:6px 0;text-align:right;font-size:1rem;" + cost_style + "'>"
                + cost_str + "</div>")
    st.html("<hr style='margin:0;border:none;border-top:1px solid #EEF3EE;'>")


# ============================================================
# SECTION 1 -- SALE ITEMS BY STORE
# ============================================================
if store_items:
    for sid, items in store_items.items():
        store_label   = STORE_NAMES.get(sid, sid)
        store_total   = sum(v["cost"] for v in items.values())
        item_count    = len(items)
        store_checked = sum(
            1 for item_name in items
            if st.session_state.get("check_" + sid + "_" + item_name, False)
        )
        all_done   = store_checked == item_count
        done_badge = " v" if all_done else (" - " + str(store_checked) + "/" + str(item_count))
        hdr_bg     = "#3A8C4E" if all_done else "#1E5C32"
        st.html(
            "<div style='background:" + hdr_bg + ";color:#FFFFFF;border-radius:8px 8px 0 0;"
            "padding:12px 18px;margin-top:20px;'>"
            "<span style='font-size:1.05rem;font-weight:700;'>🏪 " + store_label + "</span>"
            "<span style='font-size:0.85rem;color:#9FD9A8;margin-left:10px;'>"
            + str(item_count) + " items" + done_badge + "</span>"
            "<span style='float:right;font-size:0.9rem;font-weight:600;color:#D8EDD0;'>"
            "$" + "{:.2f}".format(store_total) + "</span></div>")

        for item_name, data in items.items():
            _item_row("check_" + sid + "_" + item_name, item_name,
                      data["qty"], data["meals"], data["cost"])

        footer_label = ("All done at " + store_label) if all_done else (store_label + " subtotal")
        st.html(
            "<div style='background:#E3F4E8;border-radius:0 0 8px 8px;padding:10px 18px;"
            "display:flex;justify-content:space-between;align-items:center;"
            "border-top:2px solid #5DAA6A;margin-bottom:4px;'>"
            "<span style='font-size:0.85rem;color:#3A8C4E;'>"
            + ("✅ " if all_done else "") + footer_label + "</span>"
            "<span style='font-size:1rem;font-weight:700;color:#1E5C32;'>"
            "$" + "{:.2f}".format(store_total) + "</span></div>")

    st.divider()


# ============================================================
# SECTION 2 -- ALSO NEEDED THIS WEEK (recipe extras)
# Non-pantry recipe ingredients not covered by the sale list.
# Pilot: no store assigned. Phase 2: matched to nearest store.
# ============================================================
if recipe_extras:
    extra_checked  = sum(
        1 for n in recipe_extras
        if st.session_state.get("check_extra_" + n, False)
    )
    all_extra_done = extra_checked == len(recipe_extras)
    hdr_bg2        = "#5A7A62" if all_extra_done else "#3A8C4E"
    st.html(
        "<div style='background:" + hdr_bg2 + ";color:#FFFFFF;border-radius:8px 8px 0 0;"
        "padding:12px 18px;margin-top:20px;'>"
        "<span style='font-size:1.05rem;font-weight:700;'>🧺 Also needed this week</span>"
        "<span style='font-size:0.85rem;color:#C8E6C9;margin-left:10px;'>"
        "Recipe ingredients - pick up anywhere - "
        + str(extra_checked) + "/" + str(len(recipe_extras)) + "</span></div>")

    for item_name, data in recipe_extras.items():
        _item_row("check_extra_" + item_name, item_name,
                  data["qty_label"], data["meals"], None)

    footer2 = "All grabbed" if all_extra_done else "Grab these alongside your sale items -- not store-specific."
    st.html(
        "<div style='background:#E8F5E9;border-radius:0 0 8px 8px;padding:10px 18px;"
        "border-top:2px solid #5DAA6A;margin-bottom:4px;font-size:0.82rem;color:#3A8C4E;'>"
        + ("✅ " if all_extra_done else "") + footer2 + "</div>")

    st.divider()


# ============================================================
# SECTION 3 -- PANTRY CHECK (collapsed)
# ============================================================
if pantry_check:
    with st.expander("🧂 Pantry check -- " + str(len(pantry_check)) + " items to verify",
                     expanded=False):
        st.html(
            "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:10px;'>"
            "WhollyFare assumed you have these on hand. Quick check before you shop."
            "</div>")
        for item_name, days in pantry_check.items():
            days_str = ", ".join(days)
            st.html(
                "<div style='font-size:0.9rem;padding:4px 0;border-bottom:1px solid #EEF3EE;'>"
                "<span style='color:#1A2E1D;'>✓ " + item_name + "</span>"
                "<span style='color:#9AA8A0;font-size:0.78rem;float:right;'>"
                + days_str + "</span></div>")
    st.divider()


# -- Summary footer --
sf1, sf2 = st.columns(2)
with sf1:
    st.metric("Total estimated cost", "$" + "{:.2f}".format(totals["whollyfare_plan"]))
with sf2:
    st.metric("Found Money 💚", "$" + "{:.2f}".format(totals["found_money"]),
              delta="saved vs. one store")

st.divider()

# -- Utility buttons --
btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    lines = ["WhollyFare Shopping List -- Week of " + week, "=" * 48, ""]
    for sid, items in store_items.items():
        store_label = STORE_NAMES.get(sid, sid)
        store_total = sum(v["cost"] for v in items.values())
        lines += ["=" * 30, "  " + store_label.upper(), "=" * 30]
        for item_name, data in items.items():
            lines.append("  []  " + item_name.ljust(32) + data["qty"].ljust(10)
                         + "  $" + "{:.2f}".format(data["cost"]))
        lines += ["  Subtotal".ljust(46) + "  $" + "{:.2f}".format(store_total), ""]
    if recipe_extras:
        lines += ["-" * 48, "  ALSO NEEDED (pick up anywhere)", "-" * 48]
        for item_name, data in recipe_extras.items():
            lines.append("  []  " + item_name.ljust(32) + data["qty_label"])
        lines.append("")
    if pantry_check:
        lines += ["-" * 48, "  PANTRY CHECK (you should have these)", "-" * 48]
        for item_name in pantry_check:
            lines.append("  v   " + item_name)
        lines.append("")
    lines += [
        "=" * 48,
        "  Total estimated cost:   $" + "{:.2f}".format(totals["whollyfare_plan"]),
        "  Found Money this week:  $" + "{:.2f}".format(totals["found_money"]),
        "  vs. HelloFresh:         $" + "{:.2f}".format(totals["vs_hellofresh"]),
        "",
        "Generated by WhollyFare -- Eat well. Spend less.",
    ]
    st.download_button(
        label="📥 Save list as text file",
        data="\n".join(lines),
        file_name="whollyfare_shopping_" + week + ".txt",
        mime="text/plain",
        use_container_width=True,
    )

with btn_col2:
    if st.button("Clear all check marks", use_container_width=True):
        for sid, items in store_items.items():
            for item_name in items:
                st.session_state["check_" + sid + "_" + item_name] = False
        for item_name in recipe_extras:
            st.session_state["check_extra_" + item_name] = False
        st.rerun()

st.html("<br>")
st.page_link("pages/6_Ledger.py", label="-> View Found Money History")
