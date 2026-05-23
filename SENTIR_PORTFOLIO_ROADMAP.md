# Sentir Solutions® — Portfolio Brand Roadmap
*Supplemental strategic document — does not modify WhollyFare's product roadmap*
*Drafted: May 2026 · Author: Tim Hislop, Sentir Solutions® LLC*

---

## The Portfolio Thesis

Sentir Solutions LLC is a holding company that builds consumer platforms under a single founding philosophy: **the Sincere Strategy®**. Every brand in the portfolio operates by the same rules — allergen constraints before price optimization, net savings shown honestly (trip cost included), zero paid placements, user data never sold or shared.

The moat is structural. Competitors cannot copy it without destroying their own revenue model.

WhollyFare proved the model in the hardest category — perishables, where freshness, meal planning, and dietary complexity all compound. Every brand that follows is simpler to build because the engine is already proven.

**The investor answer in one sentence:**
*"Sentir Solutions is building the Sincere Strategy platform for household spending — an allergen-aware, cross-retailer price optimizer. WhollyFare proved it with food. WhollyWare, WhollyPaws, and WhollyCare extend it to every shelf in the house. Same engine, four markets, one founding principle."*

---

## Brand Architecture

```
Sentir Solutions® LLC  (holding company — investor-facing)
├── sentir-consulting       AI consulting practice (original business, sub-brand)
├── WhollyFare®            Perishables + meal planning (active, Phase 1 pilot)
├── WhollyWare™            Household non-perishables
├── WhollyPaws™            Pet food + supplies
└── WhollyCare™            Personal care + beauty
```

---

## The Sincere Strategy® — Applied Across All Brands

Every brand enforces these rules identically:

| Principle | What it means |
|---|---|
| Constraints before optimization | Allergen and health filters run first. No savings justify a health violation. |
| Net savings only | Always show gross savings minus trip cost. Never just the flattering number. |
| Radical transparency | Every rejection is logged and shown. User knows exactly why something was filtered out. |
| Zero paid placements | Revenue is subscriptions only. Retailers cannot pay to appear higher. Ever. |
| Local-first | Plans built from your actual stores' actual prices, not national averages. |
| Data never sold | User data is not sold, shared, or used for targeting. Full stop. |

---

## Brand 1: WhollyFare® — Perishables + Meal Planning

**Tagline:** The meal plan that pays you back.
**Retailers:** Kroger, Food Lion, Aldi, Harris Teeter, Giant, Wegmans, Whole Foods, Trader Joe's
**Unique complexity:** Meal planning, ingredient pooling across meals, weekly circular parsing, serving size math, recipe library
**Status:** Phase 1 pilot — Charlottesville, VA — launch imminent (May 2026)

*Full roadmap lives in `ui/pages/8_Roadmap.py` and PLAYBOOK.md. Do not duplicate here.*

---

## Brand 2: WhollyWare™ — Household Non-Perishables

**Tagline:** *The household staple plan that pays you back.*
**The name:** "Wares" is the correct term for household goods (kitchenware, hardware). Echoes WhollyFare's "-are" ending. Immediately communicates the category without over-explaining.

### What it does
Cross-grocer price comparison for shelf-stable household goods: paper towels, laundry detergent, dish soap, trash bags, cleaning supplies, aluminum foil, batteries, light bulbs. Same Sincere Strategy engine — but no meal planning complexity. It's pure price comparison + allergen/sensitivity filtering (fragrance-free, dye-free, hypoallergenic).

### Target retailers
Walmart, Target, Costco, BJ's Wholesale, Sam's Club, Aldi, Lidl, Dollar General, Amazon Subscribe & Save, Walgreens, CVS

### Constraint categories (simpler than WhollyFare)
- Fragrance sensitivities (unscented products)
- Dye-free requirements
- Phosphate-free cleaning products
- Eco/biodegradable preferences
- Brand exclusions (user-defined)

### Why it's easier to build than WhollyFare
- No meal planning engine required
- No recipe library
- No serving size math
- Ingredients lists are shorter and more standardized
- Products don't expire — reorder cadence is predictable
- Retail APIs (Walmart, Target) are better documented than grocer circular PDFs

