"""
2_Grocer_Hub.py — Grocer Data Hub
===================================
Weekly price data entry for all configured stores.

Store selection is a first-class onboarding moment: four tiers (Value,
Full-Service, Specialty, Local) so every household — from SNAP-budget
families to organic-only shoppers — finds their stores immediately.

Data paths (in order of POC reliability):
  1. Manual item entry  — type items in directly; always works
  2. PDF upload         — parse sale circulars; heuristic, review required
  3. Kroger API         — live pull when credentials are available

POC vs. PRODUCTION
-------------------
POC:  Data lives in Streamlit session_state. Cleared on browser refresh.
PROD: Items persist to PostgreSQL. PDF parsing runs in a background worker.
      Store selection persists to user profile; zip-code resolver suggests
      nearby stores automatically (Kroger Locations API + Google Places).
"""

import sys
import datetime
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

from app.data.flyer_ingestor import FlyerIngestor
from app.core_logic.constraint_engine import IngredientCandidate
from app.data.store_regions import chains_for_zip, region_label, CHARLOTTESVILLE_CHAINS
from app.data.store_locations import stores_near_zip, zip_centroid, trip_cost_estimate

# POC: folium + streamlit-folium optional — map degrades gracefully if not installed.
# Install: pip install folium streamlit-folium
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

st.set_page_config(page_title="Grocer Hub · WhollyFare", page_icon="🏪", layout="wide")
state.init()

# ── Ensure household_id is hydrated ──────────────────────────────────────────
# save_grocers() requires household_id to be in session_state. It gets set in
# sign_in() → _load_household_from_db(), but if the user navigates directly here
# (e.g. via sidebar) without going through Household Setup, household_id might
# not yet be set. Load it once at page load so Save Store Profile always works.
# POC: cheap single-row read; always runs when authenticated.
# PROD: add TTL cache so this doesn't run on every re-render.
if state.is_authenticated():
    if state._jwt_is_expired():
        state.refresh_session()
    if not st.session_state.get("household_id"):
        state.load_household()

if "manual_items" not in st.session_state:
    st.session_state["manual_items"] = []

with st.sidebar:
    style.sidebar_nav()
    st.html("<hr style='border-color:#3A8C4E;margin:10px 0;'>")
    grocers = st.session_state.get("grocers", [])
    if grocers:
        st.html("<div style='font-size:0.7rem;font-weight:700;color:#9FD9A8;"
                "letter-spacing:0.08em;margin-bottom:6px;'>YOUR STORES</div>")
        for g in grocers:
            src    = g.get("source", "manual")
            icon   = "🔗" if "api" in src else "📄"
            star   = " ⭐" if g.get("is_primary") else ""
            tier_c = {"discount": "#F28B30", "mainstream": "#9FD9A8",
                      "specialty": "#81C784", "local": "#FFCC80"}.get(g.get("tier",""), "#9FD9A8")
            st.html(f"<div style='font-size:0.82rem;color:#e8f5ec;padding:2px 0;'>"
                    f"<span style='color:{tier_c};'>{icon}</span> {g.get('chain','?')}{star}</div>")

style.page_header(
    "Grocer Hub",
    "Set up your store profile — the stores you shop at, saved permanently so you never have to pick them again.",
)

# ── Progress stepper ──────────────────────────────────────────────────────────
st.html("""
<div style='display:flex;align-items:center;gap:0;margin-bottom:22px;'>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;'>✓</div>
  <div style='height:2px;width:40px;background:#3A8C4E;'></div>
  <div style='background:#3A8C4E;color:white;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;'>2</div>
  <div style='height:2px;width:40px;background:#D8EDD0;'></div>
  <div style='background:#D8EDD0;color:#5A7A62;border-radius:50%;width:28px;height:28px;
              display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;'>3</div>
  <div style='margin-left:12px;font-size:0.82rem;color:#5A7A62;'>
    Household → <strong style='color:#1E5C32;'>Grocer Prices</strong> → Generate Plan
  </div>
</div>
""")


# ══════════════════════════════════════════════════════════════════════════════
# STORE TIER REGISTRY
#
# Four tiers reflecting how real households actually shop:
#   1. Value & Discount  — ALDI, Walmart, Lidl, Dollar General
#   2. Full-Service      — Kroger, Food Lion, Harris Teeter, Wegmans
#   3. Specialty         — Whole Foods, Trader Joe's, Sprouts, Fresh Market
#   4. Local & Regional  — EW Thomas, Foods of All Nations, independent markets
#
# POC: Static list. The "local" tier is pre-seeded for the Charlottesville
#      pilot area plus a free-entry form for any chain we haven't listed.
# PROD: Store registry backed by a DB table (chain_id, tier, name, logo_url,
#       api_available, pdf_parser_quality, regional_states[]). User's zip
#       resolves to nearby stores automatically; unknown chains go into a
#       "community-submitted" queue for parser dev prioritisation.
# ══════════════════════════════════════════════════════════════════════════════

