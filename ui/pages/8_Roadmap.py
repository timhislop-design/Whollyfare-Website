"""
8_Roadmap.py — WhollyFare Product Roadmap
==========================================
This page lives inside the app and serves a dual purpose:
  1. For Tim — a working spec of what we're building and in what order
  2. For investors — a product vision that shows what $7-10M actually builds

Design principle: the roadmap is the argument. Every feature listed here
exists because a real household need drove it — not because it sounded good
in a pitch. That's the WhollyFare difference, and it should be visible here.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Product Roadmap · WhollyFare", page_icon="🗺️", layout="wide")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Product Roadmap",
    "Where WhollyFare is going — and why each step is earned, not assumed.",
)

# ── Roadmap CSS ───────────────────────────────────────────────────────────────
st.html("""
<style>
.phase-hero {
    border-radius: 14px;
    padding: 28px 28px 24px;
    margin-bottom: 6px;
    position: relative;
    overflow: hidden;
}
.phase-live      { background: linear-gradient(135deg, #142B1C, #1E5C32); }
.phase-beta      { background: linear-gradient(135deg, #1A2E40, #1E4060); }
.phase-growth    { background: linear-gradient(135deg, #2D1A40, #4A2060); }
.phase-scale     { background: linear-gradient(135deg, #1A1200, #3D2C00); }
.phase-wholesale { background: linear-gradient(135deg, #071F1F, #0A3A3A); }

.phase-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.phase-title {
    font-size: 1.55rem;
    font-weight: 800;
    color: white;
    margin-bottom: 8px;
    line-height: 1.1;
    letter-spacing: -0.01em;
}
.phase-subtitle {
    font-size: 0.88rem;
    color: rgba(255,255,255,0.65);
    line-height: 1.55;
    max-width: 520px;
}
.phase-timing {
    display: inline-block;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    font-weight: 600;
    color: rgba(255,255,255,0.8);
    margin-bottom: 14px;
    letter-spacing: 0.04em;
}
.feature-card {
    background: white;
    border-radius: 10px;
    padding: 16px 18px;
    border: 1px solid #E8EEE8;
    box-shadow: 0 1px 8px rgba(30,92,50,0.06);
    margin-bottom: 10px;
}
.feature-card.built   { border-left: 4px solid #3A8C4E; }
.feature-card.beta    { border-left: 4px solid #3A6EA8; }
.feature-card.growth  { border-left: 4px solid #7B3F9E; }
.feature-card.scale   { border-left: 4px solid #B8860B; }
.feature-card.horizon { border-left: 4px solid #0A9090; }

.feature-icon  { font-size: 1.5rem; margin-bottom: 8px; }
.feature-title { font-size: 0.95rem; font-weight: 700; color: #1A2E1D; margin-bottom: 5px; }
.feature-body  { font-size: 0.81rem; color: #5A6B5E; line-height: 1.55; }
.feature-why   { font-size: 0.76rem; color: #3A8C4E; font-weight: 600; margin-top: 8px; }

.status-pill-built   { background:#E3F4E8; color:#1E5C32;  border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
.status-pill-next    { background:#EBF2FB; color:#1A4A7A;  border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
.status-pill-future  { background:#F3EDFB; color:#5A1A8A;  border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
.status-pill-horizon { background:#D6F0EF; color:#0A5C5C;  border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
</style>
""")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE INTRO — the honest frame
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div style='background:white;border:1px solid #D8EDD0;border-left:4px solid #3A8C4E;
            border-radius:8px;padding:18px 22px;margin-bottom:28px;'>
  <div style='font-weight:700;color:#1E5C32;font-size:1rem;margin-bottom:6px;'>
    The roadmap is earned, not assumed.
  </div>
  <div style='font-size:0.86rem;color:#5A7A62;line-height:1.65;'>
    Every feature on this page was driven by a real household need — not market research,
    not a competitor's feature list. The pilot households (Phase 1) tell us what Phase 2
    builds. The beta households (Phase 2) tell us what the growth product (Phase 3) looks like.
    That's the WhollyFare approach: build for the family in front of you, then build for everyone.
  </div>
</div>
""")


# ══════════════════════════════════════════════════════════════════════════════
# THE WEEKLY RITUAL — what a household actually does
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div style='background:#F0F7F2;border:1px solid #B0D4B8;border-radius:12px;
            padding:22px 24px 18px 24px;margin-bottom:24px;'>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:10px;'>The weekly ritual · 7 steps · under 10 minutes</div>
  <div style='font-size:1.1rem;font-weight:800;color:#1A2E1D;margin-bottom:16px;'>
    From sale prices to dinner on the table — without guesswork, without overpaying.
  </div>
  <div style='display:grid;grid-template-columns:repeat(7,1fr);gap:8px;'>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>🔐</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Log in</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Household profile &amp; dietary rules load automatically</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>🏪</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Load prices</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>This week&apos;s sale circulars from your stores</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>🍽️</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Set preferences</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Cuisine mix, proteins, dinners, nights out</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>⚙️</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Engine runs</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Safety filter → budget optimizer → meal plan</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>✅</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Approve</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Sunday Buy-Off — confirm, swap, or skip any meal</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>🛒</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Shop</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Shopping list by store · Instacart/Shipt in Phase 3</div>
    </div>
    <div style='text-align:center;'>
      <div style='font-size:1.4rem;'>💰</div>
      <div style='font-size:0.68rem;font-weight:700;color:#1A2E1D;margin-top:4px;'>Ledger</div>
      <div style='font-size:0.63rem;color:#5A7A62;margin-top:2px;'>Actual receipt vs. plan · Found Money confirmed</div>
    </div>
  </div>
  <div style='margin-top:14px;padding-top:12px;border-top:1px solid #C8E0CC;
              font-size:0.78rem;color:#3A8C4E;font-weight:600;'>
    Phase 1: steps 1–5 are manual (circulars loaded by Tim, plans approved weekly).
    Phase 2: multi-household accounts, step 6 mobile-native.
    Phase 3: steps 2 &amp; 6 fully automated — circulars pulled by API, cart sent to Instacart/Shipt.
  </div>
</div>
""")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — POC / PILOT (NOW)
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='phase-hero phase-live'>
  <div class='phase-label' style='color:#9FD9A8;'>Phase 1</div>
  <div class='phase-timing'>Now — Charlottesville Pilot · Hislop Family + Friends</div>
  <div class='phase-title'>Prove the engine. Record the savings.</div>
  <div class='phase-subtitle'>
    One household. Four local stores. Manual flyer entry. Eight weeks of real receipts.
    The goal is not a polished product — it's undeniable data.
  </div>
</div>
""")

st.html("<div style='height:10px;'></div>")

p1c1, p1c2, p1c3, p1c4 = st.columns(4)

with p1c1:
    st.html("""
    <div class='feature-card built'>
      <div class='feature-icon'>🛡️</div>
      <div class='feature-title'>Safety-First Engine <span class='status-pill-built'>Built</span></div>
      <div class='feature-body'>Constraint engine → budget optimizer → meal planner, running
      in sequence every week. Hard-rule filtering for Top-14 allergens, celiac, CKD, diabetes,
      MCAS, IBS. Safety absolute — never traded for savings. Every rejection logged.</div>
      <div class='feature-why'>Why: One peanut allergy in one household means every
      recommendation must be bulletproof. Trust is built before anything else.</div>
    </div>
    """)

with p1c2:
    st.html("""
    <div class='feature-card built'>
      <div class='feature-icon'>🍽️</div>
      <div class='feature-title'>Weekly Preferences Wizard <span class='status-pill-built'>Built</span></div>
      <div class='feature-body'>4-step weekly wizard: schedule (dinners + nights out),
      cuisine mix (multi-select with smart recommendation), protein preferences (Chicken,
      Beef, Pork, Seafood, Turkey + others), and notes. Saves to profile with flyer-week
      expiration — resets automatically when new sale prices load.</div>
      <div class='feature-why'>Why: "What do you want this week?" is the right question
      before "here is your plan." Preferences make every week feel different.</div>
    </div>
    """)

with p1c3:
    st.html("""
    <div class='feature-card built'>
      <div class='feature-icon'>🏪</div>
      <div class='feature-title'>Multi-Tier Grocer Hub <span class='status-pill-built'>Built</span></div>
      <div class='feature-body'>Four store tiers — Value, Full-Service, Specialty, Local — with
      zip-aware filtering and trip-cost math. Kroger live via API (239 items). Manual circular
      entry + PDF parsing for Food Lion, Harris Teeter, Aldi.
      Admin refresh model: Tim loads once, all pilot households benefit.</div>
      <div class='feature-why'>Why: Manual entry is 100% reliable for the pilot.
      Admin-shared circulars is the Phase 2 bridge to full automation.</div>
    </div>
    """)

with p1c4:
    st.html("""
    <div class='feature-card built'>
      <div class='feature-icon'>💰</div>
      <div class='feature-title'>Savings Dashboard <span class='status-pill-built'>Built</span></div>
      <div class='feature-body'>Per-serving cost hero ($2–4 target vs. $5.99–$12.99 meal kits),
      cross-store Found Money, and expandable per-service comparison — EveryPlate, HelloFresh,
      Blue Apron, Green Chef and more. Found Money Ledger tracks actual receipts vs. plan
      week over week, net of gas costs.</div>
      <div class='feature-why'>Why: "$2.40/serving vs. $9.99 Blue Apron" on the same screen
      as your actual meal plan is the moment that drives cancellations.</div>
    </div>
    """)

st.html("<div style='height:24px;'></div>")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — BETA (POST-PILOT · 5–10 HOUSEHOLDS)
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='phase-hero phase-beta'>
  <div class='phase-label' style='color:#7EB3E8;'>Phase 2</div>
  <div class='phase-timing'>Beta · Months 2–5 · 5–10 Pilot Households · Charlottesville + friends</div>
  <div class='phase-title'>What families actually want. Learned from families.</div>
  <div class='phase-subtitle'>
    The pilot data tells us what to build next. These are the features driven by
    real household conversations — moms who quit HelloFresh, families managing food
    allergies, people who know they're leaving money on the table every week.
  </div>
</div>
""")

st.html("<div style='height:10px;'></div>")

# Row 1
p2r1c1, p2r1c2, p2r1c3 = st.columns(3)

with p2r1c1:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>🍽️</div>
      <div class='feature-title'>Meal Type Selection <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>Casual weeknight, date night, Sunday formal, quick 20-minute,
      slow cooker, kids eat too. The plan adapts to the kind of week your family is having —
      not just what's on sale.</div>
      <div class='feature-why'>Why: "What's for dinner?" is also "how much energy do I have
      tonight?" The plan needs to answer both.</div>
    </div>
    """)

with p2r1c2:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>🥫</div>
      <div class='feature-title'>Pantry Tracker <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>Tracks what you bought and how much the meal plan used.
      Shows what's still in the pantry. Skips planning around ingredients you already have.
      Reduces waste and cost simultaneously.</div>
      <div class='feature-why'>Why: Families already have half a pantry. Planning around it
      is the difference between a $95 week and a $60 week.</div>
    </div>
    """)

with p2r1c3:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>🏷️</div>
      <div class='feature-title'>Coupon Vault <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>Automatic coupon matching layered on top of the weekly plan.
      Digital coupons from store apps, manufacturer offers, and cashback apps all factored
      into the Found Money number. Every dollar counts.</div>
      <div class='feature-why'>Why: Coupons already exist — families just don't have time
      to match them. WhollyFare does it automatically, transparently, zero paid placements.</div>
    </div>
    """)

st.html("<div style='height:10px;'></div>")

# Row 2
p2r2c1, p2r2c2, p2r2c3 = st.columns(3)

with p2r2c1:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>👨‍👩‍👧</div>
      <div class='feature-title'>Multi-Household + Admin Data <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>Full user accounts with isolated household profiles, plan history,
      and Found Money ledgers. Admin shared-circular model: Tim (or any admin) loads the
      week's circulars once into a shared_flyers table — every household in the same market
      benefits automatically. Zip-native store matching: your zip finds your nearest
      Food Lion, not just the chain.</div>
      <div class='feature-why'>Why: One person doing Sunday updates serves ten households.
      That's the bridge from manual to automated — and it's already architectured in.</div>
    </div>
    """)

with p2r2c2:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>📱</div>
      <div class='feature-title'>Mobile-First UI <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>The shopping list is used in a grocery store on a phone.
      The Sunday Buy-Off is done on a couch on a Sunday morning. The Streamlit UI works
      on mobile but Phase 2 makes it feel native — the bar is usable in a Kroger aisle.</div>
      <div class='feature-why'>Why: If the shopping list isn't usable on a phone in
      a grocery aisle, the product hasn't shipped.</div>
    </div>
    """)

with p2r2c3:
    st.html("""
    <div class='feature-card beta'>
      <div class='feature-icon'>🩺</div>
      <div class='feature-title'>Health Guard Dashboard <span class='status-pill-next'>Phase 2</span></div>
      <div class='feature-body'>A household-facing view of every ingredient accepted or
      rejected each week — by constraint, by member, by date. Full audit trail of safety
      decisions. The compliance layer that health-system partners will eventually license.</div>
      <div class='feature-why'>Why: Families managing celiac or CKD need to see the
      engine's reasoning, not just its output. Trust requires transparency.</div>
    </div>
    """)

st.html("<div style='height:24px;'></div>")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — GROWTH (INVESTMENT ROUND · REGIONAL SCALE)
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='phase-hero phase-growth'>
  <div class='phase-label' style='color:#C09FE0;'>Phase 3</div>
  <div class='phase-timing'>Growth · Months 6–18 · Investment Round · Regional Scale</div>
  <div class='phase-title'>From pilot data to a product people pay for.</div>
  <div class='phase-subtitle'>
    This is what investment buys. Not the concept — the infrastructure to take a proven
    concept to 500 households across the Mid-Atlantic, with real revenue, real retention
    data, and the engineering foundation for national scale.
  </div>
</div>
""")

st.html("<div style='height:10px;'></div>")

# Row 1
p3r1c1, p3r1c2, p3r1c3, p3r1c4 = st.columns(4)

with p3r1c1:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>🤖</div>
      <div class='feature-title'>Automated Circular Parsing <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>No more manual uploads. Grocer circulars pulled automatically
      each week via API integrations — Kroger is live; others via data partnerships or improved
      PDF automation. The Sunday workflow becomes truly one tap.</div>
      <div class='feature-why'>Why: Manual upload is the POC's biggest friction point.
      Removing it is the difference between a product families use and one they try once.</div>
    </div>
    """)

with p3r1c2:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>📖</div>
      <div class='feature-title'>Recipe Library <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>Full step-by-step recipes built from hero ingredients the engine
      selects each week. Recipes adapt to your constraints automatically and grow with your
      household's history — meals you loved come back when the same ingredients go on sale.</div>
      <div class='feature-why'>Why: Retention. A family with 20 approved recipes in their
      WhollyFare library doesn't cancel their subscription.</div>
    </div>
    """)

with p3r1c3:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>📈</div>
      <div class='feature-title'>Price Intelligence <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>Price history across all stores and weeks, surfaced as trends.
      "Chicken thighs go on sale every 3 weeks at Food Lion." Alerts when a staple item
      drops to an all-time low. Stock-up recommendations based on real household consumption.</div>
      <div class='feature-why'>Why: The data moat. Every week of flyer data makes the
      price model smarter. Competitors can't buy this history.</div>
    </div>
    """)

with p3r1c4:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>🚚</div>
      <div class='feature-title'>Delivery Hub <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>Instacart, Shipt, and store pickup integrated into the shopping
      list. WhollyFare calculates whether delivery fees eat the Found Money or preserve it.
      Honest math — we'll tell you when pickup beats delivery and when staying home beats both.</div>
      <div class='feature-why'>Why: Busy households need delivery options without losing
      the savings. Radical transparency applies to delivery fees too.</div>
    </div>
    """)

st.html("<div style='height:10px;'></div>")

# Row 2
p3r2c1, p3r2c2, p3r2c3 = st.columns(3)

with p3r2c1:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>📊</div>
      <div class='feature-title'>Market Insights <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>Anonymised, aggregated price and savings data across all WhollyFare
      households — published as a public resource. Which stores are cheapest for which categories,
      by region, by week. The Sincere Strategy applied to market data: we share what we know.</div>
      <div class='feature-why'>Why: A public data product builds brand authority and
      drives organic growth. Zero cost to produce once the data exists.</div>
    </div>
    """)

with p3r2c2:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>🏥</div>
      <div class='feature-title'>Health System Partnerships <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>B2B licensing to health systems, insurance companies, and employer
      wellness programs. A hospital managing 10,000 patients with CKD or celiac has a direct
      interest in a tool that helps those patients eat safely at home.</div>
      <div class='feature-why'>Why: The medical edge is the highest-value market and the
      hardest one for competitors to enter honestly.</div>
    </div>
    """)

with p3r2c3:
    st.html("""
    <div class='feature-card growth'>
      <div class='feature-icon'>🌐</div>
      <div class='feature-title'>React + FastAPI Platform <span class='status-pill-future'>Phase 3</span></div>
      <div class='feature-body'>The Streamlit POC retires. A real web app — React frontend,
      FastAPI backend, PostgreSQL, background job queue — replaces it. Same product logic,
      same data model, built to handle 10,000 households without re-architecting.</div>
      <div class='feature-why'>Why: Streamlit is the right tool for a POC. It is not
      the right tool for a product with 500 households and a mobile app.</div>
    </div>
    """)

st.html("<div style='height:24px;'></div>")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — NATIONAL (SERIES A)
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='phase-hero phase-scale'>
  <div class='phase-label' style='color:#E8C060;'>Phase 4</div>
  <div class='phase-timing'>National · Months 18–36 · Series A · 50,000+ Households</div>
  <div class='phase-title'>The category-defining meal planning platform.</div>
  <div class='phase-subtitle'>
    15+ grocer chains. National coverage. The Sincere Strategy as a brand that carries
    the same weight as "no artificial ingredients" or "B Corp certified."
    The moat competitors spent 10 years building is the thing that prevents them
    from competing with us.
  </div>
</div>
""")

st.html("<div style='height:10px;'></div>")

p4c1, p4c2, p4c3, p4c4 = st.columns(4)

_national = [
    ("🌍", "National Grocer Coverage",
     "15+ chain integrations via API partnerships and data licensing. Kroger, Publix, "
     "Albertsons, H-E-B, Aldi, Meijer, Wegmans, Safeway — the stores American families "
     "actually shop."),
    ("🧠", "Preference Learning",
     "The plan gets smarter the longer you use it. Cuisine preferences, rejected meals, "
     "family favourites, and pantry patterns feed a personalised recommendation layer. "
     "WhollyFare in Year 2 is fundamentally better than WhollyFare on Day 1."),
    ("🧾", "Receipt Auto-Capture",
     "Point your phone at a receipt and WhollyFare reads it. OCR + ML matches items to "
     "the week's plan and updates the Found Money ledger automatically. "
     "No manual entry, ever."),
    ("🤝", "Community & Sharing",
     "Share approved meals and savings tips with other WhollyFare families. A community "
     "built around real cooking, real savings, and real food — not influencer content."),
]

for col, (icon, title, body) in zip([p4c1, p4c2, p4c3, p4c4], _national):
    with col:
        st.html(f"""
        <div class='feature-card scale'>
          <div class='feature-icon'>{icon}</div>
          <div class='feature-title'>{title} <span class='status-pill-future'>Phase 4</span></div>
          <div class='feature-body'>{body}</div>
        </div>
        """)

st.html("<div style='height:24px;'></div>")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — WHOLESALE & DELIVERY (HORIZON)
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='phase-hero phase-wholesale'>
  <div class='phase-label' style='color:#7FD4D4;'>Phase 5 · Horizon</div>
  <div class='phase-timing'>Wholesale &amp; Delivery · Post Series A · When national coverage is proven</div>
  <div class='phase-title'>The full grocery universe. Every format, every model.</div>
  <div class='phase-subtitle'>
    Warehouse clubs and online delivery are fundamentally different purchase models —
    bulk buying, membership economics, delivery logistics. Phase 5 brings them into the
    engine once national grocery coverage is solid enough to make the comparison honest.
    Not just cheaper per ounce — cheaper in your actual kitchen.
  </div>
</div>
""")

st.html("<div style='height:10px;'></div>")

p5c1, p5c2, p5c3, p5c4 = st.columns(4)

_wholesale = [
    ("🏭", "Warehouse Clubs",
     "Costco, Sam's Club, and BJ's Wholesale integrated into the price engine. "
     "Bulk pricing comparisons that account for realistic consumption: a 10-lb bag "
     "of chicken thighs is only a deal if your household uses 10 lbs before it spoils. "
     "Per-unit and per-serving math done honestly."),
    ("📦", "Amazon Fresh & Prime",
     "Online grocery delivery mapped against your weekly plan. Time value, delivery fees, "
     "and minimum order thresholds calculated alongside per-item prices. The honest "
     "answer is sometimes: the convenience isn't worth the markup. "
     "The Sincere Strategy means we'll say so."),
    ("🔄", "Bulk Buy Optimisation",
     "The engine learns which staples your household consumes consistently and flags when "
     "warehouse club pricing beats per-unit grocery pricing over a realistic 30-day "
     "window. Not an ounce-price comparison — a whole-pantry, whole-month savings model."),
    ("📊", "Hybrid Trip Planning",
     "One warehouse run per month plus weekly grocery shops, modelled as a system. "
     "WhollyFare plans both: what to stock up on at Costco and what to buy fresh "
     "each week. The full-year Found Money picture becomes the most compelling number "
     "in the product."),
]

for col, (icon, title, body) in zip([p5c1, p5c2, p5c3, p5c4], _wholesale):
    with col:
        st.html(f"""
        <div class='feature-card horizon'>
          <div class='feature-icon'>{icon}</div>
          <div class='feature-title'>{title} <span class='status-pill-horizon'>Horizon</span></div>
          <div class='feature-body'>{body}</div>
        </div>
        """)

st.html("<div style='height:28px;'></div>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# THE INVESTMENT ARGUMENT
# ══════════════════════════════════════════════════════════════════════════════
st.html(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:12px;'>Why this raises at 7–8 figures</div>")

ia1, ia2 = st.columns([3, 2])

with ia1:
    st.html("""
    <div style='font-size:1.3rem;font-weight:800;color:#1A2E1D;margin-bottom:14px;
                letter-spacing:-0.01em;line-height:1.2;'>
      The market is enormous. The gap is real.<br>The moat is structural.
    </div>
    <div style='font-size:0.88rem;color:#5A6B5E;line-height:1.7;'>
      American families spend <strong>$1.6 trillion on food annually</strong>.
      The grocery segment alone is $800B. Meal kits — a product that costs <em>more</em>
      than the grocery store and delivers less flexibility — are a $9B category.
      The fact that HelloFresh can charge $9.99/serving and still have customers is the
      market signal. Families will pay for help. They just don't want to be exploited doing it.<br><br>
      WhollyFare's moat is not technology — any well-funded team can build the technology.
      The moat is the <strong>Sincere Strategy</strong>: a commitment to zero paid placements,
      absolute health constraints, and radical transparency that competitors with existing
      advertiser and brand relationships <em>cannot adopt without destroying their own revenue.</em><br><br>
      That asymmetry is durable. It gets stronger as WhollyFare grows, because every week
      a family trusts WhollyFare with a celiac diagnosis or a peanut allergy is a week the
      relationship deepens. Trust, built over time, at the household level, around food safety,
      is not something you can acquire. It has to be earned.
    </div>
    """)

with ia2:
    for val, label in [
        ("$800B",  "U.S. grocery market"),
        ("$9B",    "Meal kit market WhollyFare disrupts"),
        ("$1,400", "Average annual savings per household"),
        ("96%",    "Gross margin at steady state"),
        ("$0",     "Paid placements. Ever."),
    ]:
        st.html(f"""
        <div style='background:white;border:1px solid #E8EEE8;border-left:4px solid #3A8C4E;
                    border-radius:8px;padding:14px 18px;margin-bottom:10px;'>
          <div style='font-size:1.8rem;font-weight:800;color:#1A2E1D;line-height:1;'>{val}</div>
          <div style='font-size:0.79rem;color:#5A7A62;margin-top:4px;'>{label}</div>
        </div>
        """)

st.html("<div style='height:20px;'></div>")

# ── Contact / CTA ─────────────────────────────────────────────────────────────
st.html("""
<div style='background:linear-gradient(160deg,#0A0F0D,#0F1F14);border-radius:14px;
            padding:36px 40px;text-align:center;'>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.14em;
              text-transform:uppercase;color:#5DAA6A;margin-bottom:12px;'>
    Ready to talk
  </div>
  <div style='font-size:1.6rem;font-weight:800;color:white;margin-bottom:8px;
              letter-spacing:-0.01em;'>
    WhollyFare is the future done right.
  </div>
  <div style='font-size:0.9rem;color:rgba(255,255,255,0.65);max-width:520px;margin:0 auto 28px;'>
    Built with honesty, constraint, and conviction.<br>
    Ready when you are.
  </div>
  <a href='mailto:tim.hislop@gmail.com?subject=WhollyFare conversation'
     style='display:inline-block;background:#3A8C4E;color:white;font-weight:700;
            font-size:0.95rem;padding:14px 32px;border-radius:8px;text-decoration:none;
            letter-spacing:0.01em;'>
    Start a conversation
  </a>
</div>
""")
