"""
9_App_Roadmap.py — WhollyFare Application Roadmap

This is NOT the investor vision deck. That's page 8.
This is the ground-level build plan: what we're actually building,
month by month, driven by what real households tell us is broken,
missing, or worth doing next.

Every feature on this list was earned — either by Tim's family running
the pilot, or by the first wave of households telling us what they need.
No theoretical roadmapping. No features added because they sounded good.

POC vs. PRODUCTION
-------------------
POC:  Status badges are hardcoded. Feedback quotes are from real pilot
      conversations but entered manually.
PROD: Status pulled from a project tracker (Linear / GitHub Projects).
      Feedback entries linked to household IDs and week numbers.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="Application Roadmap · WhollyFare",
    page_icon="🔨",
    layout="wide",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Application Roadmap",
    "What we're building, when, and why — driven by real pilot data, not theory.",
)

# ── Page CSS ──────────────────────────────────────────────────────────────────
st.html("""
<style>
.rm-phase {
    border-radius: 14px;
    padding: 26px 28px 22px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
}
.rm-live    { background: linear-gradient(135deg, #142B1C 0%, #1E5C32 100%); }
.rm-next    { background: linear-gradient(135deg, #1A2C3D 0%, #1E4A6A 100%); }
.rm-beta    { background: linear-gradient(135deg, #2D1F00 0%, #5C3D00 100%); }
.rm-invest  { background: linear-gradient(135deg, #1A1040 0%, #2D1A6E 100%); }

.rm-phase-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.rm-phase-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: white;
    margin-bottom: 4px;
    line-height: 1.15;
}
.rm-phase-dates {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.55);
    margin-bottom: 16px;
    font-weight: 500;
}
.rm-phase-goal {
    font-size: 0.92rem;
    color: rgba(255,255,255,0.82);
    line-height: 1.6;
    max-width: 640px;
    margin-bottom: 0;
}

/* Status pills */
.status-done     { background:#1E5C32; color:#9FD9A8; }
.status-building { background:#5C3A00; color:#FFB74D; }
.status-planned  { background:#1A2E40; color:#81D4FA; }
.status-pilot    { background:#4A1A5C; color:#CE93D8; }

.rm-pill {
    display:inline-block;
    font-size:10px;
    font-weight:700;
    letter-spacing:0.08em;
    text-transform:uppercase;
    padding:3px 9px;
    border-radius:20px;
    margin-right:6px;
    vertical-align:middle;
}

/* Feature row */
.rm-feature {
    display:flex;
    align-items:flex-start;
    gap:12px;
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,0.07);
}
.rm-feature:last-child { border-bottom: none; }
.rm-feature-name {
    font-size:0.9rem;
    font-weight:600;
    color:white;
    line-height:1.3;
}
.rm-feature-why {
    font-size:0.78rem;
    color:rgba(255,255,255,0.55);
    margin-top:2px;
    line-height:1.4;
}

/* Feedback card */
.rm-feedback {
    background: rgba(255,255,255,0.07);
    border-left: 3px solid rgba(255,255,255,0.25);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-top: 4px;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.78);
    font-style: italic;
    line-height: 1.55;
}
.rm-feedback-attr {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    margin-top:6px;
    font-style: normal;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* Progress bar */
.rm-progress-track {
    background: rgba(255,255,255,0.12);
    border-radius: 4px;
    height: 6px;
    margin: 10px 0 4px;
    overflow: hidden;
}
.rm-progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}
</style>
""")

# ── Intro ─────────────────────────────────────────────────────────────────────
st.html("""
<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
            padding:16px 20px;margin-bottom:24px;'>
  <div style='font-size:0.95rem;font-weight:700;color:#1E5C32;margin-bottom:4px;'>
    This roadmap is driven by the pilot, not a whiteboard.
  </div>
  <div style='font-size:0.85rem;color:#3A8C4E;line-height:1.6;'>
    Every item below is on the list because a real household hit a real wall.
    Features move from Planned → Building → Done when the pilot data says they matter —
    not when they sound impressive in a deck.
  </div>
</div>
""")


# ══════════════════════════════════════════════════════════════════════════════
# MONTH 1 — LIVE NOW
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='rm-phase rm-live'>
  <div class='rm-phase-label' style='color:#9FD9A8;'>Month 1 — Live Now</div>
  <div class='rm-phase-title'>Hislop Family Pilot</div>
  <div class='rm-phase-dates'>May 2026 · Charlottesville, VA · 1 household · 4 stores</div>
  <div class='rm-phase-goal'>
    Tim, Abby, and Chas run the full flow every Sunday. Manual flyer entry.
    Real receipts. The goal is eight weeks of undeniable Found Money data —
    the kind of numbers that end a conversation with an investor before it starts.
  </div>
</div>
""")

with st.expander("Month 1 — what's built, what's in progress, what the pilot is teaching us", expanded=True):
    col_done, col_building = st.columns(2)

    with col_done:
        st.html("""
<div style='margin-bottom:8px;'>
  <span style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
               text-transform:uppercase;color:#3A8C4E;'>Completed</span>
</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Core constraint engine</div>
    <div class='rm-feature-why'>Filters every ingredient against household allergies, diagnoses,
    and lifestyle tags before the optimizer sees it. Safety first, always.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Budget optimizer + meal planner</div>
    <div class='rm-feature-why'>Scores sale-priced ingredients by nutrition density, selects the
    best mix, and assembles five dinners for the week.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Manual flyer entry — all 4 Cville stores</div>
    <div class='rm-feature-why'>Kroger, Food Lion, Aldi, Harris Teeter. Type items
    from the weekly circular. Reliable for the pilot. Slow by design — we learn more
    from doing it manually first.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Sunday Buy-Off screen</div>
    <div class='rm-feature-why'>One number, one decision, one tap. The emotional
    centrepiece of the week. Locks in the plan and generates the shopping list.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Shopping list by store — mobile-first</div>
    <div class='rm-feature-why'>Centred layout, interactive checkboxes, progress bar.
    Designed to be usable in a grocery store aisle on a phone.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Found Money Ledger + CSV export</div>
    <div class='rm-feature-why'>Running weekly savings record. Receipt upload.
    Eight weeks of this data is the investor argument.</div>
  </div>
</div>
        """)

    with col_building:
        st.html("""
<div style='margin-bottom:8px;'>
  <span style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
               text-transform:uppercase;color:#F28B30;'>In Progress / Learning</span>
</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>End-to-end flow without hand-holding</div>
    <div class='rm-feature-why'>Can Abby run a full Sunday cycle without Tim in the room?
    That's the bar. We're not there yet. Every point of confusion is a bug.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Pilot onboarding guide</div>
    <div class='rm-feature-why'>A simple doc or in-app walkthrough so pilot friends
    can set up and run week one without a phone call to Tim.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Receipt-to-ledger accuracy</div>
    <div class='rm-feature-why'>Is what the engine predicted close to what the receipt says?
    We're tracking the delta every week. That gap is what we fix in Month 2.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name'>Constraint edge cases</div>
    <div class='rm-feature-why'>Chas has specific preferences that don't fit clean
    category labels. Real households are messier than the data model expects.
    Every exception we find now is a rule we add before we scale.</div>
  </div>
</div>
        """)

    st.html("""
<div class='rm-feedback'>
  "I didn't realise how much we were spending at Kroger just because it was convenient.
  Seeing the Found Money number on Sunday morning actually changed how I think about
  where we shop."
  <div class='rm-feedback-attr'>— Abby · Pilot Week 1</div>
</div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# MONTHS 2-3 — FIRST WAVE
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='rm-phase rm-next' style='margin-top:16px;'>
  <div class='rm-phase-label' style='color:#81D4FA;'>Months 2–3 — Building Now</div>
  <div class='rm-phase-title'>First Wave · 5–10 Pilot Households</div>
  <div class='rm-phase-dates'>June – July 2026 · Charlottesville area · Friends and family recruited by Tim</div>
  <div class='rm-phase-goal'>
    What breaks at 1 household stays a quirk. What breaks at 5 households becomes a pattern.
    The first wave tells us what to fix before we grow further.
    Each new household is a different set of constraints, a different store mix,
    a different definition of "this week's budget."
  </div>
</div>
""")

with st.expander("Months 2–3 — what the first wave is expected to drive", expanded=False):
    col_a, col_b = st.columns(2)

    with col_a:
        st.html("""
<div style='margin-bottom:8px;'>
  <span style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
               text-transform:uppercase;color:#81D4FA;'>Planned — driven by pilot feedback</span>
</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Multi-household account structure</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Right now the app is Tim's family.
    Five households means five separate setups, five store configurations, five constraint profiles.
    Session state isn't enough. We need the skeleton of a real account model.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Allergy household mode</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>One of our first pilot targets is a
    household managing multiple food allergies. The constraint engine handles them,
    but the UI needs to make that safety visible and trustworthy — not just a list of rules.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Store coverage outside Charlottesville</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Pilot friends may shop at Wegmans,
    Giant, Lidl. The engine works for any store — the manual entry flow just needs to
    handle store names it hasn't seen before gracefully.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Ingredient rejection transparency</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>The Sincere Strategy says every
    rejection is logged and shown. Right now that data exists in the engine output.
    We need to surface it: "Chicken was excluded because of Chas's egg sensitivity."</div>
  </div>
</div>
        """)

    with col_b:
        st.html("""
<div style='margin-bottom:8px;'>
  <span style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
               text-transform:uppercase;color:#81D4FA;'>Infrastructure to support 5–10 households</span>
</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Simple data persistence</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Session state clears on refresh.
    That's fine for 1 household running a demo. Not fine for 5 households building
    8 weeks of history. We need the simplest possible persistence layer —
    SQLite locally or a hosted Postgres, depending on how quickly we move.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Household onboarding flow</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>A pilot friend should be able to
    set up their household in under 10 minutes with no help from Tim.
    Currently the Household Setup page works but the flow isn't guided enough
    for someone doing it cold.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Weekly summary email (optional)</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>A simple "here's your Found Money
    this week" email keeps pilot households engaged between Sundays.
    No marketing. Just their own data.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Feedback capture in-app</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>A simple thumbs up/down on each
    meal and a free-text "what would you change?" field. The pilot data is only as
    good as what households are willing to tell us.</div>
  </div>
</div>
        """)

    st.html("""
<div style='background:rgba(255,255,255,0.07);border-radius:8px;padding:14px 18px;margin-top:8px;'>
  <div style='font-size:0.8rem;color:rgba(255,255,255,0.6);line-height:1.6;'>
    <strong style='color:rgba(255,255,255,0.85);'>What we're watching:</strong>
    Are households completing their first Sunday cycle alone? Are they coming back
    the following week? Is the Found Money number surprising them?
    If the answer to all three is yes, the product works. If not — that's the next month's roadmap.
  </div>
</div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# MONTHS 4-5 — BETA EXPANSION
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='rm-phase rm-beta' style='margin-top:16px;'>
  <div class='rm-phase-label' style='color:#FFB74D;'>Months 4–5 — Planned</div>
  <div class='rm-phase-title'>Beta Expansion · 20–30 Households</div>
  <div class='rm-phase-dates'>August – September 2026 · Broader Virginia / mid-Atlantic</div>
  <div class='rm-phase-goal'>
    This is where the product either holds together or shows us what needs to change.
    Twenty households is not a lot of users. It is a lot of data.
    By this point we should know: which constraints are most common,
    which stores are hardest to handle, and which features households actually use
    versus the ones we thought they'd want.
  </div>
</div>
""")

with st.expander("Months 4–5 — what beta expansion requires", expanded=False):
    st.html("""
<div style='display:grid;grid-template-columns:1fr 1fr;gap:24px;'>
<div>
<div style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
            color:#FFB74D;margin-bottom:12px;'>Application features</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>PDF circular parsing — Kroger + Food Lion</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Manual entry doesn't scale to 30 households.
    The PDF parsers exist in the codebase. At this stage we need them to be reliable enough
    that households can use them as their primary path, not just a fallback.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Meal ratings + preference memory</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>If a household says "we hated
    the stir-fry," the planner should remember that. Preference memory is the
    feature that makes Week 8 better than Week 1 — and makes switching away feel costly.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Pantry awareness (basic)</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>
    "We already have olive oil — don't buy it this week."
    Not full pantry tracking. Just a way to flag items the household always has
    so the shopping list doesn't repeat them.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Health Guard tier features</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Diabetes-aware meal scoring.
    CKD-safe phosphorus limits. MCAS trigger avoidance. The constraint engine
    handles the hard rules — the Health Guard tier adds proactive guidance
    and transparency about why each meal is safe for each household member.</div>
  </div>
</div>
</div>

<div>
<div style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
            color:#FFB74D;margin-bottom:12px;'>Infrastructure</div>

<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Hosted database (PostgreSQL)</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Households, plans, ledger history,
    and feedback need to persist somewhere that isn't a browser tab.
    This is the point where we move from POC to a product people can rely on.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Basic authentication</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Thirty households means thirty
    separate logins. Email + password minimum.
    OAuth (Google/Apple) as soon as it makes sense.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Monitoring + error reporting</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>At 30 households Tim can't watch
    every session. We need to know when the engine fails, when the PDF parser
    returns zero items, and when households drop off mid-flow.</div>
  </div>
</div>
<div class='rm-feature'>
  <div>
    <div class='rm-feature-name' style='color:white;'>Architecture transition planning</div>
    <div class='rm-feature-why' style='color:rgba(255,255,255,0.55);'>Streamlit is the right tool for
    the pilot. React + FastAPI is the right tool for scale.
    By Month 5 we should know what we're keeping, what we're rewriting,
    and what the migration plan looks like. This is also the point
    where we need our first infrastructure engineer.</div>
  </div>
</div>
</div>
</div>
    """)


# ══════════════════════════════════════════════════════════════════════════════
# MONTH 6+ — INVESTMENT MILESTONE
# ══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class='rm-phase rm-invest' style='margin-top:16px;'>
  <div class='rm-phase-label' style='color:#CE93D8;'>Month 6+ — The Milestone</div>
  <div class='rm-phase-title'>The Data Package · Investment-Ready</div>
  <div class='rm-phase-dates'>October 2026 and beyond · The number that gets Tim in the room</div>
  <div class='rm-phase-goal'>
    Six months of pilot data. 20–30 households. Real Found Money numbers.
    Retention metrics. Constraint compliance records. Feedback transcripts.
    This is not a pitch deck — it's evidence. The roadmap from here is written by the data,
    not by Tim alone.
  </div>
</div>
""")

with st.expander("Month 6+ — what the investment milestone looks like", expanded=False):
    c1, c2, c3 = st.columns(3)

    with c1:
        st.html("""
<div style='background:rgba(255,255,255,0.06);border-radius:10px;padding:16px;height:100%;'>
  <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#CE93D8;margin-bottom:12px;'>The data package</div>
  <div style='font-size:0.85rem;color:rgba(255,255,255,0.75);line-height:1.65;'>
    Average Found Money per household per week<br><br>
    Week-over-week retention across pilot cohort<br><br>
    Constraint engine accuracy vs. actual receipts<br><br>
    Which household types benefit most (allergy, budget, health condition)<br><br>
    Cost to serve per household per month
  </div>
</div>
        """)

    with c2:
        st.html("""
<div style='background:rgba(255,255,255,0.06);border-radius:10px;padding:16px;height:100%;'>
  <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#CE93D8;margin-bottom:12px;'>What gets built next</div>
  <div style='font-size:0.85rem;color:rgba(255,255,255,0.75);line-height:1.65;'>
    React + FastAPI rewrite — production-grade architecture<br><br>
    Kroger API live integration — no more manual entry<br><br>
    Full recipe library — complete meal instructions, not just ingredient lists<br><br>
    Health system B2B licensing — hospitals and clinics as distribution partners<br><br>
    15+ grocer chains — mid-Atlantic to national coverage
  </div>
</div>
        """)

    with c3:
        st.html("""
<div style='background:rgba(255,255,255,0.06);border-radius:10px;padding:16px;height:100%;'>
  <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
              color:#CE93D8;margin-bottom:12px;'>The team this requires</div>
  <div style='font-size:0.85rem;color:rgba(255,255,255,0.75);line-height:1.65;'>
    Infrastructure engineer — cloud architecture, database, DevOps<br><br>
    Front-end developer — React, mobile-first, design system<br><br>
    Back-end developer — FastAPI, engine optimisation, integrations<br><br>
    Grocer partnerships lead — circular data agreements, API access<br><br>
    Health systems BD — clinical licensing, HIPAA compliance path
  </div>
</div>
        """)

    st.html("""
<div style='background:rgba(206,147,216,0.1);border:1px solid rgba(206,147,216,0.25);
            border-radius:10px;padding:14px 20px;margin-top:16px;'>
  <div style='font-size:0.88rem;color:rgba(255,255,255,0.8);line-height:1.6;'>
    <strong style='color:#CE93D8;'>The honest version of Month 6:</strong>
    The roadmap written here will be wrong in some ways. That's not a problem —
    it means the pilot data did its job. What we're building toward is a product
    that households won't give up once they've used it for eight weeks.
    Everything else follows from that.
  </div>
</div>
    """)


st.divider()

# ── Bottom callout ────────────────────────────────────────────────────────────
st.html("""
<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;
            padding:16px 20px;display:flex;justify-content:space-between;
            align-items:center;flex-wrap:wrap;gap:12px;'>
  <div>
    <div style='font-size:0.95rem;font-weight:700;color:#1E5C32;'>
      Want to be part of the pilot?
    </div>
    <div style='font-size:0.82rem;color:#3A8C4E;margin-top:2px;'>
      The roadmap moves faster with more households. Each new family makes the product better for all of them.
    </div>
  </div>
  <div style='font-size:0.82rem;color:#1E5C32;font-weight:600;'>
    <a href='mailto:tim.hislop@gmail.com?subject=WhollyFare Pilot — I want in'
       style='color:#1E5C32;text-decoration:none;background:#D8EDD0;
              padding:8px 16px;border-radius:8px;'>
      → Get in touch
    </a>
  </div>
</div>
""")

st.html("<br>")
st.page_link("pages/7_Investor.py", label="← Investor Brief")
st.page_link("pages/8_Roadmap.py",  label="→ Product Vision Roadmap")
