# WhollyFare® — Agentic Coupon & Rewards Integration
## Architecture, Feasibility, and Staged Investment Roadmap

**Document status:** Working draft — strategic planning  
**Author:** Tim Hislop, Sentir Solutions® LLC  
**Date:** May 2026  
**Audience:** Internal + Investor briefing

---

## Executive Summary

WhollyFare's core value proposition — constraint-first, cross-grocer savings intelligence — becomes
substantially more powerful when it can act on the user's behalf: automatically ingesting weekly
circulars, pulling available digital coupons from the household's grocer accounts, and surfacing
matched savings before the shopping list is finalized.

This document evaluates two distinct problem domains:

1. **Automated circular ingestion** — replacing Tim's Wednesday manual workflow with a scheduled
   agentic pipeline that fetches, extracts, and stages flyer data with no human touch.

2. **User-authenticated rewards and coupon integration** — allowing WhollyFare to read a
   household's digital coupons (Food Lion MVP, Giant BonusCard, Kroger Plus, Flipp, etc.),
   stage them against the approved meal plan, and surface genuine incremental savings.

Both domains are achievable. They carry meaningfully different risk profiles, legal postures, and
fragility characteristics. The right path for each is a staged approach — starting with what's
clean and defensible, building toward what's powerful and durable.

The honest framing for investors: **the moat is not the data access method. The moat is the
constraint engine running on top of whatever data comes in.** Circular data access improves
over time. The engine that makes it useful is already built and running.

---

## Part 1 — Automated Circular Ingestion

### 1.1 Current State

Tim manually downloads PDF circulars from grocer websites every Wednesday and uploads them to the
WhollyFare Admin page, where Claude Vision (claude-haiku-4-5-20251001) extracts structured item
data — name, price, unit, category. Kroger is already automated via live API. The remaining
~9 stores require manual PDF handling: Food Lion, Aldi, Harris Teeter, Giant, Lidl, Walmart,
Whole Foods, Wegmans.

This works for a solo-operator pilot. It does not scale to 50 households and is not investor-ready
as a permanent workflow.

### 1.2 The Agentic Approach

A scheduled agent — running on GitHub Actions, a cloud function, or a lightweight VPS — performs
the following pipeline every Wednesday morning:

1. Fetch each store's circular PDF from a known URL or a scraped links page
2. Pass the PDF bytes to the existing Claude Vision extractor (`claude_extractor.py`)
3. Stage the result in a `pending_circulars` table in Supabase
4. Tim (or eventually, auto-approval logic) reviews and publishes
5. Items flow into `platform_flyer_items` and become available to all authenticated users

This mirrors exactly what Tim does today, with the human steps reduced to a 5-minute review
rather than a 45-minute download-upload-review cycle.

### 1.3 Legal and Terms of Service Posture

**Weekly circulars are public marketing documents.** Grocers publish them to drive foot traffic.
There is no reasonable legal argument that reading a public PDF constitutes unauthorized access
under the Computer Fraud and Abuse Act (CFAA) or any comparable statute.

Robots.txt disallows automated crawling on most grocer sites, but robots.txt is an advisory
standard, not law. Reading a publicly accessible URL does not constitute a CFAA violation — the
CFAA requires accessing a system "without authorization," and public web resources are, by
definition, authorized for access.

**Honest risk:** Grocer sites can detect and block automated fetching. A blocked URL breaks
that store's circular for the week. This is an operational fragility, not a legal exposure.
The mitigation is monitoring (alert if a fetch fails) and fallback to manual for that store.

**Risk rating: Low.** Public data, established legal precedent, no account credentials involved.

### 1.4 Technical Feasibility

