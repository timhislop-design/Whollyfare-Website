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
st.markdown("""
<style>
.phase-hero {
    border-radius: 14px;
    padding: 28px 28px 24px;
    margin-bottom: 6px;
    position: relative;
    overflow: hidden;
}
.phase-live   { background: linear-gradient(135deg, #142B1C, #1E5C32); }
.phase-beta   { background: linear-gradient(135deg, #1A2E40, #1E4060); }
.phase-growth { background: linear-gradient(135deg, #2D1A40, #4A2060); }
.phase-scale  { background: linear-gradient(135deg, #1A1200, #3D2C00); }

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
    height: 100%;
}
.feature-card.built {
    border-left: 4px solid #3A8C4E;
}
.feature-card.beta {
    border-left: 4px solid #3A6EA8;
}
.feature-card.growth {
    border-left: 4px solid #7B3F9E;
}
.feature-card.scale {
    border-left: 4px solid #B8860B;
}
.feature-icon { font-size: 1.5rem; margin-bottom: 8px; }
.feature-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1A2E1D;
    margin-bottom: 5px;
}
.feature-body {
    font-size: 0.81rem;
    color: #5A6B5E;
    line-height: 1.55;
}
.feature-why {
    font-size: 0.76rem;
    color: #3A8C4E;
    font-weight: 600;
    margin-top: 8px;
}
.status-pill-built  { background:#E3F4E8; color:#1E5C32; border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
.status-pill-next   { background:#EBF2FB; color:#1A4A7A; border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
.status-pill-future { background:#F3EDFB; color:#5A1A8A; border-radius:20px; padding:2px 10px; font-size:0.68rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE INTRO — the honest frame
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
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
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — POC / PILOT (NOW)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="phase-hero phase-live">', unsafe_allow_html=True)
st.markdown("""
<div class="phase-label" style="color:#9FD9A8;">Phase 1</div>
<div class="phase-timing">Now — Charlottesville Pilot · Hislop Family + Friends</div>
<div class="phase-title">Prove the engine. Record the savings.</div>
<div class="phase-subtitle">
  One household. Four local stores. Manual flyer entry. Eight weeks of real receipts.
  The goal is not a polished product — it's undeniable data.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

p1c1, p1c2, p1c3 = st.columns(3)

with p1c1:
    st.markdown("""
    <div class="feature-card built">
      <div class="feature-icon">🛡️</div>
      <div class="feature-title">Constraint Engine <span class="status-pill-built">Built</span></div>
      <div class="feature-body">Hard-rule filtering for Top-14 allergens, celiac, CKD, diabetes,
      MCAS, IBS, and more. Every rejection logged with reason + household member.
      Safety is absolute — never traded for savings.</div>
      <div class="feature-why">Why: One peanut allergy in one household means every recommendation
      must be bulletproof. Trust is built before anything else.</div>
    </div>
    """, unsafe_allow_html=True)

with p1c2:
    st.markdown("""
    <div class="feature-card built">
      <div class="feature-icon">🏪</div>
      <div class="feature-title">Manual Grocer Hub <span class="status-pill-built">Built</span></div>
      <div class="feature-body">Type items in directly from any store's weekly circular.
      PDF upload as a bonus path. Charlottesville store presets (Kroger, Food Lion, Aldi,
      Harris Teeter) load in one click.</div>
      <div class="feature-why">Why: PDF parsing is unreliable. Manual entry is 100% reliable.
      The pilot loop must work every Sunday without fail.</div>
    </div>
    """, unsafe_allow_html=True)

with p1c3:
    st.markdown("""
    <div class="feature-card built">
      <div class="feature-icon">💰</div>
      <div class="feature-title">Found Money Ledger <span class="status-pill-built">Built</span></div>
      <div class="feature-body">Logs both the WhollyFare plan estimate and your actual receipt total.
      Tracks accuracy week over week. Exports to CSV for investor conversations.
      The annualised savings projection builds automatically.</div>
      <div class="feature-why">Why: A savings claim backed by real receipts is evidence.
      One backed by estimates is marketing.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — BETA (POST-PILOT · 5–10 HOUSEHOLDS)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="phase-hero phase-beta">', unsafe_allow_html=True)
st.markdown("""
<div class="phase-label" style="color:#7EB3E8;">Phase 2</div>
<div class="phase-timing">Beta · Months 2–5 · 5–10 Pilot Households · Charlottesville + friends</div>
<div class="phase-title">What families actually want. Learned from families.</div>
<div class="phase-subtitle">
  The pilot data tells us what to build next. These are the features driven by
  household conversations — moms who quit HelloFresh, families managing food allergies,
  people who know they're leaving money on the table every week.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

p2c1, p2c2, p2c3, p2c4 = st.columns(4)

with p2c1:
    st.markdown("""
    <div class="feature-card beta">
      <div class="feature-icon">🍽️</div>
      <div class="feature-title">Meal Type Selection <span class="status-pill-next">Phase 2</span></div>
      <div class="feature-body">Casual weeknight, date night, Sunday formal, quick 20-minute,
      slow cooker, kids eat too. The plan adapts to the kind of week your family is having —
      not just what's on sale.</div>
      <div class="feature-why">Why: "What's for dinner?" is also "how much energy do I have
      tonight?" The plan needs to answer both.</div>
    </div>
    """, unsafe_allow_html=True)

with p2c2:
    st.markdown("""
    <div class="feature-card beta">
      <div class="feature-icon">🥫</div>
      <div class="feature-title">Pantry Tracker <span class="status-pill-next">Phase 2</span></div>
      <div class="feature-body">Automatically tracks what you bought and how much the meal plan
      used. Shows what's still in the pantry. Skips planning around ingredients you already have.
      Reduces waste and cost simultaneously.</div>
      <div class="feature-why">Why: Families already have half a pantry. Planning around it
      is the difference between a $95 week and a $60 week.</div>
    </div>
    """, unsafe_allow_html=True)

with p2c3:
    st.markdown("""
    <div class="feature-card beta">
      <div class="feature-icon">👨‍👩‍👧</div>
      <div class="feature-title">Multi-Household Support <span class="status-pill-next">Phase 2</span></div>
      <div class="feature-body">User accounts so pilot friends can set up their own household
      without Tim holding their hand. Each household has its own profile, plan history,
      and Found Money ledger. Data stays isolated and private.</div>
      <div class="feature-why">Why: The product can't scale if every new user requires
      a personal introduction.</div>
    </div>
    """, unsafe_allow_html=True)

with p2c4:
    st.markdown("""
    <div class="feature-card beta">
      <div class="feature-icon">📱</div>
      <div class="feature-title">Mobile-First UI <span class="status-pill-next">Phase 2</span></div>
      <div class="feature-body">The shopping list is used in a grocery store on a phone.
      The Sunday Buy-Off is done on a couch on a Sunday morning. The current Streamlit UI
      is functional on mobile but not optimised for it. Phase 2 fixes that.</div>
      <div class="feature-why">Why: If the shopping list isn't usable on a phone in
      a Kroger aisle, the product hasn't shipped.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — GROWTH (INVESTMENT ROUND · REGIONAL SCALE)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="phase-hero phase-growth">', unsafe_allow_html=True)
st.markdown("""
<div class="phase-label" style="color:#C09FE0;">Phase 3</div>
<div class="phase-timing">Growth · Months 6–18 · Investment Round · Regional Scale</div>
<div class="phase-title">From pilot data to a product people pay for.</div>
<div class="phase-subtitle">
  This is what investment buys. Not the concept — the infrastructure to take a proven
  concept to 500 households across the Mid-Atlantic, with real revenue, real retention data,
  and the engineering foundation for national scale.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

p3c1, p3c2, p3c3 = st.columns(3)

with p3c1:
    st.markdown("""
    <div class="feature-card growth">
      <div class="feature-icon">📖</div>
      <div class="feature-title">WhollyFare Cookbook <span class="status-pill-future">Phase 3</span></div>
      <div class="feature-body">Full step-by-step recipes built from the hero ingredients the engine
      selects each week. Recipes adapt to your constraints automatically. The cookbook grows with
      your household's history — meals you loved come back when the same ingredients go on sale.
      Eventually: a publishable, personalised household cookbook.</div>
      <div class="feature-why">Why: Retention. A family with 20 approved recipes in their
      WhollyFare cookbook doesn't cancel their subscription.</div>
    </div>
    """, unsafe_allow_html=True)

with p3c2:
    st.markdown("""
    <div class="feature-card growth">
      <div class="feature-icon">🤖</div>
      <div class="feature-title">Automated Circular Parsing <span class="status-pill-future">Phase 3</span></div>
      <div class="feature-body">No more manual uploads. Grocer circulars are pulled automatically
      each week via API integrations (Kroger is live; others via data partnerships or improved
      PDF automation). The Sunday workflow becomes truly one tap — not one tap plus a PDF download.</div>
      <div class="feature-why">Why: The manual upload is the POC's biggest friction point.
      Removing it is the difference between a product families use and one they try once.</div>
    </div>
    """, unsafe_allow_html=True)

with p3c3:
    st.markdown("""
    <div class="feature-card growth">
      <div class="feature-icon">🏥</div>
      <div class="feature-title">Health System Partnerships <span class="status-pill-future">Phase 3</span></div>
      <div class="feature-body">B2B licensing to health systems, insurance companies, and employer
      wellness programs. A hospital system managing 10,000 patients with CKD or celiac has a
      direct interest in a tool that helps those patients eat safely at home.
      The constraint engine's audit log is the compliance layer they need.</div>
      <div class="feature-why">Why: The medical edge is the highest-value market and the
      hardest one for competitors to enter honestly.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — NATIONAL (SERIES A)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="phase-hero phase-scale">', unsafe_allow_html=True)
st.markdown("""
<div class="phase-label" style="color:#E8C060;">Phase 4</div>
<div class="phase-timing">National · Months 18–36 · Series A · 50,000+ Households</div>
<div class="phase-title">The category-defining meal planning platform.</div>
<div class="phase-subtitle">
  15+ grocer chains. National coverage. The Sincere Strategy as a brand that carries
  the same weight as "no artificial ingredients" or "B Corp certified."
  The moat competitors spent 10 years building is the thing that prevents them from
  competing with us.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

p4c1, p4c2, p4c3, p4c4 = st.columns(4)

national_features = [
    ("🌍", "National Grocer Coverage", "15+ chain integrations via API partnerships and data licensing agreements. Kroger, Publix, Albertsons, H-E-B, Aldi, Meijer, Wegmans, Safeway — the stores American families actually shop."),
    ("🧠", "Preference Learning", "The plan gets smarter the longer you use it. Cuisine preferences, rejected meals, family favourites, and pantry patterns all feed a personalised recommendation layer. WhollyFare in Year 2 is fundamentally better than WhollyFare on Day 1."),
    ("🧾", "Receipt Auto-Capture", "Point your phone at a receipt and WhollyFare reads it. OCR + ML matches items to the week's plan and updates the Found Money ledger automatically. No manual entry, ever."),
    ("🤝", "Community & Sharing", "Share your household's approved meals and savings tips with other WhollyFare families. A WhollyFare community built around real cooking, real savings, and real food — not influencer content."),
]

for col, (icon, title, body) in zip([p4c1, p4c2, p4c3, p4c4], national_features):
    with col:
        st.markdown(f"""
        <div class="feature-card scale">
          <div class="feature-icon">{icon}</div>
          <div class="feature-title">{title} <span class="status-pill-future">Phase 4</span></div>
          <div class="feature-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# THE INVESTMENT ARGUMENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:12px;'>Why this raises at 7–8 figures</div>",
    unsafe_allow_html=True,
)

ia1, ia2 = st.columns([3, 2])

with ia1:
    st.markdown("""
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
    """, unsafe_allow_html=True)

with ia2:
    metrics = [
        ("$800B", "U.S. grocery market"),
        ("$9B",   "Meal kit market WhollyFare disrupts"),
        ("$1,400","Average annual savings per household"),
        ("96%",   "Gross margin at steady state"),
        ("$0",    "Paid placements. Ever."),
    ]
    for val, label in metrics:
        st.markdown(f"""
        <div style='background:white;border:1px solid #E8EEE8;border-left:4px solid #3A8C4E;
                    border-radius:8px;padding:14px 18px;margin-bottom:10px;'>
          <div style='font-size:1.8rem;font-weight:800;color:#1A2E1D;line-height:1;'>{val}</div>
          <div style='font-size:0.79rem;color:#5A7A62;margin-top:4px;'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# ── Contact / CTA ─────────────────────────────────────────────────────────────
st.markdown("""
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
  <div style='font-size:0.9rem;color:rgba(255,255,255,0.65);max-width:520px;
              margin:0 auto 20px;line-height:1.6;'>
    The POC is live. The pilot data is accumulating. The moat is structural.
    If you're an investor who believes American families deserve a meal planner
    that works for them — let's talk.
  </div>
  <a href="mailto:tim.hislop@gmail.com"
     style="display:inline-block;background:#3A8C4E;color:white;font-weight:700;
            font-size:0.92rem;padding:13px 32px;border-radius:8px;text-decoration:none;">
    📧 tim.hislop@gmail.com
  </a>
  <div style='font-size:0.76rem;color:rgba(255,255,255,0.35);margin-top:16px;'>
    Sentir Solutions® LLC · Charlottesville, VA
  </div>
</div>
""", unsafe_allow_html=True)
