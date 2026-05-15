"""
7_Investor.py — WhollyFare Investor Page
Who we are, why we matter, what we mean to the food and meal planning landscape.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.style as style

st.set_page_config(
    page_title="Investor Brief · WhollyFare",
    page_icon="📈",
    layout="wide",
)
style.inject()

# ── Custom investor-page CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
.inv-hero {
    background: linear-gradient(135deg, #1B2A4A 0%, #007A87 100%);
    border-radius: 12px;
    padding: 48px 40px;
    color: white;
    margin-bottom: 32px;
}
.inv-hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0 0 12px 0;
    color: white;
}
.inv-hero .tagline {
    font-size: 1.2rem;
    opacity: 0.88;
    max-width: 680px;
    line-height: 1.6;
}
.inv-hero .sub {
    margin-top: 20px;
    font-size: 0.9rem;
    opacity: 0.65;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.stat-card {
    background: #f4f7f9;
    border-radius: 10px;
    padding: 22px 18px;
    border-left: 4px solid #007A87;
    height: 100%;
}
.stat-card .stat-number {
    font-size: 2rem;
    font-weight: 800;
    color: #1B2A4A;
    line-height: 1.1;
}
.stat-card .stat-label {
    font-size: 0.82rem;
    color: #555;
    margin-top: 4px;
    line-height: 1.4;
}
.stat-card .stat-source {
    font-size: 0.72rem;
    color: #888;
    margin-top: 8px;
}
.sincere-pill {
    display: inline-block;
    background: #E8F5E9;
    color: #2E7D32;
    border: 1px solid #A5D6A7;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
}
.competitor-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px 14px;
}
.competitor-card .comp-name {
    font-weight: 700;
    font-size: 1rem;
    color: #1B2A4A;
}
.competitor-card .comp-cost {
    font-size: 1.3rem;
    font-weight: 800;
    color: #C62828;
    margin: 4px 0;
}
.competitor-card .comp-desc {
    font-size: 0.8rem;
    color: #666;
    line-height: 1.4;
}
.whollyfare-card {
    background: linear-gradient(135deg, #E8F5E9, #E0F7FA);
    border: 2px solid #007A87;
    border-radius: 8px;
    padding: 16px 14px;
}
.whollyfare-card .comp-name {
    font-weight: 700;
    font-size: 1rem;
    color: #007A87;
}
.whollyfare-card .comp-cost {
    font-size: 1.3rem;
    font-weight: 800;
    color: #2E7D32;
    margin: 4px 0;
}
.whollyfare-card .comp-desc {
    font-size: 0.8rem;
    color: #555;
    line-height: 1.4;
}
.phase-card {
    border-radius: 8px;
    padding: 18px 16px;
    margin-bottom: 8px;
}
.phase-1 { background: #E3F2FD; border-left: 4px solid #1565C0; }
.phase-2 { background: #E8F5E9; border-left: 4px solid #2E7D32; }
.phase-3 { background: #FFF3E0; border-left: 4px solid #E65100; }
.phase-4 { background: #F3E5F5; border-left: 4px solid #6A1B9A; }
.phase-card .phase-title { font-weight: 700; font-size: 1rem; color: #1B2A4A; }
.phase-card .phase-sub   { font-size: 0.8rem; color: #555; margin-top: 4px; line-height: 1.5; }
.halo-ring {
    background: #FFF8E1;
    border: 1px solid #FFD54F;
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
}
.halo-ring .ring-label { font-weight: 700; font-size: 0.9rem; color: #F57F17; }
.halo-ring .ring-desc  { font-size: 0.78rem; color: #666; margin-top: 4px; line-height: 1.4; }
.ask-box {
    background: linear-gradient(135deg, #1B2A4A 0%, #0D4F5C 100%);
    border-radius: 12px;
    padding: 36px 32px;
    color: white;
    text-align: center;
}
.ask-box h2 { color: white; font-size: 1.8rem; margin-bottom: 12px; }
.ask-box .ask-amount { font-size: 3rem; font-weight: 900; color: #80DEEA; margin: 8px 0; }
.ask-box .ask-desc   { opacity: 0.85; max-width: 560px; margin: 0 auto; line-height: 1.6; }
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #007A87;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="inv-hero">
  <div class="sub">Investor Brief · Sentir Solutions LLC · Palmyra, VA</div>
  <h1>WhollyFare</h1>
  <div class="tagline">
    The first meal-planning platform built entirely around your family's budget —
    not a chef's brand, not a subscription box, not a sponsored circular.
    Real groceries. Real savings. Radically transparent.
  </div>
</div>
""", unsafe_allow_html=True)


