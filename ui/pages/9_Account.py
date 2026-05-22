"""
9_Account.py — WhollyFare Account Page
=======================================
Handles sign-in, account creation, and (when signed in) basic account management.

This page is reached three ways:
  1. "Get started free" button on the homepage → lands on Create Account tab
  2. "Sign in" button on the homepage → lands on Sign In tab (?auth=signin)
  3. Sidebar "Account" link → shows appropriate tab based on auth state

POC vs. PRODUCTION
-------------------
POC:  Email/password auth only. No email confirmation required (disabled in
      Supabase settings for the pilot). Password reset is manual via Supabase dashboard.
PROD: Add Google/Apple OAuth, magic link option, email verification enforcement,
      password reset flow (self-serve), MFA, session management, and account deletion
      per GDPR/CCPA requirements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="Account · WhollyFare",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)
state.init()


def _show_db_diagnosis():
    """Show a step-by-step diagnosis when the DB connection fails."""
    status = state.db_status()

    st.error("Can't reach the database. Here's what's failing:")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        icon = "✅" if status["package_ok"] else "❌"
        st.html(
            f"<div style='text-align:center;padding:12px;background:#{'E3F4E8' if status['package_ok'] else 'FFEBEE'};"
            f"border-radius:8px;'>"
            f"<div style='font-size:1.5rem;'>{icon}</div>"
            f"<div style='font-size:0.8rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>supabase package</div>"
            f"<div style='font-size:0.72rem;color:#5A7A62;'>installed in environment</div>"
            f"</div>")
    with col_b:
        icon = "✅" if status["secrets_ok"] else "❌"
        st.html(
            f"<div style='text-align:center;padding:12px;background:#{'E3F4E8' if status['secrets_ok'] else 'FFEBEE'};"
            f"border-radius:8px;'>"
            f"<div style='font-size:1.5rem;'>{icon}</div>"
            f"<div style='font-size:0.8rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>secrets configured</div>"
            f"<div style='font-size:0.72rem;color:#5A7A62;'>Streamlit Cloud settings</div>"
            f"</div>")
    with col_c:
        icon = "✅" if status["connect_ok"] else "❌"
        st.html(
            f"<div style='text-align:center;padding:12px;background:#{'E3F4E8' if status['connect_ok'] else 'FFEBEE'};"
            f"border-radius:8px;'>"
            f"<div style='font-size:1.5rem;'>{icon}</div>"
            f"<div style='font-size:0.8rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>DB reachable</div>"
            f"<div style='font-size:0.72rem;color:#5A7A62;'>Supabase query succeeded</div>"
            f"</div>")

    if status["error"]:
        st.html("<div style='height:8px;'></div>")

        # First failed step tells us exactly what to fix
        if not status["package_ok"]:
            st.warning(
                "**Fix:** The `supabase` Python package isn't installed.  \n\n"
                "1. Make sure `requirements.txt` has `supabase>=2.0.0` ✓ (it does)  \n"
                "2. Push / commit to GitHub  \n"
                "3. In Streamlit Cloud, click **Reboot app** to force a fresh install  \n\n"
                f"_Raw error: {status['error']}_",
                icon="🔧",
            )
        elif not status["secrets_ok"]:
            st.warning(
                "**Fix:** Supabase credentials aren't in Streamlit Cloud's secrets.  \n\n"
                "1. Go to your app on [share.streamlit.io](https://share.streamlit.io)  \n"
                "2. Click **⋮ → Settings → Secrets**  \n"
                "3. Paste this exactly:\n\n"
                "```toml\n"
                "[supabase]\n"
                "url = \"https://liviclgyapbeoefxbunh.supabase.co\"\n"
                "anon_key = \"sb_publishable_suP4Ty6mULuNTKyilIfEHw_QsBVjwCf\"\n"
                "```\n\n"
                "4. Click **Save** — the app will reboot automatically.",
                icon="🔑",
            )

with st.sidebar:
    style.sidebar_nav()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.html("""
