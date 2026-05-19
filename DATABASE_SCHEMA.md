# WhollyFare® — Supabase Database Schema
**Sentir Solutions® LLC · Charlottesville, VA**
*Last updated: May 2026 · Prepared for Supabase + PostgreSQL*

---

## Overview

This document is the single source of truth for WhollyFare's database design.
Every table, column, relationship, and design decision is documented here so
that the transition from Streamlit session_state (POC) to a real persistent
database is fully planned before a line of migration code is written.

The schema is organized into seven layers, moving from the user inward to the
data they generate:

1. **Auth & User** — who is using the app, where they live, their account settings
2. **Household** — the family unit, its shopping location, and its members
3. **Grocers** — stores the household shops at, seeded from location
4. **Flyer & Items** — the weekly price data loaded per store
5. **Meal Plans & Constraint Engine** — the engine output and its audit trail
6. **Ledger** — the real savings history
7. **Store Registry** *(Phase 3)* — the platform-wide catalog of chains and locations that powers store discovery

Supabase handles the `auth.users` table automatically. Everything below lives
in the `public` schema unless noted otherwise.

---

## Layer 1 — Auth & User

### `profiles`
One row per registered user. Extends Supabase's `auth.users` with
WhollyFare-specific fields. Created automatically when a user signs up via
a Supabase Auth database trigger.

This table serves two purposes: (1) the user's account identity, and (2) their
home location, which seeds store discovery during onboarding and eventually
powers regional market analytics — e.g. "Charlottesville households save an
average of $42/week."

**Location here is "where the user lives."** It is separate from where their
household shops (which lives on `households.primary_zip`). They usually match,
but not always — someone might live in one zip and do their weekly grocery run
near their workplace or a different part of town.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | Same UUID as `auth.users.id` |
| `email` | `text` NOT NULL | Mirrors auth.users — denormalized for query convenience |
| `display_name` | `text` | Shown in the app UI |
| `zip_code` | `text` | Home zip code — entered during signup; used to seed store suggestions |
| `city` | `text` | City name — e.g. "Charlottesville" |
| `state` | `text` | 2-letter state abbreviation — e.g. "VA" |
| `metro_area` | `text` | Soft geographic grouping for market analytics — e.g. "Charlottesville, VA". Set by the app from zip lookup, not user-entered. |
| `timezone` | `text` | IANA timezone string — e.g. "America/New_York". Used for Sunday Buy-Off timing and future push notifications. |
| `phone` | `text` | Optional — for future push/SMS notifications |
| `created_at` | `timestamptz` | Default: `now()` |
| `updated_at` | `timestamptz` | Updated via trigger on any row change |
| `tier` | `text` | `'free'` / `'meal_planner'` / `'health_guard'` / `'full_table'` — maps to the 4-tier business model |
| `onboarding_complete` | `boolean` | False until household + at least one grocer are saved |
| `marketing_opt_in` | `boolean` | Default: false — whether the user wants product emails (Sincere Strategy: never for ads or targeting) |
| `acquisition_source` | `text` | How this user found WhollyFare — e.g. `'hislop_pilot'`, `'mcas_support_group'`, `'celiac_community'`, `'word_of_mouth'`, `'invitation'`, `'organic_search'`. Set at signup, never changed. Powers the "Halo of Trust" cohort analysis — do allergy-community signups retain better than general signups? |
| `invited_by` | `uuid` FK → `profiles.id` | Which existing user sent the invitation. Null for organic signups. |

**Supabase RLS policy:** Users can only read and update their own row.
`auth.uid() = id`

**Why `metro_area` is app-set, not user-entered:** In Phase 3, WhollyFare
maps zip codes to metro areas using a reference table (or a zip-to-metro API).
This lets you build market-level reports — "here's what Charlottesville
households saved this week" — without exposing exact home addresses or zip
codes in aggregate queries. It's a privacy-preserving grouping layer.

---

## Layer 2 — Household

A household is the planning unit — the family or group that eats together and
shares constraints, a budget, and a weekly plan. In the pilot, one user = one
household. In Phase 3+, a household may have multiple user logins (e.g. both
parents can access the plan).

### `households`

The household is the planning unit — the family or group that eats together.
It carries both the dietary constraints (via members) and the shopping context
(via location and grocers). The location fields here are "where this household
shops," which seeds grocer suggestions and drives the plan optimizer's store
selection. They are pre-filled from `profiles.zip_code` during onboarding but
can be changed independently — a household might shop at stores in a different
part of town than where they live.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | Generated: `gen_random_uuid()` |
| `name` | `text` NOT NULL | e.g. "The Hislop Family" |
| `weekly_budget_usd` | `numeric(8,2)` NOT NULL | Hard ceiling for the optimizer |
| `servings_per_meal` | `smallint` NOT NULL | Default 4 — how many people eat each dinner |
| `meals_per_week` | `smallint` NOT NULL | Default 5 — dinners to plan each week |
| `primary_zip` | `text` | Zip code of the household's primary shopping area. Pre-filled from `profiles.zip_code` during onboarding. Used to seed the grocer list and, in Phase 3, to auto-suggest nearby stores. |
| `city` | `text` | Shopping city — usually matches user's city but can differ |
| `state` | `text` | 2-letter state |
| `metro_area` | `text` | Soft geographic grouping — set by app from zip lookup, same logic as `profiles.metro_area`. Used for regional market analytics. |
| `created_by` | `uuid` FK → `profiles.id` | The user who created the household |
| `created_at` | `timestamptz` | Default: `now()` |
| `updated_at` | `timestamptz` | Updated via trigger |

**Derived values** (computed in app, not stored):
- `budget_per_meal` = `weekly_budget_usd / meals_per_week`
- `budget_per_serving` = `budget_per_meal / servings_per_meal`

**Why location lives on both `profiles` and `households`:**
`profiles.zip_code` = where the *person* lives (account-level).
`households.primary_zip` = where the *household* shops (plan-level).
They usually match and are seeded from the same value at signup. They diverge
when, for example, both parents share a login but one does the shopping near
their workplace. Keeping them separate avoids a design trap later.

### `household_users`
Join table — which users belong to which household. Enables multi-user
households in Phase 3 without a schema change.

| Column | Type | Notes |
|---|---|---|
| `household_id` | `uuid` FK → `households.id` | |
| `user_id` | `uuid` FK → `profiles.id` | |
| `role` | `text` | `'owner'` or `'member'` — owners can edit settings |
| `joined_at` | `timestamptz` | Default: `now()` |

**PK:** `(household_id, user_id)`

**RLS:** Users can only see households they belong to.

---

## Layer 3 — Household Members

Each household has one or more *members* — the people who eat the meals.
Members are not users. A member is just a name + constraint set attached to
a household. In Phase 3, a member could optionally link to a user account,
but this is not required.

### `members`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `name` | `text` NOT NULL | First name or nickname |
| `age` | `smallint` | Optional — used to adjust serving size guidance for children |
| `display_order` | `smallint` | Controls the order members appear on the Household page |
| `created_at` | `timestamptz` | |

### `member_allergies`
The top-14 allergens, stored one row per allergen per member.
This is a hard-filter list — the constraint engine never violates it.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `member_id` | `uuid` FK → `members.id` NOT NULL | |
| `allergen` | `text` NOT NULL | One of the 14 keys: `peanuts`, `tree_nuts`, `milk`, `eggs`, `wheat`, `soy`, `fish`, `shellfish`, `sesame`, `mustard`, `celery`, `lupin`, `molluscs`, `sulphites` |

**Unique:** `(member_id, allergen)` — can't add the same allergen twice.

### `member_diagnoses`
Medical conditions that activate a specific constraint ruleset in the engine.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `member_id` | `uuid` FK → `members.id` NOT NULL | |
| `diagnosis` | `text` NOT NULL | One of: `celiac`, `type1_diabetes`, `type2_diabetes`, `ckd`, `pku`, `gerd`, `ibs_low_fodmap`, `crohns`, `hypertension`, `mcas`, `eds`, `pots` |

**Unique:** `(member_id, diagnosis)`

### `member_lifestyle_tags`
Dietary preferences and lifestyle choices. These are filters — not hard safety
rules like allergies. The engine applies them where possible.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `member_id` | `uuid` FK → `members.id` NOT NULL | |
| `tag` | `text` NOT NULL | One of: `vegan`, `vegetarian`, `halal`, `kosher`, `keto`, `paleo`, `whole30`, `low_fodmap`, `gluten_free`, `dairy_free` |

**Unique:** `(member_id, tag)`

### `member_custom_exclusions`
Free-text ingredients a member won't eat — personal dislikes, not allergies.
The engine avoids these where safe alternatives exist.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `member_id` | `uuid` FK → `members.id` NOT NULL | |
| `exclusion_text` | `text` NOT NULL | e.g. "Brussels sprouts", "Mushrooms" |
| `created_at` | `timestamptz` | |

---

## Layer 4 — Grocers

The household's configured stores. In the POC these live in
`session_state["grocers"]` as a flat list of dicts. In production, each store
is a row tied to the household.

### `household_grocers`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `chain_name` | `text` NOT NULL | e.g. "Kroger", "Food Lion", "Aldi" |
| `location_description` | `text` | e.g. "Barracks Road, Charlottesville VA 22903" |
| `source_type` | `text` NOT NULL | `'manual'`, `'pdf'`, `'api'`, `'pdf_and_api'` |
| `rewards_enrolled` | `boolean` | Default: false — loyalty/rewards card enrolled |
| `delivery_preferred` | `boolean` | Default: false |
| `is_primary` | `boolean` | Default: false — only one store per household should be primary |
| `flyer_url` | `text` | Weekly circular URL — displayed as a link in the Grocer Hub |
| `display_order` | `smallint` | Controls store card order in the UI |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Constraint:** Only one `is_primary = true` per household (enforced at app layer; add a partial unique index in prod).

