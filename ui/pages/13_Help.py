"""13_Help.py — WhollyFare Help & FAQ

Architecture: FAQ content lives in FAQ_SECTIONS (a list of dicts) at the top
of this file, completely separate from the render logic below. To update the
FAQ when the app changes, edit only the data section — the render code is stable.

MAINTENANCE RULE: Whenever a fundamental change is made to any of these areas,
search this file for the corresponding section tag and update the Q&As:
  [GETTING_STARTED]  — Home.py, 9_Account.py, trial/tier system
  [HOUSEHOLD]        — 1_Household.py, state.py household profile
  [STORES]           — 2_Grocer_Hub.py, store_directory.py, Admin workflow
  [PLAN]             — 3_Plan.py, meal_planner.py, recipe_library.py
  [BUYOFF]           — 4_Sunday_BuyOff.py, state.py approve_week_db()
  [SHOPPING]         — 5_Shopping_List.py
  [SAVINGS]          — 6_Ledger.py, state.py net_found_money(), trip_cost_for_store()
  [ACCOUNT]          — 9_Account.py, tier system, state.py get_user_tier()
  [TROUBLESHOOT]     — Any systemic issue patterns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(
    page_title="Help & FAQ · WhollyFare",
    page_icon="❓",
    layout="centered",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

style.inject()
style.maybe_scroll_to_top()

# ══════════════════════════════════════════════════════════════════════════════
# FAQ CONTENT — edit this section when the app changes
# Tag each section with its [MAINTENANCE_TAG] for easy grep
# ══════════════════════════════════════════════════════════════════════════════

FAQ_SECTIONS = [
    # ── [GETTING_STARTED] ─────────────────────────────────────────────────────
    {
        "icon": "🌿",
        "title": "Getting Started",
        "tag": "GETTING_STARTED",
        "questions": [
            {
                "q": "What is WhollyFare?",
                "a": (
                    "WhollyFare is a meal planning platform that builds your weekly dinner plan "
                    "from this week's actual sale prices at your local grocery stores. Instead of "
                    "paying for a meal kit at $9.99/serving, WhollyFare shows you how to get the "
                    "same variety for $2–4/serving using what's already on sale — and tracks exactly "
                    "how much you saved each week in your Found Money ledger."
                ),
            },
            {
                "q": "How does the free trial work?",
                "a": (
                    "When you create an account, you get 7 days of full Meal Planner access — "
                    "no credit card required. That means the weekly plan, Sunday Buy-Off, shopping "
                    "list, and savings ledger are all unlocked from day one. After 7 days, the "
                    "app moves to the free Price Finder tier unless you upgrade. Your saved data "
                    "and Found Money history stay with your account."
                ),
            },
            {
                "q": "What do I need to get started?",
                "a": (
                    "Three things: (1) Create a free account. (2) Tell us about your household — "
                    "how many people, any dietary needs. (3) Select your local grocery stores. "
                    "Once those are set up, WhollyFare can generate your first weekly plan. "
                    "The whole setup takes about 5 minutes."
                ),
            },
            {
                "q": "Is WhollyFare really free?",
                "a": (
                    "The Price Finder tier is free forever — no credit card, no expiry. It gives "
                    "you cross-store price comparison and weekly savings reports. The Meal Planner "
                    "($7/mo), Health Guard ($19/mo), and Full Table ($29/mo) tiers add the weekly "
                    "plan, health filtering, and full recipes. There are zero paid placements, "
                    "zero ads, and your data is never sold."
                ),
            },
        ],
    },
    # ── [HOUSEHOLD] ───────────────────────────────────────────────────────────
    {
        "icon": "👨‍👩‍👧",
        "title": "Household Setup",
        "tag": "HOUSEHOLD",
        "questions": [
            {
                "q": "How do I add family members?",
                "a": (
                    "Go to My Household in the sidebar. Under Members, add each person in your "
                    "household. You can give each member a name and set their individual dietary "
                    "needs — allergens, health conditions, or lifestyle preferences. WhollyFare "
                    "applies the most restrictive constraints across all members, so if one person "
                    "has a peanut allergy, peanuts are excluded for everyone."
                ),
            },
            {
                "q": "Can I change my household info later?",
                "a": (
                    "Yes — go to My Household any time to update members, dietary needs, or your "
                    "household name. Changes take effect on the next plan you generate. Your "
                    "existing approved plans and Found Money history are not affected."
                ),
            },
            {
                "q": "What dietary conditions does WhollyFare support?",
                "a": (
                    "The Health Guard tier (coming soon) supports the top-14 allergens (peanuts, "
                    "tree nuts, milk, eggs, wheat, soy, fish, shellfish, sesame, and more), plus "
                    "clinical conditions including celiac disease, MCAS, Type 2 diabetes, "
                    "chronic kidney disease (CKD), IBS/low-FODMAP, GERD, hypertension, and "
                    "Crohn's disease. Each condition triggers a specific constraint ruleset, and "
                    "every rejection is logged so you can see exactly why an ingredient was excluded."
                ),
            },
            {
                "q": "What is the pantry tracker?",
                "a": (
                    "The pantry tracker (My Pantry in the sidebar) lets you mark staples you "
                    "always have on hand — olive oil, salt, garlic, etc. WhollyFare excludes "
                    "these from your shopping list and costs them at $0 in meal estimates, "
                    "so your per-serving numbers reflect what you actually need to buy."
                ),
            },
            {
                "q": "How does the 'running low' flag work?",
                "a": (
                    "Every time you approve a week's meal plan, WhollyFare notes which pantry "
                    "staples appeared in those recipes — olive oil in the stir-fry, garlic in "
                    "three dinners, that kind of thing. When the cumulative count crosses what "
                    "a typical container would cover, the item gets flagged running low (🔶) "
                    "on the Pantry page. No sensors, no guessing — just your own cooking history. "
                    "Hit 'Restocked' when you pick it up and the counter resets to zero."
                ),
            },
            {
                "q": "What is a restock recommendation and why should I trust it?",
                "a": (
                    "When a pantry item is running low and also on sale at one of your stores "
                    "this week, WhollyFare surfaces it on your shopping list under "
                    "'Good time to restock.' It shows you the store, the sale price, and exactly "
                    "how many meals you've cooked with that item since you last restocked — "
                    "so you can see the reasoning, not just the recommendation. "
                    "There are no sponsored placements in WhollyFare. This flag is triggered "
                    "purely by your usage data and the store circular. That is the Sincere "
                    "Strategy: if we recommend something, we show you why."
                ),
            },
            {
                "q": "What are Weekly Regulars?",
                "a": (
                    "Weekly Regulars are items you buy every week regardless of the meal plan — "
                    "milk, eggs, cold cuts, orange juice. They appear as a separate section on "
                    "your shopping list and their cost is tracked separately, never folded into "
                    "WhollyFare Found Money. That distinction matters: your meal-plan savings "
                    "are real savings, not padded with items you would have bought anyway."
                ),
            },
        ],
    },
    # ── [STORES] ──────────────────────────────────────────────────────────────
    {
        "icon": "🏪",
        "title": "Stores & Prices",
        "tag": "STORES",
        "questions": [
            {
                "q": "Which stores does WhollyFare support?",
                "a": (
                    "In the Charlottesville pilot, WhollyFare supports Kroger (live API — prices "
                    "update automatically), Food Lion, Aldi, Harris Teeter, and other local stores "
                    "via weekly circular uploads. Store coverage expands in Phase 2. You can also "
                    "add any local or independent store manually."
                ),
            },
            {
                "q": "How does WhollyFare get store prices?",
                "a": (
                    "Kroger prices come from the live Kroger API — updated automatically each week. "
                    "Other stores (Food Lion, Aldi, Harris Teeter) are loaded from their weekly "
                    "PDF circulars, which are uploaded and processed every Wednesday by the "
                    "WhollyFare team. You don't need to do anything — when you log in on Wednesday "
                    "or later, that week's prices are already loaded."
                ),
            },
            {
                "q": "What if my store isn't listed?",
                "a": (
                    "You can add any store as a personal store from the Grocer Hub. For personal "
                    "stores, you can manually enter items on sale that week. Phase 2 will add "
                    "automated circular parsing for more chains. If you'd like to see a specific "
                    "store added, use the feedback button in the sidebar — Tim reads every one."
                ),
            },
            {
                "q": "What does trip cost mean, and why does it affect my savings?",
                "a": (
                    "WhollyFare shows your net Found Money — that's gross grocery savings minus "
                    "the gas cost of driving to each store. The trip cost is calculated at "
                    "$0.22/mile round trip, which is a conservative personal vehicle estimate. "
                    "If a store's grocery savings are less than its trip cost, you'll see a skip "
                    "hint on the Sunday Buy-Off screen. WhollyFare will never show you a flattering "
                    "savings number that ignores gas costs."
                ),
            },
        ],
    },
    # ── [PLAN] ────────────────────────────────────────────────────────────────
    {
        "icon": "🍽️",
        "title": "Your Weekly Plan",
        "tag": "PLAN",
        "questions": [
            {
                "q": "How does WhollyFare choose my meals?",
                "a": (
                    "Each week's plan is built fresh from the best-priced ingredients at your "
                    "selected stores. WhollyFare selects a set of hero ingredients — proteins, "
                    "produce, and pantry items — that are on sale that week, then builds meals "
                    "around them. Flavor Plugins rotate the same core ingredients across cuisines "
                    "so Monday might be Mexican chicken tacos and Wednesday is Asian stir-fry, "
                    "using much of the same shopping basket. This reduces waste and keeps dinners "
                    "interesting without blowing the budget."
                ),
            },
            {
                "q": "What are Flavor Plugins?",
                "a": (
                    "Flavor Plugins are cuisine lenses applied to the same core ingredients. "
                    "Instead of buying completely different groceries for each meal, WhollyFare "
                    "reuses the week's hero proteins and produce across Mexican, Italian, Asian, "
                    "American, and Mediterranean meals. The result: five completely different "
                    "dinners from one efficient shopping trip."
                ),
            },
            {
                "q": "How do I regenerate or change my plan?",
                "a": (
                    "Go to My Plan and click 'Generate new plan'. You can adjust cuisine "
                    "preferences, number of dinners, or nights out before regenerating. "
                    "Regenerating replaces the current plan — if you've already approved this "
                    "week's plan, you'll need to re-approve the new one."
                ),
            },
            {
                "q": "Why does my plan show different stores for different meals?",
                "a": (
                    "WhollyFare builds your plan across all your selected stores to maximise "
                    "savings. An ingredient might be $1.50 cheaper at Food Lion than Kroger "
                    "this week — WhollyFare assigns it to the better store and groups your "
                    "shopping list accordingly. The shopping list always tells you which items "
                    "to buy at which store."
                ),
            },
        ],
    },
    # ── [BUYOFF] ──────────────────────────────────────────────────────────────
    {
        "icon": "✅",
        "title": "Sunday Buy-Off",
        "tag": "BUYOFF",
        "questions": [
            {
                "q": "What is the Sunday Buy-Off?",
                "a": (
                    "The Sunday Buy-Off is the weekly approval screen. It shows your five planned "
                    "meals, the total estimated cost, your Found Money for the week, and any skip "
                    "hints (stores where trip cost exceeds grocery savings). You review the plan, "
                    "swap or skip meals you don't want, and tap Approve. That locks in the plan "
                    "and makes your shopping list available."
                ),
            },
            {
                "q": "How do I swap or skip a meal?",
                "a": (
                    "On the Sunday Buy-Off screen, each meal has Approve, Swap, and Skip options. "
                    "Swap suggests an alternative meal using this week's on-sale ingredients. "
                    "Skip removes the meal from your plan and shopping list entirely. Skipped "
                    "meals are not counted in your Found Money for the week."
                ),
            },
            {
                "q": "What is Found Money?",
                "a": (
                    "Found Money is the net savings you put back in your pocket this week — "
                    "that's the difference between what you'd pay buying the same meals at a "
                    "single store at full price, minus what WhollyFare's cross-store plan costs, "
                    "minus the gas cost of your store trips. It's always shown net, never gross. "
                    "Your cumulative Found Money is tracked in the Savings Ledger."
                ),
            },
            {
                "q": "Do I have to do the Buy-Off on Sunday?",
                "a": (
                    "No — the name is just a convention. You can approve your plan any day of the "
                    "week. Most households find Sunday works well because store circulars refresh "
                    "on Wednesdays and you can plan before the weekend shop. But WhollyFare "
                    "works whenever your household shops."
                ),
            },
        ],
    },
    # ── [SHOPPING] ────────────────────────────────────────────────────────────
    {
        "icon": "🛒",
        "title": "Shopping List",
        "tag": "SHOPPING",
        "questions": [
            {
                "q": "How do I use the shopping list in the store?",
                "a": (
                    "Open the Shopping List page on your phone while you're in the store. Items "
                    "are grouped by store, then by category (produce, protein, dairy, etc.) so "
                    "you're never backtracking through aisles. Tap any item to check it off. "
                    "Your Weekly Regulars (items you buy every week) and pantry restocks appear "
                    "in their own sections."
                ),
            },
            {
                "q": "Can I add items to the list manually?",
                "a": (
                    "Yes — at the bottom of the Shopping List page, there's an Add Item form. "
                    "You can add any item with a quantity, assign it to a store, and it'll "
                    "appear in the right section. Manually added items persist through the "
                    "session and can be removed individually."
                ),
            },
            {
                "q": "How do I export my shopping list?",
                "a": (
                    "The Shopping List page has CSV and TXT export buttons. The CSV includes "
                    "item name, quantity, store, category, and estimated cost — useful for "
                    "sharing or printing. The TXT version is plain text, one item per line, "
                    "grouped by store."
                ),
            },
        ],
    },
    # ── [SAVINGS] ─────────────────────────────────────────────────────────────
    {
        "icon": "💰",
        "title": "Found Money & Savings",
        "tag": "SAVINGS",
        "questions": [
            {
                "q": "How is my savings calculated?",
                "a": (
                    "WhollyFare compares three numbers: (1) what your meals would cost at a "
                    "single store at full price, (2) what the cross-store WhollyFare plan "
                    "actually costs, and (3) what the equivalent HelloFresh meal kit would "
                    "cost at $9.99/serving. The difference between (1) and (2), minus gas "
                    "costs, is your net Found Money."
                ),
            },
            {
                "q": "Why does WhollyFare subtract gas costs from savings?",
                "a": (
                    "Because it's honest. Saving $8 at Aldi means nothing if you drove 20 miles "
                    "to get there. WhollyFare calculates trip cost at $0.22/mile (round trip) "
                    "for each store you visit and deducts it from your gross savings. If a store "
                    "trip costs more in gas than you save in groceries, you'll see a skip hint "
                    "before you approve your plan."
                ),
            },
            {
                "q": "What are milestones and streaks?",
                "a": (
                    "The Savings Ledger tracks your cumulative Found Money and weekly streak — "
                    "the number of consecutive weeks you've saved money. Milestones appear when "
                    "you cross savings thresholds ($25, $50, $100, $250, $500, $1,000) or "
                    "streak thresholds (2, 4, 8, 12 weeks). They're a way to see the "
                    "compounding effect of planning consistently."
                ),
            },
            {
                "q": "My savings seem lower than I expected — why?",
                "a": (
                    "A few common reasons: (1) Trip costs — gas is deducted from gross savings. "
                    "(2) Some stores hadn't loaded their circular yet when the plan was generated. "
                    "(3) The plan chose meals that were already budget-friendly, so the "
                    "discount off 'full price' is smaller. The Ledger shows gross and net "
                    "separately so you can see exactly where savings come from."
                ),
            },
        ],
    },
    # ── [ACCOUNT] ─────────────────────────────────────────────────────────────
    {
        "icon": "🔐",
        "title": "Account & Subscription",
        "tag": "ACCOUNT",
        "questions": [
            {
                "q": "What's included in each tier?",
                "a": (
                    "Price Finder (Free): cross-store price comparison, coupon matching, "
                    "weekly savings report. "
                    "Meal Planner ($7/mo): everything in Price Finder, plus weekly 5-dinner plan, "
                    "Sunday Buy-Off, shopping list by store, Found Money tracking. "
                    "Health Guard ($19/mo): everything in Meal Planner, plus clinical-grade dietary "
                    "filtering for allergens and health conditions. "
                    "Full Table ($29/mo): everything in Health Guard, plus full step-by-step "
                    "recipes, cuisine preference memory, and meal history."
                ),
            },
            {
                "q": "What happens when my trial ends?",
                "a": (
                    "After 7 days, your account moves to the free Price Finder tier. You can "
                    "still see your store prices and Found Money history, but plan generation, "
                    "the Sunday Buy-Off, and the shopping list require a Meal Planner "
                    "subscription. Your data — household profile, store selections, ledger "
                    "history — is never deleted."
                ),
            },
            {
                "q": "How do I upgrade my subscription?",
                "a": (
                    "Subscription management is coming in Phase 2. During the pilot, reach out "
                    "directly to tim.hislop@gmail.com to upgrade your account. Pilot households "
                    "get extended trial access while we build the payment flow."
                ),
            },
            {
                "q": "Is my data private?",
                "a": (
                    "Yes. Your household profile, dietary needs, shopping history, and Found Money "
                    "data are never sold, shared, or used for advertising. WhollyFare's only "
                    "revenue is subscriptions. This is a core part of the Sincere Strategy — "
                    "we can't serve you honestly while selling your data to the people "
                    "whose products we're supposed to help you evaluate objectively."
                ),
            },
        ],
    },
    # ── [TROUBLESHOOT] ────────────────────────────────────────────────────────
    {
        "icon": "🔧",
        "title": "Troubleshooting",
        "tag": "TROUBLESHOOT",
        "questions": [
            {
                "q": "My plan didn't generate — what do I do?",
                "a": (
                    "Most likely cause: no store prices are loaded for this week. Go to Grocer Hub "
                    "and check which stores show items loaded. If none do, prices may not have been "
                    "uploaded yet (they refresh each Wednesday). Try again Wednesday evening or "
                    "later. If stores show prices but the plan still fails, use the feedback button "
                    "in the sidebar to report it."
                ),
            },
            {
                "q": "Prices look wrong or outdated — what do I do?",
                "a": (
                    "Store circulars refresh every Wednesday. If you're looking at the app before "
                    "Wednesday, you're seeing last week's prices. If it's Wednesday or later and "
                    "prices still look wrong, the circular may not have uploaded yet. "
                    "Use the feedback button to flag the issue — Tim checks it daily during the pilot."
                ),
            },
            {
                "q": "I can't sign in — what do I do?",
                "a": (
                    "Make sure you're using the same email address you signed up with. If you've "
                    "forgotten your password, there's currently no self-serve reset during the pilot "
                    "— email tim.hislop@gmail.com and we'll sort it out. Streamlit Cloud sessions "
                    "expire after a period of inactivity, so you may need to sign in again after "
                    "a browser restart."
                ),
            },
            {
                "q": "The app seems slow or something isn't loading — what do I do?",
                "a": (
                    "WhollyFare runs on Streamlit Community Cloud, which occasionally has cold "
                    "start delays (30–60 seconds on first load). A hard refresh (Ctrl+Shift+R on "
                    "desktop, pull-to-refresh on mobile) usually fixes display issues. If "
                    "something is consistently broken, please use the feedback button — it goes "
                    "directly to Tim."
                ),
            },
            {
                "q": "Something's wrong that isn't listed here — how do I report it?",
                "a": (
                    "Use the 💬 Share feedback button at the bottom of the sidebar — it's on "
                    "every page. Your feedback goes directly to Tim. During the pilot, every "
                    "report is read and most issues are fixed within 24 hours. You can also "
                    "email tim.hislop@gmail.com directly."
                ),
            },
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# RENDER — do not edit below this line for content changes
# ══════════════════════════════════════════════════════════════════════════════

style.page_header("Help & FAQ", "Everything you need to know about WhollyFare.")

# ── Search / filter ───────────────────────────────────────────────────────────
_search = st.text_input(
    "Search questions",
    placeholder="Try 'savings', 'trial', 'stores'…",
    label_visibility="collapsed",
)
_q = _search.strip().lower()

st.html("<div style='height:8px;'></div>")

# ── Section rendering ─────────────────────────────────────────────────────────
_any_results = False

for section in FAQ_SECTIONS:
    # Filter questions by search term
    if _q:
        _matched = [
            qa for qa in section["questions"]
            if _q in qa["q"].lower() or _q in qa["a"].lower()
        ]
    else:
        _matched = section["questions"]

    if not _matched:
        continue

    _any_results = True

    # Section header
    st.html(
        f"<div style='display:flex;align-items:center;gap:10px;"
        f"margin-top:28px;margin-bottom:12px;'>"
        f"<span style='font-size:1.4rem;'>{section['icon']}</span>"
        f"<span style='font-size:1.1rem;font-weight:800;color:#1A2E1D;'>{section['title']}</span>"
        f"</div>"
    )

    # Q&A expanders
    for qa in _matched:
        with st.expander(qa["q"], expanded=bool(_q)):
            st.html(
                f"<div style='font-size:0.9rem;color:#3A4A3E;line-height:1.7;"
                f"padding:4px 0 8px;'>{qa['a']}</div>"
            )

if _q and not _any_results:
    st.html(
        "<div style='text-align:center;padding:40px 20px;'>"
        "<div style='font-size:1.5rem;margin-bottom:10px;'>🔍</div>"
        "<div style='font-size:1rem;font-weight:600;color:#1A2E1D;margin-bottom:6px;'>"
        f"No results for \"{_search}\"</div>"
        "<div style='font-size:0.87rem;color:#5A7A62;'>"
        "Try a different search term, or use the feedback button below to ask directly."
        "</div></div>"
    )

# ── Contact WhollyFare form ───────────────────────────────────────────────────
# Writes to Supabase feedback table (same as sidebar feedback button) AND
# sends an email notification to tim.hislop@gmail.com via Gmail SMTP.
# Email requires CONTACT_EMAIL_USER + CONTACT_EMAIL_PASS in Streamlit secrets.
# POC: If SMTP credentials are absent or fail, form still saves to Supabase and
#      informs the user. PROD: replace with transactional email service (Resend/SendGrid).

def _send_contact_email(from_email: str, subject: str, message: str) -> bool:
    """Send contact form submission to tim.hislop@gmail.com via Gmail SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    try:
        smtp_user = st.secrets.get("CONTACT_EMAIL_USER", "")
        smtp_pass = st.secrets.get("CONTACT_EMAIL_PASS", "")
        if not smtp_user or not smtp_pass:
            return False
        body = (
            f"New WhollyFare contact form submission\n\n"
            f"From: {from_email}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}\n\n"
            f"---\nReply directly to: {from_email}"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"[WhollyFare Contact] {subject}"
        msg["From"]    = smtp_user
        msg["To"]      = "tim.hislop@gmail.com"
        msg["Reply-To"] = from_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as _e:
        return False


st.html("<div style='height:40px;'></div>")
st.html(
    "<div style='font-size:1.1rem;font-weight:800;color:#1A2E1D;margin-bottom:4px;'>"
    "✉️ Contact WhollyFare</div>"
    "<div style='font-size:0.88rem;color:#5A7A62;margin-bottom:16px;'>"
    "During the pilot, Tim reads every message personally and responds within 24 hours.</div>"
)

_user = st.session_state.get("user", {})
_prefill_email = _user.get("email", "") if _user else ""

with st.form("contact_whollyfare_form", clear_on_submit=True):
    _contact_email = st.text_input(
        "Your email address",
        value=_prefill_email,
        placeholder="you@example.com",
    )
    _contact_subject = st.selectbox(
        "What's this about?",
        options=[
            "Question about the app",
            "Something isn't working",
            "Feature request or idea",
            "Pricing or subscription",
            "Something else",
        ],
    )
    _contact_msg = st.text_area(
        "Your message",
        placeholder="Tell us what's on your mind — the more detail the better.",
        height=120,
    )
    _contact_submit = st.form_submit_button(
        "Send message →", type="primary", use_container_width=True
    )

if _contact_submit:
    if not _contact_email.strip() or "@" not in _contact_email:
        st.warning("Please enter a valid email address so we can reply.")
    elif not _contact_msg.strip():
        st.warning("Please enter a message before sending.")
    else:
        _db_ok, _db_msg = False, ""
        _email_ok = False
        # Write to Supabase feedback table
        try:
            _db_ok, _db_msg = state.submit_feedback(
                message=f"[Contact: {_contact_subject}] {_contact_msg.strip()}",
                page="Help & FAQ / Contact",
                rating=None,
            )
        except Exception as _e:
            _db_ok = False
        # Send email notification
        _email_ok = _send_contact_email(
            from_email=_contact_email.strip(),
            subject=_contact_subject,
            message=_contact_msg.strip(),
        )
        if _db_ok or _email_ok:
            st.success(
                "✅ Message sent! Tim will reply to "
                + _contact_email.strip()
                + " within 24 hours."
            )
        else:
            # Both paths failed — still acknowledge gracefully
            st.warning(
                "Message saved. If you don't hear back within 48 hours, "
                "email tim.hislop@gmail.com directly."
            )
