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

DB layer keys (added when Supabase is wired)
----
user            : dict | None   — Supabase auth user object (id, email)
household_id    : str | None    — UUID of the household row in DB
"""

import streamlit as st
import logging
import requests as _requests
from datetime import date, timedelta

# ── Secret loading strategy ──────────────────────────────────────────────────
# POC:  .env for local dev, .streamlit/secrets.toml for Streamlit Cloud.
# PROD: vault-based secret management (AWS Secrets Manager / GCP Secret Manager).
#
# We push everything into os.environ so all downstream code (KrogerClient, etc.)
# can use os.environ.get() without knowing whether the value came from .env or
# st.secrets. Order of precedence: shell env > st.secrets > .env file.

# 1. Load .env (local dev — silently no-ops if file or package absent)
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(override=False)
except ImportError:
    pass

# 2. Bridge Streamlit secrets into os.environ (covers both local secrets.toml
#    and Streamlit Cloud secrets — whichever is present).
#    Nested TOML tables are flattened: [kroger] client_id → KROGER_CLIENT_ID
import os as _os
try:
    for _section, _val in st.secrets.items():
        if hasattr(_val, "items"):          # TOML table → flatten with prefix
            for _k, _v in _val.items():
                _env_key = f"{_section}_{_k}".upper()
                if _env_key not in _os.environ:
                    _os.environ[_env_key] = str(_v)
        else:                               # top-level scalar
            if _section.upper() not in _os.environ:
                _os.environ[_section.upper()] = str(_val)
except Exception:
    pass  # st.secrets not available (e.g. running outside Streamlit)

# Debug logging — appears in Streamlit Cloud 'Manage app' logs.
# Remove or set to WARNING in production.
_log = logging.getLogger("whollyfare")
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# DB layer import — captures the real error so it can be shown to the user
_DB_AVAILABLE = False
_DB_IMPORT_ERROR: str | None = None

try:
    from app.db.client import get_client
    _DB_AVAILABLE = True
except ModuleNotFoundError as _e:
    _DB_IMPORT_ERROR = (
        f"The 'supabase' package is not installed in this environment. "
        f"({_e})  Make sure requirements.txt is committed to GitHub and "
        f"Streamlit Cloud has redeployed."
    )
except Exception as _e:
    # Enhanced diagnostics: find where Python is finding 'supabase'
    import sys as _sys
    _sb_location = "not found on sys.path"
    try:
        import supabase as _sb_mod
        _sb_location = str(getattr(_sb_mod, '__file__', None) or getattr(_sb_mod, '__path__', 'no __file__ or __path__'))
    except Exception:
        pass
    _DB_IMPORT_ERROR = (
        f"DB client import failed: {_e} | "
        f"supabase found at: {_sb_location} | "
        f"Python: {_sys.version[:6]} | "
        f"sys.path[0:2]: {_sys.path[:2]}"
    )

# Profile schema import for conversion helpers (optional — pages may use HouseholdProfile directly)
try:
    from app.core_logic.profile_schema import (
        HouseholdProfile, MemberProfile, Diagnosis, LifestyleTag,
    )
    _PROFILE_SCHEMA_AVAILABLE = True
except Exception:
    _PROFILE_SCHEMA_AVAILABLE = False


def db_dict_to_profile(d: dict) -> "HouseholdProfile | None":
    """
    Convert a household DB dict (as stored in session_state["household_db"]) back
    into a HouseholdProfile Pydantic object for the constraint engine and existing pages.

    Returns None if profile_schema is unavailable or conversion fails.

    POC:  birth_year → age is not round-tripped (DB stores birth_year, profile stores age).
          Age is set to None on restore. This is fine for constraint purposes — age is
          only used for serving-size guidance, not for hard constraints.
    PROD: Store age or birth_year consistently in one place.
    """
    if not _PROFILE_SCHEMA_AVAILABLE or not d:
        return None
    try:
        members = []
        for m in d.get("members", []):
            # Diagnoses and lifestyle tags: skip unrecognised values silently
            diagnoses = []
            for val in m.get("diagnoses", []):
                try:
                    diagnoses.append(Diagnosis(val))
                except ValueError:
                    pass

            lifestyle = []
            for val in m.get("lifestyle", []):
                try:
                    lifestyle.append(LifestyleTag(val))
                except ValueError:
                    pass

            members.append(MemberProfile(
                name=m["name"],
                age=m.get("age"),
                allergies=m.get("allergies", []),
                diagnoses=diagnoses,
                lifestyle_tags=lifestyle,
                custom_exclusions=m.get("exclusions", []),
            ))

        return HouseholdProfile(
            household_name=d.get("name", "My Household"),
            members=members,
            weekly_budget_usd=float(d.get("weekly_budget_usd", 120.0)),
            servings_per_meal=int(d.get("servings_per_meal", 4)),
            meals_per_week=int(d.get("meals_per_week", 5)),
        )
    except Exception:
        return None


def _next_sunday() -> str:
    today = date.today()
    days = (6 - today.weekday()) % 7
    d = today if days == 0 else date.fromordinal(today.toordinal() + days)
    return d.isoformat()


# ── Pantry defaults ──────────────────────────────────────────────────────────
# Items virtually every household keeps on hand. Drawn from pantry_stable=True
# ingredients across the recipe library.
#
# Pilot (Tier 1): These are assumed present — cost $0, excluded from shopping
# list "buy this week" section, shown in "check your pantry" instead.
#
# Pilot (Tier 2): A "My Pantry" UI in the Account page lets households
# customise this list and persist it to Supabase. pantry_items() returns the
# customised set when available, these defaults otherwise.
PANTRY_DEFAULTS: frozenset[str] = frozenset({
    # Oils & fats
    "olive oil", "vegetable oil", "sesame oil", "butter", "cooking spray",
    # Acids & sauces
    "soy sauce", "fish sauce", "worcestershire sauce", "hot sauce",
    "apple cider vinegar", "white vinegar", "balsamic vinegar",
    # Aromatics
    "garlic", "onion", "shallot", "ginger",
    # Dry spices & herbs
    "salt", "black pepper", "red pepper flakes", "paprika", "smoked paprika",
    "cumin", "chili powder", "oregano", "thyme", "basil", "bay leaves",
    "coriander", "turmeric", "cinnamon", "cayenne", "italian seasoning",
    "garlic powder", "onion powder",
    # Baking & pantry staples
    "flour", "cornstarch", "sugar", "brown sugar", "honey",
    "chicken broth", "beef broth", "vegetable broth",
    # Condiments
    "dijon mustard", "tomato paste",
    # Citrus (treat as pantry — usually on hand)
    "lemon", "lime",
    # Fridge condiments (commonly on hand — track so shopping list stays accurate)
    "ketchup", "mayonnaise", "yellow mustard", "ranch dressing",
    "bbq sauce", "salsa", "cream cheese", "sour cream",
    "jam", "pickles", "maple syrup", "peanut butter",
})


# ── Weekly Regulars defaults ─────────────────────────────────────────────────
# Items bought every week regardless of the meal plan — not recipe-driven.
# Tier 2 pantry: milk, eggs, cheese, cold cuts, etc.
#
# Pilot: Customizable list shown in "Weekly Regulars" section of the Pantry page.
#        Stored in st.session_state["weekly_regulars"]; defaults used when None.
#        NOT included in WhollyFare Found Money savings math (Sincere Strategy:
#        weekly regulars are a household baseline, not a meal-plan optimisation).
#        Shopping List shows them in a separate "Weekly Regulars" section with
#        a separate cost line: "Meal plan: $X · Weekly regulars: ~$Y · Total: $Z"
#
# Phase 2: Match regulars against grocer price data and surface "grab eggs at
#           Kroger this week — on sale" style hints (store intelligence).
WEEKLY_REGULARS_DEFAULTS: list[dict] = [
    {"name": "Whole milk",       "qty": "1",   "unit": "gallon", "store_pref": None},
    {"name": "Eggs",             "qty": "1",   "unit": "dozen",  "store_pref": None},
    {"name": "Butter",           "qty": "1",   "unit": "lb",     "store_pref": None},
    {"name": "Cheddar cheese",   "qty": "8",   "unit": "oz",     "store_pref": None},
    {"name": "Bread",            "qty": "1",   "unit": "loaf",   "store_pref": None},
    {"name": "Yogurt",           "qty": "32",  "unit": "oz",     "store_pref": None},
    {"name": "Cold cuts",        "qty": "0.5", "unit": "lb",     "store_pref": None},
]


def weekly_regulars_items() -> list[dict]:
    """
    Return the household's weekly regulars list.
    Each item is a dict: {name, qty, unit, store_pref}.

    Falls back to WEEKLY_REGULARS_DEFAULTS when user hasn't customised.
    Pilot: stored in session_state["weekly_regulars"].
    PROD: persisted to Supabase household_pantry / weekly_regulars table.
    """
    custom = st.session_state.get("weekly_regulars")
    if custom is not None:
        return custom
    return WEEKLY_REGULARS_DEFAULTS


def pantry_items() -> frozenset[str]:
    """
    Return the household's pantry as a lowercase frozenset of item names.

    Tier 1: Returns PANTRY_DEFAULTS (items we assume every household has).
    Tier 2: Returns household_pantry from session_state when the user has
            customised their list via the Account page.

    Usage:
        pantry = state.pantry_items()
        if ingredient_name.lower() in pantry:
            cost = 0.0   # assume on hand
    """
    custom = st.session_state.get("household_pantry")
    if custom is not None:
        return frozenset(s.lower() for s in custom)
    return PANTRY_DEFAULTS


def pantry_has(item_name: str) -> bool:
    """True if item_name (case-insensitive) is in the household pantry."""
    return item_name.lower().strip() in pantry_items()


def init():
    """Ensure all session state keys exist with sensible defaults."""
    defaults = {
        "household":       None,
        "grocers":         [],
        "flyer_data":      {},
        "flyer_meta":      {},   # {chain: {count, week, method, fresh}}   # store_name → list[IngredientCandidate]
        "filter_result":   None,
        "plan":            None,
        "approved_weeks":  [],
        "ledger_history":  [],
        "active_week":     _next_sunday(),
        # Location — used to filter stores by regional availability
        # POC: Default to Charlottesville pilot zip. User can update in Account page.
        # PROD: Set from billing address on account creation; resolved against store
        #       locator APIs to confirm which chains are within the radius.
        "home_zip":        "22901",   # Charlottesville VA default
        "store_radius_mi":  15,        # miles — legacy key (kept for compat)
        "travel_radius_mi": 15,        # miles — grocer wizard preference (written to DB)
        # DB layer
        "user":            None,   # Supabase auth user dict
        "household_id":    None,   # UUID string of households row
        "household_db":    None,   # plain dict loaded from DB (complement to HouseholdProfile)
        # Pantry — None means "use PANTRY_DEFAULTS"; a set means user-customised
        "household_pantry": None,
        # Weekly regulars — None means "use WEEKLY_REGULARS_DEFAULTS"; a list means user-customised
        "weekly_regulars":   None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # ── Session persistence ───────────────────────────────────────────────────
    # If user is not authenticated, try to restore from browser localStorage.
    # try_restore_from_browser() is a no-op until streamlit-javascript renders;
    # on the first pass it returns False while the JS component loads, then
    # Streamlit auto-reruns and the second pass gets the real localStorage value.
    # POC: Runs on every page load — cheap (no network call unless token found).
    if not is_authenticated():
        if try_restore_from_browser():
            st.rerun()

    # ── Proactive token refresh ───────────────────────────────────────────────
    # If authenticated but the JWT is within 5 minutes of expiry, silently
    # exchange it for a fresh pair.  If the refresh token is also gone, show
    # the session-expired banner so the user knows to sign in again.
    # POC: Called on every page load — cheap when secs > 300 (early return).
    session_expiry_check()


# ── Convenience getters ───────────────────────────────────────────────────────

def is_setup_complete() -> bool:
    """True once household + at least one grocer are configured."""
    return (
        st.session_state.get("household") is not None
        and len(st.session_state.get("grocers", [])) > 0
    )


def setup_stage() -> str:
    """
    Return the user's current setup stage — used to drive first-login routing.

    Returns one of:
      "no_auth"   — not signed in
      "household" — signed in but no household profile yet
      "stores"    — household done but no stores selected
      "plan"      — stores done but no plan generated this week
      "ready"     — plan exists; user is in the weekly flow

    POC: Reads session_state only. PROD: cross-device by querying Supabase
         for household, grocers, and active meal_plan rows on sign-in.
    """
    if not is_authenticated():
        return "no_auth"
    if st.session_state.get("household") is None:
        return "household"
    if len(st.session_state.get("grocers", [])) == 0:
        return "stores"
    if st.session_state.get("plan") is None:
        return "plan"
    return "ready"


def stores_loaded_this_week() -> list[str]:
    """Return store names that have flyer data for the active week."""
    return list(st.session_state.get("flyer_data", {}).keys())


def total_items_loaded() -> int:
    """Count of ingredient items across all loaded stores.

    Handles two flyer_data shapes:
      - {store_name: list[IngredientCandidate | dict]}  (normal engine path)
      - {week: str, stores: dict}  (old wrapped demo format — should be normalised before this)
    """
    total = 0
    for v in st.session_state.get("flyer_data", {}).values():
        if isinstance(v, list):
            total += len(v)
        # Non-list values (e.g. a leftover week-string) are silently skipped
    return total


def plan_ready() -> bool:
    return st.session_state.get("plan") is not None


# ── Trip cost utilities ───────────────────────────────────────────────────────
# POC: Distance entered manually per store. Cost at $0.22/mile round-trip.
# PROD: Distance calculated automatically from household zip to store address
#       via Google Maps Distance Matrix API. Updated weekly (traffic patterns
#       vary). User can override with "I combine this trip with other errands."
#
# $0.22/mile is a conservative estimate for personal vehicle gas cost only
# (not IRS business mileage rate). We deliberately understate so we are never
# accusing the user of wasting money when they are not.

COST_PER_MILE: float = 0.22  # $ per mile, one-way


def trip_cost_for_store(grocer: dict) -> float:
    """Round-trip gas cost estimate for one visit to this store.

    Returns 0.0 for the primary store (assumed already in the weekly routine)
    and for stores with no distance set.
    """
    if grocer.get("is_primary"):
        return 0.0
    miles = grocer.get("distance_miles")
    if not miles:
        return 0.0
    return round(float(miles) * 2 * COST_PER_MILE, 2)


def plan_trip_costs() -> dict:
    """Return {store_name: trip_cost} for stores that contributed items to the plan.

    Primary store always gets 0.0. Stores with no distance set return 0.0.

    POC: Uses grocers from session_state. Distance must be manually entered.
    PROD: Hydrated from household grocer preferences in the DB.
    """
    grocers = st.session_state.get("grocers", [])
    active  = set(st.session_state.get("flyer_data", {}).keys())
    costs: dict = {}
    for g in grocers:
        name = g.get("chain", "")
        if name in active:
            costs[name] = trip_cost_for_store(g)
    return costs


def net_found_money() -> dict:
    """Calculate gross Found Money, total trip costs, and net savings.

    Returns a dict with:
        gross_found_money   -- price saving vs. single-store shopping
        total_trip_cost     -- sum of gas costs for secondary store visits
        net_found_money     -- gross minus trip costs (what you actually keep)
        trip_costs          -- {store: cost} breakdown
        skip_suggestions    -- stores where savings < trip cost

    Sincere Strategy: we show the real number, not just the flattering one.

    POC: store_savings is estimated proportionally by item count share.
    PROD: Track per-store ingredient costs vs. primary store to get exact savings.
    """
    plan = st.session_state.get("plan")
    if not plan:
        return {}

    gross      = plan.get("totals", {}).get("found_money", 0.0)
    trip_costs = plan_trip_costs()
    total_trip = round(sum(trip_costs.values()), 2)
    net        = round(gross - total_trip, 2)

    # Estimate per-store savings share by item count
    flyer       = st.session_state.get("flyer_data", {})
    total_items = sum(len(v) for v in flyer.values() if isinstance(v, list)) or 1

    skip_suggestions = []
    for store, cost in trip_costs.items():
        if cost <= 0:
            continue
        store_share   = len(flyer.get(store, [])) / total_items
        store_savings = round(gross * store_share, 2)
        if store_savings < cost:
            skip_suggestions.append({
                "store":         store,
                "trip_cost":     cost,
                "store_savings": store_savings,
                "difference":    round(cost - store_savings, 2),
            })

    return {
        "gross_found_money": gross,
        "total_trip_cost":   total_trip,
        "net_found_money":   net,
        "trip_costs":        trip_costs,
        "skip_suggestions":  skip_suggestions,
    }


def week_approved() -> bool:
    w = st.session_state.get("active_week", "")
    return w in st.session_state.get("approved_weeks", [])


def approve_week():
    w = st.session_state.get("active_week", "")
    approved = st.session_state.get("approved_weeks", [])
    if w and w not in approved:
        approved.append(w)
        st.session_state["approved_weeks"] = approved

    # Record ledger entry — include trip cost / net Found Money.
    # Sincere Strategy: the ledger shows what you actually kept, not just
    # the gross price saving. Trip costs are recorded so the running total
    # is honest about cumulative net benefit.
    plan = st.session_state.get("plan")
    if plan:
        history   = st.session_state.get("ledger_history", [])
        totals    = plan.get("totals", {})
        trip_info = net_found_money()

        weekly_cost           = totals.get("whollyfare_plan", 0.0)
        savings_vs_single     = totals.get("found_money", 0.0)
        savings_vs_hellofresh = totals.get("vs_hellofresh", 0.0)
        trip_cost_total       = trip_info.get("total_trip_cost", 0.0)
        net_savings           = trip_info.get("net_found_money", savings_vs_single)

        grocers     = st.session_state.get("grocers", [])
        stores_used = len([g for g in grocers
                           if g.get("chain") in st.session_state.get("flyer_data", {})])

        # Pull supplemental spend tracking — kept separate from Found Money math.
        # regulars_cost: user-estimated weekly regulars (milk, eggs, bread, etc.)
        # staples_cost:  sum of household_staples items that have a cost entered
        # total_spend_est: the honest full grocery bill for the week
        # Sincere Strategy: shown on dashboard + ledger, never in savings vs. HelloFresh.
        regulars_cost = float(st.session_state.get("_regulars_cost_override") or 0.0)
        staples = st.session_state.get("household_staples", [])
        staples_cost  = round(sum(float(s.get("cost") or 0) for s in staples), 2)
        total_spend   = round(weekly_cost + regulars_cost + staples_cost, 2)

        history.append({
            "week":              w,
            "whollyfare_cost":   round(weekly_cost, 2),
            "single_store_cost": round(weekly_cost + savings_vs_single, 2),
            "found_money":       round(savings_vs_single, 2),
            "trip_cost":         round(trip_cost_total, 2),
            "net_found_money":   round(net_savings, 2),
            "vs_hellofresh":     round(savings_vs_hellofresh, 2),
            "meals_planned":     len(plan.get("meals", [])),
            "stores_used":       stores_used or 2,
            # Supplemental spend — honest total, NOT part of Found Money
            "regulars_cost_est": round(regulars_cost, 2),
            "staples_cost_est":  round(staples_cost, 2),
            "total_spend_est":   total_spend,
        })
        st.session_state["ledger_history"] = history


# ── Auth layer ────────────────────────────────────────────────────────────────
# POC:  Email/password auth via Supabase Auth.
#       The JWT returned by sign-in is automatically attached to the supabase
#       client for all subsequent calls, which lets auth.uid() work in RLS.
# PROD: Add OAuth providers (Google, Apple), magic links, session refresh
#       tokens stored server-side, and a proper logout/timeout flow.

def db_status() -> dict:
    """
    Return a dict describing the current DB connection status.
    Used on the Account page to show a human-readable diagnosis when things fail.

    Returns:
        {
          "package_ok": bool,    # supabase package importable
          "secrets_ok": bool,    # secrets.toml / Streamlit Cloud secrets present
          "connect_ok": bool,    # actually reached Supabase
          "error": str | None,   # first error found, or None
        }
    """
    result = {"package_ok": _DB_AVAILABLE, "secrets_ok": False,
               "connect_ok": False, "error": _DB_IMPORT_ERROR}

    if not _DB_AVAILABLE:
        return result

    # Check secrets
    try:
        import streamlit as _st
        _ = _st.secrets["supabase"]["url"]
        _ = _st.secrets["supabase"]["anon_key"]
        result["secrets_ok"] = True
    except Exception as e:
        result["error"] = (
            f"Supabase secrets not found. On Streamlit Cloud, go to your app's "
            f"Settings → Secrets and add:\n\n"
            f"[supabase]\n"
            f"url = \"https://liviclgyapbeoefxbunh.supabase.co\"\n"
            f"anon_key = \"sb_publishable_suP4Ty6mULuNTKyilIfEHw_QsBVjwCf\"\n\n"
            f"(Raw error: {e})"
        )
        return result

    # Try connecting
    try:
        from app.db.client import test_connection
        result["connect_ok"] = test_connection()
        if not result["connect_ok"]:
            result["error"] = "Supabase is reachable but the test query failed. Check the feature_flags table exists."
    except Exception as e:
        result["error"] = f"Connection failed: {e}"

    return result


def sign_up(email: str, password: str) -> tuple[bool, str]:
    """
    Create a new Supabase auth account.

    Returns (success: bool, message: str).
    On success, also signs the user in and populates st.session_state["user"].
    """
    if not _DB_AVAILABLE:
        return False, _DB_IMPORT_ERROR or "Database client not available."
    try:
        db = get_client()
        resp = db.auth.sign_up({"email": email, "password": password})
        if resp.user:
            st.session_state["user"] = {"id": resp.user.id, "email": resp.user.email}
            # POC: email confirmation is disabled in Supabase settings so the user
            # is active immediately. PROD: enforce email confirmation before granting access.
            log_activity("sign_up")
            return True, "Account created."
        return False, "Sign-up failed — no user returned."
    except Exception as e:
        return False, str(e)


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """
    Sign in with email + password via direct Supabase Auth REST call.

    Bypasses supabase-py's GoTrue client entirely — the GoTrue internal session
    storage is not reliably propagated across Streamlit reruns or st.switch_page()
    calls. We store the access token ourselves in session_state and use it
    explicitly in every authenticated request via _sb_headers().

    POC:  Token stored in session_state only — lost on browser refresh.
          User must sign in again on each new browser session.
    PROD: Store refresh_token in a secure HttpOnly cookie and silently refresh
          before the 1-hour access token expiry.
    """
    if not _DB_AVAILABLE:
        return False, _DB_IMPORT_ERROR or "Database client not available."
    try:
        url  = st.secrets["supabase"]["url"]
        anon = st.secrets["supabase"]["anon_key"]

        # Direct POST to Supabase Auth REST — same as supabase-js internally uses.
        # Returns access_token, refresh_token, and user object without any
        # intermediate GoTrue Python session-management layer.
        resp = _requests.post(
            f"{url}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers={
                "apikey":        anon,
                "Content-Type":  "application/json",
            },
            timeout=10,
        )

        if resp.status_code == 400:
            _log.warning("sign_in: bad credentials for %s", email)
            return False, "Invalid email or password."
        if not resp.ok:
            _log.error("sign_in: auth endpoint error %s: %s", resp.status_code, resp.text)
            return False, f"Sign-in failed ({resp.status_code})."

        data = resp.json()
        access_token  = data.get("access_token")
        refresh_token = data.get("refresh_token", "")
        user_obj      = data.get("user", {})
        uid           = user_obj.get("id")
        user_email    = user_obj.get("email")

        if not access_token or not uid:
            _log.error("sign_in: response missing token or uid: %s", data)
            return False, "Sign-in response incomplete — please try again."

        # Store everything we need for subsequent authenticated requests.
        st.session_state["user"]               = {"id": uid, "email": user_email}
        st.session_state["_sb_access_token"]   = access_token
        st.session_state["_sb_refresh_token"]  = refresh_token
        _log.info("sign_in: success uid=%s token_stored=True", uid)

        # Attempt to load the household that belongs to this user
        _load_household_from_db()
        # Restore grocer selections so the Grocer Hub wizard is pre-filled
        # without the user having to re-enter their stores on every sign-in.
        _load_grocers_from_db()
        # Restore this week's circular data so user doesn't have to re-pull.
        _load_flyer_items_from_db()
        # Cache admin + test flags from profiles so is_admin() is free.
        _load_admin_flag()
        # Persist refresh token to browser localStorage so the session survives
        # page navigation, browser refresh, and Streamlit Cloud worker restarts.
        _save_tokens_to_browser()
        log_activity("sign_in")
        return True, "Signed in."

    except Exception as e:
        _log.error("sign_in: exception for %s: %s", email, e)
        return False, str(e)


def sign_out():
    """Sign out and clear all session state."""
    if _DB_AVAILABLE:
        try:
            get_client().auth.sign_out()
        except Exception:
            pass
    # Remove persisted tokens from browser localStorage so auto-restore
    # doesn't silently log the user back in on the next page load.
    _clear_tokens_from_browser()
    # Clear everything — init() will re-populate defaults on next page load
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def _jwt_is_expired() -> bool:
    """Return True if the stored access token is expired or missing.

    Checks the JWT 'exp' claim with a 60-second safety buffer so we refresh
    slightly before the actual expiry rather than right at the edge.

    POC:  Called on key pages to decide whether to proactively refresh.
    PROD: Run in a background thread and refresh automatically before expiry.
    """
    import time as _time
    import base64 as _b64
    import json as _json_mod

    token = st.session_state.get("_sb_access_token")
    if not token:
        return True
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return True
        # Pad to a multiple of 4 (base64url has no padding by design)
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        data = _json_mod.loads(_b64.urlsafe_b64decode(padded))
        exp = data.get("exp", 0)
        return _time.time() >= (exp - 60)   # 60s buffer
    except Exception:
        return True   # Treat parse errors as expired — refreshing is always safe


# ── Browser session persistence ─────────────────────────────────────────────
# Stores the Supabase refresh token in browser localStorage so auth survives:
#   • browser refresh (F5)
#   • Streamlit Cloud worker restart (idle spin-down)
#   • navigating away and returning
# On every page load init() calls try_restore_from_browser(); if a token is
# found it silently exchanges it for a fresh access+refresh pair.
#
# POC:  streamlit-javascript package (see requirements.txt). The JS eval bridge
#       is async — on the very first render the read returns None; Streamlit
#       automatically reruns when the component resolves, so the second pass
#       gets the real value.
# PROD: Replace with a custom Streamlit component using HttpOnly cookies so the
#       refresh token is never readable by JS on the page.

_WF_RT_KEY = "wf_refresh_token"   # localStorage key


def _save_tokens_to_browser() -> None:
    """Write the current refresh token to browser localStorage."""
    try:
        from streamlit_javascript import st_javascript
        rt = st.session_state.get("_sb_refresh_token", "")
        if rt:
            # Use double-backslash-safe f-string — no backslashes in token, safe to inline.
            st_javascript(f"localStorage.setItem('{_WF_RT_KEY}', '{rt}'); 0")
    except Exception as _e:
        _log.debug("_save_tokens_to_browser: %s", _e)


def _clear_tokens_from_browser() -> None:
    """Remove the stored refresh token from browser localStorage (on sign-out)."""
    try:
        from streamlit_javascript import st_javascript
        st_javascript(f"localStorage.removeItem('{_WF_RT_KEY}'); 0")
    except Exception:
        pass


def try_restore_from_browser() -> bool:
    """
    Attempt to restore a previous auth session from browser localStorage.

    Called from init() when user is None.  Returns True if session was
    successfully restored — caller should st.rerun() so the page re-renders
    in authenticated state.

    Flow:
      1. Read refresh token from localStorage via streamlit-javascript.
      2. st_javascript is async: first render returns None (not ready yet),
         second render returns the actual value.  We only attempt the restore
         once per Streamlit session (guarded by _browser_restore_attempted).
      3. If a token is found, call refresh_session() to get a fresh access token.
      4. On success, load household + grocers from DB and save rotated tokens
         back to localStorage.
      5. On failure (token expired or revoked), clear localStorage and give up
         gracefully — user sees the sign-in form.

    POC:  streamlit-javascript async bridge; requires a double render on first
          visit after a browser refresh.
    PROD: HttpOnly cookie read on the server side — no JS bridge, no extra render.
    """
    if is_authenticated():
        return False

    # Only attempt once per Streamlit session to avoid rerun loops.
    if st.session_state.get("_browser_restore_attempted"):
        return False

    try:
        from streamlit_javascript import st_javascript
        rt = st_javascript(f"localStorage.getItem('{_WF_RT_KEY}')")

        # None → component hasn't rendered yet; will auto-rerun when it does.
        # 0   → localStorage key absent (st_javascript converts JS null/undefined to 0).
        if rt is None:
            return False

        # Mark attempted so we don't loop forever even if the token is bad.
        st.session_state["_browser_restore_attempted"] = True

        if not rt or not isinstance(rt, str) or not rt.strip() or rt == "0":
            return False

        _log.info("try_restore_from_browser: refresh token found, attempting restore")
        st.session_state["_sb_refresh_token"] = rt.strip()
        ok = refresh_session()
        if ok:
            _load_household_from_db()
            _load_grocers_from_db()
            _load_flyer_items_from_db()
            _load_admin_flag()
            _save_tokens_to_browser()   # write back rotated tokens
            _log.info("try_restore_from_browser: session restored successfully")
            return True

        _log.warning("try_restore_from_browser: refresh failed — clearing stored token")
        st.session_state.pop("_sb_refresh_token", None)
        _clear_tokens_from_browser()
        return False

    except Exception as _e:
        st.session_state["_browser_restore_attempted"] = True
        _log.warning("try_restore_from_browser: exception: %s", _e)
        return False


def _jwt_seconds_remaining() -> float:
    """Seconds until the access token expires. Returns 0.0 if expired/missing."""
    import time as _time
    import base64 as _b64
    import json as _json_mod

    token = st.session_state.get("_sb_access_token")
    if not token:
        return 0.0
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return 0.0
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        data = _json_mod.loads(_b64.urlsafe_b64decode(padded))
        exp = data.get("exp", 0)
        return max(0.0, float(exp) - _time.time())
    except Exception:
        return 0.0


def session_expiry_check() -> None:
    """
    Silently refresh the access token when it is near expiry.
    Show a visible banner only when the refresh token itself has expired
    and the user must re-authenticate.

    POC: Call this from init() — runs on every page render.
         Supabase default: access token = 1h, refresh token = 7 days.
    PROD: Run proactively in a background thread 5 min before expiry
          so users never see the expired-state banner at all.
    """
    if not is_authenticated():
        return

    secs = _jwt_seconds_remaining()
    if secs > 300:          # >5 min left — nothing to do
        return

    # <5 min or already expired — try a silent refresh
    ok = refresh_session()
    if ok:
        _save_tokens_to_browser()
        return              # Refreshed silently — user sees nothing

    # Refresh token also expired (after ~7 days) or revoked — need re-auth
    st.warning(
        "⏱️ Your session has expired. "
        "[Sign in again →](/Account) to keep your progress.",
        icon="🔒",
    )


def refresh_session() -> bool:
    """
    Silently renew the access token using the stored refresh token.

    Call this when the JWT may have expired (after ~1 hour) to keep an active
    Streamlit session working without forcing the user to sign in again.

    Updates session_state["_sb_access_token"] and ["_sb_refresh_token"] on success.
    Also updates session_state["user"] if the response includes updated user info.

    Returns True if refresh succeeded, False if the user must sign in again.

    POC:  Refresh tokens rotate on use — the new refresh_token from the response
          must replace the old one immediately or it becomes invalid.
    PROD: Schedule proactive refresh ~5 minutes before expiry. Add exponential
          back-off on network errors. Store refresh_token in a secure HttpOnly
          cookie so it survives Streamlit Cloud session restarts.
    """
    if not _DB_AVAILABLE:
        return False

    refresh_tok = st.session_state.get("_sb_refresh_token")
    if not refresh_tok:
        _log.warning("refresh_session: no refresh_token in session — user must re-sign-in")
        return False

    try:
        url  = st.secrets["supabase"]["url"]
        anon = st.secrets["supabase"]["anon_key"]

        resp = _requests.post(
            f"{url}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_tok},
            headers={"apikey": anon, "Content-Type": "application/json"},
            timeout=10,
        )

        if not resp.ok:
            _log.warning("refresh_session: refresh failed %s — %s",
                         resp.status_code, resp.text[:200])
            return False

        data          = resp.json()
        new_access    = data.get("access_token")
        new_refresh   = data.get("refresh_token", refresh_tok)  # tokens rotate
        user_obj      = data.get("user", {})
        uid           = user_obj.get("id")
        user_email    = user_obj.get("email")

        if not new_access:
            _log.warning("refresh_session: response missing access_token")
            return False

        # Update tokens — refresh_token rotates on every use, must update immediately
        st.session_state["_sb_access_token"]  = new_access
        st.session_state["_sb_refresh_token"] = new_refresh
        if uid:
            st.session_state["user"] = {"id": uid, "email": user_email}
        _log.info("refresh_session: token refreshed successfully for uid=%s", uid)
        # Persist rotated tokens — refresh tokens are single-use; the new pair
        # must overwrite the old ones in localStorage immediately.
        _save_tokens_to_browser()
        return True

    except Exception as e:
        _log.warning("refresh_session: exception: %s", e)
        return False


def is_authenticated() -> bool:
    """True if a user is signed in this session."""
    return st.session_state.get("user") is not None


# Bootstrap admin emails — fallback if DB is unavailable.
# Primary admin check is is_platform_admin column in profiles table.
ADMIN_EMAILS: list[str] = [
    "tim.hislop@gmail.com",
]


def is_admin() -> bool:
    """True if the signed-in user is a WhollyFare platform admin.

    Checks session state cache first (set at sign-in / restore).
    Falls back to ADMIN_EMAILS if DB was unavailable at sign-in.
    """
    user = st.session_state.get("user")
    if not user:
        return False
    # Prefer DB-backed flag cached at sign-in
    if st.session_state.get("_is_platform_admin") is True:
        return True
    # Bootstrap fallback — covers Tim even if profile load failed
    return (user.get("email") or "").lower() in [e.lower() for e in ADMIN_EMAILS]


def _load_admin_flag() -> None:
    """Load is_platform_admin from profiles into session state cache.
    Called at sign-in and session restore so is_admin() never hits the DB."""
    uid = current_user_id()
    if not uid:
        return
    try:
        rows = _sb_select("profiles", select="is_platform_admin,is_test_account",
                          filters={"id": uid})
        if rows:
            st.session_state["_is_platform_admin"] = rows[0].get("is_platform_admin", False)
            st.session_state["_is_test_account"]   = rows[0].get("is_test_account", False)
    except Exception as e:
        _log.warning("_load_admin_flag: %s", e)


def current_user_id() -> str | None:
    """Return the Supabase auth user UUID, or None if not signed in."""
    user = st.session_state.get("user")
    return user["id"] if user else None


def log_activity(event_type: str, page: str = "", metadata: dict | None = None) -> None:
    """Fire-and-forget activity event. Never raises — a logging failure must not
    break the page that triggered it.

    event_type values: 'sign_in', 'sign_up', 'page_view', 'plan_generated',
                       'buyoff_approved', 'shopping_list_viewed', 'flyer_uploaded'
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return
    try:
        user = st.session_state.get("user", {})
        _sb_insert("activity_events", {
            "user_id":    user.get("id"),
            "email":      user.get("email", ""),
            "event_type": event_type,
            "page":       page or "",
            "metadata":   metadata or {},
        })
    except Exception as e:
        _log.debug("log_activity: %s", e)   # silent — never blocks the caller