---

## Layer 5 — Flyer Data

Each week, the household loads prices from each grocer — by manual entry, PDF
upload, or API pull. This is the raw input the constraint engine and optimizer
consume.

### `flyer_weeks`
A "load session" — one row per store per week. Tracks when the data was loaded
and by what method. Lets the app show "3 of 4 stores loaded for the week of
May 18".

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `grocer_id` | `uuid` FK → `household_grocers.id` NOT NULL | |
| `week_start_date` | `date` NOT NULL | Always a Sunday (ISO week start) |
| `load_method` | `text` NOT NULL | `'manual'`, `'pdf'`, `'api'` — what sourced this load |
| `loaded_at` | `timestamptz` | When the data was loaded |
| `item_count` | `integer` | Denormalized count of items in this load — updated after insert |

**Unique:** `(household_id, grocer_id, week_start_date)` — one load per store per week per household.

### `flyer_items`
Every individual item loaded from a store's circular for a given week. This is
the primary input table to the constraint engine.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `flyer_week_id` | `uuid` FK → `flyer_weeks.id` NOT NULL | |
| `grocer_id` | `uuid` FK → `household_grocers.id` NOT NULL | Denormalized for query performance |
| `name` | `text` NOT NULL | Item name as entered (e.g. "Chicken Breast, Boneless Skinless") |
| `category` | `text` | One of: `produce`, `protein`, `dairy`, `grain`, `legume`, `pantry`, `bakery`, `frozen`, `beverage`, `other` |
| `unit` | `text` | One of: `lb`, `oz`, `each`, `pkg`, `bunch`, `bag`, `dozen`, `gal`, `qt`, `can`, `jar`, `box` |
| `sale_price` | `numeric(8,2)` NOT NULL | The weekly sale price |
| `regular_price` | `numeric(8,2)` | Pre-sale regular price — used to calculate % savings in the Ledger. Nullable (not always known). |
| `allergens` | `text[]` | Array of allergen keys present in this item (user-declared in POC; USDA-verified in prod) |
| `tags` | `text[]` | Freeform tags — e.g. `['organic', 'store_brand']` |
| `usda_fdc_id` | `text` | USDA FoodData Central ID — nullable in POC, populated by enricher in prod |
| `is_manual` | `boolean` | True if entered by hand vs. parsed from PDF or API |
| `created_at` | `timestamptz` | |

**Index:** `(flyer_week_id)` — the engine fetches all items by week in one query.

---

## Layer 6 — Meal Plans & Constraint Engine

The engine output: the weekly dinner plan, the individual meals, their
ingredients, and — critically — every ingredient the engine rejected and why.
The rejection log is the radical transparency feature that makes WhollyFare
trustworthy.

### `meal_plans`
One per household per week. Null `approved_at` means the household has not
yet done their Sunday Buy-Off for this week.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `week_start_date` | `date` NOT NULL | |
| `whollyfare_cost` | `numeric(8,2)` | Engine's estimated total cost for the week |
| `single_store_est` | `numeric(8,2)` | Estimated cost if bought at one store (whollyfare_cost × 1.18 in POC) |
| `hellofresh_equiv` | `numeric(8,2)` | HelloFresh cost for equivalent servings ($9.99/serving) |
| `found_money_est` | `numeric(8,2)` | `single_store_est - whollyfare_cost` |
| `vs_hellofresh_est` | `numeric(8,2)` | `hellofresh_equiv - whollyfare_cost` |
| `total_servings` | `integer` | `meals_per_week × servings_per_meal` — denormalized for Ledger display |
| `approved_at` | `timestamptz` | Null until Sunday Buy-Off button is pressed |
| `created_at` | `timestamptz` | When the engine ran |

**Unique:** `(household_id, week_start_date)` — one plan per household per week.

### `plan_meals`
The individual dinners within a weekly plan.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `plan_id` | `uuid` FK → `meal_plans.id` NOT NULL | |
| `day_label` | `text` NOT NULL | e.g. "Monday", "Tuesday" — display label |
| `day_order` | `smallint` NOT NULL | 1–7 for sort ordering |
| `meal_name` | `text` NOT NULL | e.g. "Herb-Roasted Chicken Thighs" |
| `meal_cost` | `numeric(8,2)` | Sum of ingredient costs for this meal |
| `best_store` | `text` | Primary store for this meal's ingredients |
| `is_gluten_free` | `boolean` | True if all ingredients passed gluten-free constraints |
| `allergen_notes` | `text` | Human-readable summary of constraints applied to this meal |

### `meal_ingredients`
Each ingredient selected for a meal by the optimizer.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `meal_id` | `uuid` FK → `plan_meals.id` NOT NULL | |
| `flyer_item_id` | `uuid` FK → `flyer_items.id` | Null if ingredient was from demo data or a fallback |
| `item_name` | `text` NOT NULL | Denormalized — item name at time of plan generation |
| `quantity` | `text` | e.g. "1 lb", "2 each" |
| `unit` | `text` | |
| `store_name` | `text` | Which store this ingredient comes from |
| `cost` | `numeric(8,2)` | Sale price at time of plan generation |
| `display_order` | `smallint` | Ordering within the meal |
| `selection_rationale` | `text` | Why the optimizer chose this ingredient — e.g. "Best price per serving in protein category · 34% off regular · on sale 3 of last 4 weeks at Kroger." Radical transparency: every selection is explainable. |
| `price_rank` | `smallint` | Where this ranked among safe options in its category (1 = cheapest safe option chosen) |
| `discount_pct` | `numeric(5,2)` | Percentage off regular price at selection time — null if regular price unknown |

### `constraint_rejections`
Every ingredient the constraint engine rejected, and the reason why. This is
the radical transparency feature — the app shows households exactly why
something didn't make it into their plan.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `plan_id` | `uuid` FK → `meal_plans.id` NOT NULL | |
| `flyer_item_id` | `uuid` FK → `flyer_items.id` | The item that was rejected |
| `item_name` | `text` NOT NULL | Denormalized |
| `rejection_reason` | `text` NOT NULL | Human-readable reason e.g. "Contains wheat — celiac constraint for Abby" |
| `rejection_category` | `text` NOT NULL | `'allergen'`, `'diagnosis'`, `'lifestyle'`, `'custom_exclusion'`, `'budget'` |
| `triggered_by_member` | `text` | Member name whose constraint triggered the rejection. Null for budget rejections. |
| `created_at` | `timestamptz` | |

**Index:** `(plan_id)` — the Plan page loads all rejections for a plan in one query.

---

## Layer 7 — Ledger

The Found Money ledger. One entry per approved week. The most important data
in the app for both households (their savings history) and investors (real
household data, not projections).

### `ledger_entries`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `plan_id` | `uuid` FK → `meal_plans.id` NOT NULL | Links back to the plan that generated this entry |
| `week_start_date` | `date` NOT NULL | |
| `meals_planned` | `smallint` | Number of dinners in the approved plan |
| `stores_used` | `text[]` | Array of store names shopped that week |
| `whollyfare_cost_est` | `numeric(8,2)` | Engine's prediction at plan time |
| `found_money_est` | `numeric(8,2)` | Estimated savings at plan time |
| `hellofresh_equiv` | `numeric(8,2)` | HelloFresh cost for equivalent meals |
| `actual_receipt` | `numeric(8,2)` | What the household actually spent — null until logged |
| `single_store_actual` | `numeric(8,2)` | What the same basket would have cost at one store — null until logged |
| `found_money_actual` | `numeric(8,2)` | `single_store_actual - actual_receipt` — null until receipt logged |
| `vs_hellofresh_actual` | `numeric(8,2)` | `hellofresh_equiv - actual_receipt` — null until logged |
| `accuracy_delta` | `numeric(8,2)` | `actual_receipt - whollyfare_cost_est` — how far off the estimate was |
| `notes` | `text` | Household's freeform notes for the week |
| `receipt_logged_at` | `timestamptz` | When the receipt was entered. Null until logged. |
| `created_at` | `timestamptz` | When the Buy-Off was approved |
| `updated_at` | `timestamptz` | Updated when receipt is logged |

**Unique:** `(household_id, week_start_date)` — one ledger entry per household per week.

**Index:** `(household_id, week_start_date DESC)` — the Ledger page always loads entries newest-first.

---

## Layer 8 — Historical Trends & Price Intelligence

This layer is what separates a useful app from a data asset. The tables below
capture the time-series data that answers three distinct questions:

1. **For the household:** "Am I actually saving more by following WhollyFare week over week?"
2. **For the investor:** "Do households that follow WhollyFare consistently save money — and by how much?"
3. **For the platform:** "What are prices doing over time, and which stores consistently win on which categories?"

None of this requires new user input. It is derived from data that already flows
through the app — the key is writing it to the right tables as it happens.

---

### `ingredient_price_history`

The most strategically important table in the entire schema. Every time a
flyer item is saved, a row is also written here. Over weeks, this builds a
proprietary price time-series — item by item, store by store — that no
competitor has without running their own data collection at scale.

