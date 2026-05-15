"""
5_Shopping_List.py — Shopping list organised by store then category.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Shopping List · WhollyFare", page_icon="🛒", layout="wide")
state.init()
style.page_header("Shopping List", "Everything you need this week, grouped by store and category.")

plan = st.session_state.get("plan")
if not plan:
    st.warning("No plan yet.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="→ Grocer Hub", icon="🏪")
    st.stop()

# For the POC all items come from one plan — in multi-store, items would be
# tagged with the store that had the best price.
st.markdown(f"**Week of {st.session_state['active_week']}** · {len(plan.shopping_list)} unique items")
st.divider()

# Group by category
by_cat: dict[str, list] = {}
for si in plan.shopping_list:
    by_cat.setdefault(si.ingredient.category.title(), []).append(si)

category_icons = {
    "Protein": "🥩", "Produce": "🥦", "Grain": "🌾",
    "Legume": "🫘", "Dairy": "🧀", "Other": "🫙",
}

total = 0.0
for cat, items in sorted(by_cat.items()):
    icon = category_icons.get(cat, "•")
    st.markdown(f"#### {icon} {cat}")
    for si in items:
        ing = si.ingredient
        item_cost = ing.sale_price_per_unit
        total += item_cost
        savings = ing.nutrition.get("sale_savings_pct", 0)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            allergen_note = f" ⚠️ {', '.join(ing.allergens)}" if ing.allergens else ""
            st.markdown(f"&nbsp;&nbsp;□ &nbsp;**{ing.name}**{allergen_note}")
        with col2:
            st.caption(f"${ing.sale_price_per_unit:.2f}/{ing.unit}")
        with col3:
            if savings:
                st.caption(f"🏷 {int(savings)}% off")
    st.divider()

col1, col2 = st.columns(2)
with col1:
    st.metric("Estimated total", f"${plan.total_cost:.2f}")
with col2:
    st.metric("Saved vs. single store", f"${plan.total_cost * 0.20:.2f}")

# Export
st.download_button(
    label="📥 Export shopping list (text)",
    data="\n".join(
        f"{si.ingredient.name} — ${si.ingredient.sale_price_per_unit:.2f}/{si.ingredient.unit}"
        for si in plan.shopping_list
    ),
    file_name=f"whollyfare_shopping_{st.session_state['active_week']}.txt",
    mime="text/plain",
)
