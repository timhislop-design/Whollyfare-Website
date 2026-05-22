# WhollyFare® — Project Briefing for Claude

This file is read automatically at the start of every session. It is the
single source of truth for context, decisions already made, and how to work
with Tim on this project. Read it fully before doing anything.

---

## What This Is

WhollyFare® is a meal-planning platform built by Tim Hislop under his LLC
**Sentir Solutions® LLC** (Palmyra / Charlottesville, VA). It is a standalone
product — separate from Sentir Solutions' AI consulting practice.

**Core value proposition:** Cross-grocer price optimisation + automated coupon
harvesting. WhollyFare builds a weekly dinner plan from your local grocery
stores' actual sale circulars, filtered for your household's dietary constraints,
and shows you exactly how much you saved vs. single-store shopping and vs.
HelloFresh — net of gas costs.

**The founding philosophy is called the Sincere Strategy®:**
- Zero paid placements. Ever. Revenue is subscriptions only.
- Health constraints are absolute hard rules, never traded for savings.
- Every ingredient rejection is logged and shown to the user (radical transparency).
- Local-first: plans built from your actual stores' actual circulars.
- Safety before savings, always. The constraint engine runs before the optimizer.
- Don't burn gas to save pennies — trip costs are shown honestly.
- User data is never sold, shared, or used for targeting.

This is the moat. Competitors cannot copy it without destroying their own
revenue model. That asymmetry is structural and durable.

---

## The Pilot Household

Tim Hislop, Abby, and Chas — Charlottesville, VA.
Stores: Kroger Barracks Road, Food Lion Pantops, Aldi Rio Road, Harris Teeter Barracks Road.

The pilot runs on **manual flyer entry** (type items from the weekly circular)
with PDF upload via the Admin Circular Manager as the primary path for PDF stores.
Kroger pulls automatically via API. Tim operates the Admin page each Wednesday —
users just log in and get current prices.

---

## Four-Tier Business Model

| Tier | Name | Price | What it does |
|---|---|---|---|
| 1 | Price Finder | Free | Cross-store price comparison, coupon matching, weekly savings report |
| 2 | Meal Planner | $7/mo | Weekly 5-dinner plan, Sunday Buy-Off, shopping list by store |
| 3 | Health Guard | $19/mo | Hard dietary constraint engine — allergens, celiac, CKD, diabetes, MCAS, etc. |
| 4 | Full Table | $29/mo | Full recipes, cuisine preference memory, meal history, pantry tracking |

Never suggest ad revenue, affiliate revenue, or data sales. These violate the
Sincere Strategy and are non-negotiable.

---

## Five-Phase Product Roadmap

**Phase 1 (now):** POC. Hislop family pilot, Charlottesville stores, manual flyer
entry + PDF extraction via Admin page, 8 weeks of real receipts. Goal: undeniable
Found Money data.

**Phase 2 (months 2–5):** 5–10 pilot households. Meal type selection, pantry tracker,
Coupon Vault, Health Guard Dashboard, multi-household accounts, mobile-first UI.

**Phase 3 (post-investment, months 6–18):** Regional scale. React + FastAPI replaces
Streamlit. Automated circular parsing, Recipe Library, Price Intelligence, Delivery Hub
(Instacart/Shipt), Market Insights (public data product), Health System B2B licensing.

**Phase 4 (Series A, months 18–36):** National. 15+ grocer chains. 50,000+ households.
Preference learning, receipt auto-capture, community & sharing. $2M+ ARR.

**Phase 5 (Horizon, post-Series A):** Wholesale & Delivery. Costco, Sam's Club, BJ's,
Amazon Fresh. Bulk-unit math, membership economics, hybrid trip planning.

**Investment target: 7–8 figures.**

---

## Tech Stack

- **Language:** Python 3.12
- **UI:** Streamlit (MVP only — React + FastAPI in Phase 3)
- **Deployment:** Streamlit Community Cloud (share.streamlit.io). Tim pushes to
  GitHub; Streamlit Cloud auto-redeploys. Tim does NOT run the app locally.
- **Core logic:** `app/core_logic/` — constraint engine, budget optimizer, meal planner,
  claude_extractor
- **Data:** `app/data/` — flyer ingestor, store_regions, store_directory, recipe_library
- **UI pages:** `ui/` — Home.py + pages in `ui/pages/`
- **State:** `ui/state.py` — all session state init, DB helpers, trip cost logic,
  auth, flyer persistence (1,881 lines — NEVER use Edit tool on this file)
- **Style:** `ui/style.py` — inject(), page_header(), sidebar_nav() (377 lines)
- **Integrations:** `integrations/` — Kroger API client, Food Lion parser, others
- **DB:** Supabase (PostgreSQL). Schema in `migrations/schema_phase1.sql`.
  Connection via Streamlit secrets: `SUPABASE_URL`, `SUPABASE_KEY` (service_role).