This is the data moat. After 6 months of pilot data it starts to show seasonal
patterns. After 12 months you can predict when chicken breast is about to go on
sale. After Phase 4 scale, it is a pricing intelligence layer that grocery
chains themselves would pay for.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `flyer_item_id` | `uuid` FK → `flyer_items.id` | Source item record |
| `chain_name` | `text` NOT NULL | Denormalized — e.g. "Kroger". Allows cross-household aggregation without exposing household identity. |
| `metro_area` | `text` NOT NULL | Denormalized from household — enables regional price trend queries |
| `item_name_normalized` | `text` NOT NULL | Cleaned, lowercased item name for grouping across different spellings. e.g. "chicken breast boneless skinless". Set by app on save. |
| `category` | `text` NOT NULL | e.g. "protein", "produce" |
| `unit` | `text` NOT NULL | e.g. "lb" |
| `sale_price` | `numeric(8,2)` NOT NULL | Price this week |
| `regular_price` | `numeric(8,2)` | Pre-sale price if known |
| `discount_pct` | `numeric(5,2)` | `(regular_price - sale_price) / regular_price * 100` — computed on insert |
| `week_start_date` | `date` NOT NULL | The week this price was observed |
| `usda_fdc_id` | `text` | If resolved — enables cross-store nutrient comparison |
| `created_at` | `timestamptz` | |

**Unique:** `(flyer_item_id)` — one price history row per flyer item.

**Index:** `(item_name_normalized, chain_name, week_start_date)` — the core trend query: "show me chicken breast prices at Kroger over the last 12 weeks."

**Index:** `(metro_area, category, week_start_date)` — the regional category trend query: "what has produce done in Charlottesville this quarter?"

**Privacy note:** This table stores no household identifiers. It aggregates
across all households in a metro area. A household that enters chicken breast
at $2.99/lb at Kroger contributes that data point to a pool — their identity
is never exposed in price queries.

**What this enables over time:**
- "Chicken breast has been on sale 4 of the last 6 weeks at Food Lion" — shown in Grocer Hub
- "Category X is trending up 12% this month in your market" — shown in Sunday Buy-Off
- Optimizer can weight ingredients higher if they've been consistently on sale (anticipate future deals)
- Investor slide: "WhollyFare tracks X,000 price points per week across Y markets"

---

### `plan_adherence_log`

One row per approved week per household. Captures how closely the household
followed the plan — which stores they actually visited, whether they stayed on
budget, and any deviations they noted. This is the "did they follow our
recommendation" data.

In the POC this is entirely optional — logged when the household enters their
receipt. In Phase 3 it could be partially automated via receipt OCR (store
name on the receipt tells you which stores they actually visited).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `ledger_entry_id` | `uuid` FK → `ledger_entries.id` NOT NULL | |
| `week_start_date` | `date` NOT NULL | |
| `stores_visited` | `text[]` | Which stores the household actually shopped at — entered when logging receipt, or inferred from receipt OCR |
| `stores_planned` | `text[]` | Which stores the plan said to shop at — copied from the plan at Buy-Off time |
| `followed_store_split` | `boolean` | True if stores_visited matches stores_planned — rough adherence signal |
| `items_bought_count` | `smallint` | How many of the planned items they confirm buying — optional, entered manually |
| `items_planned_count` | `smallint` | How many items were in the approved plan — copied from plan at Buy-Off time |
| `adherence_score` | `numeric(4,2)` | 0.0–1.0 — `items_bought_count / items_planned_count` if both entered, else null |
| `went_off_plan` | `boolean` | Household self-reports: did you deviate significantly from the plan? |
| `deviation_notes` | `text` | Freetext — "Aldi was out of chicken, substituted at Food Lion" |
| `budget_kept` | `boolean` | `actual_receipt <= households.weekly_budget_usd` — auto-computed when receipt is logged |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Unique:** `(household_id, week_start_date)`

**What this enables:**
- "Households that followed the store split saved an average of $12 more per week than those who didn't"
- Retention signal: if a household starts deviating from the plan, that's a churn risk
- Product insight: if households frequently deviate on a specific store, that store's flyer data or pricing may be the problem

---

### `household_trend_snapshots`

A pre-computed summary per household, updated every time a receipt is logged.
This is what powers the Ledger's trend charts and the annual savings projection
without running an expensive aggregation query every page load.

Think of it as a materialized view — it's always current and always fast.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL UNIQUE | One row per household, updated in place |
| `as_of_date` | `date` NOT NULL | Last date this snapshot was recomputed |
| `total_weeks_planned` | `smallint` | How many weeks a plan was generated |
| `total_weeks_with_receipt` | `smallint` | How many weeks a real receipt was logged |
| `receipt_rate` | `numeric(4,2)` | `total_weeks_with_receipt / total_weeks_planned` — engagement signal |
| `total_found_money_est` | `numeric(10,2)` | Cumulative estimated Found Money (all weeks) |
| `total_found_money_actual` | `numeric(10,2)` | Cumulative actual Found Money (receipt weeks only) |
| `avg_weekly_found_money` | `numeric(8,2)` | Average across receipt weeks — the number shown in the annual projection |
| `projected_annual_savings` | `numeric(10,2)` | `avg_weekly_found_money × 52` |
| `total_vs_hellofresh` | `numeric(10,2)` | Cumulative savings vs. HelloFresh |
| `avg_accuracy_pct` | `numeric(5,2)` | Average estimate accuracy — `1 - (abs(accuracy_delta) / actual_receipt)` |
| `best_week_found_money` | `numeric(8,2)` | Single-week record — shown as a milestone |
| `best_week_date` | `date` | The week of the record saving |
| `current_streak_weeks` | `smallint` | Consecutive weeks with a logged receipt — retention / engagement metric |
| `longest_streak_weeks` | `smallint` | All-time longest consecutive streak |
| `first_week_date` | `date` | When this household started using WhollyFare |
| `latest_week_date` | `date` | Most recent week with a receipt |
| `updated_at` | `timestamptz` | Updated every time a receipt is logged |

**RLS:** Same as `households` — users can only read their own household's snapshot.

**What this enables:**
- Annual savings projection on the Ledger page renders instantly — no aggregation query
- "You've now saved more than $500 total" milestone notification
- "Your best week was $67 saved — week of March 3" — shown in the Ledger
- Streak counter: "🔥 8 weeks in a row" — retention gamification (Full Table tier)
- Investor dashboard: sort all households by `projected_annual_savings` to find your power users

---

### `platform_weekly_metrics`

Aggregate metrics across all households, one row per week. This is WhollyFare's
own operational data — not tied to any individual household. Powers the investor
dashboard and regional market stories.

Written by a scheduled job (Supabase Edge Function or cron) every Monday after
the week closes, aggregating from `ledger_entries` and `meal_plans` across all
households.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `week_start_date` | `date` NOT NULL | |
| `metro_area` | `text` | NULL = national aggregate. Regional rows also written per metro. |
| `households_with_plan` | `integer` | How many households generated a plan this week |
| `households_approved` | `integer` | How many did the Sunday Buy-Off |
| `plan_approval_rate` | `numeric(4,2)` | `households_approved / households_with_plan` |
| `households_with_receipt` | `integer` | How many logged a real receipt |
| `receipt_rate` | `numeric(4,2)` | `households_with_receipt / households_approved` |
| `total_found_money_est` | `numeric(12,2)` | Sum of estimated Found Money across all households this week |
| `total_found_money_actual` | `numeric(12,2)` | Sum of actual Found Money (receipt households only) |
| `avg_found_money_per_household` | `numeric(8,2)` | Mean across receipt households |
| `median_found_money` | `numeric(8,2)` | Median — more honest than mean for investor presentation |
| `avg_accuracy_pct` | `numeric(5,2)` | How close the engine's estimates were to real receipts on average |
| `total_meals_planned` | `integer` | Total dinners planned across all households |
| `total_items_processed` | `integer` | Total flyer items the constraint engine evaluated |
| `total_items_rejected` | `integer` | Total constraint rejections — shows the safety engine is running |
| `created_at` | `timestamptz` | When this row was written |

**Unique:** `(week_start_date, metro_area)` — one row per week per geographic cut.

**RLS:** This table is platform-internal. No household user can query it directly.
Only service-role queries (admin dashboard, investor report generation) can read it.

**What this enables for investors:**
- "WhollyFare households saved a combined $X,XXX last week" — real number, not projection
- "Plan approval rate: 84% — households that see the plan overwhelmingly commit to it"
- "Receipt rate: 71% — nearly 3 in 4 approved households log their actual receipt"
- Week-over-week growth chart as you add Phase 2 pilot households
- Regional breakdown: Charlottesville vs. future markets, side by side

---

## Relationships at a Glance

```
auth.users (Supabase managed)
    └── profiles (1:1)
            │   zip_code / city / state / metro_area  ← account-level location
            │   tier / onboarding_complete
            └── household_users (M:M join)
                    └── households (1:1 in POC, 1:M in Phase 3)
                            │   primary_zip / city / state / metro_area  ← shopping location
                            ├── members (1:M)
                            │       ├── member_allergies (1:M)        ← HARD RULES (safety)
                            │       ├── member_diagnoses (1:M)        ← HARD RULES (safety)
                            │       ├── member_lifestyle_tags (1:M)   ← HARD RULES (lifestyle)
                            │       └── member_custom_exclusions (1:M) ← SOFT RULES (dislikes)
                            ├── household_meal_preferences (1:1)      ← PREFERENCES (soft signals)
                            ├── household_cuisine_preferences (1:M)   ← PREFERENCES
                            ├── household_protein_preferences (1:M)   ← PREFERENCES
                            ├── ingredient_preferences (1:M)          ← PREFERENCES (wish list)
                            ├── meal_history (1:M)                    ← HISTORY (repeat prevention)
                            │       └── meal_ratings (1:1 per meal)   ← FEEDBACK (loop)
                            ├── household_grocers (1:M)
                            │       │   seeded from store_locations on onboarding
                            │       └── flyer_weeks (1:M per grocer per week)
                            │               └── flyer_items (1:M)
                            ├── meal_plans (1 per week)
                            │       ├── plan_meals (1:M)
                            │       │       └── meal_ingredients (1:M)
                            │       └── constraint_rejections (1:M)
                            └── ledger_entries (1 per approved week)
                                    └── FK → meal_plans.id

Store Registry (platform-wide reference data, not per-household):
store_chains (1:M) → store_locations
    └── queried by zip_code / metro_area during onboarding
    └── matched rows copied into household_grocers when user picks their stores
    └── metro_area joins to households.metro_area for regional market analytics

Historical Trends & Price Intelligence (written as data flows in):
flyer_items ──────────────────────────────→ ingredient_price_history
                                                (no household ID — aggregate price data)
ledger_entries ────────→ plan_adherence_log    (did they follow the plan?)
              └────────→ household_trend_snapshots (1:1 per household, updated each receipt)
                                    (platform job, runs weekly) → platform_weekly_metrics
```

