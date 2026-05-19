"""app/db/client.py — WhollyFare Supabase client

Single source of truth for the database connection. Every page imports
get_client() from here rather than initialising Supabase directly.

POC:  Credentials loaded from .streamlit/secrets.toml locally,
      or from Streamlit Cloud's Secrets dashboard in deployment.
PROD: Rotate to environment variables managed by the hosting platform;
      add connection pooling (PgBouncer) and service-role key separation.

Usage:
    from app.db.client import get_client
    db = get_client()
    result = db.table("households").select("*").execute()
"""

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    """
    Returns a cached Supabase client for the duration of the session.

    st.cache_resource means this only initialises once per app instance —
    not once per page load or user action. Safe and efficient for a POC.

    POC:  Uses the anon key — safe for RLS-protected tables because
          every table has row-level security policies that gate access
          by auth.uid(). The anon key cannot read data it isn't allowed to.
    PROD: Add a separate service-role client for admin operations
          (aggregate queries, audit log reads, weekly metrics jobs).
          Never expose the service-role key to the browser.
    """
    url: str = st.secrets["supabase"]["url"]
    key: str = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


def test_connection() -> bool:
    """
    Quick sanity check — returns True if the DB is reachable.
    Used on the Admin page and during onboarding to surface connection errors early.

    POC:  Reads one row from feature_flags (public, no auth required).
    PROD: Replace with a dedicated health-check endpoint or a lightweight ping.
    """
    try:
        client = get_client()
        client.table("feature_flags").select("id").limit(1).execute()
        return True
    except Exception:
        return False
