# WhollyFare — Product Tier Strategy

*Source of truth for how the WhollyFare product is positioned, sold, and built. Supersedes the medical-anchored tier model in the older Sentir docs, which framed the clinical use case as the headline. That framing carried legal exposure (compliance claims) and addressed too narrow a market for an acquisition wedge.*

---

## The four tiers

### Tier 1 — Smart Multi-Grocer Shopping  *(the wedge)*

**What it does.** Optimizes a household's weekly grocery basket across their 2–3 preferred local grocers, with automated digital-coupon matching. Output: "Buy these 10 at Food Lion (with these clipped coupons), these 5 at Aldi — projected savings $X over single-sourcing."

**Who it's for.** Every household that shops more than one store, or could. Universal market.

**The claim.** "We don't sell food. We make sure you don't pay too much for the food you'd buy anyway." Auditable against the user's own previous receipts — no inflated meal-kit comparisons required.

**Realistic savings.** 15–25% off current grocery spend. For a $600–$900/month household, that's $90–$225/month.

**Monetization role.** Free or near-free. Acquisition layer. The thing that gets a user to install and try.

---

### Tier 2 — Meal Planning

**What it does.** Wraps the optimized basket into a 5–7 ingredient weekly menu using the Flavor Plugin variety engine. Same hero ingredients become Mexican on Monday, Asian on Wednesday, Mediterranean on Friday — minimizing the shopping list while maximizing the menu.

**Who it's for.** Households that want the "what's for dinner" question solved, not just the price-comparison question.

**The claim.** "Five to seven ingredients become seven different dinners. One shopping trip, one decision."

**Monetization role.** Small subscription (~$5–10/mo). Converts free Tier 1 users into weekly active users. The Sunday Buy-Off lives here.

---

### Tier 3 — Health-Aware Constraints  *(was the headline, now a premium upgrade)*

**What it does.** Hard-constraint filtering for allergies (Top-14 + Alpha-gal), medical diagnoses (celiac, T1/T2 diabetes, CKD, PKU, GERD, IBS, MCAS, POTS, EDS, hypertension, heart disease), lifestyle patterns (vegan, halal, Whole30, low-FODMAP, etc.), and free-text exclusions. Every recommendation is auditable — the user sees why each ingredient was passed or rejected and which household member triggered the rule.

**Who it's for.** Households with at least one member who has a serious dietary constraint — the "Medical Complex" segment from the original Sentir framing, plus lifestyle households (vegan, kosher, halal) where mistakes are unacceptable.

**The claim.** "Best-available ingredient data with auditable sourcing, plus per-meal verification — every constraint check is shown to you, not hidden in a model." (Note: deliberately *not* "100% medical compliance," which is a liability claim we cannot defend at MVP scale.)

**Monetization role.** Premium subscription (~$15–25/mo). High switching cost — once a household has invested in setting up the constraint profile and has trusted the engine for weeks, they don't leave.

---

### Tier 4 — Recipe Suggestions

**What it does.** Tuned recipe inspiration based on household preferences — cuisines marked as favorites, prior-approved meals, member-specific notes. Goes beyond the Flavor Plugin's method hints into actual recipes with prep time, ingredient quantities, and step-by-step instructions.

**Who it's for.** All tiers. The retention / engagement layer that keeps users opening the app even on weeks when the savings are similar.

**The claim.** "Your week, but never the same week twice. Suggestions tuned to what your family actually eats."

**Monetization role.** Bundled into Tiers 2 and 3. The reason you don't churn.

---

## Why this tiering is the right shape

**It maps cleanly to a freemium ladder.** Free → small subscription → premium subscription, with each step delivering more value than the last. Users self-select into the tier that matches their need.

**It de-risks the medical-claims liability.** By moving clinical-grade filtering from the headline to a premium tier, the product's main marketing surface is the safe "smart shopping" claim. The clinical capability is still there for the households that need it, but it's not the load-bearing promise of the brand.

**It addresses the right market sizes at the right tiers.** Tier 1's universal market is the acquisition surface. Tier 3's narrower clinical market is where the per-user economics work hardest. Tier 4 is the retention glue across both.

**It survives a sophisticated reader.** The savings claim (15–25% on current spend) is auditable. The constraint engine doesn't make compliance claims it cannot defend. The recipe layer is honest about being inspiration, not prescription. None of this requires walking back later.

---

## What this means for the build

| Tier | Status in repo today | What's left |
|---|---|---|
| Tier 1 — Smart Multi-Grocer | Profile schema supports multiple grocers; budget_optimizer is single-store | Upgrade BudgetOptimizer to weigh cross-store splits; add `max_stops` parameter; build coupon-matching module (start with public digital-coupon page scrape, deep-link out) |
| Tier 2 — Meal Planning | Built — meal_planner.py with Flavor Plugins, Sunday Buy-Off page, Financial Ledger | Refine cost-per-serving math; tighten meal-name variety |
| Tier 3 — Health-Aware Constraints | Built — constraint_engine.py with full diagnosis and allergen rules | Add UPC-level data source (USDA FoodData Central + Open Food Facts) for non-bundled ingredients |
| Tier 4 — Recipe Suggestions | Not started — only have Flavor Plugin method hints | New module: recipe_db with cuisine tags + per-household ranking |

---

## What's explicitly *not* in this tier strategy

- **No advertising or paid placement, ever.** Across all four tiers. This is the Sincere Strategy commitment from `sincere_strategy.md` and applies regardless of pricing.
- **No reselling user data.** Tier 3 health profiles never leave the user's device or account.
- **No "100% medical compliance" claim.** Tier 3 surfaces the constraint engine's reasoning so users can verify; it does not promise infallibility.
