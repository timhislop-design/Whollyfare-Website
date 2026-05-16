"""4_Sunday_BuyOff.py — The Sunday Buy-Off
One screen. One number. One decision.

This is the emotional centrepiece of WhollyFare: the moment a household sees
exactly what they saved this week and locks in their plan. Everything else
builds toward this screen.

POC vs. PRODUCTION
-------------------
POC:  Approval stored in session_state.approved_weeks (lost on refresh).
PROD: Approval persisted to DB (approval_id, household_id, week_id, timestamp).
      Triggers shopping list generation job and optionally sends a push notification.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Sunday Buy-Off · WhollyFare", page_icon="✅", layout="wide")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Sunday Buy-Off",
    "The moment of the week. Here's what you saved — confirm the plan and shop with confidence.",
)

# ── Setup check ───────────────────────────────────────────────────────────────
plan = st.session_state.get("plan")

if not plan:
    st.warning(
        "No plan generated yet — head to Grocer Hub to load this week's prices and run the engine.",
        icon="⚠️",
    )
    st.page_link("pages/2_Grocer_Hub.py", label="→ Go to Grocer Hub", icon="🏪")
    st.stop()

totals   = plan["totals"]
meals    = plan["meals"]
servings = plan["servings"]
week     = plan["week"]

# All four Charlottesville pilot stores + normalised display keys
# POC: Hardcoded to Charlottesville pilot stores.
# PROD: Resolved at runtime from the household's configured store list.
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

approved = state.week_approved()

# ── Week banner ───────────────────────────────────────────────────────────────
st.markdown(
    f"""<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
                    padding:12px 20px;margin-bottom:20px;font-size:1rem;color:#1E5C32;
                    font-weight:600;'>
      Week of {week}
      &nbsp;·&nbsp; {len(meals)} dinners planned
      &nbsp;·&nbsp; {servings} servings each
    </div>""",
    unsafe_allow_html=True,
)

# ── Cumulative savings banner (shown once there's prior history) ──────────────
# POC: Reads from ledger_history in session_state — lost on refresh.
# PROD: Fetched from DB (household_id, sum of found_money over all approved weeks).
ledger = st.session_state.get("ledger_history", [])
if ledger:
    cumulative = sum(e.get("found_money", 0) for e in ledger)
    num_weeks  = len(ledger)
    week_word  = "week" if num_weeks == 1 else "weeks"
    st.markdown(
        f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                        padding:10px 18px;margin-bottom:18px;font-size:0.92rem;color:#5A3A00;'>
          You've found <strong style='color:#BF5E00;font-size:1.05rem;'>${cumulative:.2f}</strong>
          across {num_weeks} {week_word} with WhollyFare. This week adds to that.
        </div>""",
        unsafe_allow_html=True,
    )

