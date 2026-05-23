"""
04_shopping_list.py — Consolidated, exportable shopping list.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

st.set_page_config(page_title="Shopping List · WhollyFare", page_icon="🛒", layout="wide")
st.title("🛒 Shopping List")

plan = st.session_state.get("plan")
if not plan:
    st.warning("Generate a meal plan first.")
    st.page_link("pages/03_meal_plan.py", label="→ My Meal Plan")
    st.stop()

st.caption(
    f"Plan: **{plan.household_name}** · Grocer: **{plan.grocer or 'unset'}** · "
    f"Week of: **{plan.flyer_week or 'current'}**"
)

shopping = plan.shopping_list

# Group by category
by_cat: dict[str, list] = {}
for s in shopping:
    by_cat.setdefault(s.ingredient.category, []).append(s)

for cat, items in by_cat.items():
    st.subheader(cat.title())
    for s in items:
        ing = s.ingredient
        cols = st.columns([4, 1, 1])
        cols[0].markdown(f"- **{ing.name}** ({ing.unit})")
        cols[1].markdown(f"${ing.sale_price_per_unit:.2f}")
        cols[2].markdown(f"`{s.value_score:.1f}` value")

st.markdown("---")
st.metric("Estimated weekly grocery bill", f"${plan.total_cost:.2f}")

# Export
csv_lines = ["name,category,unit,sale_price_per_unit"]
for s in shopping:
    ing = s.ingredient
    csv_lines.append(f'"{ing.name}",{ing.category},{ing.unit},{ing.sale_price_per_unit:.2f}')
csv_text = "\n".join(csv_lines)

st.download_button(
    "📤 Download shopping list (CSV)",
    csv_text,
    file_name=f"whollyfare_shopping_{plan.flyer_week or 'week'}.csv",
    mime="text/csv",
    mime="text/csv",
)