# circular_support levels — used to show badges and control PDF tab behaviour:
#   "api"         — live API pull (structured data, best quality)
#   "pdf_text"    — text-extractable PDF circular (good, parser handles well)
#   "pdf_image"   — image-based PDF (OCR fallback, incomplete results expected)
#   "manual_only" — no machine-readable circular; enter prices manually
STORE_TIERS = [
    {
        "key":     "discount",
        "label":   "Value & Discount",
        "icon":    "💰",
        "tagline": "Deepest per-unit prices on staples. ALDI and Lidl in particular consistently beat full-service chains on produce and dairy. These are your savings anchors.",
        "color":   "#BF5E00",
        "bg":      "#FFF8F0",
        "border":  "#FFCC80",
        "pill_bg": "#FFF3E0",
        "stores": [
            {"chain": "ALDI",           "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_image",
             "flyer": "https://www.aldi.us/en/weekly-specials/",
             "note": "No loyalty card. Weekly Specialbuys are image-based — upload the PDF and review results carefully, or enter key items manually."},
            {"chain": "Lidl",           "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_image",
             "flyer": "https://www.lidl.com/en/weekly-specials",
             "note": "Image-based circular similar to ALDI. PDF upload works via OCR — results vary. Manual entry for key items is more reliable."},
            {"chain": "Walmart",        "source": "manual",  "rewards": False, "delivery": True,
             "circular_support": "manual_only",
             "flyer": "https://www.walmart.com/store/finder",
             "note": "No structured weekly circular. Rollback prices change continuously. Add items manually from the Walmart app or website."},
            {"chain": "Dollar General", "source": "manual",  "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.dollargeneral.com/weekly-ad",
             "note": "Strong on canned goods, pasta, and pantry staples. Text-based weekly ad parses well."},
            {"chain": "Dollar Tree",    "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_image",
             "flyer": "https://www.dollartree.com/deals",
             "note": "$1.25 flat pricing. Ad is image-heavy — PDF upload via OCR, or enter a few key items manually."},
            {"chain": "WinCo Foods",    "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.wincofoods.com/weekly-ad",
             "note": "Employee-owned. Consistently lowest prices in markets where it operates. Text circular parses well."},
            {"chain": "Save-A-Lot",     "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.savealot.com/savings/weekly-ad",
             "note": "Deep-discount regional chain. Strong in Southeast and Midwest. Standard text circular."},
            {"chain": "Food 4 Less",    "source": "manual",  "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.food4less.com/weeklyad",
             "note": "Kroger warehouse banner. No-frills pricing, full selection. Text circular parses well."},
        ],
    },
    {
        "key":     "mainstream",
        "label":   "Full-Service Grocers",
        "icon":    "🏪",
        "tagline": "Your regular weekly shop. Loyalty cards, digital coupons, and consistent weekly ads make these the backbone of most WhollyFare plans. The more you add, the more we can route across them.",
        "color":   "#1E5C32",
        "bg":      "#F0FAF2",
        "border":  "#D8EDD0",
        "pill_bg": "#E3F4E8",
        "stores": [
            {"chain": "Kroger",         "source": "api", "rewards": True,  "delivery": True,
             "circular_support": "api",
             "flyer": "https://www.kroger.com/weeklyad",
             # POC: location hardcoded for Charlottesville pilot (Barracks Rd store).
             # PROD: resolved from household zip via Kroger Locations API.
             "location": "02900359",
             "note": "Live API connected — WhollyFare pulls current prices automatically. Loyalty card unlocks stacked digital coupons."},
            {"chain": "Food Lion",      "source": "manual",     "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://stores.foodlion.com",
             "note": "MVP Card deals often beat Kroger on produce. Dedicated parser — PDF circular imports cleanly."},
            {"chain": "Harris Teeter",  "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.harristeeter.com/weeklyad",
             "note": "VIC card + e-VIC digital coupons. Text-based circular parses reliably. Super Double coupon events quarterly."},
            {"chain": "Giant Food",     "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://stores.giantfood.com",
             "note": "Giant Card + Gas Rewards. Mid-Atlantic staple. Text circular parses well."},
            {"chain": "Wegmans",        "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.wegmans.com/weeklyad",
             "note": "Club card + app coupons. Known for quality and store-brand price. Text circular parses reliably."},
            {"chain": "Publix",         "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.publix.com/savings/weekly-ad",
             "note": "BOGO deals are a Publix signature. Well-structured text circular — one of the best-parsing PDFs."},
            {"chain": "Safeway",        "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.safeway.com/weeklyad",
             "note": "Just for U digital coupons stack on Club Card pricing. Text circular parses well."},
            {"chain": "Albertsons",     "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.albertsons.com/weeklyad",
             "note": "Same ownership as Safeway. Strong BOGO weeks. Text circular parses reliably."},
            {"chain": "Meijer",         "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.meijer.com/shopping/weekly-deals.html",
             "note": "Midwest supercenter. mPerks digital coupons stack on weekly sales. Text circular."},
            {"chain": "Hy-Vee",         "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.hy-vee.com/weekly-deals/",
             "note": "Employee-owned Midwest chain. Fuel Saver + Perks program. Text circular parses well."},
            {"chain": "Stop & Shop",    "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://stopandshop.com/weeklyCircular/",
             "note": "Gas Points program. Northeast regional staple. Standard text circular."},
            {"chain": "ShopRite",       "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.shoprite.com/sm/planning/rsid/5002/weekly-specials",
             "note": "Price Plus card. Can-Can Sale in January is legendary. Text circular parses well."},
            {"chain": "Giant Eagle",    "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.gianteagle.com/save/weekly-circular",
             "note": "fuelperks+ program. Strong in Ohio, Pennsylvania, West Virginia. Text circular."},
            {"chain": "H-E-B",          "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.heb.com/static-page/weekly-ad",
             "note": "Texas institution. H-E-B Combo deals are a local savings fixture. Text circular parses well."},
            {"chain": "Weis Markets",   "source": "manual",     "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.weismarkets.com/weeklyad",
             "note": "Mid-Atlantic regional. Weis Club card + digital deals. Text circular."},
            {"chain": "Ingles Markets", "source": "manual",     "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.ingles-markets.com/weeklyad",
             "note": "Southeast regional. Advantage Card savings + gas discounts. Text circular parses well."},
        ],
    },
    {
        "key":     "specialty",
        "label":   "Specialty & Natural",
        "icon":    "🌿",
        "tagline": "Premium, organic, and specialty options. Worth checking for their sale weeks — Whole Foods 365 brand and Trader Joe's store brand often match mainstream prices on key items.",
        "color":   "#1565C0",
        "bg":      "#EEF4FB",
        "border":  "#BBDEFB",
        "pill_bg": "#E3F2FD",
        "stores": [
            {"chain": "Whole Foods",    "source": "manual",  "rewards": True,  "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.wholefoodsmarket.com/sales-flyer",
             "note": "Prime members get extra 10% off sale items. 365 brand is price-competitive. Text-based sales flyer parses well."},
            {"chain": "Trader Joe's",   "source": "manual",  "rewards": False, "delivery": False,
             "circular_support": "pdf_image",
             "flyer": "https://www.traderjoes.com/home/fearless-flyer",
             "note": "No weekly sale cycle — Fearless Flyer runs monthly and is magazine-style (image-based). Stable everyday pricing; manual entry is more reliable than PDF upload."},
            {"chain": "Sprouts",        "source": "manual",  "rewards": False, "delivery": True,
             "circular_support": "pdf_text",
             "flyer": "https://www.sprouts.com/deals/weekly-ad/",
             "note": "Produce-forward. Double Ad Wednesdays overlap two sale weeks. Text circular parses well."},
            {"chain": "The Fresh Market","source": "manual",  "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.thefreshmarket.com/weekly-specials",
             "note": "Premium meats and produce. Weekly specials often include protein deals. Text circular."},
            {"chain": "Earth Fare",     "source": "manual",  "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.earthfare.com/deals/",
             "note": "No artificial ingredients policy. Regional natural chain, Southeast focus. Text circular."},
            {"chain": "Natural Grocers","source": "manual",  "rewards": True,  "delivery": False,
             "circular_support": "pdf_text",
             "flyer": "https://www.naturalgrocers.com/weekly-ad",
             "note": "100% organic produce, always. {N}power card unlocks member pricing. Text circular parses well."},
        ],
    },
    {
        "key":     "local",
        "label":   "Local & Independent",
        "icon":    "📍",
        "tagline": "Your community stores — the ones your neighbors shop at, that know your town, and run deals you won't find in a national app. This is what makes your plan yours.",
        "color":   "#5D4037",
        "bg":      "#FBF8F5",
        "border":  "#D7CCC8",
        "pill_bg": "#EFEBE9",
        "stores": [
            # Charlottesville / Palmyra VA pilot area — pre-seeded for Tim's household
            {"chain": "EW Thomas Grocery",        "source": "manual", "rewards": False, "delivery": False,
             "circular_support": "manual_only",
             "flyer": "",
             "note": "Palmyra, VA. Local institution — meat counter, produce, and weekly specials."},
            {"chain": "Foods of All Nations",     "source": "manual", "rewards": False, "delivery": False,
             "circular_support": "manual_only",
             "flyer": "",
             "note": "Charlottesville, VA. International specialty market. Unique ingredients, fair prices."},
            {"chain": "Integral Yoga Natural",    "source": "manual", "rewards": False, "delivery": False,
             "circular_support": "manual_only",
             "flyer": "",
             "note": "Charlottesville, VA. Natural and organic co-op. Bulk bins, local produce."},
            {"chain": "The Fresh Marketplace",    "source": "manual", "rewards": False, "delivery": False,
             "circular_support": "manual_only",
             "flyer": "",
             "note": "Charlottesville, VA area. Check locally for current weekly specials."},
            {"chain": "Reid's Country Store",     "source": "manual", "rewards": False, "delivery": False,
             "circular_support": "manual_only",
             "flyer": "",
             "note": "Local farm-country store. Seasonal produce, local meats, unbeatable eggs."},
        ],
    },
]

# Build lookup maps
CHAIN_FLYER_URLS: dict[str, str] = {}
CHAIN_TIER:       dict[str, str] = {}
CHAIN_NOTES:      dict[str, str] = {}
CHAIN_DATA:       dict[str, dict] = {}
for tier in STORE_TIERS:
    for s in tier["stores"]:
        key = s["chain"].lower()
        CHAIN_FLYER_URLS[key] = s.get("flyer", "")
        CHAIN_TIER[key]       = tier["key"]
        CHAIN_NOTES[key]      = s.get("note", "")
        CHAIN_DATA[key]       = {**s, "tier": tier["key"]}


# ══════════════════════════════════════════════════════════════════════════════
# STORE PROFILE WIZARD
# Sets up the household's store list: zip-aware discovery, travel radius,
# trip distance per store, and a folium map showing all nearby options.
#
# POC: Saves to session_state. PROD: Persists to user profile in Supabase.
# ══════════════════════════════════════════════════════════════════════════════
grocers = st.session_state.get("grocers", [])
existing_chains_lower = {g.get("chain", "").lower() for g in grocers}

# ── Resolve home zip and travel radius ───────────────────────────────────────
home_zip      = st.session_state.get("home_zip", "")
travel_radius = int(st.session_state.get("travel_radius_mi", 15))

# POC: Streamlit caches widget values by key name. If we use a fixed key like
# "wizard_zip_input", the browser returns the previously typed value on every rerun,
# ignoring the value= argument. The reliable fix is a dynamic key that changes
# whenever the household identity or saved zip changes — Streamlit treats it as a
# brand-new widget and initialises it from value= instead of the stale cache.
_db_zip   = (st.session_state.get("household_db") or {}).get("zip_code", "") or home_zip
_hh_id    = st.session_state.get("household_id", "new")
_wiz_zip_key = f"wizard_zip_{_hh_id}_{_db_zip}"

# nearby_chains: used by tier cards below to filter store lists by region.
# Always computed from confirmed store location data (not broad regional lookup)
# so tier cards only show chains that actually exist near the user's zip.
# POC: hardcoded store registry. PROD: real store-locator API.
_confirmed_nearby = stores_near_zip(home_zip or "22903", float(travel_radius))
nearby_chains = (
    {loc["chain"] for loc in _confirmed_nearby}
    if home_zip
    else {s["chain"] for t in STORE_TIERS for s in t["stores"]}
)

# Wizard state: show if no stores OR user clicked "Edit my stores"
_wizard_done = st.session_state.get("store_wizard_done", False) and bool(grocers)
_show_wizard = (not _wizard_done) or st.session_state.get("show_store_wizard", False)

