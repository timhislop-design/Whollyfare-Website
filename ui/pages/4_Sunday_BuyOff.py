"""
4_Sunday_BuyOff.py — The Sunday Buy-Off
One screen. One button. The killer UX moment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from datetime import datetime, timedelta
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Sunday Buy-Off · WhollyFare", page_icon="✅", layout="wide")
state.init()
style.page_header("Sunday Buy-Off", "Review, approve, and send.")

plan      = st.session_state.get("plan")
household = st.session_state.get("household")
grocers   = st.session_state.get("grocers", [])
approved  = state.week_approved()

if not plan or not household:
    st.warning("No plan ready yet. Generate a plan first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="→ Go to Grocer Hub", icon="🏪")
    st.stop()

primary = next((g for g in grocers if g.get("is_primary")), grocers[0] if grocers else {})

# ── Hero banner ───────────────────────────────────────────────────────────────
with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            f"### I've optimised your week based on the "
            f"**{primary.get('chain', 'your store')}** weekly circular."
        )
        st.markdown(
            f"**{household.household_name}** · {len(plan.meals)} dinners · "
            f"{household.servings_per_meal} servings each · "
            f"Week of **{st.session_state['active_week']}**"
        )
    with c2:
        # Suggest next delivery window
        now    = datetime.now()
        target = now.replace(hour=16, minute=0, second=0, microsecond=0)
        if now.hour >= 14:
            target += timedelta(days=1)
        st.metric(
            "Suggested delivery window",
            f"{target.strftime('%a %I:%M %p')} – {(target + timedelta(hours=1)).strftime('%I:%M %p')}",
        )

st.divider()

# ── Found Money ───────────────────────────────────────────────────────────────
weekly_cost  = plan.total_cost
hellofresh   = len(plan.meals) * household.servings_per_meal * 9.99
single_store = weekly_cost * 1.20
found_money  = single_store - weekly_cost

col_fm, col_vs = st.columns([1, 2])

with col_fm:
    st.markdown(
        f"""<div class='found-money-box'>
          <div class='found-money-amount'>${found_money:,.2f}</div>
          <div class='found-money-label'>Found Money this week</div>
          <div style='font-size:11px;color:#388E3C;margin-top:6px'>vs. single-store shopping</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col_vs:
    st.markdown("**Your plan vs. the alternatives**")
    comp_data = {
        "Option":       ["WhollyFare plan", "Single-store estimate", "HelloFresh equivalent"],
        "Weekly cost":  [f"${weekly_cost:.2f}", f"${single_store:.2f}", f"${hellofresh:.2f}"],
        "Per serving":  [
            f"${weekly_cost / (len(plan.meals) * household.servings_per_meal):.2f}",
            f"${single_store / (len(plan.meals) * household.servings_per_meal):.2f}",
            "$9.99",
        ],
        "You save":     [
            "—",
            f"${found_money:.2f}",
            f"${hellofresh - weekly_cost:.2f}",
        ],
    }
    st.dataframe(comp_data, use_container_width=True, hide_index=True)

st.divider()

# ── Plan at a glance ──────────────────────────────────────────────────────────
with st.expander("📅 Review the week before approving", expanded=False):
    for m in plan.meals:
        st.markdown(
            f"**{m.day}** — {m.name} &nbsp;&nbsp;"
            f"<span style='color:#888;font-size:12px'>"
            f"${m.cost_per_serving:.2f}/serving · "
            f"✅ {', '.join(m.safety_attestation)}"
            f"</span>",
            unsafe_allow_html=True,
        )

with st.expander("🛒 Shopping list preview", expanded=False):
    by_cat: dict[str, list] = {}
    for s in plan.shopping_list:
        by_cat.setdefault(s.ingredient.category.title(), []).append(s.ingredient)
    for cat, items in sorted(by_cat.items()):
        st.markdown(f"**{cat}:** " + ", ".join(i.name for i in items))

st.divider()

# ── The big button ────────────────────────────────────────────────────────────
if approved:
    st.success(
        f"✅ **Approved for the week of {st.session_state['active_week']}.** "
        f"Your shopping list is ready.",
        icon="✅",
    )
    st.balloons()
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/5_Shopping_List.py", label="📤 View / export shopping list", icon="🛒")
    with c2:
        st.page_link("pages/6_Ledger.py", label="📊 View Found Money history", icon="💰")
else:
    if st.button(
        "✅  ONE-CLICK APPROVE — Send shopping list to grocer",
        type="primary",
        use_container_width=True,
    ):
        state.approve_week()
        st.rerun()

    delivery_txt = "delivery" if primary.get("delivery") else "pickup"
    st.caption(
        f"Approving queues your shopping list for {primary.get('chain', 'your store')} {delivery_txt}. "
        "Nothing is shared with anyone else. Ever."
    )
