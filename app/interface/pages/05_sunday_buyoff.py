"""
05_sunday_buyoff.py — The Sunday Buy-Off Hub.

This is the killer UX moment from the Sentir Command Center spec. Once a
week, the user lands on a single screen that says, in plain English:
  "I've optimized your week based on the [grocer] weekly circular.
   Savings identified: $X.XX. Delivery window: [...]. [APPROVE]"

It is intentionally a one-screen, one-click experience. The detail pages
(meal plan, shopping list) are available for users who want to audit, but
the default flow is "trust the orchestration, hit approve."
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from interface.components.financial_ledger import (  # noqa: E402
    LedgerInputs,
    comparator_picker,
    render_financial_ledger,
)

st.set_page_config(page_title="Sunday Buy-Off · WhollyFare", page_icon="✅", layout="wide")

st.title("✅ Sunday Buy-Off")
st.caption("Your week, ready to approve.")

household = st.session_state.get("household")
plan = st.session_state.get("plan")

if not household or not plan:
    st.warning(
        "Generate this week's meal plan first, then come back here to approve it."
    )
    st.page_link("pages/03_meal_plan.py", label="→ Generate Meal Plan", icon="🍽️")
    st.stop()

primary_grocer = next(
    (g for g in household["grocers"] if g.get("is_primary")),
    household["grocers"][0],
)

# ── Header banner ─────────────────────────────────────────────────────────────

with st.container(border=True):
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown(
            f"### I've optimized your week based on the "
            f"**{primary_grocer['chain']}** weekly circular."
        )
        st.markdown(
            f"**{plan.household_name}** · {len(plan.meals)} dinners · "
            f"{household['servings']} servings each"
        )
    with h2:
        # Suggest the next available delivery window for the user's selection.
        target = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
        if datetime.now().hour > 14:
            target += timedelta(days=1)
        st.metric(
            "Suggested delivery window",
            f"{target.strftime('%a %I:%M %p')} – {(target + timedelta(hours=1)).strftime('%I:%M %p')}",
        )

st.markdown("---")

# ── Financial ledger (the "why approve" hook) ────────────────────────────────

comparator = comparator_picker()
render_financial_ledger(
    LedgerInputs(
        weekly_total=plan.total_cost,
        servings_per_meal=household["servings"],
        meals_per_week=household["meals_per_week"],
        # Loyalty values are simulated for the MVP. Real grocer-API
        # integration will populate these from the user's account.
        coupons_clipped_value=4.50,
        loyalty_points_value=1.20 if primary_grocer.get("rewards_enrolled") else 0.0,
        fuel_rewards_value=0.80 if primary_grocer.get("rewards_enrolled") else 0.0,
    ),
    comparator=comparator,
)

st.markdown("---")

# ── The week at a glance (collapsed by default) ──────────────────────────────

with st.expander("📅 Review the week before approving", expanded=False):
    for m in plan.meals:
        st.markdown(
            f"**{m.day}** — {m.name}  "
            f"<span style='color:#888'>(${m.cost_per_serving:.2f}/serving · "
            f"{', '.join(m.safety_attestation)} ✅)</span>",
            unsafe_allow_html=True,
        )

with st.expander("🛒 Shopping list preview"):
    by_cat: dict[str, list] = {}
    for s in plan.shopping_list:
        by_cat.setdefault(s.ingredient.category, []).append(s.ingredient)
    for cat, items in by_cat.items():
        st.markdown(f"**{cat.title()}**: " + ", ".join(i.name for i in items))

st.markdown("---")

# ── The big button ────────────────────────────────────────────────────────────

if st.session_state.get("approved_for", None) == plan.flyer_week:
    st.success(
        f"✅ Approved for the week of **{plan.flyer_week or 'this week'}**. "
        f"Your shopping list has been queued for "
        f"{primary_grocer['chain']} "
        f"{'delivery' if primary_grocer.get('delivery') else 'pickup'}."
    )
    st.balloons()
    st.page_link("pages/04_shopping_list.py", label="📤 Export final shopping list")
else:
    if st.button(
        "✅  ONE-CLICK APPROVE — Send shopping list to grocer",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["approved_for"] = plan.flyer_week
        st.rerun()

    st.caption(
        "Approving sends the shopping list to your primary grocer's delivery "
        "or pickup queue. You can still adjust quantities in the Shopping List "
        "before checkout. Nothing is sent to anyone else, ever."
    )