- **Claude API:** `ANTHROPIC_API_KEY` in Streamlit secrets. Used by Admin page
  for PDF circular extraction. Model: `claude-3-haiku-20240307`.
- **Docs:** `PLAYBOOK.md` — full strategic spec. `CLAUDE.md` — this file.

**Session state is the primary working store in the POC.** Supabase is the durable
backup (degrades gracefully if not connected). Every file that touches persistence
has a comment explaining what production would require.

---

## Complete Page Inventory

| Page | File | Status | Notes |
|---|---|---|---|
| Home / Landing | `ui/Home.py` | ✅ Complete | Hero with fork+leaf SVG, "The meal plan that pays you back.", pricing tiers, auth CTAs |
| Household Setup | `ui/pages/1_Household.py` | ✅ Complete | Supabase wired, member profiles |
| Grocer Hub | `ui/pages/2_Grocer_Hub.py` | ✅ Complete | 4 store tiers, zip filtering, trip cost, PDF parse review, Kroger API pull |
| This Week's Plan | `ui/pages/3_Plan.py` | ✅ Built | Needs polish — pilot friends must understand without explanation |
| Sunday Buy-Off | `ui/pages/4_Sunday_BuyOff.py` | ✅ Built | Net Found Money, skip hints, Supabase wired |
| Shopping List | `ui/pages/5_Shopping_List.py` | ✅ Built | Canonical cart, per-store sections, weekly regulars, pantry check, CSV/TXT export |
| Found Money Ledger | `ui/pages/6_Ledger.py` | ✅ Complete | Net savings, CSV export, Supabase wired |
| Investor Brief | `ui/pages/7_Investor.py` | ✅ Complete | Production-quality investor narrative |
| Product Roadmap | `ui/pages/8_Roadmap.py` | ✅ Complete | 5-phase, matches product vision |
| Account | `ui/pages/9_Account.py` | ✅ Built | Sign in, create account, zip/radius |
| My Pantry | `ui/pages/10_Pantry.py` | ✅ Complete | Tier 1 staples (checkboxes) + Weekly Regulars (Tier 2) with sale hints |
| Admin: Circulars | `ui/pages/11_Admin.py` | ✅ Complete | Tim's weekly workflow — PDF upload → Claude Vision extraction → preview → save to flyer_data + Supabase |

**Sidebar nav sections:** GET STARTED → WEEKLY PLAN → SAVINGS INTELLIGENCE →
HEALTH GUARD (coming soon) → DELIVERY (coming soon) → PLATFORM

---

## Key Supporting Modules

### ui/state.py (1,881 lines — bash string-replace only)
Critical functions:
- `init()` — session state defaults. Keys: household, grocers, flyer_data,
  flyer_meta, plan, approved_weeks, ledger_history, active_week, home_zip,
  store_radius_mi, travel_radius_mi, household_pantry, weekly_regulars
- `PANTRY_DEFAULTS` — list of ~40 pantry staple strings
- `WEEKLY_REGULARS_DEFAULTS` — list of dicts {name, qty, unit, store_pref}
- `net_found_money()` — gross savings minus total trip costs
- `trip_cost_for_store(grocer)` — distance_mi * 2 * $0.22/mile
- `approve_week_db()` — saves approved week to Supabase
- `save_flyer_items(chain, candidates, week, method)` — persists IngredientCandidates
  to flyer_weeks + flyer_items tables. Handles both dataclass and dict candidates.
- `_sb_insert / _sb_update / _sb_delete / _sb_select` — direct REST helpers
- `save_household / load_household` — profile persistence
- `sign_in / sign_up / sign_out / try_restore_from_browser` — auth flow

### ui/style.py (377 lines — bash string-replace only)
- `inject()` — global CSS + WhollyFare brand styles
- `page_header(title, subtitle)` — standard page header
- `sidebar_nav()` — full nav with all 11 pages + coming-soon items
- `scroll_to_top() / maybe_scroll_to_top()` — JS-based scroll reset after rerun

### app/core_logic/claude_extractor.py
- `extract_uploaded_pdf(file_bytes, store_chain, api_key, max_pages)` — main entry
- `merge_into_flyer_data(result, store_key, flyer_data)` — merges into session dict
- Renders pages with PyMuPDF (fitz) at dynamic zoom capped to 2048px, JPEG 80%
- Sends to `claude-3-haiku-20240307` — universally available on all API tiers
- Claude API limit: 5MB per image. PyMuPDF + JPEG keeps pages ~300-600KB.

### app/data/store_directory.py
- `CHARLOTTESVILLE_STORES` — 12 stores with chain, location, flyer_url, method,
  tier, notes, flyer_day
