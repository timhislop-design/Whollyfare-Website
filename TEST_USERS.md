# WhollyFare — Test User Accounts

These accounts exist in the live Supabase project (`liviclgyapbeoefxbunh`).
Use the Sign In panel in the sidebar to log in. All emails are pre-confirmed.

---

## Tier 1 — Price Finder (Free)

| Field | Value |
|---|---|
| Email | `test.free@whollyfare.dev` |
| Password | `WhollyFare1!` |
| Household | The Free Household |
| Members | Alex (38), Sam (36) |
| Constraints | None |
| Budget | $80/week · 2 servings · 5 dinners |

**What to test:** Sign in → Household Setup restores from DB → Grocer Hub → price comparison flow. No health filters active. Clean baseline.

---

## Tier 2 — Meal Planner ($7/mo)

| Field | Value |
|---|---|
| Email | `test.planner@whollyfare.dev` |
| Password | `WhollyFare2!` |
| Household | The Planner Family |
| Members | Jordan (41), Casey (39), Riley (12), Morgan (9) |
| Constraints | Jordan: vegetarian · Morgan: no Brussels sprouts |
| Budget | $120/week · 4 servings · 5 dinners |

**What to test:** Full weekly flow — Household → Grocer Hub → Plan → Sunday Buy-Off → Shopping List → Ledger. This is the **primary test account** for the POC phase. Vegetarian preference filters Jordan's meals; Morgan's exclusion should never surface Brussels sprouts.

---

## Tier 3 — Health Guard ($19/mo)

| Field | Value |
|---|---|
| Email | `test.health@whollyfare.dev` |
| Password | `WhollyFare3!` |
| Household | The Health Household |
| Members | Taylor (46), Drew (44), Parker (14) |
| Constraints | Taylor: **celiac** (strict gluten-free) · Drew: **peanuts + tree nuts** allergy · Parker: **peanuts** allergy + no mushrooms |
| Budget | $140/week · 4 servings · 5 dinners |

**What to test:** Constraint engine. Three hard rules from three members combine: every plan must be gluten-free AND peanut/tree-nut-free AND mushroom-free. The constraint audit log should show exactly which member triggered each rejection.

---

## Tier 4 — Full Table ($29/mo)

| Field | Value |
|---|---|
| Email | `test.full@whollyfare.dev` |
| Password | `WhollyFare4!` |
| Household | The Full Table Family |
| Members | Quinn (51), Avery (48), Blake (16), Cameron (13) |
| Constraints | Quinn: **hypertension** (AHA low-sodium) · Avery: **type2_diabetes + dairy-free** · Blake: **shellfish** allergy |
| Budget | $160/week · 5 servings · 5 dinners |

**What to test:** Multi-condition constraint stacking. Three medical conditions + one allergy running simultaneously. Useful for the Health Guard demo to investors — shows clinical-grade filtering working across a realistic household.

---

## Notes

- **Tier 1 and 2 are the primary focus** for the current POC sprint. Tiers 3 and 4 are seeded so constraint-engine testing is always available without manual setup.
- All accounts are email-confirmed. No email verification step required.
- Passwords follow the pattern `WhollyFare{tier}!` — easy to remember on-site during a demo.
- Data persists in Supabase across sessions. If you edit a household profile and save, it will be there next time you sign in.
- **Do not share these credentials publicly** — they connect to the live pilot database.

---

## For pilot friends (Phase 2)

When onboarding pilot households, they will create their own accounts via the Sign In → Create Account tab in the sidebar. Their data will be isolated to their own household via RLS — they will never see Tim's data or these test accounts' data.

---

*WhollyFare® · Sentir Solutions® LLC · Last updated: 2026-05-19*
