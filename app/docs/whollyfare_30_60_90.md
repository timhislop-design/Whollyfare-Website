# WhollyFare — 30 / 60 / 90 Day Plan

*A B2C execution roadmap for the WhollyFare meal-planning product (a Sentir Solutions, LLC initiative).*

> Note: this is the **consumer-product** roadmap. The Sentir Solutions consultancy roadmap (T&N Printing, I-64/66 Corridor, Foundry Logic, Moat Scan pricing) is a separate document and is **not applicable** to WhollyFare.

---

## Phase 0 — Where we are today

The repository under `/whollyfare` is a working MVP scaffold:
the constraint engine, budget optimizer, meal planner, profile builder,
flyer ingestor, Sunday Buy-Off page, and Financial Advocacy Ledger are all
in place. The bundled sample data simulates a **Food Lion Palmyra** weekly
circular for end-to-end demos.

What's missing for an honest "v0.1": chain-specific flyer scrapers, USDA
nutrition lookups for any non-bundled ingredient, real coupon/loyalty data,
and unit tests.

---

## 30 Days — The Hislop Pilot

**Goal:** Run the full WhollyFare loop on the founder's own household for
four consecutive weeks. Prove the logic in real life before showing it to
anyone else.

**Workstreams**

- *Week 1 — Wire up & dogfood.* Run the Streamlit app locally with a real
  Hislop-household profile (Abby/Chas/Tim — kept in a private dev profile,
  not committed). Manually fetch the Food Lion Palmyra circular each
  Sunday and feed it through the JSON ingestor.
- *Week 2 — Instrument the Ledger.* Track actual receipts vs. the
  Financial Advocacy Ledger's projections. Tune the comparison baselines
  if HelloFresh / Fresh Market published prices have drifted.
- *Week 3 — Fix what hurts.* Whatever was painful in weeks 1–2 (probably
  the manual flyer-to-JSON step) gets a small tool built for it. Add the
  first chain-specific parser for Food Lion's PDF.
- *Week 4 — Write the case study.* One-page, plain-English: dollars saved,
  hours reclaimed, safety incidents (target: zero), what broke.

**Exit criteria**

- 4 weeks of complete plans approved through the Sunday Buy-Off.
- Documented Found Money number for a real household.
- Zero allergen / diagnosis violations.
- A tightly-scoped backlog of "what week 5 needs" before friends-and-family.

---

## 60 Days — Friends & Family Beta (5 households)

**Goal:** Move WhollyFare off a single laptop and onto the phones of five
trusted households across mixed dietary profiles.

**Workstreams**

- *Hosting.* Push the Streamlit app to Streamlit Community Cloud or Render
  with per-household session state. Still no accounts/login — each user
  gets a private URL with a token.
- *Profile diversity.* Recruit five households that span the constraint
  space: at least one with celiac, one with a Top-14 allergy, one with a
  diabetes diagnosis, one strict vegetarian, one no-restrictions
  budget-only family.
- *Two more grocer parsers.* Beyond Food Lion, add Kroger and Aldi. These
  three together cover ~70% of mid-Atlantic households.
- *Privacy commitment in product.* Add an in-app Settings → Data tab that
  lets users export their full profile JSON and wipe it with one click.
  This isn't a feature — it's a Sincere Strategy compliance requirement.
- *Telemetry (anonymous).* Count plans generated, plans approved, average
  Found Money. Nothing identifying. This is the data that will eventually
  back the public "we save families $X/yr" claim.

**Exit criteria**

- 5 households running for ≥ 3 weeks each.
- Aggregated Found Money in real dollars (no model assumptions).
- ≥ 1 testimonial willing to be quoted.
- Bug list triaged into "fix before public" vs. "fix after public."

---

## 90 Days — Palmyra-Area Public Alpha

**Goal:** Open WhollyFare to anyone in the Palmyra / Charlottesville
metro who shops at the supported grocers. Validate that the platform
acquires users without paid marketing.

**Workstreams**

- *Accounts + persistence.* Migrate session state to a small Postgres
  instance. Implement export-and-delete from day one (per Sincere
  Strategy commitment #6).
- *Self-serve sign-up.* Email + magic link. No third-party SSO yet — fewer
  data flows means fewer privacy questions to answer.
- *Onboarding flow.* The comprehensive Family Profile page is the
  front door; add a 90-second guided walkthrough that lands a user on
  their first Sunday Buy-Off in under 3 minutes.
- *USDA FoodData Central integration.* Replace bundled nutrition stubs
  with real USDA lookups so the engine isn't blind to non-sample
  ingredients.
- *Distribution.* Two channels, both unpaid:
    1. The Hislop pilot case study, posted publicly with permission.
    2. Outreach to one Charlottesville-area MCAS / EDS support group
       and one celiac support group. The Halo of Trust thesis says
       starting at the medical edge gets us to mass retention faster
       than starting in the middle.

**Exit criteria**

- 100 households signed up; 30 approving plans weekly.
- Documented Found Money across the cohort.
- Zero reported allergen / diagnosis violations.
- A clear v0.2 backlog (Instacart push, real coupon harvesting,
  multi-grocer arbitrage) that we know is worth doing because real
  users are asking for it.

---

## What we are explicitly *not* doing in this 90 days

- No mobile native app. PWA-quality web is the v0.x deliverable.
- No paid advertising. Distribution is pilot → case study →
  community group → word of mouth.
- No advertiser, sponsor, or affiliate revenue. Not in this roadmap, not
  in v1.0, not ever — see `sincere_strategy.md`.
- No expansion outside the Palmyra / Charlottesville footprint. The
  three-grocer footprint is intentional; geographic concentration makes
  the Found Money number defensible.

---

## What success at 90 days unlocks

A defensible 4-month dataset of real households, with real receipts,
saving real money against real meal-kit prices — used to (a) decide
whether to seek seed capital under Sentir Solutions, LLC, and (b) write
the v0.2 roadmap (Instacart Connect push, agentic coupon harvesting,
clinical-grade UPC verification).
