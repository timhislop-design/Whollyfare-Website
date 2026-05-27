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

style.maybe_scroll_to_top()
style.page_header(
    "Sunday Buy-Off",
    "The moment of the week. Here's what you saved — confirm the plan and shop with confidence.",
)

# ── Subscription tier gate ────────────────────────────────────────────────────
# Free users who have completed their 7-day trial see this upsell card instead
# of the page content. Trial users and paid users pass through silently.
# POC: tier checked from session state (cached at sign-in). No DB hit.
# PROD: same — tier is immutable within a session; changes take effect on next sign-in.
if not state.has_access("meal_planner"):
    st.html("""
    <div style='max-width:520px;margin:32px auto 0;background:white;border-radius:18px;
                border-top:5px solid #1E5C32;box-shadow:0 4px 32px rgba(30,92,50,0.10);
                padding:36px 36px 28px;text-align:center;'>
      <div style='font-size:2.2rem;margin-bottom:12px;'>🔒</div>
      <div style='font-size:1.3rem;font-weight:800;color:#1A2E1D;margin-bottom:10px;'>
        Meal Planner feature
      </div>
      <div style='font-size:0.93rem;color:#5A7A62;line-height:1.65;margin-bottom:24px;'>
        The Sunday Buy-Off is where you see exactly what you saved this week and approve your plan in one tap. Upgrade to Meal Planner to unlock this weekly ritual.
      </div>
      <div style='background:#F4FAF5;border:1px solid #D0EDD8;border-radius:12px;
                  padding:16px 20px;margin-bottom:24px;text-align:left;'>
        <div style='font-size:0.75rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.09em;color:#3A8C4E;margin-bottom:8px;'>
          Meal Planner — $7/month includes:
        </div>
        <div style='font-size:0.85rem;color:#4A5568;line-height:1.6;'>
          ✓ &nbsp;Weekly 5-dinner plan built from this week's sale prices<br>
          ✓ &nbsp;Sunday Buy-Off — one tap to approve and lock in savings<br>
          ✓ &nbsp;Shopping list organised by store, ready on your phone<br>
          ✓ &nbsp;Found Money tracked every week
        </div>
      </div>
    </div>
    """)
    _u1, _u2, _u3 = st.columns([1, 2, 1])
    with _u2:
        if st.button("See plans & pricing →", type="primary", use_container_width=True,
                     key="upsell_cta"):
            st.switch_page("Home.py")
    st.stop()


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

# ── Recipe library imports for swap feature ──────────────────────────────────
try:
    from app.data.recipe_library import query_recipes, get_recipe_shopping_items, get_recipe
    _RECIPE_LIB_OK = True
except ImportError:
    _RECIPE_LIB_OK = False


def _get_hh_dietary_flags() -> dict:
    """Extract household dietary constraint flags for recipe filtering."""
    flags: dict = {}
    hh = st.session_state.get("household")
    if not hh:
        return flags
    for member in getattr(hh, "members", []):
        for allergy in getattr(member, "allergies", []):
            al = allergy.lower()
            if any(k in al for k in ["gluten", "wheat", "celiac"]):
                flags["gluten_free"] = True
            if any(k in al for k in ["dairy", "milk", "lactose"]):
                flags["dairy_free"] = True
    return flags


def _get_alternates(meal_dict: dict, used_ids: set, n: int = 4) -> list:
    """Return up to n alternate recipes for a meal slot, respecting constraints."""
    if not _RECIPE_LIB_OK:
        return []
    hh_flags     = _get_hh_dietary_flags()
    current_id   = meal_dict.get("recipe_id")
    current_rec  = get_recipe(current_id) if current_id else None
    current_prot = current_rec["primary_protein"] if current_rec else None
    exclude      = list(used_ids | ({current_id} if current_id else set()))

    # Pass 1: same protein, varied cuisines
    alts = query_recipes(
        proteins=[current_prot] if current_prot else None,
        dietary_flags=hh_flags or None,
        exclude_ids=exclude,
        max_results=n * 2,
    )
    # Pass 2: any protein (fills out variety if same-protein pool is thin)
    if len(alts) < n:
        more = query_recipes(
            dietary_flags=hh_flags or None,
            exclude_ids=exclude + [r["id"] for r in alts],
            max_results=n,
        )
        alts += more
    return alts[:n]


def _apply_swap(meal_idx: int, new_recipe: dict) -> None:
    """Swap a meal to a new recipe and reset its approval status to pending."""
    p    = st.session_state["plan"]
    meal = p["meals"][meal_idx]
    meal["name"]               = new_recipe["name"]
    meal["recipe_id"]          = new_recipe["id"]
    meal["recipe_ingredients"] = (
        get_recipe_shopping_items(new_recipe) if _RECIPE_LIB_OK else []
    )
    p["meals"][meal_idx]         = meal
    p["_meal_status"][meal_idx]  = "pending"
    st.session_state["plan"]     = p
    st.session_state[f"_swap_open_{meal_idx}"] = False


# ── Per-meal decision cards ───────────────────────────────────────────────────
# Approve / Swap / Skip each dinner before locking the week.
# POC: decisions in session_state. PROD: persisted to meal_plans table.

