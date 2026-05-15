"""7_Investor.py — WhollyFare® Investor Brief"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.style as style
import ui.state as state

st.set_page_config(page_title="Investor Brief · WhollyFare", page_icon="📈", layout="wide")
state.init()
with st.sidebar:
    style.sidebar_nav()
style.inject()

# ── Investor-page CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ── */
.inv-dark-hero {
    background: linear-gradient(160deg, #0A0F0D 0%, #0F1F14 60%, #0A0F0D 100%);
    border-radius: 16px;
    padding: 64px 52px 56px 52px;
    color: white;
    margin-bottom: 36px;
    position: relative;
    overflow: hidden;
}
.inv-dark-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(58,140,78,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.inv-dark-hero .hero-eyebrow {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5DAA6A;
    margin-bottom: 18px;
}
.inv-dark-hero h1 {
    font-size: 4rem;
    font-weight: 800;
    margin: 0 0 14px 0;
    color: #ffffff;
    line-height: 1.05;
    letter-spacing: -0.02em;
}
.inv-dark-hero .tagline {
    font-size: 1.2rem;
    opacity: 0.78;
    max-width: 600px;
    line-height: 1.65;
    font-weight: 400;
}
.inv-hero-stats {
    display: flex;
    gap: 20px;
    margin-top: 44px;
    flex-wrap: wrap;
}
.inv-hero-stat-tile {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(93,170,106,0.25);
    border-radius: 12px;
    padding: 22px 28px;
    min-width: 150px;
    flex: 1;
}
.inv-hero-stat-tile .stat-big {
    font-size: 2rem;
    font-weight: 800;
    color: #F28B30;
    line-height: 1.1;
}
.inv-hero-stat-tile .stat-small {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.55);
    margin-top: 5px;
    line-height: 1.4;
}

/* ── Section labels ── */
.inv-section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3A8C4E;
    margin-bottom: 6px;
    margin-top: 0;
}

/* ── Stat cards (light sections) ── */
.inv-stat {
    background: #ffffff;
    border-radius: 10px;
    padding: 24px 20px;
    border: 1px solid #e8e8e8;
    border-left: 5px solid #3A8C4E;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    height: 100%;
    margin-bottom: 14px;
}
.inv-stat .stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    color: #0A0F0D;
    line-height: 1.1;
}
.inv-stat .stat-label {
    font-size: 0.82rem;
    color: #555;
    margin-top: 5px;
    line-height: 1.45;
}
.inv-stat .stat-source {
    font-size: 0.70rem;
    color: #999;
    margin-top: 8px;
}

/* ── Generic white card ── */
.inv-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 20px 18px;
    border: 1px solid #ebebeb;
    border-left: 4px solid #3A8C4E;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 12px;
}
.inv-card .card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0A0F0D;
    margin-bottom: 5px;
}
.inv-card .card-body {
    font-size: 0.83rem;
    color: #444;
    line-height: 1.55;
}

/* ── Dark band sections ── */
.inv-dark-band {
    background: linear-gradient(160deg, #0A0F0D 0%, #0F1F14 100%);
    border-radius: 14px;
    padding: 48px 44px;
    color: white;
    margin: 8px 0 8px 0;
}
.inv-dark-band h2 {
    color: #ffffff;
    font-size: 1.9rem;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.01em;
}
.inv-dark-band .band-sub {
    color: rgba(255,255,255,0.65);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 32px;
}
.inv-dark-band .band-section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5DAA6A;
    margin-bottom: 8px;
}

/* ── Dark band phase cards ── */
.dark-phase-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(93,170,106,0.2);
    border-left: 4px solid #3A8C4E;
    border-radius: 10px;
    padding: 20px 18px;
    margin-bottom: 12px;
    color: white;
}
.dark-phase-card .dp-title {
    font-size: 1rem;
    font-weight: 700;
    color: #5DAA6A;
    margin-bottom: 6px;
}
.dark-phase-card .dp-timing {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.dark-phase-card .dp-body {
    font-size: 0.83rem;
    color: rgba(255,255,255,0.72);
    line-height: 1.55;
}

/* ── Competitor table ── */
.comp-col {
    background: #1a1a1a;
    border-radius: 10px;
    padding: 18px 14px;
    height: 100%;
    border: 1px solid #2a2a2a;
}
.comp-col-wf {
    background: linear-gradient(160deg, #0F2518 0%, #1A3D22 100%);
    border-radius: 10px;
    padding: 18px 14px;
    height: 100%;
    border: 2px solid #3A8C4E;
}
.comp-col .comp-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #cccccc;
    margin-bottom: 6px;
}
.comp-col-wf .comp-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #5DAA6A;
    margin-bottom: 6px;
}
.comp-col .comp-price {
    font-size: 1.4rem;
    font-weight: 800;
    color: #e05c5c;
    margin-bottom: 6px;
    line-height: 1.1;
}
.comp-col-wf .comp-price {
    font-size: 1.4rem;
    font-weight: 800;
    color: #F28B30;
    margin-bottom: 6px;
    line-height: 1.1;
}
.comp-col .comp-desc {
    font-size: 0.78rem;
    color: #888;
    line-height: 1.45;
}
.comp-col-wf .comp-desc {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7);
    line-height: 1.45;
}
.comp-badge {
    display: inline-block;
    background: rgba(224,92,92,0.18);
    color: #e05c5c;
    border: 1px solid rgba(224,92,92,0.35);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.68rem;
    font-weight: 600;
    margin-top: 8px;
    letter-spacing: 0.04em;
}
.comp-badge-wf {
    display: inline-block;
    background: rgba(93,170,106,0.2);
    color: #5DAA6A;
    border: 1px solid rgba(93,170,106,0.4);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.68rem;
    font-weight: 600;
    margin-top: 8px;
    letter-spacing: 0.04em;
}

/* ── Tier rows ── */
.inv-tier-row {
    background: #ffffff;
    border-radius: 10px;
    padding: 20px 22px;
    border: 1px solid #e8e8e8;
    border-left: 5px solid #3A8C4E;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
}
.inv-tier-name {
    font-size: 1rem;
    font-weight: 700;
    color: #0A0F0D;
    min-width: 160px;
}
.inv-tier-price {
    font-size: 1.4rem;
    font-weight: 800;
    color: #3A8C4E;
    min-width: 120px;
}
.inv-tier-desc {
    font-size: 0.83rem;
    color: #555;
    line-height: 1.5;
    flex: 1;
}

/* ── Halo rings ── */
.halo-card-1 { background: #0F2518; border: 1px solid #3A8C4E; border-radius: 10px; padding: 20px 16px; }
.halo-card-2 { background: #163320; border: 1px solid #4A9E5C; border-radius: 10px; padding: 20px 16px; }
.halo-card-3 { background: #1E4228; border: 1px solid #5DAA6A; border-radius: 10px; padding: 20px 16px; }
.halo-card-4 { background: #274F30; border: 1px solid #7ABF87; border-radius: 10px; padding: 20px 16px; }
.halo-card-1 .halo-ring-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #5DAA6A; margin-bottom: 4px; }
.halo-card-2 .halo-ring-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #6DC47B; margin-bottom: 4px; }
.halo-card-3 .halo-ring-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #84CE90; margin-bottom: 4px; }
.halo-card-4 .halo-ring-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #9ED9A9; margin-bottom: 4px; }
.halo-ring-title { font-size: 1rem; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
.halo-ring-desc  { font-size: 0.80rem; color: rgba(255,255,255,0.65); line-height: 1.5; }

/* ── Ask hero ── */
.inv-ask-hero {
    background: linear-gradient(160deg, #060B08 0%, #0D1F11 60%, #060B08 100%);
    border-radius: 16px;
    padding: 64px 52px;
    text-align: center;
    color: white;
    margin-top: 8px;
    position: relative;
    overflow: hidden;
}
.inv-ask-hero::before {
    content: '';
    position: absolute;
    bottom: -80px; left: 50%;
    transform: translateX(-50%);
    width: 500px; height: 300px;
    background: radial-gradient(ellipse, rgba(58,140,78,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.inv-ask-hero .ask-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5DAA6A;
    margin-bottom: 20px;
}
.inv-ask-hero h2 {
    font-size: 2.6rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 12px;
    letter-spacing: -0.02em;
}
.inv-ask-hero .ask-amount {
    font-size: 3.2rem;
    font-weight: 900;
    color: #F28B30;
    margin: 8px 0 24px 0;
    letter-spacing: -0.02em;
}
.inv-ask-hero .ask-desc {
    font-size: 1rem;
    opacity: 0.78;
    max-width: 580px;
    margin: 0 auto 28px auto;
    line-height: 1.7;
}
.inv-ask-hero .ask-contact {
    font-size: 0.85rem;
    opacity: 0.55;
    letter-spacing: 0.03em;
    margin-top: 20px;
}
.inv-ask-hero a {
    color: #5DAA6A;
}

/* ── Solution step cards ── */
.step-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 22px 18px;
    border: 1px solid #e8e8e8;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    height: 100%;
}
.step-card .step-icon {
    font-size: 1.8rem;
    margin-bottom: 10px;
}
.step-card .step-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0A0F0D;
    margin-bottom: 7px;
}
.step-card .step-body {
    font-size: 0.83rem;
    color: #555;
    line-height: 1.55;
}
.step-card-1 { border-left: 5px solid #3A8C4E; }
.step-card-2 { border-left: 5px solid #5DAA6A; }
.step-card-3 { border-left: 5px solid #7ABF87; }

/* ── Sincere strategy cards ── */
.sincere-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid #e8e8e8;
    border-left: 4px solid #3A8C4E;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 12px;
}
.sincere-card .sc-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0A0F0D;
    margin-bottom: 5px;
}
.sincere-card .sc-body {
    font-size: 0.82rem;
    color: #444;
    line-height: 1.55;
}

/* ── Moat callout ── */
.moat-callout {
    background: #F0F9F2;
    border: 1px solid #A8D5B0;
    border-radius: 10px;
    padding: 18px 22px;
    margin-top: 20px;
    font-size: 0.9rem;
    color: #1E4228;
    font-weight: 600;
    line-height: 1.55;
}

/* ── Why Now cards ── */
.why-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 22px 18px;
    border: 1px solid #ebebeb;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    height: 100%;
    border-top: 4px solid #3A8C4E;
}
.why-card .why-icon { font-size: 1.6rem; margin-bottom: 10px; }
.why-card .why-title { font-size: 0.95rem; font-weight: 700; color: #0A0F0D; margin-bottom: 7px; }
.why-card .why-body  { font-size: 0.82rem; color: #555; line-height: 1.55; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 1. HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="inv-dark-hero">
  <div class="hero-eyebrow">Investor Brief &nbsp;·&nbsp; Sentir Solutions&#174; LLC &nbsp;·&nbsp; Palmyra, VA</div>
  <h1>WhollyFare&#174;</h1>
  <div class="tagline">The meal plan that pays you back.</div>
  <div class="inv-hero-stats">
    <div class="inv-hero-stat-tile">
      <div class="stat-big">15–25%</div>
      <div class="stat-small">avg household savings<br>vs. single-store shopping</div>
    </div>
    <div class="inv-hero-stat-tile">
      <div class="stat-big">~$2–4</div>
      <div class="stat-small">cost per serving<br>vs. $9.99 HelloFresh</div>
    </div>
    <div class="inv-hero-stat-tile">
      <div class="stat-big">$0</div>
      <div class="stat-small">paid placements<br>ever, by design</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_cta1, col_cta2, col_spacer = st.columns([1, 1, 4])
with col_cta1:
    if st.button("🌿 Try the app", use_container_width=True):
        st.switch_page("Home.py")
with col_cta2:
    st.markdown(
        '<a href="mailto:tim.hislop@gmail.com" style="display:block;text-align:center;'
        'padding:8px 0;border:1px solid #3A8C4E;border-radius:8px;color:#3A8C4E;'
        'font-size:0.9rem;font-weight:600;text-decoration:none;">📧 Get in touch</a>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 2. THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">The Problem</div>', unsafe_allow_html=True)
st.markdown("### American families are losing the grocery game.")

col_p1, col_p2 = st.columns([6, 4])
with col_p1:
    st.markdown("""