# ── Debug expander (temp — always visible; remove before pilot launch) ───────
# Placed OUTSIDE the wizard block so it persists after Save triggers a rerun.
# After clicking Save, expand this to read last_grocer_save (OK vs FAILED).
import json as _json
_db_zip_debug   = (st.session_state.get("household_db") or {}).get("zip_code", "") or home_zip
_hh_id_debug    = st.session_state.get("household_id", "new")
_wiz_key_debug  = f"wizard_zip_{_hh_id_debug}_{_db_zip_debug}"
with st.expander("🔍 Debug: session state (remove before pilot)", expanded=False):
    _db_state = {
        "is_authenticated":      state.is_authenticated(),
        "household_id":          st.session_state.get("household_id"),
        "home_zip (session)":    st.session_state.get("home_zip"),
        "db_zip (household_db)": (st.session_state.get("household_db") or {}).get("zip_code"),
        "_wiz_zip_key":          _wiz_key_debug,
        "grocers (count)":       len(st.session_state.get("grocers", [])),
        "last_grocer_save":      st.session_state.get("_last_grocer_save_status", "not set"),
        "jwt_expired":           state._jwt_is_expired(),
    }
    st.code(_json.dumps(_db_state, indent=2, default=str))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WIZARD — shown on first visit or when editing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if _show_wizard:
    st.html("""
    <div style='background:linear-gradient(135deg,#E8F5E9,#F0FAF2);
                border:1px solid #D8EDD0;border-radius:14px;
                padding:22px 26px 18px;margin-bottom:20px;'>
      <div style='font-size:1.15rem;font-weight:800;color:#1E5C32;margin-bottom:6px;'>
        Your Store Profile
      </div>
      <div style='font-size:0.88rem;color:#3A8C4E;line-height:1.6;'>
        Choose the stores you shop at and how far you'll travel.
        This is saved to your profile — not something you redo each week.
        Add or remove stores any time from here or the Household page.
      </div>
    </div>""")

    # ── Zip + radius controls ─────────────────────────────────────────────────
    # Zip pre-populates from Household Setup profile. Changing it here only
    # affects this session — useful when traveling. It does NOT update the
    # household profile; go to Household Setup to change your home zip.
    _hh_zip = (st.session_state.get("household_db") or {}).get("zip_code", "")
    _zip_label = (
        "Your zip code (from household profile)"
        if _hh_zip
        else "Your zip code"
    )
    _zip_help = (
        "Pre-filled from your Household Setup. Change here to search stores near "
        "a different location — handy when traveling. This only affects your current "
        "session and won't update your household profile."
        if _hh_zip
        else "We use this to find stores near you and calculate trip costs."
    )
    wz_col1, wz_col2 = st.columns([1, 2])
    with wz_col1:
        w_zip = st.text_input(
            _zip_label,
            value=home_zip,
            key=_wiz_zip_key,
            placeholder="e.g. 22903",
            help=_zip_help,
        )
    with wz_col2:
        w_radius = st.slider(
            "How far are you willing to travel? (miles)",
            min_value=5, max_value=30, value=travel_radius, step=5,
            help="One-way distance. WhollyFare calculates round-trip gas cost per store.",
        )

    # Update session from wizard inputs (live, before Save)
    if w_zip != home_zip:
        st.session_state["home_zip"] = w_zip
        home_zip = w_zip
    if w_radius != travel_radius:
        st.session_state["travel_radius_mi"] = w_radius
        travel_radius = w_radius

    # ── Nearby stores ─────────────────────────────────────────────────────────
    # POC: store registry covers Charlottesville / Palmyra VA only.
    # PROD: Replace with Google Places API (Tim has prior experience with this)
    #       to return real stores with lat/lon + address for any US zip.
    effective_zip = home_zip if home_zip else "22903"
    nearby_stores = stores_near_zip(effective_zip, float(w_radius))
    nearby_chains = {loc["chain"] for loc in nearby_stores}

    # Fallback: if zip is outside our location registry, use regional chain list
    if not nearby_stores and home_zip:
        from app.data.store_regions import chains_for_zip as _cfz
        _regional = _cfz(home_zip)
        for _t in STORE_TIERS:
            for _s in _t["stores"]:
                if _s["chain"] in _regional:
                    nearby_stores.append({
                        "chain":          _s["chain"],
                        "location":       _s["chain"],
                        "address":        "",
                        "lat":            None,
                        "lon":            None,
                        "tier":           _t["key"],
                        "distance_miles": None,
                        "trip_cost":      None,
                        "api_live":       "api" in _s.get("source", ""),
                        "_fallback":      True,
                    })
        nearby_chains = {s["chain"] for s in nearby_stores}
        st.html(
            "<div style='background:#FFF8F0;border:1px solid #FFCC80;"
            "border-radius:8px;padding:12px 16px;font-size:0.83rem;"
            "color:#7A4A00;margin-bottom:12px;line-height:1.6;'>"
            "<strong>&#128205; Pilot area notice:</strong> Confirmed store "
            "locations and distances are available for Charlottesville / Palmyra VA. "
            "For your zip we're showing chains available in your region — "
            "<strong>enter your distance to each store manually</strong> and "
            "WhollyFare will calculate trip costs from there. "
            "Full location data via Google Places API is on the roadmap."
            "</div>"
        )

    _has_real_locs = any(not s.get("_fallback") for s in nearby_stores)
    centroid = zip_centroid(effective_zip)
    if centroid and FOLIUM_AVAILABLE and nearby_stores and _has_real_locs:
        tier_marker_colors = {
            "discount":   "orange",
            "mainstream": "green",
            "specialty":  "blue",
            "local":      "red",
        }
        m = folium.Map(location=list(centroid), zoom_start=12, tiles="OpenStreetMap")

        # Radius circle
        folium.Circle(
            location=list(centroid),
            radius=w_radius * 1609.34,   # miles → metres
            color="#3A8C4E",
            fill=True,
            fill_opacity=0.06,
            weight=2,
            dash_array="6 4",
            tooltip=f"{w_radius}-mile radius",
        ).add_to(m)

        # Home pin
        folium.Marker(
            location=list(centroid),
            tooltip="Your location",
            icon=folium.Icon(color="gray", icon="home", prefix="fa"),
        ).add_to(m)

        # Store markers
        for loc in nearby_stores:
            already = loc["chain"].lower() in existing_chains_lower
            mcolor  = tier_marker_colors.get(loc["tier"], "gray")
            dist_str = f"{loc['distance_miles']:.1f} mi" if loc["distance_miles"] else ""
            cost_str = f" · ~${loc['trip_cost']:.2f} round trip" if loc["trip_cost"] else ""
            popup_html = (
                f"<b>{loc['location']}</b><br>"
                f"{loc['address']}<br>"
                f"<span style='color:#3A8C4E'>{dist_str}{cost_str}</span>"
                + ("<br><b style='color:#1E5C32'>✓ In your store list</b>" if already else "")
            )
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                tooltip=f"{'✓ ' if already else ''}{loc['location']} ({dist_str})",
                popup=folium.Popup(popup_html, max_width=260),
                icon=folium.Icon(
                    color=mcolor if not already else "darkgreen",
                    icon="shopping-cart",
                    prefix="fa",
                ),
            ).add_to(m)

        st.html("<div style='font-size:0.75rem;color:#5A7A62;margin-bottom:6px;'>"
                "📍 Stores within your travel radius. Click any marker for details.</div>")
        st_folium(m, height=340, use_container_width=True, returned_objects=[])

    elif centroid and not FOLIUM_AVAILABLE:
        st.html("<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;"
                "padding:10px 14px;font-size:0.82rem;color:#BF5E00;margin-bottom:12px;'>"
                "🗺️ Install <code>folium</code> and <code>streamlit-folium</code> to see the store map. "
                "Run: <code>pip install folium streamlit-folium</code></div>")
    elif not centroid:
        st.html("<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;"
                "padding:10px 14px;font-size:0.82rem;color:#BF5E00;margin-bottom:12px;'>"
                "Enter your zip code above to see nearby stores on the map.</div>")

    # ── Store checkboxes ──────────────────────────────────────────────────────
    st.html("<div style='font-size:0.78rem;font-weight:700;color:#1E5C32;"
            "letter-spacing:0.08em;text-transform:uppercase;margin:16px 0 10px;'>"
            "Select your stores</div>")

    if not nearby_stores:
        st.html("<div style='font-size:0.84rem;color:#5A7A62;padding:10px 0;'>"
                "Enter a zip code above to see stores near you.</div>")
    elif nearby_stores:
        # Track wizard selections in temp state
        if "wizard_selections" not in st.session_state:
            st.session_state["wizard_selections"] = {
                g["chain"]: True for g in grocers
            }

        # Group by tier
        tier_order_wiz = ["discount", "mainstream", "specialty", "local"]
        tier_meta_wiz  = {
            "discount":   ("💰", "Value & Discount",     "#BF5E00", "#FFF8F0",  "#FFCC80"),
            "mainstream": ("🏪", "Full-Service Grocers", "#1E5C32", "#F0FAF2",  "#D8EDD0"),
            "specialty":  ("🌿", "Specialty & Natural",  "#1565C0", "#EEF4FB",  "#BBDEFB"),
            "local":      ("📍", "Local & Independent",  "#5D4037", "#FBF8F5",  "#D7CCC8"),
        }
        by_tier = {}
        for loc in nearby_stores:
            by_tier.setdefault(loc["tier"], []).append(loc)

        # Discovery callout: stores not yet in their list that are within radius
        new_discoveries = [
            loc for loc in nearby_stores
            if loc["chain"].lower() not in existing_chains_lower
        ]
        if new_discoveries and grocers:
            disc_names = ", ".join(loc["location"].split("—")[0].strip() for loc in new_discoveries[:3])
            st.html(f"""
            <div style='background:#E3F4E8;border:1px solid #A8D5B0;border-radius:8px;
                        padding:10px 14px;font-size:0.82rem;color:#1E4228;margin-bottom:12px;'>
              🔍 <strong>Stores near you you haven't added yet:</strong> {disc_names}
              {"and more" if len(new_discoveries) > 3 else ""} — check them below.
            </div>""")

        for tier_key in tier_order_wiz:
            if tier_key not in by_tier:
                continue
            icon, label, color, bg, border = tier_meta_wiz[tier_key]
            tier_locs = by_tier[tier_key]

            st.html(f"""
            <div style='font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                        text-transform:uppercase;color:{color};margin:12px 0 6px;
                        border-left:3px solid {color};padding-left:8px;'>
              {icon} {label}
            </div>""")

            n_cols = min(3, len(tier_locs))
            cols_wiz = st.columns(n_cols)
            for i, loc in enumerate(tier_locs):
                chain = loc["chain"]
                dist_str = f"{loc['distance_miles']:.1f} mi away" if loc["distance_miles"] is not None else ""
                cost_str = f"~${loc['trip_cost']:.2f} round trip" if loc["trip_cost"] else ""
                api_badge = " 🔗 API" if loc.get("api_live") else ""
                already   = chain.lower() in existing_chains_lower

                with cols_wiz[i % n_cols]:
                    # Support badge for wizard checkbox
                    _csupp = CHAIN_DATA.get(chain.lower(), {}).get("circular_support", "pdf_text")
                    _supp_badge_map = {
                        "api":         ("🔗", "#1E5C32", "Live API"),
                        "pdf_text":    ("📄", "#1565C0", "PDF supported"),
                        "pdf_image":   ("🖼️", "#BF5E00", "Image PDF — limited"),
                        "manual_only": ("✏️", "#5D4037", "Manual entry only"),
                    }
                    _si, _sc, _sl = _supp_badge_map.get(_csupp, ("📄", "#1565C0", "PDF supported"))
                    checked = st.checkbox(
                        f"**{chain}**",
                        value=st.session_state["wizard_selections"].get(chain, already),
                        key=f"wiz_check_{chain}",
                    )
                    st.session_state["wizard_selections"][chain] = checked
                    st.html(f"<div style='font-size:0.68rem;color:{_sc};margin:-4px 0 4px 0;'>"
                            f"{_si} {_sl}</div>")

                    if checked:
                        # Trip distance input for selected stores
                        default_dist = loc["distance_miles"] or 0.0
                        # Try to pull saved distance from existing grocers
                        for g in grocers:
                            if g["chain"] == chain and g.get("distance_miles"):
                                default_dist = g["distance_miles"]
                                break
                        trip_d = st.number_input(
                            "Miles from home",
                            min_value=0.0, max_value=100.0, step=0.5,
                            value=float(round(default_dist, 1)),
                            key=f"wiz_dist_{chain}",
                            help="One-way distance used to calculate round-trip gas cost.",
                        )
                        if cost_str:
                            actual_cost = trip_cost_estimate(trip_d)
                            st.html(f"<div style='font-size:0.72rem;color:#5A7A62;margin-bottom:4px;'>"
                                    f"{dist_str} · ~${actual_cost:.2f} round trip</div>")
                    else:
                        st.html(f"<div style='font-size:0.72rem;color:#9AA8A0;margin-bottom:6px;'>"
                                f"{dist_str}{(' · ' + cost_str) if cost_str else ''}{api_badge}</div>")

    # ── Add a store not on the list ──────────────────────────────────────────
    # Replaces the old tier-card "Add" buttons. Any store, co-op, or chain
    # not in the registry can be added here and staged for the profile save.
    # POC: manual entry only. PROD: verify against Google Places API.
    with st.expander("➕ My store isn't listed above", expanded=False):
        st.html("<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:10px;line-height:1.5;'>"
                "Add any store, co-op, farm stand, or chain not shown in the checkboxes above. "
                "It will appear in your profile and can receive manual price entries.</div>")
        _mc1, _mc2, _mc3 = st.columns([3, 2, 1])
        with _mc1:
            _manual_name = st.text_input(
                "Store name",
                placeholder="e.g. Blue Ridge Co-op, Murphy's Market",
                key="manual_store_name",
                label_visibility="collapsed",
            )
        with _mc2:
            _manual_loc = st.text_input(
                "Town / zip (optional)",
                placeholder="Crozet VA",
                key="manual_store_loc",
                label_visibility="collapsed",
            )
        with _mc3:
            _manual_dist = st.number_input(
                "Miles from home",
                min_value=0.0, max_value=100.0, step=0.5, value=0.0,
                key="manual_store_dist",
                help="One-way distance — used to calculate round-trip gas cost",
            )
        _mc4, _mc5, _mc6 = st.columns([2, 2, 2])
        with _mc4:
            _manual_tier = st.selectbox(
                "Store type",
                ["local", "discount", "mainstream", "specialty"],
                format_func=lambda x: {
                    "local": "📍 Local / Independent",
                    "discount": "💰 Value & Discount",
                    "mainstream": "🏪 Full-Service",
                    "specialty": "🌿 Specialty & Natural",
                }[x],
                key="manual_store_tier",
            )
        with _mc5:
            _manual_rewards = st.checkbox("Has loyalty / rewards card", key="manual_store_rewards")
        with _mc6:
            _manual_delivery = st.checkbox("Offers delivery", key="manual_store_delivery")
        if st.button("Stage this store", key="add_manual_store", type="primary"):
            if _manual_name.strip():
                _pending_m = st.session_state.setdefault("_pending_custom_grocers", [])
                _existing_all_m = (
                    {g["chain"].lower() for g in grocers}
                    | {p["chain"].lower() for p in _pending_m}
                )
                if _manual_name.strip().lower() not in _existing_all_m:
                    _pending_m.append({
                        "chain":          _manual_name.strip(),
                        "location":       _manual_loc.strip(),
                        "source":         "manual",
                        "rewards":        _manual_rewards,
                        "delivery":       _manual_delivery,
                        "is_primary":     (not grocers and not _pending_m),
                        "tier":           _manual_tier,
                        "distance_miles": _manual_dist if _manual_dist > 0 else None,
                    })
                    st.session_state["_pending_custom_grocers"] = _pending_m
                    st.rerun()
                else:
                    st.warning(f"{_manual_name.strip()} is already in your list.")
            else:
                st.warning("Enter a store name to add it.")

    # ── Enforce + Save ────────────────────────────────────────────────────────
    selected_chains = [
        chain for chain, sel in st.session_state.get("wizard_selections", {}).items() if sel
    ]
    _pending_preview = st.session_state.get("_pending_custom_grocers", [])

    # Preview panel — shows what will be saved when the user clicks Save.
    # This is the review step: nothing commits to the profile until Save is clicked.
    _all_staged = selected_chains + [p["chain"] for p in _pending_preview]
    if _all_staged:
        _preview_pills = "".join(
            f"<span style='background:#D8EDD0;color:#1E5C32;border-radius:14px;"
            f"padding:3px 10px;font-size:0.76rem;font-weight:600;margin:0 4px 4px 0;"
            f"display:inline-block;'>{ch}</span>"
            for ch in _all_staged
        )
        st.html(
            "<div style='background:#F0FAF2;border:1px solid #A8D5B0;border-radius:10px;"
            "padding:12px 16px;margin:14px 0 10px;'>"
            "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#3A8C4E;margin-bottom:8px;'>"
            "Ready to save</div>"
            "<div style='display:flex;flex-wrap:wrap;'>" + _preview_pills + "</div>"
            "<div style='font-size:0.72rem;color:#5A7A62;margin-top:6px;'>"
            "These stores will be added to your profile when you click Save store profile.</div>"
            "</div>"
        )

    st.html("<div style='margin-top:16px;'></div>")
    if not selected_chains and not _pending_preview:
        st.html("<div style='font-size:0.82rem;color:#BF5E00;margin-bottom:8px;'>"
                "⚠️ Select at least one store to continue.</div>")

    save_col, cancel_col = st.columns([1, 5])
    with save_col:
        save_disabled = len(selected_chains) == 0 and not _pending_preview
        save_clicked  = st.button(
            "Save store profile",
            type="primary",
            disabled=save_disabled,
            use_container_width=True,
        )

    if save_clicked and selected_chains:
        # Build updated grocers list from wizard selections
        new_grocers = []
        for chain in selected_chains:
            dist_val = st.session_state.get(f"wiz_dist_{chain}", 0.0)
            # Find full store metadata
            match = next(
                (s for t in STORE_TIERS for s in t["stores"] if s["chain"] == chain),
                None,
            )
            # Also check store_locations for lat/lon
            loc_match = next(
                (loc for loc in (nearby_stores if nearby_stores else []) if loc["chain"] == chain),
                None,
            )
            tier_key = loc_match["tier"] if loc_match else (
                CHAIN_TIER.get(chain.lower(), "mainstream")
            )
            new_grocers.append({
                "chain":          chain,
                "location":       loc_match["address"] if loc_match else "",
                "source":         match["source"] if match else "manual",
                "rewards":        match.get("rewards", False) if match else False,
                "delivery":       match.get("delivery", False) if match else False,
                "is_primary":     len(new_grocers) == 0,
                "tier":           tier_key,
                "distance_miles": dist_val if dist_val > 0 else None,
                "lat":            loc_match["lat"] if loc_match else None,
                "lon":            loc_match["lon"] if loc_match else None,
            })

        # Merge any custom/local stores staged during this wizard session
        # (these have no checkbox entry and were staged in _pending_custom_grocers).
        _pending_custom = st.session_state.pop("_pending_custom_grocers", [])
        _committed_lower = {ng["chain"].lower() for ng in new_grocers}
        for _pcg in _pending_custom:
            if _pcg["chain"].lower() not in _committed_lower:
                new_grocers.append(_pcg)

        st.session_state["grocers"]           = new_grocers
        st.session_state["travel_radius_mi"]  = w_radius
        st.session_state["home_zip"]          = effective_zip
        st.session_state["store_wizard_done"] = True
        st.session_state["show_store_wizard"] = False
        # Clear wizard staging state so next open starts fresh from committed grocers
        st.session_state.pop("wizard_selections", None)
        for _k in list(st.session_state.keys()):
            if _k.startswith("wiz_check_") or _k.startswith("wiz_dist_"):
                del st.session_state[_k]

        # Persist to Supabase so grocer selections survive browser refresh.
        # Degrades gracefully: if DB is unavailable the session_state save above
        # still works and the user can continue — they just need to re-enter on
        # the next sign-in (same behaviour as before this wiring).
        _db_ok, _db_msg = state.save_grocers()
        n = len(new_grocers)
        label = f"{n} store{'s' if n != 1 else ''}"
        # Track save outcome for debug expander
        st.session_state["_last_grocer_save_status"] = "OK" if _db_ok else f"FAILED: {_db_msg}"
        if _db_ok:
            st.success(f"Store profile saved — {label} added to your profile.")
        else:
            st.warning(f"Stores saved to this session ({label}). DB save failed: {_db_msg}")
        st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROFILE CARD — compact view after wizard is complete
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
else:
    # Keep nearby_chains in sync with confirmed locations (used by tier cards below)
    nearby_stores = _confirmed_nearby
    nearby_chains = {loc["chain"] for loc in nearby_stores}
    tier_colors_prof = {
        "discount": "#BF5E00", "mainstream": "#1E5C32",
        "specialty": "#1565C0", "local": "#5D4037",
    }
    tier_icons_prof = {
        "discount": "💰", "mainstream": "🏪", "specialty": "🌿", "local": "📍",
    }
    store_pills = "".join(
        f"<span style='background:#E3F4E8;color:{tier_colors_prof.get(g.get('tier',''), '#1E5C32')};"
        f"border:1px solid #D8EDD0;border-radius:20px;padding:3px 10px;"
        f"font-size:0.76rem;font-weight:600;margin:0 4px 4px 0;display:inline-block;'>"
        f"{tier_icons_prof.get(g.get('tier',''), '🏪')} {g['chain']}"
        + (f" · {g['distance_miles']:.1f}mi" if g.get("distance_miles") else "")
        + "</span>"
        for g in grocers
    )
    region_lbl = region_label(home_zip) if home_zip else "your area"
    radius_lbl = f"{travel_radius}-mile radius" if travel_radius else ""

    st.html(f"""
    <div style='background:#F0FAF2;border:1px solid #D8EDD0;border-radius:12px;
                padding:16px 20px;margin-bottom:18px;'>
      <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;'>
        <div>
          <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                      color:#3A8C4E;margin-bottom:6px;'>Your Store Profile · {region_lbl} · {radius_lbl}</div>
          <div style='flex-wrap:wrap;display:flex;'>{store_pills}</div>
        </div>
      </div>
    </div>""")

    if st.button("✏️ Edit my stores", key="open_store_wizard"):
        st.session_state["show_store_wizard"] = True
        # Dynamic key approach: no need to clear a stale widget key — the key
        # itself changes on login (encodes household_id + db_zip), so Streamlit
        # automatically initialises the new widget from value= on the next render.
        # Clearing any leftover legacy key just in case.
        st.session_state.pop("wizard_zip_input", None)
        st.rerun()
    st.html("<div style='margin-bottom:8px;'></div>")