# Initialise meal_status list if this is the first visit
if "_meal_status" not in plan:
    plan["_meal_status"] = ["pending"] * len(meals)
    st.session_state["plan"] = plan

meal_status = plan["_meal_status"]

_STATUS_STYLE: dict = {
    "approved": ("#E8F5E9", "#1E5C32", "✓ Approved"),
    "skipped":  ("#FFF0F0", "#BF3030", "✗ Skipping"),
    "pending":  ("#FAFAFA", "#888888",  "· Pending"),
}

st.html("""
<div style='font-size:0.78rem;font-weight:700;color:#5A7A62;letter-spacing:0.08em;
            text-transform:uppercase;margin:4px 0 14px 0;'>
    📅 This week's dinners — approve, swap, or skip each one
</div>""")

for _idx, _meal in enumerate(meals):
    _status              = meal_status[_idx] if _idx < len(meal_status) else "pending"
    _bg, _fc, _st_label  = _STATUS_STYLE.get(_status, _STATUS_STYLE["pending"])
    _cost_per            = _meal["meal_cost"] / servings if servings else 0
    _border_color        = "#5DAA6A" if _status == "approved" else (
                           "#E57373" if _status == "skipped" else "#E0E0E0")

    # Anchor item — top protein sale item driving this meal
    _meal_ings  = _meal.get("ingredients", [])
    _anchor_ing = next((i for i in _meal_ings if i.get("category") == "protein"),
                       _meal_ings[0] if _meal_ings else None)
    _anchor_txt = ""
    if _anchor_ing:
        _short_name = _anchor_ing["item"].split(",")[0][:26]
        _anchor_txt = (
            f"🏷️ {_short_name} · {_anchor_ing.get('store','?')} · "
            f"${_anchor_ing.get('cost', 0):.2f}"
        )

    st.html(f"""
    <div style='border:1px solid {_border_color};border-left:4px solid {_fc};
                border-radius:8px;padding:12px 16px;margin-bottom:4px;background:{_bg};'>
      <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
        <div>
          <span style='font-size:0.68rem;font-weight:700;color:#5A7A62;
                       text-transform:uppercase;letter-spacing:0.07em;'>{_meal["day"]}</span>
          <div style='font-size:1rem;font-weight:700;color:#1A2E1D;margin:2px 0;'>{_meal["name"]}</div>
          <div style='font-size:0.78rem;color:#5A7A62;'>${_cost_per:.2f}/serving
            {(" &nbsp;·&nbsp; " + _anchor_txt) if _anchor_txt else ""}
          </div>
        </div>
        <div style='font-size:0.75rem;font-weight:700;color:{_fc};white-space:nowrap;
                    padding-left:12px;padding-top:2px;'>{_st_label}</div>
      </div>
    </div>""")

    _bc1, _bc2, _bc3, _bc4 = st.columns([1, 1, 1, 3])
    with _bc1:
        if st.button("✅ Approve", key=f"approve_{_idx}",
                     disabled=(_status == "approved"), use_container_width=True):
            plan["_meal_status"][_idx] = "approved"
            st.session_state[f"_swap_open_{_idx}"] = False
            st.session_state["plan"] = plan
            st.rerun()
    with _bc2:
        _swap_label = "✕ Cancel" if st.session_state.get(f"_swap_open_{_idx}") else "🔄 Swap"
        if st.button(_swap_label, key=f"swap_{_idx}", use_container_width=True):
            st.session_state[f"_swap_open_{_idx}"] = not st.session_state.get(
                f"_swap_open_{_idx}", False)
            st.rerun()
    with _bc3:
        if st.button("⏭ Skip", key=f"skip_{_idx}",
                     disabled=(_status == "skipped"), use_container_width=True):
            plan["_meal_status"][_idx] = "skipped"
            st.session_state[f"_swap_open_{_idx}"] = False
            st.session_state["plan"] = plan
            st.rerun()

    # ── Swap panel — alternate recipe picker ──────────────────────────────────
    if st.session_state.get(f"_swap_open_{_idx}"):
        import random as _random
        _used_ids   = {m.get("recipe_id") for m in meals if m.get("recipe_id")} - {_meal.get("recipe_id")}
        _alternates = _get_alternates(_meal, _used_ids, n=4)

        if not _alternates:
            st.info("No alternates found matching your dietary constraints.", icon="ℹ️")
        else:
            st.html("""
            <div style='background:#FFFDF0;border:1px dashed #FFD54F;
                        border-radius:8px;padding:12px 16px;margin:4px 0 8px 0;'>
              <div style='font-size:0.75rem;font-weight:700;color:#5A3A00;
                          text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;'>
                Pick an alternate — or let us choose
              </div>""")
            for _alt in _alternates:
                _cuisine_lbl = _alt.get("cuisine", "").capitalize()
                _protein_lbl = _alt.get("primary_protein", "").capitalize()
                _mins        = _alt.get("active_minutes", 0)
                _adf         = _alt.get("dietary_flags", {})
                _badges      = []
                if _adf.get("gluten_free"): _badges.append("GF")
                if _alt.get("complexity") == "weeknight": _badges.append("Quick")
                _badge_str   = " · ".join(_badges)
                _btn_label   = (
                    f"{_alt['name']}  ·  {_cuisine_lbl} · {_protein_lbl} · {_mins} min"
                    + (f" · {_badge_str}" if _badge_str else "")
                )
                if st.button(_btn_label, key=f"alt_{_idx}_{_alt['id']}",
                             use_container_width=True):
                    _apply_swap(_idx, _alt)
                    st.rerun()
            st.html("</div>")

            if st.button("🎲 Surprise me", key=f"random_{_idx}"):
                _apply_swap(_idx, _random.choice(_alternates))
                st.rerun()

    st.html("<div style='height:2px;'></div>")