The average U.S. household spends **$5,703 per year** on groceries *(BLS Consumer Expenditure Survey, 2023)*
and leaves an estimated **15–25% on the table** through brand loyalty, single-store shopping,
and missed weekly sales. That's up to **$1,400/year** quietly evaporating from a family's budget.

The tools that exist today don't actually solve this:

- **Meal-kit services** (HelloFresh, Blue Apron) charge a **$9.99/serving premium** — they cost *more* than the grocery store, not less.
- **Grocery apps** (Flipp, Ibotta) surface coupons but have zero integration with meal planning — families still have to figure out what to *cook*.
- **Instacart / DoorDash** optimize for convenience at a margin premium; savings are never the goal.
- **Nutrition apps** give meal guidance but have no price awareness whatsoever.

**Nobody has connected the dots.** No platform currently optimizes the full loop:
sale prices → constraint-aware meal plan → shopping list → grocer checkout.
That is the gap WhollyFare&#174; was built to close.
    """)
with col_p2:
    st.markdown("""
<div class="inv-stat">
  <div class="stat-number">$5,703</div>
  <div class="stat-label">Average annual U.S. household grocery spend</div>
  <div class="stat-source">BLS Consumer Expenditure Survey, 2023</div>
</div>
<div class="inv-stat">
  <div class="stat-number">$1,400</div>
  <div class="stat-label">Estimated annual savings available through cross-store price optimization (15–25%)</div>
  <div class="stat-source">Internal WhollyFare analysis</div>
