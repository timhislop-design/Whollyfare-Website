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
    initial_sidebar_state="collapsed",   # collapsed on landing, full nav opens on click
)

state.init()

# ── DB load on home page ───────────────────────────────────────────────────────
# If authenticated and no household in session yet, restore from DB.
if state.is_authenticated() and st.session_state.get("household_db") is None:
    state.load_household()
if st.session_state.get("household_db") and st.session_state.get("household") is None:
    profile = state.db_dict_to_profile(st.session_state["household_db"])
    if profile:
        st.session_state["household"] = profile

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    style.sidebar_nav()   # full branded nav + auth widget — same on every page

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

    # ── CSS + page treatment ──────────────────────────────────────────────────
    st.html("""
    <style>
      .block-container { padding-top: 0.5rem !important; }

      [data-testid="stAppViewContainer"] > .main {
        background: #FAFAF7;
      }

      [data-testid="stSidebarNav"] { display: none !important; }

      /* Smooth lift on hover for any wf-card class */
      .wf-card {
        transition: transform 0.18s ease, box-shadow 0.18s ease !important;
      }
      .wf-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 16px 48px rgba(30,92,50,0.16) !important;
      }

      /* Tier detail expand panel */
      .wf-detail {
        animation: slideDown 0.22s ease;
      }
      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      /* Hide hero brand icon on mobile so it doesn't overlap text */
      @media (max-width: 768px) {
        .wf-hero-icon { display: none !important; }
      }
    </style>
    """)

    # ── Brand header ──────────────────────────────────────────────────────────
    st.html("""
    <div style='display:flex;align-items:center;gap:10px;margin-top:10px;margin-bottom:16px;
                padding:10px 18px;background:rgba(255,255,255,0.55);
                backdrop-filter:blur(6px);border-radius:10px;
                border:1px solid rgba(93,170,106,0.22);'>
      <svg width="26" height="26" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg">
        <line x1="14" y1="46" x2="14" y2="10" stroke="#3A8C4E" stroke-width="2.8" stroke-linecap="round"/>
        <line x1="9"  y1="10" x2="9"  y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="14" y1="10" x2="14" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <line x1="19" y1="10" x2="19" y2="24" stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
        <ellipse cx="36" cy="26" rx="13" ry="8.5" fill="#5DAA6A" transform="rotate(-28 36 26)"/>
        <line x1="24" y1="35" x2="46" y2="18" stroke="#9FD9A8" stroke-width="1.3" stroke-linecap="round"/>
      </svg>
      <span style='font-size:1.05rem;font-weight:700;color:#1E5C32;'>WhollyFare</span>
      <span style='color:#C8DFC8;margin:0 4px;'>·</span>
      <span style='font-size:0.82rem;color:#666;'>a <a href="https://sentir-solutions.com" target="_blank"
           style="color:#3A8C4E;font-weight:600;text-decoration:none;">Sentir Solutions</a>&#174; Company</span>
    </div>
    """)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.html("""
    <div style='position:relative;overflow:hidden;
                background:linear-gradient(140deg,#142B1C 0%,#1E5C32 55%,#2D7A45 100%);
                border-radius:18px;padding:54px 52px 50px;margin-bottom:10px;'>

      <!-- Decorative fork+leaf — right side, vertically centred in text block, background only -->
      <svg class='wf-hero-icon' style='position:absolute;right:60px;top:50%;transform:translateY(-55%);
                  opacity:0.80;pointer-events:none;'
           width="200" height="200" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg"
           aria-hidden="true">
        <!-- Fork handle -->
        <line x1="14" y1="46" x2="14" y2="10" stroke="#9FD9A8" stroke-width="2.8" stroke-linecap="round"/>
        <!-- Fork tines -->
        <line x1="9"  y1="10" x2="9"  y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <line x1="14" y1="10" x2="14" y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <line x1="19" y1="10" x2="19" y2="24" stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
        <!-- Leaf body -->
        <ellipse cx="36" cy="26" rx="13" ry="8.5" fill="#5DAA6A" transform="rotate(-28 36 26)"/>
        <!-- Leaf midrib -->
        <line x1="24" y1="35" x2="46" y2="18" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
        <!-- Leaf veins -->
        <line x1="30" y1="32" x2="40" y2="20" stroke="white" stroke-width="0.7" stroke-linecap="round" opacity="0.6"/>
        <line x1="35" y1="28" x2="44" y2="23" stroke="white" stroke-width="0.7" stroke-linecap="round" opacity="0.6"/>
      </svg>

      <!-- Small top badge -->
      <div style='display:inline-flex;align-items:center;gap:7px;
                  background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);
                  border-radius:20px;padding:5px 14px;margin-bottom:20px;'>
        <span style='width:7px;height:7px;background:#5DAA6A;border-radius:50%;display:inline-block;'></span>
        <span style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;
                     text-transform:uppercase;color:rgba(255,255,255,0.85);'>
          Smart meal planning &nbsp;·&nbsp; Sincere savings
        </span>
      </div>

      <!-- Headline -->
      <div style='font-size:3.1rem;font-weight:800;color:white;line-height:1.08;
                  letter-spacing:-0.025em;margin-bottom:16px;'>
        The meal plan<br>that pays you back.
      </div>

      <!-- Subhead -->
      <div style='font-size:1.05rem;color:rgba(255,255,255,0.75);
                  max-width:500px;line-height:1.65;margin-bottom:38px;'>
        Built from this week's actual sale prices at your local grocery stores —
        no subscriptions, no ads, no one getting paid to put food on your plate.
      </div>

      <!-- Stats row -->
      <div style='display:flex;gap:14px;flex-wrap:wrap;'>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:white;line-height:1;'>15–25%</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            avg. grocery savings
          </div>
        </div>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:#F28B30;line-height:1;'>~$2–4</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            per serving vs. $9.99 meal kits
          </div>
        </div>
        <div style='background:rgba(255,255,255,0.1);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.14);border-radius:12px;
                    padding:16px 24px;min-width:130px;'>
          <div style='font-size:2.1rem;font-weight:800;color:white;line-height:1;'>$0</div>
          <div style='font-size:0.74rem;color:rgba(255,255,255,0.6);margin-top:5px;letter-spacing:0.02em;'>
            paid placements. Ever.
          </div>
        </div>
      </div>
    </div>
    """)

    # CTA buttons — Get Started, Sign In, Create Account, Investor Brief
    # Show auth state-aware labels: if already signed in, skip the auth buttons
    if state.is_authenticated():
        h1, h2, _ = st.columns([2, 2, 3])
        with h1:
            if st.button("🌿 Go to my household", type="primary", use_container_width=True):
                st.switch_page("pages/1_Household.py")
        with h2:
            if st.button("📈 Investor brief", use_container_width=True):
                st.switch_page("pages/7_Investor.py")
    else:
        h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
        with h1:
            if st.button("🌿 Get started free", type="primary", use_container_width=True):
                st.switch_page("pages/9_Account.py")
        with h2:
            if st.button("🔐 Sign in", use_container_width=True):
                st.query_params["auth"] = "signin"
                st.switch_page("pages/9_Account.py")
        with h3:
            if st.button("📈 Investor brief", use_container_width=True):
                st.switch_page("pages/7_Investor.py")

    st.html("<div style='height:36px;'></div>")

    # ── How it works ──────────────────────────────────────────────────────────
    st.html("""
    <div style='text-align:center;margin-bottom:22px;'>
      <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;
                  color:#5DAA6A;margin-bottom:6px;'>How it works</div>
      <div style='font-size:1.55rem;font-weight:700;color:#1A2E1D;letter-spacing:-0.01em;'>
        Three steps. Every Sunday.
      </div>
    </div>
    """)

    s1, s2, s3 = st.columns(3)
    for col, icon, num, title, desc in zip(
        [s1, s2, s3],
        ["🏪", "🛡️", "✅"],
        ["01", "02", "03"],
        ["Load your stores", "We build your plan", "One tap to approve"],
        [
            "Pull this week's prices from Kroger live or PDF upload. We read the deals, not the ads.",
            "Safe, affordable meals from this week's best-priced ingredients — filtered for your family.",
            "Review dinners + Found Money on the Sunday Buy-Off screen. One tap sends the shopping list.",
        ],
    ):
        with col:
            st.html(f"""
            <div class='wf-card' style='background:white;border-radius:14px;padding:28px 22px 24px;
                        box-shadow:0 2px 20px rgba(30,92,50,0.07);text-align:center;'>
              <div style='width:48px;height:48px;background:linear-gradient(135deg,#E8F5EC,#D0EDD8);
                          border-radius:50%;display:flex;align-items:center;justify-content:center;
                          margin:0 auto 14px;font-size:1.4rem;'>{icon}</div>
              <div style='font-size:0.62rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                          color:#5DAA6A;margin-bottom:6px;'>Step {num}</div>
              <div style='font-weight:700;font-size:1rem;color:#1A2E1D;margin-bottom:9px;'>{title}</div>
              <div style='font-size:0.84rem;color:#5A6B5E;line-height:1.6;'>{desc}</div>
            </div>
            """)

    st.html("<div style='height:40px;'></div>")

    # ── Pricing tiers ─────────────────────────────────────────────────────────
    st.html("""
    <div style='text-align:center;margin-bottom:22px;'>
      <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.13em;text-transform:uppercase;
                  color:#5DAA6A;margin-bottom:6px;'>Plans & pricing</div>
      <div style='font-size:1.55rem;font-weight:700;color:#1A2E1D;letter-spacing:-0.01em;'>
        Start free. Add what your family needs.
      </div>
    </div>
    """)

    # ── Tier data (shared between cards and sub-pages) ────────────────────────
    tiers = [
        {
            "id": 1, "color": "#3A8C4E", "price": "Free", "price_sub": "forever",
            "name": "Price Finder", "badge": "", "cta": "Get started",
            "tagline": "See where the savings are before you ever shop.",
            "features": ["Cross-store price comparison", "Digital coupon matching", "Weekly savings report", "No credit card needed"],
            "headline": "Start here. No commitment, no card.",
            "description": "Connect your local stores and WhollyFare pulls this week's actual sale prices — then shows you exactly where the deals are and how much you're leaving on the table.",
            "detail_sections": [
                ("What you get", [
                    ("Cross-store price comparison", "Kroger vs Food Lion vs any store you add — side by side, updated every week from live APIs and PDF circulars."),
                    ("Automated coupon matching", "WhollyFare scans digital coupons at every connected store and matches them to items you're already buying."),
                    ("Weekly savings report", "See exactly how much you'd save vs. single-store shopping — every week, before you commit to anything."),
                    ("PDF upload for any store", "No API? Upload the weekly circular as a PDF and we parse it automatically."),
                    ("Free forever", "Price Finder never charges. No trial period, no credit card."),
                ]),
                ("Perfect for", [
                    ("New to WhollyFare", "Explore the platform and build confidence before committing to a meal plan."),
                    ("Savvy comparison shoppers", "You already split your shopping — this tells you which store wins on what, every single week."),
                    ("Households tracking spend", "The Found Money Ledger starts logging your savings from day one."),
                ]),
            ],
            "next_tier": {"id": 2, "name": "Meal Planner", "price": "$7/mo", "teaser": "Ready to have five dinners planned for you every Sunday?"},
        },
        {
            "id": 2, "color": "#5DAA6A", "price": "$7", "price_sub": "/ month",
            "name": "Meal Planner", "badge": "Most popular", "cta": "Start planning",
            "tagline": "Five dinners planned around this week's best prices.",
            "features": ["Everything in Price Finder", "Weekly 5-dinner meal plan", "Flavor Plugins", "Sunday Buy-Off screen", "Shopping list by store"],
            "headline": "Five dinners. Every Sunday. Done.",
            "description": "WhollyFare builds your week's dinners from this week's actual sale prices. You review the plan on Sunday, approve it in one tap, and get a shopping list organised by store.",
            "detail_sections": [
                ("What you get", [
                    ("Weekly 5-dinner meal plan", "Each week's plan is built fresh from the best-priced safe ingredients at your stores. No pre-set menus, no repeated weeks."),
                    ("Flavor Plugins", "The same 5–7 hero ingredients become Mexican Monday, Asian Wednesday, Italian Friday. One shopping trip, five completely different dinners."),
                    ("Sunday Buy-Off", "The one-tap approval screen. Review your week, see your Found Money, tap Approve — the shopping list is ready."),
                    ("Shopping list by store & category", "Kroger items together, Food Lion items together. No backtracking through the aisles."),
                    ("Found Money tracking", "Every week WhollyFare shows you what you saved vs. single-store shopping and vs. HelloFresh at $9.99/serving."),
                ]),
                ("Perfect for", [
                    ("Families of 2–6", "Default 4 servings per meal, adjustable to your household."),
                    ("'What's for dinner?' households", "Sunday Buy-Off turns a weekly stress into a two-minute ritual."),
                    ("Budget-conscious cooks", "Every meal is 30 minutes or less and uses what was actually on sale this week."),
                ]),
            ],
            "next_tier": {"id": 3, "name": "Health Guard", "price": "$19/mo", "teaser": "Managing allergies or a health condition? Add clinical-grade safety filtering."},
        },
        {
            "id": 3, "color": "#F28B30", "price": "$19", "price_sub": "/ month",
            "name": "Health Guard", "badge": "", "cta": "Protect my family",
            "tagline": "Every ingredient checked against your family's health profile.",
            "features": ["Everything in Meal Planner", "Top-14 allergen hard filtering", "Celiac, MCAS, diabetes, CKD, IBS support", "Per-member household profiles", "Every rejection logged & explained"],
            "headline": "Safe first. Every single time.",
            "description": "Meal Planner with a clinical safety layer. Before any ingredient enters your plan, it passes through every constraint in your household's health profile. Hard rules — not suggestions.",
            "detail_sections": [
                ("What you get", [
                    ("Top-14 allergen filtering", "Peanuts, tree nuts, milk, eggs, wheat, soy, fish, shellfish, sesame, mustard, celery, lupin, molluscs, sulphites — any allergen flagged for any member is permanently excluded."),
                    ("Clinical condition support", "Celiac, MCAS, Type 2 Diabetes, Chronic Kidney Disease (CKD), IBS/Low-FODMAP, GERD, Hypertension, Crohn's — each condition triggers a specific constraint ruleset."),
                    ("Per-member profiles", "Tim has no restrictions. Abby has celiac. Chas has a peanut allergy. Each member's constraints are respected individually — and the most restrictive applies to the whole household."),
                    ("Constraint audit log", "Every rejected ingredient is logged with the exact reason: which member, which rule, which item. No black boxes, ever."),
                    ("Safety before savings, always", "The constraint engine runs before the budget optimizer. WhollyFare will never recommend an unsafe ingredient because it happens to be on sale."),
                ]),
                ("Perfect for", [
                    ("Food allergy households", "One peanut allergy means peanuts never appear — not in a plan, not in a suggestion, not in a 'you might also like.'"),
                    ("Celiac families", "Every ingredient checked against the full gluten-containing grain list. GF alternatives surfaced automatically."),
                    ("Complex multi-condition households", "A household with celiac, CKD, and a peanut allergy runs all three rulesets simultaneously without extra work."),
                ]),
            ],
            "next_tier": {"id": 4, "name": "Full Table", "price": "$29/mo", "teaser": "Want full recipes, cooking instructions, and preference learning?"},
        },
        {
            "id": 4, "color": "#1E5C32", "price": "$29", "price_sub": "/ month",
            "name": "Full Table", "badge": "", "cta": "Get the full experience",
            "tagline": "Full recipes, cuisine learning, the complete experience.",
            "features": ["Everything in Health Guard", "Full recipes with prep times", "Cuisine preference memory", "Meal history & favourites", "Priority support"],
            "headline": "The complete WhollyFare table.",
            "description": "Everything in Health Guard, plus full cooking instructions, cuisine preference learning, and meal history. WhollyFare remembers what your family loves and keeps the weekly menu interesting.",
            "detail_sections": [
                ("What you get", [
                    ("Full recipes with prep times", "Step-by-step cooking instructions, ingredient quantities per serving, estimated prep and cook time for every meal."),
                    ("Cuisine preference memory", "WhollyFare tracks which meals were approved, which were skipped, what your household consistently enjoys — and reflects that in future plans."),
                    ("Meal history & favourites", "Flag meals as household favourites. WhollyFare brings them back when the same ingredients go on sale again."),
                    ("Pantry-aware planning (coming soon)", "Tell WhollyFare what's already in your pantry and it won't plan around things you have."),
                    ("Priority support", "Plan issues, constraint questions, PDF uploads that need a hand — you go to the front of the queue."),
                ]),
                ("Perfect for", [
                    ("Households who actually cook", "Full recipes turn the shopping list into a complete cooking guide."),
                    ("Long-term WhollyFare users", "The preference memory gets better the longer you use it."),
                    ("Anyone who wants everything", "From sale price to plated dinner — every step covered in one place."),
                ]),
            ],
            "next_tier": None,
        },
    ]

    # ── Tier sub-page: if ?tier=N is set, render detail view and stop ─────────
    _tier_param = st.query_params.get("tier")
    if _tier_param:
        try:
            _active = next((t for t in tiers if str(t["id"]) == str(_tier_param)), None)
        except Exception:
            _active = None

        if _active:
            # Back nav
            if st.button("← Plans & Pricing", key="back_to_plans"):
                st.query_params.clear()
                st.rerun()

            c = _active["color"]

            # Tier hero
            st.html(f"""
            <div style='background:linear-gradient(135deg,#142B1C,#1E5C32);border-radius:16px;
                        padding:44px 48px 38px;margin-bottom:28px;position:relative;overflow:hidden;'>
              <svg style='position:absolute;right:-40px;bottom:-40px;opacity:0.06;' width="300" height="300" viewBox="0 0 300 300">
                <ellipse cx="150" cy="150" rx="130" ry="86" fill="white" transform="rotate(-28 150 150)"/>
                <line x1="60" y1="220" x2="230" y2="90" stroke="white" stroke-width="4"/>
              </svg>
              <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                          color:#9FD9A8;margin-bottom:10px;'>Plans &amp; Pricing</div>
              <div style='display:flex;align-items:baseline;gap:14px;margin-bottom:12px;'>
                <span style='font-size:2.4rem;font-weight:800;color:white;letter-spacing:-0.02em;'>{_active["name"]}</span>
                <span style='font-size:2rem;font-weight:800;color:{c};'>{_active["price"]}</span>
                <span style='font-size:0.9rem;color:rgba(255,255,255,0.6);'>{_active["price_sub"]}</span>
              </div>
              <div style='font-size:1.1rem;font-weight:600;color:white;margin-bottom:8px;'>{_active["headline"]}</div>
              <div style='font-size:0.95rem;color:rgba(255,255,255,0.78);max-width:580px;line-height:1.65;'>
                {_active["description"]}
              </div>
            </div>
            """)

            # Detail sections
            for section_title, items in _active["detail_sections"]:
                st.html(f"""
                <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                            color:{c};margin-bottom:10px;margin-top:20px;'>{section_title}</div>
                """)
                for item_title, item_desc in items:
                    st.html(f"""
                    <div style='background:white;border-radius:10px;padding:16px 18px;margin-bottom:8px;
                                border-left:3px solid {c};box-shadow:0 1px 8px rgba(30,92,50,0.06);'>
                      <div style='font-weight:700;font-size:0.93rem;color:#1A2E1D;margin-bottom:3px;'>
                        <span style='color:{c};margin-right:6px;'>✓</span>{item_title}
                      </div>
                      <div style='font-size:0.84rem;color:#5A6B5E;line-height:1.55;padding-left:22px;'>{item_desc}</div>
                    </div>
                    """)

            # Next tier teaser
            if _active["next_tier"]:
                nt = _active["next_tier"]
                st.html(f"""
                <div style='background:#F4FAF5;border:1px solid #D8EDD0;border-radius:10px;
                            padding:16px 20px;margin-top:24px;display:flex;
                            justify-content:space-between;align-items:center;'>
                  <div>
                    <div style='font-size:0.8rem;color:#5A7A62;'>Next tier up</div>
                    <div style='font-weight:600;color:#1E5C32;'>{nt["name"]} — {nt["price"]}</div>
                    <div style='font-size:0.83rem;color:#5A6B5E;margin-top:2px;'>{nt["teaser"]}</div>
                  </div>
                </div>
                """)
                if st.button(f"See {nt['name']} →", key="next_tier_btn"):
                    st.query_params["tier"] = str(nt["id"])
                    st.rerun()

            # CTA
            st.html("<div style='height:24px;'></div>")
            cta_a, cta_b, _ = st.columns([2, 1, 3])
            with cta_a:
                if st.button(f"🌿 Start with {_active['name']}", type="primary", use_container_width=True):
                    st.query_params.clear()
                    st.switch_page("pages/1_Household.py")
            with cta_b:
                if st.button("← All plans", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()

            st.stop()

    # ── Pricing tier cards ─────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.columns(4)
    for col, tier in zip([t1, t2, t3, t4], tiers):
        badge_html = (
            f"<div style='display:inline-block;background:{tier['color']};color:white;"
            f"font-size:0.65rem;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;"
            f"border-radius:20px;padding:3px 10px;margin-bottom:12px;'>{tier['badge']}</div>"
            if tier["badge"] else "<div style='height:24px;'></div>"
        )
        feats = "".join(
            f"<div style='display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;'>"
            f"<span style='color:{tier['color']};font-size:0.85rem;margin-top:1px;flex-shrink:0;'>✓</span>"
            f"<span style='font-size:0.8rem;color:#4A5568;line-height:1.45;'>{f}</span></div>"
            for f in tier["features"]
        )
        with col:
            st.html(f"""
            <div class='wf-card' style='background:white;border-radius:14px;
                        border-top:4px solid {tier["color"]};
                        box-shadow:0 2px 22px rgba(30,92,50,0.08);
                        padding:22px 18px 14px;min-height:340px;'>
              {badge_html}
              <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;
                          text-transform:uppercase;color:{tier["color"]};margin-bottom:6px;'>
                {tier["name"]}
              </div>
              <div style='margin-bottom:10px;line-height:1;'>
                <span style='font-size:2rem;font-weight:800;color:#1A2E1D;'>{tier["price"]}</span>
                <span style='font-size:0.76rem;color:#9AA8A0;margin-left:3px;'>{tier["price_sub"]}</span>
              </div>
              <div style='font-size:0.82rem;color:#5A6B5E;line-height:1.5;margin-bottom:14px;
                          min-height:36px;'>{tier["tagline"]}</div>
              <div style='border-top:1px solid #F0F4F1;padding-top:14px;'>
                {feats}
              </div>
            </div>
            """)

            if st.button(f"{tier['cta']} →", key=f"tier_{tier['id']}", use_container_width=True):
                st.query_params["tier"] = str(tier["id"])
                st.rerun()

    st.html("<div style='height:32px;'></div>")

    # ── Trust bar ────────────────────────────────────────────────────────────
    st.html("""
    <div style='text-align:center;padding:15px 20px;
                background:rgba(255,255,255,0.6);backdrop-filter:blur(4px);
                border-radius:10px;border:1px solid rgba(93,170,106,0.18);'>
      <span style='font-size:0.85rem;color:#3A6645;font-weight:500;'>
        🚫 No paid placements &nbsp;·&nbsp; 🛡️ Health rules are absolute &nbsp;·&nbsp;
        🔍 Every pick shows its reason &nbsp;·&nbsp; 🔐 Your data is yours
      </span>
    </div>
    """)

    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
# DASHBOARD VIEW — returning users with household set up
# ════════════════════════════════════════════════════════════════════════════════
hh_name = household.household_name if household else "your household"
week    = st.session_state["active_week"]

if approved and plan:
    st.html(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>✅ Week of {week} is approved.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Your shopping list is ready.</span>
    </div>""")
elif plan:
    st.html(f"""<div style='background:#FFF8E1;border:1px solid #FFD54F;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📋 Plan ready for {hh_name}.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Head to Sunday Buy-Off to approve.</span>
    </div>""")
elif loaded:
    st.html(f"""<div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#1E5C32;'>📦 {len(loaded)} store(s) loaded.</span>
      <span style='color:#3A8C4E;font-size:0.9rem;margin-left:8px;'>Head to Grocer Hub to run the engine.</span>
    </div>""")
else:
    st.html("""<div style='background:#FFF3E0;border:1px solid #FFCC80;border-radius:10px;
                   padding:16px 20px;margin-bottom:16px;'>
      <span style='font-size:1rem;font-weight:600;color:#8C4A00;'>📄 No store data loaded yet for this week.</span>
      <span style='color:#8C4A00;font-size:0.9rem;margin-left:8px;'>Upload circulars or pull from Kroger in the Grocer Hub.</span>
    </div>""")

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
st.html(f"<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:12px;'>This week — {week}</div>")

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
    st.html("<div style='font-size:1rem;font-weight:600;color:#1E5C32;margin-bottom:10px;'>Recent weeks</div>")
    for entry in reversed(history[-5:]):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.caption(f"**Week of {entry.get('week','—')}**  ·  {entry.get('meals_planned', 0)} dinners")
        with c2:
            st.caption(f"${entry.get('whollyfare_cost', 0):.2f} spent")
        with c3:
            st.caption(f"💚 ${entry.get('found_money', 0):.2f} found")
        with c4:
            stores_n = entry.get('stores_used', 1)
            grocer_txt = "Kroger + Food Lion" if stores_n >= 2 else "Kroger"
            st.caption(f"📍 {grocer_txt}")
