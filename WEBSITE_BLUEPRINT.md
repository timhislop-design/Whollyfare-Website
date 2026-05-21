# WhollyFare® — Website Architecture & Construction Blueprint
**Sentir Solutions® LLC · Charlottesville, VA**
*Last updated: May 2026 · Use this alongside DATABASE_SCHEMA.md*

---

## Purpose of This Document

This is Tim's construction guide for the WhollyFare website — every page that
exists, every page that's planned, and every page that's coming once investment
lands. It maps the investor problem statement directly to features, gives each
page a build status, and sequences the work so that each thing built is usable
before the next thing starts.

**The investor problem statement maps to the site like this:**

| Investor bullet | Feature | Pages | Status |
|---|---|---|---|
| Families lose 15–25% to single-store shopping | Cross-store price optimization | Grocer Hub, Plan, Sunday Buy-Off | ✅ Built |
| Meal kits cost $9.99/serving | Found Money vs. HelloFresh comparison | Sunday Buy-Off, Ledger | ✅ Built |
| Coupon apps (Flipp, Ibotta) don't connect to meal planning | Coupon Vault | Coupon Vault | 📋 Planned (Phase 2) |
| Instacart/DoorDash optimize for convenience, not savings | Delivery Hub with real cost transparency | Delivery Hub | 🔒 Requires Investment |
| Nutrition apps have zero price awareness | Health Guard + USDA nutrition integration | Health Guard Dashboard | 📋 Planned (Phase 2) |
| Nobody connected the full loop | The full WhollyFare flow | All core pages | ✅ Spine built |

---

## Medical Disclaimer Architecture

**This applies to every page that touches health, nutrition, or dietary advice.**

WhollyFare is a meal planning and price optimization tool. It is not a medical
service, a clinical dietary management system, or a substitute for professional
medical advice. This distinction must be visible and consistent across every
page that involves health constraints, nutrition data, or dietary guidance.

The practical rule: **hard constraints are a safety feature, not a medical
claim.** When WhollyFare says "peanuts will never appear in your plan," that is
a product guarantee backed by the constraint engine. When WhollyFare says "this
meal is 1,200mg sodium," that is nutritional information to help the household
make informed choices — not a clinical prescription.

**The core pattern — cite the source, give the link, step back:**

WhollyFare does not make medical claims. For every dietary constraint it
applies, it cites the recognized authority whose guideline it's following and
gives the user a direct link to read that guideline themselves. The user decides
whether to act on it. WhollyFare is out of the final determination.

Every constraint rejection, every nutrition threshold flag, and every
health-related planning note follows this structure:

> *"[Item] contains [ingredient], which conflicts with [Member]'s hypertension
> constraint. WhollyFare applies this filter following the American Heart
> Association's DASH dietary guidelines.* ***[Read the AHA guideline →]***
> *This is a planning tool — your doctor has the final say."*

The link opens in a new tab. No interpretation. No recommendation. Just:
here's what the authority says, here's the link, you decide.

**The database table that powers this:** `constraint_evidence_sources` — a
platform-maintained catalog mapping every diagnosis and allergen to the
authoritative guideline WhollyFare implements, including the plain-English
summary WhollyFare shows and the exact URL the user is linked to.

**Every page that shows health-related data must follow this pattern:**
- Cite the source authority by name
- Link directly to the original guideline (new tab)
- Distinguish hard constraints (safety engine, always applied) from nutrition
  guidance (informational, user decides)
- Never use language that implies clinical accuracy — "following low-sodium
  guidelines" not "medically prescribed low-sodium"; "based on celiac
  guidelines" not "medically certified gluten-free"

**Pages where this applies:** Household Setup (constraint entry), Plan
(rejection explanations), Health Guard Dashboard, nutrition summary displays,
Help/FAQ (medical section), and the Onboarding constraints step.

**In the database:** `member_diagnoses` uses condition keys for guideline
matching — but the UI always frames these as "dietary conditions that affect
your plan," never as "your medical record." The data is a planning input,
not a clinical record.

---

## Status Key

| Symbol | Meaning |
|---|---|
| ✅ Built | Functional and pilot-ready |
| 🔧 Needs Polish | Built but not pilot-friend ready — rough edges |
| 📋 Planned | Designed in schema, not yet coded — stub page recommended |
| 🚧 Coming Soon | Code started or schema ready — show to users with timeline |
| 🔒 Requires Investment | Needs API budget, third-party agreements, or team — honest "Coming Soon" |