</div>
<div class="inv-stat">
  <div class="stat-number">$9.99</div>
  <div class="stat-label">HelloFresh cost per serving — the benchmark WhollyFare beats every week</div>
  <div class="stat-source">HelloFresh published pricing, 2024</div>
</div>
    """, unsafe_allow_html=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 3. THE SOLUTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">The Solution</div>', unsafe_allow_html=True)
st.markdown("### One engine. Three steps. Every Sunday.")

st.markdown("""
WhollyFare&#174; inverts the meal-kit model. Instead of charging a premium for pre-portioned ingredients,
we use each week's **actual sale circulars** from your local grocers to build the lowest-cost,
nutritionally sound, allergy-safe meal plan for your household — then hand you a single shopping list
organized by store and aisle.
""")

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown("""
<div class="step-card step-card-1">
  <div class="step-icon">🛒</div>
  <div class="step-title">1. Harvest</div>
  <div class="step-body">Pull weekly sale prices from grocery APIs and PDF circulars.
  Every item is tagged with category, allergens, and nutrition data via USDA FDC.</div>
</div>
    """, unsafe_allow_html=True)
with col_s2:
    st.markdown("""
<div class="step-card step-card-2">
  <div class="step-icon">🛡️</div>
  <div class="step-title">2. Filter</div>
  <div class="step-body">Run every item through the household's hard constraints —
  allergies, diagnoses (celiac, diabetes, CKD, IBS), lifestyle tags.
  Zero compromise. Every rejection is logged and shown to the user.</div>