<style>
.wf-auth-card {
  background: #ffffff;
  border: 1px solid #D8EDD0;
  border-radius: 14px;
  padding: 36px 40px;
  max-width: 480px;
  margin: 0 auto;
  box-shadow: 0 4px 32px rgba(30,92,50,0.08);
}
.wf-auth-logo {
  text-align: center;
  margin-bottom: 24px;
}
.wf-auth-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: #1E5C32;
  text-align: center;
  margin-bottom: 6px;
}
.wf-auth-sub {
  font-size: 0.85rem;
  color: #5A7A62;
  text-align: center;
  margin-bottom: 28px;
  line-height: 1.5;
}
.wf-auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0;
  color: #A8C5B0;
  font-size: 0.78rem;
}
.wf-auth-divider::before,
.wf-auth-divider::after {
  content: '';
  flex: 1;
  border-top: 1px solid #D8EDD0;
}
.wf-promise {
  background: #F4FAF5;
  border: 1px solid #D8EDD0;
  border-left: 3px solid #3A8C4E;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.8rem;
  color: #3A5C40;
  margin-top: 20px;
  line-height: 1.55;
}
.wf-acct-section {
  background: #ffffff;
  border: 1px solid #D8EDD0;
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.wf-acct-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #3A8C4E;
  margin-bottom: 8px;
}
</style>
""")


# ════════════════════════════════════════════════════════════════════════════
# SIGNED-IN VIEW — account management
# ════════════════════════════════════════════════════════════════════════════
if state.is_authenticated():
    user = st.session_state.get("user", {})
    email = user.get("email", "")
    hh = st.session_state.get("household")
    hh_db = st.session_state.get("household_db", {})

    style.page_header("My Account", "Manage your WhollyFare profile and preferences.")

    # ── Account summary ───────────────────────────────────────────────────────
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.html('<div class="wf-acct-label">Your account</div>')
        st.html(
            f"""<div class="wf-acct-section">
              <div style="font-size:1.05rem;font-weight:700;color:#1E5C32;margin-bottom:4px;">
                {email}
              </div>
              <div style="font-size:0.82rem;color:#5A7A62;">
                WhollyFare account · Charlottesville pilot
              </div>
            </div>""")

        # Household summary
        if hh or hh_db:
            hh_name    = hh.household_name if hh else hh_db.get("name", "My Household")
            members    = hh.members if hh else []
            budget     = hh.weekly_budget_usd if hh else hh_db.get("weekly_budget_usd", 0)
            meals      = hh.meals_per_week if hh else hh_db.get("meals_per_week", 5)
            servings   = hh.servings_per_meal if hh else hh_db.get("servings_per_meal", 4)
            n_members  = len(members) if members else len(hh_db.get("members", []))
            n_constraints = sum(
                len(m.allergies) + len(m.diagnoses) + len(m.lifestyle_tags)
                for m in members
            ) if members else 0

            st.html('<div class="wf-acct-label" style="margin-top:16px;">Household</div>')
            st.html(
                f"""<div class="wf-acct-section">
                  <div style="font-size:1rem;font-weight:700;color:#1E5C32;margin-bottom:8px;">
                    {hh_name}
                  </div>
                  <div style="display:flex;gap:24px;flex-wrap:wrap;">
                    <div>
                      <div style="font-size:1.3rem;font-weight:800;color:#3A8C4E;">{n_members}</div>
                      <div style="font-size:0.72rem;color:#5A7A62;">members</div>
                    </div>
                    <div>
                      <div style="font-size:1.3rem;font-weight:800;color:#3A8C4E;">${budget:.0f}</div>
                      <div style="font-size:0.72rem;color:#5A7A62;">weekly budget</div>
                    </div>
                    <div>
                      <div style="font-size:1.3rem;font-weight:800;color:#3A8C4E;">{meals}</div>
                      <div style="font-size:0.72rem;color:#5A7A62;">dinners/week</div>
                    </div>
                    <div>
                      <div style="font-size:1.3rem;font-weight:800;color:#3A8C4E;">{servings}</div>
                      <div style="font-size:0.72rem;color:#5A7A62;">servings/meal</div>
                    </div>
                    {f'<div><div style="font-size:1.3rem;font-weight:800;color:#F28B30;">{n_constraints}</div><div style="font-size:0.72rem;color:#5A7A62;">active constraints</div></div>' if n_constraints else ''}
                  </div>
                </div>""")

            if st.button("✏️ Edit household profile", use_container_width=False):
                st.switch_page("pages/1_Household.py")
        else:
            st.info("No household set up yet.", icon="🏠")
            if st.button("👨‍👩‍👧 Set up household", type="primary"):
                st.switch_page("pages/1_Household.py")

        # ── Shopping area ─────────────────────────────────────────────────────
        # POC: User sets their zip and radius; Grocer Hub filters chains accordingly.
        # PROD: Zip resolved from billing address; radius updated from profile.
        #       Store locator API confirms which chains have locations within radius.
        from app.data.store_regions import region_label, chains_for_zip
        st.html('<div class="wf-acct-label" style="margin-top:16px;">Shopping area</div>')

        current_zip    = st.session_state.get("home_zip", "22901")
        current_radius = st.session_state.get("store_radius_mi", 15)
        region_name    = region_label(current_zip)
        nearby_count   = len(chains_for_zip(current_zip))

        st.html(
            f"""<div class="wf-acct-section">
              <div style="font-size:0.85rem;color:#5A7A62;margin-bottom:12px;">
                WhollyFare shows you stores available within your zip code and radius.
                Change these and the Grocer Hub updates instantly.
              </div>
              <div style="display:flex;gap:20px;align-items:baseline;flex-wrap:wrap;margin-bottom:10px;">
                <div>
                  <div style="font-size:1.4rem;font-weight:800;color:#3A8C4E;">{current_zip}</div>
                  <div style="font-size:0.72rem;color:#5A7A62;">{region_name}</div>
                </div>
                <div>
                  <div style="font-size:1.4rem;font-weight:800;color:#3A8C4E;">{current_radius} mi</div>
                  <div style="font-size:0.72rem;color:#5A7A62;">radius</div>
                </div>
                <div>
                  <div style="font-size:1.4rem;font-weight:800;color:#3A8C4E;">{nearby_count}</div>
                  <div style="font-size:0.72rem;color:#5A7A62;">chains available near you</div>
                </div>
              </div>
            </div>""")

        with st.expander("Change zip code or radius", expanded=False):
            za, zb = st.columns([1, 1])
            with za:
                new_zip = st.text_input(
                    "Home zip code",
                    value=current_zip,
                    max_chars=5,
                    placeholder="e.g. 22901",
                    help="Used to filter which grocery chains are shown in the Grocer Hub.",
                )
            with zb:
                new_radius = st.number_input(
                    "Shopping radius (miles)",
                    min_value=5, max_value=100, step=5,
                    value=int(current_radius),
                    help="How far you're willing to drive for groceries.",
                )
            if st.button("Update shopping area", type="primary"):
                if new_zip.strip().isdigit() and len(new_zip.strip()) == 5:
                    st.session_state["home_zip"]        = new_zip.strip()
                    st.session_state["store_radius_mi"] = int(new_radius)
                    new_region = region_label(new_zip.strip())
                    new_count  = len(chains_for_zip(new_zip.strip()))
                    st.success(
                        f"Updated — showing stores for {new_zip.strip()} "
                        f"({new_region}, {new_count} chains within {int(new_radius)} miles)."
                    )
                    st.rerun()
                else:
                    st.warning("Enter a valid 5-digit US zip code.")

        # Savings summary
        ledger = state.load_ledger()
        if ledger:
            total_found = sum(e.get("found_money", 0) for e in ledger)
            st.html('<div class="wf-acct-label" style="margin-top:16px;">Savings to date</div>')
            st.html(
                f"""<div class="wf-acct-section"
                         style="display:flex;align-items:center;gap:24px;">
                  <div>
                    <div style="font-size:2rem;font-weight:800;color:#BF5E00;line-height:1;">
                      ${total_found:,.2f}
                    </div>
                    <div style="font-size:0.8rem;color:#5A7A62;margin-top:4px;">
                      Found Money across {len(ledger)} week(s)
                    </div>
                  </div>
                </div>""")
            if st.button("💰 View full ledger"):
                st.switch_page("pages/6_Ledger.py")

        # Subscription tier
        st.html('<div class="wf-acct-label" style="margin-top:16px;">Current plan</div>')
        st.html(
            """<div class="wf-acct-section">
              <div style="display:flex;align-items:center;gap:12px;">
                <div style="background:#D8EDD0;color:#1E5C32;font-size:0.7rem;font-weight:700;
                            letter-spacing:0.08em;padding:4px 12px;border-radius:20px;">
                  PILOT ACCESS
                </div>
                <div style="font-size:0.85rem;color:#5A7A62;">
                  All features active · Charlottesville pilot program
                </div>
              </div>
            </div>""")

    with col_side:
        st.html("<div style='height:36px;'></div>")
        if st.button("🚪 Sign out", use_container_width=True):
            state.sign_out()
            st.rerun()

        st.html("<div style='height:12px;'></div>")
        st.html(
            """<div style='font-size:0.75rem;color:#5A7A62;line-height:1.6;
                          background:#F4FAF5;border-radius:8px;padding:12px;'>
              <strong style='color:#1E5C32;'>Your data promise</strong><br>
              Your health data and grocery data are never sold, shared, or used for targeting.
              WhollyFare's only revenue is your subscription.
            </div>""")

    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# SIGNED-OUT VIEW — sign in or create account
# ════════════════════════════════════════════════════════════════════════════

# Determine which tab to open by default — ?auth=signin routes to Sign In
_default_tab = st.session_state.pop("_auth_tab", "create")

# Centred card layout
_, card_col, _ = st.columns([1, 2, 1])

with card_col:

    # Logo / brand mark inside the card
    st.html("""
    <div class="wf-auth-logo">
      <svg width="52" height="52" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg"
           aria-label="WhollyFare" role="img">
        <line x1="14" y1="46" x2="14" y2="10" stroke="#3A8C4E" stroke-width="2.8" stroke-linecap="round"/>
        <line x1="9"  y1="10" x2="9"  y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="14" y1="10" x2="14" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="19" y1="10" x2="19" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <ellipse cx="36" cy="26" rx="13" ry="8.5" fill="#5DAA6A" transform="rotate(-28 36 26)"/>
        <line x1="24" y1="35" x2="46" y2="18" stroke="#9FD9A8" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <div style="font-size:1.3rem;font-weight:800;color:#1E5C32;margin-top:6px;">WhollyFare</div>
      <div style="font-size:0.78rem;color:#5A7A62;font-style:italic;">Eat well. Spend less.</div>
    </div>
    """)

    # ── Tabs — Create Account is default for new visitors, Sign In for returning ─
    if _default_tab == "signin":
        tab_in, tab_up = st.tabs(["🔐 Sign in", "✨ Create account"])
    else:
        tab_up, tab_in = st.tabs(["✨ Create account", "🔐 Sign in"])

    # ── CREATE ACCOUNT TAB ────────────────────────────────────────────────────
    with tab_up:
        st.html(
            "<div style='font-size:0.92rem;color:#5A7A62;margin:12px 0 20px;line-height:1.55;'>"
            "Free forever for Price Finder. No credit card needed.<br>"
            "Takes about two minutes to get your first week's plan."
            "</div>")

        with st.form("create_account_form", clear_on_submit=False):
            new_email = st.text_input(
                "Email address",
                placeholder="you@example.com",
                help="This is your WhollyFare login. We won't send you marketing email.",
            )
            new_pw = st.text_input(
                "Choose a password",
                type="password",
                placeholder="8 or more characters",
                help="Pick something you'll remember — no password rules, just make it decent.",
            )
            new_pw2 = st.text_input(
                "Confirm password",
                type="password",
                placeholder="Same password again",
            )
            create_btn = st.form_submit_button(
                "Create my WhollyFare account →",
                type="primary",
                use_container_width=True,
            )

        if create_btn:
            if not new_email or not new_pw:
                st.error("Enter your email and choose a password.")
            elif new_pw != new_pw2:
                st.error("Passwords don't match — try again.")
            elif len(new_pw) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                with st.spinner("Creating your account…"):
                    ok, msg = state.sign_up(new_email.strip(), new_pw)
                if ok:
                    st.success("✅ Account created! Setting you up…")
                    st.balloons()
                    import time; time.sleep(1.2)
                    st.switch_page("pages/1_Household.py")
                else:
                    if "already registered" in msg.lower() or "already exists" in msg.lower():
                        st.error("That email is already registered. Use the Sign In tab.")
                    elif "not available" in msg.lower() or "not installed" in msg.lower() or "secrets" in msg.lower():
                        # DB/config problem — show diagnostic
                        _show_db_diagnosis()
                    else:
                        st.error(f"Couldn't create account: {msg}")

        st.html(
            """<div class="wf-promise">
              🔐 <strong>Your data promise:</strong> WhollyFare never sells your data, shares
              your health information, or shows you ads. Revenue is subscriptions only — that's
              the Sincere Strategy, and it's non-negotiable.
            </div>""")

    # ── SIGN IN TAB ───────────────────────────────────────────────────────────
    with tab_in:
        st.html(
            "<div style='font-size:0.92rem;color:#5A7A62;margin:12px 0 20px;'>"
            "Welcome back. Sign in to restore your household and savings history."
            "</div>")

        with st.form("sign_in_form", clear_on_submit=False):
            si_email = st.text_input(
                "Email address",
                placeholder="you@example.com",
                key="si_email",
            )
            si_pw = st.text_input(
                "Password",
                type="password",
                placeholder="Your password",
                key="si_pw",
            )
            si_btn = st.form_submit_button(
                "Sign in →",
                type="primary",
                use_container_width=True,
            )

        if si_btn:
            if not si_email or not si_pw:
                st.error("Enter your email and password.")
            else:
                with st.spinner("Signing in…"):
                    ok, msg = state.sign_in(si_email.strip(), si_pw)
                if ok:
                    st.success("✅ Signed in! Loading your household…")
                    import time; time.sleep(0.8)
                    st.switch_page("pages/1_Household.py")
                else:
                    if "invalid" in msg.lower() or "credentials" in msg.lower():
                        st.error("Email or password not recognised. Check your details and try again.")
                    elif "not available" in msg.lower() or "not installed" in msg.lower() or "secrets" in msg.lower():
                        _show_db_diagnosis()
                    else:
                        st.error(f"Sign in failed: {msg}")

        st.html(
            "<div style='font-size:0.8rem;color:#5A7A62;margin-top:16px;text-align:center;'>"
            "Forgot your password? Email "
            "<a href='mailto:tim.hislop@gmail.com' style='color:#3A8C4E;'>tim.hislop@gmail.com</a> "
            "during the pilot — self-serve reset coming in Phase 2."
            "</div>")