### Phase Roadmap

**Phase 1 — POC (months 1–2 after WhollyFare Phase 1)**
- Hislop household pilot, 5 product categories, 4 stores
- Manual product entry (same Admin-style workflow as WhollyFare)
- Cross-store price comparison table
- Constraint filtering (fragrance-free, dye-free)
- Trip cost shown honestly — net savings only
- Found Money ledger for household goods

**Phase 2 — Beta (months 3–6)**
- 10 pilot households
- Walmart and Target API integrations (both have public APIs)
- Automated price tracking — no more manual entry for major chains
- Reorder reminders (paper towels last ~3 weeks — WhollyWare knows)
- Subscribe & Save comparison (Amazon vs. store price + trip cost)
- Mobile-first UI (in-store price check on phone)

**Phase 3 — Scale (months 6–18, post-investment)**
- 20+ retailer integrations
- Bulk-unit math (Costco 2-pack vs. Target single — true cost per unit)
- Household staple calendar (when you'll run out, when to buy)
- Price history charts (is this actually a good price?)
- B2B: property management companies, corporate office supply

**Revenue model (same tiers as WhollyFare, adapted):**
- Free: Cross-store price comparison, 3 categories
- $5/mo: Full comparison, all categories, reorder reminders
- $12/mo: Constraint filtering, allergy/sensitivity profiles
- $19/mo: Full history, subscribe-and-save optimizer, bulk math

---

## Brand 3: WhollyPaws™ — Pet Food + Supplies

**Tagline:** *The four-legged life plan that pays you back.*
**The name:** "Paws" immediately communicates pets — warm, recognizable, covers all species (dogs and cats both have paws). WhollyFetch and WhollyWag were considered but skew too dog-centric. WhollyPaws covers the full household.

### What it does
Cross-retailer price comparison for pet food, treats, supplies, and medications — filtered against each pet's dietary profile. A dog with a chicken allergy gets chicken flagged everywhere. A cat on a vet-prescribed kidney diet gets the constraint enforced before any price is shown.

Tim is the proof of concept: he spends significantly more on pets than he should because he doesn't have a tool that shows him where the best price is for the *specific* product his specific animal can actually eat.

### Target retailers
Chewy, PetSmart, Petco, Tractor Supply Co., Walmart, Target, Costco, Amazon, local pet stores, some veterinary suppliers

### Constraint categories
- **Food allergens:** chicken, beef, grain, corn, soy, fish, dairy, eggs
- **Dietary type:** grain-free, limited ingredient, raw, freeze-dried, prescription
- **Life stage:** puppy/kitten, adult, senior
- **Breed size:** toy, small, medium, large, giant (affects kibble size, calorie density)
- **Vet dietary restrictions:** kidney diet, weight management, diabetic, urinary health
- **Species + breed:** dog, cat, bird, rabbit, small animal — different formulations entirely

### Why pets are a strong second brand
- The pain is visceral and universal — every pet owner is Tim
- Chewy has an excellent API (they want third-party integrations)
- The constraint engine from WhollyFare maps almost directly to pet dietary profiles
- No meal planning required — just "find the cheapest bag of this kibble that my dog can eat"
- Prescription diet market alone is a significant segment with almost zero price transparency

### Phase Roadmap

**Phase 1 — POC (months 1–3 after WhollyFare Phase 1)**
- Hislop household pilot (Tim's pets)
- Dogs + cats initially; other species Phase 2
- Manual product entry for 3 retailers (Chewy, PetSmart, Tractor Supply)
- Dietary constraint profiles per pet (name, species, breed, allergens, vet restrictions)
- Cross-retailer price comparison
- Trip cost honesty (Tractor Supply vs. Chewy delivery — true net cost comparison)
- Found Money ledger for pet spending

**Phase 2 — Beta (months 4–8)**
- 15 pilot households
- Chewy API integration (their developer program is accessible)
- Petco and PetSmart price feeds
- Subscription vs. one-time price comparison (Chewy Autoship vs. store)
- Vet diet integration — common prescription brands flagged and tracked
- Medication price comparison (heartworm, flea/tick, joint supplements)
- Multi-pet households (each pet has its own profile; combined shopping list by store)

**Phase 3 — Scale (months 8–20, post-investment)**
- Full retailer coverage including Amazon, Walmart, local stores
- Vet clinic integration (prescription fulfillment price comparison)
- Breed-specific nutrition recommendations (flagged, not mandated — Sincere Strategy)
- Subscription optimizer (when Chewy Autoship + coupon beats PetSmart in-store)
- B2B: animal shelters, rescue organizations, boarding facilities

**Revenue model:**
- Free: 1 pet, cross-store price comparison, 3 stores
- $6/mo: Unlimited pets, all stores, reorder reminders
- $15/mo: Full dietary constraint profiles, vet diet tracking
- $22/mo: Medication pricing, prescription comparison, full history

---

## Brand 4: WhollyCare™ — Personal Care + Beauty

**Tagline:** *The personal care plan that pays you back.*
**The name:** Tim confirmed WhollyCare. Strong choice — "care" covers both personal care (shampoo, deodorant, oral care) and beauty/cosmetics without over-promising. It's warm, clear, and the double meaning of "caring about what goes on your body" is genuine.

### What it does
Cross-retailer price comparison for personal care products and cosmetics — filtered against each household member's skin sensitivities, ingredient exclusions, and product preferences. Same Sincere Strategy. The person with rosacea gets fragrance-flagged first. The person avoiding parabens never sees paraben products in their results.

### Target retailers
CVS, Walgreens, Rite Aid, Target, Walmart, Ulta, Sephora, Amazon, Costco, Dollar General

### Constraint categories
- **Skin sensitivities:** fragrance-free, dye-free, alcohol-free, sulfate-free
- **Ingredient exclusions:** parabens, phthalates, formaldehyde, talc, mineral oil
- **Skin conditions:** rosacea (no fragrance, no alcohol), eczema (fragrance-free, hypoallergenic), acne-prone (non-comedogenic, oil-free)
- **Ethics flags:** cruelty-free, vegan, no animal testing, B-Corp certified
- **SPF requirements:** minimum SPF thresholds for sun-sensitive users
- **Hair type/texture:** matching products to hair profile
- **Dietary-derived allergies that appear in cosmetics:** nut oils, gluten (celiac patients who absorb topically), soy, oat

### Why personal care is the most complex of the four
- Beauty industry has the least price transparency and the most brand loyalty noise
- Ingredient parsing is harder — INCI names (International Nomenclature of Cosmetic Ingredients) are not plain English
- CVS and Walgreens have loyalty programs that change the effective price dynamically (ExtraCare, myWalgreens)
- Sephora and Ulta have different pricing tiers and rewards structures
- But: the pain is massive, the market is enormous, and the Sincere Strategy is a genuine differentiator in a category full of paid influence

### Phase Roadmap

**Phase 1 — POC (months 2–4 after WhollyFare Phase 1)**
- Hislop household pilot
- 4 categories: skincare, haircare, oral care, deodorant/body care
- 3 retailers: CVS, Walgreens, Target
- Manual product entry with constraint profiles per household member
- Fragrance-free, paraben-free, sulfate-free filters (highest-demand constraints first)
- Cross-retailer price comparison with loyalty card pricing shown honestly
- Trip cost honesty — CVS pickup vs. Amazon delivery net cost

**Phase 2 — Beta (months 5–10)**
- 15 pilot households
- CVS ExtraCare and myWalgreens integration (loyalty pricing factored in automatically)
- INCI ingredient parsing — plain English translation of ingredient lists
- Ulta and Sephora price feeds
- Personal care calendar (shampoo lasts ~6 weeks — WhollyCare knows when you'll run out)
- Routine builder — "your full skincare routine, priced optimally across stores"
- Cruelty-free and vegan verification layer (third-party certified only — no self-reported claims)

**Phase 3 — Scale (months 10–24, post-investment)**
- Full retailer coverage
- Dermatologist-grade ingredient flagging (known irritants, comedogenic ratings)
- Subscription optimizer (Sephora Play vs. store purchases — is the subscription worth it?)
- Receipt scanning — what did you actually pay? Track real vs. listed prices.
- B2B: dermatology practices, medical spas, employer wellness programs
- Retail partnership data product (anonymized trend data sold to brands — opt-in only, Sincere Strategy compliant)

**Revenue model:**
- Free: 1 household member, 3 categories, 3 stores
- $6/mo: Full household, all categories, all stores, reorder calendar
- $15/mo: Full ingredient constraint engine, skin condition profiles, INCI parsing
- $24/mo: Routine builder, receipt tracking, subscription optimizer, full history

---

## Portfolio Sequencing

| Brand | Start after | Why this order |
|---|---|---|
| WhollyFare | Now (pilot live) | Hardest. Proves the engine. |
| WhollyWare | WhollyFare Phase 1 data in hand | Simplest. No meal planning. Great retail APIs. Fast POC. |
| WhollyPaws | WhollyWare beta running | Medium complexity. Chewy API accessible. Pain point is visceral and universal. |
| WhollyCare | WhollyPaws beta running | Most complex. Ingredient parsing, loyalty pricing, beauty fragmentation. Worth the wait — market is enormous. |

---

## Investor Narrative — The Sentir Portfolio

**The ask:** Sentir Solutions is raising a 7–8 figure round on the strength of WhollyFare Phase 1 + Phase 2 pilot data, with the supplemental portfolio as the market size argument.

**The story arc:**

> Every American household overspends on the same four shopping categories — groceries, household goods, pet supplies, and personal care. Collectively, that's over $1 trillion in annual household spending, almost none of it optimized. There is no tool that simultaneously filters for health constraints and finds the lowest cross-retailer price, shows you the honest net savings after gas, and refuses to take a dollar from the companies whose products it evaluates.
>
> WhollyFare is the proof. Eight weeks of real pilot data shows [X]% found money for participating households. The constraint engine, the cross-store optimizer, and the transparency ledger all work.
>
> WhollyWare, WhollyPaws, and WhollyCare take the same engine — already built, already proven — into three adjacent markets. Same codebase foundation. Same data architecture. Same founding principle. Different shelves.
>
> We are not a meal planning app. We are a household spending platform. The addressable market isn't dinners — it's everything your family buys.

---

## Immediate Actions (No Cost, High Signal)

1. **Domains secured (May 2026):** whollyfare.com · wholly-ware.com · wholly-paws.com · wholly-care.com
   Note: WhollyFare has no hyphen; the three newer brands use a hyphen.
2. **Update Sentir Solutions landing page** to name all four brands (even if just "coming 2027")
3. **One paragraph on the investor brief** naming the portfolio — changes how any investor reads WhollyFare immediately
4. **Two more brand ideas** — Tim and Chas are workshopping. Reserve space in this roadmap.

---

*Sentir Solutions® LLC · WhollyFare® · WhollyWare™ · WhollyPaws™ · WhollyCare™*
*Charlottesville, VA · tim.hislop@gmail.com*
*This document is confidential and intended for internal planning and investor conversations only.*

---

## What's Already Built in WhollyFare That Transfers

Every module below was built for WhollyFare but is brand-agnostic at its core. When starting WhollyWare, WhollyPaws, or WhollyCare, this is the codebase you copy and adapt — not rebuild from scratch.

### Transfers Directly (copy, rename brand references, done)

| Module | File | What it does | Adaptation needed |
|---|---|---|---|
| Constraint engine | `app/core_logic/constraint_engine.py` | IngredientCandidate dataclass, FilterResult, rejection logging | Rename "ingredient" to "product" for non-food brands; add brand-specific allergen categories |
| Price optimizer | `app/core_logic/budget_optimizer.py` | Cross-store price comparison, trip cost math | None — already brand-agnostic |
| Supabase helpers | `ui/state.py` (_sb_insert, _sb_update, etc.) | Direct REST helpers, auth flow, session state patterns | Copy the helper functions; rebuild session defaults per brand |
| Style system | `ui/style.py` | inject(), page_header(), sidebar_nav() | Swap brand color tokens; update nav links |
| Home page structure | `ui/Home.py` | Hero, pricing tiers, auth CTAs | Swap logo, tagline, tier names and prices |
| Admin page | `ui/pages/11_Admin.py` | PDF upload → Claude Vision extraction → preview → save | Works for any retailer circular; just update store directory |
| Claude extractor | `app/core_logic/claude_extractor.py` | PyMuPDF → Claude API → IngredientCandidate list | Update the Claude prompt for non-food items (products vs. meals) |
| Found Money ledger | `ui/pages/6_Ledger.py` | Net savings, CSV export, Supabase wired | Rename "meals" to "products"; same math |
| Trip cost logic | `ui/state.py` → `trip_cost_for_store()`, `net_found_money()` | Distance × $0.22/mile, gross − gas | None — already brand-agnostic |
| Auth flow | `ui/state.py` → sign_in, sign_up, sign_out | Supabase auth | None |
| Household setup | `ui/pages/1_Household.py` | Member profiles, dietary constraints | Replace dietary fields with brand-appropriate constraint fields (e.g., pet profiles, skin sensitivities) |
| Supabase schema | `migrations/schema_phase1.sql` | profiles, households, members, member_allergies | Core tables reuse; add brand-specific tables (flyer_items → product_items, etc.) |

### Transfers as a Template (reference, rebuild for brand)

| Module | File | What to take from it |
|---|---|---|
| Store directory | `app/data/store_directory.py` | The data shape: chain, location, method, tier, flyer_day |
| Store regions | `app/data/store_regions.py` | Zip-prefix → region mapping pattern |
| Grocer Hub | `ui/pages/2_Grocer_Hub.py` | 4-tier store selection UX, zip filtering, trip cost display |
| Sunday Buy-Off | `ui/pages/4_Sunday_BuyOff.py` | Approval flow, skip hints, net Found Money display |
| Shopping List | `ui/pages/5_Shopping_List.py` | Per-store sections, mobile-first layout, export |

### Stays WhollyFare-Only

| Module | Why it's WhollyFare-specific |
|---|---|
| `app/data/recipe_library.py` | 150 recipes with meal planning metadata — not relevant to other brands |
| `app/core_logic/meal_planner.py` | Weekly dinner plan generation — WhollyFare only |
| `ui/pages/3_Plan.py` | Weekly plan UI |
| `ui/pages/8_Roadmap.py` | WhollyFare product roadmap |
| Kroger API client | `integrations/kroger/` — grocery-specific |

---

## Recommended File & Repo Structure

### Phase 1–2: Separate repos, shared patterns (current approach — right call)

Each brand is a standalone Streamlit app deployed to Streamlit Cloud. Independent git repos. Tim can build and pilot them independently without entangling codebases.

```
GitHub/
├── Whollyfare/
│   └── Whollyfare-Website/         ← current repo, active
├── WhollyWare/
│   └── WhollyWare-Website/         ← copy WhollyFare, adapt
├── WhollyPaws/
│   └── WhollyPaws-Website/         ← copy WhollyFare, adapt
└── WhollyCare/
    └── WhollyCare-Website/         ← copy WhollyFare, adapt
```

**To start a new brand:** Fork WhollyFare's repo. Strip out recipe_library, meal_planner, Plan page, Kroger integration. Update brand tokens (colors, logo, name). Rebuild store_directory for that brand's retailers. Adapt constraint categories. You have a working skeleton in one session.

### Phase 3: Monorepo with shared package (post-investment, React migration)

When moving to React + FastAPI in Phase 3, consolidate into a true monorepo:

```
sentir-platform/
├── packages/
│   └── sincere-core/               ← pip/npm package: constraint engine,
│       ├── constraint_engine/          price optimizer, trip cost, Supabase
│       ├── price_optimizer/            helpers, auth — shared across all apps
│       ├── trip_cost/
│       └── found_money/
├── apps/
│   ├── whollyfare/                 ← React + FastAPI
│   ├── whollyware/
│   ├── whollypaws/
│   └── whollycare/
├── shared-ui/                      ← React component library
│   ├── WhollyHero/                     (brand-tokenized)
│   ├── PricingTiers/
│   ├── FoundMoneyLedger/
│   ├── ConstraintProfile/
│   └── StoreSelector/
└── sentir-solutions/               ← Investor/holding company site
```

### Supabase: One project per brand (recommended)

Keeps data isolated, billing transparent, and pilot data clean. Each brand's Supabase project shares the same schema pattern but is independent. In Phase 3, a cross-brand analytics layer can read from all four with appropriate permissions.

---

## Brand System — Consistency Across All Four Sites

### Logo Concepts

Every brand uses a simple 2-element icon + the Wholly wordmark. The icon uses the brand's primary color. All icons are designed to work at 32px (favicon), 48px (mobile nav), and 120px (hero).

| Brand | Icon concept | Rationale |
|---|---|---|
| WhollyFare® | Fork + leaf | Fork = food. Leaf = fresh, natural, local. The original. |
| WhollyWare™ | House outline with a small leaf inside | House = home goods. Leaf echoes WhollyFare's natural/honest ethos. Clean and unmistakable. |
| WhollyPaws™ | Paw print (1 large pad, 4 toe pads) | Universal pet symbol. Warm and immediately recognizable. |
| WhollyCare™ | Five-petal botanical flower | Botanical = natural ingredients, clean beauty. Gentle, not clinical. |

### Color Palette — The Wholly Family

All brands share: warm cream background `#FAF8F3`, same font stack, same structural layout. Each brand owns a distinct primary + accent pairing.

| Brand | Primary | Accent | Feeling |
|---|---|---|---|
| WhollyFare® | `#2A5F1E` Deep forest green | `#D4A017` Warm gold | Fresh, natural, harvest |
| WhollyWare™ | `#1B3D6E` Deep navy | `#E06030` Warm orange | Trustworthy, organized, domestic |
| WhollyPaws™ | `#8B3A1A` Warm terra cotta | `#3A8A5C` Forest green | Earthy, warm, alive |
| WhollyCare™ | `#5C3580` Soft purple | `#D45878` Rose | Gentle, botanical, honest |

### Structural Consistency Rules

Every brand site has the same bones — only the content and colors change:

1. **Hero:** Logo + tagline ("The [X] plan that pays you back.") + primary CTA
2. **Value strip:** 3 Sincere Strategy pillars (adapted per brand, same visual treatment)
3. **Pricing tiers:** 4 tiers, same card layout, different tier names
4. **Found Money sample:** A real number. "Pilot households saved an average of $X in week 1."
5. **Sincere Strategy® seal:** Same badge on every site — this is the trust mark
6. **Roadmap teaser:** "Where we're going" — builds investor confidence from the landing page
7. **Sidebar nav:** Same section structure (GET STARTED → WEEKLY PLAN → SAVINGS INTELLIGENCE → PLATFORM)
8. **Footer:** "A Sentir Solutions® brand" with links to sibling brands

### Tagline Family (working — all follow the same pattern)

- WhollyFare®: *The meal plan that pays you back.*
- WhollyWare™: *The household staple plan that pays you back.*
- WhollyPaws™: *The four-legged life plan that pays you back.*
- WhollyCare™: *The personal care plan that pays you back.*

Simple. Parallel. Immediately understood. Every tagline follows the exact same structure: 'The [descriptor] plan that pays you back.' The repetition across four brands is intentional — it teaches investors and users what Sentir does before a word of explanation.

---

## Final Decision Log — May 2026

- ✅ Sentir Solutions LLC = holding company / investor-facing parent
- ✅ sentir-consulting = AI consulting sub-brand (original business, rebranded)
- ✅ Four Wholly brands confirmed: WhollyFare, WhollyWare, WhollyPaws, WhollyCare
- ✅ No more workshopping. No new brands until these four have working pilots.
- ✅ Phase 1–2: separate Streamlit repos. Phase 3: monorepo migration.
- ✅ Each brand gets its own investment brief + roadmap page (linked from Sentir Solutions parent)
- ✅ WhollyFare pilot first — proves the engine. Other brands follow in sequence.
- ✅ Domains secured May 2026: whollyfare.com (no hyphen) · wholly-ware.com · wholly-paws.com · wholly-care.com
- ✅ Tim and Chas: no additional brand ideas to workshop. Four is the portfolio.

