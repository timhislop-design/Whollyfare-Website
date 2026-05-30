"""
store_directory.py -- WhollyFare multi-metro store directory.

Covers every market where WhollyFare runs a pilot household.
Structured as METRO_STORES dict keyed by metro slug (e.g. "charlottesville_va").
Each store entry has: chain, location, flyer_url, method, tier, notes, flyer_day.

method values:
  "kroger_api"  -- pulled via Kroger Developer API (automatic, same credentials)
  "pdf"         -- Tim downloads PDF from store website and uploads via Admin page
  "manual"      -- no digital circular; enter items by hand

Adding a new pilot market:
  1. Look up the Kroger banner location ID: KrogerClient().find_stores(zip_code="XXXXX")
  2. Add an entry to METRO_STORES with the banner chain name + location_id in notes.
  3. List the PDF stores in the market (Aldi, Walmart, regional chains).
  4. Admin page market selector automatically picks up new metros.

Kroger banner API note:
  All banners (Kroger, Harris Teeter, King Soopers, Ralphs, Fred Meyer, Smiths,
  Frys, Marianos, Pick n Save, Bakers, QFC, City Market, Dillons) use the
  SAME client_id / client_secret. Only the location_id differs.
  Phase 3: Kroger Cart API (Authorization Code flow) enables one-click delivery.
  Same API credentials -- user authenticates their Kroger account once.

Backward-compatible exports (used by Admin, Plan, state.py -- do not rename):
  CHARLOTTESVILLE_STORES, PDF_STORES, STORE_BY_CHAIN, WEDNESDAY_STORES
"""

from __future__ import annotations


# -- Kroger banner map --------------------------------------------------------
# All banners use the same Kroger Developer API credentials.
# One API key covers the entire Kroger family -- 2,800+ stores nationwide.
# Phase 3: Kroger Cart API enables direct delivery from WhollyFare plan.

KROGER_BANNERS: dict[str, dict] = {
    "Kroger":           {"region": "Southeast / Midwest / South",  "states": "VA,GA,TN,OH,KY,IN,MI,WI,TX,MS,LA,AR", "api_chain": "Kroger"},
    "Harris Teeter":    {"region": "Mid-Atlantic / Southeast",     "states": "VA,NC,SC,MD,DC,FL,GA,DE",             "api_chain": "Harris Teeter"},
    "King Soopers":     {"region": "Mountain West",                "states": "CO,WY",                               "api_chain": "King Soopers"},
    "Ralphs":           {"region": "Southern California",          "states": "CA",                                  "api_chain": "Ralphs"},
    "Fred Meyer":       {"region": "Pacific Northwest",            "states": "OR,WA,ID,AK",                         "api_chain": "Fred Meyer"},
    "Smiths":           {"region": "Mountain Southwest",           "states": "NV,NM,UT,AZ,WY,MT,ID",               "api_chain": "Smiths"},
    "Frys":             {"region": "Arizona",                      "states": "AZ",                                  "api_chain": "Frys"},
    "Marianos":         {"region": "Chicago metro",                "states": "IL",                                  "api_chain": "Marianos"},
    "Pick n Save":      {"region": "Wisconsin",                    "states": "WI",                                  "api_chain": "PickNSave"},
    "Bakers":           {"region": "Nebraska",                     "states": "NE",                                  "api_chain": "Bakers"},
    "QFC":              {"region": "Pacific Northwest",            "states": "WA,OR",                               "api_chain": "QFC"},
    "City Market":      {"region": "Mountain West",                "states": "CO,UT,WY",                            "api_chain": "CityMarket"},
    "Dillons":          {"region": "Kansas",                       "states": "KS",                                  "api_chain": "Dillons"},
    "Jay C":            {"region": "Indiana",                      "states": "IN",                                  "api_chain": "JayC"},
    "Ruler Foods":      {"region": "Midwest (discount)",           "states": "IN,IL,KY,OH",                         "api_chain": "Ruler"},
}