| Store | Current Method | Automation Path | Fragility |
|---|---|---|---|
| Kroger | Live API (done) | Already automated | Very low |
| Food Lion | Manual PDF | Fetch from foodlion.com/weekly-specials | Medium |
| Aldi | Manual PDF | Fetch from aldi.us/en/weekly-specials | Medium |
| Harris Teeter | Manual PDF | Fetch from harristeeter.com/savings/weekly-ad | Medium |
| Giant | Manual PDF | Fetch from giantfood.com/weekly-specials | Medium |
| Lidl | Manual PDF | Fetch from lidl.com/en_US/weekly-specials | Medium |
| Walmart | Manual PDF | Walmart uses JavaScript-rendered pages; requires headless browser | High |
| Whole Foods | Manual PDF | PDF available; structured format varies | Medium |
| Wegmans | Manual PDF | PDF available; good structure | Low-Medium |

**The Walmart problem** is representative of a class of challenge: some grocer sites render
their circulars in JavaScript rather than serving a static PDF. For these, a headless browser
(Playwright, Puppeteer, or Claude in Chrome) is required, which adds complexity and increases
the chance of bot detection.

### 1.5 Benefits

- Eliminates Tim's 45-minute Wednesday workflow entirely
- Platform stays current even as WhollyFare scales beyond pilot
- Consistent, timestamped data ingestion supports investor-grade engagement metrics
- Staging layer lets Tim review before publishing — control without manual labor
- Claude Vision extraction already proven; this is plumbing, not new capability

### 1.6 Challenges

- Grocer websites change their circular URLs seasonally (especially around holidays)
- PDF format varies by chain; Food Lion and Giant PDFs differ significantly
- Walmart and some others require headless browser, not simple HTTP fetch
- Need monitoring to catch failed fetches before the week's plan is affected
- Rate limiting and IP blocking require respectful request pacing

### 1.7 Workarounds and Mitigations

- **URL monitoring:** Alert when a fetch returns non-PDF content or a 404. Tim gets a
  notification; falls back to manual for that store only.
- **Headless browser for JS-rendered stores:** Playwright running in a cloud function handles
  Walmart and similar. More complex but not fragile once set up.
- **Caching:** Store last-known-good PDF as fallback if this week's fetch fails.
- **Structured fallback order:** If automated extraction fails confidence thresholds, flag for
  manual review rather than publishing bad data silently.

### 1.8 The Better Path — Flipp Partnership

**Flipp** (flipp.com) aggregates weekly circulars from 2,000+ retailers across North America,
including every chain WhollyFare targets. They process and structure this data at scale.

A Flipp data partnership would give WhollyFare:
- Clean, structured item data without PDF parsing
- Automated weekly refresh with no URL maintenance
- Coverage that scales nationally as WhollyFare expands
- A defensible data supply chain for investor conversations

Flipp does not have a public API, but they do license data commercially. Their business model
is consumer-facing (their own app) plus data licensing to partners. A partnership conversation
becomes realistic once WhollyFare has demonstrable pilot traction — specifically, engaged
household counts and Found Money data. That is the investor metric that opens the door.

**Kroger precedent:** Kroger's developer API was not available to WhollyFare until Tim applied
and was approved. The same pattern applies at scale — demonstrated traction earns access.

**Staging recommendation:** Automate what can be automated now (Phase 2), use that as
proof-of-scale for a Flipp conversation (Phase 3).

---

## Part 2 — User-Authenticated Rewards and Coupon Integration

### 2.1 The Vision

A WhollyFare household connects their grocer loyalty accounts — Food Lion MVP, Giant BonusCard,
Kroger Plus, Flipp account for multi-chain coupons. When a meal plan is approved, an agent:

1. Authenticates with each connected store account using the user's credentials
2. Reads available digital coupons and loaded offers
3. Stages them against the approved plan — matching items, checking quantities, verifying
   that matched items pass the household's constraint engine
4. Surfaces genuine incremental savings: "Clip this $0.75 coupon for the chicken thighs
   in Tuesday's dinner — saves you $0.75 beyond the sale price"
5. Optionally clips the coupon to the user's store card automatically

This is a materially different value proposition than a coupon aggregator. WhollyFare knows
what the household is buying this week, which constraints apply, and which stores they're
visiting. That context makes the coupon match genuinely useful rather than a fire hose of
irrelevant offers.