---

## Row-Level Security (RLS) Summary

Supabase RLS means a user can only ever read or write their own household's
data — even if they know another household's UUID. This is the data safety
guarantee for the pilot.

Every table in `public` needs two policies:

- **SELECT:** `household_id IN (SELECT household_id FROM household_users WHERE user_id = auth.uid())`
- **INSERT / UPDATE / DELETE:** Same condition — users can only modify their own household's data.

The `profiles` table is simpler: `auth.uid() = id`.

---

## What Goes in JSONB vs. Normalized Columns

Two fields use arrays (`text[]`) rather than separate join tables:
- `flyer_items.allergens` — because allergen lists are read-only after entry, rarely queried individually, and always consumed as a whole set by the constraint engine.
- `flyer_items.tags` — same reason; freeform and not filtered by.
- `ledger_entries.stores_used` — a display list; no queries filter by individual store within a ledger entry.

Everything else — member allergies, diagnoses, lifestyle tags — is normalized
into its own table because the constraint engine filters on individual values
and because future features (e.g. "which households have a CKD member?") need
proper indexing.

---

## POC → Production Migration Map

| POC (session_state key) | Production table | Notes |
|---|---|---|
| `session_state["household"]` | `households` + `members` + all constraint tables | The big one — almost all state lives here |
| `session_state["grocers"]` | `household_grocers` | Flat list → normalized rows |
| `session_state["manual_items"]` | `flyer_items` (is_manual=true) | Keyed by week + store |
| `session_state["flyer_data"]` | `flyer_items` (is_manual=false) | PDF/API parsed items |
| `session_state["active_week"]` | `flyer_weeks.week_start_date` | ISO date string → date column |
| `session_state["plan"]` | `meal_plans` + `plan_meals` + `meal_ingredients` | Plan dict → 3 normalized tables |
| `session_state["filter_result"]` | `constraint_rejections` | Currently lost after engine run |
| `session_state["ledger_history"]` | `ledger_entries` | List of dicts → normalized rows |
| `session_state["approved_weeks"]` | `meal_plans.approved_at` | Boolean set → timestamp |

---

## Layer 7 — Store Registry *(Phase 3 — design now, build later)*

This is the platform-wide catalog of grocery store chains and locations. It is
not per-household — it is WhollyFare's own reference data, used to suggest
stores to new users during onboarding based on their zip code.

In the POC, the Charlottesville presets are hardcoded. In Phase 3, onboarding
becomes: "Enter your zip code → WhollyFare finds the grocery stores near you →
you pick the ones you shop → done." The store registry is what makes that work.

### `store_chains`
The platform-level catalog of grocery chains WhollyFare supports.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `chain_name` | `text` NOT NULL UNIQUE | e.g. "Kroger", "Food Lion", "Aldi", "Harris Teeter" |
| `chain_slug` | `text` NOT NULL UNIQUE | URL-safe key — e.g. `kroger`, `food_lion`, `aldi` |
| `flyer_url_template` | `text` | Weekly circular URL — can include `{zip}` placeholder |
| `api_supported` | `boolean` | Default: false — whether WhollyFare has a live API integration |
| `pdf_supported` | `boolean` | Default: true — whether PDF parsing is supported |
| `logo_url` | `text` | For display in the Grocer Hub store cards |
| `notes` | `text` | Internal notes on parsing quirks, API status, etc. |
| `created_at` | `timestamptz` | |

### `store_locations`
Individual store locations — one row per physical store. Populated from grocer
API directories (Kroger Locations API, etc.) or manually for chains without APIs.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `chain_id` | `uuid` FK → `store_chains.id` NOT NULL | |
| `external_location_id` | `text` | The chain's own location ID — e.g. Kroger store number. Used when pulling API data. |
| `display_name` | `text` | e.g. "Kroger Barracks Road" |
| `address_line` | `text` | Street address |
| `city` | `text` | |
| `state` | `text` | |
| `zip_code` | `text` | The store's zip — used for proximity matching |
| `metro_area` | `text` | Same metro grouping as `profiles` and `households` |
| `latitude` | `numeric(9,6)` | For distance-based store suggestions in Phase 3+ |
| `longitude` | `numeric(9,6)` | |
| `is_active` | `boolean` | Default: true — set false when a store closes |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Index:** `(zip_code)` and `(metro_area)` — the onboarding flow queries by zip or metro to surface nearby stores.

**How this powers onboarding:** When a user enters zip code `22903` during
signup, the query is:
```sql
SELECT sl.*, sc.chain_name, sc.logo_url
FROM store_locations sl
JOIN store_chains sc ON sc.id = sl.chain_id
WHERE sl.zip_code = '22903'   -- exact match first
   OR sl.metro_area = 'Charlottesville, VA'  -- nearby fallback
ORDER BY sc.chain_name;
```
The user picks their stores, and those rows get copied into `household_grocers`
for their household. From that point on, `household_grocers` is the operational
table and `store_locations` is just the reference catalog.

**What this enables long-term:** Regional market stories — "households in the
Charlottesville market are saving an average of $38/week" — become a join
between `ledger_entries` and `households.metro_area`. No personal data exposed.
It's also the foundation for a "stores near me have changed their prices"
alert system if you ever want to go there.

---

## Layer 9 — Meal Planning Preferences

**Critical design distinction:** Layers 2–3 capture what a household *cannot*
eat — allergies, diagnoses, lifestyle constraints. Those are hard rules. The
constraint engine runs them first and never violates them.

This layer captures what a household *wants* to eat — cuisine styles, favorite
proteins, how long they're willing to cook on a Tuesday, which meals they've
loved and want to see again. These are soft signals. The meal planner uses them
to choose *among safe options*, not to override safety rules.

The engine's priority order is always:
1. **Safety** — constraint engine filters out anything unsafe. Non-negotiable.
2. **Budget** — optimizer picks the best value from what's safe.
3. **Preferences** — planner steers toward what the household enjoys, within
   what's safe and on-budget.

Preference data should start being captured from the pilot even if the planner
doesn't act on it yet. The data costs nothing to store, and having 8 weeks of
real preference and rating data when you build the preference-aware planner in
Phase 3 is far better than starting from zero.

---

### `household_meal_preferences`

One row per household. The household-level dials that shape how the planner
builds the week — cooking time, complexity, repeat tolerance, batch cooking.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL UNIQUE | One row per household |
| `max_weeknight_cook_minutes` | `smallint` | How long they're willing to cook on a weeknight. Common values: 30, 45, 60. Default: 45. |
| `complexity_preference` | `text` | `'simple'` (one-pan, minimal prep), `'moderate'` (standard), `'elaborate'` (fine with multi-step). Default: `'moderate'`. |
| `batch_cooking` | `boolean` | Do they like making large batches they can eat across multiple nights? Default: false. |
| `leftovers_ok` | `boolean` | Are they comfortable with the same meal two nights in a row? Default: false. |
| `meal_variety` | `text` | `'high'` (never repeat a meal within 6 weeks), `'moderate'` (ok after 3 weeks), `'low'` (fine repeating weekly). Default: `'moderate'`. |
| `weekend_cooking_different` | `boolean` | Do they want more elaborate meals on weekends? If true, the planner can assign higher-complexity meals to Friday/Saturday. Default: false. |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

---

### `household_cuisine_preferences`

Which cuisines the household likes, dislikes, or never wants to see. The
planner uses these to steer meal selection when multiple safe options exist.
`preference_level` is a -2 to +2 scale so the optimizer can weight, not just
filter.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `cuisine` | `text` NOT NULL | e.g. `'mexican'`, `'italian'`, `'asian'`, `'mediterranean'`, `'american'`, `'indian'`, `'greek'`, `'middle_eastern'`, `'thai'`, `'japanese'`, `'french'`, `'caribbean'`, `'other'` |
| `preference_level` | `smallint` NOT NULL | `-2` = never, `-1` = dislike, `0` = neutral, `1` = like, `2` = love |
| `notes` | `text` | e.g. "kids don't like spicy" — captured from freetext during setup |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Unique:** `(household_id, cuisine)`

**How the planner uses this:** After the constraint engine clears safe options
and the optimizer picks budget-optimal ingredients, the planner scores candidate
meals by cuisine match. A household that loves Mexican and rates Italian as
neutral will see more tacos and fewer pasta dishes when both are equally priced
and safe. A `-2` (never) acts as a soft block — it won't be overridden for
budget reasons, but it's not a safety constraint.

---

### `household_protein_preferences`