# -- Metro store lists --------------------------------------------------------
# Each key is a unique metro slug used in Admin + Grocer Hub.
# Kroger banners: location_id in notes -- update via find_stores() per market.

METRO_STORES: dict[str, list[dict]] = {

    # Charlottesville, VA (Pilot market 1 -- active)
    "charlottesville_va": [
        {
            "chain":       "Kroger",
            "location":    "Barracks Rd",
            "location_id": "01200441",
            "flyer_url":   None,
            "method":      "kroger_api",
            "tier":        "full_service",
            "notes":       "Kroger banner. Pull via Admin page (Kroger API tab). "
                           "Location ID 01200441 = Barracks Rd, Charlottesville VA.",
            "flyer_day":   None,
        },
        {
            "chain":       "Harris Teeter",
            "location":    "Barracks Rd",
            "location_id": None,
            "flyer_url":   "https://www.harristeeter.com/savings/weekly-ad",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Kroger-owned banner. Could also pull via Kroger API "
                           "(find HT location_id with find_stores('22901')). "
                           "PDF fallback: harristeeter.com/savings/weekly-ad",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Food Lion",
            "location":    "Pantops Mountain",
            "location_id": None,
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
            "location_id": None,
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
            "location_id": None,
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
            "location_id": None,
            "flyer_url":   "https://www.walmart.com/store/2272/weekly-ad",
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "Download weekly rollback ad from walmart.com/store/2272/weekly-ad.",
            "flyer_day":   "Friday",
        },
        {
            "chain":       "Wegmans",
            "location":    "Charlottesville",
            "location_id": None,
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
            "location_id": None,
            "flyer_url":   "https://www.wholefoodsmarket.com/sales-flyer",
            "method":      "pdf",
            "tier":        "specialty",
            "notes":       "Download from wholefoodsmarket.com/sales-flyer. "
                           "Prime member deals separate -- grab both if relevant.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Trader Joes",
            "location":    "Charlottesville",
            "location_id": None,
            "flyer_url":   "https://www.traderjoes.com/home/products/new-items",
            "method":      "manual",
            "tier":        "specialty",
            "notes":       "No weekly circular. Everyday low prices. "
                           "Manual entry for staples.",
            "flyer_day":   None,
        },
        {
            "chain":       "EW Thomas",
            "location":    "Waynesboro",
            "location_id": None,
            "flyer_url":   None,
            "method":      "manual",
            "tier":        "local",
            "notes":       "Local independent. No digital circular. Manual entry only.",
            "flyer_day":   None,
        },
        {
            "chain":       "Foods of All Nations",
            "location":    "Charlottesville",
            "location_id": None,
            "flyer_url":   None,
            "method":      "manual",
            "tier":        "local",
            "notes":       "Local specialty. No digital circular. Manual entry only.",
            "flyer_day":   None,
        },
    ],

    # Charlotte, NC (Pilot market 2 -- planned)
    # Harris Teeter is the dominant Kroger banner here.
    # Run find_stores("28202") to get the right HT location ID.
    "charlotte_nc": [
        {
            "chain":       "Harris Teeter",
            "location":    "Charlotte (TBD)",
            "location_id": None,
            "flyer_url":   "https://www.harristeeter.com/savings/weekly-ad",
            "method":      "kroger_api",
            "tier":        "full_service",
            "notes":       "Kroger banner (Harris Teeter). Pull via Kroger API. "
                           "Run KrogerClient().find_stores('28202') to get location_id.",
            "flyer_day":   None,
        },
        {
            "chain":       "Food Lion",
            "location":    "Charlotte",
            "location_id": None,
            "flyer_url":   "https://www.foodlion.com/weekly-specials/",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Strong Charlotte presence. foodlion.com/weekly-specials.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Publix",
            "location":    "Charlotte",
            "location_id": None,
            "flyer_url":   "https://www.publix.com/savings/weekly-ad",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Dominant Southeast grocer. publix.com/savings/weekly-ad.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Aldi",
            "location":    "Charlotte",
            "location_id": None,
            "flyer_url":   "https://www.aldi.us/en/weekly-specials/",
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "National chain. Same PDF URL, same Wednesday circular.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Walmart",
            "location":    "Charlotte",
            "location_id": None,
            "flyer_url":   None,
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "walmart.com/store/[STORE_NUMBER]/weekly-ad "
                           "-- pilot household confirms their store number.",
            "flyer_day":   "Friday",
        },
    ],

    # Denver, CO (Pilot market 3 -- planned)
    # King Soopers is the dominant Kroger banner (Mountain West).
    # Run find_stores("80202") to get the right KS location ID.
    "denver_co": [
        {
            "chain":       "King Soopers",
            "location":    "Denver (TBD)",
            "location_id": None,
            "flyer_url":   None,
            "method":      "kroger_api",
            "tier":        "full_service",
            "notes":       "Kroger banner (King Soopers). Same API credentials as Kroger. "
                           "Run KrogerClient().find_stores('80202') to get location_id.",
            "flyer_day":   None,
        },
        {
            "chain":       "Safeway",
            "location":    "Denver",
            "location_id": None,
            "flyer_url":   "https://www.safeway.com/weeklyad",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Albertsons-owned. Strong Denver presence. safeway.com/weeklyad.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Aldi",
            "location":    "Denver",
            "location_id": None,
            "flyer_url":   "https://www.aldi.us/en/weekly-specials/",
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "National chain. Same PDF URL, same Wednesday circular.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Whole Foods",
            "location":    "Denver",
            "location_id": None,
            "flyer_url":   "https://www.wholefoodsmarket.com/sales-flyer",
            "method":      "pdf",
            "tier":        "specialty",
            "notes":       "Strong Denver presence. Same national flyer URL.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Walmart",
            "location":    "Denver",
            "location_id": None,
            "flyer_url":   None,
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "walmart.com/store/[STORE_NUMBER]/weekly-ad.",
            "flyer_day":   "Friday",
        },
    ],

    # Chicago, IL (Pilot market 4 -- future)
    # Marianos is the Kroger banner in Chicago (acquired 2015).
    # Run find_stores("60601") to get the right Marianos location ID.
    "chicago_il": [
        {
            "chain":       "Marianos",
            "location":    "Chicago (TBD)",
            "location_id": None,
            "flyer_url":   None,
            "method":      "kroger_api",
            "tier":        "full_service",
            "notes":       "Kroger banner (Marianos). Same API credentials as Kroger. "
                           "Run KrogerClient().find_stores('60601') to get location_id.",
            "flyer_day":   None,
        },
        {
            "chain":       "Jewel-Osco",
            "location":    "Chicago",
            "location_id": None,
            "flyer_url":   "https://www.jewelosco.com/weeklyad",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Albertsons-owned. Dominant Chicago grocer. jewelosco.com/weeklyad.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Aldi",
            "location":    "Chicago",
            "location_id": None,
            "flyer_url":   "https://www.aldi.us/en/weekly-specials/",
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "National chain. Same PDF URL, same Wednesday circular.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Walmart",
            "location":    "Chicago",
            "location_id": None,
            "flyer_url":   None,
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "walmart.com/store/[STORE_NUMBER]/weekly-ad.",
            "flyer_day":   "Friday",
        },
    ],

    # Los Angeles, CA (Pilot market 5 -- future)
    # Ralphs is the Kroger banner in Southern California.
    # Run find_stores("90001") to get the right Ralphs location ID.
    "los_angeles_ca": [
        {
            "chain":       "Ralphs",
            "location":    "Los Angeles (TBD)",
            "location_id": None,
            "flyer_url":   None,
            "method":      "kroger_api",
            "tier":        "full_service",
            "notes":       "Kroger banner (Ralphs). Same API credentials as Kroger. "
                           "Run KrogerClient().find_stores('90001') to get location_id.",
            "flyer_day":   None,
        },
        {
            "chain":       "Vons",
            "location":    "Los Angeles",
            "location_id": None,
            "flyer_url":   "https://www.vons.com/weeklyad",
            "method":      "pdf",
            "tier":        "full_service",
            "notes":       "Albertsons-owned. Strong LA presence. vons.com/weeklyad.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Trader Joes",
            "location":    "Los Angeles",
            "location_id": None,
            "flyer_url":   "https://www.traderjoes.com/home/products/new-items",
            "method":      "manual",
            "tier":        "specialty",
            "notes":       "No weekly circular. Manual entry for staples.",
            "flyer_day":   None,
        },
        {
            "chain":       "Aldi",
            "location":    "Los Angeles",
            "location_id": None,
            "flyer_url":   "https://www.aldi.us/en/weekly-specials/",
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "National chain. Same PDF URL, same Wednesday circular.",
            "flyer_day":   "Wednesday",
        },
        {
            "chain":       "Walmart",
            "location":    "Los Angeles",
            "location_id": None,
            "flyer_url":   None,
            "method":      "pdf",
            "tier":        "value_discount",
            "notes":       "walmart.com/store/[STORE_NUMBER]/weekly-ad.",
            "flyer_day":   "Friday",
        },
    ],
}


