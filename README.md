# WhollyFare

A meal-planning platform that saves families 15–25% on groceries through
cross-grocer price optimization, automated coupon matching, and a weekly
menu built from the best-priced safe ingredients available that week.

**Sentir Solutions, LLC — Confidential**

---

## Folder Structure

```
WhollyFare/
├── app/                    ← Product codebase (start here)
│   ├── core_logic/         ← Constraint engine, budget optimizer, meal planner
│   ├── data/               ← Flyer ingestor; data/flyers/ holds weekly circular JSONs
│   ├── docs/               ← Strategy source-of-truth (.md)
│   ├── interface/          ← Streamlit app and pages
│   └── tests/              ← Unit tests
│
├── integrations/           ← Grocer API clients and flyer parsers
│   ├── kroger/             ← Kroger Developer API client (OAuth2 + product/coupon)
│   ├── food_lion/          ← PDF weekly flyer parser → JSON
│   ├── giant/              ← PDF weekly flyer parser → JSON (Phase 2)
│   ├── walmart/            ← Walmart product/price API client (Phase 2)
│   └── wegmans/            ← PDF weekly flyer parser → JSON (Phase 2)
│
├── collateral/             ← Non-code outputs and reference material
│   ├── strategy/           ← WhollyFare_Blueprint.docx and strategic docs
│   ├── pitch/              ← Investor deck, one-pagers (Phase 3)
│   └── prework/            ← Gemini ideation session exports
│
├── phases/                 ← Phase-specific data and outputs
│   ├── phase1_poc/         ← Founder pilot: receipt logs, Found Money exports, case study
│   ├── phase2_beta/        ← Beta household tracker, testimonials
│   └── phase3_alpha/       ← Public alpha cohort metrics
│
└── Whollyfare/             ← Git repo stub (ignore)
    NOTE: "Website test/" is a legacy nested git repo — all code has been
    migrated to app/. Do not edit files in Website test/.
```

---

## Running the App (POC)

```bash
cd app
pip install streamlit pydantic
streamlit run interface/app.py
```

---

## Key Concepts

- **Sincere Strategy** — No paid placements. Ever. See `app/docs/sincere_strategy.md`
- **Sunday Buy-Off** — The weekly one-click approval experience
- **Found Money** — The auditable savings number vs. single-store and vs. HelloFresh
- **Flavor Plugins** — Same 5–7 hero ingredients, different cuisine each night

See `collateral/strategy/WhollyFare_Blueprint.docx` for the full product blueprint.
