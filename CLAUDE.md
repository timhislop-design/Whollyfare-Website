# WhollyFare® — Project Briefing for Claude

This file is read automatically at the start of every session. It is the
single source of truth for context, decisions already made, and how to work
with Tim on this project. Read it fully before doing anything.

---

## What This Is

WhollyFare® is a meal-planning platform built by Tim Hislop under his LLC
**Sentir Solutions® LLC** (Palmyra / Charlottesville, VA). It is a standalone
product — separate from Sentir Solutions' AI consulting practice.

**Core value proposition:** Cross-grocer price optimization + automated coupon
harvesting. WhollyFare builds a weekly dinner plan from your local grocery
stores' actual sale circulars, filtered for your household's dietary constraints,
and shows you exactly how much you saved vs. single-store shopping and vs.
HelloFresh.

**The founding philosophy is called the Sincere Strategy®:**
- Zero paid placements. Ever. Revenue is subscriptions only.
- Health constraints are absolute hard rules, never traded for savings.
- Every ingredient rejection is logged and shown to the user (radical transparency).
- Local-first: plans built from your actual stores' actual circulars.
- Safety before savings, always. The constraint engine runs before the optimizer.
- User data is never sold, shared, or used for targeting.

This is the moat. Competitors cannot copy it without destroying their own
revenue model. That asymmetry is structural and durable.

---

## The Pilot Household

Tim Hislop, Abby, and Chas — Charlottesville, VA.
Stores: Kroger Barracks Road, Food Lion Pantops, Aldi Rio Road, Harris Teeter Barracks Road.

The pilot runs on **manual flyer entry** (type items from the weekly circular)
with PDF upload as a secondary path. Manual entry is the reliable path — PDF
parsing is heuristic and will miss items.

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

## Project Phases

**Phase 1 (now):** POC. Hislop family pilot, Charlottesville stores, manual flyer
entry, 8 weeks of real receipts. Goal: undeniable Found Money data.

**Phase 2 (months 2–5):** 5–10 pilot households — friends and family recruited by Tim.
Moms who quit HelloFresh. Allergy households. Budget-conscious families. Build what
the pilot data tells us to build.

**Phase 3 (post-investment, months 6–18):** Regional scale. Real web app
(React + FastAPI, not Streamlit). Multi-household accounts. Automated circular
parsing. Cookbook. Pantry tracker. Meal type selection (casual, date night, etc.).
Health system B2B licensing.

**Phase 4 (Series A, months 18–36):** National. 15+ grocer chains. 50,000+
households. $2M+ ARR. National brand built on the Sincere Strategy®.

**Investment target: 7–8 figures.** The pilot data (Phase 1) + beta household
data (Phase 2) is what gets Tim in the room. The roadmap page and investor brief
are the argument that justifies the number.

---

## Tech Stack

- **Language:** Python
- **UI:** Streamlit (MVP only — React + FastAPI in Phase 3)
- **Core logic:** `app/core_logic/` — constraint engine, budget optimizer, meal planner
- **Data:** `app/data/` — flyer ingestor, sample data
- **UI pages:** `ui/` — Home.py + 8 pages in `ui/pages/`
- **Integrations:** `integrations/` — Food Lion PDF parser, Kroger API client
- **Docs:** `PLAYBOOK.md` — full strategic spec, POC vs. production for every feature

**Session state is the database in the POC.** Data is lost on browser refresh.
This is a known limitation. Every file that touches persistence has a comment
explaining what production would require (PostgreSQL, user accounts, etc.).

---

## What's Already Built

| Page | File | Status |
|---|---|---|
| Home / Landing | `ui/Home.py` | ✅ Complete — hero, pricing tiers, how it works |
| Household Setup | `ui/pages/1_Household.py` | ✅ Complete — pilot-friend ready |
| Grocer Hub | `ui/pages/2_Grocer_Hub.py` | ✅ Complete — manual entry + PDF + Cville presets |
| This Week's Plan | `ui/pages/3_Plan.py` | ✅ Built |
| Sunday Buy-Off | `ui/pages/4_Sunday_BuyOff.py` | ✅ Built — needs polish |
| Shopping List | `ui/pages/5_Shopping_List.py` | ✅ Built |
| Found Money Ledger | `ui/pages/6_Ledger.py` | ✅ Complete — receipt logger, CSV export |
| Investor Brief | `ui/pages/7_Investor.py` | ✅ Complete — production-quality |
| Product Roadmap | `ui/pages/8_Roadmap.py` | ✅ Complete — 4-phase investor roadmap |

---

## How to Run the App

```bash
cd Whollyfare-Website
streamlit run ui/Home.py
```

Dependencies: `pip install streamlit pydantic pdfplumber pandas`

---

## How Tim Works

- Tim is the founder and sole operator right now. He codes with Claude, not
  independently. Assume he needs decisions explained, not just executed.
- He moves fast. Don't over-plan. Build the page, explain the key decisions,
  move on.
- He cares deeply about honesty and transparency — in the product and in how
  we work. If something is a shortcut, name it as a shortcut.
- Every file should have inline comments marking POC shortcuts vs. what
  production would require. This is not technical debt documentation — it's
  the investor argument embedded in the code.
- The goal is investor meetings with real data, 7–8 figure raise, hire a team,
  execute. This is Tim's path to leaving his day job (ECS) and building
  something that matters for his family and thousands of others.

---

## What to Build Next

Priority order (as of May 2026):

1. **Sunday Buy-Off polish** (`4_Sunday_BuyOff.py`) — needs to feel like the
   signature moment of the product: one screen, one decision, one tap. Currently
   functional but not emotionally resonant.

2. **This Week's Plan polish** (`3_Plan.py`) — review for clarity. Pilot friends
   need to understand the plan without explanation.

3. **Shopping List** (`5_Shopping_List.py`) — must be usable on a phone in a
   grocery store. That's the bar.

4. **Pilot onboarding guide** — a simple how-to document (or in-app walkthrough)
   so pilot friends can set up and run a week without Tim present.

Do not build new features before the existing flow works end-to-end without
hand-holding. Fix before you add.

---

## What NOT to Do

- Do not suggest ad revenue, affiliate revenue, or sponsored content. Ever.
- Do not add a feature that creates a conflict of interest between WhollyFare
  and the household it serves.
- Do not confuse this project with Sentir Solutions (Tim's AI consulting firm).
  They are separate companies. WhollyFare is the product. Sentir Solutions is
  the vehicle.
- Do not use `st.session_state` to persist anything critical without noting in
  a comment that this is a POC limitation.
- Do not describe POC limitations as bugs. They are design decisions appropriate
  for this stage.

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*
*Contact: tim.hislop@gmail.com*