# -- Helper functions ---------------------------------------------------------

def get_stores_for_metro(metro_slug: str) -> list[dict]:
    """Return store list for a metro slug. Empty list if slug not found."""
    return METRO_STORES.get(metro_slug, [])


def get_kroger_store_for_metro(metro_slug: str) -> dict | None:
    """Return the Kroger-API-backed store entry for a metro, or None."""
    for s in METRO_STORES.get(metro_slug, []):
        if s.get("method") == "kroger_api":
            return s
    return None


def get_kroger_banner_for_state(state_abbr: str) -> str:
    """Best-guess Kroger banner chain name for a US state abbreviation."""
    for banner, info in KROGER_BANNERS.items():
        if state_abbr.upper() in info["states"].split(","):
            return banner
    return "Kroger"  # default for unlisted states


def get_all_metro_slugs() -> list[str]:
    """Return all configured metro slugs in METRO_STORES."""
    return list(METRO_STORES.keys())


def get_metro_label(metro_slug: str) -> str:
    """Human-readable label for a metro slug."""
    _labels = {
        "charlottesville_va": "Charlottesville, VA",
        "charlotte_nc":       "Charlotte, NC",
        "denver_co":          "Denver, CO",
        "chicago_il":         "Chicago, IL",
        "los_angeles_ca":     "Los Angeles, CA",
    }
    return _labels.get(metro_slug, metro_slug.replace("_", " ").title())