# ── Admin API helpers ─────────────────────────────────────────────────────────
# These call Supabase's admin REST endpoints (auth/v1/admin/*) using the
# service_role key. Only callable server-side — key never reaches the browser.

def _admin_headers() -> dict:
    """Headers for Supabase admin auth endpoints."""
    svc = st.secrets.get("supabase", {}).get("service_role_key", "")
    url_base = st.secrets.get("supabase", {}).get("url", "")
    return {
        "apikey":        svc,
        "Authorization": f"Bearer {svc}",
        "Content-Type":  "application/json",
    }, url_base


def admin_list_users() -> list[dict]:
    """Return all auth users with their profile flags. Admin only.
    POC: fetches up to 1000 users. PROD: paginate."""
    try:
        headers, url_base = _admin_headers()
        resp = _requests.get(
            f"{url_base}/auth/v1/admin/users?per_page=1000",
            headers=headers, timeout=15,
        )
        if not resp.ok:
            _log.error("admin_list_users: %s %s", resp.status_code, resp.text)
            return []
        users = resp.json().get("users", [])
        # Enrich with profile flags
        profile_rows = _sb_select("profiles",
                                  select="id,is_platform_admin,is_test_account,tier")
        profile_map = {r["id"]: r for r in profile_rows} if profile_rows else {}
        for u in users:
            p = profile_map.get(u["id"], {})
            u["is_platform_admin"] = p.get("is_platform_admin", False)
            u["is_test_account"]   = p.get("is_test_account", False)
            u["tier"]              = p.get("tier", "free")
        return users
    except Exception as e:
        _log.error("admin_list_users: %s", e)
        return []


