"""
Home.py — WhollyFare Dashboard
Run with:  streamlit run ui/Home.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from datetime import date

import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="WhollyFare — Smart Grocery Planning",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

state.init()

# ── Sidebar brand mark ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 14px 0 22px 0;'>
      <svg width="130" height="34" viewBox="0 0 130 34" xmlns="http://www.w3.org/2000/svg">
        <g transform="translate(3, 2)">
          <line x1="8"  y1="29" x2="8"  y2="6"  stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
          <line x1="5"  y1="6"  x2="5"  y2="16" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="8"  y1="6"  x2="8"  y2="16" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="11" y1="6"  x2="11" y2="16" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
          <ellipse cx="19" cy="15" rx="8.5" ry="5.5" fill="#5DAA6A" transform="rotate(-28 19 15)"/>
          <line x1="12" y1="20" x2="24" y2="11" stroke="#9FD9A8" stroke-width="0.9" stroke-linecap="round"/>
        </g>
        <text x="34" y="22" font-family="Arial, sans-serif" font-size="16" font-weight="600" fill="white">WhollyFare</text>
      </svg>
      <div style='font-size:11px; color:#9FD9A8; margin-top:2px; margin-left:2px;'>
        Eat well. Spend less.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
style.inject()

household = st.session_state.get("household")
approved  = state.week_approved()
plan      = st.session_state.get("plan")
grocers   = st.session_state.get("grocers", [])
loaded_stores = state.stores_loaded_this_week()
history   = st.session_state.get("ledger_history", [])
total_saved = sum(e.get("found_money", 0) for e in history)

# ── Setup banner ──────────────────────────────────────────────────────────────
if not state.is_setup_complete():
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1E5C32,#3A8C4E);border-radius:12px;
                padding:32px 28px;margin-bottom:24px;'>
      <div style='font-size:1.6rem;font-weight:700;color:white;margin-bottom:8px;'>
        Welcome to WhollyFare 🌿
      </div>
      <div style='font-size:0.95rem;color:rgba(255,255,255,0.85);max-width:540px;line-height:1.7;'>
        Smart meal planning built around your family's budget — not a chef's brand,
        not a subscription box. Real groceries. Real savings. Takes about two minutes to set up.
      </div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("→ Set up my household", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Household.py")
    with col2:
        if st.button("→ Connect my stores", use_container_width=True):
            st.switch_page("pages/2_Grocer_Hub.py")
    st.stop()

# ── Week status banner ────────────────────────────────────────────────────────
hh_name = household.household_name if household else "your household"
week    = st.session_state["active_week"]

if approved and plan:
    st.markdown(
        f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                        padding:16px 20px;margin-bottom:16px;'>
          <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>
            ✅ Week of {week} is approved.
          </span>
          <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>
            Your shopping list is ready.
          </span>
        </div>""",
        unsafe_allow_html=True,
    )
elif plan:
    st.markdown(
        f"""<div style='background:#FFF8E1;border:1px solid #FFD54F;border-radius:10px;
                        padding:16px 20px;margin-bottom:16px;'>
          <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>
            📋 Plan ready for {hh_name}.
          </span>
          <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>
            Head to Sunday Buy-Off to review and approve.
          </span>
        </div>""",
        unsafe_allow_html=True,
    )
elif loaded_stores:
    st.markdown(
        f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                        padding:16px 20px;margin-bottom:16px;'>
          <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>
            📦 {len(loaded_stores)} store(s) loaded.
          </span>
          <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>
            Head to Grocer Hub to run the engine.
          </span>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """<div style='background:#FFF3E0;border:1px solid #FFCC80;border-radius:10px;
                       padding:16px 20px;margin-bottom:16px;'>
          <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>
            📄 No store data loaded yet for this week.
          </span>
          <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>
            Upload circulars or pull from Kroger in the Grocer Hub.
          </span>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Metrics row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    members = household.members if household else []
    st.metric("Household members", len(members))
with col2:
    st.metric("Stores configured", len(grocers))
with col3:
    st.metric("Weeks planned", len(history))
with col4:
    st.metric(
        "Total Found Money 💚",
        f"${total_saved:,.2f}" if total_saved else "$0.00",
        help="Savings vs. buying everything at a single store, every week",
    )

st.divider()

# ── Quick actions ─────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:12px;'>"
    f"This week — {week}</div>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    n_loaded = len(loaded_stores)
    n_total  = len(grocers)
    if st.button(f"🏪 Grocer Hub  ({n_loaded}/{n_total} loaded)", use_container_width=True):
        st.switch_page("pages/2_Grocer_Hub.py")
with col2:
    label = "🍽️ View Plan" if plan else "⚙️ Generate Plan"
    if st.button(label, use_container_width=True):
        st.switch_page("pages/3_Plan.py")
with col3:
    label = "✅ Sunday Buy-Off" + (" — done" if approved else "")
    btn_type = "secondary" if approved else "primary"
    if st.button(label, use_container_width=True, type=btn_type):
        st.switch_page("pages/4_Sunday_BuyOff.py")

# ── Recent history table ──────────────────────────────────────────────────────
if history:
    st.divider()
    st.markdown(
        "<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:10px;'>"
        "Recent weeks</div>",
        unsafe_allow_html=True,
    )
    for entry in reversed(history[-5:]):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.caption(f"**Week of {entry.get('week', '—')}**  ·  {entry.get('meals', 0)} dinners")
        with c2:
            st.caption(f"${entry.get('plan_cost', 0):.2f} spent")
        with c3:
            st.caption(f"${entry.get('found_money', 0):.2f} found")
        with c4:
            st.caption(f"📍 {entry.get('primary_grocer', '—')}")