# ── Wholesale & Delivery — Coming Soon ──────────────────────────────
# POC: This tier is a roadmap placeholder — wholesale clubs and delivery require
# membership pricing APIs, bulk-unit math, and trip/delivery-fee modelling that is
# scoped for Phase 5. Showing it here so pilot friends (and investors) can see the
# full picture of where WhollyFare is going.
with st.expander("\U0001f3ed **Wholesale & Delivery** — Costco, Sam's Club, Amazon Fresh", expanded=False):
    st.html("""
    <div style='background:linear-gradient(135deg,#071F1F,#0A3A3A);border-radius:10px;
                padding:20px 22px;color:white;'>
      <div style='font-size:0.65rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                  color:#7FD4D4;margin-bottom:8px;'>Phase 5 Roadmap — Coming Soon</div>
      <div style='font-size:1.05rem;font-weight:800;margin-bottom:8px;'>
        Warehouse clubs + online delivery in the price engine.
      </div>
      <div style='font-size:0.84rem;color:rgba(255,255,255,0.7);line-height:1.6;max-width:560px;'>
        Costco, Sam’s Club, BJ’s Wholesale, and Amazon Fresh are a fundamentally different
        purchase model — bulk units, membership fees, delivery costs, and monthly rather than
        weekly shopping cadences. WhollyFare will integrate them once national grocery coverage
        is solid. The engine will handle the math honestly: a 10-lb bag of chicken is only
        a deal if your household actually uses 10 lbs before it spoils.
      </div>
      <div style='margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;'>
        <span style='background:rgba(127,212,212,0.15);border:1px solid rgba(127,212,212,0.4);
                     border-radius:20px;padding:4px 14px;font-size:0.76rem;color:#7FD4D4;'>
          \U0001f3ed Costco
        </span>
        <span style='background:rgba(127,212,212,0.15);border:1px solid rgba(127,212,212,0.4);
                     border-radius:20px;padding:4px 14px;font-size:0.76rem;color:#7FD4D4;'>
          \U0001f6d2 Sam’s Club
        </span>
        <span style='background:rgba(127,212,212,0.15);border:1px solid rgba(127,212,212,0.4);
                     border-radius:20px;padding:4px 14px;font-size:0.76rem;color:#7FD4D4;'>
          \U0001f4e6 BJ’s Wholesale
        </span>
        <span style='background:rgba(127,212,212,0.15);border:1px solid rgba(127,212,212,0.4);
                     border-radius:20px;padding:4px 14px;font-size:0.76rem;color:#7FD4D4;'>
          \U0001f6d2 Amazon Fresh
        </span>
      </div>
    </div>
    """)


