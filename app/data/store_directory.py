"""
store_directory.py -- Charlottesville-area store directory for WhollyFare Admin.

Every store Tim can pull a weekly circular from, with:
  - chain / location / flyer_url
  - method: "kroger_api" | "pdf" | "manual"
  - notes: what to expect, any quirks

Pilot: Tim downloads PDFs manually each week and uploads via the Admin page.
       Kroger pulls automatically via the existing API integration.
Phase 2: Scheduled task downloads PDFs Wednesday/Thursday mornings automatically.
Phase 3: Direct API relationships replace PDF parsing where available.

Update this file when new stores are added or flyer URLs change.
"""

CHARLOTTESVILLE_STORES: list[dict] = [
    # ── API-backed (automatic) ─────────────────────────────────────────────────
    {
        "chain":       "Kroger",
        "location":    "Barracks Rd",
        "flyer_url":   None,
        "method":      "kroger_api",
        "tier":        "full_service",
        "notes":       "Live API. Pull automatically from Grocer Hub.",
        "flyer_day":   None,
    },
    {
        "chain":       "Harris Teeter",
        "location":    "Barracks Rd",
        "flyer_url":   "https://www.harristeeter.com/savings/weekly-ad",
        "method":      "pdf",
        "tier":        "full_service",
        "notes":       "Owned by Kroger — test Kroger API with HT location ID first. "
                       "PDF fallback: download from harristeeter.com/savings/weekly-ad",
        "flyer_day":   "Wednesday",
    },

    # ── PDF circulars (manual download, weekly) ────────────────────────────────
    {
        "chain":       "Food Lion",
        "location":    "Pantops Mountain",
        "flyer_url":   "https://www.foodlion.com/weekly-specials/",
        "method":      "pdf",
        "tier":        "full_service",
        "notes":       "Download PDF from foodlion.com/weekly-specials. "
                       "New circular posts Wednesday or Thursday.",
        "flyer_day":   "Wednesday",
    },
    {
        "chain":       "Aldi",
        "location":    "Rio Rd",
        "flyer_url":   "https://www.aldi.us/en/weekly-specials/",
        "method":      "pdf",
        "tier":        "value_discount",
        "notes":       "New circular posts every Wednesday. "
                       "Download PDF from aldi.us/en/weekly-specials.",
        "flyer_day":   "Wednesday",
    },
    {
        "chain":       "Giant Food",
        "location":    "Charlottesville",
        "flyer_url":   "https://giantfood.com/weekly-sales-ads/",
        "method":      "pdf",
        "tier":        "full_service",
        "notes":       "Download from giantfood.com/weekly-sales-ads. "
                       "Select Charlottesville store before downloading.",
        "flyer_day":   "Friday",
    },
    {
        "chain":       "Walmart",
        "location":    "Charlottesville",
        "flyer_url":   "https://www.walmart.com/store/2272/weekly-ad",
        "method":      "pdf",
        "tier":        "value_discount",
        "notes":       "Download weekly rollback ad from walmart.com/store/2272/weekly-ad.",
        "flyer_day":   "Friday",
    },
    {
        "chain":       "Wegmans",
        "location":    "Charlottesville",
        "flyer_url":   "https://www.wegmans.com/savings/weekly-specials/",
        "method":      "pdf",
        "tier":        "full_service",
        "notes":       "Download from wegmans.com/savings/weekly-specials. "
                       "Select Charlottesville store.",
        "flyer_day":   "Sunday",
    },
    {
        "chain":       "Whole Foods",
        "location":    "Charlottesville",
        "flyer_url":   "https://www.wholefoodsmarket.com/sales-flyer",
        "method":      "pdf",
        "tier":        "specialty",
        "notes":       "Download from wholefoodsmarket.com/sales-flyer. "
                       "Prime member deals are separate — grab both if relevant.",
        "flyer_day":   "Wednesday",
    },
    {
        "chain":       "Trader Joe's",
        "location":    "Charlottesville",
        "flyer_url":   "https://www.traderjoes.com/home/products/new-items",
        "method":      "manual",
        "tier":        "specialty",
        "notes":       "TJ's does not publish a weekly circular or sale prices. "
                       "Prices are everyday low — enter manually for relevant staples.",
        "flyer_day":   None,
    },

    # ── Local / Independent ────────────────────────────────────────────────────
    {
        "chain":       "EW Thomas",
        "location":    "Waynesboro",
        "flyer_url":   None,
        "method":      "manual",
        "tier":        "local",
        "notes":       "Local independent. No digital circular. Manual entry only.",
        "flyer_day":   None,
    },
    {
        "chain":       "Foods of All Nations",
        "location":    "Charlottesville",
        "flyer_url":   None,
        "method":      "manual",
        "tier":        "local",
        "notes":       "Local specialty. No digital circular. Manual entry only.",
        "flyer_day":   None,
    },
]

# Quick lookup by chain name
STORE_BY_CHAIN: dict[str, dict] = {s["chain"]: s for s in CHARLOTTESVILLE_STORES}

# Stores with PDF circulars (Tim downloads weekly)
PDF_STORES: list[dict] = [s for s in CHARLOTTESVILLE_STORES if s["method"] == "pdf"]

# Wednesday-refresh stores (Aldi, Food Lion, Harris Tee