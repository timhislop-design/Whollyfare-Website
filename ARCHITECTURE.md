# WhollyFare® — Application Architecture
*Sentir Solutions® LLC · Last updated: 2026-05-29*

This document is the living map of the WhollyFare application. Update it whenever a page is added, a module changes its role, a new table is added, or a key function is renamed. It is meant to be read by Tim, future developers, and Claude at the start of every session.

---

## System Overview

```
User browser (Streamlit Cloud)
    │
    ├── ui/Home.py                     ← Landing page (unauthenticated)
    └── ui/pages/                      ← Authenticated app pages
           │
           ├── Session State (ui/state.py)    ← In-memory working store
           │       └── Supabase (PostgreSQL)  ← Durable backup
           │
           ├── app/core_logic/                ← Constraint engine + planner
           ├── app/data/                      ← Recipe library + store data
           └── integrations/                  ← Kroger API + PDF parsers
```

**Deployment:** Streamlit Community Cloud (share.streamlit.io). Tim pushes to GitHub; Cloud auto-redeploys in ~60 seconds. Tim does NOT run the app locally.

**Auth:** Supabase Auth (email + password). Session keys `_user_id`, `_user_email`, `_user_tier`, `_user_created_at` are set at sign-in.

---

## Page Inventory

| # | File | Title | Status | Notes |
|---|------|--------|--------|-------|
| — | `ui/Home.py` | Landing | ✅ | Hero, pricing tiers, auth CTAs. Fork+leaf SVG. 612 lines — bash-replace only. |
| 0 | `ui/pages/0_This_Week.py` | This Week Dashboard | ✅ | Post-login home. Onboarding flow if setup incomplete. Tonight's Dinner card. Primary retention mechanic. |
| 1 | `ui/pages/1_Household.py` | Household Setup | ✅ | Member profiles, allergies, diagnoses, lifestyle tags. Step 2 of 3 CTA. Supabase wired. |
| 2 | `ui/pages/2_Grocer_Hub.py` | Grocer Hub | ✅ | 4 store tiers, zip filtering, trip cost display, PDF parse review, Kroger API pull. |
| 3 | `ui/pages/3_Plan.py` | This Week's Plan | ✅ | Single-column layout, rationale lines, sale-affinity recipe selection, tier-gated. 972 lines — bash-replace only. |
| 4 | `ui/pages/4_Sunday_BuyOff.py` | Sunday Buy-Off | ✅ | Approve / Swap / Skip per meal, net Found Money, skip hints when gas > savings, Supabase wired. |
| 5 | `ui/pages/5_Shopping_List.py` | Shopping List | ✅ | Mobile-first 2-col layout, per-store sections, weekly regulars, pantry check, CSV/TXT export. 916 lines — bash-replace only. |
| 6 | `ui/pages/6_Ledger.py` | Found Money Ledger | ✅ | Net savings, milestones, streak tracker, CSV export, Supabase wired. |
| 7 | `ui/pages/7_Investor.py` | Investor Brief | ✅ | Production-quality investor narrative. |
| 8 | `ui/pages/8_Roadmap.py` | Product Roadmap | ✅ | 5-phase visual roadmap. |
| 9 | `ui/pages/9_Account.py` | Account | ✅ | Sign in, create account, zip/radius settings, tier display. |
| 10 | `ui/pages/10_Pantry.py` | My Pantry | ✅ | Tier 1 pantry staples (checkboxes), Tier 2 weekly regulars (sale hints). |
| 11 | `ui/pages/11_Admin.py` | Admin: Circulars | ✅ | Admin-gated. Tim's weekly workflow: PDF upload → Claude Vision extraction → preview → save to platform tables + Supabase. |
| 12 | `ui/pages/12_Recipes.py` | Recipe Library | ✅ | This Week tab, Tonight's Dinner, Claude Haiku recipe steps (cached per session). |
| 13 | `ui/pages/13_Help.py` | Help & FAQ | ✅ | Searchable FAQ, contact form (Gmail SMTP + Supabase feedback table). FAQ content in `FAQ_SECTIONS` list at top. |