# ── Active store list ─────────────────────────────────────────────────────────
if grocers:
    # Group by tier for display
    tier_order  = ["discount", "mainstream", "specialty", "local", ""]
    tier_labels = {"discount": "💰 Value", "mainstream": "🏪 Full-Service",
                   "specialty": "🌿 Specialty", "local": "📍 Local", "": "Other"}
    tier_colors = {"discount": "#F28B30", "mainstream": "#3A8C4E",
                   "specialty": "#1565C0", "local": "#5D4037", "": "#5A7A62"}

    st.html("<hr style='border-color:#D8EDD0;margin:20px 0 14px 0;'>")
    st.html("<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#3A8C4E;margin-bottom:10px;'>"
            "YOUR SAVED STORES</div>")

    to_remove = None
    for idx, g in enumerate(grocers):
        t      = g.get("tier", "")
        tcolor = tier_colors.get(t, "#5A7A62")
        tlabel = tier_labels.get(t, "Other")
        star   = " ⭐" if g.get("is_primary") else ""
        loc    = f" · {g['location']}" if g.get("location") else ""
        src_ic = "🔗" if "api" in g.get("source","") else "📄"
        dist   = g.get("distance_miles")
        trip_c = round(float(dist) * 2 * 0.22, 2) if dist and not g.get("is_primary") else None
        trip_str = (f" · ~${trip_c:.2f} round trip" if trip_c else
                    (" · home base" if g.get("is_primary") else " · add distance →"))

        ra, rb, rc, rd = st.columns([4, 1.5, 1.2, 0.7])
        with ra:
            st.html(
                f"<div style='padding:5px 0;'>"
                f"<span style='font-size:0.88rem;font-weight:700;color:#1E5C32;'>"
                f"{src_ic} {g['chain']}{star}</span>"
                f"<span style='font-size:0.75rem;color:{tcolor};font-weight:600;"
                f" margin-left:8px;padding:1px 7px;border-radius:10px;'>{tlabel}</span>"
                f"<span style='font-size:0.75rem;color:#9AA8A0;'>{trip_str}{loc}</span>"
                f"</div>"
            )
        with rb:
            # Inline distance editor
            new_dist = st.number_input(
                "Miles", min_value=0.0, max_value=200.0, step=0.5,
                value=float(dist) if dist else 0.0,
                key=f"dist_{idx}",
                label_visibility="collapsed",
                help="Miles from home (one way) — used to calculate trip cost",
            )
            if new_dist != (dist or 0.0):
                grocers[idx]["distance_miles"] = new_dist if new_dist > 0 else None
                st.session_state["grocers"] = grocers
                st.rerun()
        with rc:
            if not g.get("is_primary"):
                if st.button("Set primary", key=f"primary_{idx}", use_container_width=True):
                    for gg in grocers:
                        gg["is_primary"] = False
                    grocers[idx]["is_primary"] = True
                    st.session_state["grocers"] = grocers
                    st.rerun()
        with rd:
            if st.button("✕", key=f"remove_{idx}", help=f"Remove {g['chain']}"):
                to_remove = idx

    if to_remove is not None:
        grocers.pop(to_remove)
        st.session_state["grocers"] = grocers
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# WEEK SELECTOR + STATUS
# ══════════════════════════════════════════════════════════════════════════════

if not grocers:
    st.stop()

st.html("<hr style='border-color:#D8EDD0;margin:20px 0 16px 0;'>")