---

## Full Site Map

### PUBLIC MARKETING SITE — whollyfare.com (separate from the app)

**Critical architectural distinction:** `whollyfare.com` is the public-facing
marketing site — static, SEO-optimized, no login required. `app.whollyfare.com`
(or `whollyfare.com/app`) is the Streamlit application where households actually
use the product. They are different surfaces with different audiences.

The public site's job is to convert visitors into signups. The app's job is to
deliver value to signed-up households. Conflating them means the app carries
SEO and marketing weight it shouldn't, and the marketing site tries to do
things the app does better.

In the POC, `Home.py` serves both roles. That's fine for the pilot. Separate
them before the 90-day public alpha.

---

#### `whollyfare.com` — Public Home / Landing
**Status:** 📋 Planned as separate surface — currently `Home.py` fills this role

**What it does:** Introduces WhollyFare to a cold visitor. Problem statement,
how it works, pricing tiers, pilot story / social proof, waitlist signup or
get started CTA. Static, fast, SEO-friendly.

**Key sections:**
- Hero: the Found Money number from `platform_weekly_metrics` ("households saved
  $X last week") — live pull, not hardcoded
- The problem (the four competitor bullets from the investor brief)
- How it works (4 steps: setup → prices → plan → shop)
- Tiers & pricing
- Pilot story (the Hislop family data, with permission)
- Coming features (Coupon Vault, Delivery, Health Guard)
- Waitlist CTA for unavailable areas
- Footer: Sincere Strategy link, Privacy Policy, Terms

**Database:** `platform_weekly_metrics` (social proof number), `waitlist` (CTA)

---

#### `whollyfare.com/for-health-systems` — B2B / Health Systems
**Status:** 📋 Planned — one page, Phase 3

**What it does:** Explains the constraint engine licensing opportunity to
hospital nutrition departments, patient advocacy organizations, and employer
wellness programs. The Health Guard tier's constraint engine — CKD, celiac,
diabetes, MCAS, hypertension — is clinical-grade filtering that health systems
would pay to license as a white-label API.

**Key sections:**
- The problem (patients discharged with dietary restrictions and no practical
  grocery tool)
- What WhollyFare licenses (the constraint engine as an API, not the consumer app)
- Use cases (hospital discharge planning, patient advocacy portal, employer
  wellness benefit)
- The Sincere Strategy commitment (no data sharing, ever)
- Medical disclaimer — prominent: "WhollyFare provides dietary planning
  assistance. It is not a clinical nutrition management system or a substitute
  for registered dietitian oversight."
- Contact form → Tim's email

**Database:** `b2b_licenses` (contact form writes here as `'prospect'`)

---

#### `whollyfare.com/privacy` — Privacy Policy & Data Rights
**Status:** 📋 Required before 90-day public alpha

**What it does:** The Sincere Strategy's data commitments in plain English.
Export your data, delete your account, what WhollyFare does and does not share.
This page is a founding commitment made visible — not legal boilerplate.

**Key sections:**
- What we collect (household profiles, plan history, receipts)
- What we never collect (browsing behavior for ads, health data for targeting)
- What we never do (sell, share, or train on your personal data — ever)
- Your rights: export your data (link to Account → Data Export), delete your
  account (link to Account → Delete Account)
- Retention: what data remains after deletion (anonymized price intelligence
  contributions only — explained in plain language)
- Contact for privacy questions: tim.hislop@gmail.com

**Database:** `data_privacy_requests` (export/delete requests initiated here)

---

### AUTH & ONBOARDING — Getting households set up

---

#### `Login.py` / `Signup.py` — Authentication
**Status:** 📋 Required before Phase 2 public access

**What it does:** Email + magic link authentication (Supabase Auth). No
passwords in Phase 2 — magic link is simpler, more secure for a pilot, and
requires fewer data flows. Social login (Google) can be added in Phase 3 if
demand warrants.

**Pages needed:**
- `Login.py` — email entry → "check your email for a magic link"
- `Auth_Confirm.py` — landing page after clicking magic link; redirects to app
- `Signup.py` — new account creation; captures name, zip, tier selection
- `Forgot.py` / `Reset.py` — for when magic link isn't available (Phase 3)

**Database:** `profiles` (created on signup), `invitations` (check for
invitation code at signup), `household_access_tokens` (for pilot-phase token auth)

---

#### `Onboarding.py` — First-Time Walkthrough
**Status:** 📋 Required for 90-day public alpha (named explicitly in 30/60/90 plan)

**What it does:** The "90-second guided walkthrough that lands a user on their
first Sunday Buy-Off in under 3 minutes." A step-by-step wizard that runs
*before* the household is dropped into the full app. Replaces the assumption
that a new user knows to start on the Household Setup page.

**Steps:**
1. Welcome — what WhollyFare does in one sentence
2. Your location — zip code → show nearby supported stores
3. Your household — name, budget, servings, meals/week (simplified from full Household page)
4. Your constraints — one-screen allergen + diagnosis capture (most important fields only)
5. Your stores — pick from the suggested nearby stores
6. Ready — "Your first plan generates Sunday. See you then."

**Design principle:** Onboarding is not the Household Setup page compressed.
It's a separate, simpler flow that gets the *minimum viable profile* entered.
The household can fill in full preferences later. The goal is first Sunday
Buy-Off, not perfection.

**Medical disclaimer:** Visible on the constraints step — "These are planning
inputs, not a medical record. Always consult your doctor for clinical dietary
management."

**Database:** Writes to `households`, `members`, `member_allergies`,
`member_diagnoses`, `household_grocers`. Creates `notification_preferences`
row with defaults. Sets `profiles.onboarding_complete = true` on completion.

---

### THE CORE FLOW — The spine of WhollyFare

These seven pages are the product. Everything else supports or extends them.
A pilot friend should be able to run the full loop — setup to ledger — without
Tim in the room.

---

#### `Home.py` — Landing Page
**Status:** ✅ Built — review messaging after adding new pages

**What it does:** Introduces WhollyFare to a cold visitor. Explains the value
prop, shows the four tiers, explains how it works. The first impression for
both pilot friends and investors.

**What to add as new pages go live:**
- Add a section showing the full feature map (all pages, with Coming Soon labels)
- Update the "How It Works" steps to reference the Coupon Vault when it's live
- Add a "What's Coming" section that links to feature stubs

**Database tables read:** None (static content). Eventually: `feature_flags`
to drive the "Coming Soon" badges dynamically; `platform_weekly_metrics`
for a live "households are saving $X/week" social proof banner.

---

#### `1_Household.py` — Household Setup
**Status:** ✅ Built — pilot-ready

**What it does:** Household name, budget, servings, meals per week. Member
profiles with allergies, diagnoses, lifestyle tags, and custom exclusions.

**What to add when preferences layer is live (Phase 2):**
- Tab 2: "Meal Preferences" — cuisine likes/dislikes, protein rotation limits,
  cooking time, complexity preference, leftovers OK
- Tab 3: "Ingredient Wish List" — positive preferences (sweet potatoes, salmon)

**Database tables written:** `households`, `members`, `member_allergies`,
`member_diagnoses`, `member_lifestyle_tags`, `member_custom_exclusions`

**Future:** `household_meal_preferences`, `household_cuisine_preferences`,
`household_protein_preferences`, `ingredient_preferences`

---

#### `2_Grocer_Hub.py` — Grocer Data Hub
**Status:** ✅ Built — pilot-ready. Add integration status indicators.

**What it does:** Store setup, price loading (manual entry, PDF upload, Kroger
API pull), week selector, engine runner.

**What to add:**
- Integration status badges per store (Kroger API ✅ Connected, Food Lion 📄 PDF, Instacart 🔒 Coming Soon)
- Coupon count badge: "3 coupons available for your plan this week →" (links to Coupon Vault)
- Delivery availability indicator per store

**Database tables read/written:** `household_grocers`, `flyer_weeks`,
`flyer_items`, `household_integrations`, `coupons` (count badge only)

---

#### `3_Plan.py` — This Week's Plan
**Status:** 🔧 Needs Polish — functional, not yet emotionally clear to a cold user

**What it does:** Displays the 5-dinner plan with cost breakdown, ingredient
detail, store routing, and constraint compliance.

**Polish needed:**
- Make constraint compliance section more prominent — this is the safety story
- Add "why this meal" explanations (which sale price drove this choice)
- Add cuisine tags on each meal card

**What to add when ratings are live (Phase 3):**
- Star rating widget on each meal card after the week is complete
- "You've had this before — rated 4★" badge on repeat meals

**Database tables read:** `meal_plans`, `plan_meals`, `meal_ingredients`,
`constraint_rejections`, `meal_history` (repeat detection)

---

#### `4_Sunday_BuyOff.py` — The Sunday Buy-Off
**Status:** 🔧 Needs Polish — the signature moment needs to feel like the
signature moment. Currently functional but not emotionally resonant.

**What it does:** The one screen, one number, one decision moment. Shows Found
Money vs. single-store and HelloFresh. Locks in the plan.

**Polish needed:**
- The Found Money number needs to be bigger and more celebratory
- Competitor comparison table should pull from `competitor_benchmarks` DB table
  instead of hardcoded values — so it can show Dinnerly, EveryPlate, etc.
- Coupon savings line item: "Plus $8.40 in coupons clipped for this week"
- Cumulative savings banner should be more prominent

**What to add:**
- Delivery quote button: "Order for delivery instead? See the cost →"

**Database tables read:** `meal_plans`, `plan_meals`, `meal_ingredients`,
`ledger_entries` (cumulative), `competitor_benchmarks`, `household_coupon_clips`

**Database tables written:** `meal_plans.approved_at`, `ledger_entries`,
`meal_history` (one row per meal on approval), `plan_adherence_log`

---

#### `5_Shopping_List.py` — Shopping List
**Status:** 🔧 Needs Polish — must be usable on a phone in a grocery store.
That is the bar. Currently built but not tested at that bar.

**What it does:** The confirmed shopping list organized by store, with
checkboxes, costs, and coupon callouts.

**Polish needed:**
- Mobile-first layout — larger tap targets, bigger text
- Checkbox state that persists for the session (don't lose ticks on refresh)
- Store subtotals prominent at the top of each store section
- Coupon reminder strip: "Don't forget to clip the Kroger digital coupon for
  chicken breast before checkout"

**What to add:**
- Print/share button — a clean PDF or shareable link
- "Mark all at this store done" button
- Delivery option per store: "Order this section from Kroger instead →"

**Database tables read:** `plan_meals`, `meal_ingredients`, `household_grocers`,
`household_coupon_clips` (reminder strip)

---

#### `6_Ledger.py` — Found Money Ledger
**Status:** ✅ Built — production-quality for pilot

**What it does:** Week-by-week savings history, receipt logging, charts,
cumulative savings, annualized projection, CSV export.

**What to add when trend tables are live:**
- Streak counter (from `household_trend_snapshots.current_streak_weeks`)
- Milestone callouts: "You've now saved over $200 total 🎉"
- Coupon savings as a separate line in the weekly breakdown
- Accuracy trend chart (how close were the estimates over time)
- Plan adherence correlation: "Weeks you followed the store split, you saved
  $18 more on average"

**Database tables read:** `ledger_entries`, `household_trend_snapshots`,
`household_coupon_clips`, `plan_adherence_log`

---

### SAVINGS INTELLIGENCE — What makes WhollyFare smarter than a coupon app

---

#### `9_Coupon_Vault.py` — Coupon Vault
**Status:** 📋 Planned — stub page now, build Phase 2

**What it does:** Shows all available coupons and deals for the household's
configured stores, filtered through the constraint engine (allergen-unsafe
coupons are hidden), surfaced by relevance to the current plan. Households can
"clip" coupons that apply to their plan. Clipped coupons appear in the Shopping
List as reminders.

**The key differentiator vs. Flipp/Ibotta:** Every coupon shown has already
passed the constraint engine. A coupon for a peanut-containing product never
appears for a household with a peanut allergy. Every coupon shown is either in
the current plan or could be added to it. The integration, not the coupon, is
the product.

**Stub page content (before build):**
- Explain the feature and the Flipp/Ibotta problem
- "Coming in Phase 2" timeline
- Email capture for early access

**Database tables read:** `coupons`, `household_coupon_clips`, `flyer_items`,
`member_allergies` (for constraint filtering), `plan_meals` (relevance ranking)

**Database tables written:** `household_coupon_clips`

---

#### `10_Price_Intelligence.py` — Price Intelligence
**Status:** 📋 Planned — data starts collecting now, page builds Phase 3

**What it does:** Shows price trend data from `ingredient_price_history` —
which items have been on sale multiple weeks in a row, which categories are
trending up or down in your market, when to stock up on specific proteins.

**The moat story:** After 6 months of pilot data, WhollyFare knows that chicken
breast at Kroger Barracks Road goes on sale approximately every 3 weeks. After
Phase 2, it knows that across the Charlottesville market. After Phase 4, it has
national pricing intelligence that no meal kit company has.

**Stub page content (before build):**
- "WhollyFare is building a price intelligence database for your market"
- "Every week you load prices, you're contributing to data that will help you
  predict sales before they're announced"
- Show the count: "X price points tracked in your market so far"

**Database tables read:** `ingredient_price_history`, `household_trend_snapshots`

---

#### `11_Market_Insights.py` — Market Insights
**Status:** 📋 Planned — platform-level data, Phase 3

**What it does:** Anonymized regional savings data. "Charlottesville households
using WhollyFare saved an average of $38 last week." Shows your household
relative to the market. Drives the regional market story for investors.

**Stub page content:** A single metric tile: "X households in your market are
using WhollyFare. Their average weekly savings: coming soon."

**Database tables read:** `platform_weekly_metrics`, `households.metro_area`

---

### HEALTH GUARD — The tier that makes WhollyFare irreplaceable for allergy and medical households

---

#### `12_Health_Guard.py` — Health Guard Dashboard
**Status:** 📋 Planned — data exists now, visualization builds Phase 2

**What it does:** Visualizes the constraint engine for the household. Shows
every constraint that's active, which member it protects, how many items were
rejected this week because of it, and what categories of ingredients the
household can and cannot eat.

**Why this matters:** This is the page that makes Health Guard ($19/mo) feel
worth it. An allergy household doesn't just want a plan — they want to see the
engine actively protecting them. "14 items rejected this week because of
peanuts. Abby is protected." That's a different product than a meal kit.

**Stub page content:**
- Show current active constraints from session state
- "Full constraint engine dashboard — Health Guard tier — coming Phase 2"
- Highlight the safety-first philosophy

**Database tables read:** `members`, `member_allergies`, `member_diagnoses`,
`member_lifestyle_tags`, `constraint_rejections`, `meal_plans`

---

### DELIVERY & CHECKOUT — Closing the loop on the full grocery experience

---

#### `13_Delivery_Hub.py` — Delivery Hub
**Status:** 🔒 Requires Investment — Kroger delivery via API is provable now;
Instacart/DoorDash require partner agreements

**What it does:** After Sunday Buy-Off, the household can request a delivery
quote for their shopping list. Shows true cost comparison: pickup vs. Kroger
delivery vs. Instacart vs. DoorDash. WhollyFare never recommends delivery over
pickup — it shows the real numbers and lets the household decide. Sincere
Strategy applies.

**When Kroger delivery is enabled:** The household can place the order directly
from WhollyFare via the Kroger API. The shopping list becomes a cart. One tap.

**Stub page content:**
- "The full loop: WhollyFare finds the savings, then gets the groceries to your
  door — without the Instacart premium markup"
- Show a static cost comparison mock: Pickup $94 / Kroger Delivery $108 /
  Instacart $127
- "Kroger delivery integration: in development"
- "Instacart/DoorDash: coming post-investment"
- Email capture: "Notify me when delivery is live"

**Database tables read:** `household_integrations`, `plan_meals`,
`meal_ingredients`, `delivery_quotes`, `platform_integrations`

**Database tables written:** `delivery_quotes`

---

### FULL TABLE — The complete meal planning experience

---

#### `14_Recipe_Library.py` — Recipe Library
**Status:** 🔒 Requires Investment — Full Table tier, Phase 3

**What it does:** Full recipes for every meal in the plan. Cuisine preference
memory — the planner remembers what you've loved and steers toward it. Meal
history so you never see the same dinner twice in a month unless you want to.

**Stub page content:**
- "Full recipes built around your actual sale prices. Every ingredient in every
  recipe is something you're already buying this week."
- "Cuisine memory: WhollyFare learns what your family loves and plans around it."
- "Full Table tier — launching Phase 3"

**Database tables read:** `plan_meals`, `meal_history`, `meal_ratings`,
`household_cuisine_preferences`, `household_meal_preferences`

---

#### `15_Pantry.py` — Pantry Tracker
**Status:** 🔒 Requires Investment — Full Table tier, Phase 3

**What it does:** Track what's already in your pantry. Ingredients you have
on hand are deducted from the shopping list. The optimizer accounts for pantry
stock when building the plan.

**Stub page content:** "Never buy a second bottle of olive oil you didn't need.
Pantry Tracker — Full Table tier, Phase 3."

---

### ACCOUNT & SETTINGS

---

#### `16_Account.py` — Account & Preferences
**Status:** 📋 Required once Supabase Auth is live

**What it does:** Profile (name, email, zip, location), subscription tier,
notification preferences, meal preferences, connected integrations, data export,
and account deletion. This is where the Sincere Strategy's data commitments
become tangible for the user.

**Tabs:**
- **Profile** — name, email, zip, display name, tier
- **Notifications** — toggle each notification type on/off, preferred channel
- **Meal Preferences** — cuisine likes/dislikes, cooking time, complexity,
  protein rotation (links to the preference layer in Household Setup)
- **Integrations** — connected stores, Kroger API status, Coming Soon (Instacart)
- **Your Data** — export full profile as JSON (writes to `data_privacy_requests`
  with type='export'); delete account (writes type='deletion' with confirmation
  dialog: "This permanently removes all your household data. Price intelligence
  contributions remain anonymized.")
- **Privacy** — summary of what WhollyFare stores and what it doesn't; links to
  Privacy Policy

**Build this immediately after Supabase Auth is wired up.**

**Medical disclaimer:** Not applicable to this page, but the "Your Data" tab
should note that health profile data (diagnoses, allergies) is stored only as
planning inputs and is fully deleted on account deletion.

**Database:** `profiles`, `notification_preferences`, `household_meal_preferences`,
`household_cuisine_preferences`, `household_protein_preferences`,
`household_integrations`, `data_privacy_requests`, `feature_flags`

---

#### `17_Help.py` — Help & FAQ
**Status:** 📋 Planned — required before pilot friends use the app unsupported

**What it does:** Answers the questions pilot friends will ask without Tim in
the room. Not a support ticket system — a curated FAQ. Build from the actual
questions that come up in the Hislop pilot.

**Sections:**
- Getting started (how to set up a household, what each tier does)
- Household & constraints ("what's the difference between an allergy and a
  diagnosis?")
- Grocer Hub ("my PDF didn't parse — what do I do?")
- The plan ("why did the engine pick this meal?")
- Sunday Buy-Off ("what happens when I lock in the plan?")
- Ledger ("how do I log my receipt?")
- Troubleshooting
- Contact: tim.hislop@gmail.com

**Medical disclaimer section:** Prominent, warm, non-legalese —
"WhollyFare helps you plan meals around your family's dietary needs. We're not
doctors, and your plan isn't medical advice. If you have a serious medical
condition, always work with your doctor or a registered dietitian — WhollyFare
is a tool to support that, not replace it."

**Database:** None (static content). Eventually: links to `feature_flags` to
show which features are live vs. coming soon.

---

#### `18_Admin.py` — Internal Admin Dashboard
**Status:** 📋 Planned — Tim's visibility into his own platform

**What it does:** Tim's internal view of the platform — all households, their
activity, platform metrics, integration status, invitation management, waitlist,
and b2b prospects. Gated to Tim's user ID only — no household can access this.

**Sections:**
- Platform metrics (from `platform_weekly_metrics` and `app_events`)
- Household roster — list of all households, their tier, their last active date,
  their weekly savings, their streak
- Invitation manager — send invitations, see which were accepted, revoke tokens
- Waitlist — see who's signed up for which features
- Integration status — Kroger API health, parser status per grocer
- B2B prospects — the `b2b_licenses` table in `'prospect'` and `'negotiating'` status
- Audit log viewer — search the audit log for any household or table

**Database:** Everything — service-role access. This page bypasses RLS by
design; Tim is the service operator.

---

### INVESTOR & PLATFORM

---

#### `7_Investor.py` — Investor Brief
**Status:** ✅ Built — production-quality

**Updates to make:**
- Wire competitor comparison to `competitor_benchmarks` table instead of
  hardcoded values
- Add integration status section: "Proven integrations: Kroger API ✅,
  USDA FDC ✅. In development: Harris Teeter PDF. Planned: Flipp, Ibotta,
  Instacart"
- Add a "Coming Features" section that mirrors the feature_flags table

---

#### `8_Roadmap.py` — Product Roadmap
**Status:** ✅ Built — production-quality

**Updates to make:**
- Ensure Phase 2 section references Coupon Vault and Health Guard Dashboard
- Ensure Phase 3 section references Delivery Hub, Recipe Library, Price
  Intelligence, Market Insights

---

## Construction Sequence

This is the order to build things in after the database is connected. Each step
produces something usable before the next step starts. Steps 1–3 are the
30-day pilot foundation. Steps 4–6 are the 60-day friends-and-family phase.
Steps 7–10 are the 90-day public alpha.

---

### Step 1 — Database foundation
*Goal: pilot data survives a browser refresh*

1. Create Supabase project, configure environment
2. Run schema SQL — Layers 1–6 (auth through ledger), Layer 12 (audit log + privacy)
3. Seed `competitor_benchmarks`, `feature_flags`, `platform_integrations`
4. Enable RLS on all tables; verify service-role bypass for admin
5. Wire `1_Household.py` → `households` + all member/constraint tables
6. Wire `2_Grocer_Hub.py` → `household_grocers`, `flyer_items`, `ingredient_price_history`
7. Wire `4_Sunday_BuyOff.py` → `meal_plans.approved_at`, `ledger_entries`, `meal_history`
8. Wire `6_Ledger.py` → read from `ledger_entries`
9. Wire audit log triggers on health-sensitive tables

**Milestone:** Pilot data survives a browser refresh. Zero allergen violations
are now provable, not just asserted.

---

### Step 2 — Core flow polish
*Goal: pilot friends run a full week without Tim present*

1. Polish `4_Sunday_BuyOff.py` — bigger Found Money number, competitor comparison
   from `competitor_benchmarks` table
2. Polish `3_Plan.py` — add `selection_rationale` display, clearer for cold users
3. Polish `5_Shopping_List.py` — mobile-first layout, coupon reminder strip placeholder
4. Add medical disclaimer component to `3_Plan.py` and `1_Household.py`

**Milestone:** Pilot friends can use the app confidently. First investor-ready
data week.

---

### Step 3 — Historical tracking
*Goal: start building the data moat from day one*

1. `ingredient_price_history` writes on flyer item save
2. `plan_adherence_log` write on receipt logging
3. `household_trend_snapshots` trigger on receipt log
4. Add streak, milestone callouts to `6_Ledger.py`
5. `app_events` writes on plan generation, Buy-Off approval, receipt log

**Milestone:** Price intelligence data starts accumulating. Behavioral
correlation data starts accumulating. The investor story gets stronger
every week from here.

---

### Step 4 — Auth + access tokens (pilot expansion)
*Goal: pilot friends have their own private access, Tim can manage them*

1. Build `household_access_tokens` — Tim generates tokens, texts pilot families
2. Build token-auth middleware in Streamlit (read token from URL, load household)
3. Build `18_Admin.py` — Tim's visibility into all households and activity
4. Build `invitations` table + invite flow for Tim to onboard Phase 2 households
5. Build `waitlist` table + email capture on stub Coming Soon pages

**Milestone:** Tim can invite the 5–10 Phase 2 households without hand-holding.

---

### Step 5 — Coming Soon stubs
*Goal: a first-time visitor sees the full product vision*

1. Build stub pages for all planned features (Coupon Vault, Price Intelligence,
   Health Guard, Delivery Hub, Recipe Library, Market Insights, B2B)
2. Each stub: clear description, timeline, email capture → `waitlist`
3. Drive stub page visibility from `feature_flags` table
4. Build `17_Help.py` with pilot-informed FAQ
5. Add Coming Soon section to `Home.py`

**Milestone:** A new visitor sees a complete product, not a partial app.
Investor Brief becomes more credible.

---

### Step 6 — Full auth + onboarding (public alpha)
*Goal: anyone can sign up without Tim's involvement*

1. Supabase magic link auth — signup, login, email confirmation pages
2. Build `Onboarding.py` — 90-second wizard, 5 steps, first Buy-Off in 3 minutes
3. Build `16_Account.py` — profile, notifications, data export, account deletion
4. Build `whollyfare.com` public marketing site (separate from app)
5. Build `whollyfare.com/privacy` Privacy Policy page
6. Launch `notification_queue` + email provider (Resend or Postmark)
7. Wire weekly plan ready + receipt reminder notifications

**Milestone:** 100 households can sign up without Tim. This is the 90-day alpha.

---

### Step 7 — Preference layer
*Goal: the planner knows what households like, not just what they can't eat*

1. Add preferences tabs to `1_Household.py`
2. Wire all preference tables on save
3. `meal_ratings` capture after each week completes

---

### Step 8 — Coupon Vault (Phase 2)
1. Kroger API digital coupons ingestion → `coupons` table
2. Build `9_Coupon_Vault.py` with constraint engine filtering
3. Wire clipped coupons into Shopping List + Ledger

---

### Step 9 — Health Guard Dashboard (Phase 2)
1. Build `12_Health_Guard.py` — constraint visualization with medical disclaimer
2. Wire `meal_nutrition_summary` from USDA FDC lookups
3. Add nutrition guidance (with disclaimer) to Plan page

---

### Step 10 — Delivery Hub + B2B (Phase 3, post-investment)
1. Kroger delivery quotes via existing API
2. Build `13_Delivery_Hub.py`
3. Launch `whollyfare.com/for-health-systems` B2B page
4. First `b2b_licenses` prospect entered from inbound interest

---

## "Coming Soon" Page Template

For every stub page (Coupon Vault, Delivery Hub, etc.), use this structure
consistently so the site feels intentional rather than incomplete:

```
[Feature icon + name] — Coming [Phase X]

[One paragraph explaining what this feature does and why it matters,
written in WhollyFare voice — honest, specific, no hype]

[What you get today without this feature — so the user understands
the current workaround]

[Timeline or trigger: "This launches in Phase 2 / after investment /
when X households are on the platform"]

[Optional: email capture — "Notify me when this is live"]
```

The key principle: a Coming Soon page is a promise, not a placeholder. It tells
the user exactly what they're waiting for and why it isn't ready yet. That
honesty is the Sincere Strategy applied to the product roadmap.

---

## Database Tables — Quick Reference by Page

| Page | Reads from | Writes to |
|---|---|---|
| Home | `feature_flags`, `platform_weekly_metrics` | — |
| Household Setup | `households`, `members`, all constraint tables | Same |
| Grocer Hub | `household_grocers`, `flyer_items`, `household_integrations` | Same + `flyer_weeks`, `ingredient_price_history` |
| Plan | `meal_plans`, `plan_meals`, `meal_ingredients`, `constraint_rejections` | — |
| Sunday Buy-Off | `meal_plans`, `ledger_entries`, `competitor_benchmarks` | `meal_plans.approved_at`, `ledger_entries`, `meal_history`, `plan_adherence_log` |
| Shopping List | `plan_meals`, `meal_ingredients`, `household_coupon_clips` | — |
| Ledger | `ledger_entries`, `household_trend_snapshots`, `plan_adherence_log` | `ledger_entries` (receipt update) |
| Coupon Vault | `coupons`, `flyer_items`, `member_allergies` | `household_coupon_clips` |
| Price Intelligence | `ingredient_price_history`, `household_trend_snapshots` | — |
| Health Guard | `members`, all constraint tables, `constraint_rejections` | — |
| Delivery Hub | `meal_ingredients`, `household_integrations`, `delivery_quotes` | `delivery_quotes` |
| Recipe Library | `plan_meals`, `meal_history`, `meal_ratings`, `household_cuisine_preferences` | `meal_ratings` |
| Account | `profiles`, `household_meal_preferences`, `household_integrations` | Same |
| Investor Brief | `competitor_benchmarks`, `platform_integrations`, `platform_weekly_metrics` | — |
| Roadmap | `feature_flags` | — |
| Market Insights | `platform_weekly_metrics`, `households.metro_area` | — |

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*
*Use this document alongside DATABASE_SCHEMA.md. Together they are the full
blueprint for the WhollyFare platform — from the pilot running today to the
national product that follows investment.*
