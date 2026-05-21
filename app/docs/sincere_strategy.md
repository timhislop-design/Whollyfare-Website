# The Sincere Strategy — WhollyFare's Founding Philosophy

*This document is the philosophical brief behind every product decision at WhollyFare. It exists so that as the team grows, every engineer, designer, and partner understands what we're building and — equally important — what we will never build.*

---

## The Problem We're Solving

Meal planning apps have a trust problem.

Most of them are built on a conflict of interest: they earn money by promoting specific products, brands, or retailers — then present those promotions as personalized recommendations. Users have no way to know whether a recipe appeared because it's a good fit for their family, or because a food brand paid for placement.

For families managing food allergies, diabetes, celiac disease, or chronic kidney disease, this isn't just an inconvenience. A sponsored ingredient recommendation that conflicts with a medical dietary restriction is a safety issue.

WhollyFare exists because families deserve better.

---

## The Sincere Strategy: Six Commitments

### 1. No Paid Placements. Ever.
WhollyFare will never accept payment — in any form — to recommend a specific ingredient, brand, or product to a user. Not in the MVP. Not in v10. Not ever.

This is a founding constraint, not a preference. We build our business model around subscriptions and grocer partnership APIs — not advertising.

### 2. Health Constraints Are Sacrosanct
A household member's allergy, intolerance, or medical diagnosis is a hard constraint — not a preference that can be "relaxed" in exchange for a cheaper plan or a sponsored ingredient.

The engine will never output a meal plan that violates any member's documented health constraint. If it cannot build a valid plan within the budget, it tells the user honestly rather than silently dropping a constraint.

### 3. Radical Transparency in Every Recommendation
Every ingredient in every meal plan carries a visible explanation:
- Why it was selected (sale price, nutritional value, constraint satisfaction)
- What it costs per serving at the current sale price
- Which household member's constraints it satisfies (or doesn't conflict with)

Users are never shown a recommendation they can't audit.

### 4. Local-First Economics
We connect to the stores users already shop at, using their *actual* weekly sale prices. We don't use a national average price database that doesn't reflect what a family in rural Georgia or East Oakland actually pays.

Where grocer APIs permit, we surface rewards program savings and home delivery options — so families who can't easily get to the store are not left out.

### 5. Safety Over Savings
Budget optimization is always constrained by safety. The engine will never choose a slightly cheaper ingredient that violates a dietary constraint. Safety comes first; optimization happens within the safe set.

### 6. The User's Data Belongs to the User
Household health profiles — diagnoses, allergies, family member names — are sensitive. We will never sell, share, or train on individual user health data. Users can export their complete profile and delete their account at any time.

---

## What "Wholly" Means

The name WhollyFare carries a double meaning we take seriously:

- **Wholly** — complete, entire, leaving nothing out. A plan that accounts for every member of the household, every constraint, every preference.
- **Wholly on your side** — unlike the apps with hidden sponsors, we are completely and exclusively in the user's corner.

**Fare** — the food itself. What your family eats. Derived from the Old English *faran* — to journey. This is about the whole journey of feeding your family well.

---

## What This Means for Engineers

When you're making a product decision, ask:

1. Does this feature create a conflict of interest between the user's needs and any commercial relationship?
2. Does this expose a health-sensitive recommendation without an auditable explanation?
3. Does this reduce transparency, even slightly?

If the answer to any of these is "yes" or "maybe," stop and bring it to the team before shipping.

The Sincere Strategy is not marketing copy. It is a constraint on the system, the same way a nut allergy is a constraint on a meal plan.

---

*WhollyFare.com*
