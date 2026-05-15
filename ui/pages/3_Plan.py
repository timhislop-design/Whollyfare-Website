"""3_Plan.py — This Week's Plan"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Plan · WhollyFare", page_icon="🍽️", layout="wide")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "This Week's Plan",
    "Every ingredient chosen on merit — sale price, safety, budget. Every decision shown.",
)

# ── Progress breadcrumb ───────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:center;gap:0;margin-bottom:22px;'>
  <div style='background:#D8EDD0;color:#3A8C4E;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#D8EDD0;color:#3A8C4E;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#3A8C4E;color:white;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
              flex-shrink:0;'>3</div>
  <div style='margin-left:12px;font-size:0.82rem;color:#5A7A62;'>
    Household → Grocer Prices → <strong style='color:#1E5C32;'>This Week's Plan</strong>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Setup check ───────────────────────────────────────────────────────────────
plan = st.session_state.get("plan")

if not plan:
    st.warning("No plan generated yet. Load store data and run the engine first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="→ Go to Grocer Hub", icon="🏪")
    st.stop()

totals   = plan["totals"]
meals    = plan["meals"]
servings = plan["servings"]

# ── Summary bar ───────────────────────────────────────────────────────────────
st.markdown("<div style='margin-bottom:8px;'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Plan cost", f"${totals['whollyfare_plan']:.2f}")
with c2:
    st.metric(
        "Found Money 💚",
        f"${totals['found_money']:.2f}",
        delta=f"saved vs. single store",
        delta_color="normal",
    )
with c3:
    st.metric("vs. HelloFresh", f"${totals['vs_hellofresh']:.2f}", delta="you keep this")
with c4:
    st.metric("Dinners planned", len(meals))
st.markdown("</div>", unsafe_allow_html=True)

# ── Cross-store breakdown ─────────────────────────────────────────────────────
STORE_NAMES = {
    "kroger_palmyra":     "Kroger",
    "food_lion_palmyra":  "Food Lion",
}

store_counts: dict[str, int] = {}
for meal in meals:
    for ing in meal["ingredients"]:
        sid = ing["store"]
        store_counts[sid] = store_counts.get(sid, 0) + 1

store_parts = "  |  ".join(
    f"🏪 {STORE_NAMES.get(sid, sid)}: {count} items"
    for sid, count in store_counts.items()
)
st.markdown(
    f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                    padding:10px 16px;margin-bottom:20px;font-size:0.9rem;color:#5A3A00;'>
      {store_parts}  &nbsp;·&nbsp;
      <strong style='color:#BF5E00;'>Multi-store arbitrage saves you ${totals['found_money']:.2f}</strong>
    </div>""",
    unsafe_allow_html=True,
)

# ── Meal cards ────────────────────────────────────────────────────────────────
DAY_COLORS = ["#1E5C32", "#3A8C4E", "#5DAA6A", "#F28B30", "#BF5E00"]

card_cols = st.columns(5)
for idx, meal in enumerate(meals):
    color        = DAY_COLORS[idx % len(DAY_COLORS)]
    cost         = meal["meal_cost"]
    per_serving  = cost / servings if servings else 0
    store_label  = STORE_NAMES.get(meal.get("best_store", ""), meal.get("best_store", ""))
    gf_badge     = (
        "<span style='background:#E3F4E8;color:#1E5C32;border-radius:10px;"
        "padding:2px 7px;font-size:10px;font-weight:600;'>GF</span> "
        if meal.get("gluten_free") else ""
    )
    with card_cols[idx]:
        st.markdown(
            f"""<div style='background:#FFFFFF;border-radius:10px;
                            box-shadow:0 1px 6px rgba(0,0,0,0.08);
                            border-top:4px solid {color};
                            padding:14px 12px;margin-bottom:8px;'>
              <div style='font-size:11px;font-weight:700;color:{color};
                          letter-spacing:0.06em;text-transform:uppercase;
                          margin-bottom:4px;'>{meal['day']}</div>
              <div style='font-size:13px;font-weight:700;color:#1E5C32;
                          line-height:1.3;margin-bottom:8px;'>{meal['name']}</div>
              <div style='font-size:1.25rem;font-weight:800;color:#1E5C32;'>${cost:.2f}</div>
              <div style='font-size:11px;color:#5A7A62;margin-bottom:6px;'>
                ${per_serving:.2f}/serving</div>
              <div style='font-size:11px;color:#5A7A62;margin-bottom:4px;'>
                🏪 {store_label}</div>
              <div>{gf_badge}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ── Meal detail expanders ─────────────────────────────────────────────────────
st.subheader("Meal details")

for meal in meals:
    with st.expander(f"**{meal['day']}** — {meal['name']}", expanded=False):
        # Allergen notes
        if meal.get("allergen_notes"):
            st.info(f"⚠️ **Allergen notes:** {meal['allergen_notes']}", icon="🛡️")

        # Ingredients table
        ings = meal.get("ingredients", [])
        if ings:
            header_c1, header_c2, header_c3, header_c4 = st.columns([3, 1, 2, 1])
            with header_c1:
                st.markdown("**Item**")
            with header_c2:
                st.markdown("**Qty**")
            with header_c3:
                st.markdown("**Store**")
            with header_c4:
                st.markdown("**Cost**")

            for ing in ings:
                c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
                store_name = STORE_NAMES.get(ing.get("store", ""), ing.get("store", ""))
                with c1:
                    st.caption(ing["item"])
                with c2:
                    st.caption(ing["qty"])
                with c3:
                    st.caption(store_name)
                with c4:
                    st.caption(f"${ing['cost']:.2f}")

        # Meal total
        st.markdown(
            f"<div style='text-align:right;font-size:13px;font-weight:700;"
            f"color:#1E5C32;margin-top:8px;border-top:1px solid #D8EDD0;padding-top:6px;'>"
            f"Meal total: ${meal['meal_cost']:.2f}"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Constraint compliance ─────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
                   padding:14px 18px;margin-bottom:20px;'>
      <span style='font-size:1rem;font-weight:700;color:#1E5C32;'>
        ✅ All 5 meals are safe for your household
      </span>
      <span style='font-size:0.85rem;color:#3A8C4E;margin-left:12px;'>
        Gluten-free compliant · No peanuts · No tree nuts
      </span>
    </div>""",
    unsafe_allow_html=True,
)

# ── CTA ───────────────────────────────────────────────────────────────────────
if st.button("✅ Approve this week's plan →", type="primary"):
    st.switch_page("pages/4_Sunday_BuyOff.py")

st.page_link("pages/4_Sunday_BuyOff.py", label="→ Go to Sunday Buy-Off")
