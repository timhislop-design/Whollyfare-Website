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
from datetime import date, timedelta

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
            return True, "Account created."
        return False, "Sign-up failed — no user returned."
    except Exception as e:
        return False, str(e)


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """
    Sign in with email + password.

    Returns (success: bool, message: str).
    On success, populates st.session_state["user"] and loads household from DB.
    """
    if not _DB_AVAILABLE:
        return False, _DB_IMPORT_ERROR or "Database client not available."
    try:
        db = get_client()
        resp = db.auth.sign_in_with_password({"email": email, "password": password})
        if resp.user:
            st.session_state["user"] = {"id": resp.user.id, "email": resp.user.email}
            # Store both tokens so get_authed_client() can call set_session()
            # which populates the GoTrue internal storage that postgrest reads.
            if resp.session:
                st.session_state["_sb_access_token"]  = resp.session.access_token
                st.session_state["_sb_refresh_token"] = resp.session.refresh_token
            _log.info("sign_in: success uid=%s access_token_stored=%s",
                      resp.user.id, "_sb_access_token" in st.session_state)
            # Attempt to load the household that belongs to this user
            _load_household_from_db()
            # Restore grocer selections so the Grocer Hub wizard is pre-filled
            # without the user having to re-enter their stores on every sign-in.
            _load_grocers_from_db()
            return True, "Signed in."
        _log.warning("sign_in: no user returned for %s", email)
        return False, "Invalid email or password."
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
    # Clear everything — init() will re-populate defaults on next page load
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def is_authenticated() -> bool:
    """True if a user is signed in this session."""
    return st.session_state.get("user") is not None


def current_user_id() -> str | None:
    """Return the Supabase auth user UUID, or None if not signed in."""
    user = st.session_state.get("user")
    return user["id"] if user else None


