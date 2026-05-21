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
st.html(
    f"""<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
                    padding:12px 20px;margin-bottom:20px;font-size:1rem;color:#1E5C32;
                    font-weight:600;'>
      Week of {week}
      &nbsp;·&nbsp; {len(meals)} dinners planned
      &nbsp;·&nbsp; {servings} servings each
    </div>""")

# ── Cumulative savings banner (shown once there's prior history) ──────────────
# Load ledger from DB if authenticated; falls back to session_state if not.
# POC: session_state is the primary working store; DB is the durable backup.
ledger = state.load_ledger()
if ledger:
    cumulative = sum(e.get("found_money", 0) for e in ledger)
    num_weeks  = len(ledger)
    week_word  = "week" if num_weeks == 1 else "weeks"
    st.html(
        f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;
                        padding:10px 18px;margin-bottom:18px;font-size:0.92rem;color:#5A3A00;'>
          You've found <strong style='color:#BF5E00;font-size:1.05rem;'>${cumulative:.2f}</strong>
          across {num_weeks} {week_word} with WhollyFare. This week adds to that.
        </div>""")

# ── Trip cost / net savings calculation ───────────────────────────────────────
# Sincere Strategy: show the real number, not just the flattering one.
# If secondary store trips cost more than they save, say so — right here.
trip_data    = state.net_found_money()
gross_found  = trip_data.get("gross_found_money", totals["found_money"])
total_trip   = trip_data.get("total_trip_cost", 0.0)
net_found    = trip_data.get("net_found_money",  gross_found)
skip_hints   = trip_data.get("skip_suggestions", [])

# ── Found Money hero ──────────────────────────────────────────────────────────
col_left, col_hero, col_right = st.columns([1, 2, 1])
with col_hero:
    if total_trip > 0:
        # Show both gross and net — honesty is the product
        st.html(
            f"""<div class='found-money-box'>
              <div class='found-money-amount'>${net_found:.2f}</div>
              <div class='found-money-label'>Net Found Money this week</div>
              <div style='font-size:12px;color:#BF5E00;margin-top:6px;'>
                ${gross_found:.2f} saved on groceries &minus; ${total_trip:.2f} in gas
              </div>
            </div>""")
    else:
        st.html(
            f"""<div class='found-money-box'>
              <div class='found-money-amount'>${gross_found:.2f}</div>
              <div class='found-money-label'>Found Money this week</div>
              <div style='font-size:12px;color:#BF5E00;margin-top:6px;'>
                vs. buying everything at one store
              </div>
            </div>""")

# ── Sincere Strategy skip hints ───────────────────────────────────────────────
# If any store costs more in gas than it saves on groceries, surface that here.
# This is radical transparency: we'd rather you skip a stop than feel deceived.
if skip_hints:
    for hint in skip_hints:
        st.html(
            f"""<div style='background:#FFF3E0;border:1px solid #FFCC80;border-left:4px solid #F28B30;
                            border-radius:8px;padding:10px 16px;margin-top:8px;font-size:0.88rem;'>
              <strong style='color:#BF5E00;'>You could skip {hint['store']} this week.</strong>
              <span style='color:#5A3A00;'>
                The items there save you <strong>${hint['store_savings']:.2f}</strong>,
                but the round trip costs an estimated <strong>${hint['trip_cost']:.2f}</strong>
                in gas — a net loss of ${hint['difference']:.2f}.
                Everything you need is available at your other stores.
              </span>
            </div>""")

st.html("<br>")

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

st.html("**Your plan vs. the alternatives**")
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
    </table>""")

# ── Meal preview expander ─────────────────────────────────────────────────────
with st.expander("📅 Review this week's dinners", expanded=False):
    for meal in meals:
        cost_per       = meal["meal_cost"] / servings if servings else 0
        allergen_short = meal.get("allergen_notes", "")
        gf_label       = " · GF" if meal.get("gluten_free") else ""
        st.html(
            f"**{meal['day']}** — {meal['name']} &nbsp;&nbsp;"
            f"<span style='color:#5A7A62;font-size:12px;'>"
            f"${cost_per:.2f}/serving{gf_label}"
            f"{' · ' + allergen_short if allergen_short else ''}"
            f"</span>")

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
        st.html(
            f"<div style='font-weight:700;color:#1E5C32;font-size:0.95rem;"
            f"margin:12px 0 4px 0;'>🏪 {store_label} — {len(items)} items</div>")
        for ing in items:
            st.html(
                f"<div style='font-size:12px;color:#5A7A62;padding:2px 0 2px 12px;'>"
                f"□ {ing['item']} &nbsp; <span style='color:#1E5C32;'>${ing['cost']:.2f}</span>"
                f"</div>")
        st.html(
            f"<div style='font-size:12px;font-weight:600;color:#3A8C4E;"
            f"text-align:right;margin-top:4px;'>{store_label} subtotal: ${store_total:.2f}</div>")
        st.html("<hr style='border-color:#D8EDD0;margin:8px 0;'>")

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
        # approve_week_db() stamps session_state AND writes to DB (if authenticated).
        # POC: silently degrades to session-only if DB unavailable.
        state.approve_week_db()
        st.rerun()

    st.caption(
             "Once you're happy with the five dinners above, tap to lock in the week. "
        "Your shopping list will be ready immediately."
    )
