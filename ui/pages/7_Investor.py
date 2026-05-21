"""7_Investor.py — WhollyFare® Investor Brief

Framing: This is not a pitch deck asking for permission.
WhollyFare is happening. The question is whether you want to be part of it —
and if so, how, and at what return.

Three types of investors. Real math. Tim keeps control. Every path shown honestly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.style as style
import ui.state as state
from datetime import date, timedelta
import math

st.set_page_config(page_title="Investor Brief · WhollyFare", page_icon="📈", layout="wide")
state.init()
with st.sidebar:
    style.sidebar_nav()
style.inject()

# ── Page CSS ──────────────────────────────────────────────────────────────────
st.html("""
<style>
/* ── Hero ── */
.inv-dark-hero {
    background: linear-gradient(160deg, #0A0F0D 0%, #0F1F14 60%, #0A0F0D 100%);
    border-radius: 16px; padding: 64px 52px 56px; color: white;
    margin-bottom: 36px; position: relative; overflow: hidden;
}
.inv-dark-hero::before {
    content:''; position:absolute; top:-60px; right:-60px;
    width:320px; height:320px;
    background:radial-gradient(circle,rgba(58,140,78,.18) 0%,transparent 70%);
    pointer-events:none;
}
.inv-dark-hero .hero-eyebrow {
    font-size:.72rem; font-weight:700; letter-spacing:.14em;
    text-transform:uppercase; color:#5DAA6A; margin-bottom:18px;
}
.inv-dark-hero h1 { font-size:4rem; font-weight:800; margin:0 0 14px; color:#fff; line-height:1.05; letter-spacing:-.02em; }
.inv-dark-hero .tagline { font-size:1.2rem; opacity:.78; max-width:660px; line-height:1.65; }
.inv-hero-stats { display:flex; gap:20px; margin-top:44px; flex-wrap:wrap; }
.inv-hero-stat-tile {
    background:rgba(255,255,255,.06); backdrop-filter:blur(8px);
    border:1px solid rgba(93,170,106,.25); border-radius:12px;
    padding:22px 28px; min-width:150px; flex:1;
}
.inv-hero-stat-tile .stat-big  { font-size:2rem; font-weight:800; color:#F28B30; line-height:1.1; }
.inv-hero-stat-tile .stat-small{ font-size:.78rem; color:rgba(255,255,255,.55); margin-top:5px; line-height:1.4; }

/* ── Section labels ── */
.inv-section-label {
    font-size:.68rem; font-weight:700; letter-spacing:.14em;
    text-transform:uppercase; color:#3A8C4E; margin-bottom:6px;
}

/* ── Stat cards ── */
.inv-stat { background:#fff; border-radius:10px; padding:24px 20px; border:1px solid #e8e8e8;
            border-left:5px solid #3A8C4E; box-shadow:0 2px 12px rgba(0,0,0,.06); margin-bottom:14px; }
.inv-stat .stat-number { font-size:2.2rem; font-weight:800; color:#0A0F0D; line-height:1.1; }
.inv-stat .stat-label  { font-size:.82rem; color:#555; margin-top:5px; line-height:1.45; }
.inv-stat .stat-source { font-size:.70rem; color:#999; margin-top:8px; }

/* ── Dark band ── */
.inv-dark-band {
    background:linear-gradient(160deg,#0A0F0D 0%,#0F1F14 100%);
    border-radius:14px; padding:48px 44px; color:white; margin:8px 0;
}
.inv-dark-band h2 { color:#fff; font-size:1.9rem; font-weight:800; margin-bottom:10px; letter-spacing:-.01em; }
.inv-dark-band .band-sub { color:rgba(255,255,255,.65); font-size:.95rem; line-height:1.6; margin-bottom:32px; }
.inv-dark-band .band-section-label {
    font-size:.68rem; font-weight:700; letter-spacing:.14em;
    text-transform:uppercase; color:#5DAA6A; margin-bottom:8px;
}
.dark-phase-card {
    background:rgba(255,255,255,.05); border:1px solid rgba(93,170,106,.2);
    border-left:4px solid #3A8C4E; border-radius:10px; padding:20px 18px;
    margin-bottom:12px; color:white;
}
.dark-phase-card .dp-timing { font-size:.72rem; color:rgba(255,255,255,.45); text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }
.dark-phase-card .dp-body   { font-size:.83rem; color:rgba(255,255,255,.72); line-height:1.55; }

/* ── Competitor ── */
.comp-col    { background:#1a1a1a; border-radius:10px; padding:18px 14px; height:100%; border:1px solid #2a2a2a; }
.comp-col-wf { background:linear-gradient(160deg,#0F2518,#1A3D22); border-radius:10px; padding:18px 14px; height:100%; border:2px solid #3A8C4E; }
.comp-col .comp-name    { font-size:.95rem; font-weight:700; color:#ccc; margin-bottom:6px; }
.comp-col-wf .comp-name { font-size:.95rem; font-weight:700; color:#5DAA6A; margin-bottom:6px; }
.comp-col .comp-price    { font-size:1.4rem; font-weight:800; color:#e05c5c; margin-bottom:6px; line-height:1.1; }
.comp-col-wf .comp-price { font-size:1.4rem; font-weight:800; color:#F28B30; margin-bottom:6px; line-height:1.1; }
.comp-col .comp-desc    { font-size:.78rem; color:#888; line-height:1.45; }
.comp-col-wf .comp-desc { font-size:.78rem; color:rgba(255,255,255,.7); line-height:1.45; }
.comp-badge    { display:inline-block; background:rgba(224,92,92,.18); color:#e05c5c; border:1px solid rgba(224,92,92,.35); border-radius:20px; padding:3px 10px; font-size:.68rem; font-weight:600; margin-top:8px; letter-spacing:.04em; }
.comp-badge-wf { display:inline-block; background:rgba(93,170,106,.2); color:#5DAA6A; border:1px solid rgba(93,170,106,.4); border-radius:20px; padding:3px 10px; font-size:.68rem; font-weight:600; margin-top:8px; letter-spacing:.04em; }

/* ── Tier rows ── */
.inv-tier-row {
    background:#fff; border-radius:10px; padding:20px 22px;
    border:1px solid #e8e8e8; border-left:5px solid #3A8C4E;
    box-shadow:0 2px 8px rgba(0,0,0,.05); margin-bottom:12px;
    display:flex; align-items:center; gap:24px; flex-wrap:wrap;
}
.inv-tier-name  { font-size:1rem; font-weight:700; color:#0A0F0D; min-width:160px; }
.inv-tier-price { font-size:1.4rem; font-weight:800; color:#3A8C4E; min-width:120px; }
.inv-tier-desc  { font-size:.83rem; color:#555; line-height:1.5; flex:1; }

/* ── Halo rings ── */
.halo-card-1 { background:#0F2518; border:1px solid #3A8C4E; border-radius:10px; padding:20px 16px; }
.halo-card-2 { background:#163320; border:1px solid #4A9E5C; border-radius:10px; padding:20px 16px; }
.halo-card-3 { background:#1E4228; border:1px solid #5DAA6A; border-radius:10px; padding:20px 16px; }
.halo-card-4 { background:#274F30; border:1px solid #7ABF87; border-radius:10px; padding:20px 16px; }
.halo-card-1 .halo-ring-label,.halo-card-2 .halo-ring-label,.halo-card-3 .halo-ring-label,.halo-card-4 .halo-ring-label {
    font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:4px;
}
.halo-card-1 .halo-ring-label { color:#5DAA6A; }
.halo-card-2 .halo-ring-label { color:#6DC47B; }
.halo-card-3 .halo-ring-label { color:#84CE90; }
.halo-card-4 .halo-ring-label { color:#9ED9A9; }
.halo-ring-title { font-size:1rem; font-weight:700; color:#fff; margin-bottom:8px; }
.halo-ring-desc  { font-size:.80rem; color:rgba(255,255,255,.65); line-height:1.5; }

/* ── Why cards ── */
.why-card { background:#fff; border-radius:10px; padding:22px 18px; border:1px solid #ebebeb;
            box-shadow:0 2px 10px rgba(0,0,0,.05); height:100%; border-top:4px solid #3A8C4E; }
.why-card .why-icon  { font-size:1.6rem; margin-bottom:10px; }
.why-card .why-title { font-size:.95rem; font-weight:700; color:#0A0F0D; margin-bottom:7px; }
.why-card .why-body  { font-size:.82rem; color:#555; line-height:1.55; }

/* ── Step cards ── */
.step-card { background:#fff; border-radius:10px; padding:22px 18px; border:1px solid #e8e8e8;
             box-shadow:0 2px 10px rgba(0,0,0,.05); height:100%; }
.step-card .step-icon  { font-size:1.8rem; margin-bottom:10px; }
.step-card .step-title { font-size:1rem; font-weight:700; color:#0A0F0D; margin-bottom:7px; }
.step-card .step-body  { font-size:.83rem; color:#555; line-height:1.55; }
.step-card-1 { border-left:5px solid #3A8C4E; }
.step-card-2 { border-left:5px solid #5DAA6A; }
.step-card-3 { border-left:5px solid #7ABF87; }

/* ── Sincere cards ── */
.sincere-card { background:#fff; border-radius:10px; padding:16px 18px;
                border:1px solid #e8e8e8; border-left:4px solid #3A8C4E;
                box-shadow:0 2px 8px rgba(0,0,0,.05); margin-bottom:12px; }
.sincere-card .sc-title { font-size:.95rem; font-weight:700; color:#0A0F0D; margin-bottom:5px; }
.sincere-card .sc-body  { font-size:.82rem; color:#444; line-height:1.55; }
.moat-callout { background:#F0F9F2; border:1px solid #A8D5B0; border-radius:10px;
                padding:18px 22px; margin-top:20px; font-size:.9rem;
                color:#1E4228; font-weight:600; line-height:1.55; }

/* ── Founder's Bet ── */
.founder-card {
    background:linear-gradient(160deg,#0A0F0D,#0F2518);
    border:2px solid #3A8C4E; border-radius:14px; padding:36px 40px;
    color:white; margin-bottom:8px; position:relative; overflow:hidden;
}
.founder-card::before {
    content:''; position:absolute; bottom:-40px; right:-40px;
    width:200px; height:200px;
    background:radial-gradient(circle,rgba(93,170,106,.15) 0%,transparent 70%);
}
.founder-pull {
    font-size:1.45rem; font-weight:800; color:#fff; line-height:1.3;
    letter-spacing:-.01em; margin-bottom:20px; max-width:700px;
}
.founder-body { font-size:.92rem; color:rgba(255,255,255,.72); line-height:1.7; }
.founder-signal {
    background:rgba(93,170,106,.15); border:1px solid rgba(93,170,106,.35);
    border-radius:10px; padding:16px 20px; margin-top:22px;
    font-size:.86rem; color:rgba(255,255,255,.8); line-height:1.6;
}

/* ── Investor type cards ── */
.itype-card {
    border-radius:12px; padding:28px 24px; height:100%;
    border:2px solid; position:relative;
}
.itype-angel   { background:linear-gradient(160deg,#0A0F0D,#1A2810); border-color:#3A8C4E; }
.itype-partner { background:linear-gradient(160deg,#0A0D1A,#102040); border-color:#3A6EA8; }
.itype-acquirer{ background:linear-gradient(160deg,#1A0A0A,#2D1208); border-color:#B8860B; }
.itype-badge {
    display:inline-block; border-radius:20px; padding:4px 14px;
    font-size:.68rem; font-weight:700; letter-spacing:.1em;
    text-transform:uppercase; margin-bottom:16px;
}
.itype-badge-angel   { background:rgba(93,170,106,.2);  color:#5DAA6A; border:1px solid #5DAA6A; }
.itype-badge-partner { background:rgba(58,110,168,.2);  color:#7EB3E8; border:1px solid #3A6EA8; }
.itype-badge-acquirer{ background:rgba(184,134,11,.2);  color:#E8C060; border:1px solid #B8860B; }
.itype-title { font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:8px; letter-spacing:-.01em; }
.itype-sub   { font-size:.83rem; color:rgba(255,255,255,.55); line-height:1.55; margin-bottom:20px; }
.itype-give  { font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:8px; }
.itype-give-angel   { color:#5DAA6A; }
.itype-give-partner { color:#7EB3E8; }
.itype-give-acquirer{ color:#E8C060; }
.itype-item {
    font-size:.82rem; color:rgba(255,255,255,.78); padding:6px 0;
    border-bottom:1px solid rgba(255,255,255,.07); line-height:1.45;
    display:flex; gap:8px; align-items:flex-start;
}
.itype-item:last-child { border-bottom:none; }
.itype-check-angel   { color:#5DAA6A; flex-shrink:0; }
.itype-check-partner { color:#7EB3E8; flex-shrink:0; }
.itype-check-acquirer{ color:#E8C060; flex-shrink:0; }

/* ── Control architecture ── */
.ctrl-bar {
    background:#FFFFFF; border:1px solid #D8EDD0; border-radius:10px;
    padding:20px 24px; margin-bottom:12px;
}
.ctrl-scenario { font-size:.78rem; font-weight:700; color:#1E5C32; margin-bottom:8px; text-transform:uppercase; letter-spacing:.06em; }
.ctrl-bar-outer {
    background:#EEF3EE; border-radius:20px; height:28px; width:100%;
    position:relative; overflow:hidden; margin-bottom:4px;
}
.ctrl-bar-tim {
    background:linear-gradient(90deg,#3A8C4E,#5DAA6A);
    height:100%; border-radius:20px; display:flex; align-items:center;
    padding:0 12px; font-size:.75rem; font-weight:700; color:white;
    white-space:nowrap; position:absolute; left:0; top:0;
}
.ctrl-bar-inv {
    background:linear-gradient(90deg,#F28B30,#BF5E00);
    height:100%; border-radius:0 20px 20px 0; display:flex; align-items:center;
    padding:0 10px; font-size:.75rem; font-weight:700; color:white;
    white-space:nowrap; position:absolute; top:0;
}

/* ── Grant / non-dilutive ── */
.grant-card {
    background:#fff; border-radius:10px; padding:18px 20px;
    border:1px solid #ebebeb; border-left:4px solid #3A8C4E;
    box-shadow:0 2px 8px rgba(0,0,0,.05); margin-bottom:12px; height:100%;
}
.grant-card .gc-name   { font-size:.95rem; font-weight:700; color:#0A0F0D; margin-bottom:4px; }
.grant-card .gc-amount { font-size:1.3rem; font-weight:800; color:#3A8C4E; margin-bottom:6px; }
.grant-card .gc-body   { font-size:.80rem; color:#555; line-height:1.5; }
.grant-card .gc-badge  {
    display:inline-block; background:#E3F4E8; color:#1E5C32;
    border-radius:20px; padding:2px 10px; font-size:.67rem;
    font-weight:700; margin-top:8px;
}

/* ── Ask ── */
.inv-ask-hero {
    background:linear-gradient(160deg,#060B08,#0D1F11 60%,#060B08);
    border-radius:16px; padding:64px 52px; text-align:center; color:white;
    margin-top:8px; position:relative; overflow:hidden;
}
.inv-ask-hero::before {
    content:''; position:absolute; bottom:-80px; left:50%;
    transform:translateX(-50%); width:500px; height:300px;
    background:radial-gradient(ellipse,rgba(58,140,78,.15) 0%,transparent 70%);
    pointer-events:none;
}
.inv-ask-hero .ask-eyebrow { font-size:.68rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#5DAA6A; margin-bottom:20px; }
.inv-ask-hero h2 { font-size:2.6rem; font-weight:800; color:#fff; margin-bottom:12px; letter-spacing:-.02em; }
.inv-ask-hero .ask-desc { font-size:1rem; opacity:.78; max-width:620px; margin:0 auto 28px; line-height:1.7; }
.inv-ask-hero a { color:#5DAA6A; }
</style>
""")


# ══════════════════════════════════════════════════════════════════════════════
# 1. HERO — conviction, not ask
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class="inv-dark-hero">
  <div class="hero-eyebrow">WhollyFare&#174; &nbsp;·&nbsp; Sentir Solutions&#174; LLC &nbsp;·&nbsp; Charlottesville, VA</div>
  <h1>This is happening.</h1>
  <div class="tagline">
    A meal plan that pays families back — built from real sale circulars, filtered for their
    actual health constraints, with zero paid placements. Ever.<br><br>
    The only question is whether you want to be part of it.
  </div>
  <div class="inv-hero-stats">
    <div class="inv-hero-stat-tile">
      <div class="stat-big">$1,400</div>
      <div class="stat-small">average annual savings<br>available per household</div>
    </div>
    <div class="inv-hero-stat-tile">
      <div class="stat-big">~$2–4</div>
      <div class="stat-small">cost per serving<br>vs. $9.99 HelloFresh</div>
    </div>
    <div class="inv-hero-stat-tile">
      <div class="stat-big">$0</div>
      <div class="stat-small">paid placements<br>ever, by design</div>
    </div>
    <div class="inv-hero-stat-tile">
      <div class="stat-big">100%</div>
      <div class="stat-small">founder voting control<br>retained through seed phase</div>
    </div>
  </div>
</div>
""")

col_cta1, col_cta2, col_spacer = st.columns([1, 1, 4])
with col_cta1:
    if st.button("🌿 Try the app", use_container_width=True):
        st.switch_page("Home.py")
with col_cta2:
    st.html(
        '<a href="mailto:tim.hislop@gmail.com" style="display:block;text-align:center;'
        'padding:8px 0;border:1px solid #3A8C4E;border-radius:8px;color:#3A8C4E;'
        'font-size:.9rem;font-weight:600;text-decoration:none;">📧 Get in touch</a>')
st.html("<br>")


# ══════════════════════════════════════════════════════════════════════════════
# 2. THE FOUNDER'S BET
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">The Founder\'s Bet</div>')

st.html("""
<div class="founder-card">
  <div class="founder-pull">
    I am doing this with or without outside capital. That is not a negotiating position —
    it is the honest truth about what this product means to me and my family.
  </div>
  <div class="founder-body">
    I am Tim Hislop. I built WhollyFare&#174; because my family shops at four stores in
    Charlottesville, Virginia and I was tired of leaving money on the table every week.
    I am currently employed full-time at ECS. WhollyFare is what I am building every night
    and every weekend — not because a VC told me there was a market opportunity, but because
    I fed my family with it last Sunday and it worked.<br><br>
    My goal is not to raise a round. My goal is to build something so undeniably useful —
    with real receipt data, real households, and a constraint engine no competitor can honestly
    copy — that the right partners and acquirers come to <em>me</em>. On my terms. At a price
    that reflects what we built, not what I needed to survive.<br><br>
    I will invest time, nights, weekends, and personal capital into this for as long as it takes.
    I am recruiting pilot households one conversation at a time. I am logging real grocery receipts.
    I am building the evidence before I make the argument.
  </div>
  <div class="founder-signal">
    <strong style="color:#9FD9A8;">Early signal:</strong> &nbsp;Two people have seen an early version
    of WhollyFare. Neither was asked for feedback. Both immediately understood the idea and offered
    suggestions that assumed it would exist. That is the response you get when something is real —
    not when it's a pitch. That is what we are building toward.
  </div>
</div>
""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 3. THE PROBLEM
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">The Problem</div>')
st.html("### American families are losing the grocery game.")

col_p1, col_p2 = st.columns([6, 4])
with col_p1:
    st.markdown("""
The average U.S. household spends **$5,703 per year** on groceries *(BLS Consumer Expenditure Survey, 2023)*
and leaves an estimated **15–25% on the table** through brand loyalty, single-store shopping,
and missed weekly sales. That's up to **$1,400/year** quietly leaving every family's budget.

The tools that exist today don't actually solve this:

- **Meal-kit services** (HelloFresh, Blue Apron) charge a **$9.99/serving premium** — they cost *more* than the grocery store.
- **Grocery apps** (Flipp, Ibotta) surface coupons but have zero integration with meal planning.
- **Instacart / DoorDash** optimize for convenience at a margin premium; savings are never the goal.
- **Nutrition apps** give meal guidance with zero price awareness.

**Nobody has connected the dots.** No platform optimizes the full loop:
sale prices → constraint-aware meal plan → shopping list → grocer checkout.
That gap is WhollyFare&#174;.
    """)
with col_p2:
    st.html("""
<div class="inv-stat">
  <div class="stat-number">$5,703</div>
  <div class="stat-label">Average annual U.S. household grocery spend</div>
  <div class="stat-source">BLS Consumer Expenditure Survey, 2023</div>
</div>
<div class="inv-stat">
  <div class="stat-number">$1,400</div>
  <div class="stat-label">Estimated annual savings available through cross-store price optimization</div>
  <div class="stat-source">Internal WhollyFare analysis</div>
</div>
<div class="inv-stat">
  <div class="stat-number">$9.99</div>
  <div class="stat-label">HelloFresh cost per serving — the benchmark WhollyFare beats every single week</div>
  <div class="stat-source">HelloFresh published pricing, 2024</div>
</div>
    """)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 4. THE SOLUTION
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">The Solution</div>')
st.html("### One engine. Three steps. Every Sunday.")
st.markdown("""
WhollyFare&#174; inverts the meal-kit model. Instead of charging a premium for pre-portioned ingredients,
we use each week's **actual sale circulars** from your local grocers to build the lowest-cost,
safe, constraint-compliant meal plan for your household — then hand you a shopping list by store.
""")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.html("""<div class="step-card step-card-1">
  <div class="step-icon">🛒</div><div class="step-title">1. Harvest</div>
  <div class="step-body">Pull weekly sale prices from grocery APIs and PDF circulars.
  Every item tagged with category, allergens, and nutrition data via USDA FDC.</div>
</div>""")
with col_s2:
    st.html("""<div class="step-card step-card-2">
  <div class="step-icon">🛡️</div><div class="step-title">2. Filter</div>
  <div class="step-body">Run every item through the household's hard constraints —
  allergies, diagnoses (celiac, diabetes, CKD, IBS), lifestyle. Zero compromise.
  Every rejection logged and shown to the user.</div>
</div>""")
with col_s3:
    st.html("""<div class="step-card step-card-3">
  <div class="step-icon">🍽️</div><div class="step-title">3. Plan</div>
  <div class="step-body">Score remaining ingredients by sale savings × nutrition density.
  Build 5–7 hero ingredients into a full week of dinners across flavor profiles.
  One tap to approve. One list to shop.</div>
</div>""")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 5. THE MOAT — THE SINCERE STRATEGY
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">The Moat</div>')
st.html("### Six commitments competitors cannot copy.")
st.markdown("""
WhollyFare&#174; operates under the **Sincere Strategy&#174;** — commitments to the user that
competitors with existing advertiser and brand relationships cannot adopt without dismantling their revenue model.
""")
sincere = [
    ("🚫 No paid placements", "No grocer, brand, or CPG company can pay to appear in a plan. Recommendations are pure. Ever."),
    ("🛡️ Sacrosanct health constraints", "If a member has a peanut allergy, peanuts never appear — not in a plan, a suggestion, a 'you might like.' Health is the engine's highest-priority input."),
    ("🔍 Radical transparency", "Every ingredient rejection is logged and shown to the user. The constraint audit log is a first-class feature. No black boxes."),
    ("📍 Local-first", "Plans are built from your local grocers' actual weekly circulars — not national averages or partnered inventory. Savings are real and verifiable."),
    ("💰 Safety over savings", "WhollyFare will never recommend an unsafe ingredient because it's on sale. The constraint engine runs before the budget optimizer. Always."),
    ("🔐 User data ownership", "Household health data is yours. WhollyFare does not sell, share, or use it for targeting. Full stop."),
]
col_a, col_b = st.columns(2)
for i, (title, desc) in enumerate(sincere):
    with (col_a if i % 2 == 0 else col_b):
        st.html(f"""<div class="sincere-card">
  <div class="sc-title">{title}</div>
  <div class="sc-body">{desc}</div>
</div>""")
st.html("""<div class="moat-callout">
  Competitors cannot copy the Sincere Strategy&#174; without dismantling their own revenue model.
  That asymmetry is structural and gets stronger the longer WhollyFare builds trust.
</div>""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 6. COMPETITIVE LANDSCAPE
# ══════════════════════════════════════════════════════════════════════════════
st.html("""<div class="inv-dark-band">
  <div class="band-section-label">Competitive Landscape</div>
  <h2>A $25B industry working against the consumer.</h2>
  <div class="band-sub">The meal planning and grocery delivery space is large, fragmented, and almost entirely
  oriented around margins for the platform rather than savings for the family.
  WhollyFare&#174; occupies white space none of the incumbents can enter honestly.</div>
</div>""")

comp_cols = st.columns(5)
competitors = [
    ("HelloFresh",     "$9.99/serving",      "Convenient, branded, expensive. No local-store integration. No constraint awareness.", "conflict of interest", False),
    ("Blue Apron",     "$10.99/serving",      "Premium meal-kit. Financially distressed. Same model as HelloFresh.", "conflict of interest", False),
    ("Flipp / Ibotta", "Free (ad-supported)", "Coupon aggregators. No meal planning. Revenue from advertisers.", "conflict of interest", False),
    ("Instacart",      "$3.99+/order",        "Delivery platform. Charges markup. No meal planning, no savings goal.", "conflict of interest", False),
    ("WhollyFare®",    "~$2–4/serving",       "Cross-grocer optimization, hard health constraints, transparent logic, zero paid placements.", "user-aligned", True),
]
for col, (name, price, desc, badge, wf) in zip(comp_cols, competitors):
    with col:
        cc = "comp-col-wf" if wf else "comp-col"
        bc = "comp-badge-wf" if wf else "comp-badge"
        st.html(f"""<div class="{cc}">
  <div class="comp-name">{name}</div>
  <div class="comp-price">{price}</div>
  <div class="comp-desc">{desc}</div>
  <div class="{bc}">{badge}</div>
</div>""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 7. GO-TO-MARKET
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">Go-To-Market</div>')
st.html("### Start at the edge. Earn the mainstream.")
st.markdown("""
Our distribution strategy is deliberately counter-intuitive. We start with households who need
reliable, safe meal planning the *most* — medical-edge users — and let their advocacy carry us
outward. Families managing celiac, MCAS, Type 1 diabetes, or CKD need a tool they can *trust absolutely.*
When WhollyFare&#174; earns that trust, it radiates.
""")
ring_cols = st.columns(4)
rings = [
    ("Ring 1", "Medical Edge",   "MCAS · Celiac · CKD · EDS · PKU",       "Highest advocacy. Zero tolerance for error. The trust that radiates outward.", "halo-card-1"),
    ("Ring 2", "Health-Aware",   "Diabetic · Low-FODMAP · Hypertension",   "Actively managing diet. Responsive to proven results. Deep retention.", "halo-card-2"),
    ("Ring 3", "Budget-First",   "Inflation-squeezed families",             "Savings is the primary value prop. Large addressable segment.", "halo-card-3"),
    ("Ring 4", "Mainstream",     "General households",                       "Convenience + savings via advocacy and word of mouth.", "halo-card-4"),
]
for col, (rn, rt, tags, desc, css) in zip(ring_cols, rings):
    with col:
        st.html(f"""<div class="{css}">
  <div class="halo-ring-label">{rn}</div>
  <div class="halo-ring-title">{rt}</div>
  <div style="font-size:.72rem;color:rgba(255,255,255,.45);margin-bottom:8px">{tags}</div>
  <div class="halo-ring-desc">{desc}</div>
</div>""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 8. BUSINESS MODEL
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">Business Model</div>')
st.html("### Subscription only. No ads. No affiliate revenue. Ever.")
for tier_name, tier_price, tier_desc, tier_features in [
    ("Free",     "Free",     "The wedge. Multi-grocer price comparison. Establishes habit and trust.",
     "Cross-store price comparison · Weekly sale highlights · Basic shopping list"),
    ("Core",     "$7 / mo",  "Full meal planning, Sunday Buy-Off, Found Money tracking.",
     "Weekly meal plan · Found Money ledger · Sunday Buy-Off · Plan history"),
    ("Health",   "$19 / mo", "Medical constraint engine. The clinical safety layer.",
     "Everything in Core · Hard dietary constraints · Allergen audit log · Clinical-grade filtering"),
    ("Complete", "$29 / mo", "Recipes, pantry tracking, family favorites memory, auto-reorder.",
     "Everything in Health · Recipe engine · Pantry tracker · Flavor memory · Auto-reorder"),
]:
    st.html(f"""<div class="inv-tier-row">
  <div class="inv-tier-name">{tier_name}</div>
  <div class="inv-tier-price">{tier_price}</div>
  <div class="inv-tier-desc"><strong>{tier_desc}</strong><br>
    <span style="font-size:.78rem;color:#888">{tier_features}</span>
  </div>
</div>""")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 9. WHY NOW
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">Why Now</div>')
st.html("### Three forces converging. The window is open.")
col_w1, col_w2, col_w3 = st.columns(3)
for col, icon, title, body in [
    (col_w1, "📈", "Grocery inflation",     "U.S. grocery prices rose 25%+ between 2020–2024. Demand for savings tools is unprecedented and still climbing."),
    (col_w2, "🔗", "Grocer APIs opening",   "Kroger's Developer API launched in 2019 and continues expanding. Other major chains are following. The manual PDF path becomes automated within 24 months."),
    (col_w3, "🤖", "AI makes it tractable", "LLM-assisted PDF parsing, constraint reasoning, and recipe generation have crossed the threshold of production reliability. This is buildable by a small team right now."),
]:
    with col:
        st.html(f"""<div class="why-card">
  <div class="why-icon">{icon}</div>
  <div class="why-title">{title}</div>
  <div class="why-body">{body}</div>
</div>""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 10. NON-DILUTIVE FUNDING — what's available before or instead of outside capital
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">Non-Dilutive Funding Available</div>')
st.html("### Tim doesn't need your money. Here's what's available before any equity conversation.")
st.markdown("""
Showing investors the non-dilutive options is not a threat — it's transparency.
It shows we have a path forward regardless, and that any equity conversation is a choice,
not a necessity. This matters for valuation, for terms, and for the relationship.
""")

nd_col1, nd_col2, nd_col3, nd_col4 = st.columns(4)
with nd_col1:
    st.html("""<div class="grant-card">
  <div class="gc-name">USDA SBIR / NIFA Grants</div>
  <div class="gc-amount">$100k – $750k</div>
  <div class="gc-body">USDA's Small Business Innovation Research program funds food tech with health, nutrition, and local agriculture angles. WhollyFare's constraint engine and local-grocer focus are strong fits.</div>
  <div class="gc-badge">Zero dilution</div>
</div>""")
with nd_col2:
    st.html("""<div class="grant-card">
  <div class="gc-name">Virginia VIPC / CIT Grants</div>
  <div class="gc-amount">$25k – $250k</div>
  <div class="gc-body">Virginia Innovation Partnership Corporation and the Center for Innovative Technology fund early-stage Virginia-based tech companies. Charlottesville presence is an advantage.</div>
  <div class="gc-badge">Zero dilution</div>
</div>""")
with nd_col3:
    st.html("""<div class="grant-card">
  <div class="gc-name">SBA Loans (7a / Microloan)</div>
  <div class="gc-amount">$50k – $500k</div>
  <div class="gc-body">SBA-guaranteed debt financing. Repaid from revenue. No equity surrendered, no board seats, no dilution. Best deployed once initial revenue validates the model.</div>
  <div class="gc-badge">Debt, not equity</div>
</div>""")
with nd_col4:
    st.html("""<div class="grant-card">
  <div class="gc-name">Revenue-Based Financing</div>
  <div class="gc-amount">$100k – $1M+</div>
  <div class="gc-body">Providers like Clearco and Lighter Capital advance capital repaid as a % of monthly revenue (typically 6–12%). Available once WhollyFare reaches $50k+ ARR. No equity, no board seats.</div>
  <div class="gc-badge">Repaid from revenue</div>
</div>""")

st.html("""
<div style='background:#F0F9F2;border:1px solid #A8D5B0;border-radius:10px;
            padding:14px 22px;margin-top:8px;font-size:.87rem;color:#1E4228;line-height:1.6;'>
  <strong>The point:</strong> WhollyFare can reach initial traction — pilot households, receipt data,
  first ARR — on a combination of Tim's personal time, bootstrap capital, and non-dilutive funding.
  Outside equity investment accelerates that path and earns a return. It does not enable it.
</div>
""")
st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 11. HOW YOU CAN HELP — three investor types
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">How You Can Help</div>')
st.html("### Three ways to be part of WhollyFare. All of them honest.")
st.markdown("""
There is no one-size-fits-all investor relationship here. The right structure depends on
who you are and what you're optimizing for. Every path shown below preserves Tim's control
through the seed phase — that is non-negotiable and is explicitly designed into each structure.
""")

itype_cols = st.columns(3)

with itype_cols[0]:
    st.html("""<div class="itype-card itype-angel">
  <div class="itype-badge itype-badge-angel">Angel Partner</div>
  <div class="itype-title">Believe in the mission. Get positioned early.</div>
  <div class="itype-sub">Individual or family office investors who want a stake in a category-defining
  consumer brand before it's obvious. Structured as convertible notes or SAFEs —
  Tim keeps 100% of the voting shares until he chooses to convert.</div>

  <div class="itype-give itype-give-angel">What you give</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>$25k – $500k in capital</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>No board seat (seed phase)</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>Patience — this is a 5–7 year play</div>

  <div class="itype-give itype-give-angel" style="margin-top:16px;">What you get</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>Convertible note with valuation cap</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>20% discount to Series A price at conversion</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>Equity stake at the priced round Tim controls</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>Pro-rata rights in future rounds</div>
  <div class="itype-item"><span class="itype-check-angel">✓</span>Full acquisition upside if buyout occurs first</div>
</div>""")

with itype_cols[1]:
    st.html("""<div class="itype-card itype-partner">
  <div class="itype-badge itype-badge-partner">Strategic Partner</div>
  <div class="itype-title">Grocer, health system, or delivery service.</div>
  <div class="itype-sub">Commercial partnerships — not equity. A grocer that provides API access
  and co-marketing gets first-mover household data and loyalty integration.
  A health system that licenses the constraint engine gets a compliance-ready
  dietary management tool. No equity exchanged.</div>

  <div class="itype-give itype-give-partner">What you give</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>API data access and integration support</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Co-marketing to your customer base</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Revenue-share licensing agreement</div>

  <div class="itype-give itype-give-partner" style="margin-top:16px;">What you get</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>First-mover household shopping intelligence</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Loyalty program integration that works</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Defensive position vs. competitors</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Revenue share on plans using your data</div>
  <div class="itype-item"><span class="itype-check-partner">✓</span>Right of first negotiation on acquisition</div>
</div>""")

with itype_cols[2]:
    st.html("""<div class="itype-card itype-acquirer">
  <div class="itype-badge itype-badge-acquirer">Strategic Acquirer</div>
  <div class="itype-title">When the data is undeniable, make an offer.</div>
  <div class="itype-sub">This is Tim's preferred endgame — an inbound acquisition offer from
  a strategic buyer who understands what they're getting. Kroger, Albertsons, HelloFresh,
  a major health insurer, or an Amazon Fresh. The price reflects the data, the households,
  the constraint engine IP, and the Sincere Strategy brand. Tim sets the terms.</div>

  <div class="itype-give itype-give-acquirer">What you get (as acquirer)</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>Verified household savings data (8+ weeks of receipts)</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>Constraint engine IP — only honest one in the market</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>The Sincere Strategy brand — trust you cannot manufacture</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>Grocer integration pipeline + data agreements</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>Defensive moat vs. any competitor who tries to copy</div>
  <div class="itype-item"><span class="itype-check-acquirer">✓</span>Tim Hislop as a committed operator post-acquisition</div>
</div>""")

st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 12. WHAT YOU CAN MAKE — interactive return calculator
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">What You Can Make</div>')
st.html("### Real math. Every assumption shown.")
st.markdown("""
Select your investor type and model the scenarios. All projections are illustrative —
they are based on stated assumptions, not guarantees. The assumptions themselves are
conservative by design: we would rather underpromise and overdeliver on exit.
""")

calc_type = st.radio(
    "I am a…",
    ["Angel Partner", "Strategic Acquirer"],
    horizontal=True,
    label_visibility="collapsed",
)

if calc_type == "Angel Partner":
    st.markdown("#### Angel Partner return scenarios")

    a_col1, a_col2 = st.columns([1, 2])
    with a_col1:
        angel_invest = st.select_slider(
            "Investment amount",
            options=[25_000, 50_000, 100_000, 150_000, 250_000, 500_000],
            value=100_000,
            format_func=lambda v: f"${v:,.0f}",
        )
        valuation_cap = st.select_slider(
            "Valuation cap on note",
            options=[2_000_000, 3_000_000, 4_000_000, 5_000_000, 6_000_000],
            value=3_000_000,
            format_func=lambda v: f"${v/1_000_000:.1f}M",
        )
        discount = 0.20  # 20% conversion discount — standard
        st.caption("Conversion discount: 20% (standard SAFE/note terms)")

    with a_col2:
        # Equity at conversion = investment / cap (simplified, pre-dilution)
        eq_at_cap  = angel_invest / valuation_cap
        # After Series A dilution (~20% dilution in a $3M raise at $9M pre)
        eq_post_sa = eq_at_cap * 0.80
        st.html(
            f"""<div style='background:#F0F9F2;border:1px solid #A8D5B0;border-radius:10px;
                            padding:16px 22px;margin-bottom:12px;'>
              <div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                          color:#3A8C4E;margin-bottom:8px;'>Your position at conversion</div>
              <div style='display:flex;gap:32px;flex-wrap:wrap;'>
                <div>
                  <div style='font-size:1.6rem;font-weight:800;color:#1A2E1D;'>{eq_at_cap*100:.1f}%</div>
                  <div style='font-size:.78rem;color:#5A7A62;'>equity at cap (pre-dilution)</div>
                </div>
                <div>
                  <div style='font-size:1.6rem;font-weight:800;color:#1A2E1D;'>{eq_post_sa*100:.1f}%</div>
                  <div style='font-size:.78rem;color:#5A7A62;'>est. equity after Series A dilution</div>
                </div>
                <div>
                  <div style='font-size:1.6rem;font-weight:800;color:#1A2E1D;'>100%</div>
                  <div style='font-size:.78rem;color:#5A7A62;'>Tim's voting control until conversion</div>
                </div>
              </div>
            </div>""")

        # Exit scenarios
        exit_scenarios = [
            ("Conservative",  10_000_000,  5, "~200 paying households, 2 grocer integrations, $300k ARR"),
            ("Base case",     30_000_000,  7, "~800 households, 5 integrations, $1M ARR, regional scale"),
            ("Strong exit",   75_000_000,  7, "~2,000 households, national coverage, $3M ARR"),
            ("Strategic buy", 120_000_000, 5, "Kroger/insurer buyout — pays for data + constraint engine IP"),
        ]

        rows = []
        for label, exit_val, years, note in exit_scenarios:
            investor_val = exit_val * eq_post_sa
            irr = (investor_val / angel_invest) ** (1 / years) - 1
            multiple = investor_val / angel_invest
            rows.append((label, exit_val, investor_val, multiple, irr * 100, years, note))

        st.html("""
<div style='background:#FFFFFF;border:1px solid #D8EDD0;border-radius:10px;overflow:hidden;'>
<table style='width:100%;border-collapse:collapse;font-size:.82rem;'>
<thead>
  <tr style='background:#1E5C32;color:white;'>
    <th style='padding:10px 14px;text-align:left;'>Scenario</th>
    <th style='padding:10px 14px;text-align:right;'>Exit value</th>
    <th style='padding:10px 14px;text-align:right;'>Your return</th>
    <th style='padding:10px 14px;text-align:right;'>Multiple</th>
    <th style='padding:10px 14px;text-align:right;'>IRR</th>
  </tr>
</thead>
<tbody>""")
        for i, (label, exit_val, investor_val, multiple, irr_pct, years, note) in enumerate(rows):
            bg = "#FAFAF7" if i % 2 else "#FFFFFF"
            st.html(f"""
  <tr style='background:{bg};border-bottom:1px solid #EEF3EE;'>
    <td style='padding:9px 14px;'>
      <div style='font-weight:700;color:#1A2E1D;'>{label}</div>
      <div style='font-size:.72rem;color:#5A7A62;'>{note}</div>
    </td>
    <td style='padding:9px 14px;text-align:right;font-weight:600;color:#1A2E1D;'>${exit_val/1_000_000:.0f}M</td>
    <td style='padding:9px 14px;text-align:right;font-weight:700;color:#F28B30;'>${investor_val:,.0f}</td>
    <td style='padding:9px 14px;text-align:right;font-weight:700;color:#3A8C4E;'>{multiple:.1f}×</td>
    <td style='padding:9px 14px;text-align:right;font-weight:700;color:#3A8C4E;'>{irr_pct:.0f}%</td>
  </tr>""")
        st.html("</tbody></table></div>")
        st.caption(f"Returns calculated on ${angel_invest:,.0f} investment · {eq_post_sa*100:.1f}% equity post-dilution · IRR over stated years. Illustrative projections only.")

else:  # Strategic Acquirer
    st.html("#### Strategic acquirer — what you're buying and what it costs")

    acq_col1, acq_col2 = st.columns([1, 2])
    with acq_col1:
        arr_target = st.select_slider(
            "WhollyFare ARR at acquisition",
            options=[500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000],
            value=2_000_000,
            format_func=lambda v: f"${v/1_000_000:.1f}M ARR",
        )
        multiple_choice = st.select_slider(
            "Revenue multiple you pay",
            options=[5, 8, 10, 12, 15, 18],
            value=10,
            format_func=lambda v: f"{v}×",
        )
        angel_raised = st.select_slider(
            "Angel capital raised by acquisition",
            options=[0, 250_000, 500_000, 1_000_000, 2_000_000],
            value=500_000,
            format_func=lambda v: f"${v:,.0f}" if v > 0 else "None",
        )

    with acq_col2:
        acq_price     = arr_target * multiple_choice
        # Rough angel ownership at acquisition (post seed dilution): angel_raised / (valuation_cap * 1.2)
        angel_pct     = min((angel_raised / 3_500_000) * 0.85, 0.25) if angel_raised > 0 else 0
        tim_pct       = 1.0 - angel_pct
        tim_payout    = acq_price * tim_pct
        angel_payout  = acq_price * angel_pct
        households_est = int(arr_target / 280)  # ~$280 ARPU (mix of tiers)

        st.html(
            f"""<div style='background:#FFFFFF;border:1px solid #D8EDD0;border-radius:10px;
                            padding:18px 24px;margin-bottom:16px;'>
              <div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                          color:#B8860B;margin-bottom:12px;'>Acquisition snapshot</div>
              <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;'>
                <div>
                  <div style='font-size:1.8rem;font-weight:800;color:#0A0F0D;'>${acq_price/1_000_000:.0f}M</div>
                  <div style='font-size:.76rem;color:#5A7A62;'>acquisition price<br>({multiple_choice}× ARR)</div>
                </div>
                <div>
                  <div style='font-size:1.8rem;font-weight:800;color:#3A8C4E;'>${tim_payout/1_000_000:.1f}M</div>
                  <div style='font-size:.76rem;color:#5A7A62;'>Tim's payout<br>({tim_pct*100:.0f}% ownership)</div>
                </div>
                <div>
                  <div style='font-size:1.8rem;font-weight:800;color:#F28B30;'>{households_est:,}</div>
                  <div style='font-size:.76rem;color:#5A7A62;'>est. active households<br>at that ARR</div>
                </div>
              </div>
            </div>""")

        if angel_raised > 0:
            angel_multiple = angel_payout / angel_raised if angel_raised > 0 else 0
            st.html(
                f"""<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:10px;
                                padding:14px 22px;margin-bottom:12px;'>
                  <div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                              color:#BF5E00;margin-bottom:8px;'>Angel return at this exit</div>
                  <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;'>
                    <div>
                      <div style='font-size:1.4rem;font-weight:800;color:#0A0F0D;'>${angel_payout:,.0f}</div>
                      <div style='font-size:.76rem;color:#5A7A62;'>angel payout</div>
                    </div>
                    <div>
                      <div style='font-size:1.4rem;font-weight:800;color:#F28B30;'>{angel_multiple:.1f}×</div>
                      <div style='font-size:.76rem;color:#5A7A62;'>return multiple</div>
                    </div>
                    <div>
                      <div style='font-size:1.4rem;font-weight:800;color:#3A8C4E;'>{angel_pct*100:.1f}%</div>
                      <div style='font-size:.76rem;color:#5A7A62;'>angel ownership at exit</div>
                    </div>
                  </div>
                </div>""")

        st.html(f"""
<div style='background:#FFFFFF;border:1px solid #D8EDD0;border-radius:10px;padding:16px 20px;'>
  <div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:10px;'>What you're acquiring at ${acq_price/1_000_000:.0f}M</div>
  {''.join(f"<div style='font-size:.82rem;color:#1A2E1D;padding:5px 0;border-bottom:1px solid #EEF3EE;'><span style='color:#3A8C4E;margin-right:6px;'>✓</span>{item}</div>" for item in [
      f"~{households_est:,} verified active households with savings history",
      "Constraint engine IP — only commercially honest one in the market",
      "8+ weeks of real household receipt data per pilot family",
      "Grocer API integration pipeline (Kroger live; Food Lion, Aldi, HT in scope)",
      "The Sincere Strategy® brand — trust built one household at a time",
      "Multi-tier subscription revenue with proven upgrade path",
      "Tim Hislop as a committed operator under transition terms",
  ])}
</div>""")
        st.caption("Acquisition modeling is illustrative. Ownership percentages assume convertible note structure at $3.5M cap, 20% dilution at Series A if applicable.")

st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 13. CONTROL ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
st.html('<div class="inv-section-label">Control Architecture</div>')
st.html("### Tim keeps control. This is how it works.")
st.markdown("""
Control is not a negotiating point — it is a design decision. WhollyFare's value is inseparable
from the Sincere Strategy, which requires a founder who cannot be overruled on paid placements,
health constraint compromises, or data monetization. The structures below preserve that.
""")

ctrl_col1, ctrl_col2 = st.columns([3, 2])
with ctrl_col1:
    scenarios = [
        ("Bootstrap / Grants only",      100, 0,  "Tim: 100% economic · 100% voting"),
        ("$250k angel (convertible note)", 96, 4,  "Tim: ~96% economic · 100% voting until conversion"),
        ("$500k angel (convertible note)", 92, 8,  "Tim: ~92% economic · 100% voting until conversion"),
        ("$1M angel round",               87, 13, "Tim: ~87% economic · 100% voting until conversion"),
        ("After Series A priced round",   75, 25, "Tim: ~75% economic · 95%+ voting (dual-class Class B shares)"),
        ("Mature / pre-acquisition",      70, 30, "Tim: ~70% economic · still controls strategic decisions"),
    ]
    for scenario, tim_pct, inv_pct, note in scenarios:
        st.html(
            f"""<div class="ctrl-bar">
              <div class="ctrl-scenario">{scenario}</div>
              <div class="ctrl-bar-outer">
                <div class="ctrl-bar-tim" style="width:{tim_pct}%;">Tim {tim_pct}%</div>
                {"" if inv_pct == 0 else f'<div class="ctrl-bar-inv" style="width:{inv_pct}%;left:{tim_pct}%;">Investors {inv_pct}%</div>'}
              </div>
              <div style='font-size:.74rem;color:#5A7A62;margin-top:4px;'>{note}</div>
            </div>""")

with ctrl_col2:
    st.html("""
<div style='background:linear-gradient(160deg,#0A0F0D,#0F2518);border:1px solid #3A8C4E;
            border-radius:12px;padding:24px 22px;color:white;height:100%;'>
  <div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
              color:#5DAA6A;margin-bottom:14px;'>How it's structured</div>

  <div style='font-size:.88rem;font-weight:700;color:#9FD9A8;margin-bottom:6px;'>Convertible Notes / SAFEs</div>
  <div style='font-size:.80rem;color:rgba(255,255,255,.65);line-height:1.55;margin-bottom:18px;'>
    Investors give capital now. It converts to equity <em>only when Tim triggers a priced round</em>
    (Series A) or at acquisition. Until then, Tim holds 100% of voting shares. There is no
    investor board seat, no investor veto, no timeline pressure — until Tim chooses it.
  </div>

  <div style='font-size:.88rem;font-weight:700;color:#9FD9A8;margin-bottom:6px;'>Dual-Class Shares (at Series A)</div>
  <div style='font-size:.80rem;color:rgba(255,255,255,.65);line-height:1.55;margin-bottom:18px;'>
    When Tim triggers the priced round, WhollyFare issues Class A shares (investors, 1× vote)
    and Class B shares (Tim, 10× vote). Tim can sell 25–30% of the <em>economics</em> while
    keeping 95%+ of the <em>voting power</em>. Google, Meta, and Snap all used this structure.
  </div>

  <div style='font-size:.88rem;font-weight:700;color:#9FD9A8;margin-bottom:6px;'>Acquisition Terms</div>
  <div style='font-size:.80rem;color:rgba(255,255,255,.65);line-height:1.55;'>
    If a strategic acquirer makes an offer, Tim negotiates the price and terms.
    Convertible note holders participate in the acquisition proceeds at their conversion
    rate. Tim decides when, to whom, and at what price — if at all.
  </div>
</div>
    """)

st.html("<br>")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 14. APPLICATION ROADMAP — month by month, pilot driven
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div style='font-size:0.65rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;
            color:#5DAA6A;margin-bottom:6px;'>Section 14</div>
<div style='font-size:1.45rem;font-weight:800;color:#1E5C32;margin-bottom:4px;'>
  Application Roadmap
</div>
<div style='font-size:0.88rem;color:#5A7A62;margin-bottom:14px;line-height:1.65;'>
  What we're building, when, and why — driven by real pilot data, not theory.
  Every item moves forward because a household told us it needed to.
</div>
<div style='background:#1E5C32;color:white;border-radius:10px;padding:14px 20px;margin-bottom:20px;
            font-size:0.9rem;line-height:1.65;'>
  <strong style='color:#9FD9A8;'>Charlottesville is the test bed. Not the goal.</strong><br>
  The pilot proves the model works for one family at four stores in one city.
  The roadmap shows how that model becomes the meal planning layer for any household,
  at any store, in any market in the country — built on direct API integrations with
  the grocer chains that already serve them.
</div>
""")

with st.expander("Month 1 — Hislop Family Pilot · Live Now", expanded=False):
    st.html("""
<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:14px;line-height:1.6;'>
  <strong style='color:#1E5C32;'>May 2026 · Charlottesville, VA · 1 household · 4 stores</strong><br>
  Tim, Abby, and Chas run the full flow every Sunday. Manual flyer entry. Real receipts.
  The goal is eight weeks of undeniable Found Money data.
</div>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>✅ Done</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    Core constraint engine — safety before savings<br>
    Budget optimizer + meal planner<br>
    Manual flyer entry — all 4 Cville stores<br>
    Sunday Buy-Off screen<br>
    Shopping list — mobile-first, interactive checkboxes<br>
    Found Money Ledger + CSV export
  </div>
</div>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#F28B30;margin-bottom:8px;'>🔄 In Progress</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    End-to-end flow without Tim in the room<br>
    Pilot onboarding guide<br>
    Receipt-to-engine accuracy tracking<br>
    Constraint edge cases from real household use
  </div>
</div>
</div>
<div style='background:#F0FBF0;border-left:3px solid #5DAA6A;border-radius:0 8px 8px 0;
            padding:12px 16px;margin-top:14px;font-size:0.84rem;color:#3A8C4E;
            font-style:italic;line-height:1.55;'>
  "I didn't realise how much we were spending at Kroger just because it was convenient.
  Seeing the Found Money number on Sunday morning actually changed how I think about where we shop."
  <div style='font-size:0.72rem;color:#5A7A62;margin-top:4px;font-style:normal;font-weight:600;'>
    — Abby · Pilot Week 1
  </div>
</div>
    """)

with st.expander("Months 2–3 — First Wave · 5–10 Pilot Households", expanded=False):
    st.html("""
<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:14px;line-height:1.6;'>
  <strong style='color:#1E5C32;'>June – July 2026 · Friends and family recruited by Tim</strong><br>
  What breaks at 1 household stays a quirk. What breaks at 5 becomes a pattern.
  Each new household is a different constraint profile, a different store mix, a different budget.
</div>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Features driven by pilot feedback</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    Multi-household account structure<br>
    Allergy household mode — visible safety, not just rules<br>
    Ingredient rejection transparency (Sincere Strategy)<br>
    Store coverage beyond Charlottesville<br>
    Guided onboarding — setup in under 10 minutes alone<br>
    In-app meal feedback ("we hated the stir-fry")
  </div>
</div>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Infrastructure to support 5–10 households</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    Simple data persistence — SQLite or hosted Postgres<br>
    Basic authentication — email + password<br>
    Weekly Found Money summary email (no marketing)<br>
    Error monitoring — know when the engine fails
  </div>
</div>
</div>
    """)

with st.expander("Months 4–5 — Beta Expansion · 20–30 Households", expanded=False):
    st.html("""
<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:14px;line-height:1.6;'>
  <strong style='color:#1E5C32;'>August – September 2026 · Broader Virginia / mid-Atlantic</strong><br>
  Twenty households is not a lot of users. It is a lot of data.
  By this point we know which features matter and which ones we thought would matter.
</div>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Application features</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    PDF circular parsing — Kroger + Food Lion production-ready<br>
    Meal ratings + preference memory — Week 8 better than Week 1<br>
    Pantry awareness (basic) — "we already have olive oil"<br>
    Health Guard tier — diabetes-aware, CKD-safe, MCAS avoidance
  </div>
</div>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Infrastructure</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.8;'>
    PostgreSQL — production-grade persistence<br>
    OAuth authentication (Google / Apple)<br>
    Architecture transition plan — Streamlit → React + FastAPI<br>
    First infrastructure engineer hire
  </div>
</div>
</div>
    """)

with st.expander("Month 6–12 — Regional Scale · API Integrations · Post-Investment Build", expanded=False):
    st.html("""
<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:14px;line-height:1.6;'>
  <strong style='color:#1E5C32;'>October 2026 – April 2027 · Mid-Atlantic → Southeast</strong><br>
  This is where manual entry ends. API integrations with major chains replace the clipboard.
  The engine that Tim ran for eight weeks in Charlottesville now runs automatically
  for hundreds of households across multiple markets — same logic, same Sincere Strategy,
  no manual work required.
</div>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px;'>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Grocer API integrations</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.85;'>
    <strong>Kroger</strong> — Developer API, live weekly sale data, loyalty pricing<br>
    <strong>Publix</strong> — BOGO detection, weekly ad feed<br>
    <strong>Safeway / Albertsons</strong> — Just4U rewards, digital circular<br>
    <strong>Aldi</strong> — ALDI Finds + weekly specials<br>
    <strong>Walmart Grocery</strong> — Rollback pricing, pickup integration<br>
    <strong>Harris Teeter</strong> — VIC card pricing, digital coupons<br>
    <strong>Giant / Stop &amp; Shop</strong> — Northeast expansion
  </div>
</div>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Architecture + team</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.85;'>
    React + FastAPI rewrite — production-grade, not Streamlit<br>
    Infrastructure engineer — cloud, database, API pipeline<br>
    Front-end developer — mobile-first React, design system<br>
    Back-end developer — FastAPI, engine optimisation<br>
    Grocer partnerships lead — API agreements, data access<br>
    Health systems BD — clinical licensing, HIPAA path<br>
    PostgreSQL + Redis — real persistence, real performance
  </div>
</div>
</div>
<div style='display:grid;grid-template-columns:1fr 1fr;gap:20px;'>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>Marketing opportunities</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.85;'>
    <strong>Zero paid placements</strong> — this is itself a marketing story<br>
    Household word-of-mouth — Found Money travels<br>
    Health system referrals — clinicians recommend to patients<br>
    Grocer loyalty program co-marketing — the chains benefit too<br>
    Food bank &amp; community org partnerships — mission-aligned distribution<br>
    Regional press — "the app that fights inflation one grocery run at a time"
  </div>
</div>
<div>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:8px;'>The data package for investors</div>
  <div style='font-size:0.84rem;color:#1A2E1D;line-height:1.85;'>
    Avg. Found Money per household per week<br>
    Week-over-week retention across cohorts<br>
    Engine accuracy vs. actual receipts<br>
    Which household types benefit most<br>
    CAC vs. LTV by acquisition channel<br>
    Cost to serve per household per month
  </div>
</div>
</div>
    """)

with st.expander("Months 12–18+ — National · Any Household, Any Store, Any Market", expanded=False):
    st.html("""
<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:16px;line-height:1.6;'>
  <strong style='color:#1E5C32;'>2027 and beyond · 50,000+ households · $2M+ ARR target</strong><br>
  The product that worked in Charlottesville works identically in Austin, Portland, Chicago,
  and Miami — because it's built on local store data, not a national average.
  Every market has different chains, different sale cycles, different prices.
  WhollyFare's engine handles all of it. That's the moat.
</div>
<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;'>
<div style='background:#E3F4E8;border-radius:10px;padding:16px;'>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:10px;'>Product at national scale</div>
  <div style='font-size:0.82rem;color:#1A2E1D;line-height:1.8;'>
    15+ grocer chain integrations<br>
    Full recipe library with step-by-step instructions<br>
    Pantry tracking — reduce food waste, not just cost<br>
    Cuisine preference memory across weeks<br>
    Meal type selection — weeknight, date night, batch cook<br>
    Family meal history — "we loved this in March"
  </div>
</div>
<div style='background:#E3F4E8;border-radius:10px;padding:16px;'>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:10px;'>Geographic expansion logic</div>
  <div style='font-size:0.82rem;color:#1A2E1D;line-height:1.8;'>
    Each new market requires: grocer API access or data agreement, constraint data
    for regional health conditions, and at least one anchor pilot household to verify
    local accuracy before broad launch.<br><br>
    <strong>Charlottesville proved the model.<br>
    The model travels. The data makes it local.</strong>
  </div>
</div>
<div style='background:#E3F4E8;border-radius:10px;padding:16px;'>
  <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#3A8C4E;margin-bottom:10px;'>Revenue at scale</div>
  <div style='font-size:0.82rem;color:#1A2E1D;line-height:1.8;'>
    50,000 households × $19/mo Health Guard = $950k MRR<br>
    Health system licensing — $50k–$500k annual contracts<br>
    No ads. No affiliate deals. No data sales.<br>
    Subscription revenue only — aligned with the household, always.<br><br>
    <strong>The Sincere Strategy is the business model.</strong>
  </div>
</div>
</div>
    """)

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 15. THE CLOSE — open door, not a round
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class="inv-ask-hero">
  <div class="ask-eyebrow">The Invitation</div>
  <h2>WhollyFare is happening.<br>The door is open.</h2>
  <div class="ask-desc">
    I am not running a fundraising process. I am building a product, logging receipts,
    and recruiting pilot households one conversation at a time. If you see what I see —
    that American families deserve a meal planner that works for them, not for its advertisers —
    the door is open at every level described above.<br><br>
    Angel partner. Strategic grocer or health system. Future acquirer who wants to understand
    what's being built. All of it is a conversation I will have honestly, without pressure,
    on a timeline that respects the work.<br><br>
    <strong>I am going to preach the Sincere Strategy from the treetops.
    The question is whether you want to be positioned when it lands.</strong>
  </div>
  <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:16px;">
    <a href="mailto:tim.hislop@gmail.com?subject=WhollyFare — Angel Partner Interest"
       style="display:inline-block;background:#3A8C4E;color:white;font-weight:700;
              font-size:.92rem;padding:14px 28px;border-radius:8px;text-decoration:none;">
      📧 Angel Partner conversation
    </a>
    <a href="mailto:tim.hislop@gmail.com?subject=WhollyFare — Strategic Partnership"
       style="display:inline-block;background:transparent;color:#7EB3E8;font-weight:700;
              font-size:.92rem;padding:14px 28px;border-radius:8px;text-decoration:none;
              border:2px solid #3A6EA8;">
      📧 Strategic Partnership
    </a>
    <a href="mailto:tim.hislop@gmail.com?subject=WhollyFare — Acquisition Interest"
       style="display:inline-block;background:transparent;color:#E8C060;font-weight:700;
              font-size:.92rem;padding:14px 28px;border-radius:8px;text-decoration:none;
              border:2px solid #B8860B;">
      📧 Acquisition conversation
    </a>
  </div>
  <div style="font-size:.85rem;opacity:.55;letter-spacing:.03em;">
    Sentir Solutions&#174; LLC &nbsp;·&nbsp; Charlottesville, VA &nbsp;·&nbsp; tim.hislop@gmail.com
  </div>
</div>
""")

st.html("<br>")
st.caption(
    "This page is a working Proof of Concept built in Streamlit. Financial projections are "
    "illustrative estimates, not guarantees. IRR and return calculations assume specific exit "
    "scenarios that may not occur. Ownership percentages are approximate and depend on final "
    "instrument terms. This is not a securities offering. WhollyFare® is a product of "
    "Sentir Solutions® LLC. All rights reserved."
)
