"""5_Shopping_List.py — Shopping list by store and item."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Shopping List · WhollyFare", page_icon="🛒", layout="wide")
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

STORE_NAMES = {
    "kroger_palmyra":    "Kroger",
    "food_lion_palmyra": "Food Lion",
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

total_items = sum(len(items) for items in store_items.values())
st.markdown(
    f"**Week of {week}** · {total_items} unique items · {len(meals)} dinners · {servings} servings each"
)
st.divider()

# ── Display by store ──────────────────────────────────────────────────────────
for sid, items in store_items.items():
    store_label  = STORE_NAMES.get(sid, sid)
    store_total  = sum(v["cost"] for v in items.values())
    item_count   = len(items)

    st.markdown(
        f"""<div style='background:#1E5C32;color:#FFFFFF;border-radius:8px 8px 0 0;
                        padding:10px 16px;margin-top:16px;'>
          <span style='font-size:1rem;font-weight:700;'>🏪 {store_label}</span>
          <span style='font-size:0.85rem;color:#9FD9A8;margin-left:10px;'>{item_count} items</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # Table header
    st.markdown(
        """<div style='display:grid;grid-template-columns:2fr 80px 120px 80px;
                        background:#D8EDD0;padding:6px 14px;
                        font-size:11px;font-weight:700;color:#1E5C32;'>
          <div>ITEM</div><div style='text-align:center;'>QTY</div>
          <div style='text-align:left;'>USED IN</div>
          <div style='text-align:right;'>COST</div>
        </div>""",
        unsafe_allow_html=True,
    )

    for item_name, data in items.items():
        meals_str = ", ".join(data["meals"])
        row_bg = "#FFFFFF" if list(items.keys()).index(item_name) % 2 == 0 else "#FAFAF7"
        st.markdown(
            f"""<div style='display:grid;grid-template-columns:2fr 80px 120px 80px;
                             background:{row_bg};padding:7px 14px;
                             border-bottom:1px solid #EEF3EE;font-size:13px;color:#1E5C32;'>
              <div>□&nbsp; <strong>{item_name}</strong></div>
              <div style='text-align:center;color:#5A7A62;'>{data['qty']}</div>
              <div style='text-align:left;font-size:11px;color:#5A7A62;'>{meals_str}</div>
              <div style='text-align:right;font-weight:600;'>${data['cost']:.2f}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div style='background:#E3F4E8;border-radius:0 0 8px 8px;padding:8px 16px;
                        text-align:right;font-size:13px;font-weight:700;color:#1E5C32;
                        border-top:2px solid #5DAA6A;'>
          {store_label} subtotal: ${store_total:.2f}
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Summary footer ────────────────────────────────────────────────────────────
sf1, sf2, sf3 = st.columns(3)
with sf1:
    st.metric("Total estimated cost", f"${totals['whollyfare_plan']:.2f}")
with sf2:
    st.metric("Found Money 💚", f"${totals['found_money']:.2f}", delta="saved vs. single store")
with sf3:
    st.metric("vs. HelloFresh", f"${totals['vs_hellofresh']:.2f}", delta="you keep this")

st.divider()

# ── Download button ───────────────────────────────────────────────────────────
lines = [f"WhollyFare Shopping List — Week of {week}", "=" * 50, ""]

for sid, items in store_items.items():
    store_label = STORE_NAMES.get(sid, sid)
    store_total = sum(v["cost"] for v in items.values())
    lines.append(f"{'=' * 30}")
    lines.append(f"  {store_label.upper()}")
    lines.append(f"{'=' * 30}")
    for item_name, data in items.items():
        lines.append(f"  □  {item_name:<35} {data['qty']:<12} ${data['cost']:.2f}")
    lines.append(f"  {'Subtotal':>47} ${store_total:.2f}")
    lines.append("")

lines += [
    "=" * 50,
    f"  Total estimated cost:   ${totals['whollyfare_plan']:.2f}",
    f"  Found Money this week:  ${totals['found_money']:.2f}",
    f"  vs. HelloFresh:         ${totals['vs_hellofresh']:.2f}",
    "",
    "Generated by WhollyFare — Eat well. Spend less.",
]

export_text = "\n".join(lines)

st.download_button(
    label="📥 Download shopping list (.txt)",
    data=export_text,
    file_name=f"whollyfare_shopping_{week}.txt",
    mime="text/plain",
)

st.markdown("<br>", unsafe_allow_html=True)
st.page_link("pages/6_Ledger.py", label="→ View Found Money History")