### 2.2 Legal and Terms of Service Posture

This is the most important section in this document. The legal posture here is genuinely
nuanced and worth understanding fully before building.

**The core legal question:** Is it permissible for WhollyFare to access a user's grocer account
on their behalf, using their credentials, without a formal API partnership?

**The Mint/Plaid precedent:** For years, Mint (and eventually Plaid) accessed users' bank
accounts using their credentials — the same username and password the user would type. Courts
and regulators generally held that this was authorized access because the account holder
explicitly consented. The CFAA's "without authorization" standard is not violated when the
account holder gives permission.

**Grocer ToS reality:** Most grocer loyalty program Terms of Service prohibit automated access.
Food Lion's MVP terms, Giant's BonusCard terms, and similar agreements typically include
language like "you may not use automated means to access your account." This is a Terms of
Service violation, not a CFAA violation — but the distinction matters less if a grocer
decides to terminate the user's account or pursue civil remedies.

**The hiQ v. LinkedIn precedent (2022):** The Ninth Circuit held that scraping publicly
accessible LinkedIn data did not violate the CFAA. The ruling narrowed the definition of
"without authorization" to systems requiring authentication. This helps on the public
circular side; it is less directly applicable to authenticated account access.

**Honest risk rating: Medium-High** for user-credentialed access. Not illegal. Potentially
violates grocer ToS. Risk to the user (account suspension) and to WhollyFare (cease and
desist, forced shutdown of this feature) are real but manageable with the right architecture.

### 2.3 The Spectrum of Approaches

From most conservative to most capable:

**Tier 1 — User-entered coupon codes (no automation)**  
User manually enters a coupon code or barcode from their store app. WhollyFare checks it
against the current plan and tells them whether it applies to something they're buying.
Zero legal exposure. Low friction. Very limited. Good starting point.

**Tier 2 — User-prompted screenshot or image capture**  
User takes a screenshot of their available coupons in the store's app. WhollyFare's Claude
Vision layer reads the offers, extracts coupon data, stages against the plan.
User is doing the capture — WhollyFare is just reading what the user provides.
Awkward UX but legally clean. Technically interesting as a bridge.

**Tier 3 — User-credentialed agentic access (session-based)**  
User provides their loyalty account credentials. WhollyFare uses a headless browser or
Claude in Chrome to log in, read available coupons, stage them, and log out.
Credentials used for one session only — never stored in WhollyFare's database.
This is the Mint model. Medium-high ToS risk. High capability.

**Tier 4 — Aggregator API (Flipp, Coupons.com, Ibotta)**  
WhollyFare integrates with a coupon aggregator that has commercial relationships with
grocers. Clean data, stable API, no credential handling. Requires commercial agreement.
This is the right long-term path. Requires traction to negotiate.

**Tier 5 — Direct grocer API partnership**  
Grocer provides WhollyFare with an OAuth-authenticated API for their loyalty program.
Kroger already has this developer program. Food Lion, Giant, and others do not yet
publicly offer this, but it is negotiable at scale.
This is the durable, investor-grade solution. Requires demonstrated household engagement.

### 2.4 The Credential Handling Problem

If WhollyFare pursues Tier 3 (user-credentialed), the UX and security architecture around
credential handling is critical — both for user trust and for legal defensibility.

**What NOT to do:**
- Store usernames and passwords in WhollyFare's database, even encrypted
- Use credentials for anything beyond reading available coupons
- Access any account data beyond what is directly relevant to the coupon match

