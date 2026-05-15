"""
3_Plan.py — Plan Generator: results view + constraint audit
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Plan · WhollyFare", page_icon="🍽️", layout="wide")
state.init()
style.page_header(
    "This Week's Plan",
    "Every ingredient selected on merit — sale price and nutrition density. Every rejection shown below.",
)

plan   = st.session_state.get("plan")
result = st.session_state.get("filter_result")

if not plan:
    st.warning("No plan generated yet. Load store data and run the engine first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="→ Go to Grocer Hub", icon="🏪")
    st.stop()

household = st.session_state["household"]

# ── Hero ingredients ──────────────────────────────────────────────────────────
st.subheader("Hero ingredients this week")
st.caption(
    "These 5–7 items anchor every meal. One shopping list, "
    "rotated through different cuisines each night."
)

# Collect unique scored ingredients from the plan
from app.core_logic.meal_planner import FLAVOR_PLUGINS
hero_set = {}
for meal in plan.meals:
    for si in meal.ingredients:
        hero_set.setdefault(si.ingredient.name, si)

hero_cols = st.columns(min(len(hero_set), 4))
for i, (name, si) in enumerate(hero_set.items()):
    with hero_cols[i % 4]:
        ing = si.ingredient
        savings = ing.nutrition.get("sale_savings_pct", 0)
        st.markdown(f"""
        <div style='background:#f4f7f9;border-radius:8px;padding:10px 12px;margin-bottom:8px;border-left:3px solid #007A87'>
          <div style='font-weight:700;font-size:13px;color:#1B2A4A'>{ing.name}</div>
          <div style='font-size:12px;color:#555;margin-top:3px'>
            ${ing.sale_price_per_unit:.2f}/{ing.unit}
            {"  · 🏷 " + str(int(savings)) + "% off" if savings else ""}
          </div>
          <div style='font-size:11px;color:#888;margin-top:2px'>{ing.category}</div>
          {"<div style='font-size:10px;color:#2E7D32;margin-top:2px'>🛡 " + ", ".join(ing.allergens[:2]) + " free</div>" if not ing.allergens else ""}
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Weekly meal schedule ──────────────────────────────────────────────────────
st.subheader("Dinner schedule")

for meal in plan.meals:
    plugin = FLAVOR_PLUGINS.get(meal.flavor_plugin, {})
    with st.expander(
        f"**{meal.day}** — {meal.name}  ·  ${meal.cost_per_serving:.2f}/serving",
        expanded=False,
    ):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**Method:** {plugin.get('method_hint', '')}")
            st.markdown(f"**Pantry seasonings:** {', '.join(meal.pantry_seasonings)}")
            st.markdown(
                f"**Serves:** {meal.servings}  ·  "
                f"**Total cost:** ${meal.total_cost:.2f}"
            )
        with c2:
            st.markdown("**Safety ✅**")
            for member in meal.safety_attestation:
                st.caption(f"  ✓ {member}")

st.divider()

# ── Constraint audit ──────────────────────────────────────────────────────────
st.subheader("Constraint audit log")
st.caption(
    "Every ingredient that was filtered out — and exactly why. "
    "This is the Sincere Strategy in practice: no black boxes."
)

if not result or not result.rejected:
    st.success("No ingredients were rejected. All available items passed your household's constraints.", icon="✅")
else:
    # Group by triggering member
    by_member: dict[str, list] = {}
    for r in result.rejected:
        m = r.get("triggered_by_member", "household")
        by_member.setdefault(m, []).append(r)

    for member, rejections in by_member.items():
        with st.expander(f"🔒 {member} — {len(rejections)} item(s) filtered", expanded=False):
            for r in rejections:
                st.markdown(
                    f"<div class='audit-row'>"
                    f"<b>{r['ingredient']}</b> — "
                    f"<span class='audit-reason'>{r['reason']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

st.divider()
st.page_link("pages/4_Sunday_BuyOff.py", label="→ Approve this week's plan", icon="✅")
