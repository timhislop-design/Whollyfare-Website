"""
ui/components/auth.py — WhollyFare authentication sidebar widget

Renders a compact sign-in / sign-up / sign-out panel for the sidebar.
Call auth_sidebar() inside a `with st.sidebar:` block, after sidebar_nav().

POC:  Email/password auth via Supabase Auth.
      No email confirmation enforced (Supabase project is in "disable confirmation"
      mode for the pilot — flip this to required before any public launch).
PROD: Add OAuth (Google, Apple), magic links, session refresh, forced logout
      after 30 days, and email verification before account activation.

Usage:
    with st.sidebar:
        style.sidebar_nav()
        auth_sidebar()
"""

import streamlit as st
import ui.state as state


_AUTH_CSS = """
<style>
/* ── Force readable text colour inside the dark sidebar ── */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextInput input {
  color: #1A2E1D !important;
  background-color: #ffffff !important;
}
[data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
  color: #e8f5ec !important;
}
[data-testid="stSidebar"] .stTabs [aria-selected="true"] {
  color: #ffffff !important;
  border-bottom-color: #5DAA6A !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(93,170,106,0.35) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  color: #e8f5ec !important;
}
.wf-auth-wrap {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(58,140,78,0.4);
}
.wf-auth-user {
  font-size: 0.75rem;
  color: #9FD9A8;
  padding: 4px 0;
}
.wf-auth-email {
  font-weight: 700;
  color: #ffffff;
  font-size: 0.8rem;
  word-break: break-all;
}
</style>
"""


def auth_sidebar() -> None:
    """
    Render the auth panel in the sidebar.

    Shows:
      - If signed in: user email + sign-out button
      - If signed out: collapsed expander with sign-in / sign-up tabs
    """
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    state.init()

    if state.is_authenticated():
        user = st.session_state.get("user", {})
        email = user.get("email", "")
        st.markdown(
            f"""<div class="wf-auth-wrap">
              <div class="wf-auth-user">Signed in as</div>
              <div class="wf-auth-email">{email}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="wf_signout", use_container_width=True):
            state.sign_out()
            st.rerun()

    else:
        with st.expander("🔐 Sign in / Create account", expanded=False):
            tab_in, tab_up = st.tabs(["Sign in", "Create account"])

            with tab_in:
                email_in = st.text_input("Email", key="wf_signin_email", label_visibility="collapsed",
                                          placeholder="your@email.com")
                pw_in = st.text_input("Password", type="password", key="wf_signin_pw",
                                      label_visibility="collapsed", placeholder="Password")
                if st.button("Sign in", key="wf_signin_btn", type="primary", use_container_width=True):
                    if email_in and pw_in:
                        ok, msg = state.sign_in(email_in.strip(), pw_in)
                        if ok:
                            st.success("Signed in!")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Enter your email and password.")

            with tab_up:
                email_up = st.text_input("Email", key="wf_signup_email", label_visibility="collapsed",
                                          placeholder="your@email.com")
                pw_up = st.text_input("Password", type="password", key="wf_signup_pw",
                                      label_visibility="collapsed",
                                      placeholder="Choose a password (8+ chars)")
                if st.button("Create account", key="wf_signup_btn", type="primary", use_container_width=True):
                    if email_up and pw_up:
                        ok, msg = state.sign_up(email_up.strip(), pw_up)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Enter your email and a password.")
