"""
Home.py — WhollyFare Dashboard + Landing Page
Run with:  streamlit run ui/Home.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
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

    st.markdown("---")
    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Get started</div>", unsafe_allow_html=True)
    st.page_link("pages/1_Household.py",    label="👨‍👩‍👧 Household Setup",   help="Set up your family profile, allergies, and budget")
    st.page_link("pages/2_Grocer_Hub.py",   label="🏪 Grocer Hub",           help="Connect your stores and load weekly prices")

    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;margin-bottom:8px;'>Weekly plan</div>", unsafe_allow_html=True)
    st.page_link("pages/3_Plan.py",         label="🍽️ This Week's Plan",     help="View your generated meal plan and ingredient picks")
    st.page_link("pages/4_Sunday_BuyOff.py",label="✅ Sunday Buy-Off",        help="Review, approve, and send your shopping list")
    st.page_link("pages/5_Shopping_List.py",label="🛒 Shopping List",         help="Your organised list by store and category")

    st.markdown("<div style='color:#9FD9A8;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;margin-bottom:8px;'>History & info</div>", unsafe_allow_html=True)
    st.page_link("pages/6_Ledger.py",       label="💰 Found Money Ledger",    help="Your running savings record week over week")
    st.page_link("pages/7_Investor.py",     label="📈 Investor Brief",        help="Who we are, why we matter, the opportunity")

style.inject()

household   = st.session_state.get("household")
approved    = state.week_approved()
plan        = st.session_state.get("plan")
grocers     = st.session_state.get("grocers", [])
loaded      = state.stores_loaded_this_week()
history     = st.session_state.get("ledger_history", [])
total_saved = sum(e.get("found_money", 0) for e in history)

# ════════════════════════════════════════════════════════════════════════════════
# LANDING VIEW — new visitors who haven't set up yet
# ════════════════════════════════════════════════════════════════════════════════
if not state.is_setup_complete():

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1E5C32,#3A8C4E);border-radius:14px;
                padding:52px 44px 44px 44px;margin-bottom:36px;text-align:center;'>
      <div style='font-size:2.6rem;font-weight:700;color:white;line-height:1.15;margin-bottom:14px;'>
        Eat well. Spend less.<br>Every week.
      </div>
      <div style='font-size:1.1rem;color:rgba(255,255,255,0.85);margin-bottom:32px;'>
        Your weekly meal plan built from <em>this week's</em> sale prices at your local stores.
      </div>
      <div style='display:flex;gap:20px;flex-wrap:wrap;justify-content:center;margin-bottom:32px;'>
        <div style='background:rgba(255,255,255,0.15);border-radius:10px;padding:16px 28px;min-width:140px;'>
          <div style='font-size:2rem;font-weight:700;color:white;'>15–25%</div>
          <div style='font-size:0.82rem;color:rgba(255,255,255,0.75);margin-top:4px;'>avg. grocery savings</div>
        </div>
        <div style='background:rgba(255,255,255,0.15);border-radius:10px;padding:16px 28px;min-width:140px;'>
          <div style='font-size:2rem;font-weight:700;color:#F28B30;'>~$2–4</div>
          <div style='font-size:0.82rem;color:rgba(255,255,255,0.75);margin-top:4px;'>per serving vs. $9.99 meal kits</div>
        </div>
        <div style='background:rgba(255,255,255,0.15);border-radius:10px;padding:16px 28px;min-width:140px;'>
          <div style='font-size:2rem;font-weight:700;color:white;'>$0</div>
          <div style='font-size:0.82rem;color:rgba(255,255,255,0.75);margin-top:4px;'>paid placements. Ever.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:20px;'>
      <div style='font-size:1.3rem;font-weight:600;color:#1E5C32;'>Three steps. Every Sunday.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, step, title in zip(
        [c1, c2, c3],
        ["🏪", "🛡️", "✅"],
        ["01", "02", "03"],
        ["Load your stores", "We build your plan", "One tap to approve"],
    ):
        with col:
            st.markdown(f"""
            <div style='background:#F4FAF5;border:1px solid #D8EDD0;border-radius:10px;
                        padding:22px 18px;text-align:center;'>
              <div style='font-size:2rem;margin-bottom:6px;'>{icon}</div>
              <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.12em;color:#5DAA6A;margin-bottom:6px;'>STEP {step}</div>
              <div style='font-weight:600;font-size:0.95rem;color:#1E5C32;'>{title}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:32px;'></div>", unsafe_allow_html=True)

    # ── Tiers ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:20px;'>
      <div style='font-size:1.3rem;font-weight:600;color:#1E5C32;'>Start free. Add what your family needs.</div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.columns(4)
    for col, color, tier, label in zip(
        [t1, t2, t3, t4],
        ["#3A8C4E", "#5DAA6A", "#F28B30", "#1E5C32"],
        ["Free", "$5–10/mo", "$15–25/mo", "Full bundle"],
        ["Compare prices across stores", "Meal plan + weekly buy-off", "Health & allergy filtering", "Full recipes + preferences"],
    ):
        with col:
            st.markdown(f"""
            <div style='border-top:4px solid {color};background:white;
                        border:1px solid #D8EDD0;border-top:4px solid {color};
                        border-radius:0 0 10px 10px;padding:16px;text-align:center;'>
              <div style='font-size:1.1rem;font-weight:700;color:{color};margin-bottom:6px;'>{tier}</div>
              <div style='font-size:0.83rem;color:#444;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:32px;'></div>", unsafe_allow_html=True)

    # ── Trust line ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;padding:18px;background:#F4FAF5;border-radius:10px;
                border:1px solid #D8EDD0;margin-bottom:32px;'>
      <span style='color:#1E5C32;font-size:0.92rem;'>
        🚫 No paid placements &nbsp;·&nbsp; 🛡️ Health constraints are hard rules &nbsp;·&nbsp;
        🔍 Every pick shows its reason &nbsp;·&nbsp; 🔐 Your data is yours
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────────────
    cta_l, cta_c, cta_r = st.columns([1, 2, 1])
    with cta_c:
        if st.button("👨‍👩‍👧 Get started — it's free", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Household.py")

    cta2_l, cta2_c, cta2_r = st.columns([2, 1, 2])
    with cta2_c:
        if st.button("📈 Investor brief", use_container_width=True):
            st.switch_page("pages/7_Investor.py")

    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
# DASHBOARD VIEW — returning users with household set up
# ════════════════════════════════════════════════════════════════════════════════
hh_name = household.household_name if household else "your household"
week    = st.session_state["active_week"]

if approved and plan:
    st.markdown(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>✅ Week of {week} is approved.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Your shopping list is ready.</span>
    </div>""", unsafe_allow_html=True)