</div>
    """, unsafe_allow_html=True)
with col_s3:
    st.markdown("""
<div class="step-card step-card-3">
  <div class="step-icon">🍽️</div>
  <div class="step-title">3. Plan</div>
  <div class="step-body">Score remaining ingredients by sale savings × nutrition density.
  Select 5–7 hero ingredients and rotate them through flavor profiles
  (Mexican, Asian, Mediterranean, Indian, American Comfort) for a full week of dinners.</div>
</div>
    """, unsafe_allow_html=True)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 4. COMPETITIVE LANDSCAPE (dark band)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="inv-dark-band">
  <div class="band-section-label">Competitive Landscape</div>
  <h2>A $25B industry working against the consumer.</h2>
  <div class="band-sub">
    The meal planning and grocery delivery space is large, fragmented, and almost entirely oriented
    around margins for the platform rather than savings for the family.
    WhollyFare&#174; occupies white space that none of the incumbents can easily enter
    without dismantling their own business model.
  </div>
</div>
""", unsafe_allow_html=True)

comp_cols = st.columns(5)
competitors = [
    {
        "name": "HelloFresh",
        "price": "$9.99/serving",
        "desc": "Convenient. Quality-branded. Expensive. No local-store integration. No constraint awareness.",
        "badge": "conflict of interest",
        "wf": False,
    },
    {
        "name": "Blue Apron",
        "price": "$10.99/serving",
        "desc": "Premium meal-kit. Chef-forward. Financially distressed. Same fundamental model as HelloFresh.",
        "badge": "conflict of interest",
        "wf": False,
    },
    {
        "name": "Flipp / Ibotta",
        "price": "Free (ad-supported)",
        "desc": "Coupon aggregators with ad-supported models. No meal planning. No constraint engine. Revenue from advertisers.",
        "badge": "conflict of interest",
        "wf": False,
    },
    {
        "name": "Instacart",
        "price": "$3.99+/order",
        "desc": "Delivery platform. Charges markup on groceries. No meal planning, no savings optimization.",
        "badge": "conflict of interest",
        "wf": False,
    },
    {
        "name": "WhollyFare®",
        "price": "~$2–4/serving",
        "desc": "Cross-grocer price optimization, hard health constraints, transparent logic, zero paid placements — ever.",
        "badge": "user-aligned",
        "wf": True,
    },
]