# ── MARKET PROBLEM ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">The Problem</div>', unsafe_allow_html=True)
st.markdown("### American families are losing the grocery game — and they don't know it.")

col_p1, col_p2 = st.columns([3, 2])
with col_p1:
    st.markdown("""
The average U.S. household spends **$5,703 per year** on groceries *(BLS Consumer Expenditure Survey, 2023)*
— and leaves an estimated **15–25% on the table** through brand loyalty, single-store shopping, and
missed weekly sales. That's up to **$1,400/year** silently evaporating from a family's budget.

The tools that exist today don't actually solve this:

- **Meal-kit services** (HelloFresh, Blue Apron) charge a **$9.99/serving premium** to solve the
  "what's for dinner" problem — but they cost *more* than the grocery store, not less.
- **Grocery apps** (Flipp, Ibotta) surface coupons but have zero integration with menu planning —
  the family still has to figure out what to *cook*.
- **Instacart / DoorDash** optimize for convenience at a margin premium; savings are never the goal.
- **Dietitians and nutrition apps** give meal guidance but have no price awareness at all.

**Nobody has connected the dots.** No platform currently optimizes the full loop:
sale prices → constraint-aware meal plan → shopping list → grocer checkout.
That's the gap WhollyFare was built to close.
    """)
with col_p2:
    st.markdown("""
<div class="stat-card">
  <div class="stat-number">$5,703</div>
  <div class="stat-label">Average annual U.S. household grocery spend</div>
  <div class="stat-source">BLS Consumer Expenditure Survey, 2023</div>
</div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div class="stat-card">
  <div class="stat-number">$1,400</div>
  <div class="stat-label">Estimated annual savings available through cross-store price optimization (15–25%)</div>
  <div class="stat-source">Internal WhollyFare analysis</div>
</div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div class="stat-card">
  <div class="stat-number">$9.99</div>
  <div class="stat-label">HelloFresh cost per serving — the benchmark WhollyFare beats every week</div>
  <div class="stat-source">HelloFresh published pricing, 2024</div>
</div>
    """, unsafe_allow_html=True)

st.divider()


# ── THE SOLUTION ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">The Solution</div>', unsafe_allow_html=True)
st.markdown("### WhollyFare: the meal-planning engine that shops for you.")

st.markdown("""
WhollyFare inverts the meal-kit model. Instead of charging a premium for pre-portioned ingredients,
we use each week's **actual sale circulars** from your local grocers to build the lowest-cost,
nutritionally sound, allergy-safe meal plan for your household — then hand you a single shopping list
organized by store and aisle.

The engine runs a three-stage pipeline every week:
""")

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown("""
<div class="stat-card" style="border-left-color:#1565C0;">
  <div style="font-size:1.4rem;margin-bottom:6px">🛒</div>
  <div class="stat-number" style="font-size:1.2rem">1. Harvest</div>
  <div class="stat-label">Pull weekly sale prices from grocery APIs and PDF circulars.
  Every item is tagged with category, allergens, and nutrition data via USDA FDC.</div>
</div>
    """, unsafe_allow_html=True)
with col_s2:
    st.markdown("""
<div class="stat-card" style="border-left-color:#2E7D32;">
  <div style="font-size:1.4rem;margin-bottom:6px">🛡️</div>
  <div class="stat-number" style="font-size:1.2rem">2. Filter</div>
  <div class="stat-label">Run every item through the household's hard constraints —
  allergies, diagnoses (celiac, diabetes, CKD, IBS), lifestyle tags.
  Zero compromise. Every rejection is logged and shown to the user.</div>
</div>
    """, unsafe_allow_html=True)