elif plan:
    st.markdown(f"""<div style='background:#FFF8E1;border:1px solid #FFD54F;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📋 Plan ready for {hh_name}.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Head to Sunday Buy-Off to approve.</span>
    </div>""", unsafe_allow_html=True)
elif loaded:
    st.markdown(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>📦 {len(loaded)} store(s) loaded.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Head to Grocer Hub to run the engine.</span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style='background:#FFF3E0;border:1px solid #FFCC80;border-radius:10px;
                   padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📄 No store data loaded yet for this week.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Upload circulars or pull from Kroger in the Grocer Hub.</span>
    </div>""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Household members", len(household.members) if household else 0)
with col2:
    st.metric("Stores configured", len(grocers))
with col3:
    st.metric("Weeks planned", len(history))
with col4:
    st.metric("Total Found Money 💚", f"${total_saved:,.2f}" if total_saved else "$0.00")

st.divider()
st.markdown(f"<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:12px;'>This week — {week}</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button(f"🏪 Grocer Hub  ({len(loaded)}/{len(grocers)} loaded)", use_container_width=True):
        st.switch_page("pages/2_Grocer_Hub.py")
with col2:
    if st.button("🍽️ View Plan" if plan else "⚙️ Generate Plan", use_container_width=True):
        st.switch_page("pages/3_Plan.py")
with col3:
    label = "✅ Sunday Buy-Off" + (" — done" if approved else "")
    if st.button(label, use_container_width=True, type="secondary" if approved else "primary"):
        st.switch_page("pages/4_Sunday_BuyOff.py")

if history:
    st.divider()
    st.markdown("<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:10px;'>Recent weeks</div>", unsafe_allow_html=True)
    for entry in reversed(history[-5:]):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.caption(f"**Week of {entry.get('week','—')}**  ·  {entry.get('meals',0)} dinners")
        with c2:
            st.caption(f"${entry.get('plan_cost',0):.2f} spent")
        with c3:
            st.caption(f"${entry.get('found_money',0):.2f} found")
        with c4:
            st.caption(f"📍 {entry.get('primary_grocer','—')}")