col_w, col_status, col_pull = st.columns([2, 2, 1])
with col_w:
    active_week = st.date_input(
        "Planning week",
        value=datetime.date.fromisoformat(st.session_state["active_week"]),
        label_visibility="collapsed",
    )
    st.session_state["active_week"] = active_week.isoformat()

loaded = state.stores_loaded_this_week()

with col_status:
    total_items  = state.total_items_loaded()
    manual_count = len(st.session_state.get("manual_items", []))
    if len(loaded) == 0 and manual_count == 0:
        st.html('<span class="pill pill-miss">⚠ No prices loaded yet</span>')
    elif len(loaded) < len(grocers):
        st.html(f'<span class="pill pill-warn">⚠ {len(loaded)} of {len(grocers)} stores loaded</span>')
    else:
        st.html(f'<span class="pill pill-ok">✓ {total_items} items across {len(loaded)} stores</span>')

with col_pull:
    _pull_all_api = st.button("Pull API stores", use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stores",         len(grocers))
c2.metric("Items loaded",   state.total_items_loaded())
c3.metric("Manual entries", len(st.session_state.get("manual_items", [])))
c4.metric("API-connected",  sum(1 for g in grocers if g.get("source") in ("api", "api")))

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _chain_name(g: dict) -> str:
    return g.get("chain") or g.get("name", "?")

def _source(g: dict) -> str:
    return g.get("source") or g.get("source_type", "manual")

def _status_badge(chain: str) -> str:
    manual = sum(1 for m in st.session_state.get("manual_items", []) if m["store"] == chain)
    if chain in loaded:
        count = len(st.session_state["flyer_data"].get(chain, []))
        parts = []
        if count:  parts.append(f"{count} from circular")
        if manual: parts.append(f"{manual} manual")
        label = " · ".join(parts) if parts else f"{count} items"
        return f'<span class="pill pill-ok">✓ {label}</span>'
    if manual:
        return f'<span class="pill pill-warn">⚠ {manual} manual only</span>'
    return '<span class="pill pill-miss">⚠ No data</span>'


def _manual_items_as_candidates(store: str) -> list[IngredientCandidate]:
    out = []
    for item in st.session_state.get("manual_items", []):
        if item["store"] != store:
            continue
        out.append(IngredientCandidate(
            name=item["name"],
            usda_fdc_id=None,
            allergens=item.get("allergens", []),
            nutrition={},
            sale_price_per_unit=item["sale_price"],
            unit=item["unit"],
            standard_unit_weight_g=100.0,
            category=item["category"],
            tags=item.get("tags", []),
        ))
    return out


def _merge_manual_into_flyer(store: str):
    flyer = st.session_state.get("flyer_data", {})
    pdf_items = [c for c in flyer.get(store, []) if not getattr(c, "_manual", False)]
    manual = _manual_items_as_candidates(store)
    for c in manual:
        c._manual = True  # type: ignore[attr-defined]
    flyer[store] = pdf_items + manual
    st.session_state["flyer_data"] = flyer


def _load_pdf_flyer(chain: str, pdf_bytes: bytes) -> tuple[int, list]:
    ingestor = FlyerIngestor()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)
    try:
        if "food lion" in chain.lower():
            try:
                from integrations.food_lion.parser import FoodLionParser
                import os
                parser = FoodLionParser(flyer_week=st.session_state["active_week"])
                result = parser.parse_pdf(tmp_path)
                usda_key = os.environ.get("USDA_API_KEY", "")
                if usda_key:
                    from integrations.food_lion.usda_enricher import USDAEnricher
                    USDAEnricher(api_key=usda_key).enrich(result)
                out = Path("app/data/flyers") / f"food_lion_{st.session_state['active_week']}.json"
                parser.save(result, out)
                candidates = ingestor.from_json(out)
            except Exception:
                candidates = ingestor.from_pdf(tmp_path, chain=chain)
        else:
            candidates = ingestor.from_pdf(tmp_path, chain=chain)

        flyer = st.session_state.get("flyer_data", {})
        existing_manual = [c for c in flyer.get(chain, []) if getattr(c, "_manual", False)]
        flyer[chain] = candidates + existing_manual
        st.session_state["flyer_data"] = flyer
        return len(candidates), candidates
    except Exception as e:
        st.error(f"PDF parse failed for {chain}: {e}")
        return 0, []
    finally:
        tmp_path.unlink(missing_ok=True)


def _pull_kroger(chain: str, location_id: str) -> int:
    import os
    client_id     = os.environ.get("KROGER_CLIENT_ID", "")
    client_secret = os.environ.get("KROGER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        st.warning("Kroger API credentials not set (KROGER_CLIENT_ID / KROGER_CLIENT_SECRET).", icon="🔑")
        return 0
    # POC: fall back to Barracks Rd location if DB row has empty or non-ID location_description.
    # A valid Kroger location_id is exactly 8 alphanumeric characters.
    # PROD: every household row will carry the user-selected location_id.
    _loc = location_id if (location_id and len(location_id) == 8 and location_id.isalnum()) else "02900359"
    try:
        from integrations.kroger.client import KrogerClient
        client = KrogerClient(client_id=client_id, client_secret=client_secret, location_id=_loc)
        result = client.get_weekly_sales(flyer_week=st.session_state["active_week"])
        out = Path("app/data/flyers") / f"kroger_{st.session_state['active_week']}.json"
        client.save(result, out)
        candidates = FlyerIngestor().from_json(out)
        flyer = st.session_state.get("flyer_data", {})
        flyer[chain] = candidates
        st.session_state["flyer_data"] = flyer
        # Diagnostic: show raw vs. filtered counts so we know what happened
        meta = result.parse_metadata
        raw   = meta.get("raw_products_seen", "?")
        no_p  = meta.get("dropped_no_promo", "?")
        found = meta.get("total_items", len(candidates))
        if found == 0:
            st.warning(
                f"Kroger API returned {raw} products, but {no_p} had no active promo price. "
                f"0 sale items passed filters. Kroger may not have active sales on these "
                f"search terms right now, or promo pricing is unavailable.",
                icon="ℹ️",
            )
        elif candidates:
            # Persist to DB so next login doesn't require a re-pull
            ok, msg = state.save_flyer_items(chain, candidates, method="api")
            if not ok:
                _log.warning("Kroger flyer DB save: %s", msg)
        return len(candidates)
    except Exception as e:
        st.error(f"Kroger pull failed: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# STORE CARDS — price entry per store
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIES = ["produce", "protein", "dairy", "grain", "legume", "pantry",
               "bakery", "frozen", "beverage", "other"]
UNITS      = ["lb", "oz", "each", "pkg", "bunch", "bag", "dozen",
               "gal", "qt", "can", "jar", "box"]
ALLERGENS  = ["peanuts", "tree_nuts", "milk", "eggs", "wheat", "soy",
               "fish", "shellfish", "sesame", "mustard", "celery", "sulphites"]

api_stores    = [g for g in grocers if _source(g) in ("api", "api")]
manual_stores = [g for g in grocers if _source(g) not in ("api",)]

# ── API stores ────────────────────────────────────────────────────────────────
if api_stores:
    st.html("<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#3A8C4E;margin-bottom:10px;'>"
            "API-connected stores</div>")

    for g in api_stores:
        chain = _chain_name(g)
        is_ok = chain in loaded
        with st.container(border=True):
            ci, cinfo, cact = st.columns([0.5, 3, 2])
            with ci:
                st.html("🔗" if is_ok else "⚡")
            with cinfo:
                st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}", unsafe_allow_html=True)
                meta = g.get("location", "")
                if g.get("rewards"):    meta += "  · 🎟 Rewards"
                if g.get("is_primary"): meta += "  · ⭐ Primary"
                st.caption(meta)
            with cact:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Re-pull" if is_ok else "Pull from API",
                                 key=f"pull_{chain}", use_container_width=True):
                        with st.spinner(f"Pulling {chain}…"):
                            n = _pull_kroger(chain, g.get("location", ""))
                        if n:
                            st.success(f"{n} items loaded.")
                            st.rerun()
                with b2:
                    if is_ok and st.button("View items", key=f"view_{chain}", use_container_width=True):
                        st.session_state["_view_store"] = chain
                        st.rerun()

    if _pull_all_api:
        for g in api_stores:
            with st.spinner(f"Pulling {_chain_name(g)}…"):
                n = _pull_kroger(_chain_name(g), g.get("location", ""))
            if n:
                st.toast(f"{_chain_name(g)}: {n} items ✓")
        st.rerun()

    st.divider()

# ── Manual / PDF stores ───────────────────────────────────────────────────────
if manual_stores:
    st.html("<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#3A8C4E;margin-bottom:10px;'>"
            "Manual entry &amp; PDF upload</div>")