def admin_set_platform_admin(user_id: str, value: bool) -> tuple[bool, str]:
    """Grant or revoke platform admin status for a user."""
    try:
        _sb_update("profiles", {"is_platform_admin": value}, "id", user_id)
        return True, "Updated."
    except Exception as e:
        return False, str(e)


def admin_set_test_account(user_id: str, value: bool) -> tuple[bool, str]:
    """Flag or unflag a user account as a test account."""
    try:
        _sb_update("profiles", {"is_test_account": value}, "id", user_id)
        return True, "Updated."
    except Exception as e:
        return False, str(e)


def admin_create_test_user(email: str, password: str) -> tuple[bool, str]:
    """Create a new user with email pre-confirmed (no confirmation email sent).
    Use for internal test accounts only — the account is flagged is_test_account.
    POC: no email sent, account active immediately. PROD: same behaviour."""
    try:
        headers, url_base = _admin_headers()
        resp = _requests.post(
            f"{url_base}/auth/v1/admin/users",
            headers=headers,
            json={"email": email, "password": password, "email_confirm": True},
            timeout=15,
        )
        if not resp.ok:
            return False, resp.json().get("message", resp.text)
        uid = resp.json().get("id") or resp.json().get("user", {}).get("id")
        if uid:
            _sb_update("profiles", {"is_test_account": True}, "id", uid)
        return True, "Test account created."
    except Exception as e:
        return False, str(e)