with col_s3:
    st.markdown("""
<div class="stat-card" style="border-left-color:#E65100;">
  <div style="font-size:1.4rem;margin-bottom:6px">🍽️</div>
  <div class="stat-number" style="font-size:1.2rem">3. Plan</div>
  <div class="stat-label">Score remaining ingredients by sale savings × nutrition density.
  Select 5–7 hero ingredients and rotate them through flavor plugins
  (Mexican, Asian, Mediterranean, Indian, American Comfort) for a full week of dinners.</div>
</div>
    """, unsafe_allow_html=True)

st.divider()


# ── COMPETITIVE LANDSCAPE ─────────────────────────────────────────────────────
st.markdown('<div class="section-label">Competitive Landscape</div>', unsafe_allow_html=True)
st.markdown("### A $25B industry with no one optimizing for the customer.")

st.markdown("""
The meal planning and grocery delivery space is large, fragmented, and almost entirely oriented
around **margins for the platform** rather than **savings for the family.**
WhollyFare occupies white space that none of the incumbents can easily enter
without dismantling their own business model.
""")

cols = st.columns(5)
competitors = [
    {
        "name": "HelloFresh",
        "cost": "$9.99/serving",
        "desc": "Convenient. Quality-branded. Expensive. No local-store integration. No constraint awareness.",
        "whollyfare": False,
    },
    {
        "name": "Blue Apron",
        "cost": "$10.99/serving",
        "desc": "Premium meal-kit. Chef-forward. Financially distressed. Same fundamental model as HelloFresh.",
        "whollyfare": False,
    },
    {
        "name": "Flipp / Ibotta",
        "cost": "Free",
        "desc": "Coupon aggregators with ad-supported models. No meal planning. No constraint engine. Revenue from advertisers.",
        "whollyfare": False,
    },
    {
        "name": "Instacart",
        "cost": "$3.99+/order",
        "desc": "Delivery platform. Charges markup on groceries. No meal planning, no savings optimization.",
        "whollyfare": False,
    },
    {
        "name": "WhollyFare",
        "cost": "~$2–4/serving",
        "desc": "Cross-grocer price optimization, hard health constraints, transparent logic, no paid placements — ever.",
        "whollyfare": True,
    },
]