for g in manual_stores:
    chain  = _chain_name(g)
    is_ok  = chain in loaded or any(m["store"] == chain for m in st.session_state.get("manual_items", []))
    dl_url = CHAIN_FLYER_URLS.get(chain.lower(), "")
    note   = CHAIN_NOTES.get(chain.lower(), "")

    with st.container(border=True):
        ci, cinfo, clink = st.columns([0.5, 4, 1.5])
        with ci:
            st.html("✅" if is_ok else "📋")
        with cinfo:
            st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}", unsafe_allow_html=True)
            _strip = _flyer_status_strip(chain)
            if _strip:
                st.html(_strip)
            loc = g.get("location", "")
            if g.get("is_primary"): loc += "  · ⭐ Primary"
            if note: loc = (loc + "  · " if loc else "") + f"*{note}*"
            st.caption(loc)
        with clink:
            if dl_url:
                st.html(f"<a href='{dl_url}' target='_blank' style='font-size:0.78rem;"
                        f"color:#3A8C4E;font-weight:600;text-decoration:none;'>"
                        f"↗ Weekly circular</a>")

        # Determine circular support for this store
        _circ_support = CHAIN_DATA.get(chain.lower(), {}).get("circular_support", "pdf_text")

        # Build tabs based on support level
        # manual_only — no PDF tab; pdf_image — PDF tab with caveat; others — both tabs normal
        if _circ_support == "manual_only":
            _tab_labels = ["✏️ Manual entry"]
        else:
            _tab_labels = ["📄 Upload circular", "✏️ Manual entry"]
        _tabs = st.tabs(_tab_labels)
        # PDF is now tab 0 (default). Manual entry is tab 1 (collapsed by default).
        if _circ_support == "manual_only":
            tab_manual = _tabs[0]
            tab_pdf    = None
        else:
            tab_pdf    = _tabs[0]
            tab_manual = _tabs[1]

        # For manual_only stores, show a gentle disclaimer above the tab
        if _circ_support == "manual_only":
            st.html(
                "<div style='background:#FBF8F5;border-left:3px solid #D7CCC8;"
                "border-radius:0 6px 6px 0;padding:8px 12px;font-size:0.79rem;"
                "color:#5D4037;margin-bottom:8px;line-height:1.5;'>"
                "✏️ <strong>Manual entry only.</strong> This store doesn't publish a "
                "machine-readable circular. Add items from their printed flyer, app, or website."
                "</div>"
            )
        elif _circ_support == "pdf_image":
            st.html(
                "<div style='background:#FFF8F0;border-left:3px solid #FFCC80;"
                "border-radius:0 6px 6px 0;padding:8px 12px;font-size:0.79rem;"
                "color:#7A4A00;margin-bottom:8px;line-height:1.5;'>"
                "🖼️ <strong>Image-based circular.</strong> PDF upload uses OCR — results vary "
                "and will miss some items. Review everything carefully, or add key items manually."
                "</div>"
            )

        with tab_manual:
            _store_items = [m for m in st.session_state.get("manual_items", [])
                            if m["store"] == chain]
            _exp_label = (
                f"✏️ Enter items manually · {len(_store_items)} added"
                if _store_items else "✏️ Enter items manually"
            )
            # Collapsed by default — expand if no items yet or user wants to add
            with st.expander(_exp_label, expanded=len(_store_items) == 0):
                st.html("<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:10px;'>"
                        "Type items directly from the weekly circular or store visit. "
                        "Useful for items the PDF upload missed, or stores without a circular.</div>")
                with st.form(key=f"manual_form_{chain}", clear_on_submit=True):
                    f1, f2, f3 = st.columns([3, 1.5, 1.5])
                    with f1:
                        item_name = st.text_input("Item name",
                                                  placeholder="e.g. Chicken Breast, Boneless Skinless",
                                                  label_visibility="collapsed")
                    with f2:
                        item_cat  = st.selectbox("Category", options=CATEGORIES,
                                                 label_visibility="collapsed")
                    with f3:
                        item_unit = st.selectbox("Unit", options=UNITS,
                                                 label_visibility="collapsed")
                    f4, f5, f6 = st.columns([1.5, 1.5, 3])
                    with f4:
                        sale_price = st.number_input("Sale price ($)", min_value=0.0, max_value=500.0,
                                                     step=0.01, format="%.2f")
                    with f5:
                        reg_price  = st.number_input("Regular price ($)", min_value=0.0, max_value=500.0,
                                                     step=0.01, format="%.2f",
                                                     help="Optional — shows % savings in the Ledger")
                    with f6:
                        item_allergens = st.multiselect("Allergens (if any)", options=ALLERGENS)
                    submitted = st.form_submit_button("＋ Add item", type="primary",
                                                      use_container_width=True)
                    if submitted and item_name.strip():
                        st.session_state["manual_items"].append({
                            "store":      chain,
                            "name":       item_name.strip(),
                            "category":   item_cat,
                            "unit":       item_unit,
                            "sale_price": round(sale_price, 2),
                            "reg_price":  round(reg_price, 2) if reg_price > 0 else None,
                            "allergens":  item_allergens,
                            "tags":       [],
                            "week":       st.session_state["active_week"],
                        })
                        _merge_manual_into_flyer(chain)
                        st.success(f"Added: {item_name.strip()} @ ${sale_price:.2f}/{item_unit}")
                        st.rerun()
                    elif submitted:
                        st.warning("Item name is required.")

            # Items list always visible below the expander
            store_items = _store_items
            if store_items:
                st.html(f"<div style='font-size:0.78rem;font-weight:700;color:#1E5C32;"
                        f"margin-bottom:6px;margin-top:8px;'>{len(store_items)} items entered</div>")
                for idx, item in enumerate(store_items):
                    ra, rb, rc, rd = st.columns([3, 1.5, 1.5, 0.8])
                    with ra:
                        st.html(f"<div style='font-size:0.88rem;color:#1A2E1D;padding:4px 0;'>"
                                f"<strong>{item['name']}</strong> "
                                f"<span style='color:#9AA8A0;font-size:0.75rem;'>"
                                f"· {item['category']}</span></div>")
                    with rb:
                        st.html(f"<div style='font-size:0.88rem;color:#F28B30;font-weight:700;"
                                f"padding:4px 0;'>${item['sale_price']:.2f}/{item['unit']}</div>")
                    with rc:
                        if item.get("reg_price"):
                            pct = round((1 - item["sale_price"] / item["reg_price"]) * 100)
                            st.html(f"<div style='font-size:0.78rem;color:#5A7A62;padding:4px 0;'>"
                                    f"was ${item['reg_price']:.2f} "
                                    f"<span style='color:#3A8C4E;font-weight:600;'>↓{pct}%</span>"
                                    f"</div>")
                        else:
                            st.html("<div style='padding:4px 0;'>—</div>")
                    with rd:
                        full_idx = next((i for i, m in enumerate(st.session_state["manual_items"])
                                         if m is item), None)
                        if full_idx is not None and st.button("✕", key=f"del_{chain}_{full_idx}"):
                            st.session_state["manual_items"].pop(full_idx)
                            _merge_manual_into_flyer(chain)
                            st.rerun()

        if tab_pdf is not None:
            with tab_pdf:
                if dl_url:
                    st.html(f"<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:8px;'>"
                            f"Download the weekly circular from "
                            f"<a href='{dl_url}' target='_blank' style='color:#3A8C4E;font-weight:600;'>"
                            f"{chain}'s website</a>, then upload it here.</div>")
                elif g.get("tier") == "local":
                    st.html("<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:8px;'>"
                            "If this store prints a paper flyer, scan or photograph it and upload the PDF. "
                            "Or use Manual Entry — works just as well.</div>")

                st.html("<div style='font-size:0.75rem;color:#9AA8A0;margin-bottom:8px;'>"
                        "⚠ PDF parsing is heuristic. Review what was extracted before running the engine.")

                uploaded = st.file_uploader(
                    f"Upload {chain} circular (PDF or JSON)",
                    type=["pdf", "json"],
                    key=f"upload_{chain}",
                    label_visibility="collapsed",
                )
                if uploaded:
                    ext = Path(uploaded.name).suffix.lower()
                    with st.spinner(f"Parsing {chain} flyer…"):
                        if ext == ".json":
                            ingestor = FlyerIngestor()
                            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                                tmp.write(uploaded.read())
                                candidates = ingestor.from_json(Path(tmp.name))
                            flyer = st.session_state.get("flyer_data", {})
                            existing_manual = [c for c in flyer.get(chain, [])
                                               if getattr(c, "_manual", False)]
                            flyer[chain] = candidates + existing_manual
                            st.session_state["flyer_data"] = flyer
                            n = len(candidates)
                        else:
                            n, candidates = _load_pdf_flyer(chain, uploaded.read())

                    if n:
                        st.success(f"✅ {n} items parsed from **{uploaded.name}**.")
                        st.session_state.setdefault("flyer_meta", {})[chain] = {
                            "count":  n,
                            "week":   st.session_state.get("active_week", ""),
                            "method": "pdf",
                            "fresh":  True,
                        }
                        st.html("<div style='font-size:0.8rem;font-weight:600;color:#1E5C32;"
                                "margin:10px 0 4px 0;'>Review — remove anything that looks wrong</div>")

                        review_key = f"pdf_review_{chain}"
                        if review_key not in st.session_state:
                            st.session_state[review_key] = {i: True for i in range(n)}

                        flyer_items = st.session_state.get("flyer_data", {}).get(chain, [])
                        pdf_items   = [c for c in flyer_items if not getattr(c, "_manual", False)]

                        # Confidence summary
                        _conf_counts = {"high": 0, "medium": 0, "low": 0}
                        for _itm in pdf_items[:50]:
                            _conf_counts[getattr(_itm, "_confidence", "medium")] += 1
                        _conf_html = (
                            f"<span style='color:#3A8C4E;font-weight:600;'>{_conf_counts['high']} high</span> · "
                            f"<span style='color:#F28B30;font-weight:600;'>{_conf_counts['medium']} medium</span> · "
                            f"<span style='color:#BF5E00;font-weight:600;'>{_conf_counts['low']} low</span> confidence"
                        )
                        st.html(f"<div style='font-size:0.75rem;color:#5A7A62;margin-bottom:8px;'>"
                                f"Parser confidence: {_conf_html}. "
                                f"Remove anything that looks wrong before running the engine.</div>")

                        for i, item in enumerate(pdf_items[:50]):
                            name  = item.name if hasattr(item, "name") else item.get("name", "?")
                            price = item.sale_price_per_unit if hasattr(item, "sale_price_per_unit") else item.get("sale_price_per_unit", 0)
                            unit  = item.unit if hasattr(item, "unit") else item.get("unit", "each")
                            cat   = item.category if hasattr(item, "category") else item.get("category", "other")
                            keep  = st.session_state[review_key].get(i, True)
                            conf  = getattr(item, "_confidence", "medium")
                            conf_dot = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "🟡")

                            ri_a, ri_b, ri_c, ri_d = st.columns([3.5, 1.5, 0.5, 0.5])
                            with ri_a:
                                col = "#1A2E1D" if keep else "#9AA8A0"
                                st.html(f"<div style='font-size:0.85rem;color:{col};padding:2px 0;'>"
                                        f"{'<s>' if not keep else ''}{name}{'</s>' if not keep else ''}"
                                        f" <span style='color:#9AA8A0;font-size:0.72rem;'>· {cat}</span>"
                                        f"</div>")
                            with ri_b:
                                st.html(f"<div style='font-size:0.85rem;color:#F28B30;padding:2px 0;'>"
                                        f"${price:.2f}/{unit}</div>")
                            with ri_c:
                                st.html(f"<div style='font-size:0.9rem;padding:2px 0;' title='{conf} confidence'>{conf_dot}</div>")
                            with ri_d:
                                if keep and st.button("✕", key=f"reject_{chain}_{i}"):
                                    st.session_state[review_key][i] = False
                                    flyer = st.session_state.get("flyer_data", {})
                                    all_pdf = [c for c in flyer.get(chain, [])
                                               if not getattr(c, "_manual", False)]
                                    kept    = [c for j, c in enumerate(all_pdf)
                                               if st.session_state[review_key].get(j, True)]
                                    manual  = [c for c in flyer.get(chain, [])
                                               if getattr(c, "_manual", False)]
                                    flyer[chain] = kept + manual
                                    st.session_state["flyer_data"] = flyer
                                    st.rerun()
                        if n > 50:
                            st.caption(f"Showing first 50 of {n} items. All {n} are in the engine.")
                    else:
                        st.warning(
                            "Parser returned 0 items — this PDF format may not be supported yet. "
                            "Use Manual Entry to add the key sale items.",
                            icon="⚠️",
                        )