def admin_send_password_reset(email: str) -> tuple[bool, str]:
    """Send a password reset email via Supabase. Safer than admin-setting
    the password directly — keeps Supabase auth as the authority."""
    try:
        headers, url_base = _admin_headers()
        resp = _requests.post(
            f"{url_base}/auth/v1/recover",
            headers=headers,
            json={"email": email},
            timeout=10,
        )
        if resp.ok:
            return True, "Password reset email sent."
        return False, resp.json().get("message", resp.text)
    except Exception as e:
        return False, str(e)


def admin_delete_user(user_id: str) -> tuple[bool, str]:
    """Permanently delete a user and their auth record. Irreversible."""
    try:
        headers, url_base = _admin_headers()
        resp = _requests.delete(
            f"{url_base}/auth/v1/admin/users/{user_id}",
            headers=headers, timeout=10,
        )
        if resp.ok:
            return True, "User deleted."
        return False, resp.json().get("message", resp.text)
    except Exception as e:
        return False, str(e)


def admin_get_activity(limit: int = 200) -> list[dict]:
    """Fetch recent activity events for the admin dashboard."""
    try:
        rows = _sb_select("activity_events", select="*")
        rows = sorted(rows or [], key=lambda r: r.get("created_at",""), reverse=True)
        return rows[:limit]
    except Exception as e:
        _log.error("admin_get_activity: %s", e)
        return []


