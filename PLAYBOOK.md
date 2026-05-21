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
**Infrastructure:** Streamlit Community Cloud (free tier) + Supabase (free tier)  
**Goal:** 8 weeks of real household data. Real receipts. Real savings numbers.

**What it costs to run:** ~$0/month  
**What it proves:** The engine logic is sound and the savings are real.

**Known Stage 1 infrastructure constraints (by design, not bugs):**
- Streamlit Community Cloud idles apps after ~15 min of inactivity. Pilot users
  will occasionally see a "This app has gone to sleep" click-through screen. Brief
  them on this. It is a hosting limitation, not a product bug.
- Session state lives server-side in the Python process. A worker restart wipes it.
  The app now stores the Supabase refresh token in browser localStorage to restore
  sessions automatically — but a clean browser (private mode, new device) will
  require a sign-in.
- These constraints are acceptable for a 1-household pilot. They become unacceptable
  at 5+ pilot households and must be resolved before Stage 2 recruiting begins.

**Infrastructure upgrade trigger:** When you have 3+ pilot households actively using
the app, evaluate the Stage 1.5 bridge below before moving to full Stage 2.

---

---

### Stage 1.5 — Pilot Bridge (no investment required, ~$10–20/month)

This is the gap between "it works for Tim" and "it works for 5–10 pilot friends
without hand-holding." Do this before the Stage 2 investment conversation, because
pilot data from a stable environment is worth more than pilot data from a flaky one.

**What changes:**
- Move hosting from Streamlit Community Cloud (free, idle-restarts) to
  **Railway** (railway.app) or **Render** (render.com). Same Streamlit codebase,
  zero code changes. Deploy with `railway up` or connect the GitHub repo directly.
  Cost: ~$5–10/month. Benefit: no idle restarts, private URL, stable sessions.
- Stay on Supabase free tier (500MB, 50K MAU limit — more than enough for Stage 1.5).

**What does NOT change:**
- Streamlit as the UI framework (Phase 3 replaces it with React + FastAPI)
- The constraint engine, meal planner, and all existing logic
- The Supabase schema — no migration needed

**How to deploy to Railway:**
1. Install Railway CLI: `npm install -g @railway/cli`
2. In the repo root: `railway login && railway init`
3. Add a `Procfile` (one line): `web: streamlit run ui/Home.py --server.port $PORT --server.address 0.0.0.0`
4. Add environment variables in Railway dashboard (copy from `.streamlit/secrets.toml`)
5. `railway up` — Railway detects Python, installs requirements.txt, starts the app
6. Set a custom domain or use the `.railway.app` URL as the pilot URL

**Database note for Stage 1.5:** Supabase free tier is sufficient. No action needed.

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

**Infrastructure decision at Stage 2 entry — Hosting:**
At Stage 2, Streamlit is replaced with React + FastAPI (see Stage 3 below). The
hosting platform decision should be made alongside the framework decision.
Recommendation: **Railway or Render** for the React/FastAPI app until Series A
(simple deploys, auto-scaling, ~$100–200/month at pilot scale). Migrate to
AWS ECS or GCP Cloud Run at Series A with dedicated DevOps.

**Infrastructure decision at Stage 2 entry — Database:**
Supabase is the right choice through Stage 2 and likely into Stage 3.
Evaluate alternatives only if one of these triggers fires:

| Trigger | Action |
|---|---|
| Row count exceeds ~1M (receipts + ledger entries at scale) | Evaluate Aurora Serverless (AWS) or Neon (Postgres, serverless billing) |
| Supabase pricing becomes prohibitive (>$500/month) | Migrate to self-hosted Postgres on Railway/Render — same schema, no code change |
| Real-time features needed (live price sync, push notifications) | Supabase Realtime is already built in — no migration needed |
| HIPAA compliance required (health system B2B) | Migrate to AWS RDS with VPC + audit logging; Supabase is not HIPAA-eligible |
| Multi-region latency (national rollout) | Neon or PlanetScale for global read replicas |

**Recommendation:** Stay on Supabase through Stage 2 and into early Stage 3.
It is a managed Postgres service with built-in auth (Supabase Auth), row-level
security (already wired in WhollyFare), storage, and an MCP plugin for Claude
(used in development). The only realistic migration trigger before Series A is
the HIPAA scenario, which requires a dedicated compliance review regardless of
database choice.

**What to evaluate at Series A (Stage 3 entry):**
- Supabase Pro → Enterprise pricing ($599+/month) vs. self-hosted Postgres on ECS
- Aurora Serverless v2 for auto-scaling at 50K+ households
- Redis for session caching and price-lookup hot paths
- A read replica for the analytics / investor reporting workload (separate from
  the transactional DB to avoid query contention)

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
| **Hosting** | Streamlit Community Cloud (free, idles) → Railway/Render at Stage 1.5 (~$10/mo, no code change) | Railway/Render (Stage 2 React app) → AWS ECS / GCP Cloud Run (Series A) |
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