**The right architecture:**
- Credentials entered in the browser, never transmitted to WhollyFare's backend
- A client-side agent (Claude in Chrome running in the user's browser session) performs
  the login, reads coupon data, and returns structured data to WhollyFare
- No credentials leave the user's device
- Explicit consent screen: "WhollyFare will log into your Food Lion account once, read
  your available digital coupons, and log out. Your password is never stored."
- Session token approach where supported: some grocer apps issue short-lived session
  tokens that can be used without re-entering credentials

This architecture is similar to how Claude in Chrome operates today — the browser handles
authentication, the agent reads what the authenticated session shows, structured data
is returned to the application.

### 2.5 Benefits

- Transforms WhollyFare from "finds sale prices" to "finds everything that reduces your cost"
- Coupon match is context-aware: WhollyFare knows what you're buying, which stores you're
  visiting, and what constraints apply — no other coupon tool has all three
- Loyalty program data surfaces personalized offers that aren't in the public circular
- First-mover advantage: no meal planning tool does this at the constraint-engine level
- Investor story: TAM expands from "savings on planned meals" to "full household grocery savings"

### 2.6 Challenges

- Grocer sites actively resist automated access: CAPTCHA, rate limiting, bot detection,
  session timeouts, 2-factor authentication
- ToS exposure for both WhollyFare and potentially the user's account
- Grocer app UX changes break automation — Food Lion's web portal structure is not stable
- Credential handling UX is inherently higher-friction than a "connect your account" OAuth flow
- Some loyalty programs are app-only (no web login), requiring mobile automation which is
  substantially harder
- Scale: managing authenticated sessions across 10 grocer chains for N households requires
  infrastructure investment

### 2.7 Workarounds and Mitigations

- **Start with Tier 2 (screenshot)** as the MVP: proves the concept, shows households the
  value, generates engagement data, zero legal exposure
- **Use Claude in Chrome for Tier 3**: executes in the user's own browser session, no
  credentials leave the device, most defensible architecture
- **CAPTCHA mitigation**: build in human-in-the-loop fallback — if automated login fails,
  prompt user to complete the login manually, then agent continues
- **Respect rate limits**: implement polite request pacing, one coupon check per store per week
- **Monitor for breakage**: if a grocer login flow changes (new 2FA prompt, redesigned portal),
  flag immediately rather than silently failing
- **Insurance via Tier 4 negotiations**: pursue Flipp/Ibotta partnership in parallel so
  Tier 3 is a bridge strategy, not the permanent solution

### 2.8 Ibotta, Flipp, and the Aggregator Landscape

Several companies have already solved the commercial relationship problem with grocers:

**Ibotta** — cash-back offers linked to purchase verification. They have 2,400+ retail partners
including Food Lion, Giant, Kroger, and Walmart. They have a publisher API (Ibotta Performance
Network) designed for exactly this kind of integration. Ibotta receives a share of the offer
redemption value — WhollyFare would be a publisher surfacing their offers. This is commercially
clean and strategically interesting, but Ibotta's revenue model means offers may have commercial
intent. WhollyFare would need to be transparent about which offers come from Ibotta vs. from
the household's own loaded coupons. The Sincere Strategy requires disclosure.

**Flipp** — aggregates circulars and digital flyers. Less coupon-focused, more
price-comparison-focused. Closer to what WhollyFare needs for circular ingestion (Part 1).

**Coupons.com / Quotient Technology** — digital coupon network with grocer integrations.
Publisher API exists. Same disclosure consideration as Ibotta applies.

**The honest Sincere Strategy evaluation of aggregator partnerships:**  
Any aggregator that pays WhollyFare for surfacing their offers (affiliate/CPC model) creates
a conflict of interest. WhollyFare would be recommending coupons partly because a vendor paid,
not purely because they match the household's plan. This violates the Sincere Strategy.

The clean version: WhollyFare integrates an aggregator's API for data access only — surfacing
offers that genuinely match the plan regardless of commercial relationship — and either charges
a subscription premium for the feature (Tier 3+) or negotiates a flat data access fee rather
than a per-redemption fee. This preserves alignment.

---

## Part 3 — The Constraint Engine Is Always First

Regardless of data source — public circular, authenticated coupon account, or aggregator API —
the WhollyFare constraint engine runs before any offer reaches the household.

A Food Lion MVP coupon for tree nut trail mix does not surface for a household with a tree nut
allergy. An Ibotta offer for a high-sodium product does not appear for a CKD household.
An Aldi circular deal on a product containing a known allergen is excluded before the plan
is built.

This is not a UX feature. It is the architectural guarantee that makes WhollyFare trustworthy.
No other coupon or savings tool offers this because no other tool has the constraint layer.
That combination — real coupon data + constraint-first filtering — is the unique capability
that WhollyFare brings to this problem.

**This is also the investor framing:** WhollyFare is not a coupon app that happens to do
meal planning. It is a constraint-first household savings engine that can ingest coupon data
as one more signal. The distinction matters for valuation.

---

## Part 4 — Staged Roadmap

### Phase 1 — Pilot (Now)
- Tim manually loads circulars every Wednesday
- No coupon integration
- Kroger API automated; 9 stores manual
- Goal: prove the constraint engine + Found Money story with real households

### Phase 2 — Automated Circulars (Months 2–4)
- Scheduled agent fetches PDFs for 6–8 stores automatically
- Walmart and JS-rendered stores handled by headless browser or Claude in Chrome
- Tim reviews staged results, publishes with one click
- Alert system if a fetch fails; fallback to manual for that store
- **Investor milestone:** "Platform circular data is fully automated. Tim's Wednesday
  workflow is now a 5-minute review, not 45 minutes."

### Phase 3 — Coupon MVP: User Screenshot Capture (Months 3–5)
- User takes screenshot of available coupons in their store app
- WhollyFare reads the screenshot via Claude Vision, extracts offer data
- Constraint engine filters offers against household profile
- Matching offers surfaced on the shopping list with explanation
- No credential handling, no ToS exposure
- **Investor milestone:** "WhollyFare can surface coupon savings on top of circular savings,
  using only data the user provides. No commercial relationship required."

### Phase 4 — User-Credentialed Agentic Access (Months 5–9)
- "Connect your store account" UX — explicit consent, credential handling via client-side agent
- Claude in Chrome executes in the user's browser session; no passwords stored
- Covers Food Lion MVP, Giant BonusCard, Aldi Finds, Harris Teeter VIC card
- CAPTCHA fallback: user completes login manually if bot detection triggers
- Kroger Plus already covered via existing API
- **Investor milestone:** "WhollyFare reads a household's actual loaded digital coupons,
  not just the public circular. Savings include personalized loyalty offers."

### Phase 5 — Aggregator Partnership (Months 9–18, post-investment)
- Negotiate Flipp data partnership for circular ingestion at scale
- Evaluate Ibotta Performance Network for coupon data — flat access fee, not per-redemption
- Any aggregator integration disclosed to users with Sincere Strategy framing
- Replace Phase 4 credential handling with clean OAuth or API for partnered chains
- **Investor milestone:** "WhollyFare has a commercial data supply chain. Circular data
  is no longer scraped — it's licensed. Coupon data comes from direct grocer relationships."

### Phase 6 — Direct Grocer OAuth (Post-Series A)
- Apply to grocer developer programs as they become available (Kroger model)
- Negotiate direct loyalty API access with Food Lion, Giant, Harris Teeter, Walmart
- WhollyFare becomes a certified integration partner for each chain
- Platform data supply chain is fully defensible, no ToS exposure anywhere
- **Investor milestone:** "WhollyFare is a recognized integration partner for X grocer chains,
  covering Y% of U.S. grocery spend. Data supply is contractually guaranteed."

---

## Part 5 — UX Principles for Credential-Based Features

The household experience of connecting a loyalty account has to feel like trust, not risk.
Several principles apply regardless of the technical implementation:

**Plain language consent.** "WhollyFare will log into your Food Lion account once this week,
read your available digital coupons, and log out. We never store your password. Here's exactly
what we'll read and what we won't touch." No buried ToS. No "by clicking you agree to..."

**Show the reasoning.** For every coupon surfaced: this came from your Food Lion MVP account,
it applies to the chicken thighs in Tuesday's dinner, it saves you $0.75 beyond the sale price.
Not "great deal!" — a specific, auditable match. Sincere Strategy.

**Constraint disclosure.** "3 available coupons were filtered out because they apply to
products that don't meet your household's dietary profile." Same radical transparency as the
constraint engine.

**User control.** "Disconnect Food Lion account" is one tap. No dark patterns around
de-authorization. The household can see exactly what WhollyFare accessed and when.

**No credential storage ever.** This is non-negotiable. Credentials entered, session used,
credentials gone. Any architecture that requires storing credentials in WhollyFare's database
is the wrong architecture.

---

## Part 6 — Investor Framing

### The valuation case

Coupon and loyalty integration is not a feature. It is a TAM expansion.

WhollyFare's current value proposition: save money on planned meals by optimizing across
store circulars. That is measurable, real, and differentiable.

With coupon integration, the value proposition becomes: save money on everything you buy
at the grocery store, including items already in your plan and items you buy every week,
using every available savings mechanism — circulars, loyalty pricing, digital coupons,
personalized offers — filtered for your household's dietary constraints.

The average U.S. household spends ~$5,000/year on groceries. Available coupon savings
represent 10–15% of that for engaged savers. WhollyFare with coupon integration is
competing for a share of $500–750/year in recoverable household savings, not just
meal-plan optimization.

### The moat argument

The constraint-first architecture is the moat. A competitor can integrate Flipp's API.
A competitor can build coupon matching. A competitor cannot replicate the constraint engine
without rebuilding WhollyFare from scratch — and cannot do so profitably if their revenue
model depends on paid placements or affiliate fees.

The combination of real coupon data + constraint-first filtering is defensible precisely
because the constraint layer is not a bolt-on. It is the foundation everything runs on.

### The partnership negotiation lever

WhollyFare's pilot data — engaged households, weekly plan completion rates, Found Money
per household, repeat usage — is the negotiation asset that opens partnership conversations
with Flipp, Ibotta, and direct grocer chains.

"We have X households running weekly plans. They are high-engagement, health-conscious
grocery shoppers — exactly the demographic you want to reach. We want a data access
agreement, not a paid placement. Here's the case for why that benefits you."

That pitch is credible with 6–8 weeks of real pilot data. It is compelling with 20–30
households and $10,000+ in documented Found Money. It is fundable at 50+ households.

### The honest risk disclosure

For investors: the user-credentialed agentic approach (Phase 4) carries ToS risk that
could result in a grocer blocking WhollyFare's access method for their chain. This is
a feature risk, not a platform risk — it affects one store's coupon data, not the
core meal planning and circular savings functionality.

The staged approach is designed so that each phase is fully functional without the next.
Phase 1 works without Phase 2. Phase 3 works without Phase 4. No phase is load-bearing
for the phases before it. This de-risks the technical fragility while building toward
the durable partnership model.

---

## Appendix — Open Questions for Next Session

1. **Ibotta Performance Network evaluation** — is the flat-fee licensing model available,
   or is it exclusively per-redemption? Does the per-redemption model violate Sincere Strategy?

2. **Claude in Chrome for Phase 4** — confirm that the client-side execution model prevents
   credential transmission to WhollyFare's backend. Legal opinion on this architecture.

3. **Flipp outreach timing** — what engagement metrics are sufficient to open a partnership
   conversation? Is the Phase 2 pilot data (5–10 households, 8 weeks) enough?

4. **Disclosure language** — draft the in-app consent screen copy for Phase 4 credential
   handling. This needs to be plain language, complete, and reviewed.

5. **Food Lion MVP web portal stability** — is the login flow stable enough for Phase 4
   automation, or does it require the mobile app (which means iOS/Android automation)?

6. **Supabase schema for coupon data** — design the staging table structure for matched
   coupons before they're surfaced to the household. Needs household_id, source, item match,
   expiry, constraint_check_passed.

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*  
*The Sincere Strategy® — zero paid placements, constraints before optimization, radical transparency.*