for col, comp in zip(cols, competitors):
    with col:
        card_class = "whollyfare-card" if comp["whollyfare"] else "competitor-card"
        st.markdown(
            f"""<div class="{card_class}">
              <div class="comp-name">{comp['name']}</div>
              <div class="comp-cost">{comp['cost']}</div>
              <div class="comp-desc">{comp['desc']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()


# ── THE SINCERE STRATEGY ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Our Moat</div>', unsafe_allow_html=True)
st.markdown("### The Sincere Strategy: six non-negotiable commitments that are also a competitive moat.")

st.markdown("""
WhollyFare operates under a founding philosophy we call the **Sincere Strategy** — a set of
commitments to the user that competitors cannot easily copy without fundamentally changing
their revenue model. Each commitment builds trust. Together, they create a moat.
""")

sincere_commitments = [
    ("🚫 No paid placements", "Recommendations are never influenced by brand partnerships or advertising. No grocer, brand, or CPG company can pay to appear in a plan. Ever."),
    ("🛡️ Sacrosanct health constraints", "If a household member has a peanut allergy, peanuts never appear — not in a plan, not in a suggestion, not in a 'you might also like.' Health constraints are the engine's highest-priority input."),
    ("🔍 Radical transparency", "Every ingredient rejection is logged and shown to the user. The constraint audit log is a first-class UI feature. No black boxes."),
    ("📍 Local-first", "Plans are built from your local grocers' actual weekly circulars, not national averages or partnered inventory. The savings are real and verifiable."),
    ("💰 Safety over savings", "We will never recommend an unsafe ingredient because it's on sale. The constraint engine runs before the budget optimizer."),
    ("🔐 User data ownership", "Household health data is yours. WhollyFare does not sell, share, or use it for targeting. The pilot runs entirely on-device — zero cloud dependency."),
]

col_a, col_b = st.columns(2)
for i, (icon_label, desc) in enumerate(sincere_commitments):
    target_col = col_a if i % 2 == 0 else col_b
    with target_col:
        st.markdown(
            f"""<div style='background:#f9f9f9;border-radius:8px;padding:14px 16px;
                margin-bottom:10px;border-left:3px solid #007A87'>
              <div style='font-weight:700;font-size:0.95rem;color:#1B2A4A;margin-bottom:4px'>{icon_label}</div>
              <div style='font-size:0.83rem;color:#444;line-height:1.5'>{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()


# ── HALO OF TRUST / GO-TO-MARKET ──────────────────────────────────────────────
st.markdown('<div class="section-label">Go-To-Market</div>', unsafe_allow_html=True)
st.markdown("### The Halo of Trust: start at the edge, earn the mainstream.")

st.markdown("""
Our distribution strategy is deliberately counter-intuitive. We don't start with mass-market families —
we start with the households who need reliable, safe meal planning the *most* and will become
the most vocal advocates: **medical-edge users**.

Families managing celiac disease, MCAS, EDS, Type 1 diabetes, or CKD don't just want a meal planner —
they need one they can *trust absolutely.* When WhollyFare earns that trust, it radiates outward:
""")

ring_cols = st.columns(4)
rings = [
    ("Ring 1\nMedical Edge", "MCAS · Celiac · CKD · EDS · PKU\nHigh advocacy, high trust-building need, zero tolerance for error"),
    ("Ring 2\nHealth-Aware", "Diabetic · Low-FODMAP · Hypertension\nActively managing diet; seeking tools that match their clinical guidance"),
    ("Ring 3\nBudget-First", "Families squeezed by inflation\nPrimary value prop is savings; health constraints are secondary but present"),
    ("Ring 4\nMainstream", "General households\nConvenience + savings; the mass market WhollyFare reaches via advocacy and word of mouth"),
]
for col, (label, desc) in zip(ring_cols, rings):
    with col:
        st.markdown(
            f"""<div class="halo-ring">
              <div class="ring-label">{label}</div>
              <div class="ring-desc">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()


# ── BUSINESS MODEL / TIERS ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Business Model</div>', unsafe_allow_html=True)
st.markdown("### Four tiers. Freemium-to-premium. Built around the value the family actually receives.")

tier_data = [
    ("Tier 1 — Free",    "Multi-grocer shopping list & price comparison. The wedge. Establishes the habit and the trust.",           "Free",           "phase-1"),
    ("Tier 2 — Core",    "Full meal planning + Sunday Buy-Off one-click approval + Found Money tracking.",                           "$5–10 / month",  "phase-2"),
    ("Tier 3 — Health",  "Medical constraint engine (celiac, CKD, FODMAP, diabetes). The clinical safety layer.",                    "$15–25 / month", "phase-3"),
    ("Tier 4 — Complete","Recipe suggestions, pantry inventory, auto-reorder, family favorites memory.",                             "$25–40 / month", "phase-4"),
]

for title, desc, price, cls in tier_data:
    st.markdown(
        f"""<div class="phase-card {cls}">
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <div class="phase-title">{title}</div>
            <div style='font-weight:800;font-size:1.1rem;color:#1B2A4A'>{price}</div>
          </div>
          <div class="phase-sub">{desc}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()


# ── POC → NATIONAL ROADMAP ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Roadmap</div>', unsafe_allow_html=True)
st.markdown("### From Palmyra, VA to national scale: a four-phase build.")

st.markdown("""
The Proof of Concept (POC) is live and running on real Food Lion and Kroger data in
Central Virginia. The engine works. What investment unlocks is **data pipeline automation**,
**clinical validation partnerships**, and **national grocer integration**.
""")

roadmap = [
    ("Phase 1 — POC (Now)",
     "Local multi-grocer integration (Food Lion PDF + Kroger API). Constraint engine + meal planner. "
     "Streamlit dashboard. Pilot household validation. This is investable.",
     "phase-1"),
    ("Phase 2 — Beta (Months 4–9)",
     "Web app (React). Email/SMS delivery of weekly plans. 3–5 grocer API integrations. "
     "USDA nutrition enrichment at scale. 100–500 beta households in target zip codes.",
     "phase-2"),
    ("Phase 3 — Alpha Product (Months 10–18)",
     "Clinical dietitian partnerships for constraint validation. "
     "Loyalty/rewards program API integrations (Kroger Plus, Food Lion MVP). "
     "Coupon harvesting engine. First revenue from Tier 2/3.",
     "phase-3"),
    ("Phase 4 — National (Months 18–36)",
     "National grocer coverage via data partnerships. Recipe engine with pantry memory. "
     "B2B licensing to health systems, insurance, and employer wellness programs. "
     "Series A / strategic partnership targets.",
     "phase-4"),
]

for title, desc, cls in roadmap:
    st.markdown(
        f"""<div class="phase-card {cls}">
          <div class="phase-title">{title}</div>
          <div class="phase-sub">{desc}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()


# ── WHY NOW ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Why Now</div>', unsafe_allow_html=True)
st.markdown("### Three forces are converging. The window is open.")

col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    st.markdown("""
<div class="stat-card" style="border-left-color:#E65100;">
  <div style="font-size:1.5rem">📈</div>
  <div class="stat-number" style="font-size:1.1rem;margin-top:6px">Grocery inflation</div>
  <div class="stat-label">
    U.S. grocery prices rose 25%+ between 2020–2024. Families are actively
    looking for tools to take control of their food spend. The demand signal is unprecedented.
  </div>
</div>
    """, unsafe_allow_html=True)
with col_w2:
    st.markdown("""
<div class="stat-card" style="border-left-color:#6A1B9A;">
  <div style="font-size:1.5rem">🔗</div>
  <div class="stat-number" style="font-size:1.1rem;margin-top:6px">Grocer APIs are opening</div>
  <div class="stat-label">
    Kroger launched its Developer API in 2019 and continues to expand it.
    Other major chains are following. The data pipeline that today requires manual PDF
    upload will be automated API calls within 24 months.
  </div>
</div>
    """, unsafe_allow_html=True)
with col_w3:
    st.markdown("""
<div class="stat-card" style="border-left-color:#1565C0;">
  <div style="font-size:1.5rem">🤖</div>
  <div class="stat-number" style="font-size:1.1rem;margin-top:6px">AI makes it tractable</div>
  <div class="stat-label">
    LLM-assisted PDF parsing, constraint reasoning, and recipe generation have crossed
    the threshold of production reliability. The technical foundations of WhollyFare
    are now buildable by a small team.
  </div>
</div>
    """, unsafe_allow_html=True)

st.divider()


# ── TEAM ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">The Team</div>', unsafe_allow_html=True)
st.markdown("### Sentir Solutions LLC — founded by operators, not academics.")

st.markdown("""
WhollyFare is a product of **Sentir Solutions LLC**, based in Palmyra, Virginia.
The founding team combines operational experience in enterprise systems, data architecture,
and process automation with a genuine household-level frustration with the problem we're solving.

The pilot household — the Hislop family — is WhollyFare's first user.
The constraint engine was built around real dietary requirements, real local grocers,
and a real $120/week grocery budget. **We eat the cooking.**

We are building WhollyFare for the family that doesn't have a personal chef, a $500/month
meal-kit budget, or three hours on Sunday to figure out dinner — but does have a Kroger and
a Food Lion within ten minutes of home.
""")

st.divider()


# ── THE ASK ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ask-box">
  <h2>The Investment Opportunity</h2>
  <div class="ask-amount">Seed Round</div>
  <div class="ask-desc">
    We are raising a seed round to fund 18 months of focused product development:
    grocer API integrations, clinical dietitian partnerships, a production web application,
    and the first 500 paid households. The POC is live. The engine is proven.
    What investment buys is the data pipeline, the clinical validation layer,
    and the engineering capacity to move from Palmyra to national.<br><br>
    <b>If you're an investor who believes American families deserve a meal planner
    that works for them — not for its advertisers — we'd like to talk.</b>
  </div>
  <div style="margin-top:24px;opacity:0.7;font-size:0.85rem">
    Contact: Sentir Solutions LLC · Palmyra, VA · tim.hislop@gmail.com
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Footer disclaimer ─────────────────────────────────────────────────────────
st.caption(
    "This page is a Proof of Concept demonstration built in Streamlit. "
    "Financial projections and market statistics are estimates for illustrative purposes. "
    "WhollyFare is a product of Sentir Solutions LLC. All rights reserved."
)
