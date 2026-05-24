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
    layout="wide",
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

# ── Main layout: 3-column workflow + 1-column savings ─────────────────────────
col_steps, col_savings = st.columns([3, 1], gap="large")

with col_steps:
    # Row 1: setup steps
    c1, c2, c3 = st.columns(3)

    def _step_card(col, icon, title, subtitle, btn_label, btn_page, done=False, warn=False):
        border = "#5DAA6A" if done else ("#F5A623" if warn else "#D0D0D0")
        bg     = "#F6FFF8" if done else ("#FFFBF2" if warn else "#FAFAFA")
        check  = "✅ " if done else ""
        with col:
            st.html(
                f"<div style='border:2px solid {border};border-radius:10px;"
                f"background:{bg};padding:14px 16px;min-height:110px;'>"
                f"<div style='font-size:1.4rem;'>{icon}</div>"
                f"<div style='font-weight:700;font-size:0.95rem;margin:4px 0 2px;'>{check}{title}</div>"
                f"<div style='font-size:0.78rem;color:#666;'>{subtitle}</div>"
                f"</div>"
            )
            if st.button(btn_label, key=f"step_{title}", use_container_width=True):
                st.switch_page(btn_page)

    _step_card(c1, "👨‍👩‍👧", "Household", "Members & dietary needs",
               "Edit →" if hh_done else "Set up →", "pages/1_Household.py", done=hh_done)

    _step_card(c2, "🏪", "Grocer Hub", "Your stores + pantry",
               "Manage →" if grocers_done else "Add stores →", "pages/2_Grocer_Hub.py",
               done=grocers_done, warn=(hh_done and not grocers_done))

    # Flyer freshness card
    loaded_count = len(db_chains) + len([c for c in session_chains if c not in
                                          [k.lower().replace(" ","_") for k in db_chains]])
    flyer_subtitle = (f"{loaded_count} store(s) loaded for this week"
                      if loaded_count else "No circulars loaded yet")
    _step_card(c3, "📋", "Circulars", flyer_subtitle,
               "View prices →", "pages/2_Grocer_Hub.py",
               done=(loaded_count > 0), warn=(grocers_done and loaded_count == 0))

    st.html("<div style='margin-top:18px;'></div>")

    # Row 2: weekly plan steps
    d1, d2, d3 = st.columns(3)

    meal_subtitle = (f"{len(active_meals)} dinners planned" if plan_meals
                     else "Not generated yet")
    _step_card(d1, "🍽️", "This Week's Plan", meal_subtitle,
               "Generate plan →" if not plan else "View plan →", "pages/3_Plan.py",
               done=bool(plan_meals), warn=(loaded_count > 0 and not plan))

    buyoff_subtitle = ("Locked in ✓" if plan_locked
                       else f"{len(active_meals)} meals to review" if plan_meals
                       else "Approve your plan here")
    _step_card(d2, "✅", "Sunday Buy-Off", buyoff_subtitle,
               "Review meals →", "pages/4_Sunday_BuyOff.py",
               done=plan_locked, warn=(bool(plan_meals) and not plan_locked))

    list_subtitle = ("Ready to shop" if plan_locked
                     else "Finalize your plan first")
    _step_card(d3, "🛍️", "Shopping List", list_subtitle,
               "View list →", "pages/5_Shopping_List.py",
               done=plan_locked)

with col_savings:
    # ── Savings summary card ───────────────────────────────────────────────────
    ledger = st.session_state.get("ledger_history", [])
    total_net = sum(e.get("net_found_money", e.get("amount", 0)) for e in ledger)
    weeks_tracked = len(ledger)

    st.html(
        f"<div style='background:#1B5E20;border-radius:12px;padding:20px 18px;"
        f"color:#fff;text-align:center;'>"
        f"<div style='font-size:0.75rem;color:#9FD9A8;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:6px;'>Found Money — All Time</div>"
        f"<div style='font-size:2.4rem;font-weight:800;color:#4CAF50;'>"
        f"${total_net:.2f}</div>"
        f"<div style='font-size:0.75rem;color:#9FD9A8;margin-top:4px;'>"
        f"{weeks_tracked} week{'s' if weeks_tracked != 1 else ''} tracked</div>"
        f"</div>"
    )

    if net_saved and net_saved > 0:
        st.html(
            f"<div style='background:#E3F4E8;border-radius:8px;padding:12px 14px;"
            f"text-align:center;margin-top:12px;'>"
            f"<div style='font-size:0.72rem;color:#2E7D32;'>This week (net of gas)</div>"
            f"<div style='font-size:1.5rem;font-weight:700;color:#1B5E20;'>"
            f"${net_saved:.2f}</div>"
            f"</div>"
        )

    st.html("<div style='margin-top:16px;'></div>")
    if st.button("📒 View full ledger", use_container_width=True):
        st.switch_page("pages/6_Ledger.py")
    if st.button("🧂 Update pantry", use_container_width=True):
        st.switch_page("pages/10_Pantry.py")

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