**Sidebar nav structure:**
- Primary (5): 📅 This Week · 🍽️ My Plan · ✅ Review & Approve · 🛒 Shopping List · 💰 Savings
- Expanders: 🏡 My Household (Household, My Stores, My Pantry, Recipes, Help & FAQ, About, My Account, Admin)
- Coming Soon: Health Guard · Coupon Vault · Price Intelligence · Delivery Hub
- Investor Vision: Investor Brief · Product Roadmap

**Post-login flow:** sign-in → `0_This_Week.py` (if setup complete) or `1_Household.py` (if not).

---

## Freemium Tier System

| Value | Tier Name | Price | Access |
|-------|-----------|-------|--------|
| `free` | Price Finder | Free | Price comparison, weekly savings report |
| `meal_planner` | Meal Planner | $7/mo | This Week's Plan, Sunday Buy-Off, Shopping List |
| `health_guard` | Health Guard | $19/mo | Dietary constraint engine (hard rules) |
| `full_table` | Full Table | $29/mo | Recipes, cuisine preferences, pantry, meal history |

**Trial:** 7 days from `profiles.created_at` = full `meal_planner` access (computed in app, not stored).

**Key functions in `ui/state.py`:**
- `get_user_tier()` → `str` — reads `_user_tier` session key
- `trial_days_remaining()` → `int`
- `has_access(min_tier)` → `bool` — used for tier gates on pages
- `is_on_trial()` → `bool`
- `is_admin()` → `bool` — checks `ADMIN_EMAILS` list (POC: tim.hislop@gmail.com)

**Upgrading a pilot household:** `UPDATE profiles SET tier = 'meal_planner' WHERE email = '...';` in Supabase SQL editor.

---

## Data Flow: Flyer → Plan → Shopping List

```
Tim (Admin page)
    │
    ├── PDF upload + "Extract with Claude"
    │       └── claude_extractor.py
    │               └── PyMuPDF renders pages → JPEG ≤ 2048px
    │               └── Claude Haiku (claude-haiku-4-5-20251001) returns JSON
    │               └── IngredientCandidate objects stored in session flyer_data
    │
    ├── Kroger API pull (Grocer Hub or Admin)
    │       └── integrations/kroger/
    │               └── Barracks Rd location ID: 01200441
    │               └── ~239 items per pull
    │
    └── "Save items" → platform_flyer_weeks + platform_flyer_items (Supabase)
                       + flyer_data (session state)

User (This Week's Plan page)
    │
    ├── flyer_data loaded from session (platform items visible to all auth'd users)
    │
    ├── ConstraintEngine.filter(candidates, household_profile)
    │       └── Allergens → hard exclusion
    │       └── Diagnoses → tag-based exclusion (celiac→gluten, CKD→high-potassium, etc.)
    │       └── Lifestyle tags → tag-based exclusion (vegan→meat, halal→pork, etc.)
    │       └── Custom exclusions → name-match exclusion
    │       └── Every rejection logged with reason + triggering member
    │
    ├── MealPlanner.assemble_week(filtered_candidates, household_profile, preferences)
    │       └── dietary identity → filters protein pool (vegan gets plant proteins only)
    │       └── protein pool round-robin (variety across 5 meals)
    │       └── 4-pass recipe selection per meal:
    │               Pass 1: protein match + preferred cuisine + unused cuisine
    │               Pass 2: protein match + unused cuisine (any)
    │               Pass 3: protein match (any cuisine)
    │               Pass 4: any unused recipe (highest sale-affinity first)
    │       └── sale_affinity_score = count of on-sale non-pantry ingredients in recipe
    │       └── weekly_shopping basket: deduplicated, total cost per item, category preserved
    │
    ├── Plan stored in session_state["plan"]
    │       └── plan["meals"] — list of meal dicts
    │       └── plan["weekly_shopping"] — deduplicated purchase list (primary shopping source)
    │       └── plan["weekly_budget"], ["total_cost"], ["found_money"]
    │
    └── Sunday Buy-Off → Approve / Swap / Skip each meal
                └── net_found_money() = gross savings − total trip costs
                └── skip hint: if store savings < trip cost for that store

Shopping List (_build_cart in 5_Shopping_List.py)
    │
    ├── PRIMARY SOURCE: plan["weekly_shopping"] — already deduplicated, has category + cost
    │       └── One cart entry per (item, store) — no per-meal duplication
    │
    └── SECONDARY SOURCES: weekly regulars, pantry check items
```

---

## Core Logic Modules

### `app/core_logic/constraint_engine.py`

