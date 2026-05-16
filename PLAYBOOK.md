# WhollyFare® — Proof of Concept Playbook
### Sentir Solutions® LLC · Charlottesville, VA · May 2026

---

> This document is a working spec, not a pitch deck. It maps every feature of the
> current POC to what production would require — technically, operationally, and
> financially. Tim Hislop and any serious investor should be able to challenge
> every line in it.

---

## What the POC Is

A fully functional meal-planning application running on a single server (Streamlit)
for a single household (the Hislop family, Charlottesville VA) using real weekly
grocery circulars from four local stores: Kroger, Food Lion, Aldi, and Harris Teeter.

**The POC proves three things:**
1. The core engine works — constraint filtering, budget optimization, and meal assembly
   produce coherent, safe, affordable weekly plans from real sale prices.
2. The savings are real — the Found Money Ledger records actual receipt-vs-plan comparisons,
   not projections.
3. The investor thesis is defensible — the Sincere Strategy moat holds up under scrutiny.

**The POC does not prove:**
- Scale (it's one household on one machine)
- Automation (PDF parsing is heuristic; manual entry is the reliable fallback)
- Retention (we have one user by design)
- Revenue (no payment processing; pricing is illustrative)

That's not weakness. That's honesty. An investor who understands the difference between
"proof of concept" and "product" is the investor this company needs.

---

## The Three Stages

### Stage 1 — Local POC (now)
**Geography:** Charlottesville, VA metro  
**Households:** 1 (Hislop family: Tim, Abby, Chas)  
**Stores:** Kroger Barracks Road, Food Lion Pantops, Aldi Rio Road, Harris Teeter Barracks Road  
**Data pipeline:** Manual item entry + PDF upload (heuristic parser)  
**Infrastructure:** Streamlit Community Cloud or local laptop  
**Goal:** 8 weeks of real household data. Real receipts. Real savings numbers.

**What it costs to run:** ~$0/month (Streamlit free tier, no cloud DB)  
**What it proves:** The engine logic is sound and the savings are real.

---

### Stage 2 — Regional (investment unlocks this)
**Geography:** Central Virginia + DC corridor (Charlottesville, Richmond, Northern VA)  
**Households:** 25–100 beta households across 5 dietary profiles  
**Stores:** Kroger, Food Lion, Aldi, Giant, Wegmans, Harris Teeter  
**Data pipeline:** Improved PDF parsers per chain + Kroger API integration  
**Infrastructure:** Hosted web app (Railway or Render), PostgreSQL, basic auth  
**Goal:** Retention data, NPS, savings validation across diverse households  

**What it costs to build:** $40,000–80,000 (6–9 months, one developer + Tim)  
**What it costs to run:** $300–800/month (hosting, DB, USDA API calls)  
**What it proves:** The model works beyond one household. Retention is real. Savings hold.

**Regional requires investment in:**
- A real database (PostgreSQL). Session state doesn't survive a browser refresh.
- User accounts (email/password or OAuth). Right now there's no such thing as a "user."
- A proper web framework (React + FastAPI). Streamlit is not production-grade.
- PDF parser improvement. Current heuristic accuracy is 60–80% on a good week.
  Chain-specific parsers with test suites are 4–6 weeks of engineering each.
- Legal review of health constraint claims. "Clinical-grade" is a phrase with liability attached.
  A dietitian review of every constraint ruleset is non-negotiable before public launch.

---

### Stage 3 — National (Series A territory)
**Geography:** Top 30 U.S. metro markets  
**Households:** 50,000+ (Year 3 target)  
**Stores:** 15+ chains via API partnerships, supplemented by PDF parsing  
**Data pipeline:** Grocer API integrations (negotiated partnerships), automated USDA enrichment  
**Infrastructure:** AWS/GCP, microservices, background task queues, CDN  
**Goal:** $2M ARR from paid subscribers; B2B licensing to health systems

**What it costs to build:** $500,000–1,500,000 (Series A round, 18-month runway)  
**What it costs to run:** $15,000–40,000/month at 50K households  

**National requires investment in:**
- Grocer API partnerships. Kroger's API exists; Food Lion, Aldi, and HT do not have
  public APIs. Getting data at scale means either scraping (legal risk) or negotiated
  data-sharing agreements (6–18 month BD cycles, legal cost).
- A real engineering team. 4–6 engineers to build the production stack.
- Clinical validation. A registered dietitian on staff or on retainer for each
  medical constraint ruleset (celiac, CKD, diabetes, MCAS, etc.).
- USDA FDC at scale. The free USDA API rate-limits at 1,000 calls/hour.
  Production volume requires a data licensing agreement.
- Compliance review. HIPAA is not triggered by meal planning alone, but the moment
  WhollyFare markets to healthcare or handles anything construed as medical advice,
  legal review is required. Budget $30,000–60,000 for initial compliance work.
- Customer support. A product used by celiac and allergy households has zero tolerance
  for errors. Support is not optional.

---

## Feature-by-Feature: POC vs. Production

| Feature | POC (now) | Production |
|---|---|---|
| **User accounts** | None — one household hardcoded | Auth0 or Cognito, email/password + OAuth |
| **Data persistence** | Streamlit session_state (lost on refresh) | PostgreSQL, user_id + week_id indexed |
| **Grocer data** | Manual entry + PDF heuristic parser | Grocer APIs + trained per-chain PDF parsers |
| **USDA nutrition** | Stubs (hardcoded 100g weight) | USDA FoodData Central API, async enrichment |
| **Constraint engine** | Rule-based Python, runs in-request | Same rules, runs as background task (Celery) |
| **PDF parsing accuracy** | 60–80% (regex heuristic) | 90–95%+ (chain-specific parsers with test suites) |
| **Allergen data** | User-declared in manual entry | USDA FDC + user declaration + dietitian review |
| **Coupon matching** | Not built | Digital coupon API or store-specific scraping |
| **Meal recipes** | Flavor Plugin method hints only | Full step-by-step recipes (Tier 4) |
| **Shopping list delivery** | Display in browser | Email, SMS, or share link |
| **Found Money Ledger** | Manual receipt entry | Automated via receipt photo OCR or loyalty API |
| **Multi-household** | 1 household | Unlimited, isolated by user_id |
| **Hosting** | Streamlit Community Cloud / laptop | Railway → AWS ECS / GCP Cloud Run |
| **Uptime SLA** | None (best-effort) | 99.5% (needed for health-constraint users) |
| **Payments** | None | Stripe subscription billing |
| **Mobile** | Responsive Streamlit (functional) | Native PWA or React Native |

---

## The Moat — What Competitors Cannot Copy

This is the part worth debating with an investor.

The Sincere Strategy creates asymmetric protection: **every WhollyFare commitment is a
direct conflict of interest for every existing competitor.**

1. **No paid placements.** HelloFresh, Flipp, Ibotta, and Instacart earn from sponsored
   content. Removing paid placements destroys their revenue model. WhollyFare earns only
   from subscriptions — so the recommendation is always the cheapest safe option.

2. **Health constraints are absolute.** Building a hard constraint engine that rejects
   ingredients rather than warning about them is an engineering and liability choice.
   Incumbents show warnings. WhollyFare refuses. That's not a feature; it's a design
   philosophy that a company with advertiser relationships cannot afford.

3. **Radical transparency.** The audit log showing why every ingredient was rejected is
   a trust feature. No competitor shows this because it exposes the conflicts in their
   recommendation logic.

4. **Local-first.** National meal-kit services use national average pricing and
   pre-selected inventory. WhollyFare uses your actual store's actual sale circular.
   This is only possible without grocer relationships that create bias.

**The question an investor should ask:** Can a well-funded competitor build this?

**The answer:** Yes, technically. But they would have to abandon their existing revenue
model to do it. A company that earns $50M/year from paid placements is not going to
voluntarily remove them to copy WhollyFare. The moat is structural, not just technical.

---

## The Ask — What Investment Buys

**Seed round target: $250,000–400,000**  
**Runway:** 18 months  
**Use of funds:**

| Category | Allocation | What it buys |
|---|---|---|
| Engineering | 55% | One full-stack developer (contract or hire), database build, web app migration from Streamlit, PDF parser improvement |
| Clinical validation | 15% | Registered dietitian review of all constraint rulesets; legal review of health claims language |
| GTM — Charlottesville/VA | 15% | Local household acquisition (SEO, community partnerships, MCAS/celiac support groups), first 50 paid users |
| Operations & legal | 10% | LLC formalization, IP filing, Stripe integration, USDA data license |
| Reserve | 5% | Buffer |

**What seed money does NOT buy:** National grocer partnerships, a large engineering
team, or TV advertising. That's Series A. Seed proves the model at regional scale
and delivers the data that makes Series A possible.

---

## The Four Questions Tim Should Be Able to Answer Cold

**1. What does one week of the product cost to run?**  
POC: ~$0. Regional: ~$400/month for 50 households. National: scales with usage.

**2. What's the unit economics at steady state?**  
$19/month Health Guard subscriber. COGS: ~$0.80/month (hosting + compute + USDA API calls).
Gross margin: ~96%. Customer acquisition cost (CAC) is the variable; target <$40 via
community-led growth through medical support groups.

**3. What breaks at 1,000 households?**  
The Streamlit session model (no shared state). The synchronous engine run (timeouts).
The USDA free API tier. PDF parsing at volume. All known. All solvable with the seed round.

**4. What's the risk that a big company just builds this?**  
See "The Moat" section. The risk is not that they build it — it's that they can't
build it honestly without dismantling their revenue model. That's the bet.

---

## Weekly POC Workflow (Charlottesville)

Every Sunday, the process is:

1. Download the weekly circular PDF from Kroger, Food Lion, Aldi (Charlottesville locations)
2. Upload to Grocer Hub → parse + manual entry for any missed items
3. Run the engine → review the plan on This Week's Plan page
4. Sunday Buy-Off → approve the week → Found Money recorded
5. Shop Tuesday–Wednesday (when shelves are restocked from weekend)
6. Log actual receipt total in the Ledger → real savings data accumulates

**After 8 weeks:** The ledger is the investor pitch. Real dollar amounts, real weeks,
real household. That's not a projection. That's a case study.

---

*WhollyFare® is a product of Sentir Solutions® LLC. Charlottesville, VA.*  
*Contact: tim.hislop@gmail.com*  
*This document is a working internal spec. Not for distribution without authorization.*