def admin_get_feedback(status: str = "new") -> list[dict]:
    """Fetch feedback submissions, filtered by status."""
    try:
        filters = {"status": status} if status != "all" else {}
        rows = _sb_select("feedback", select="*", filters=filters)
        return sorted(rows or [], key=lambda r: r.get("created_at",""), reverse=True)
    except Exception as e:
        _log.error("admin_get_feedback: %s", e)
        return []


def submit_feedback(message: str, page: str = "", rating: int | None = None) -> tuple[bool, str]:
    """Submit user feedback. Works for authenticated users."""
    if not message.strip():
        return False, "Message is required."
    try:
        user = st.session_state.get("user", {})
        row: dict = {
            "message": message.strip(),
            "page":    page or "",
            "email":   user.get("email", ""),
        }
        if user.get("id"):
            row["user_id"] = user["id"]
        if rating and 1 <= rating <= 5:
            row["rating"] = rating
        _sb_insert("feedback", row)
        return True, "Thanks for your feedback!"
    except Exception as e:
        return False, str(e)


# ── Authenticated client helper ─────────────────────────────────────────────
def _sb_headers(write: bool = False) -> dict:
    """Build Supabase REST headers for PostgREST calls.

    Token strategy (POC):
      - Writes: service_role_key — bypasses RLS entirely. Safe for server-side
        Python code because the key never reaches the browser. User isolation
        is enforced at the application layer (we always include created_by/user_id
        in write payloads explicitly).
      - Reads: user JWT from session_state, falling back to anon key. RLS
        ensures users only see their own rows.

    PROD: Keep service_role_key for admin/write paths. Add per-user JWT reads
          with token refresh so sessions survive beyond 1 hour.
    """
    url    = st.secrets["supabase"]["url"]
    anon   = st.secrets["supabase"]["anon_key"]

    if write:
        # Service role key bypasses RLS — required for INSERT/UPDATE/DELETE.
        # IMPORTANT: use try/except not .get() — Streamlit's SecretSection
        # doesn't support chained .get() with dict defaults; it silently
        # returns empty when the key exists but the accessor pattern is wrong.
        try:
            svc = st.secrets["supabase"]["service_role_key"] or ""
        except (KeyError, AttributeError, TypeError):
            svc = ""
        if not svc:
            _log.warning("_sb_headers: service_role_key missing from secrets — INSERT will fail RLS")
        # For service_role writes: use svc as BOTH apikey and Authorization.
        # This is the standard Supabase pattern for server-side bypass.
        api_key = svc if svc else anon
        token   = svc if svc else anon
    else:
        api_key = anon
        token   = st.session_state.get("_sb_access_token") or anon

    h = {
        "apikey":        api_key,
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }
    _log.debug("_sb_headers: mode=%s token_type=%s",
               "write" if write else "read",
               "service_role" if (write and svc) else
               "user_jwt"     if (not write and token != anon) else "anon")
    return h


def _sb_url(table: str) -> str:
    return f"{st.secrets['supabase']['url']}/rest/v1/{table}"


def _sb_insert(table: str, payload: dict) -> dict:
    """Insert one row via direct REST call. Returns the created row."""
    resp = _requests.post(_sb_url(table), json=payload, headers=_sb_headers(write=True))
    if not resp.ok:
        raise RuntimeError(f"INSERT {table} failed {resp.status_code}: {resp.text}")
    data = resp.json()
    return data[0] if isinstance(data, list) and data else {}


def _sb_update(table: str, payload: dict, eq_col: str, eq_val: str) -> None:
    """Update rows matching eq_col=eq_val via direct REST call."""
    params = {eq_col: f"eq.{eq_val}"}
    resp = _requests.patch(_sb_url(table), json=payload, headers=_sb_headers(write=True),
                           params=params)
    if not resp.ok:
        raise RuntimeError(f"UPDATE {table} failed {resp.status_code}: {resp.text}")


def _sb_delete(table: str, eq_col: str, eq_val: str) -> None:
    """Delete rows matching eq_col=eq_val via direct REST call."""
    params = {eq_col: f"eq.{eq_val}"}
    resp = _requests.delete(_sb_url(table), headers=_sb_headers(write=True), params=params)
    if not resp.ok:
        raise RuntimeError(f"DELETE {table} failed {resp.status_code}: {resp.text}")


def _sb_select(table: str, select: str = "*", filters: dict | None = None,
               order: str | None = None) -> list:
    """Select rows via direct REST call.

    Args:
        order: PostgREST order string, e.g. "display_order.asc" or "created_at.desc".
    """
    params = {"select": select}
    if filters:
        params.update({k: f"eq.{v}" for k, v in filters.items()})
    if order:
        params["order"] = order
    resp = _requests.get(_sb_url(table), headers=_sb_headers(), params=params)
    if not resp.ok:
        raise RuntimeError(f"SELECT {table} failed {resp.status_code}: {resp.text}")
    return resp.json()


def get_authed_client():
    """Return a Supabase client with the user session restored.

    supabase-py v2's postgrest property calls _get_token() → get_session()
    on the GoTrue client. set_session() populates that internal storage so
    auth.uid() resolves correctly in every RLS policy check.

    PROD: Add token refresh logic when access token nears expiry (1hr default).
    """
    db = get_client()
    access_token  = st.session_state.get("_sb_access_token")
    refresh_token = st.session_state.get("_sb_refresh_token", "")
    if access_token:
        try:
            db.auth.set_session(access_token, refresh_token)
            _log.debug("get_authed_client: session restored via set_session()")
        except Exception as e:
            _log.warning("get_authed_client: set_session failed: %s", e)
    else:
        _log.warning("get_authed_client: no access token — request will be anon")
    return db


# ── Household DB layer ────────────────────────────────────────────────────────
# POC:  Household is saved/loaded on the Household Setup page.
#       Session_state is the working copy; DB is the persistent store.
#       load → session_state on sign-in; save → DB on form submit.
# PROD: Add optimistic updates, conflict resolution, and multi-device sync.

def _load_household_from_db():
    """
    Internal: load household + members from DB into session_state.
    Called automatically on sign-in and on the Household page.
    Silently no-ops if the user has no household yet.

    POC:  Uses direct REST (_sb_select) with the user JWT from session_state —
          same pattern as save_household() and _load_grocers_from_db(). This
          eliminates all supabase-py PostgREST / GoTrue dependency so auth is
          drawn from session_state["_sb_access_token"] directly, not from the
          shared @st.cache_resource client's internal GoTrue session state.
    PROD: Add token refresh on 401, retry logic, and a user-visible banner
          when the profile can't be loaded (e.g. "Saved locally — sync pending").
    """
    if not _DB_AVAILABLE or not is_authenticated():
        _log.warning("_load_household_from_db: skipped — DB available=%s authenticated=%s",
                     _DB_AVAILABLE, is_authenticated())
        return

    uid = current_user_id()
    _log.info("_load_household_from_db: looking up household for uid=%s", uid)

    try:
        # ── Find the household this user belongs to ───────────────────────────
        # Direct REST with user JWT — no GoTrue dependency.
        hh_user_rows = _sb_select("household_users",
                                  select="household_id,role",
                                  filters={"user_id": uid})
        if not hh_user_rows:
            _log.info("_load_household_from_db: no household_users row for uid=%s", uid)
            return

        hid = hh_user_rows[0]["household_id"]
        st.session_state["household_id"] = hid
        _log.info("_load_household_from_db: found household_id=%s", hid)

        # ── Load household record ─────────────────────────────────────────────
        hh_rows = _sb_select("households", select="*", filters={"id": hid})
        if not hh_rows:
            _log.warning("_load_household_from_db: no households row for hid=%s", hid)
            return

        hh = hh_rows[0]

        # ── Load members with their constraints ───────────────────────────────
        members_rows = _sb_select("members",
                                  select="id,name,age,display_order",
                                  filters={"household_id": hid},
                                  order="display_order.asc")

        members = []
        for m in members_rows:
            mid = m["id"]

            allergies  = [r["allergen"]
                          for r in _sb_select("member_allergies",
                                              select="allergen",
                                              filters={"member_id": mid})]
            diagnoses  = [r["diagnosis"]
                          for r in _sb_select("member_diagnoses",
                                              select="diagnosis",
                                              filters={"member_id": mid})]
            lifestyle  = [r["tag"]
                          for r in _sb_select("member_lifestyle_tags",
                                              select="tag",
                                              filters={"member_id": mid})]
            exclusions = [r["exclusion_text"]
                          for r in _sb_select("member_custom_exclusions",
                                              select="exclusion_text",
                                              filters={"member_id": mid})]

            members.append({
                "id":         mid,
                "name":       m["name"],
                "age":        m.get("age"),
                "allergies":  allergies,
                "diagnoses":  diagnoses,
                "lifestyle":  lifestyle,
                "exclusions": exclusions,
            })

        # ── Write into session_state ──────────────────────────────────────────
        st.session_state["household_db"] = {
            "id":                hid,
            "name":              hh.get("name", ""),
            "weekly_budget_usd": float(hh.get("weekly_budget_usd", 120.0)),
            "servings_per_meal": int(hh.get("servings_per_meal", 4)),
            "meals_per_week":    int(hh.get("meals_per_week", 5)),
            "zip_code":          hh.get("primary_zip", ""),
            "city":              hh.get("city", ""),
            "state":             hh.get("state", ""),
            "members":           members,
        }

        # Convert to HouseholdProfile so pages that read session_state["household"] work.
        profile = db_dict_to_profile(st.session_state["household_db"])
        if profile:
            st.session_state["household"] = profile

        # Restore zip into home_zip so the Grocer Hub wizard pre-fills correctly.
        if hh.get("primary_zip"):
            st.session_state["home_zip"] = hh["primary_zip"]
            _log.info("_load_household_from_db: restored home_zip=%s", hh["primary_zip"])

        _log.info("_load_household_from_db: loaded %d members for hid=%s",
                  len(members), hid)

    except Exception as _e:
        # Degrade gracefully — session_state keeps whatever was already loaded.
        # Auth state intentionally NOT cleared here — a DB hiccup should not log
        # the user out. The inline sign-in on the Household page handles genuine
        # auth expiry.
        _log.warning("_load_household_from_db: DB error for uid=%s: %s", uid, _e)


