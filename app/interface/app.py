"""
app.py — WhollyFare Streamlit Dashboard
----------------------------------------
Entry point for the MVP interface. Run with:
    streamlit run interface/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="WhollyFare",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar nav ──────────────────────────────────────────────────────────────
st.sidebar.image("https://via.placeholder.com/200x60?text=WhollyFare", width=200)
st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")
st.sidebar.page_link("pages/01_profile_setup.py", label="👨‍👩‍👧 Family Profile", icon="1️⃣")
st.sidebar.page_link("pages/02_grocer_connect.py", label="🏪 Connect Grocer", icon="2️⃣")
st.sidebar.page_link("pages/03_meal_plan.py", label="🍽️ My Meal Plan", icon="3️⃣")
st.sidebar.page_link("pages/04_shopping_list.py", label="🛒 Shopping List", icon="4️⃣")
st.sidebar.page_link("pages/05_sunday_buyoff.py", label="✅ Sunday Buy-Off", icon="5️⃣")
st.sidebar.markdown("---")
st.sidebar.caption("WhollyFare.com — Wholly on your side.")

# ── Home page ─────────────────────────────────────────────────────────────────
st.title("🥦 WhollyFare")
st.subheader("Honest meal planning. Real savings. Built around your family.")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**Step 1: Build your family profile**\nTell us about each family member — allergies, diagnoses, food preferences.")

with col2:
    st.info("**Step 2: Connect your grocer**\nWe pull this week's actual sales flyer and rewards deals from your store.")

with col3:
    st.info("**Step 3: Get your plan**\nA 5–7 ingredient weekly meal plan, optimized for your budget and every family member's needs.")

st.markdown("---")

st.markdown("""
### The Sincere Strategy
WhollyFare is a **safe place** to plan your family's meals.

- 🔒 **No sponsored ingredients.** Every recommendation is based on your family's needs — not an advertiser's.
- 💸 **Real savings.** We use your grocer's *actual* weekly circular to find the best deals that work for your dietary profile.
- 🩺 **Health-aware.** Allergies and medical diagnoses are first-class constraints — we will never suggest something that conflicts with any family member's health needs.
- 🧾 **Full transparency.** You can always see *why* each ingredient was selected — what sale triggered it, which constraint it satisfies, what it costs per serving.
""")

if st.button("Get Started →", type="primary"):
    st.switch_page("pages/01_profile_setup.py")