for col, comp in zip(comp_cols, competitors):
    with col:
        card_cls  = "comp-col-wf" if comp["wf"] else "comp-col"
        badge_cls = "comp-badge-wf" if comp["wf"] else "comp-badge"
        st.markdown(
            f"""<div class="{card_cls}">
              <div class="comp-name">{comp['name']}</div>
              <div class="comp-price">{comp['price']}</div>
              <div class="comp-desc">{comp['desc']}</div>
              <div class="{badge_cls}">{comp['badge']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 5. THE SINCERE STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">Our Moat</div>', unsafe_allow_html=True)
st.markdown("### Six commitments that are also a competitive moat.")

st.markdown("""
WhollyFare&#174; operates under a founding philosophy called the **Sincere Strategy&#174;** — a set of
commitments to the user that competitors cannot easily copy without fundamentally changing
their revenue model. Each commitment builds trust. Together, they create a durable moat.
""")

sincere_commitments = [
    ("🚫 No paid placements",
     "Recommendations are never influenced by brand partnerships or advertising. No grocer, brand, or CPG company can pay to appear in a plan. Ever."),
    ("🛡️ Sacrosanct health constraints",
     "If a household member has a peanut allergy, peanuts never appear — not in a plan, not in a suggestion, not in a 'you might also like.' Health constraints are the engine's highest-priority input."),
    ("🔍 Radical transparency",
     "Every ingredient rejection is logged and shown to the user. The constraint audit log is a first-class UI feature. No black boxes."),
    ("📍 Local-first",
     "Plans are built from your local grocers' actual weekly circulars, not national averages or partnered inventory. The savings are real and verifiable."),
    ("💰 Safety over savings",
     "WhollyFare will never recommend an unsafe ingredient because it's on sale. The constraint engine runs before the budget optimizer — always."),
    ("🔐 User data ownership",
     "Household health data is yours. WhollyFare does not sell, share, or use it for targeting. The pilot runs entirely on-device — zero cloud dependency."),
]

col_a, col_b = st.columns(2)
for i, (title, desc) in enumerate(sincere_commitments):
    target_col = col_a if i % 2 == 0 else col_b
    with target_col:
        st.markdown(
            f"""<div class="sincere-card">
              <div class="sc-title">{title}</div>
              <div class="sc-body">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("""
<div class="moat-callout">
  Competitors cannot copy the Sincere Strategy&#174; without dismantling their own revenue model.
  That asymmetry is the moat.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 6. HALO OF TRUST GO-TO-MARKET
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">Go-To-Market</div>', unsafe_allow_html=True)
st.markdown("### Start at the edge. Earn the mainstream.")

st.markdown("""
Our distribution strategy is deliberately counter-intuitive. We don't start with mass-market families —
we start with the households who need reliable, safe meal planning the *most* and will become
the most vocal advocates: **medical-edge users**.

Families managing celiac disease, MCAS, EDS, Type 1 diabetes, or CKD don't just want a meal planner —
they need one they can *trust absolutely.* When WhollyFare&#174; earns that trust, it radiates outward.
""")

ring_cols = st.columns(4)
rings = [
    ("Ring 1", "Medical Edge",
     "MCAS · Celiac · CKD · EDS · PKU",
     "Highest advocacy potential. Zero tolerance for error. Earns the deepest trust.",
     "halo-card-1"),
    ("Ring 2", "Health-Aware",
     "Diabetic · Low-FODMAP · Hypertension",
     "Actively managing diet. Seeking tools that match clinical guidance. Responsive to proven results.",
     "halo-card-2"),
    ("Ring 3", "Budget-First",
     "Inflation-squeezed families",
     "Primary value prop is savings. Health constraints present but secondary. Large addressable segment.",
     "halo-card-3"),
    ("Ring 4", "Mainstream",
     "General households",
     "Convenience + savings. The mass market WhollyFare reaches via advocacy and word of mouth.",
     "halo-card-4"),
]

for col, (ring_num, ring_title, tags, desc, css_class) in zip(ring_cols, rings):
    with col:
        st.markdown(
            f"""<div class="{css_class}">
              <div class="halo-ring-label">{ring_num}</div>
              <div class="halo-ring-title">{ring_title}</div>
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.45);margin-bottom:8px">{tags}</div>
              <div class="halo-ring-desc">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 7. BUSINESS MODEL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">Business Model</div>', unsafe_allow_html=True)
st.markdown("### Freemium to premium. Value drives the tier.")

tier_data = [
    ("Free",           "Free",           "The wedge. Multi-grocer shopping list & price comparison. Establishes the habit and the trust.",
     "Price comparison across Kroger + Food Lion · Weekly sale highlights · Basic shopping list"),
    ("Core",           "$7 / mo",        "Full meal planning + Sunday Buy-Off one-click approval + Found Money tracking.",
     "Full weekly meal plan · Found Money ledger · Sunday Buy-Off approval flow · Plan history"),
    ("Health",         "$19 / mo",       "Medical constraint engine: celiac, CKD, FODMAP, diabetes. The clinical safety layer.",
     "Everything in Core · Hard dietary constraint engine · Allergen audit log · Clinical-grade filtering"),
    ("Complete",       "$29 / mo",       "Recipe suggestions, pantry inventory, auto-reorder, family favorites memory.",
     "Everything in Health · Recipe engine · Pantry tracker · Flavor profile memory · Auto-reorder"),
]

for tier_name, tier_price, tier_desc, tier_features in tier_data:
    st.markdown(
        f"""<div class="inv-tier-row">
          <div class="inv-tier-name">{tier_name}</div>
          <div class="inv-tier-price">{tier_price}</div>
          <div class="inv-tier-desc"><strong>{tier_desc}</strong><br>
            <span style="font-size:0.78rem;color:#888">{tier_features}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 8. ROADMAP (dark band)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="inv-dark-band">
  <div class="band-section-label">Roadmap</div>
  <h2>From Palmyra, VA to national scale.</h2>
  <div class="band-sub">
    The Proof of Concept is live and running on real Food Lion and Kroger data in Central Virginia.
    The engine works. What investment unlocks is data pipeline automation,
    clinical validation partnerships, and national grocer integration.
  </div>
</div>
""", unsafe_allow_html=True)

roadmap = [
    ("Phase 1", "POC — Now",
     "Local multi-grocer integration (Food Lion PDF + Kroger API). Constraint engine + meal planner. "
     "Streamlit dashboard. Pilot household validation (Palmyra, VA). This is investable."),
    ("Phase 2", "Beta — Months 4–9",
     "Web app (React). Email/SMS delivery of weekly plans. 3–5 grocer API integrations. "
     "USDA nutrition enrichment at scale. 100–500 beta households in target zip codes."),
    ("Phase 3", "Alpha Product — Months 10–18",
     "Clinical dietitian partnerships for constraint validation. "
     "Loyalty/rewards API integrations (Kroger Plus, Food Lion MVP). "
     "Coupon harvesting engine. First revenue from Tier 2/3."),
    ("Phase 4", "National — Months 18–36",
     "National grocer coverage via data partnerships. Recipe engine with pantry memory. "
     "B2B licensing to health systems, insurance, and employer wellness programs. "
     "Series A / strategic partnership targets."),
]

for phase_num, phase_timing, phase_desc in roadmap:
    st.markdown(
        f"""<div class="dark-phase-card">
          <div class="dp-timing">{phase_num} &nbsp;·&nbsp; {phase_timing}</div>
          <div class="dp-body">{phase_desc}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 9. WHY NOW
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">Why Now</div>', unsafe_allow_html=True)
st.markdown("### Three forces converging. The window is open.")

col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    st.markdown("""
<div class="why-card">
  <div class="why-icon">📈</div>
  <div class="why-title">Grocery inflation</div>
  <div class="why-body">
    U.S. grocery prices rose 25%+ between 2020–2024. Families are actively
    looking for tools to take control of their food spend. The demand signal is unprecedented
    and still climbing.
  </div>
</div>
    """, unsafe_allow_html=True)
with col_w2:
    st.markdown("""
<div class="why-card">
  <div class="why-icon">🔗</div>
  <div class="why-title">Grocer APIs are opening</div>
  <div class="why-body">
    Kroger launched its Developer API in 2019 and continues to expand it.
    Other major chains are following. The data pipeline that today requires manual PDF
    upload will be automated API calls within 24 months.
  </div>
</div>
    """, unsafe_allow_html=True)
with col_w3:
    st.markdown("""
<div class="why-card">
  <div class="why-icon">🤖</div>
  <div class="why-title">AI makes it tractable</div>
  <div class="why-body">
    LLM-assisted PDF parsing, constraint reasoning, and recipe generation have crossed
    the threshold of production reliability. The technical foundations of WhollyFare&#174;
    are now buildable by a small team.
  </div>
</div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 10. THE TEAM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="inv-section-label">The Team</div>', unsafe_allow_html=True)
st.markdown("### Sentir Solutions&#174; — operators, not academics.", unsafe_allow_html=True)

st.markdown("""
WhollyFare&#174; is a product of **Sentir Solutions&#174; LLC**, based in Palmyra, Virginia.
The founding team combines operational experience in enterprise systems, data architecture,
and process automation with a genuine household-level frustration with the problem we're solving.

The pilot household — the Hislop family — is WhollyFare's first user.
The constraint engine was built around real dietary requirements, real local grocers
(Food Lion and Kroger, Central Virginia), and a real weekly grocery budget.
**We eat the cooking.**

We are building WhollyFare&#174; for the family that doesn't have a personal chef, a $500/month
meal-kit budget, or three hours on Sunday to figure out dinner — but does have a Kroger and
a Food Lion within ten minutes of home.
""")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 11. THE ASK (dark hero, full-width)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="inv-ask-hero">
  <div class="ask-eyebrow">Investment Opportunity</div>
  <h2>Seed Round</h2>
  <div class="ask-desc">
    We are raising a seed round to fund 18 months of focused product development:
    grocer API integrations, clinical dietitian partnerships, a production web application,
    and the first 500 paid households. The POC is live. The engine is proven.
    What investment buys is the data pipeline, the clinical validation layer,
    and the engineering capacity to move from Palmyra to national.<br><br>
    <strong>If you're an investor who believes American families deserve a meal planner
    that works for them — not for its advertisers — we'd like to talk.</strong>
  </div>
  <div>
    <a href="mailto:tim.hislop@gmail.com" style="display:inline-block;background:#3A8C4E;
    color:white;font-weight:700;font-size:0.95rem;padding:14px 36px;border-radius:8px;
    text-decoration:none;margin-top:8px;">📧 tim.hislop@gmail.com</a>
  </div>
  <div class="ask-contact">
    Sentir Solutions&#174; LLC &nbsp;·&nbsp; Palmyra, VA
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Footer disclaimer ─────────────────────────────────────────────────────────
st.caption(
    "This page is a Proof of Concept demonstration built in Streamlit. "
    "Financial projections and market statistics are estimates for illustrative purposes only. "
    "WhollyFare® is a product of Sentir Solutions® LLC. All rights reserved."
)