**`IngredientCandidate`** (dataclass) — the universal data shape for any sale item:
```python
name: str
usda_fdc_id: Optional[str]
allergens: list[str]          # e.g. ["milk", "soy"]
nutrition: dict               # {"calories": 52, "protein_g": 1.2}
sale_price_per_unit: float
unit: str                     # "lb", "oz", "each"
standard_unit_weight_g: float
category: str                 # "produce", "protein", "grain", "dairy", "legume"
tags: list[str]               # ["vegan", "gluten-free", "low-fodmap", ...]
```

**`FilterResult`** — `passed: list[IngredientCandidate]`, `rejected: list[dict]`

**`ConstraintEngine`** — `.filter(candidates, household)`:
- Allergen exclusion (Top-14 EU + extras)
- Diagnosis exclusions (via `DIAGNOSIS_EXCLUSIONS` dict — celiac, T2D, CKD, PKU, GERD, IBS, Crohn's, hypertension)
- Lifestyle tag exclusions (vegan, vegetarian, halal, kosher, whole30, etc.)
- Custom exclusion text match

---

### `app/core_logic/meal_planner.py`

**Key module-level constants:**

`FLAVOR_PLUGINS` — cuisine → flavor pairings and ingredients

`PROTEIN_POOL_FOR_IDENTITY` — dietary identity → allowed protein keywords:
```python
{
  "vegan":        {"chickpeas", "tofu", "lentils", "tempeh", "edamame", "jackfruit"},
  "vegetarian":   {"eggs", "chickpeas", "tofu", "lentils", ...},
  "pescatarian":  {"salmon", "shrimp", "tuna", "cod", "tilapia", ...},
  None:           {"chicken", "beef", "pork", "salmon", "shrimp", ...}  # omnivore
}
```

`PLANT_PROTEIN_PANTRY_FALLBACK` — synthetic IngredientCandidates injected when vegan/vegetarian household has no on-sale plant proteins:
```python
{
  "vegan":      [chickpeas, tofu, lentils, black beans],
  "vegetarian": [eggs, chickpeas, tofu, lentils],
}
```

**Key methods on `MealPlanner`:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `_dietary_flags()` | `dict` | Reads `lifestyle_tags` from all members; returns `{vegan, vegetarian, halal, ...}` flags |
| `_household_dietary_identity()` | `str\|None` | Most restrictive tag: vegan > vegetarian > pescatarian > keto > paleo > whole30 |
| `_sale_affinity_score(recipe, sale_names)` | `int` | Count of on-sale non-pantry ingredients in recipe; tiebreaker for recipe selection |
| `_compatible_flavor_plugins()` | `list[str]` | Cuisines compatible with dietary flags |
| `assemble_week(candidates, ...)` | `WeeklyPlan` | Full plan assembly: filter proteins, select recipes, build shopping basket |
| `_compose_meal_name(...)` | `str` | Human-readable meal name |
| `_estimate_cost_per_serving(...)` | `float` | Budget math |

**`ScoredIngredient`** (dataclass):
```python
ingredient: IngredientCandidate
nutrition_score: float
value_score: float
sale_savings_pct: float
score_breakdown: dict
```

---

### `app/core_logic/profile_schema.py`

**`LifestyleTag`** (Enum): `vegan, vegetarian, pescatarian, halal, kosher, whole30, low-fodmap, paleo, keto`

**`Diagnosis`** (Enum): `celiac, type1_diabetes, type2_diabetes, ckd, pku, gerd, ibs_low_fodmap, crohns, hypertension`

**`MemberProfile`**: `name, age, allergies, diagnoses, lifestyle_tags, custom_exclusions`

**`HouseholdProfile`**: `household_name, members, weekly_budget_usd, servings_per_meal, meals_per_week, grocer`

---

### `app/core_logic/claude_extractor.py`

**`extract_uploaded_pdf(file_bytes, store_chain, api_key, max_pages)`**
- Renders PDF pages via PyMuPDF (fitz) at dynamic zoom: `min(1.0, 2048/longest_edge)`, JPEG 80%
- Sends base64-encoded images to Claude Haiku (`claude-haiku-4-5-20251001`)
- Returns list of `IngredientCandidate`-ready dicts
- Claude API limit: 5MB/image; typical Food Lion/Giant pages = 300–600KB

**`merge_into_flyer_data(result, store_key, flyer_data)`** — merges extraction results into the session `flyer_data` dict.

---

### `app/data/recipe_library.py`

**183 total recipes** across 8 collections:

| Collection | Count | IDs |
|-----------|-------|-----|
| MEXICAN | ~25 | MEX-* |
| ITALIAN | ~25 | ITA-* |
| ASIAN | ~25 | ASN-* |
| AMERICAN | ~25 | AMR-* |
| MEDITERRANEAN | ~23 | MED-* |
| VEGAN | 12 | VGN-* |
| VEGETARIAN | 10 | VGT-* |
| PESCATARIAN | 11 | PSC-* |

`ALL_RECIPES = MEXICAN + ITALIAN + ASIAN + AMERICAN + MEDITERRANEAN + VEGAN + VEGETARIAN + PESCATARIAN`

**Important:** `_BY_ID = {}` is defined as empty dict early in file; `_BY_ID.update({r["id"]: r for r in ALL_RECIPES})` is called at the end of file after all lists are assembled. Never move this initialization above the recipe list definitions.

**Key functions:**
- `recipes_for_sale_items(sale_items)` → recipes matching available proteins
- `query_recipes(vegan, vegetarian, pescatarian, cuisine, protein_keyword)` → filtered list
- `get_recipe_by_id(id)` → single recipe dict

**Recipe dict shape:**
```python
{
  "id": "VGN-MEX-001",
  "name": str,
  "cuisine": str,
  "category": "weeknight" | "weekend",
  "servings": int,
  "proteins": list[str],        # ["chickpeas"]
  "tags": list[str],            # ["vegan", "gluten-free"]
  "ingredients": [
    {"name": str, "qty": float, "unit": str}
  ]
}
```

---

### `app/data/store_directory.py`

**`CHARLOTTESVILLE_STORES`** — 12 stores with: `chain, location, flyer_url, method, tier, notes, flyer_day`

**Methods:** `"kroger_api"` | `"pdf"` | `"manual"`

**Flyer days:** Wednesday (Food Lion, Aldi, HT, Lidl, Whole Foods), Friday (Giant, Walmart), Sunday (Wegmans)

**Convenience lookups:** `PDF_STORES`, `WEDNESDAY_STORES`, `STORE_BY_CHAIN`

---

### `app/data/store_regions.py`

**`CHARLOTTESVILLE_CHAINS`** — chains in the Charlottesville metro

**`chains_for_zip(home_zip)`** — zip-prefix → regional chain list (used by Grocer Hub to filter tiers 1–3)

**`region_label(zip)`** — human-readable region name

---

### `ui/state.py` (1,881 lines — bash string-replace only)

Central session state manager. Every page calls `state.init()` at top.

**Key session state keys:**
```
household          — HouseholdProfile dict
grocers            — list of selected stores
flyer_data         — {store_key: [IngredientCandidate dicts]} — the live sale item pool
flyer_meta         — {store_key: {week, method, item_count}}
plan               — full WeeklyPlan dict (meals + weekly_shopping + budget)
approved_weeks     — list of approved week dicts
ledger_history     — list of ledger entry dicts
active_week        — current ISO week string
home_zip           — user's home zip (set in Account page)
store_radius_mi    — search radius for zip-based store filtering
travel_radius_mi   — trip cost calculation radius
household_pantry   — list of pantry staple strings
weekly_regulars    — list of {name, qty, unit, store_pref} dicts
_user_id           — Supabase auth user ID
_user_email        — user email
_user_tier         — "free" | "meal_planner" | "health_guard" | "full_table"
_user_created_at   — ISO datetime string (for trial calculation)
_is_admin          — bool (set at sign-in)
```

**Key functions:**
| Function | Purpose |
|----------|---------|
| `init()` | Set all session state defaults |
| `net_found_money()` | Gross savings − total trip costs |
| `trip_cost_for_store(grocer)` | `distance_mi * 2 * $0.22/mile` |
| `approve_week_db()` | Saves approved week to Supabase ledger |
| `save_flyer_items(chain, candidates, week, method)` | Persists to platform_flyer_weeks + platform_flyer_items |
| `get_user_tier()` | Returns current user tier string |
| `has_access(min_tier)` | Tier gate check |
| `is_on_trial()` | True if within 7-day trial |
| `trial_days_remaining()` | Days left in trial |
| `is_admin()` | True if email in ADMIN_EMAILS |
| `save_household / load_household` | Supabase profile persistence |
| `sign_in / sign_up / sign_out` | Auth flow |
| `PANTRY_DEFAULTS` | ~40 standard pantry staple strings |
| `WEEKLY_REGULARS_DEFAULTS` | list of {name, qty, unit, store_pref} dicts |

---

### `ui/style.py` (377 lines — bash string-replace only)

| Function | Purpose |
|----------|---------|
| `inject()` | Global CSS + WhollyFare brand styles (called on every page) |
| `page_header(title, subtitle)` | Standard page header with WhollyFare logo mark |
| `sidebar_nav()` | Full nav with all 11+ pages + coming-soon items |
| `scroll_to_top()` | JS-based scroll reset |
| `maybe_scroll_to_top()` | Conditional scroll on page rerun |

---

## Supabase Schema (migrations/schema_phase1.sql + migration_002_platform_flyers.sql)

### Phase 1 Tables (schema_phase1.sql)

| Layer | Table | Purpose |
|-------|-------|---------|
| 1 | `profiles` | Mirrors auth.users. Has `tier text DEFAULT 'free'`, `is_platform_admin bool`. Auto-created by trigger on signup. |
| 2 | `households` | One per family. Has `pantry_items JSONB`. |
| 2 | `household_users` | Links auth users to households (Phase 3: multi-user). |
| 3 | `members` | Individual household members with name, age. |
| 3 | `member_allergies` | Top-14 allergen records per member. |
| 3 | `member_diagnoses` | Medical diagnoses per member. |
| 3 | `member_lifestyle_tags` | Lifestyle tags (vegan, halal, etc.) per member. |
| 3 | `member_custom_exclusions` | Free-text ingredient exclusions per member. |
| 4 | `household_grocers` | Stores saved by household, with `distance_mi`, `trip_cost`. |
| 5 | `flyer_weeks` | **Legacy** — per-household flyer week header. Superseded by platform tables. |
| 5 | `flyer_items` | **Legacy** — per-household sale items. Superseded by platform tables. |
| 6 | `meal_plans` | Weekly plan header (session → Supabase in Phase 2). |
| 6 | `plan_meals` | Individual meals in a plan. |
| 6 | `meal_ingredients` | Ingredients per meal. |
| 6 | `constraint_rejections` | Logged rejections (Sincere Strategy transparency). |
| 7 | `ledger_entries` | Weekly Found Money records with gross/net savings. |
| 8 | `ingredient_price_history` | Price tracking over time (Phase 2). |
| 8 | `plan_adherence_log` | Did household follow the plan? (Phase 2). |
| 12 | `constraint_evidence_sources` | Evidence citations for medical constraint rules. |
| 13 | `audit_log` | Immutable audit trail on health-sensitive tables. |
| 13 | `data_privacy_requests` | GDPR/CCPA deletion requests. |
| 13 | `household_access_tokens` | Secure access tokens for household sharing. |
| Ref | `platform_integrations` | Grocer API configs. |
| Ref | `competitor_benchmarks` | HelloFresh + Instacart pricing (for Found Money math). |
| Ref | `feature_flags` | Rollout flags. |

### Platform Flyer Tables (migration_002_platform_flyers.sql)

| Table | Purpose |
|-------|---------|
| `platform_flyer_weeks` | One row per (chain, week). Tim writes as service_role. All auth'd users read. |
| `platform_flyer_items` | One row per sale item. Deleted + re-inserted on each upload (no stale items). |

**Architecture shift (May 2026):** Flyer data is now operator-managed, not per-household. Tim loads circulars once per week; all users see the same platform prices.

---

## Integrations

| Directory | What it does |
|-----------|-------------|
| `integrations/kroger/` | Live Kroger product API. Credentials in Streamlit secrets. Location ID for Barracks Rd: `01200441`. ~239 items per pull. |
| `integrations/food_lion/` | Food Lion PDF parser |
| `integrations/giant/` | Giant PDF parser |
| `integrations/walmart/` | Walmart parser |
| `integrations/wegmans/` | Wegmans parser |
| `integrations/flipp/` | Flipp integration (Phase 2 — not yet active) |

---

## Dietary Identity Layer (added May 2026)

The constraint engine has always handled **clinical constraints** (allergies, diagnoses). The dietary identity layer adds **lifestyle identity filtering** on top of the recipe selection layer.

```
Flyer pool
    │
    ├── ConstraintEngine (hard rules — allergens, diagnoses, custom exclusions)
    │       └── passed: IngredientCandidate[]
    │
    └── MealPlanner._household_dietary_identity()
            └── "vegan" | "vegetarian" | "pescatarian" | "keto" | "paleo" | "whole30" | None
            │
            ├── Filter protein pool to identity-allowed proteins (PROTEIN_POOL_FOR_IDENTITY)
            │
            ├── If vegan/vegetarian and no on-sale plant proteins:
            │       inject PLANT_PROTEIN_PANTRY_FALLBACK (chickpeas, tofu, lentils, eggs)
            │
            └── Recipe selection limited to recipes matching identity
                    (VGN-*, VGT-*, PSC-* collections filter naturally by protein + tags)
```

**Priority order for identity:** `vegan > vegetarian > pescatarian > keto > paleo > whole30 > None`

One member being vegan overrides the household to vegan-safe recipes. This is the same safety-first logic as the constraint engine.

---

## Admin Weekly Workflow (Tim operates every Wednesday)

1. Open share.streamlit.io → WhollyFare → **Admin: Circulars**
2. Kroger: "Pull from Kroger API" button (live API, ~239 items, automatic)
3. For each PDF store (Food Lion, Giant, Aldi, Harris Teeter, etc.):
   - Download PDF from store website
   - Upload in Admin page
   - Click "Extract items with Claude" (Haiku Vision)
   - Review preview table (name, price, unit, category, raw text)
   - Click "Save X items to app + database"
4. Items flow into `flyer_data` (session) + `platform_flyer_items` (Supabase) immediately
5. Navigate to "This Week's Plan" — meal planner now sees all store prices

---

## Secrets

All secrets live in Streamlit Cloud → Settings → Secrets:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."        # Claude Haiku for PDF extraction
CONTACT_EMAIL_USER = "tim.hislop@gmail.com"
CONTACT_EMAIL_PASS = "xxxx xxxx xxxx xxxx"  # Gmail App Password (not account password)

[supabase]
url              = "https://liviclgyapbeoefxbunh.supabase.co"
anon_key         = "..."
service_role_key = "..."
```

Kroger API credentials are also in Streamlit secrets (check `integrations/kroger/` for exact key names).

---

## Key Engineering Rules (condensed)

1. **Never use the Edit tool on files >300 lines.** Use Python bash string-replace + `ast.parse()` verify.
2. **`st.html()` — one complete HTML block per call.** Never `st.markdown(unsafe_allow_html=True)`.
3. **`_BY_ID` in recipe_library.py** must be populated via `.update()` at end of file, after ALL_RECIPES is assembled.
4. **`weekly_shopping` is the primary shopping list source** — already deduplicated with category + cost. Do not re-derive from `meals` array.
5. **Protein ingredient names in plan must match sale item names** — prevents double-counting in shopping list.
6. **`sale_names_lower` and `cuisine_prefs_lower`** are computed once before the meal loop, not inside it.
7. **Git: Tim commits/pushes from Windows cmd prompt only.** Bash sandbox cannot reach GitHub. Always `del .git\index.lock` first.
8. **Claude model:** `claude-haiku-4-5-20251001` (3-haiku-20240307 deprecated May 2026).

---

## Phase 2 Gaps (known, deferred)

| Gap | Impact | When |
|-----|--------|------|
| Plan lost on hard refresh | Supabase persistence not wired to `meal_plans` table | Phase 2 |
| Personal store flyer uploads | Household-level, not platform — session only | Phase 2 |
| Admin user management UI | Currently SQL console upgrade | Phase 2 |
| Contact form Gmail App Password | Needs secret in Streamlit Cloud | Soon |
| Pescatarian pantry fallback | No fish/seafood synthetic fallback (unlike vegan/veg) | Phase 2 |
| National multi-metro store data | `store_directory.py` is Charlottesville-only | Phase 2 |
| Tonight's Dinner card polish | Cook time, ingredient count, "already made this?" | Phase 2 |

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA · tim.hislop@gmail.com*