def load_household():
    """
    Public: refresh household from DB into session_state.
    Call at the top of the Household Setup page to ensure data is current.
    """
    _load_household_from_db()


def save_household(household_dict: dict) -> tuple[bool, str]:
    """
    Upsert household + members to DB, then update session_state.

    Args:
        household_dict: dict with keys matching the household session_state shape:
            {name, zip_code, city, state, members: [{name, role, birth_year,
             allergies, diagnoses, lifestyle, exclusions}]}

    Returns (success: bool, message: str).

    POC:  Simple upsert — deletes and re-inserts all member constraints on each save.
          This is fine for a pilot household; PROD needs delta-tracking.
    PROD: Diff members + constraints, apply only changes, write audit log entry.
    """
    if not _DB_AVAILABLE or not is_authenticated():
        _log.warning("save_household: no DB write — DB available=%s authenticated=%s user=%s",
                     _DB_AVAILABLE, is_authenticated(), st.session_state.get("user"))
        # Graceful degradation — keep working in session_state only
        st.session_state["household_db"] = household_dict
        return True, "Saved to session only (no DB connection)."

    uid = current_user_id()
    _log.info("save_household: starting for uid=%s token_present=%s",
              uid, "_sb_access_token" in st.session_state)

    try:
        hid = st.session_state.get("household_id")

        # ── Upsert household row (direct REST — bypasses supabase-py JWT issues) ──
        hh_payload = {
            "name":              household_dict.get("name", "My Household"),
            "weekly_budget_usd": household_dict.get("weekly_budget_usd", 120.0),
            "servings_per_meal": household_dict.get("servings_per_meal", 4),
            "meals_per_week":    household_dict.get("meals_per_week", 5),
            "primary_zip":       household_dict.get("zip_code", ""),
            "city":              household_dict.get("city", ""),
            "state":             household_dict.get("state", "VA"),
            "created_by":        uid,
        }
        if hid:
            update_payload = {k: v for k, v in hh_payload.items() if k not in ("created_by",)}
            _sb_update("households", update_payload, "id", hid)
        else:
            row = _sb_insert("households", hh_payload)
            hid = row["id"]
            st.session_state["household_id"] = hid
            _sb_insert("household_users", {
                "household_id": hid,
                "user_id":      uid,
                "role":         "owner",
            })

        # ── Upsert members ────────────────────────────────────────────────────
        existing = _sb_select("members", select="id,name", filters={"household_id": hid})
        existing_by_name = {r["name"]: r["id"] for r in existing}
        incoming_names = {m["name"] for m in household_dict.get("members", [])}

        for name, mid in existing_by_name.items():
            if name not in incoming_names:
                _sb_delete("members", "id", mid)

        for order_idx, m in enumerate(household_dict.get("members", [])):
            name = m["name"]
            if name in existing_by_name:
                mid = existing_by_name[name]
                _sb_update("members", {"age": m.get("age"), "display_order": order_idx},
                           "id", mid)
            else:
                row = _sb_insert("members", {
                    "household_id":  hid,
                    "name":          name,
                    "age":           m.get("age"),
                    "display_order": order_idx,
                })
                mid = row["id"]

            # Constraints: delete-and-replace (POC)
            for tbl in ("member_allergies", "member_diagnoses",
                        "member_lifestyle_tags", "member_custom_exclusions"):
                _sb_delete(tbl, "member_id", mid)

            for allergen in m.get("allergies", []):
                _sb_insert("member_allergies", {"member_id": mid, "allergen": allergen})
            for diagnosis in m.get("diagnoses", []):
                _sb_insert("member_diagnoses", {"member_id": mid, "diagnosis": diagnosis})
            for tag in m.get("lifestyle", []):
                _sb_insert("member_lifestyle_tags", {"member_id": mid, "tag": tag})
            for exclusion in m.get("exclusions", []):
                _sb_insert("member_custom_exclusions",
                           {"member_id": mid, "exclusion_text": exclusion})

        household_dict["id"] = hid
        st.session_state["household_db"] = household_dict
        _log.info("save_household: saved household_id=%s for uid=%s", hid, uid)
        return True, "Saved."

    except Exception as e:
        _log.error("save_household: exception for uid=%s: %s", uid, e)
        return False, f"DB save failed: {e}. Data saved to session only."


# ── Ledger DB layer ───────────────────────────────────────────────────────────
# POC:  Write one ledger_entry per approved week.
# PROD: Tie entries to specific plan_id + receipt_id; add deduplication.