# ── Found Money hero ──────────────────────────────────────────────────────────
col_left, col_hero, col_right = st.columns([1, 2, 1])
with col_hero:
    st.markdown(
        f"""<div class='found-money-box'>
          <div class='found-money-amount'>${totals['found_money']:.2f}</div>
          <div class='found-money-label'>Found Money this week</div>
          <div style='font-size:12px;color:#BF5E00;margin-top:6px;'>
            vs. buying everything at one store
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Comparison table ──────────────────────────────────────────────────────────
num_servings_total = len(meals) * servings if meals and servings else 1

wf_cost     = totals["whollyfare_plan"]
single_cost = totals["single_store_best"]
hf_cost     = totals["hellofresh_equiv"]

wf_per     = wf_cost / num_servings_total
single_per = single_cost / num_servings_total
hf_per     = hf_cost / num_servings_total

found_money = totals["found_money"]
vs_hf       = totals["vs_hellofresh"]

st.markdown("**Your plan vs. the alternatives**")
st.markdown(
    f"""<table style='width:100%;border-collapse:collapse;font-size:0.9rem;
                       font-family:Arial,sans-serif;margin-bottom:20px;'>
      <thead>
        <tr style='background:#D8EDD0;color:#1E5C32;'>
          <th style='padding:10px 14px;text-align:left;border-radius:6px 0 0 0;'></th>
          <th style='padding:10px 14px;text-align:right;'>Weekly cost</th>
          <th style='padding:10px 14px;text-align:right;'>Per serving</th>
          <th style='padding:10px 14px;text-align:right;border-radius:0 6px 0 0;'>You save</th>
        </tr>
      </thead>
      <tbody>
        <tr style='background:#FFFFFF;border-bottom:1px solid #D8EDD0;'>
          <td style='padding:10px 14px;font-weight:700;color:#1E5C32;'>
            🟢 WhollyFare plan
          </td>
          <td style='padding:10px 14px;text-align:right;font-weight:700;color:#1E5C32;'>
            ${wf_cost:.2f}
          </td>
          <td style='padding:10px 14px;text-align:right;color:#3A8C4E;'>
            ${wf_per:.2f}
          </td>
          <td style='padding:10px 14px;text-align:right;color:#5A7A62;'>—</td>
        </tr>
        <tr style='background:#FAFAF7;border-bottom:1px solid #D8EDD0;'>
          <td style='padding:10px 14px;color:#5A7A62;'>Best single store</td>
          <td style='padding:10px 14px;text-align:right;color:#5A7A62;'>${single_cost:.2f}</td>
          <td style='padding:10px 14px;text-align:right;color:#5A7A62;'>${single_per:.2f}</td>
          <td style='padding:10px 14px;text-align:right;font-weight:700;color:#F28B30;'>
            ${found_money:.2f}
          </td>
        </tr>
        <tr style='background:#FFFFFF;'>
          <td style='padding:10px 14px;color:#5A7A62;'>HelloFresh equivalent</td>
          <td style='padding:10px 14px;text-align:right;color:#5A7A62;'>${hf_cost:.2f}</td>
          <td style='padding:10px 14px;text-align:right;color:#5A7A62;'>${hf_per:.2f}</td>
          <td style='padding:10px 14px;text-align:right;font-weight:700;color:#F28B30;'>
            ${vs_hf:.2f}
          </td>
        </tr>
      </tbody>
    </table>""",
    unsafe_allow_html=True,
)

# ── Meal preview expander ─────────────────────────────────────────────────────
with st.expander("📅 Review this week's dinners", expanded=False):
    for meal in meals:
        cost_per       = meal["meal_cost"] / servings if servings else 0
        allergen_short = meal.get("allergen_notes", "")
        gf_label       = " · GF" if meal.get("gluten_free") else ""
        st.markdown(
            f"**{meal['day']}** — {meal['name']} &nbsp;&nbsp;"
            f"<span style='color:#5A7A62;font-size:12px;'>"
            f"${cost_per:.2f}/serving{gf_label}"
            f"{' · ' + allergen_short if allergen_short else ''}"
            f"</span>",
            unsafe_allow_html=True,
        )

# ── Shopping split expander ───────────────────────────────────────────────────
with st.expander("🛒 Shopping split by store", expanded=False):
    store_items: dict[str, list[dict]] = {}
    for meal in meals:
        for ing in meal.get("ingredients", []):
            sid = ing["store"]
            store_items.setdefault(sid, []).append(ing)

    for sid, items in store_items.items():
        store_label = STORE_NAMES.get(sid, sid)
        store_total = sum(i["cost"] for i in items)
        st.markdown(
            f"<div style='font-weight:700;color:#1E5C32;font-size:0.95rem;"
            f"margin:12px 0 4px 0;'>🏪 {store_label} — {len(items)} items</div>",
            unsafe_allow_html=True,
        )
        for ing in items:
            st.markdown(
                f"<div style='font-size:12px;color:#5A7A62;padding:2px 0 2px 12px;'>"
                f"□ {ing['item']} &nbsp; <span style='color:#1E5C32;'>${ing['cost']:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='font-size:12px;font-weight:600;color:#3A8C4E;"
            f"text-align:right;margin-top:4px;'>{store_label} subtotal: ${store_total:.2f}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border-color:#D8EDD0;margin:8px 0;'>", unsafe_allow_html=True)

st.divider()

# ── The big button ────────────────────────────────────────────────────────────
if approved:
    # Fire balloons only once per week per session — not on every rerun.
    # POC: keyed to session_state. PROD: a server-side flag on the approval record.
    celebrate_key = f"buy_off_celebrated_{week}"
    if not st.session_state.get(celebrate_key):
        st.balloons()
        st.session_state[celebrate_key] = True

    st.success(
        f"✅ **Week of {week} is locked in.** Your shopping list is ready.",
    )
    link_c1, link_c2 = st.columns(2)
    with link_c1:
        st.page_link("pages/5_Shopping_List.py", label="🛒 Open Shopping List")
    with link_c2:
        st.page_link("pages/6_Ledger.py", label="💰 View Found Money History")
else:
    if st.button(
        "✅  Lock in this week's plan",
        type="primary",
        use_container_width=True,
    ):
        state.approve_week()
        st.rerun()

    st.caption(
        "Locking the plan generates your final shopping list. "
        "You can still review everything above before you decide."
    )