How often the household wants each protein type in their weekly plan.
Prevents the planner from serving chicken five nights in a row just because
chicken breast is on sale at every store this week.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `protein_type` | `text` NOT NULL | `'chicken'`, `'beef'`, `'pork'`, `'fish'`, `'shellfish'`, `'lamb'`, `'turkey'`, `'plant_protein'`, `'eggs'` |
| `preference_level` | `smallint` | `-1` = avoid, `0` = neutral, `1` = like, `2` = love |
| `max_per_week` | `smallint` | Max times this protein should appear in a week's plan. e.g. max 2 chicken meals per week. Default: null (no limit). |
| `min_per_month` | `smallint` | Minimum appearances per month — for proteins they love. Default: null. |
| `created_at` | `timestamptz` | |

**Unique:** `(household_id, protein_type)`

**Why this matters:** Without protein rotation limits, the optimizer will
over-index on whatever protein is cheapest that week. Protein preferences give
the optimizer guardrails: "yes, chicken is the best deal this week, but they've
already had it twice — find something else for Thursday."

---

### `ingredient_preferences`

The positive counterpart to `member_custom_exclusions`. Where exclusions say
"never this," ingredient preferences say "yes please, more of this when it's
on sale." The planner uses these to break ties when two safe, budget-optimal
options are otherwise equal.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `ingredient_name` | `text` NOT NULL | e.g. "sweet potatoes", "salmon", "black beans" |
| `preference_level` | `smallint` | `1` = like, `2` = love — no negatives here; those go in `member_custom_exclusions` |
| `notes` | `text` | e.g. "great for tacos", "kids ask for this" |
| `created_at` | `timestamptz` | |

**Note:** This is a household-level positive wish list, not a per-member table.
Per-member negatives live in `member_custom_exclusions`. The reason they're
separate: a positive preference can be overridden by budget or availability;
a negative exclusion cannot.

---

### `meal_history`

Every dinner this household has been served by WhollyFare, in order. This is
what prevents the planner from repeating meals too soon and what builds the
"greatest hits" library over time. Populated automatically when a plan is
approved at Sunday Buy-Off.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `plan_meal_id` | `uuid` FK → `plan_meals.id` | Null if the meal was entered manually (pre-WhollyFare history import) |
| `meal_name` | `text` NOT NULL | Denormalized from plan_meals — preserved even if the plan is deleted |
| `cuisine_tag` | `text` | e.g. `'mexican'`, `'italian'` — used to track cuisine variety over time |
| `primary_protein` | `text` | e.g. `'chicken'`, `'beef'` — used for protein rotation tracking |
| `served_week` | `date` NOT NULL | The week_start_date this meal appeared in the plan |
| `created_at` | `timestamptz` | |

**Index:** `(household_id, served_week DESC)` — the planner queries recent history to avoid repeats.

**Index:** `(household_id, meal_name)` — quick lookup: "have we served this before, and when?"

**How the planner uses this:** Before finalizing the week's meal names, the
planner checks the last N weeks of history. If a meal appears in the last
`household_meal_preferences.meal_variety` window (3, 6, or unlimited weeks),
it's deprioritized in favor of something the household hasn't had recently.

---

### `meal_ratings`

After a meal is served, the household can rate it. One row per meal per week.
This is the feedback loop that makes WhollyFare smarter over time — meals that
consistently get high ratings get surfaced again; meals that consistently get
low ratings are retired from that household's rotation.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `meal_history_id` | `uuid` FK → `meal_history.id` NOT NULL | |
| `meal_name` | `text` NOT NULL | Denormalized |
| `rating` | `smallint` | 1–5 stars |
| `would_repeat` | `boolean` | "Would you want this in the plan again?" — the most actionable signal |
| `notes` | `text` | Freetext — "kids loved it", "too spicy for Chas", "needs more sauce" |
| `rated_by` | `text` | Which household member rated it — optional, for when individual ratings differ |
| `rated_at` | `timestamptz` | |

**Unique:** `(meal_history_id)` — one rating per meal served.

**How ratings feed back into planning:**
- `would_repeat = false` → meal is soft-blocked from future plans (household can override)
- `rating >= 4` consistently → meal is eligible for "greatest hits" rotation
- Ratings also inform the platform over time: if 80% of households rate a particular meal
  5 stars, it becomes a recommended template for new households

---

## Layer 10 — Coupons & Deal Harvesting

The investor problem statement names Flipp and Ibotta directly: "grocery apps
surface coupons but have zero integration with meal planning." This is
WhollyFare's answer — coupon data filtered through your household's constraints
and applied directly to your plan.

The difference: Flipp shows you a coupon for chicken. WhollyFare shows you that
coupon *only if* chicken is already in your plan, it's safe for your household,
and it drops your weekly cost below the HelloFresh equivalent. That integration
is the feature. Coupons alone are noise; coupons inside a constraint-aware plan
are Found Money.

---

### `coupons`

Platform-wide coupon catalog. Populated from store circulars (manual or parsed),
the Kroger API (digital coupons available via their API today), and eventually
Flipp/Ibotta API integrations.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `chain_name` | `text` NOT NULL | Which grocer chain this coupon is for |
| `store_location_id` | `uuid` FK → `store_locations.id` | Null = valid chain-wide; set = location-specific |
| `item_name` | `text` NOT NULL | Item name as listed on the coupon |
| `item_name_normalized` | `text` | Cleaned name for matching against `ingredient_price_history` |
| `category` | `text` | e.g. `'protein'`, `'produce'` |
| `discount_type` | `text` NOT NULL | `'pct'` (percentage off), `'dollar'` ($ off), `'bogo'` (buy one get one), `'fixed_price'` (item for $X) |
| `discount_value` | `numeric(6,2)` NOT NULL | The discount amount. For `'pct'`: 0.15 = 15% off. For `'dollar'`: 1.50 = $1.50 off. |
| `final_price` | `numeric(8,2)` | For `'fixed_price'` type — the price after coupon |
| `requires_loyalty_card` | `boolean` | Default: false — requires store rewards card to redeem |
| `digital_only` | `boolean` | Default: false — must be clipped digitally (no paper) |
| `clip_url` | `text` | URL to clip the digital coupon if applicable |
| `valid_from` | `date` NOT NULL | When the coupon becomes valid |
| `valid_to` | `date` NOT NULL | Expiry date |
| `source` | `text` NOT NULL | `'store_circular'`, `'kroger_api'`, `'flipp'`, `'ibotta'`, `'store_app'`, `'manual'` |
| `allergens` | `text[]` | Allergens present in this item — so the constraint engine can screen coupons |
| `week_start_date` | `date` | The flyer week this coupon was sourced from |
| `created_at` | `timestamptz` | |

**Index:** `(chain_name, week_start_date)` — Coupon Vault loads by store and week.

**Index:** `(item_name_normalized, valid_to)` — match coupons to plan ingredients.

---

### `household_coupon_clips`

Which coupons a household has clipped or plans to use. One row per coupon per
household. The Coupon Vault page writes here when a user clips a deal.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `coupon_id` | `uuid` FK → `coupons.id` NOT NULL | |
| `plan_id` | `uuid` FK → `meal_plans.id` | Which plan this coupon was applied to. Null if clipped but not yet assigned. |
| `clipped_at` | `timestamptz` | When the household clipped it |
| `used_at` | `timestamptz` | Null until confirmed used. Set when the household logs their receipt. |
| `confirmed_savings` | `numeric(6,2)` | Actual savings from this coupon — entered when receipt is logged |
| `created_at` | `timestamptz` | |

**Unique:** `(household_id, coupon_id)` — a household clips each coupon once.

**What this enables:** The Found Money Ledger can show "WhollyFare found you
$12.40 in coupons this week on top of cross-store savings." Coupon savings
become a separate line item in the ledger — distinct from sale-price savings,
which matters for the investor story.

---

## Layer 11 — Integrations

The investor problem statement's third and fourth bullets — Instacart/DoorDash
and Kroger API — both require a layer that tracks what external systems
WhollyFare is connected to, per household and platform-wide.

WhollyFare has already proven the Kroger API works. This layer formalizes that
connection in the database and creates the foundation for delivery and third-
party coupon integrations.

---

### `platform_integrations`

Platform-wide registry of every external system WhollyFare connects to or plans
to. Not per-household — this is the admin record of what's live, in development,
or planned. Powers the "Coming Soon" badges on the Delivery Hub and Coupon Vault
pages.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `integration_key` | `text` NOT NULL UNIQUE | e.g. `'kroger_api'`, `'instacart'`, `'doordash'`, `'flipp'`, `'ibotta'`, `'usda_fdc'`, `'food_lion_pdf'` |
| `display_name` | `text` NOT NULL | e.g. "Kroger API", "Instacart", "USDA FoodData Central" |
| `integration_type` | `text` NOT NULL | `'grocer_api'`, `'delivery'`, `'coupon'`, `'nutrition'`, `'location'` |
| `status` | `text` NOT NULL | `'live'`, `'beta'`, `'in_development'`, `'planned'`, `'requires_investment'` |
| `description` | `text` | One-line description shown in the UI |
| `logo_url` | `text` | For display in the Integrations page |
| `api_docs_url` | `text` | Reference link for developers |
| `expected_release` | `text` | e.g. "Phase 3", "Q3 2026" — shown on Coming Soon pages |
| `notes` | `text` | Internal notes on API status, rate limits, costs |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Seed data (insert at setup):**

| key | type | status |
|---|---|---|
| `kroger_api` | grocer_api | **live** — proven in POC |
| `food_lion_pdf` | grocer_api | live — PDF parser built |
| `aldi_manual` | grocer_api | live — manual entry |
| `harris_teeter_pdf` | grocer_api | in_development |
| `usda_fdc` | nutrition | beta — enricher built |
| `flipp` | coupon | planned |
| `ibotta` | coupon | planned |
| `instacart` | delivery | requires_investment |
| `doordash` | delivery | requires_investment |
| `kroger_delivery` | delivery | in_development — same API key as grocer_api |