def _get_or_create_plan_id(db, hid: str, week_start: str) -> str | None:
    """
    Return the meal_plans.id for this household + week_start.
    Creates a stub row if none exists yet (POC shortcut).

    POC:  plan_id is required by ledger_entries (NOT NULL FK).
          We create a minimal placeholder meal_plans row if the engine
          hasn't written one yet (e.g. receipt logged after session refresh).
    PROD: plan_id is set when the weekly plan is generated; this helper is
          only needed for backfill or cross-session reconciliation.
    """
    rows = (
        db.table("meal_plans")
        .select("id")
        .eq("household_id", hid)
        .eq("week_start_date", week_start)
        .limit(1)
        .execute()
        .data
    )
    if rows:
        return rows[0]["id"]

    # Create a stub plan row so the ledger entry FK constraint is satisfied
    try:
        result = db.table("meal_plans").insert({
            "household_id":   hid,
            "week_start_date": week_start,
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception:
        return None


def save_ledger_entry(entry: dict) -> tuple[bool, str]:
    """
    Write a ledger entry to the DB.

    Args:
        entry: dict with app-side keys (see ledger_history shape):
            {week, whollyfare_cost, single_store_cost, found_money,
             vs_hellofresh, meals_planned, stores_used,
             actual_receipt?, actual_found_money?, accuracy_delta?, notes?}

    Returns (success: bool, message: str).
    Session_state ledger_history is the source of truth for the POC;
    DB is a durable backup that survives browser refresh.

    POC:  Column names differ between app-side dicts and the DB schema;
          this function handles the mapping.
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return True, "Session only."

    hid = st.session_state.get("household_id")
    if not hid:
        return False, "No household_id — save household first."

    week_start = entry.get("week")
    if not week_start:
        return False, "No week date in entry."

    try:
        db = get_client()

        # Ensure we have a plan_id (FK is NOT NULL in schema)
        plan_id = _get_or_create_plan_id(db, hid, week_start)
        if not plan_id:
            return False, "Could not resolve plan_id — ledger entry not saved to DB."

        # stores_used is text[] in schema — wrap scalar counts in a list
        stores_val = entry.get("stores_used", [])
        if isinstance(stores_val, int):
            stores_val = []  # count-only — no names available, leave empty
        elif not isinstance(stores_val, list):
            stores_val = [str(stores_val)]

        payload = {
            "household_id":       hid,
            "plan_id":            plan_id,
            "week_start_date":    week_start,
            "meals_planned":      entry.get("meals_planned", 0),
            "stores_used":        stores_val,
            "whollyfare_cost_est": entry.get("whollyfare_cost", 0),
            "found_money_est":    entry.get("found_money", 0),
            "hellofresh_equiv":   entry.get("vs_hellofresh", 0),
            # Honest total spend — separate from Found Money, never affects savings math
            "regulars_cost_est":  entry.get("regulars_cost_est", 0),
            "staples_cost_est":   entry.get("staples_cost_est", 0),
            "total_spend_est":    entry.get("total_spend_est", 0),
            "trip_cost_est":      entry.get("trip_cost", 0),
        }

        # Receipt actuals — only set when present
        if entry.get("actual_receipt") is not None:
            payload["actual_receipt"]       = entry["actual_receipt"]
            payload["single_store_actual"]  = entry.get("single_store_cost", 0)
            payload["found_money_actual"]   = entry.get("actual_found_money", 0)
            payload["vs_hellofresh_actual"] = entry.get("vs_hellofresh", 0)
            payload["accuracy_delta"]       = entry.get("accuracy_delta", 0)
            payload["notes"]                = entry.get("notes", "")
            payload["receipt_logged_at"]    = "now()"

        db.table("ledger_entries").upsert(
            payload, on_conflict="household_id,week_start_date"
        ).execute()
        return True, "Saved."
    except Exception as e:
        return False, str(e)


def load_ledger() -> list[dict]:
    """
    Load ledger entries from DB into session_state["ledger_history"].

    Returns the list of entries (also available in session_state).
    Falls back to existing session_state if DB is unavailable.
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return st.session_state.get("ledger_history", [])

    hid = st.session_state.get("household_id")
    if not hid:
        return st.session_state.get("ledger_history", [])

    try:
        db = get_client()
        rows = (
            db.table("ledger_entries")
            .select("*")
            .eq("household_id", hid)
            .order("week_start_date", desc=True)
            .execute()
            .data
        )
        # Normalise DB column names → app-side dict shape
        history = []
        for r in rows:
            e = {
                "week":              r["week_start_date"],
                "whollyfare_cost":   float(r.get("whollyfare_cost_est") or 0),
                "single_store_cost": float(r.get("single_store_actual") or 0),
                "found_money":       float(r.get("found_money_est") or 0),
                "vs_hellofresh":     float(r.get("hellofresh_equiv") or 0),
                "meals_planned":     r.get("meals_planned") or 0,
                "stores_used":       r.get("stores_used") or [],
                "trip_cost":         float(r.get("trip_cost_est") or 0),
                # Honest total spend fields
                "regulars_cost_est": float(r.get("regulars_cost_est") or 0),
                "staples_cost_est":  float(r.get("staples_cost_est") or 0),
                "total_spend_est":   float(r.get("total_spend_est") or 0),
            }
            # Include actuals if present
            if r.get("actual_receipt") is not None:
                e["actual_receipt"]      = float(r["actual_receipt"])
                e["actual_found_money"]  = float(r.get("found_money_actual") or 0)
                e["vs_hf_actual"]        = float(r.get("vs_hellofresh_actual") or 0)
                e["accuracy_delta"]      = float(r.get("accuracy_delta") or 0)
                e["notes"]               = r.get("notes", "")
            history.append(e)
        st.session_state["ledger_history"] = history
        return history
    except Exception:
        return st.session_state.get("ledger_history", [])


# ── Plan approval DB layer ────────────────────────────────────────────────────

def approve_week_db():
    """
    Extended version of approve_week() that also persists to DB.

    Writes:
      1. meal_plans.approved_at — stamps the approval timestamp
      2. ledger_entries — via save_ledger_entry()

    Call this instead of approve_week() once DB is wired.
    Falls back to session_only approve_week() if DB unavailable.
    """
    # Always update session state first
    approve_week()

    if not _DB_AVAILABLE or not is_authenticated():
        return

    hid = st.session_state.get("household_id")
    if not hid:
        return

    w = st.session_state.get("active_week", "")
    plan = st.session_state.get("plan")
    history = st.session_state.get("ledger_history", [])

    try:
        db = get_client()

        # Stamp approval on meal_plan row if one exists for this week
        db.table("meal_plans").update({"approved_at": "now()"}).eq(
            "household_id", hid
        ).eq("week_start_date", w).is_("approved_at", "null").execute()

        # Save the ledger entry that approve_week() just appended to history
        latest = next((e for e in reversed(history) if e.get("week") == w), None)
        if latest:
            save_ledger_entry(latest)

    except Exception:
        pass  # POC: silently degrade — session_state already updated

# ── Grocer DB layer ───────────────────────────────────────────────────────────
# Mirrors the Household DB layer: session_state is the working copy,
# Supabase is the persistent store. Grocer selections survive browser refresh.
#
# POC:  Upsert on (household_id, chain_name) — last-write-wins per store.
#       Migration 002 added tier, distance_miles, lat, lon to household_grocers
#       and travel_radius_mi to households.
# PROD: Add delta-tracking (detect removed stores), audit log, multi-device
#       sync, and per-store flyer URL resolution.

def _coerce_source(src: str) -> str:
    """Map app-side source labels to the DB CHECK constraint values.

    DB constraint: source_type IN ('manual', 'pdf', 'api', 'pdf_and_api')
    App historically used 'manual_pdf' and 'manual_pdf+api' — these are coerced here
    so INSERTs don't fail the check constraint silently.
    """
    _MAP = {
        "manual_pdf":     "manual",
        "manual_pdf+api": "api",
    }
    return _MAP.get(src, src) if src else "manual"


def save_grocers() -> tuple[bool, str]:
    """
    Persist the current grocer wizard selections to Supabase.

    Reads from:
        st.session_state["grocers"]          — list of grocer dicts (set by wizard)
        st.session_state["travel_radius_mi"] — int, user's preferred search radius
        st.session_state["home_zip"]         — str, household zip

    Writes to:
        household_grocers  — one row per store (delete + re-insert on each save)
        households         — travel_radius_mi preference column

    Returns (success: bool, message: str).
    Degrades gracefully: if DB is unavailable, session_state already has the data.

    POC:  Uses direct REST (_sb_insert/_sb_delete) with service_role_key — same
          pattern as save_household(). This bypasses supabase-py's GoTrue session
          management entirely, so auth is always drawn from session_state tokens.
    PROD: Diff incoming vs existing stores (delta-only writes), add audit log.
    """
    grocers = st.session_state.get("grocers", [])

    # Always persist travel_radius_mi into session_state even without DB
    radius = st.session_state.get("travel_radius_mi", 15)

    if not _DB_AVAILABLE:
        # DB not configured (local dev without Supabase) — degrade gracefully.
        return True, "Saved to session only (no DB connection)."

    if not is_authenticated():
        # User hasn't signed in yet — stores are held in session_state only.
        # Return False so the Grocer Hub shows the orange "sign in to persist" warning,
        # not the green "saved!" message.  Once the user signs in, save_grocers() is
        # called again and writes to DB.
        _log.info("save_grocers: not authenticated — session-only save")
        return False, "Sign in to save your stores permanently."

    hid = st.session_state.get("household_id")
    if not hid:
        _log.warning("save_grocers: no household_id in session — save household profile first")
        return False, "No household_id — save your household profile first, then add stores."

    _log.info("save_grocers: saving %d stores for hid=%s", len(grocers), hid)

    try:
        # ── 1. Persist travel_radius_mi preference on households row ─────────
        # Direct REST with service_role_key — consistent with save_household().
        _sb_update("households", {"travel_radius_mi": radius}, "id", hid)

        # ── 2. Delete existing grocer rows for this household ─────────────────
        # POC: delete-and-replace keeps the logic simple and correct for a single
        # household. PROD: diff incoming vs existing to avoid unnecessary deletes.
        _sb_delete("household_grocers", "household_id", hid)

        # ── 3. Insert each selected store ─────────────────────────────────────
        for order_idx, g in enumerate(grocers):
            payload = {
                "household_id":         hid,
                "chain_name":           g.get("chain", ""),
                "location_description": g.get("location", ""),
                "source_type":          _coerce_source(g.get("source", "manual")),
                "rewards_enrolled":     bool(g.get("rewards", False)),
                "delivery_preferred":   bool(g.get("delivery", False)),
                "is_primary":           bool(g.get("is_primary", False)),
                "display_order":        order_idx,
                # New columns from migration 002
                "tier":                 g.get("tier"),
                "distance_miles":       g.get("distance_miles"),
                "lat":                  g.get("lat"),
                "lon":                  g.get("lon"),
            }
            _sb_insert("household_grocers", payload)

        _log.info("save_grocers: saved %d stores for hid=%s", len(grocers), hid)
        return True, f"Saved {len(grocers)} store(s) to your profile."

    except Exception as e:
        # Degrade gracefully — session_state already has the selections
        _log.error("save_grocers: exception for hid=%s: %s", hid, e)
        return False, f"DB save failed: {e}. Stores saved to session only."


def _load_grocers_from_db():
    """
    Internal: load grocer selections from DB into session_state["grocers"].
    Called automatically on sign-in so the wizard is pre-populated.
    Silently no-ops if the user has no saved grocers yet.

    Also restores:
        session_state["travel_radius_mi"]  — from households.travel_radius_mi
        session_state["store_wizard_done"] — True if at least one grocer exists

    POC:  Uses direct REST (_sb_select) — same auth path as _load_household_from_db()
          and save_grocers(). This is more reliable than the supabase-py PostgREST
          client because auth is drawn from session_state tokens directly.
    PROD: Add per-store flyer URL resolution and location refresh on load.
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return

    hid = st.session_state.get("household_id")
    if not hid:
        _log.warning("_load_grocers_from_db: household_id not set — skipping grocer load")
        return

    _log.info("_load_grocers_from_db: loading grocers for hid=%s", hid)

    try:
        # ── 1. Restore travel_radius_mi from households row ───────────────────
        # Direct REST read — user JWT from session_state, no GoTrue dependency.
        hh_rows = _sb_select("households", select="travel_radius_mi", filters={"id": hid})
        if hh_rows and hh_rows[0].get("travel_radius_mi"):
            st.session_state["travel_radius_mi"] = int(hh_rows[0]["travel_radius_mi"])

        # ── 2. Load grocer rows ───────────────────────────────────────────────
        rows = _sb_select(
            "household_grocers",
            select="*",
            filters={"household_id": hid},
            order="display_order.asc",
        )
        if not rows:
            _log.info("_load_grocers_from_db: no saved grocers found for hid=%s", hid)
            return

        # Normalise DB column names → app-side grocer dict shape
        grocers = []
        for r in rows:
            dist = r.get("distance_miles")
            grocers.append({
                "chain":          r.get("chain_name", ""),
                "location":       r.get("location_description", ""),
                "source":         r.get("source_type", "manual"),
                "rewards":        bool(r.get("rewards_enrolled", False)),
                "delivery":       bool(r.get("delivery_preferred", False)),
                "is_primary":     bool(r.get("is_primary", False)),
                "tier":           r.get("tier"),
                "distance_miles": float(dist) if dist is not None else None,
                "lat":            float(r["lat"]) if r.get("lat") is not None else None,
                "lon":            float(r["lon"]) if r.get("lon") is not None else None,
            })

        st.session_state["grocers"] = grocers
        # Mark wizard as done so the Grocer Hub shows the profile card, not the wizard
        st.session_state["store_wizard_done"] = True
        _log.info("_load_grocers_from_db: restored %d stores for hid=%s", len(grocers), hid)

    except Exception as _e:
        # POC: degrade gracefully — session_state keeps whatever was there.
        # Log the actual error so it shows up in Streamlit Cloud's Manage App logs.
        _log.warning("_load_grocers_from_db: failed for hid=%s: %s", hid, _e)


# ── Flyer / circular DB layer ─────────────────────────────────────────────────
# POC:  flyer_weeks + flyer_items tables store circular data keyed by
#       (household_id, grocer_id, week_start_date). Survives browser refresh
#       and cross-device login — user never has to re-pull the same week twice.
# PROD: Automated background workers re-pull circulars; push notifications
#       when new week's data is available ("New deals just loaded for Kroger").

_VALID_UNITS = {"lb","oz","each","pkg","bunch","bag","dozen","gal","qt","can","jar","box"}
_UNIT_MAP = {
    "lbs":"lb","pound":"lb","pounds":"lb",
    "ounce":"oz","ounces":"oz",
    "gallon":"gal","gallons":"gal","quart":"qt",
    "ea":"each","count":"each","ct":"each","pc":"each","pcs":"each",
    "doz":"dozen",
}
_VALID_CATS = {"produce","protein","dairy","grain","legume","pantry","bakery","frozen","beverage","other"}


def _coerce_unit(unit: str) -> str:
    u = (unit or "each").lower().strip()
    return _UNIT_MAP.get(u, u) if _UNIT_MAP.get(u, u) in _VALID_UNITS else "each"


def _coerce_cat(cat: str) -> str:
    c = (cat or "other").lower().strip()
    return c if c in _VALID_CATS else "other"


def save_flyer_items(chain: str, candidates: list, method: str = "api", week: str = "", platform: bool = True) -> tuple[bool, str]:
    """
    Persist flyer items for one store.

    platform=True  (Admin uploads): writes to platform_flyer_weeks + platform_flyer_items.
                   Data is shared across ALL households. Tim uploads once per week.
    platform=False (User personal stores): writes to session state only. The user's
                   privately-added store items are not shared with other households.
                   PROD: write to household-level flyer_items table instead.

    Each platform upload does a CLEAN REPLACE — stale circular items never persist.

    POC:  Items inserted one at a time (~100-300 rows, fast enough).
    PROD: Bulk upsert via background worker; push notification when new week lands.
    """
    # Non-platform save: session-state only (user personal store, not admin-managed)
    if not platform:
        chain_key = chain.lower().replace(" ", "_")
        from app.core_logic.constraint_engine import IngredientCandidate
        cands = []
        for c in candidates:
            if hasattr(c, "name"):
                cands.append(c)
            else:
                try:
                    cands.append(IngredientCandidate(
                        name=c.get("name",""),
                        usda_fdc_id=c.get("usda_fdc_id"),
                        allergens=c.get("allergens",[]),
                        nutrition={},
                        sale_price_per_unit=float(c.get("sale_price", c.get("sale_price_per_unit",0))),
                        unit=c.get("unit","each"),
                        standard_unit_weight_g=100.0,
                        category=c.get("category","other"),
                        tags=c.get("tags",[]),
                    ))
                except Exception:
                    pass
        fd = st.session_state.get("flyer_data", {})
        fd[chain_key] = cands
        st.session_state["flyer_data"] = fd
        return True, f"Saved {len(cands)} items for {chain} (session only — personal store)."

    if not _DB_AVAILABLE:
        return False, "DB not available — items saved to session only."

    if not week:
        week = st.session_state.get("active_week", "")
    if not week:
        return False, "No active_week set."

    try:
        # 1. Upsert platform_flyer_weeks — one row per (chain, week)
        fw_rows = _sb_select(
            "platform_flyer_weeks",
            select="id",
            filters={"chain_name": chain, "week_start_date": week},
        )
        if fw_rows:
            platform_week_id = fw_rows[0]["id"]
            # Clean replace: delete all existing items for this chain+week
            _sb_delete("platform_flyer_items", "platform_week_id", platform_week_id)
            _log.info("save_flyer_items: replacing existing items for %s week=%s", chain, week)
        else:
            fw_row = _sb_insert("platform_flyer_weeks", {
                "chain_name":      chain,
                "week_start_date": week,
                "load_method":     method if method in ("manual", "pdf", "api") else "manual",
                "item_count":      0,
                "loaded_by":       current_user_id(),
            })
            platform_week_id = fw_row.get("id") if fw_row else None
            if not platform_week_id:
                return False, "Could not create platform_flyer_weeks row."

        # 2. Insert items
        count = 0
        for c in candidates:
            # Support both IngredientCandidate dataclass and plain dicts
            if hasattr(c, "name"):
                name   = c.name
                cat    = _coerce_cat(c.category)
                unit   = _coerce_unit(c.unit)
                price  = float(c.sale_price_per_unit)
                reg    = None
                tags   = list(c.tags) if c.tags else []
                alrg   = list(c.allergens) if c.allergens else []
                fdc    = c.usda_fdc_id
                manual = False
            else:
                name   = c.get("name", "")
                cat    = _coerce_cat(c.get("category", "other"))
                unit   = _coerce_unit(c.get("unit", "each"))
                price  = float(c.get("sale_price", c.get("sale_price_per_unit", 0)))
                reg    = c.get("reg_price") or c.get("regular_price")
                tags   = list(c.get("tags", []))
                alrg   = list(c.get("allergens", []))
                fdc    = c.get("usda_fdc_id")
                manual = bool(c.get("_manual", False))

            if not name or price <= 0:
                continue

            _sb_insert("platform_flyer_items", {
                "platform_week_id": platform_week_id,
                "chain_name":       chain,
                "name":             name[:200],
                "category":         cat,
                "unit":             unit,
                "sale_price":       round(price, 2),
                "regular_price":    round(float(reg), 2) if reg else None,
                "allergens":        alrg,
                "tags":             tags,
                "usda_fdc_id":      fdc,
                "is_manual":        manual,
            })
            count += 1

        # 3. Update item_count
        _sb_update("platform_flyer_weeks", {"item_count": count}, "id", platform_week_id)

        _log.info("save_flyer_items: saved %d platform items for %s week=%s", count, chain, week)
        return True, f"Saved {count} items for {chain}."

    except Exception as e:
        _log.error("save_flyer_items: failed for %s: %s", chain, e)
        return False, f"DB save failed: {e}"


def _load_flyer_items_from_db():
    """
    Load platform flyer items for the current active_week into session_state["flyer_data"].

    Reads from platform_flyer_weeks + platform_flyer_items — shared across ALL
    households. Tim uploads once; every authenticated user sees the same prices.

    Filtered to chains the household has selected in their Grocer Hub so users
    only see items from stores they actually shop at.

    POC:  One query per chain. Loads current week only.
    PROD: Redis cache; fall back to prior week if current week not yet uploaded.
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return

    hid = st.session_state.get("household_id")
    week = st.session_state.get("active_week", "")
    if not week:
        return

    try:
        from app.core_logic.constraint_engine import IngredientCandidate

        # 1. Get chains this household has selected (for filtering)
        chains = []
        if hid:
            g_rows = _sb_select(
                "household_grocers",
                select="chain_name",
                filters={"household_id": hid},
            )
            chains = [r["chain_name"] for r in g_rows] if g_rows else []

        # Fallback 1: session state grocers (user mid-setup, not yet saved to DB)
        if not chains:
            chains = [g.get("chain", "") for g in st.session_state.get("grocers", [])
                      if g.get("chain")]

        # Fallback 2: no stores selected at all — load ALL platform items so new
        # users see prices before completing household setup.
        # POC: fast at pilot scale (handful of chains). PROD: Redis cache.
        if not chains:
            all_weeks = _sb_select("platform_flyer_weeks", select="id,chain_name",
                                   filters={"week_start_date": week})
            chains = [r["chain_name"] for r in all_weeks] if all_weeks else []

        if not chains:
            return

        flyer_data = st.session_state.get("flyer_data", {})
        total = 0

        # 2. For each household chain, load platform items for current week
        for chain in chains:
            fw_rows = _sb_select(
                "platform_flyer_weeks",
                select="id",
                filters={"chain_name": chain, "week_start_date": week},
            )
            if not fw_rows:
                continue
            platform_week_id = fw_rows[0]["id"]

            items = _sb_select(
                "platform_flyer_items",
                select="*",
                filters={"platform_week_id": platform_week_id},
            )
            if not items:
                continue

            candidates = []
            for row in items:
                try:
                    cand = IngredientCandidate(
                        name=row["name"],
                        usda_fdc_id=row.get("usda_fdc_id"),
                        allergens=row.get("allergens") or [],
                        nutrition={},
                        sale_price_per_unit=float(row.get("sale_price") or 0.0),
                        unit=row.get("unit") or "each",
                        standard_unit_weight_g=100.0,
                        category=row.get("category") or "other",
                        tags=row.get("tags") or [],
                    )
                    candidates.append(cand)
                except Exception:
                    pass

            if candidates:
                key = chain.lower().replace(" ", "_")
                # Platform data is authoritative — replace, don't extend
                flyer_data[key] = candidates
                total += len(candidates)

        st.session_state["flyer_data"] = flyer_data
        if total:
            _log.info("_load_flyer_items_from_db: loaded %d platform items for week=%s", total, week)

    except Exception as e:
        _log.error("_load_flyer_items_from_db: %s", e)
        # DB unavailable — session state unchanged