# -- Flat union of all metro stores -------------------------------------------
# Used for STORE_BY_CHAIN -- same chain appears in multiple metros but
# the metadata (method, flyer_day, tier) is the same everywhere.

ALL_STORES: list[dict] = [
    store
    for stores in METRO_STORES.values()
    for store in stores
]


# -- Backward-compatible exports -----------------------------------------------
# These names are imported by Admin (11_Admin.py), Plan (3_Plan.py), state.py.
# Do NOT rename them.

# Primary pilot market -- used by Admin page for its PDF store selector
CHARLOTTESVILLE_STORES: list[dict] = METRO_STORES["charlottesville_va"]

# PDF stores in Charlottesville market (Admin page default list)
PDF_STORES: list[dict] = [s for s in CHARLOTTESVILLE_STORES if s["method"] == "pdf"]

# Wednesday-refresh stores in Charlottesville (used in Admin UI day labels)
WEDNESDAY_STORES: list[dict] = [
    s for s in CHARLOTTESVILLE_STORES if s.get("flyer_day") == "Wednesday"
]

# Chain name -> store dict for metadata lookups (method, flyer_day, tier, notes).
# Covers ALL metros so Plan + state can resolve any pilot market chain by name.
# For chains in multiple metros, first occurrence wins (metadata identical).
STORE_BY_CHAIN: dict[str, dict] = {}
for _s in ALL_STORES:
    if _s["chain"] not in STORE_BY_CHAIN:
        STORE_BY_CHAIN[_s["chain"]] = _s