# ── Authenticated client helper ─────────────────────────────────────────────
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
    """
    if not _DB_AVAILABLE or not is_authenticated():
        _log.warning("_load_household_from_db: skipped — DB available=%s authenticated=%s",
                     _DB_AVAILABLE, is_authenticated())
        return

    uid = current_user_id()
    _log.info("_load_household_from_db: looking up household for uid=%s", uid)

    db = get_authed_client()

    # Find the household this user belongs to
    rows = (
        db.table("household_users")
        .select("household_id, role")
        .eq("user_id", uid)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        return

    hid = rows[0]["household_id"]
    st.session_state["household_id"] = hid
    _log.info("_load_household_from_db: found household_id=%s", hid)

    # Load household record
    hh_rows = (
        db.table("households")
        .select("*")
        .eq("id", hid)
        .limit(1)
        .execute()
        .data
    )
    if not hh_rows:
        return

    hh = hh_rows[0]

    # Load members with their constraints
    members_rows = (
        db.table("members")
        .select("id, name, age, display_order")
        .eq("household_id", hid)
        .order("display_order")
        .execute()
        .data
    )

    members = []
    for m in members_rows:
        mid = m["id"]

        allergies = [
            r["allergen"]
            for r in db.table("member_allergies")
            .select("allergen")
            .eq("member_id", mid)
            .execute()
            .data
        ]
        diagnoses = [
            r["diagnosis"]                          # DB column: diagnosis
            for r in db.table("member_diagnoses")
            .select("diagnosis")
            .eq("member_id", mid)
            .execute()
            .data
        ]
        lifestyle = [
            r["tag"]
            for r in db.table("member_lifestyle_tags")
            .select("tag")
            .eq("member_id", mid)
            .execute()
            .data
        ]
        exclusions = [
            r["exclusion_text"]                     # DB column: exclusion_text
            for r in db.table("member_custom_exclusions")
            .select("exclusion_text")
            .eq("member_id", mid)
            .execute()
            .data
        ]

        members.append({
            "id":         mid,
            "name":       m["name"],
            "age":        m.get("age"),
            "allergies":  allergies,
            "diagnoses":  diagnoses,
            "lifestyle":  lifestyle,
            "exclusions": exclusions,
        })

    # Write into session_state in the shape save_household() expects
    # (a plain dict — pages that need HouseholdProfile call _dict_to_profile())
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
    # Without this, sign-in populates household_db but leaves household=None.
    # PROD: this conversion is always cheap; keep it here.
    profile = db_dict_to_profile(st.session_state["household_db"])
    if profile:
        st.session_state["household"] = profile

    # Also restore zip into home_zip for Grocer Hub wizard
    if hh.get("primary_zip"):
        st.session_state["home_zip"] = hh["primary_zip"]


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

    db = get_authed_client()
    uid = current_user_id()

    try:
        hid = st.session_state.get("household_id")

        # ── Upsert household row ──────────────────────────────────────────────
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
            hh_payload["id"] = hid
            # created_by is set only on insert; remove from update payload
            update_payload = {k: v for k, v in hh_payload.items() if k not in ("id", "created_by")}
            db.table("households").update(update_payload).eq("id", hid).execute()
        else:
            result = db.table("households").insert(hh_payload).execute()
            hid = result.data[0]["id"]
            st.session_state["household_id"] = hid

            # Link user to household
            db.table("household_users").insert({
                "household_id": hid,
                "user_id":      uid,
                "role":         "owner",
            }).execute()

        # ── Upsert members ────────────────────────────────────────────────────
        # POC: fetch existing member IDs by name to detect add/remove
        existing = (
            db.table("members")
            .select("id, name")
            .eq("household_id", hid)
            .execute()
            .data
        )
        existing_by_name = {r["name"]: r["id"] for r in existing}
        incoming_names = {m["name"] for m in household_dict.get("members", [])}

        # Remove members no longer in the list
        for name, mid in existing_by_name.items():
            if name not in incoming_names:
                db.table("members").delete().eq("id", mid).execute()

        # Upsert each incoming member
        for order_idx, m in enumerate(household_dict.get("members", [])):
            name = m["name"]
            if name in existing_by_name:
                mid = existing_by_name[name]
                db.table("members").update({
                    "age":           m.get("age"),
                    "display_order": order_idx,
                }).eq("id", mid).execute()
            else:
                result = db.table("members").insert({
                    "household_id":  hid,
                    "name":          name,
                    "age":           m.get("age"),
                    "display_order": order_idx,
                }).execute()
                mid = result.data[0]["id"]

            # ── Constraints: delete-and-replace (POC) ────────────────────────
            db.table("member_allergies").delete().eq("member_id", mid).execute()
            db.table("member_diagnoses").delete().eq("member_id", mid).execute()
            db.table("member_lifestyle_tags").delete().eq("member_id", mid).execute()
            db.table("member_custom_exclusions").delete().eq("member_id", mid).execute()

            for allergen in m.get("allergies", []):
                db.table("member_allergies").insert({
                    "member_id": mid, "allergen": allergen
                }).execute()

            for diagnosis in m.get("diagnoses", []):
                db.table("member_diagnoses").insert({
                    "member_id": mid, "diagnosis": diagnosis  # DB column: diagnosis
                }).execute()

            for tag in m.get("lifestyle", []):
                db.table("member_lifestyle_tags").insert({
                    "member_id": mid, "tag": tag
                }).execute()

            for exclusion in m.get("exclusions", []):
                db.table("member_custom_exclusions").insert({
                    "member_id": mid, "exclusion_text": exclusion  # DB column: exclusion_text
                }).execute()

        # Update session_state to include the resolved IDs
        household_dict["id"] = hid
        st.session_state["household_db"] = household_dict
        _log.info("save_household: saved household_id=%s for user=%s", hid, uid)
        return True, "Saved."

    except Exception as e:
        # Degrade gracefully — session_state already has the HouseholdProfile
        # set by the calling page before save_household() was called.
        # Do NOT overwrite it with household_dict (a plain dict) — that
        # breaks every page that calls household.household_name etc.
        _log.error("save_household: DB exception for user=%s: %s", uid, e)
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

        payload = {
            "household_id":       hid,
            "plan_id":            plan_id,
            "week_start_date":    week_start,
            "meals_planned":      entry.get("meals_planned", 0),
            "stores_used":        entry.get("stores_used", 0),   # smallint in schema
            "whollyfare_cost_est": entry.get("whollyfare_cost", 0),
            "found_money_est":    entry.get("found_money", 0),
            "hellofresh_equiv":   entry.get("vs_hellofresh", 0),
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
                "stores_used":       r.get("stores_used") or 0,
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

def save_grocers() -> tuple[bool, str]:
    """
    Persist the current grocer wizard selections to Supabase.

    Reads from:
        st.session_state["grocers"]         — list of grocer dicts (set by wizard)
        st.session_state["travel_radius_mi"] — int, user's preferred search radius
        st.session_state["home_zip"]         — str, household zip

    Writes to:
        household_grocers  — one row per store (upsert on household_id + chain_name)
        households         — travel_radius_mi preference column

    Returns (success: bool, message: str).
    Degrades gracefully: if DB is unavailable, session_state already has the data.

    POC:  Removes stores that were deselected (delete + re-insert on each save).
          This is safe for a pilot household. PROD: diff and apply only changes.
    """
    grocers = st.session_state.get("grocers", [])

    # Always persist travel_radius_mi into session_state even without DB
    radius = st.session_state.get("travel_radius_mi", 15)

    if not _DB_AVAILABLE or not is_authenticated():
        return True, "Saved to session only (no DB connection)."

    hid = st.session_state.get("household_id")
    if not hid:
        return False, "No household_id — save household profile first."

    try:
        db = get_authed_client()

        # ── 1. Persist travel_radius_mi preference on households row ─────────
        db.table("households").update(
            {"travel_radius_mi": radius}
        ).eq("id", hid).execute()

        # ── 2. Delete existing grocer rows for this household ─────────────────
        # POC: delete-and-replace keeps the logic simple and correct for a single
        # household. PROD: diff incoming vs existing to avoid unnecessary deletes.
        db.table("household_grocers").delete().eq("household_id", hid).execute()

        # ── 3. Insert each selected store ─────────────────────────────────────
        for order_idx, g in enumerate(grocers):
            payload = {
                "household_id":       hid,
                "chain_name":         g.get("chain", ""),
                "location_description": g.get("location", ""),
                "source_type":        g.get("source", "manual_pdf"),
                "rewards_enrolled":   bool(g.get("rewards", False)),
                "delivery_preferred": bool(g.get("delivery", False)),
                "is_primary":         bool(g.get("is_primary", False)),
                "display_order":      order_idx,
                # New columns from migration 002
                "tier":               g.get("tier"),
                "distance_miles":     g.get("distance_miles"),
                "lat":                g.get("lat"),
                "lon":                g.get("lon"),
            }
            db.table("household_grocers").insert(payload).execute()

        return True, f"Saved {len(grocers)} store(s) to your profile."

    except Exception as e:
        # Degrade gracefully — session_state already has the selections
        return False, f"DB save failed: {e}. Stores saved to session only."


def _load_grocers_from_db():
    """
    Internal: load grocer selections from DB into session_state["grocers"].
    Called automatically on sign-in so the wizard is pre-populated.
    Silently no-ops if the user has no saved grocers yet.

    Also restores:
        session_state["travel_radius_mi"]  — from households.travel_radius_mi
        session_state["store_wizard_done"] — True if at least one grocer exists
    """
    if not _DB_AVAILABLE or not is_authenticated():
        return

    hid = st.session_state.get("household_id")
    if not hid:
        return

    try:
        db = get_authed_client()

        # ── 1. Restore travel_radius_mi from households row ───────────────────
        hh_rows = (
            db.table("households")
            .select("travel_radius_mi")
            .eq("id", hid)
            .limit(1)
            .execute()
            .data
        )
        if hh_rows and hh_rows[0].get("travel_radius_mi"):
            st.session_state["travel_radius_mi"] = int(hh_rows[0]["travel_radius_mi"])

        # ── 2. Load grocer rows ───────────────────────────────────────────────
        rows = (
            db.table("household_grocers")
            .select("*")
            .eq("household_id", hid)
            .order("display_order")
            .execute()
            .data
        )
        if not rows:
            return

        # Normalise DB column names → app-side grocer dict shape
        grocers = []
        for r in rows:
            dist = r.get("distance_miles")
            grocers.append({
                "chain":          r.get("chain_name", ""),
                "location":       r.get("location_description", ""),
                "source":         r.get("source_type", "manual_pdf"),
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

    except Exception:
        pass  # POC: silently degrade — session_state keeps whatever was there

