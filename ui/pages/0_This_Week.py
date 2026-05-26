"""0_This_Week.py — This Week Dashboard

The weekly entry point for signed-in users. Shows at a glance:
  • Flyer freshness — which stores have been loaded for this week
  • Plan status — pending / approved / ready to shop
  • Quick-jump buttons to every step in the weekly workflow
  • Found Money running total

Pilot vs. Production
---------------------
Pilot:  Reads session_state + Supabase platform_flyer_weeks for freshness badges.
PROD:   Push notification badge when Tim uploads new circulars Wednesday morning.
        Household-level plan persistence so the dashboard reflects real approvals.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
from datetime import date, timedelta

import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="This Week — WhollyFare",
    page_icon="📅",
    layout="centered",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

# ── Auth gate ──────────────────────────────────────────────────────────────────
if not state.is_authenticated():
    style.page_header("This Week", "Your weekly WhollyFare dashboard")
    st.info("Sign in to see your weekly plan and savings.", icon="👋")
    if st.button("Sign in / Create account"):
        st.switch_page("pages/9_Account.py")
    st.stop()

style.page_header(
    "This Week",
    "Your weekly WhollyFare dashboard — one place to see what's on sale, plan dinners, and track savings.",
)

# ── Week label ────────────────────────────────────────────────────────────────
today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end   = week_start + timedelta(days=6)
week_label = f"{week_start.strftime('%b %-d')} – {week_end.strftime('%b %-d, %Y')}"
active_week = st.session_state.get("active_week", week_start.isoformat())

st.html(
    f"<div style='font-size:0.9rem;color:#555;margin-bottom:18px;'>"
    f"📅 <strong>Week of {week_label}</strong></div>"
)

# ── Helper: flyer freshness from DB ───────────────────────────────────────────
def _get_loaded_chains() -> dict[str, int]:
    """Return {chain_name: item_count} for chains loaded in platform this week."""
    try:
        from ui.state import _sb_select  # noqa: PLC0415
        rows = _sb_select(
            "platform_flyer_weeks",
            select="chain_name,item_count",
            filters={"week_start_date": active_week},
        )
        return {r["chain_name"]: r.get("item_count", 0) for r in (rows or [])}
    except Exception:
        return {}

# ── Step cards ────────────────────────────────────────────────────────────────
hh_done      = bool(st.session_state.get("household_id"))
grocers      = st.session_state.get("grocers", [])
grocers_done = len(grocers) > 0
plan         = st.session_state.get("plan")
plan_meals   = plan.get("meals", []) if plan else []
plan_locked  = bool(plan and plan.get("approved"))
skipped      = set(plan.get("_skipped_indices", [])) if plan else set()
active_meals = [m for i, m in enumerate(plan_meals) if i not in skipped] if plan else []
net_saved    = state.net_found_money()

# Flyer freshness
session_flyer = st.session_state.get("flyer_data", {})
session_chains = [k for k, v in session_flyer.items() if v]
db_chains = _get_loaded_chains()

# ── Status banner ─────────────────────────────────────────────────────────────
if not hh_done:
    status_color, status_icon, status_msg = "#FFF3CD", "👋", "Start by telling us about your household."
elif not grocers_done:
    status_color, status_icon, status_msg = "#FFF3CD", "🏪", "Add your local stores to unlock this week's prices."
elif not plan:
    status_color, status_icon, status_msg = "#E3F4E8", "🍽️", "Prices are loaded — generate your meal plan when you're ready."
elif plan_locked:
    status_color, status_icon, status_msg = "#E3F4E8", "✅", "Plan approved! Your shopping list is ready."
else:
    status_color, status_icon, status_msg = "#E8F0FE", "📝", "Plan generated — review and approve your meals in the Buy-Off."

st.html(
    f"<div style='background:{status_color};border-radius:10px;padding:12px 18px;"
    f"margin-bottom:24px;font-size:0.95rem;'>"
    f"{status_icon} {status_msg}</div>"
)

# ── Savings strip ─────────────────────────────────────────────────────────────
ledger       = st.session_state.get("ledger_history", [])
total_net    = sum(e.get("net_found_money", e.get("amount", 0)) for e in ledger)
weeks_tracked = len(ledger)

loaded_count = len(db_chains) + len([c for c in session_chains if c not in
                                      [k.lower().replace(" ", "_") for k in db_chains]])

_strip_parts = [
    f"<span style='margin-right:20px;'><strong style='font-size:1.1rem;color:#1B5E20;'>"
    f"${total_net:.2f}</strong> <span style='font-size:0.78rem;color:#666;'>found money</span></span>"
]
if net_saved and net_saved > 0:
    _strip_parts.append(
        f"<span style='margin-right:20px;'><strong style='font-size:1.1rem;color:#1B5E20;'>"
        f"${net_saved:.2f}</strong> <span style='font-size:0.78rem;color:#666;'>this week</span></span>"
    )
if weeks_tracked:
    _strip_parts.append(
        f"<span style='font-size:0.78rem;color:#888;'>{weeks_tracked} week"
        f"{'s' if weeks_tracked != 1 else ''} tracked</span>"
    )

st.html(
    "<div style='background:#F0FAF2;border-radius:10px;padding:12px 18px;"
    "margin-bottom:20px;display:flex;align-items:center;flex-wrap:wrap;'>"
    + "".join(_strip_parts) + "</div>"
)

# ── Step cards — single column, mobile-first ───────────────────────────────────
def _step_card(icon, title, subtitle, btn_label, btn_page, done=False, warn=False, disabled=False):
    border = "#5DAA6A" if done else ("#F5A623" if warn else "#D0D0D0")
    bg     = "#F6FFF8" if done else ("#FFFBF2" if warn else "#FAFAFA")
    check  = "✅ " if done else ("⚠️ " if warn else "")
    st.html(
        f"<div style='border:2px solid {border};border-radius:10px;"
        f"background:{bg};padding:14px 16px;margin-bottom:4px;'>"
        f"<span style='font-size:1.3rem;'>{icon}</span>"
        f"<strong style='font-size:0.95rem;margin-left:8px;'>{check}{title}</strong>"
        f"<div style='font-size:0.8rem;color:#666;margin-top:4px;margin-left:2px;'>{subtitle}</div>"
        f"</div>"
    )
    if not disabled:
        if st.button(btn_label, key=f"step_{title}", use_container_width=True):
            st.switch_page(btn_page)
    st.html("<div style='margin-bottom:10px;'></div>")

# Setup steps
_step_card("👨‍👩‍👧", "Household", "Members & dietary needs",
           "Edit →" if hh_done else "Set up now →",
           "pages/1_Household.py", done=hh_done)

_step_card("🏪", "My Stores", "Where you shop this week",
           "Manage stores →" if grocers_done else "Add stores →",
           "pages/2_Grocer_Hub.py",
           done=grocers_done, warn=(hh_done and not grocers_done))

flyer_subtitle = (f"{loaded_count} store(s) loaded for this week"
                  if loaded_count else "No prices loaded yet — Tim uploads Wednesdays")
_step_card("📋", "This Week's Prices", flyer_subtitle,
           "View Grocer Hub →", "pages/2_Grocer_Hub.py",
           done=(loaded_count > 0), warn=(grocers_done and loaded_count == 0))

st.html("<hr style='margin:8px 0 16px;border-color:#E8EEE9;'>")

# Weekly flow steps
meal_subtitle = (f"{len(active_meals)} dinners planned" if plan_meals else "Not generated yet")
_step_card("🍽️", "This Week's Plan", meal_subtitle,
           "Generate plan →" if not plan else "View plan →",
           "pages/3_Plan.py",
           done=bool(plan_meals), warn=(loaded_count > 0 and not plan))

buyoff_subtitle = ("Locked in ✓" if plan_locked
                   else f"{len(active_meals)} meals to review" if plan_meals
                   else "Approve your plan here")
_step_card("✅", "Review & Approve", buyoff_subtitle,
           "Review meals →", "pages/4_Sunday_BuyOff.py",
           done=plan_locked, warn=(bool(plan_meals) and not plan_locked))

list_subtitle = "Ready — open this in the store" if plan_locked else "Approve your plan first"
_step_card("🛒", "Shopping List", list_subtitle,
           "Open list →", "pages/5_Shopping_List.py",
           done=plan_locked, disabled=(not plan_locked))

_step_card("💰", "Savings Ledger", f"${total_net:.2f} found so far",
           "View ledger →", "pages/6_Ledger.py",
           done=(total_net > 0))

# ── Tonight's Dinner card ─────────────────────────────────────────────────────
# Shown only when a plan exists. Highlights tonight's meal (by weekday) so
# returning users get an immediate answer to "what are we making tonight?"
# Routes to the Recipe Cards view in 12_Recipes.py.
if plan_meals:
    import datetime as _tn_dt
    _tn_today  = _tn_dt.datetime.today().strftime("%A")
    _tn_meal   = next((m for m in plan_meals if m.get("day", "") == _tn_today), None)
    # Fall back to first meal if today isn't in the plan (weekend, etc.)
    _tn_meal   = _tn_meal or (plan_meals[0] if plan_meals else None)
    if _tn_meal:
        _tn_name    = _tn_meal.get("name", "Dinner")
        _tn_cuisine = _tn_meal.get("cuisine", "american").lower()
        _tn_day     = _tn_meal.get("day", "")
        _tn_cost    = _tn_meal.get("total_cost", 0.0)
        _tn_is_tod  = (_tn_day == _tn_today)
        _tn_label   = "Tonight" if _tn_is_tod else _tn_day
        _CUISINE_GRAD = {
            "mexican":       ("🌮", "linear-gradient(135deg,#BF4F00,#F28B30)"),
            "italian":       ("🍝", "linear-gradient(135deg,#A0001A,#E53935)"),
            "asian":         ("🍜", "linear-gradient(135deg,#1E5C32,#5DAA6A)"),
            "american":      ("🍗", "linear-gradient(135deg,#5D3000,#A0522D)"),
            "mediterranean": ("🫒", "linear-gradient(135deg,#0D47A1,#1976D2)"),
        }
        _tn_emoji, _tn_grad = _CUISINE_GRAD.get(_tn_cuisine,
                              ("🍽️", "linear-gradient(135deg,#1E5C32,#3A8C4E)"))
        st.html("<hr style='margin:28px 0 20px;border-color:#E0E0E0;'>")
        st.html(f"""
        <div style='border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 20px rgba(30,92,50,0.10);margin-bottom:12px;'>
          <div style='background:{_tn_grad};height:100px;
                      display:flex;align-items:center;justify-content:center;
                      font-size:3.5rem;position:relative;'>
            {_tn_emoji}
            <div style='position:absolute;top:10px;left:14px;background:rgba(0,0,0,0.25);
                        border-radius:20px;padding:3px 10px;font-size:0.7rem;
                        font-weight:700;color:white;letter-spacing:0.05em;'>
              {_tn_label.upper()}
            </div>
            <div style='position:absolute;bottom:8px;right:12px;font-size:0.75rem;
                        font-weight:700;color:rgba(255,255,255,0.9);'>
              ${_tn_cost:.2f} est.
            </div>
          </div>
          <div style='background:white;padding:14px 18px;'>
            <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                        text-transform:uppercase;color:#5DAA6A;margin-bottom:3px;'>
              {_tn_cuisine.title()} &nbsp;·&nbsp; Tap for full recipe
            </div>
            <div style='font-size:1.1rem;font-weight:800;color:#1A2E1D;'>
              {_tn_name}
            </div>
          </div>
        </div>
        """)
        if st.button("📖 See recipe & cooking steps →", use_container_width=True,
                     key="tonight_recipe_btn"):
            st.session_state["recipe_view"] = "this_week"
            st.switch_page("pages/12_Recipes.py")

# ── This week's store prices snapshot ─────────────────────────────────────────
if db_chains or session_chains:
    st.html("<hr style='margin:28px 0 18px;border-color:#E0E0E0;'>")
    st.html(
        "<div style='font-size:1rem;font-weight:700;color:#1B5E20;margin-bottom:12px;'>"
        "📋 This Week's Circulars</div>"
    )

    badge_cols = st.columns(min(len(db_chains) + len(session_chains), 4))
    col_i = 0

    for chain_name, item_count in db_chains.items():
        with badge_cols[col_i % len(badge_cols)]:
            st.html(
                f"<div style='border:1px solid #5DAA6A;border-radius:8px;"
                f"background:#F6FFF8;padding:10px 14px;text-align:center;'>"
                f"<div style='font-weight:700;font-size:0.88rem;'>{chain_name}</div>"
                f"<div style='font-size:0.75rem;color:#3A8C4E;'>{item_count} items on sale</div>"
                f"<div style='font-size:0.65rem;color:#888;margin-top:2px;'>✅ Platform</div>"
                f"</div>"
            )
        col_i += 1

    # Session-only chains not already in DB snapshot
    db_keys = {k.lower().replace(" ", "_") for k in db_chains}
    for skey in session_chains:
        if skey in db_keys:
            continue
        items = session_flyer.get(skey, [])
        label = skey.replace("_", " ").title()
        with badge_cols[col_i % len(badge_cols)]:
            st.html(
                f"<div style='border:1px solid #F5A623;border-radius:8px;"
                f"background:#FFFBF2;padding:10px 14px;text-align:center;'>"
                f"<div style='font-weight:700;font-size:0.88rem;'>{label}</div>"
                f"<div style='font-size:0.75rem;color:#E67E00;'>{len(items)} items loaded</div>"
                f"<div style='font-size:0.65rem;color:#888;margin-top:2px;'>📱 Session</div>"
                f"</div>"
            )
        col_i += 1