---

### `household_integrations`

Per-household connection state — which integrations a specific household has
authorized or connected. The Kroger API, for example, requires the household's
location_id. Instacart would require an OAuth token.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `integration_key` | `text` NOT NULL | Matches `platform_integrations.integration_key` |
| `status` | `text` NOT NULL | `'connected'`, `'disconnected'`, `'error'`, `'pending_auth'` |
| `external_location_id` | `text` | The store's own location ID — e.g. Kroger store number, Instacart retailer ID |
| `last_synced_at` | `timestamptz` | When data was last successfully pulled |
| `error_message` | `text` | Last error if status = 'error' — shown in Grocer Hub |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Note on credentials:** OAuth tokens, API keys, and secrets are **never stored
in this table.** They live in Supabase Vault (POC/Phase 2) or AWS Secrets
Manager (Phase 3+). This table stores only non-sensitive connection metadata.

**Unique:** `(household_id, integration_key)`

---

### `delivery_quotes`

When a household requests a delivery estimate — "what would it cost to have
Kroger deliver my shopping list?" — the quote is stored here. Allows the
Delivery Hub page to show a comparison: cross-store pickup vs. Kroger delivery
vs. Instacart premium delivery.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `plan_id` | `uuid` FK → `meal_plans.id` NOT NULL | The plan whose shopping list was quoted |
| `integration_key` | `text` NOT NULL | Which delivery service quoted this (`'kroger_delivery'`, `'instacart'`, `'doordash'`) |
| `items_quoted` | `integer` | How many shopping list items were included in the quote |
| `subtotal` | `numeric(8,2)` | Item cost via this service |
| `delivery_fee` | `numeric(6,2)` | Delivery fee |
| `service_fee` | `numeric(6,2)` | Platform/service fee |
| `tip_suggested` | `numeric(6,2)` | Suggested tip — included in "true cost" calculation |
| `total_est` | `numeric(8,2)` | Full cost to the household including all fees |
| `vs_whollyfare_pickup` | `numeric(8,2)` | `total_est - meal_plans.whollyfare_cost` — the convenience premium |
| `delivery_window` | `text` | e.g. "Today 2–4pm", "Tomorrow morning" |
| `quote_expires_at` | `timestamptz` | Delivery quotes expire quickly |
| `quoted_at` | `timestamptz` | When this quote was fetched |

**What this enables:** The Delivery Hub can honestly say: "Your WhollyFare plan
costs $94 to shop yourself. Kroger delivers it for $108 ($14 convenience
premium). Instacart delivers it for $127 ($33 premium). You decide." That framing
aligns with the Sincere Strategy — WhollyFare shows the real cost of convenience
without pushing either choice.

---

### `competitor_benchmarks`

Formalizes the HelloFresh $9.99/serving comparison that's currently hardcoded
in the app. Adds other meal-kit services so the investor brief and Sunday
Buy-Off can show a richer comparison as the competitive landscape shifts.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `service_name` | `text` NOT NULL UNIQUE | e.g. `'hellofresh'`, `'blue_apron'`, `'dinnerly'`, `'factor'`, `'everyplate'`, `'instacart_express'` |
| `display_name` | `text` NOT NULL | e.g. "HelloFresh", "Blue Apron" |
| `service_type` | `text` NOT NULL | `'meal_kit'`, `'delivery_premium'`, `'subscription_box'` |
| `price_per_serving` | `numeric(6,2)` NOT NULL | Current standard price per serving |
| `min_servings_per_week` | `smallint` | Minimum order to get the quoted price |
| `as_of_date` | `date` NOT NULL | When this price was verified |
| `source_url` | `text` | Where the price was confirmed — for citation |
| `is_active` | `boolean` | Default: true — set false if service shuts down |
| `notes` | `text` | e.g. "First box discount excluded; standard plan pricing" |
| `updated_at` | `timestamptz` | |

**Seed data:**

| service | price/serving | as of |
|---|---|---|
| HelloFresh | $9.99 | 2026-05 |
| Blue Apron | $9.99 | 2026-05 |
| Dinnerly | $4.99 | 2026-05 |
| EveryPlate | $4.99 | 2026-05 |
| Factor (prepared) | $12.99 | 2026-05 |

**How it's used:** `meal_plans.hellofresh_equiv` is computed as
`total_servings × competitor_benchmarks.price_per_serving WHERE service_name = 'hellofresh'`.
In Phase 3, the Sunday Buy-Off comparison table can pull from this table instead
of a hardcoded constant — and can show multiple services side by side.

---

### `feature_flags`

Controls which features are visible to which households, and powers the "Coming
Soon" badges across the site. In the POC, this table seeds the UI labels. In
Phase 3, it gates access by tier.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `feature_key` | `text` NOT NULL UNIQUE | e.g. `'coupon_vault'`, `'delivery_hub'`, `'recipe_library'`, `'price_intelligence'` |
| `display_name` | `text` NOT NULL | Shown in the UI |
| `status` | `text` NOT NULL | `'live'`, `'beta'`, `'coming_soon'`, `'requires_investment'` |
| `tier_required` | `text` | `'free'`, `'meal_planner'`, `'health_guard'`, `'full_table'` — null = all tiers |
| `description` | `text` | One-line description for Coming Soon cards |
| `expected_phase` | `text` | e.g. `'Phase 2'`, `'Phase 3'` |
| `created_at` | `timestamptz` | |

**Seed data:**

| key | status | tier | phase |
|---|---|---|---|
| `household_setup` | live | free | Phase 1 |
| `grocer_hub` | live | free | Phase 1 |
| `meal_plan` | live | meal_planner | Phase 1 |
| `sunday_buyoff` | live | meal_planner | Phase 1 |
| `shopping_list` | live | meal_planner | Phase 1 |
| `found_money_ledger` | live | free | Phase 1 |
| `health_guard_dashboard` | coming_soon | health_guard | Phase 2 |
| `coupon_vault` | coming_soon | meal_planner | Phase 2 |
| `price_intelligence` | coming_soon | meal_planner | Phase 3 |
| `delivery_hub` | requires_investment | meal_planner | Phase 3 |
| `recipe_library` | requires_investment | full_table | Phase 3 |
| `meal_ratings` | coming_soon | full_table | Phase 3 |
| `pantry_tracker` | requires_investment | full_table | Phase 3 |
| `market_insights` | coming_soon | free | Phase 3 |

---

## Phase 3 Additions (Not Built Yet — Noted for Planning)

These tables are not part of the initial Supabase setup but are anticipated in the schema to avoid structural rework:

- **`pantry_items`** — ingredients the household already has at home; deducted from the shopping list.
- **`shopping_list_items`** — the confirmed shopping list after Buy-Off approval; separate from plan ingredients to allow edits post-approval.

---

## Layer 12 — Evidence Sources & Medical Transparency

Before safety and compliance — because this shapes how every health-related
constraint is presented to the user.

**The design principle:** WhollyFare does not make medical claims. It implements
dietary guidelines published by recognized medical authorities, cites those
sources inline, and gives the user a direct link to read the original guidance
themselves. The user decides whether to apply it. WhollyFare is out of the
final determination.

This is the Sincere Strategy applied to health data. Every constraint rejection
should be able to say: "This item conflicts with [Member]'s hypertension
constraint. WhollyFare limits sodium following the American Heart Association's
hypertension dietary guidelines. [Read the AHA guideline →]" The user clicks,
reads the actual source, and makes their own call. WhollyFare never stands
between the user and the authority.

---

### `constraint_evidence_sources`

Platform-wide catalog mapping every diagnosis, allergen, and lifestyle tag to
the authoritative guideline WhollyFare uses when applying that constraint. One
row per condition per authority. Maintained by WhollyFare — updated when
guidelines are revised.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `constraint_key` | `text` NOT NULL | The diagnosis, allergen, or lifestyle tag this source applies to — e.g. `'hypertension'`, `'celiac'`, `'ckd'`, `'peanuts'`, `'type2_diabetes'` |
| `constraint_type` | `text` NOT NULL | `'diagnosis'`, `'allergen'`, `'lifestyle'` |
| `authority_name` | `text` NOT NULL | The issuing organization — e.g. "American Heart Association", "Celiac Disease Foundation", "National Kidney Foundation", "Monash University" |
| `guideline_name` | `text` NOT NULL | Full name of the guideline document — e.g. "Dietary Approaches to Stop Hypertension (DASH)" |
| `guideline_url` | `text` NOT NULL | Direct link to the guideline. Users click this to read the original source. |
| `plain_english_summary` | `text` NOT NULL | One sentence WhollyFare shows in the UI: "WhollyFare limits sodium to under 1,500mg per serving for households with hypertension, following AHA DASH guidelines." |
| `what_whollyfare_implements` | `text` NOT NULL | Specific rule WhollyFare applies from this guideline — e.g. "Excludes ingredients flagged high-sodium (>480mg/serving). Caps meal-level sodium at 1,500mg per serving." Makes the constraint auditable. |
| `disclaimer` | `text` NOT NULL | Per-source disclaimer shown with the link — e.g. "This is a planning guideline, not medical advice. Your doctor or registered dietitian has final authority over your dietary management." |
| `last_reviewed_at` | `date` NOT NULL | When WhollyFare last confirmed this source is current. Guidelines change — WhollyFare must review annually. |
| `is_active` | `boolean` | Default: true. Set false if a guideline is superseded or the source changes. |
| `created_at` | `timestamptz` | |
| `updated_at` | `timestamptz` | |

**Seed data (initial values to implement at launch):**