# ── Item drill-down ───────────────────────────────────────────────────────────
view_store = st.session_state.pop("_view_store", None)
if view_store:
    flyer_items = st.session_state.get("flyer_data", {}).get(view_store, [])
    if flyer_items:
        st.divider()
        st.markdown(f"**{view_store} — {len(flyer_items)} items loaded this week**")
        rows = []
        for c in flyer_items:
            is_manual = getattr(c, "_manual", False)
            if isinstance(c, dict):
                price = c.get("sale_price") or c.get("sale_price_per_unit", 0)
                rows.append({"Source": "✏️ manual" if is_manual else "📄 circular",
                             "Name": c.get("name", "?"), "Category": c.get("category", "—"),
                             "Sale price": f"${price:.2f}/{c.get('unit','?')}",
                             "Allergens": ", ".join(c.get("allergens", [])) or "—"})
            else:
                rows.append({"Source": "✏️ manual" if is_manual else "📄 circular",
                             "Name": c.name, "Category": c.category,
                             "Sale price": f"${c.sale_price_per_unit:.2f}/{c.unit}",
                             "Allergens": ", ".join(c.allergens) or "—"})
        st.dataframe(rows, use_container_width=True, height=320)


# ── Demo load ─────────────────────────────────────────────────────────────────
with st.expander("✨ Load sample Charlottesville prices (demo only)", expanded=False):
    st.caption("Pre-loads Kroger Barracks Road + Food Lion Pantops data for May 11, 2026. "
               "Do not use in your actual Found Money ledger.")
    if st.button("Load sample week", key="load_demo"):
        try:
            from app.data.sample_data import load_all_demo_data
            demo = load_all_demo_data()
            norm_grocers = []
            for g in demo["grocers"]:
                src = g.get("source") or ("api" if g.get("source_type") == "api" else "manual")
                norm_grocers.append({
                    "chain":      g.get("chain") or g.get("name", "?"),
                    "location":   g.get("location", ""),
                    "source":     src,
                    "rewards":    g.get("rewards", False),
                    "delivery":   g.get("delivery", False),
                    "is_primary": g.get("is_primary", False),
                    "tier":       "mainstream",
                })
            raw_flyer = demo["flyer_data"]
            norm_flyer = {}
            if "stores" in raw_flyer:
                for _sid, _sdata in raw_flyer["stores"].items():
                    norm_flyer[_sdata.get("store_name", _sid)] = _sdata.get("items", [])
            else:
                norm_flyer = raw_flyer
            st.session_state.update({
                "grocers":        norm_grocers,
                "flyer_data":     norm_flyer,
                "plan":           demo["plan"],
                "ledger_history": demo["ledger_history"],
                "active_week":    demo["active_week"],
            })
            st.success("Sample prices loaded! Scroll down to run the engine.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load demo data: {e}")


st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# RUN THE ENGINE
# POC: Synchronous. Fine for single-household demo.
# PROD: Background Celery worker; user polls for status.
# ══════════════════════════════════════════════════════════════════════════════
all_candidates = [c for v in st.session_state.get("flyer_data", {}).values() for c in v]
can_run = len(all_candidates) > 0 and st.session_state.get("household") is not None

if not can_run:
    reasons = []
    if not st.session_state.get("household"):
        reasons.append("set up your household profile first")
    if not all_candidates:
        reasons.append("add at least one item via Manual Entry or PDF upload")
    st.info(f"Almost ready — {' and '.join(reasons)}.", icon="💡")
    if not st.session_state.get("household"):
        if st.button("→ Go to Household Setup", type="primary"):
            st.switch_page("pages/1_Household.py")

run_btn = st.button(
    f"⚙️ Run the engine — {len(all_candidates)} items across {len(grocers)} stores",
    type="primary",
    use_container_width=True,
    disabled=not can_run,
)

if run_btn:
    household = st.session_state["household"]

    with st.spinner("Running constraint engine…"):
        from app.core_logic.constraint_engine import ConstraintEngine
        engine = ConstraintEngine(household)
        result = engine.filter(all_candidates)
        st.session_state["filter_result"] = result

    with st.spinner(f"Optimising budget across {len(result.passed)} safe ingredients…"):
        from app.core_logic.budget_optimizer import BudgetOptimizer
        optimizer = BudgetOptimizer(
            weekly_budget=household.weekly_budget_usd,
            servings_per_meal=household.servings_per_meal,
            meals_per_week=household.meals_per_week,
        )
        scored   = optimizer.score(result.passed)
        selected = optimizer.select_ingredients(scored)

    with st.spinner("Assembling weekly meal plan…"):
        from app.core_logic.meal_planner import MealPlanner
        planner  = MealPlanner(household)
        raw_plan = planner.assemble_week(
            hero_ingredients=selected,
            flyer_week=st.session_state["active_week"],
        )
        n_meals    = len(raw_plan.meals)
        plan_meals = []
        plan_total = 0.0
        for meal in raw_plan.meals:
            ing_list  = []
            meal_cost = 0.0
            for scored_ing in meal.ingredients:
                ing  = scored_ing.ingredient
                cost = ing.sale_price_per_unit
                ing_list.append({"item": ing.name, "qty": f"1 {ing.unit}",
                                  "store": getattr(ing, "source_store", "—"),
                                  "cost": round(cost, 2)})
                meal_cost += cost
            plan_meals.append({
                "day": meal.day, "name": meal.name,
                "gluten_free": False, "allergen_notes": "",
                "best_store": "—", "ingredients": ing_list,
                "meal_cost": round(meal_cost, 2),
            })
            plan_total += meal_cost

        total_servings = n_meals * household.servings_per_meal
        single_est     = round(plan_total * 1.18, 2)
        hf_equiv       = round(total_servings * 9.99, 2)
        st.session_state["plan"] = {
            "week": st.session_state["active_week"],
            "servings": household.servings_per_meal,
            "meals": plan_meals,
            "totals": {
                "whollyfare_plan":   round(plan_total, 2),
                "single_store_best": single_est,
                "hellofresh_equiv":  hf_equiv,
                "found_money":       round(single_est - plan_total, 2),
                "vs_hellofresh":     round(hf_equiv - plan_total, 2),
            },
        }

    st.success(
        f"✅  {n_meals} dinners planned · "
        f"{len(result.passed)} ingredients cleared · "
        f"{len(result.rejected)} rejected by safety rules."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/3_Plan.py",          label="→ Review this week's plan", icon="🍽️")
    with c2:
        st.page_link("pages/4_Sunday_BuyOff.py", label="→ Go straight to Buy-Off",  icon="✅")
