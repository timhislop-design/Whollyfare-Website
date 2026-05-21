# WhollyFare

**Eat well. Spend less. No compromises.**

A meal-planning platform that saves families 15–25% on groceries through cross-grocer price optimization, automated coupon matching, and a weekly menu built from the best-priced safe ingredients available that week.

**Sentir Solutions, LLC — Confidential**

---

## Run the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Folder Structure

```
WhollyFare/
│
├── app.py                  ← Entry point — run this
├── requirements.txt        ← Python dependencies
│
├── ui/                     ← Streamlit app (7 pages)
│   ├── Home.py             ← Dashboard
│   ├── style.py            ← Brand CSS + Leaf+Fork logo (Direction A)
│   ├── state.py            ← Session state helpers
│   └── pages/
│       ├── 1_Household.py  ← Household & member profile setup
│       ├── 2_Grocer_Hub.py ← Load weekly store data (API pull + PDF upload)
│       ├── 3_Plan.py       ← Generated meal plan + constraint audit log
│       ├── 4_Sunday_BuyOff.py ← One-click weekly approval + Found Money
│       ├── 5_Shopping_List.py ← Shopping list by category, with export
│       ├── 6_Ledger.py     ← Found Money history + cumulative savings
│       └── 7_Investor.py   ← Investor brief (live in the app)
│
├── app/                    ← Planning engine
│   ├── core_logic/         ← Constraint engine, budget optimizer, meal planner
│   ├── data/               ← Flyer ingestor; data/flyers/ holds weekly JSONs
│   └── docs/               ← Sincere Strategy, product tiers, roadmap (.md)
│
├── integrations/           ← Grocer API clients and flyer parsers
│   ├── food_lion/          ← PDF flyer parser + USDA enricher (built)
│   └── kroger/             ← Kroger Developer API client — OAuth2 (built)
│
├── collateral/
│   ├── strategy/           ← WhollyFare_Blueprint_v2.docx
│   └── prework/            ← Original Gemini ideation session docs
│
└── phases/                 ← Phase-specific outputs and receipts
    ├── phase1_poc/
    ├── phase2_beta/
    └── phase3_alpha/
```

---

## Key Concepts

- **Sincere Strategy** — No paid placements. Ever. See `app/docs/sincere_strategy.md`
- **Sunday Buy-Off** — The weekly one-click approval screen. The killer UX moment.
- **Found Money** — Auditable savings vs. single-store shopping and vs. HelloFresh