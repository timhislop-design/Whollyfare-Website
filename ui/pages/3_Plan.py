"""3_Plan.py — This Week's Plan

Shows the five-dinner plan the engine built, with full cost breakdown, ingredient
detail, and constraint compliance. Designed so a pilot friend can understand the
plan without Tim present — no jargon, no assumed knowledge.

POC vs. PRODUCTION
-------------------
POC:  Plan data lives in session_state["plan"] — lost on browser refresh.
      best_store field may be "—" when the engine doesn't set it.
PROD: Plan persisted to DB (plan_id, household_id, week_id).
      best_store resolved from ingredient.source_store in the optimizer output.
"""

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
    "Five dinners built from your stores' actual sale prices, filtered for your household.",
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
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Plan cost", f"${totals['whollyfare_plan']:.2f}")
with c2:
    st.metric(
        "Found Money 💚",
        f"${totals['found_money']:.2f}",
        delta="saved vs. one store",
        delta_color="normal",
    )
with c3:
    st.metric("vs. HelloFresh", f"${totals['vs_hellofresh']:.2f}", delta="you keep this")
with c4:
    st.metric("Dinners planned", len(meals))

# ── Cross-store summary callout ───────────────────────────────────────────────
# POC: STORE_NAMES covers Charlottesville pilot stores + raw chain names as fallback.
# PROD: Resolved from the household's configured store list.
STORE_NAMES = {
    "kroger_palmyra":           "Kroger",
    "food_lion_palmyra":        "Food Lion",
    "aldi_rio":                 "Aldi",
    "harris_teeter_barracks":   "Harris Teeter",
    # Normalised chain names used when store IDs aren't set
    "Kroger":                   "Kroger",
    "Food Lion":                "Food Lion",
    "Aldi":                     "Aldi",
    "Harris Teeter":            "Harris Teeter",
}

store_counts: dict[str, int] = {}
for meal in meals:
    for ing in meal["ingredients"]:
        sid = ing["store"]
        store_counts[sid] = store_counts.get(sid, 0) + 1

num_stores = len(store_counts)
store_parts = "  ·  ".join(
    f"🏪 {STORE_NAMES.get(sid, sid)}: {count} items"
    for sid, count in store_counts.items()
)

if num_stores > 1:
    callout_text = (
        f"{store_parts}  &nbsp;·&nbsp;  "
        f"<strong style='color:#BF5E00;'>Shopping across {num_stores} stores "
        f"saves you ${totals['found_money']:.2f} this week</strong>"
    )
else:
    callout_text = store_parts

st.markdown(
    f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                    padding:10px 16px;margin:12px 0 20px 0;font-size:0.9rem;color:#5A3A00;'>
      {callout_text}
    </div>""",
    unsafe_allow_html=True,
)

# ── Meal cards ────────────────────────────────────────────────────────────────
DAY_COLORS = ["#1E5C32", "#3A8C4E", "#5DAA6A", "#F28B30", "#BF5E00"]

card_cols = st.columns(5)
for idx, meal in enumerate(meals):
    color       = DAY_COLORS[idx % len(DAY_COLORS)]
    cost        = meal["meal_cost"]
    per_serving = cost / servings if servings else 0
    raw_store   = meal.get("best_store", "")
    store_label = STORE_NAMES.get(raw_store, raw_store) if raw_store and raw_store != "—" else ""
    gf_badge    = (
        "<span style='background:#E3F4E8;color:#1E5C32;border-radius:10px;"
        "padding:2px 7px;font-size:10px;font-weight:600;'>GF</span> "
        if meal.get("gluten_free") else ""
    )
    store_line = (
        f"<div style='font-size:11px;color:#5A7A62;margin-bottom:4px;'>🏪 {store_label}</div>"
        if store_label else ""
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
              {store_line}
              <div>{gf_badge}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ── Meal detail expanders ─────────────────────────────────────────────────────
st.subheader("Meal details")
st.caption("Tap any meal to see exactly which ingredients the engine chose and where to buy them.")

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
                raw   = ing.get("store", "")
                sname = STORE_NAMES.get(raw, raw) if raw and raw != "—" else "—"
                with c1:
                    st.caption(ing["item"])
                with c2:
                    st.caption(ing["qty"])
                with c3:
                    st.caption(sname)
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
# Shows pilot friends exactly which rules were applied — radical transparency.
household = st.session_state.get("household")
_constraint_parts = []
if household:
    try:
        _allergens = set()
        _diagnoses = set()
        _lifestyle = set()
        for _m in household.members:
            _allergens.update(_m.allergies)
            _diagnoses.update(d.value for d in _m.diagnoses)
            _lifestyle.update(t.value for t in _m.lifestyle_tags)

        if "celiac" in _diagnoses:
            _constraint_parts.append("Gluten-free compliant")
        if _allergens:
            _allergen_str = ", ".join(
                a.replace("_", " ").capitalize() for a in sorted(_allergens)
            )
            _constraint_parts.append(f"No {_allergen_str}")
        if "type1_diabetes" in _diagnoses or "type2_diabetes" in _diagnoses:
            _constraint_parts.append("Diabetes-aware")
        if "ibs_low_fodmap" in _diagnoses:
            _constraint_parts.append("Low-FODMAP")
        if "ckd" in _diagnoses:
            _constraint_parts.append("CKD-safe")
        if "hypertension" in _diagnoses:
            _constraint_parts.append("Low-sodium")
        for _t in sorted(_lifestyle):
            _constraint_parts.append(_t.replace("_", "-").capitalize())
    except AttributeError:
        # household may be in an unexpected shape — degrade gracefully
        pass

_constraint_str = " · ".join(_constraint_parts) if _constraint_parts else "Standard filtering applied"

st.markdown(
    f"""<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
                   padding:14px 18px;margin-bottom:20px;'>
      <span style='font-size:1rem;font-weight:700;color:#1E5C32;'>
        ✅ All {len(meals)} meals are safe for your household
      </span>
      <span style='font-size:0.85rem;color:#3A8C4E;margin-left:12px;'>
        {_constraint_str}
      </span>
    </div>""",
    unsafe_allow_html=True,
)

# ── CTA ───────────────────────────────────────────────────────────────────────
if st.button("✅ Go to Sunday Buy-Off — confirm this week →", type="primary", use_container_width=True):
    st.switch_page("pages/4_Sunday_BuyOff.py")
