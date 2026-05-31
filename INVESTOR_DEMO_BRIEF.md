# WhollyFare® — National Investor Demo Briefing
### Session goal: walk into the room with live data from 5 markets

---

## The Pitch Moment

You open a laptop. You switch a zip code. A different city's grocery stores appear with live sale prices. You switch again. Different city, different banner, same credentials. You click one button. A PDF downloads showing which grocery holding company wins each ingredient category in five American cities this week.

That's the demo. Build it today.

---

## What to Build: National Demo Tab in Admin

Add a **6th tab** to `ui/pages/11_Admin.py`: `🌎 National Demo`

### Section 1 — Market Loader

A table row for each metro. For each:
- Metro name + expected Kroger banner + location ID (pre-filled, confirmed)
- "Pull API" button — runs `get_weekly_sales()` for that location, stores result in `platform_flyer_items` tagged by chain
- Suggested PDF stores for that market (name + direct flyer URL, clickable) — Tim uploads these manually
- Status indicator: ✓ API loaded / ✓ PDFs uploaded / ⚠ missing

**Kroger API pulls (all pre-wired, no setup needed):**

| Metro | Banner | Location ID |
|-------|--------|-------------|
| Charlottesville VA | Kroger | `02900359` |
| Charlotte NC | Harris Teeter | `09700205` |
| Denver CO | King Soopers | `62000115` |
| Chicago IL | Marianos | `53100503` |
| Los Angeles CA | Ralphs | `70300022` |

**Suggested PDFs to upload per market (Tim does this day-of):**

*Charlotte NC*
- Food Lion — foodlion.com/weekly-specials (Wednesday)
- Publix — publix.com/savings/weekly-ad (Wednesday)
- Aldi — aldi.us/en/weekly-specials (Wednesday)
- Lidl — lidl.com/en-us/en (Wednesday)

*Denver CO*
- Safeway — safeway.com/weeklyad (Wednesday)
- Aldi — aldi.us/en/weekly-specials (Wednesday)
- Sprouts — sprouts.com/weekly-sales (Wednesday)
- Whole Foods — (Wednesday, good premium contrast)

*Chicago IL*
- Jewel-Osco — jewelosco.com/weeklyad (Wednesday) — dominant chain
- Aldi — aldi.us/en/weekly-specials (Wednesday) — huge Aldi market
- Whole Foods — (Wednesday)

*Los Angeles CA*
- Vons — vons.com/weeklyad (Wednesday, Albertsons brand)
- Aldi — aldi.us/en/weekly-specials (Wednesday)
- Sprouts — sprouts.com/weekly-sales (Wednesday)
- Food 4 Less — (Kroger value banner, already in API results as id=70400770)

*Charlottesville VA (keep current)*
- Food Lion Pantops — foodlion.com/weekly-specials ✓
- Giant — giantfood.com/weekly-circular ✓
- Aldi Rio Rd — aldi.us/en/weekly-specials ✓

---

### Section 2 — Per-Market Results Dashboard

After data is loaded, a 5-card grid. One card per metro showing:
- Items loaded (API + PDF counts)
- Categories covered
- Top 3 sale items this week (name + price)
- Last pulled timestamp

This is the "it's real" panel. Show it in the meeting.

---

### Section 3 — Generate National Report

One button: **"Generate National Market Intelligence Report (PDF)"**

Runs `build_report()` across all 5 metros in one document:
- Holding company grouping (Kroger Co., Ahold Delhaize, Albertsons, etc.)
- Brand scores per metro — which banner wins which category where
- Visual indicators: 🟢 beating portfolio avg + market avg / 🟡 mixed / 🔴 lagging
- Footer: "The Sincere Strategy® — Zero paid placements. Honest math. Household first. Always."

Downloads as: `whollyfare_national_demo_YYYY-MM-DD.pdf`

---

## The Zip-Switching Live Demo (in-meeting flow)

**~4 minutes total. No slides.**

1. Open app → Account page → home zip = `22901` (Charlottesville)
2. Grocer Hub → show Kroger, Food Lion, Harris Teeter, Aldi with live sale prices
3. Switch zip to `28201` (Charlotte) → Grocer Hub refreshes → Harris Teeter + Food Lion + Publix appear
4. "Different city. Same app. Same credentials pulling the Kroger API."
5. Switch to `80202` (Denver) → King Soopers appears
6. Switch to `60601` (Chicago) → Marianos
7. Switch to `90012` (LA) → Ralphs Fresh Fare
8. Open Admin → National Demo tab → show per-market data cards already loaded
9. Click "Generate National Report" → PDF downloads in seconds
10. Open PDF → holding company grouping, brand scores, visual indicators across all 5 cities
11. "This is what WhollyFare does in every Kroger banner market in the country. Today."

**Key lines:**
- *"One developer account. 2,800+ stores. 15 banner brands."*
- *"We don't need to build for scale — we're already at scale. We need households to catch up to the infrastructure."*
- *"Every time a household registers in Denver, we add one store to Wednesday's pull. The architecture doesn't change."*
- *"Food Lion beat Kroger in Charlottesville this week. The algorithm doesn't care who has the API relationship."*

---

## Build Order for This Session

1. **Add National Demo tab to Admin** — new tab_demo, Section 1 loader table with pre-filled location IDs and PDF store suggestions per market
2. **Per-market results cards** — Section 2 dashboard pulling from `platform_flyer_items` grouped by metro
3. **Multi-metro report** — upgrade `build_report()` to accept multiple metros, add holding company grouping and brand score visual indicators
4. **Food 4 Less** — add as 16th Kroger banner in `KROGER_BANNERS`, add LA store entry with id `70400770`
5. **Pre-load demo data** — Tim runs API pulls for all 5 metros from the new tab, uploads PDFs for each market
6. **Generate and review the report** — confirm it reads like a leave-behind an investor would keep

---

## Before the Meeting Checklist

- [ ] National Demo tab built and deployed to Streamlit Cloud
- [ ] All 5 Kroger API pulls completed (Admin → National Demo → Pull All)
- [ ] PDFs uploaded for Charlotte, Denver, Chicago, LA (4 markets × 3-4 stores)
- [ ] National report generated and reviewed — looks investor-ready
- [ ] Zip-switching flow tested on phone (mobile demo is more impressive in a room)
- [ ] Report printed OR saved to phone as PDF backup

---

*WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA*
*Built 2026-05-30 — National scale confirmed.*
