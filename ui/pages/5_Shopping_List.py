"""5_Shopping_List.py — Shopping list by store and item.

Design bar: usable on a phone in a grocery store aisle.
- Centered layout (not wide) so it fits a phone without horizontal scrolling
- Large text and generous tap targets
- Interactive checkboxes so you can tick off items as you shop
- One section per store, clearly separated
- Download as text file for offline use

POC vs. PRODUCTION
-------------------
POC:  Checked-off items stored in session_state — cleared on browser refresh.
      Layout is Streamlit native; no progressive web app (PWA) shell.
PROD: Checked state persisted to DB per household + week + item.
      Push notification when all items for a store are checked.
      PWA manifest so the list can be added to the home screen.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

# centered keeps content in a readable column width on phones
st.set_page_config(page_title="Shopping List · WhollyFare", page_icon="🛒", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("Shopping List", "Everything you need this week, organised by store.")

# ── Setup check ───────────────────────────────────────────────────────────────
plan = st.session_state.get("plan")

if not plan:
    st.warning("No plan yet. Generate a plan first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="→ Go to Grocer Hub", icon="🏪")
    st.stop()

# POC: STORE_NAMES covers Charlottesville pilot stores + normalised chain names.
# PROD: Resolved from the household's configured store list.
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

# ── Build aggregated shopping list ────────────────────────────────────────────
# {store_id: {item_name: {"qty": str, "cost": float, "meals": [str]}}}
store_items: dict[str, dict[str, dict]] = {}

for meal in meals:
    for ing in meal.get("ingredients", []):
        sid  = ing["store"]
        key  = ing["item"]
        store_items.setdefault(sid, {})
        if key in store_items[sid]:
            store_items[sid][key]["cost"]  += ing["cost"]
            store_items[sid][key]["meals"].append(meal["day"])
        else:
            store_items[sid][key] = {
                "qty":   ing["qty"],
                "cost":  ing["cost"],
                "meals": [meal["day"]],
            }

total_items   = sum(len(items) for items in store_items.values())
total_checked = sum(
    1 for sid, items in store_items.items()
    for item_name in items
    if st.session_state.get(f"check_{sid}_{item_name}", False)
)

# ── Week header + progress ────────────────────────────────────────────────────
st.html(
    f"**Week of {week}** · {total_items} items · {len(meals)} dinners · {servings} servings each"
)

if total_items > 0:
    pct = int(total_checked / total_items * 100)
    st.progress(pct / 100, text=f"{total_checked} of {total_items} items checked off")

st.divider()

# ── Display by store ──────────────────────────────────────────────────────────
# POC: Interactive checkboxes stored in session_state (cleared on refresh).
# PROD: Checked state persisted to DB. "Clear all" resets the DB row.
for sid, items in store_items.items():
    store_label  = STORE_NAMES.get(sid, sid)
    store_total  = sum(v["cost"] for v in items.values())
    item_count   = len(items)
    store_checked = sum(
        1 for item_name in items
        if st.session_state.get(f"check_{sid}_{item_name}", False)
    )

    all_done = store_checked == item_count

    # Store header
    done_badge = " ✓" if all_done else f" · {store_checked}/{item_count}"
    st.markdown(
        f"""<div style='background:{"#3A8C4E" if all_done else "#1E5C32"};
                        color:#FFFFFF;border-radius:8px 8px 0 0;
                        padding:12px 18px;margin-top:20px;'>
          <span style='font-size:1.05rem;font-weight:700;'>🏪 {store_label}</span>
          <span style='font-size:0.85rem;color:#9FD9A8;margin-left:10px;'>
            {item_count} items{done_badge}
          </span>
          <span style='float:right;font-size:0.9rem;font-weight:600;color:#D8EDD0;'>
            ${store_total:.2f}
          </span>
        </div>""")

    # Items — one per row using st.columns for phone-friendly layout
    for item_name, data in items.items():
        check_key = f"check_{sid}_{item_name}"
        checked   = st.session_state.get(check_key, False)
        meals_str = ", ".join(data["meals"])

        col_check, col_info, col_cost = st.columns([0.5, 5, 1.5])

        with col_check:
            new_val = st.checkbox(
                label=item_name,
                value=checked,
                key=check_key,
                label_visibility="collapsed",
            )

        with col_info:
            name_style  = "text-decoration:line-through;color:#9AA8A0;" if new_val else "color:#1A2E1D;"
            meta_style  = "color:#9AA8A0;" if new_val else "color:#5A7A62;"
            st.html(
                f"<div style='padding:6px 0;'>"
                f"<div style='font-size:1rem;font-weight:600;{name_style}'>{item_name}</div>"
                f"<div style='font-size:0.78rem;{meta_style}'>{data['qty']} · {meals_str}</div>"
                f"</div>")

        with col_cost:
            cost_style = "color:#9AA8A0;text-decoration:line-through;" if new_val else "color:#1E5C32;font-weight:700;"
            st.html(
                f"<div style='padding:6px 0;text-align:right;font-size:1rem;{cost_style}'>"
                f"${data['cost']:.2f}"
                f"</div>")

        # Thin divider between items
        st.html(
            "<hr style='margin:0;border:none;border-top:1px solid #EEF3EE;'>")

    # Store subtotal footer
    st.html(
        f"""<div style='background:#E3F4E8;border-radius:0 0 8px 8px;padding:10px 18px;
                        display:flex;justify-content:space-between;align-items:center;
                        border-top:2px solid #5DAA6A;margin-bottom:4px;'>
          <span style='font-size:0.85rem;color:#3A8C4E;'>
            {"✅ All done at " + store_label if all_done else store_label + " subtotal"}
          </span>
          <span style='font-size:1rem;font-weight:700;color:#1E5C32;'>${store_total:.2f}</span>
        </div>""")

st.divider()

# ── Summary footer ────────────────────────────────────────────────────────────
sf1, sf2 = st.columns(2)
with sf1:
    st.metric("Total estimated cost", f"${totals['whollyfare_plan']:.2f}")
with sf2:
    st.metric("Found Money 💚", f"${totals['found_money']:.2f}", delta="saved vs. one store")

st.divider()

# ── Utility buttons ───────────────────────────────────────────────────────────
btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    # Build plain-text export
    lines = [f"WhollyFare Shopping List — Week of {week}", "=" * 48, ""]
    for sid, items in store_items.items():
        store_label = STORE_NAMES.get(sid, sid)
        store_total = sum(v["cost"] for v in items.values())
        lines.append(f"{'=' * 30}")
        lines.append(f"  {store_label.upper()}")
        lines.append(f"{'=' * 30}")
        for item_name, data in items.items():
            lines.append(f"  □  {item_name:<32} {data['qty']:<10} ${data['cost']:.2f}")
        lines.append(f"  {'Subtotal':>44} ${store_total:.2f}")
        lines.append("")
    lines += [
        "=" * 48,
        f"  Total estimated cost:   ${totals['whollyfare_plan']:.2f}",
        f"  Found Money this week:  ${totals['found_money']:.2f}",
        f"  vs. HelloFresh:         ${totals['vs_hellofresh']:.2f}",
        "",
        "Generated by WhollyFare — Eat well. Spend less.",
    ]
    st.download_button(
        label="📥 Save list as text file",
        data="\n".join(lines),
        file_name=f"whollyfare_shopping_{week}.txt",
        mime="text/plain",
        use_container_width=True,
    )

with btn_col2:
    if st.button("↺ Clear all check marks", use_container_width=True):
        for sid, items in store_items.items():
            for item_name in items:
                st.session_state[f"check_{sid}_{item_name}"] = False
        st.rerun()

st.html("<br>")
st.page_link("pages/6_Ledger.py", label="→ View Found Money History")