| key | authority | guideline |
|---|---|---|
| `hypertension` | American Heart Association | DASH Dietary Approach |
| `ckd` | National Kidney Foundation | KDOQI Nutrition Guidelines |
| `type2_diabetes` | American Diabetes Association | Standards of Medical Care in Diabetes |
| `type1_diabetes` | American Diabetes Association | Standards of Medical Care in Diabetes |
| `celiac` | Celiac Disease Foundation | Gluten-Free Diet Guidelines |
| `ibs_low_fodmap` | Monash University | Low FODMAP Diet Program |
| `gerd` | American College of Gastroenterology | GERD Management Guidelines |
| `crohns` | Crohn's & Colitis Foundation | Diet, Nutrition & IBD |
| `pku` | National PKU Alliance | PKU Dietary Management |
| `peanuts` | Food Allergy Research & Education (FARE) | Top 9 Allergen Guidelines |
| `celery` | Anaphylaxis Campaign (UK) | Celery Allergy Guidance |
| `mcas` | American Academy of Allergy, Asthma & Immunology | MCAS Management |
| `vegan` | Academy of Nutrition and Dietetics | Vegetarian/Vegan Diets Position Paper |
| `halal` | Islamic Food and Nutrition Council of America | Halal Certification Standards |
| `kosher` | Orthodox Union | Kosher Certification Standards |

**How this appears in the UI:** Every constraint rejection card, every Health
Guard Dashboard constraint entry, and every nutrition threshold note shows:

> *"[Item] contains [ingredient] which conflicts with [Member]'s hypertension
> constraint. WhollyFare applies this filter following the American Heart
> Association's DASH dietary guidelines.* ***[Read the AHA guideline →]***
> *This is a planning tool — your doctor has the final say."*

The link opens in a new tab. WhollyFare never interprets the guideline for the
user — it just applies the filter and cites the source.

---

Now add `evidence_source_id` to `constraint_rejections` and `meal_nutrition_summary`.

*(See those tables above for where this field appears in context.)*

**Addition to `constraint_rejections`:**
Add `evidence_source_id uuid FK → constraint_evidence_sources.id` — which
guideline triggered this rejection. This makes every rejection fully traceable
to a source the user can read.

**Addition to `meal_nutrition_summary`:**
Add `hypertension_source_id`, `ckd_source_id`, `diabetes_source_id` — or more
cleanly, a `nutrition_thresholds_applied jsonb` field listing which guideline
IDs were used to evaluate each nutrient threshold in this meal summary.

---

## Layer 13 — Safety, Audit & Compliance

These tables honor the Sincere Strategy's founding commitments. They are not
optional features — they are the evidence that WhollyFare is what it claims
to be. The 30/60/90 plan names "zero allergen violations" as an exit criterion.
The Sincere Strategy names data deletion as a founding right. Both require
database infrastructure to be provable, not just asserted.

---

### `audit_log`

Every write to health-sensitive data is logged here — member constraints,
plan approvals, ingredient selections. This is how you prove "zero allergen
violations" to an investor or a regulator. It is impossible to reconstruct
retroactively; it must be in place from the first production write.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `table_name` | `text` NOT NULL | Which table was written to — e.g. `'member_allergies'`, `'meal_plans'`, `'constraint_rejections'` |
| `record_id` | `uuid` NOT NULL | The PK of the row that was written |
| `action` | `text` NOT NULL | `'insert'`, `'update'`, `'delete'` |
| `old_values` | `jsonb` | Previous row state — null for inserts |
| `new_values` | `jsonb` | New row state — null for deletes |
| `changed_by` | `uuid` FK → `profiles.id` | Which user made the change. Null for system actions. |
| `changed_at` | `timestamptz` | Default: `now()` |
| `session_context` | `text` | e.g. `'household_setup'`, `'engine_run'`, `'receipt_log'` — which part of the app triggered this |
| `ip_address` | `text` | Hashed — never stored plain. For fraud/abuse detection only, never surfaced to users. |

**Which tables are audited:** `member_allergies`, `member_diagnoses`,
`member_lifestyle_tags`, `meal_plans`, `meal_ingredients`, `constraint_rejections`,
`ledger_entries`, `data_privacy_requests`.

**RLS:** No user can query this table. Service-role only. Admin dashboard reads it.

**Implementation:** Supabase database trigger on each audited table. The trigger
fires on INSERT/UPDATE/DELETE and writes to `audit_log` automatically — no
application code required.

**Investor use:** "Every plan WhollyFare has ever generated is auditable. We
can prove that no ingredient violating a documented constraint has ever appeared
in a household's plan." That sentence requires this table.

---

### `data_privacy_requests`

Sincere Strategy commitment #6: "Users can export their complete profile and
delete their account at any time." This table is the audit trail for those
requests — when they were made, when they were fulfilled, and what was done.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → `profiles.id` NOT NULL | |
| `request_type` | `text` NOT NULL | `'export'` or `'deletion'` |
| `status` | `text` NOT NULL | `'pending'`, `'processing'`, `'completed'`, `'failed'` |
| `requested_at` | `timestamptz` | Default: `now()` |
| `completed_at` | `timestamptz` | When the request was fulfilled |
| `export_url` | `text` | For export requests — temporary signed URL to the data package. Expires after 48 hours. |
| `deletion_scope` | `jsonb` | For deletion requests — which tables were cleared, in what order |
| `notes` | `text` | Internal notes if there was an issue |

**Target SLA:** Export requests fulfilled within 24 hours. Deletion requests
within 72 hours. Both timelines displayed on the Data & Privacy page.

**On deletion:** WhollyFare deletes all personally identifying data — profile,
household, members, constraints, plans, ledger — but retains anonymized,
aggregated contributions to `ingredient_price_history` and
`platform_weekly_metrics`, as these contain no PII and removing them would
corrupt the platform's market analytics. This policy is disclosed on the
Privacy page.

---

### `household_access_tokens`

For the 60-day friends-and-family phase before full accounts exist. Each pilot
household gets a private URL containing a token that grants access to their
household's session without a username or password. Simpler than OAuth,
appropriate for a trusted 5–10 person pilot.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `token` | `text` NOT NULL UNIQUE | Cryptographically random token. Used in the URL: `?token=abc123` |
| `created_by` | `uuid` FK → `profiles.id` | Tim's user ID — he generates these |
| `created_at` | `timestamptz` | |
| `expires_at` | `timestamptz` | Tokens expire — 90 days is reasonable for pilot |
| `last_used_at` | `timestamptz` | Helps Tim see which pilot households are active |
| `revoked_at` | `timestamptz` | Null until explicitly revoked |
| `notes` | `text` | e.g. "Martinez family — celiac pilot" |

**How it works:** Tim creates a token for each pilot family, texts them the URL.
The app reads the token from the URL, looks it up in this table, and loads the
correct household's data. No password. No OAuth. When accounts go live (Phase 3),
tokens are migrated to full user accounts.

---

## Layer 13 — Notifications & Communications

Every "notify me when" feature in the website blueprint needs a destination. This
layer provides it — a queue-based notification system that handles email, in-app,
and eventually push notifications consistently across all features.

---

### `notification_preferences`

Per-user notification settings. One row per user.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → `profiles.id` NOT NULL UNIQUE | |
| `weekly_plan_ready` | `boolean` | Default: true — email when this week's plan is generated |
| `receipt_reminder` | `boolean` | Default: true — reminder to log receipt 3 days after Buy-Off |
| `coupon_alert` | `boolean` | Default: true — alert when new coupons match the current plan |
| `price_drop_alert` | `boolean` | Default: false — alert when a watched ingredient drops in price |
| `savings_milestone` | `boolean` | Default: true — celebrate when total savings hits $100, $250, $500, $1000 |
| `feature_announcements` | `boolean` | Default: true — new features, Coming Soon launches |
| `weekly_digest` | `boolean` | Default: false — Sunday summary of the week's plan and savings |
| `preferred_channel` | `text` | `'email'` (default), `'push'` (Phase 3), `'sms'` (Phase 4) |
| `quiet_hours_start` | `time` | e.g. `22:00` — don't send push notifications after this time |
| `quiet_hours_end` | `time` | e.g. `07:00` |
| `updated_at` | `timestamptz` | |

---

### `notification_queue`

Every notification WhollyFare sends — email, push, in-app — passes through
this queue. Writing to this table is how application code triggers a
notification; a background worker (Supabase Edge Function) reads from it and
sends. This decouples notification delivery from the application request cycle.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → `profiles.id` NOT NULL | |
| `notification_type` | `text` NOT NULL | e.g. `'plan_ready'`, `'receipt_reminder'`, `'coupon_match'`, `'savings_milestone'`, `'feature_launch'` |
| `channel` | `text` NOT NULL | `'email'`, `'push'`, `'in_app'` |
| `subject` | `text` | Email subject line or push notification title |
| `body` | `text` | Notification content — plain text or HTML for email |
| `metadata` | `jsonb` | Contextual data — e.g. `{"week": "2026-05-18", "found_money": 42.50}` |
| `status` | `text` | `'pending'`, `'sent'`, `'failed'`, `'suppressed'` (user opted out) |
| `scheduled_for` | `timestamptz` | When to send — null = send immediately |
| `sent_at` | `timestamptz` | When it was actually sent |
| `error_message` | `text` | If status = 'failed' |
| `created_at` | `timestamptz` | |

**RLS:** Users can read their own in-app notifications. Email/push rows are
service-role only.

---

### `email_events`