- Methods: "kroger_api" | "pdf" | "manual"
- `PDF_STORES`, `WEDNESDAY_STORES`, `STORE_BY_CHAIN` convenience lookups

### app/data/recipe_library.py
- 150 recipes across 5 cuisines (American, Mexican, Italian, Asian, Mediterranean)
- Each recipe: name, ingredients (with qty/unit), servings, cuisine, proteins,
  category (weeknight/weekend), tags
- Wired into meal_planner.py for plan generation

### app/core_logic/constraint_engine.py
- `IngredientCandidate` dataclass — the universal data shape for sale items:
  name, usda_fdc_id, allergens, nutrition, sale_price_per_unit, unit,
  standard_unit_weight_g, category, tags
- `ConstraintEngine` — filters candidates against household dietary profile
- `FilterResult` — passed/rejected lists with rejection reasons

---

## Weekly Admin Workflow (Tim operates this every Wednesday)

Tim is the data operator. Users are consumers. Users never see the admin page.

1. Go to share.streamlit.io → WhollyFare app → Admin: Circulars
2. Kroger: pull from Grocer Hub (live API, automatic)
3. Food Lion, Giant, Aldi, Harris Teeter, etc.: download PDF from store website
4. Upload each PDF in the Admin page → click "Extract items with Claude"
5. Review the preview table (item name, price, unit, category, raw text)
6. Click "Save X items to app + database"
7. Items flow into flyer_data (session) + flyer_items (Supabase) immediately
8. Run This Week's Plan — meal planner now sees all store prices

Store flyer days: Wednesday (Food Lion, Aldi, HT, Lidl, Whole Foods),
Friday (Giant, Walmart), Sunday (Wegmans).

---

## Secrets & Deployment

**Streamlit Cloud secrets panel** (Settings → Secrets) — must contain:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."

[supabase]
url              = "https://liviclgyapbeoefxbunh.supabase.co"
anon_key         = "..."
service_role_key = "..."
```

**Local `.streamlit/secrets.toml`** — gitignored, same format. Used only if
running locally (Tim does not run locally — he uses Streamlit Cloud).

**Kroger API credentials** — stored in Streamlit secrets (check state.py for
exact key names). Location ID for Kroger Barracks Rd: 01200441.

---

## Supabase Schema (migrations/schema_phase1.sql)

15 layers. Key tables for Phase 1:
- `profiles` — mirrors auth.users, auto-created by trigger
- `households` — one per family. Has pantry_items JSONB column.
- `household_users` — links auth users to households
- `members` — individual household members with dietary profiles
- `member_allergies / member_diagnoses / member_lifestyle_tags / member_custom_exclusions`
- `household_grocers` — stores saved by household, with distance_mi, trip_cost
- `flyer_weeks` — one row per (household, grocer, week). load_method: manual/pdf/api.
- `flyer_items` — individual sale items. Links to flyer_weeks + grocer.
- `meal_plans` — weekly plan header
- `meal_plan_meals` — individual meals in the plan
- `meal_ingredients` — ingredients per meal
- `constraint_rejections` — logged rejections (Sincere Strategy transparency)
- `ledger_entries` — weekly Found Money records

---

## CRITICAL Engineering Rules

These were learned the hard way. Every one has caused a lost session.

### 1. NEVER use the Edit tool on files longer than ~300 lines
Files known to exceed this: `ui/Home.py` (612), `ui/state.py` (1881),
`ui/style.py` (377), `ui/pages/2_Grocer_Hub.py`, `ui/pages/5_Shopping_List.py`.

Always use a Python string-replace script via bash:
```python
with open(path, 'r') as f: src = f.read()
assert 'old_string' in src, "marker not found"
src = src.replace('old_string', 'new_string', 1)
with open(path, 'w') as f: f.write(src)
```
Then immediately verify:
```bash
python3 -c "import ast; ast.parse(open('path').read()); print('OK')"
```

### 2. Always run ast.parse() after every file write
No exceptions. A silent syntax error breaks the whole app on the next deploy.

### 3. bash mount and Read tool can show different file contents
The Read tool reads the Windows filesystem. Bash reads the Linux mount. They
diverge when a prior write didn't fully persist. The Read tool is what git
tracks. To fix divergence: re-apply changes via Python script.

### 4. st.html() — one complete HTML block per call
`st.html()` renders each call as an isolated HTML context. Never split a single
HTML element across multiple calls. Use `st.html()` exclusively — never
`st.markdown(unsafe_allow_html=True)` (deprecated in Streamlit 1.31+).

### 5. CSS: border shorthand clobbers border-left on subclasses
`border: 1px solid #ccc` sets all four sides and overrides a `border-left` rule
on a modifier class. Keep `border` on the base class and `border-left` on
the modifier — the cascade handles it correctly if shorthand comes first.

