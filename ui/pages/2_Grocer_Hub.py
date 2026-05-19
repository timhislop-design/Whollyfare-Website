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

st.set_page_config(page_title="Grocer Hub · WhollyFare", page_icon="🏪", layout="wide")
state.init()

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
            src    = g.get("source", "manual_pdf")
            icon   = "🔗" if "api" in src else "📄"
            star   = " ⭐" if g.get("is_primary") else ""
            tier_c = {"discount": "#F28B30", "mainstream": "#9FD9A8",
                      "specialty": "#81C784", "local": "#FFCC80"}.get(g.get("tier",""), "#9FD9A8")
            st.html(f"<div style='font-size:0.82rem;color:#e8f5ec;padding:2px 0;'>"
                    f"<span style='color:{tier_c};'>{icon}</span> {g.get('chain','?')}{star}</div>")

style.page_header(
    "Grocer Hub",
    "Tell us where you shop. We'll track prices across every store and find your savings.",
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
            {"chain": "ALDI",           "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.aldi.us/en/weekly-specials/",
             "note": "No loyalty card. Weekly Specialbuys rotate — download flyer Sunday."},
            {"chain": "Lidl",           "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.lidl.com/en/weekly-specials",
             "note": "Similar model to ALDI. Check 'Lidl Surprises' for deep cuts."},
            {"chain": "Walmart",        "source": "manual_pdf",  "rewards": False, "delivery": True,
             "flyer": "https://www.walmart.com/store/finder",
             "note": "Rollback prices change without a fixed flyer cycle. Manual entry works best."},
            {"chain": "Dollar General", "source": "manual_pdf",  "rewards": True,  "delivery": False,
             "flyer": "https://www.dollargeneral.com/weekly-ad",
             "note": "Strong on canned goods, pasta, and pantry staples."},
            {"chain": "Dollar Tree",    "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.dollartree.com/deals",
             "note": "$1.25 flat pricing. Great for spices, canned tomatoes, condiments."},
            {"chain": "WinCo Foods",    "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.wincofoods.com/weekly-ad",
             "note": "Employee-owned. Consistently lowest prices in markets where it operates."},
            {"chain": "Save-A-Lot",     "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.savealot.com/savings/weekly-ad",
             "note": "Deep-discount regional chain. Strong in Southeast and Midwest."},
            {"chain": "Food 4 Less",    "source": "manual_pdf",  "rewards": True,  "delivery": False,
             "flyer": "https://www.food4less.com/weeklyad",
             "note": "Kroger warehouse banner. No-frills pricing, full selection."},
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
            {"chain": "Kroger",         "source": "manual_pdf+api", "rewards": True,  "delivery": True,
             "flyer": "https://www.kroger.com/weeklyad",
             "note": "API available. Loyalty card unlocks digital coupons stacked on sale prices."},
            {"chain": "Food Lion",      "source": "manual_pdf",     "rewards": True,  "delivery": False,
             "flyer": "https://stores.foodlion.com",
             "note": "MVP Card deals often beat Kroger on produce. Strong in Southeast."},
            {"chain": "Harris Teeter",  "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.harristeeter.com/weeklyad",
             "note": "VIC card + e-VIC digital coupons. Super Double coupon events quarterly."},
            {"chain": "Giant Food",     "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://stores.giantfood.com",
             "note": "Giant Card + Gas Rewards. Mid-Atlantic staple."},
            {"chain": "Wegmans",        "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.wegmans.com/weeklyad",
             "note": "Club card + Wegmans app coupons. Known for quality and price on store brand."},
            {"chain": "Publix",         "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.publix.com/savings/weekly-ad",
             "note": "BOGO deals are a Publix signature. Plus Card digital coupons."},
            {"chain": "Safeway",        "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.safeway.com/weeklyad",
             "note": "Just for U digital coupons stack on Club Card pricing."},
            {"chain": "Albertsons",     "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.albertsons.com/weeklyad",
             "note": "Same ownership as Safeway. For Just U coupons, strong BOGO weeks."},
            {"chain": "Meijer",         "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.meijer.com/shopping/weekly-deals.html",
             "note": "Midwest supercenter. mPerks digital coupons stack on weekly sales."},
            {"chain": "Hy-Vee",         "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.hy-vee.com/weekly-deals/",
             "note": "Employee-owned Midwest chain. Fuel Saver + Perks program."},
            {"chain": "Stop & Shop",    "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://stopandshop.com/weeklyCircular/",
             "note": "Gas Points program. Northeast regional staple."},
            {"chain": "ShopRite",       "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.shoprite.com/sm/planning/rsid/5002/weekly-specials",
             "note": "Price Plus card. Can-Can Sale in January is legendary for savings."},
            {"chain": "Giant Eagle",    "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.gianteagle.com/save/weekly-circular",
             "note": "fuelperks+ program. Strong in Ohio, Pennsylvania, West Virginia."},
            {"chain": "H-E-B",          "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.heb.com/static-page/weekly-ad",
             "note": "Texas institution. H-E-B Combo deals are a local savings fixture."},
            {"chain": "Weis Markets",   "source": "manual_pdf",     "rewards": True,  "delivery": True,
             "flyer": "https://www.weismarkets.com/weeklyad",
             "note": "Mid-Atlantic regional. Weis Club card + digital deals."},
            {"chain": "Ingles Markets", "source": "manual_pdf",     "rewards": True,  "delivery": False,
             "flyer": "https://www.ingles-markets.com/weeklyad",
             "note": "Southeast regional. Advantage Card savings + gas discounts."},
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
            {"chain": "Whole Foods",    "source": "manual_pdf",  "rewards": True,  "delivery": True,
             "flyer": "https://www.wholefoodsmarket.com/sales-flyer",
             "note": "Prime members get extra 10% off sale items. 365 brand is price-competitive."},
            {"chain": "Trader Joe's",   "source": "manual_pdf",  "rewards": False, "delivery": False,
             "flyer": "https://www.traderjoes.com/home/fearless-flyer",
             "note": "No loyalty card, no weekly sale cycle. Fearless Flyer runs monthly. Stable pricing."},
            {"chain": "Sprouts",        "source": "manual_pdf",  "rewards": False, "delivery": True,
             "flyer": "https://www.sprouts.com/deals/weekly-ad/",
             "note": "Produce-forward. Double Ad Wednesdays overlap two sale weeks."},
            {"chain": "The Fresh Market","source": "manual_pdf",  "rewards": True,  "delivery": False,
             "flyer": "https://www.thefreshmarket.com/weekly-specials",
             "note": "Premium meats and produce. Weekly specials often include protein deals."},
            {"chain": "Earth Fare",     "source": "manual_pdf",  "rewards": True,  "delivery": False,
             "flyer": "https://www.earthfare.com/deals/",
             "note": "No artificial ingredients policy. Regional natural chain, Southeast focus."},
            {"chain": "Natural Grocers","source": "manual_pdf",  "rewards": True,  "delivery": False,
             "flyer": "https://www.naturalgrocers.com/weekly-ad",
             "note": "100% organic produce, always. {N}power card unlocks member pricing."},
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
            {"chain": "EW Thomas Grocery",        "source": "manual_pdf", "rewards": False, "delivery": False,
             "flyer": "",
             "note": "Palmyra, VA. Local institution — meat counter, produce, and weekly specials."},
            {"chain": "Foods of All Nations",     "source": "manual_pdf", "rewards": False, "delivery": False,
             "flyer": "",
             "note": "Charlottesville, VA. International specialty market. Unique ingredients, fair prices."},
            {"chain": "Integral Yoga Natural",    "source": "manual_pdf", "rewards": False, "delivery": False,
             "flyer": "",
             "note": "Charlottesville, VA. Natural and organic co-op. Bulk bins, local produce."},
            {"chain": "The Fresh Marketplace",    "source": "manual_pdf", "rewards": False, "delivery": False,
             "flyer": "",
             "note": "Charlottesville, VA area. Check locally for current weekly specials."},
            {"chain": "Reid's Country Store",     "source": "manual_pdf", "rewards": False, "delivery": False,
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
# "WHERE DO YOU LIKE TO SHOP?" — Tiered store selection
# ══════════════════════════════════════════════════════════════════════════════
grocers = st.session_state.get("grocers", [])
existing_chains_lower = {g.get("chain", "").lower() for g in grocers}

# Intro banner (shown until at least one store is configured)
if not grocers:
    st.html("""
    <div style='background:linear-gradient(135deg,#E8F5E9,#F0FAF2);
                border:1px solid #D8EDD0;border-radius:12px;
                padding:20px 24px;margin-bottom:24px;'>
      <div style='font-size:1.15rem;font-weight:700;color:#1E5C32;margin-bottom:6px;'>
        Where do you like to shop?
      </div>
      <div style='font-size:0.88rem;color:#3A8C4E;line-height:1.5;'>
        Add the stores you actually visit. WhollyFare will compare prices across all of them —
        routing each ingredient to wherever it's cheapest that week.
        The more stores, the more Found Money.
      </div>
    </div>""")

# ── Tier cards ────────────────────────────────────────────────────────────────
for tier in STORE_TIERS:
    tier_stores     = tier["stores"]
    tier_added      = [s for s in tier_stores if s["chain"].lower() in existing_chains_lower]
    tier_available  = [s for s in tier_stores if s["chain"].lower() not in existing_chains_lower]
    added_count     = len(tier_added)
    total_count     = len(tier_stores)
    is_local        = tier["key"] == "local"

    # Collapse if all stores already added and not local (local always stays open for custom adds)
    default_open = (added_count < total_count) or is_local

    with st.expander(
        f"{tier['icon']} **{tier['label']}** — {added_count} of {total_count} added",
        expanded=default_open,
    ):
        st.html(
            f"<div style='font-size:0.83rem;color:#5A7A62;margin-bottom:14px;"
            f"border-left:3px solid {tier['border']};padding-left:10px;'>"
            f"{tier['tagline']}</div>"
        )

        if tier_available:
            # Responsive 3-column grid
            COLS = 3
            for row_start in range(0, len(tier_available), COLS):
                row = tier_available[row_start:row_start + COLS]
                cols = st.columns(COLS)
                for col, store_def in zip(cols, row):
                    with col:
                        note = store_def.get("note", "")
                        badges = []
                        if store_def.get("rewards"):   badges.append("🎟 Rewards")
                        if store_def.get("delivery"):  badges.append("🚚 Delivery")
                        if "api" in store_def.get("source", ""): badges.append("🔗 API")
                        badge_str = " · ".join(badges) if badges else ""
                        flyer_link = store_def.get("flyer", "")

                        st.html(f"""
                        <div style='background:white;border:1px solid {tier["border"]};
                                    border-top:3px solid {tier["color"]};
                                    border-radius:8px;padding:12px;min-height:90px;
                                    margin-bottom:2px;'>
                          <div style='font-weight:700;color:{tier["color"]};font-size:0.92rem;'>
                            {store_def['chain']}
                          </div>
                          <div style='font-size:0.72rem;color:#5A7A62;margin-top:4px;
                                      line-height:1.4;'>{note}</div>
                          <div style='font-size:0.68rem;color:#9AA8A0;margin-top:6px;'>
                            {badge_str}
                          </div>
                        </div>""")

                        btn_label = "Add"
                        if st.button(btn_label, key=f"add_{tier['key']}_{store_def['chain']}",
                                     use_container_width=True):
                            new_store = {
                                "chain":      store_def["chain"],
                                "location":   "",
                                "source":     store_def["source"],
                                "rewards":    store_def.get("rewards", False),
                                "delivery":   store_def.get("delivery", False),
                                "is_primary": len(grocers) == 0,
                                "tier":       tier["key"],
                            }
                            grocers.append(new_store)
                            st.session_state["grocers"] = grocers
                            st.rerun()

        if tier_added:
            names = ", ".join(s["chain"] for s in tier_added)
            st.html(
                f"<div style='font-size:0.75rem;color:{tier['color']};margin-top:6px;'>"
                f"✓ Added: {names}</div>"
            )

        # ── Local tier: custom store form ─────────────────────────────────────
        if is_local:
            st.html("<hr style='border-color:#D7CCC8;margin:14px 0 10px 0;'>")
            st.html("<div style='font-size:0.82rem;font-weight:600;color:#5D4037;"
                    "margin-bottom:8px;'>Add your own local store</div>")
            st.html("<div style='font-size:0.78rem;color:#8D6E63;margin-bottom:10px;'>"
                    "Any store, co-op, farm stand, or butcher — if they run specials, "
                    "WhollyFare can track them.</div>")

            lc1, lc2 = st.columns([2, 1])
            with lc1:
                local_name = st.text_input("Store name", placeholder="e.g. Blue Ridge Co-op, Murphy's Market",
                                           key="local_custom_name", label_visibility="collapsed")
            with lc2:
                local_loc = st.text_input("Town / zip (optional)", placeholder="Crozet VA",
                                          key="local_custom_loc", label_visibility="collapsed")

            lc3, lc4 = st.columns(2)
            with lc3:
                local_rewards = st.checkbox("Has loyalty / rewards card", key="local_rewards")
            with lc4:
                local_delivery = st.checkbox("Offers delivery", key="local_delivery")

            if st.button("Add local store", type="primary", key="add_local_custom"):
                if local_name.strip():
                    grocers.append({
                        "chain":      local_name.strip(),
                        "location":   local_loc.strip(),
                        "source":     "manual_pdf",
                        "rewards":    local_rewards,
                        "delivery":   local_delivery,
                        "is_primary": len(grocers) == 0,
                        "tier":       "local",
                    })
                    st.session_state["grocers"] = grocers
                    st.rerun()
                else:
                    st.warning("Enter a store name.")

        # Non-local custom stores (discount/mainstream/specialty chains not on the list)
        if not is_local:
            with st.expander(f"My {tier['label'].lower()} store isn't listed", expanded=False):
                cc1, cc2 = st.columns([2, 1])
                with cc1:
                    c_name = st.text_input("Store name", key=f"custom_name_{tier['key']}",
                                           label_visibility="collapsed",
                                           placeholder=f"e.g. My regional {tier['label'].lower()} chain")
                with cc2:
                    c_loc = st.text_input("Location (optional)", key=f"custom_loc_{tier['key']}",
                                          label_visibility="collapsed", placeholder="City, State")
                if st.button(f"Add to {tier['label']}", key=f"add_custom_{tier['key']}", type="primary"):
                    if c_name.strip():
                        grocers.append({
                            "chain":      c_name.strip(),
                            "location":   c_loc.strip(),
                            "source":     "manual_pdf",
                            "rewards":    False,
                            "delivery":   False,
                            "is_primary": len(grocers) == 0,
                            "tier":       tier["key"],
                        })
                        st.session_state["grocers"] = grocers
                        st.rerun()
                    else:
                        st.warning("Enter a store name.")


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
            "YOUR ACTIVE STORES THIS WEEK</div>")

    to_remove = None
    for idx, g in enumerate(grocers):
        t      = g.get("tier", "")
        tcolor = tier_colors.get(t, "#5A7A62")
        tlabel = tier_labels.get(t, "Other")
        star   = " ⭐" if g.get("is_primary") else ""
        loc    = f" · {g['location']}" if g.get("location") else ""
        src_ic = "🔗" if "api" in g.get("source","") else "📄"

        ra, rb, rc = st.columns([5, 1.2, 0.7])
        with ra:
            st.html(
                f"<div style='padding:5px 0;'>"
                f"<span style='font-size:0.88rem;font-weight:700;color:#1E5C32;'>"
                f"{src_ic} {g['chain']}{star}</span>"
                f"<span style='font-size:0.75rem;color:{tcolor};font-weight:600;"
                f" margin-left:8px;background:{tier_colors.get(t, '#eee')}22;"
                f" padding:1px 7px;border-radius:10px;'>{tlabel}</span>"
                f"<span style='font-size:0.78rem;color:#5A7A62;'>{loc}</span>"
                f"</div>"
            )
        with rb:
            if not g.get("is_primary"):
                if st.button("Set primary", key=f"primary_{idx}", use_container_width=True):
                    for gg in grocers:
                        gg["is_primary"] = False
                    grocers[idx]["is_primary"] = True
                    st.session_state["grocers"] = grocers
                    st.rerun()
        with rc:
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
c4.metric("API-connected",  sum(1 for g in grocers if g.get("source") in ("api", "manual_pdf+api")))

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _chain_name(g: dict) -> str:
    return g.get("chain") or g.get("name", "?")

def _source(g: dict) -> str:
    return g.get("source") or g.get("source_type", "manual_pdf")

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
    try:
        from integrations.kroger.client import KrogerClient
        client = KrogerClient(client_id=client_id, client_secret=client_secret, location_id=location_id)
        result = client.get_weekly_sales(flyer_week=st.session_state["active_week"])
        out = Path("app/data/flyers") / f"kroger_{st.session_state['active_week']}.json"
        client.save(result, out)
        candidates = FlyerIngestor().from_json(out)
        flyer = st.session_state.get("flyer_data", {})
        flyer[chain] = candidates
        st.session_state["flyer_data"] = flyer
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

api_stores    = [g for g in grocers if _source(g) in ("api", "manual_pdf+api")]
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
            loc = g.get("location", "")
            if g.get("is_primary"): loc += "  · ⭐ Primary"
            if note: loc = (loc + "  · " if loc else "") + f"*{note}*"
            st.caption(loc)
        with clink:
            if dl_url:
                st.html(f"<a href='{dl_url}' target='_blank' style='font-size:0.78rem;"
                        f"color:#3A8C4E;font-weight:600;text-decoration:none;'>"
                        f"↗ Weekly circular</a>")

        tab_manual, tab_pdf = st.tabs(["✏️ Manual entry", "📄 PDF upload"])

        with tab_manual:
            st.html("<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:10px;'>"
                    "Type items directly from the weekly circular or store visit.</div>")
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

            store_items = [m for m in st.session_state.get("manual_items", [])
                           if m["store"] == chain]
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
            else:
                st.html("<div style='font-size:0.82rem;color:#9AA8A0;padding:8px 0;'>"
                        "No items yet — add your first item above, or upload the PDF circular.</div>")

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
                    st.html("<div style='font-size:0.8rem;font-weight:600;color:#1E5C32;"
                            "margin:10px 0 4px 0;'>Review — remove anything that looks wrong</div>")

                    review_key = f"pdf_review_{chain}"
                    if review_key not in st.session_state:
                        st.session_state[review_key] = {i: True for i in range(n)}

                    flyer_items = st.session_state.get("flyer_data", {}).get(chain, [])
                    pdf_items   = [c for c in flyer_items if not getattr(c, "_manual", False)]

                    for i, item in enumerate(pdf_items[:50]):
                        name  = item.name if hasattr(item, "name") else item.get("name", "?")
                        price = item.sale_price_per_unit if hasattr(item, "sale_price_per_unit") else item.get("sale_price_per_unit", 0)
                        unit  = item.unit if hasattr(item, "unit") else item.get("unit", "each")
                        cat   = item.category if hasattr(item, "category") else item.get("category", "other")
                        keep  = st.session_state[review_key].get(i, True)

                        ri_a, ri_b, ri_d = st.columns([4, 1.5, 0.5])
                        with ri_a:
                            col = "#1A2E1D" if keep else "#9AA8A0"
                            st.html(f"<div style='font-size:0.85rem;color:{col};padding:2px 0;'>"
                                    f"{'<s>' if not keep else ''}{name}{'</s>' if not keep else ''}"
                                    f" <span style='color:#9AA8A0;font-size:0.72rem;'>· {cat}</span>"
                                    f"</div>")
                        with ri_b:
                            st.html(f"<div style='font-size:0.85rem;color:#F28B30;padding:2px 0;'>"
                                    f"${price:.2f}/{unit}</div>")
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
                src = g.get("source") or ("api" if g.get("source_type") == "api" else "manual_pdf")
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