Tracks email delivery outcomes — sent, opened, clicked, bounced. Populated by
the email service provider webhook (Resend, Postmark, or similar). Keeps
WhollyFare's sender reputation healthy and lets Tim see which notification
types are actually read.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `notification_queue_id` | `uuid` FK → `notification_queue.id` | |
| `user_id` | `uuid` FK → `profiles.id` | |
| `event_type` | `text` NOT NULL | `'delivered'`, `'opened'`, `'clicked'`, `'bounced'`, `'unsubscribed'`, `'spam_reported'` |
| `email_address` | `text` | Hashed — never stored plain for privacy |
| `occurred_at` | `timestamptz` | |
| `metadata` | `jsonb` | e.g. `{"link_clicked": "shopping_list"}` |

---

## Layer 14 — Growth & Expansion

The 60-day plan is built on invitations. The 90-day public alpha is built on
organic signups and community outreach. This layer provides the database
infrastructure for both.

---

### `invitations`

Tim sends invitations to pilot households. Households invite friends. This table
tracks every invitation, whether it was accepted, and who referred whom — which
is the referral chain that powers the "Halo of Trust" cohort analysis.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `invited_by` | `uuid` FK → `profiles.id` NOT NULL | Who sent the invitation |
| `email_address` | `text` NOT NULL | Invitee's email |
| `invitation_code` | `text` NOT NULL UNIQUE | Short alphanumeric code included in the invitation URL |
| `household_id` | `uuid` FK → `households.id` | If the invitee is joining an existing household (e.g. second parent) vs. creating a new one |
| `message` | `text` | Personal note from Tim or the inviting household — shown on the signup page |
| `status` | `text` NOT NULL | `'pending'`, `'accepted'`, `'expired'` |
| `accepted_by` | `uuid` FK → `profiles.id` | Set when the invitee creates their account |
| `sent_at` | `timestamptz` | |
| `accepted_at` | `timestamptz` | |
| `expires_at` | `timestamptz` | Default: 30 days |

---

### `waitlist`

For capturing interest from website visitors before a feature or the product
itself is available in their area. Each "Coming Soon" page captures an email.
This is the organic demand signal before paid marketing ever starts.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `email_address` | `text` NOT NULL | |
| `zip_code` | `text` | Where they are — for geographic launch sequencing |
| `interest_tag` | `text` | Which feature or page they signed up from — e.g. `'delivery_hub'`, `'coupon_vault'`, `'general'` |
| `dietary_context` | `text` | Free-text: "I have celiac and two kids with allergies" — optional, shows product-market fit |
| `source` | `text` | Which page or channel — e.g. `'coming_soon_delivery'`, `'mcas_community_post'` |
| `notified_at` | `timestamptz` | When we emailed them that the feature went live |
| `created_at` | `timestamptz` | |

**Unique:** `(email_address, interest_tag)` — one waitlist entry per feature per person.

---

## Layer 15 — Business Model & Analytics

---

### `subscription_events`

WhollyFare's payment processor (Stripe is the obvious choice) handles billing.
But mirroring key billing events into the database means the app can show
subscription status without hitting Stripe on every page load, and gives Tim
a single source of truth for business metrics.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` FK → `profiles.id` NOT NULL | |
| `event_type` | `text` NOT NULL | `'trial_started'`, `'subscribed'`, `'upgraded'`, `'downgraded'`, `'cancelled'`, `'reactivated'`, `'payment_failed'`, `'payment_recovered'` |
| `from_tier` | `text` | Previous tier — null for new subscriptions |
| `to_tier` | `text` | New tier |
| `mrr_impact` | `numeric(8,2)` | Monthly recurring revenue change from this event — positive for upgrades, negative for cancellations |
| `stripe_event_id` | `text` UNIQUE | Stripe's event ID — for deduplication |
| `occurred_at` | `timestamptz` | When the billing event happened |
| `notes` | `text` | e.g. "Cancelled — said they couldn't afford it" from a support ticket |

**What this enables:** MRR dashboard, churn rate, upgrade/downgrade paths —
all queryable from within WhollyFare without Stripe API calls.

---

### `loyalty_rewards_events`

Rewards card savings — Kroger fuel points, Food Lion MVP discounts, Harris
Teeter VIC card pricing — are a real component of WhollyFare's Found Money
story that currently goes uncaptured. A gallon of gas at $0.30 off because
of Kroger points earned through WhollyFare's plan is savings WhollyFare
helped generate. This table captures it.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `household_id` | `uuid` FK → `households.id` NOT NULL | |
| `ledger_entry_id` | `uuid` FK → `ledger_entries.id` | Which week's shopping generated these rewards |
| `grocer_id` | `uuid` FK → `household_grocers.id` | |
| `chain_name` | `text` NOT NULL | Denormalized |
| `reward_type` | `text` NOT NULL | `'fuel_points'`, `'loyalty_discount'`, `'digital_coupon'`, `'member_price'`, `'cashback'` |
| `points_earned` | `integer` | For point-based programs — null for direct discounts |
| `dollar_value` | `numeric(6,2)` | Estimated dollar value of the reward. For fuel points, use the household's reported redemption value. |
| `notes` | `text` | e.g. "400 Kroger fuel points → saved $0.40/gal on 15 gal = $6.00" |
| `logged_at` | `timestamptz` | |

---

### `app_events`

Anonymous product telemetry. The 30/60/90 plan explicitly requires it: "count
plans generated, plans approved, average Found Money — nothing identifying."
This table is the structured version of that commitment.

No names, no household IDs, no personal data. Household identity is replaced
with a daily rotating hash — enough to count unique households without
identifying any of them.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `event_name` | `text` NOT NULL | e.g. `'plan_generated'`, `'buyoff_approved'`, `'receipt_logged'`, `'coupon_clipped'`, `'page_viewed'` |
| `metro_area` | `text` | Geographic grouping — not zip, not city. Coarse enough to be non-identifying. |
| `tier` | `text` | Which subscription tier — for feature usage analytics |
| `found_money_value` | `numeric(8,2)` | For plan events — the Found Money amount. Null for non-plan events. |
| `occurred_at` | `timestamptz` | |
| `app_version` | `text` | Which version of the app generated this event |

**RLS:** No user can query this table. Admin dashboard and platform analytics only.

**What this enables:**
- "WhollyFare has generated X plans since launch" — front page social proof
- "Average Found Money per plan: $42" — investor slide, calculated from real events
- Funnel: plans generated → buy-offs → receipts logged → retention
- Feature adoption: how many households used Coupon Vault in week 1?

---

### `b2b_licenses`

The CLAUDE.md roadmap references "health system B2B licensing" in Phase 3+.
The Sincere Strategy's health constraint engine — which handles CKD, celiac,
diabetes, MCAS, EDS, POTS — is a clinical-grade dietary filter that hospital
nutrition departments and patient advocacy organizations would pay for as a
licensed service. This table is the placeholder. One row per license
agreement.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `organization_name` | `text` NOT NULL | e.g. "UVA Health System", "Celiac Disease Foundation" |
| `organization_type` | `text` | `'health_system'`, `'patient_advocacy'`, `'insurance'`, `'employer_wellness'` |
| `contact_name` | `text` | Primary contact |
| `contact_email` | `text` | |
| `license_type` | `text` | `'constraint_engine_api'`, `'white_label'`, `'data_partnership'` |
| `status` | `text` | `'prospect'`, `'negotiating'`, `'active'`, `'expired'` |
| `monthly_fee` | `numeric(10,2)` | Contract MRR |
| `households_licensed` | `integer` | How many households this license covers |
| `start_date` | `date` | |
| `end_date` | `date` | |
| `notes` | `text` | |
| `created_at` | `timestamptz` | |

---

### `meal_nutrition_summary`

The 30/60/90 plan names USDA FoodData Central integration as an explicit
90-day workstream. The schema has `usda_fdc_id` on `flyer_items`, but there's
nowhere to store what that lookup returns at the meal level. This table fills
that gap — aggregated nutrition per meal, derived from the USDA data for each
ingredient.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `plan_meal_id` | `uuid` FK → `plan_meals.id` NOT NULL UNIQUE | |
| `calories_per_serving` | `integer` | |
| `protein_g` | `numeric(6,1)` | Grams of protein per serving |
| `carbs_g` | `numeric(6,1)` | |
| `fat_g` | `numeric(6,1)` | |
| `fiber_g` | `numeric(6,1)` | |
| `sodium_mg` | `numeric(8,1)` | Critical for hypertension constraint households |
| `potassium_mg` | `numeric(8,1)` | Critical for CKD constraint households |
| `phosphorus_mg` | `numeric(8,1)` | Critical for CKD |
| `sugar_g` | `numeric(6,1)` | Important for diabetes households |
| `usda_coverage_pct` | `numeric(5,2)` | What percentage of ingredients in this meal had USDA FDC data. < 80% = treat nutrition data as estimates. |
| `computed_at` | `timestamptz` | When the USDA lookup was run |

**Why this matters for health constraints:** The constraint engine currently
uses hard ingredient exclusions for CKD, hypertension, and diabetes. The
nutrition summary lets the engine also flag meal-level thresholds — "this
meal's sodium per serving is 1,240mg, which is above the typical low-sodium
guideline." That is nutritional information, not a medical claim.

**Sincere Strategy / Medical Disclaimer alignment:** Nutrition data from this
table is always displayed as *informational guidance*, never as clinical
prescription. UI copy is: "This meal is estimated at X mg sodium per serving
— informational only. Consult your doctor or dietitian for clinical dietary
management." WhollyFare is a planning tool, not a medical service. The hard
constraint engine (allergen exclusions, diagnosis-based ingredient filtering)
is a safety feature of the product — it is not a substitute for medical
oversight. The nutrition summary layer is one level below that: useful guidance
that the household can act on as they see fit.

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*
*This document is the design spec for the Supabase database layer. The next step is: create the Supabase project, run the SQL to build these tables, enable RLS, and wire the Streamlit pages to use the client.*