### 6. f-strings cannot contain backslashes (Python 3.10/3.12)
Extract dict lookups to a variable before the f-string, or use single quotes
inside the expression.

### 7. requirements.txt — never remove these
`supabase>=2.0.0,<3.0.0`, `python-dateutil>=2.8.0`, `anthropic>=0.25.0`,
`pymupdf>=1.23.0`, `streamlit-javascript>=0.1.5` have all been accidentally
removed before. Verify after any requirements.txt edit.

### 8. PyMuPDF image sizing for Claude API
Claude API limit: 5MB per image. Food Lion / Giant PDFs are 7000+ pts wide.
The extractor uses dynamic zoom: `min(72/72, 2048/longest_edge)` + JPEG 80%.
This produces ~300-600KB images. Never revert to PNG or static DPI.

### 9. Claude model ID for extraction
Use `claude-3-haiku-20240307` — universally available on all API key tiers.
`claude-3-5-haiku-20241022` returns 404 on the current API key.

### 10. Git workflow — Tim commits from cmd prompt only
The bash sandbox cannot reach GitHub (403). Tim runs git commands from
Windows cmd prompt. GitHub Desktop should be closed when committing to
avoid index.lock conflicts.

Clear the lock before every commit session:
```
del C:\Users\timhi\Documents\GitHub\Whollyfare\Whollyfare-Website\.git\index.lock
```

### 11. Streamlit runs on Cloud, not locally
Tim does not run Streamlit locally. The app is on share.streamlit.io.
To pick up code changes: push to GitHub, wait ~60 seconds for auto-redeploy,
then hard-refresh the browser (Ctrl+Shift+R).
Python 3.12 is installed locally at `C:\Users\timhi\AppData\Local\Python\pythoncore-3.12-64\`
but packages may not be installed there.

### 12. API key was shared in chat — rotate it
The Anthropic API key was shared in conversation. After confirming the extractor
works, create a new key at console.anthropic.com and update Streamlit Cloud secrets.

---

## Auto-Commit Rule

After every meaningful block of work, commit all changed files:

```bash
cd C:\Users\timhi\Documents\GitHub\Whollyfare\Whollyfare-Website
git add -A
git commit -m "descriptive message covering what changed and why"
```

Tim pushes to GitHub from his cmd prompt — the bash sandbox cannot reach GitHub.
Claude commits (via bash); Tim pushes. No work is lost between sessions.

---

## What to Build Next

Priority order (as of May 2026):

1. **Fix missing fork+leaf logo and "The meal plan that pays you back." tagline**
   These are in Home.py (line 113 SVG, line 147 tagline) but not rendering on
   Streamlit Cloud. Likely a CSS scoping or st.html() isolation issue. Fix first —
   it's the first thing pilot friends and investors see.

2. **Verify Admin circular pipeline end-to-end**
   Push is done. Confirm Food Lion PDF extracts successfully on Streamlit Cloud.
   Check that items appear in the preview table and save to Supabase correctly.

3. **Plan page polish** (`3_Plan.py`)
   Pilot friends need to understand the plan without explanation. Add selection
   rationale, clearer meal layout, protein variety callout.

4. **Shopping List mobile-first** (`5_Shopping_List.py`)
   Usable on a phone in a grocery store aisle. That is the bar.
   No desktop-only layouts. Per-store sections must be finger-friendly.

5. **Pilot onboarding guide**
   In-app walkthrough or printed one-pager so pilot friends can set up and run
   a week without Tim present.

6. **Ledger milestones + streaks**
   Streak callouts and milestone moments (first $100 saved, 4-week streak)
   to make the Found Money data emotionally resonant.

7. **Supabase end-to-end test**
   Full week loop (flyer entry → plan → buy-off → receipt log) persists across
   browser refresh for a real pilot session.

Do not build new features before the existing flow works end-to-end. Fix before you add.

---

## What NOT to Do

- Do not suggest ad revenue, affiliate revenue, or sponsored content. Ever.
- Do not add a feature that creates a conflict of interest between WhollyFare
  and the household it serves.
- Do not confuse WhollyFare with Sentir Solutions. They are separate companies.
- Do not use the Edit tool on any file over ~300 lines.
- Do not split an HTML element across multiple `st.html()` calls.
- Do not show gross Found Money without also showing net when trip data exists.
- Do not describe POC limitations as bugs. They are intentional design decisions.
- Do not remove supabase, python-dateutil, anthropic, pymupdf, or
  streamlit-javascript from requirements.txt.
- Do not revert to PNG output or static 150 DPI in claude_extractor.py.
- Do not change the Claude model to claude-3-5-haiku-20241022 (returns 404).

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*
*Contact: tim.hislop@gmail.com*