st.html("<div style='height:12px;'></div>")

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

# ── Full Grocery Spend ───────────────────────────────────────────────────────────
# Sincere Strategy: show the honest total grocery bill for the week.
# Regulars + staples are tracked here but NEVER folded into Found Money math —
# that comparison stays purely about meal plan savings vs. single-store / HelloFresh.
with st.expander("🧾 Full grocery spend this week", expanded=False):
    st.html("<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:12px;'>"  
            "The Sincere Strategy tracks your total grocery spend honestly. "
            "Regulars and staples are shown here but don't affect your Found Money — "
            "that metric is purely the meal plan savings.</div>")

    # Meal plan cost — calculated, not editable
    st.html(f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
            f"border-bottom:1px solid #E8F5E9;font-size:0.9rem;'>"
            f"<span>🍽️ WhollyFare meal plan</span>"
            f"<strong style='color:#1E5C32;'>${wf_cost:.2f}</strong></div>")

    # Weekly regulars — user estimates their typical spend
    reg_default = float(st.session_state.get("_regulars_cost_override") or 0.0)
    reg_val = st.number_input(
        "🛒 Weekly regulars estimate (milk, eggs, bread, etc.)",
        min_value=0.0, max_value=500.0,
        value=reg_default, step=1.0, format="%.2f",
        help="What you typically spend on regulars regardless of the meal plan. "
             "Edit to match your household. Saved when you lock the week.",
        key="regulars_cost_input",
    )
    st.session_state["_regulars_cost_override"] = reg_val

    # Household staples — pull from session, sum costs where entered
    staples = st.session_state.get("household_staples", [])
    staples_cost = sum(float(s.get("cost") or 0) for s in staples)
    staples_count = len(staples)
    if staples_count:
        cost_str = f"${staples_cost:.2f}" if staples_cost > 0 else f"{staples_count} items (no cost entered)"
        st.html(f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                f"border-bottom:1px solid #E8F5E9;font-size:0.9rem;'>"
                f"<span>🧺 Household staples</span>"
                f"<strong style='color:#1E5C32;'>{cost_str}</strong></div>")

    # Trip/gas cost
    trip_info   = state.net_found_money()
    trip_total  = trip_info.get("total_trip_cost", 0.0)
    if trip_total > 0:
        st.html(f"<div style='display:flex;justify-content:space-between;padding:6px 0;"
                f"border-bottom:1px solid #E8F5E9;font-size:0.9rem;color:#9AA8A0;'>"
                f"<span>⛽ Gas (estimated)</span>"
                f"<span>−${trip_total:.2f}</span></div>")

    # Total
    total_spend = wf_cost + reg_val + staples_cost
    st.html(f"<div style='display:flex;justify-content:space-between;padding:10px 0 4px 0;"
            f"font-size:1rem;font-weight:700;'>"
            f"<span>Total grocery spend this week</span>"
            f"<span style='color:#1E5C32;'>${total_spend:.2f}</span></div>")

    st.html("<div style='font-size:0.75rem;color:#9AA8A0;padding-top:4px;'>"  
            "Found Money ($" + f"{totals['found_money']:.2f}" + " vs. single store · "
            "$" + f"{totals['vs_hellofresh']:.2f}" + " vs. HelloFresh) is calculated from "
            "the meal plan only — not affected by regulars or staples.</div>")

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
        # Finalise any still-pending meals as approved
        _final_plan = st.session_state["plan"]
        _statuses   = _final_plan.get("_meal_status", ["pending"] * len(meals))
        _skipped    = []
        for _i, _s in enumerate(_statuses):
            if _s == "skipped":
                _skipped.append(_i)
            elif _s == "pending":
                _statuses[_i] = "approved"
        _final_plan["_meal_status"]    = _statuses
        _final_plan["_skipped_indices"] = _skipped
        st.session_state["plan"] = _final_plan

        # approve_week_db() stamps session_state AND writes to DB (if authenticated).
        # Pilot: silently degrades to session-only if Supabase is unavailable.
        state.approve_week_db()
        state.log_activity("buyoff_approved", page="Sunday Buy-Off")
        # Log pantry usage for every recipe-stable ingredient in the approved plan.
        # Drives running-low alerts and opportunistic restock recommendations.
        state.log_pantry_usage(_final_plan)
        st.rerun()
