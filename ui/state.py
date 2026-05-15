"""
state.py — Centralised session state for WhollyFare
-----------------------------------------------------
All st.session_state keys live here. Call init() once at the top of
every page to guarantee the expected keys exist before anything reads them.

Keys
----
household       : HouseholdProfile | None
grocers         : list[dict]  — each dict mirrors GrocerPreference + extra UI fields
flyer_data      : dict[str, list[IngredientCandidate]]  — store_name → candidates
filter_result   : FilterResult | None   — last ConstraintEngine run
plan            : WeeklyPlan | None
approved_weeks  : list[str]   — ISO date strings of approved week starts
ledger_history  : list[dict]  — {week, total_cost, savings_vs_single, savings_vs_hellofresh}
active_week     : str         — ISO date (YYYY-MM-DD) for the current planning week
"""

import streamlit as st
from datetime import date, timedelta


def _next_sunday() -> str:
    today = date.today()
    days = (6 - today.weekday()) % 7
    d = today if days == 0 else date.fromordinal(today.toordinal() + days)
    return d.isoformat()


def init():
    """Ensure all session state keys exist with sensible defaults."""
    defaults = {
        "household":       None,
        "grocers":         [],
        "flyer_data":      {},   # store_name → list[IngredientCandidate]
        "filter_result":   None,
        "plan":            None,
        "approved_weeks":  [],
        "ledger_history":  [],
        "active_week":     _next_sunday(),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Convenience getters ───────────────────────────────────────────────────────

def is_setup_complete() -> bool:
    """True once household + at least one grocer are configured."""
    return (
        st.session_state.get("household") is not None
        and len(st.session_state.get("grocers", [])) > 0
    )


def stores_loaded_this_week() -> list[str]:
    """Return store names that have flyer data for the active week."""
    return list(st.session_state.get("flyer_data", {}).keys())


def total_items_loaded() -> int:
    return sum(
        len(v) for v in st.session_state.get("flyer_data", {}).values()
    )


def plan_ready() -> bool:
    return st.session_state.get("plan") is not None


def week_approved() -> bool:
    w = st.session_state.get("active_week", "")
    return w in st.session_state.get("approved_weeks", [])


def approve_week():
    w = st.session_state.get("active_week", "")
    approved = st.session_state.get("approved_weeks", [])
    if w and w not in approved:
        approved.append(w)
        st.session_state["approved_weeks"] = approved

    # Record ledger entry
    plan = st.session_state.get("plan")
    if plan:
        history = st.session_state.get("ledger_history", [])
        # plan is now a dict
        totals = plan.get("totals", {})
        weekly_cost = totals.get("whollyfare_plan", 0.0)
        savings_vs_single = totals.get("found_money", 0.0)
        savings_vs_hellofresh = totals.get("vs_hellofresh", 0.0)
        history.append({
            "week":              w,
            "whollyfare_cost":   round(weekly_cost, 2),
            "single_store_cost": round(weekly_cost + savings_vs_single, 2),
            "found_money":       round(savings_vs_single, 2),
            "vs_hellofresh":     round(savings_vs_hellofresh, 2),
            "meals_planned":     len(plan.get("meals", [])),
            "stores_used":       2,
        })
        st.session_state["ledger_history"] = history
