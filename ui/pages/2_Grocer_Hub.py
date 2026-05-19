"""
2_Grocer_Hub.py — Grocer Data Hub
===================================
Weekly price data entry for all configured stores.

Three data paths (in order of reliability for the POC):
  1. Manual item entry  — type items in directly; always works; investor-demo safe
  2. PDF upload         — parse sale circulars automatically; heuristic, review required
  3. Kroger API         — live pull when credentials are available

Store management:
  - 20+ national chain presets (one-click add)
  - Add any custom/local chain by name
  - No hard limit on number of stores

POC vs. PRODUCTION
-------------------
POC:  Data lives in Streamlit session_state. Cleared on browser refresh.
      Manual entry is the primary path for the pilot weeks.
PROD: Items persist to PostgreSQL (user_id + week_id + store_id foreign keys).
      PDF parsing runs in a background worker (Celery / Lambda).
      Kroger API is the primary path; PDF/manual are fallbacks.
"""

import sys
import json
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
    st.html("<div style='font-size:0.7rem;font-weight:700;color:#9FD9A8;letter-spacing:0.08em;'>CONFIGURED STORES</div>")
    grocers = st.session_state.get("grocers", [])
    if grocers:
        for g in grocers:
            src  = g.get("source", "manual_pdf")
            icon = "🔗" if "api" in src else "📄"
            primary = " ⭐" if g.get("is_primary") else ""
            st.caption(f"{icon} {g.get('chain','?')}{primary}")
    else:
        st.caption("No stores yet — add below")

style.page_header(
    "Grocer Hub",
    "Load this week's prices — type items in, upload a circular PDF, or pull from Kroger.",
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
# KNOWN CHAINS REGISTRY
# POC: Static list covering the major US grocery chains.
# PROD: Pulled from a store registry DB (chain_id, name, logo, api_available,
#       pdf_parser_available, regional_coverage). User's zip code filters to
#       chains within 30 miles.
# ══════════════════════════════════════════════════════════════════════════════
KNOWN_CHAINS: list[dict] = [
    # ── Charlottesville pilot stores (shown first) ──
    {"chain": "Kroger",         "source": "manual_pdf+api", "rewards": True,  "delivery": False, "flyer": "https://www.kroger.com/weeklyad"},
    {"chain": "Food Lion",      "source": "manual_pdf",     "rewards": True,  "delivery": False, "flyer": "https://stores.foodlion.com"},
    {"chain": "Aldi",           "source": "manual_pdf",     "rewards": False, "delivery": False, "flyer": "https://www.aldi.us/en/weekly-specials/"},
    {"chain": "Harris Teeter",  "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.harristeeter.com/weeklyad"},
    # ── National ──
    {"chain": "Walmart",        "source": "manual_pdf",     "rewards": False, "delivery": True,  "flyer": "https://www.walmart.com/store/finder"},
    {"chain": "Target",         "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.target.com/c/weekly-ad-target/-/N-brgaj"},
    {"chain": "Costco",         "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.costco.com/warehouse-savings.html"},
    {"chain": "Sam's Club",     "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.samsclub.com/savings"},
    {"chain": "Whole Foods",    "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.wholefoodsmarket.com/sales-flyer"},
    {"chain": "Trader Joe's",   "source": "manual_pdf",     "rewards": False, "delivery": False, "flyer": "https://www.traderjoes.com/home/fearless-flyer"},
    {"chain": "Publix",         "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.publix.com/savings/weekly-ad"},
    {"chain": "Safeway",        "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.safeway.com/weeklyad"},
    {"chain": "Albertsons",     "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.albertsons.com/weeklyad"},
    {"chain": "Wegmans",        "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.wegmans.com/weeklyad"},
    {"chain": "Giant Food",     "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://stores.giantfood.com"},
    {"chain": "Giant Eagle",    "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.gianteagle.com/save/weekly-circular"},
    {"chain": "H-E-B",          "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.heb.com/static-page/weekly-ad"},
    {"chain": "Sprouts",        "source": "manual_pdf",     "rewards": False, "delivery": True,  "flyer": "https://www.sprouts.com/deals/weekly-ad/"},
    {"chain": "WinCo Foods",    "source": "manual_pdf",     "rewards": False, "delivery": False, "flyer": "https://www.wincofoods.com/weekly-ad"},
    {"chain": "Meijer",         "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.meijer.com/shopping/weekly-deals.html"},
    {"chain": "Hy-Vee",         "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.hy-vee.com/weekly-deals/"},
    {"chain": "Stop & Shop",    "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://stopandshop.com/weeklyCircular/"},
    {"chain": "ShopRite",       "source": "manual_pdf",     "rewards": True,  "delivery": True,  "flyer": "https://www.shoprite.com/sm/planning/rsid/5002/weekly-specials"},
    {"chain": "Lidl",           "source": "manual_pdf",     "rewards": False, "delivery": False, "flyer": "https://www.lidl.com/en/weekly-specials"},
    {"chain": "Dollar General", "source": "manual_pdf",     "rewards": True,  "delivery": False, "flyer": "https://www.dollargeneral.com/weekly-ad"},
]

CHAIN_FLYER_URLS = {c["chain"].lower(): c["flyer"] for c in KNOWN_CHAINS}


# ══════════════════════════════════════════════════════════════════════════════
# STORE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
grocers = st.session_state.get("grocers", [])
existing_chains_lower = {g.get("chain", "").lower() for g in grocers}

st.html("""
<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
color:#3A8C4E;margin-bottom:8px;'>YOUR STORES</div>
""")

if not grocers:
    st.info("Add your grocery stores below, then load prices for this week.", icon="🏪")

# ── Store preset browser ───────────────────────────────────────────────────────
with st.expander(
    f"{'＋ Add stores' if not grocers else '＋ Add another store'} — pick from 25 major chains",
    expanded=not grocers,
):
    # Search/filter
    search = st.text_input(
        "Search chains",
        placeholder="e.g. Kroger, Publix, Walmart…",
        key="chain_search",
        label_visibility="collapsed",
    )

    filtered = [
        c for c in KNOWN_CHAINS
        if search.lower() in c["chain"].lower() and c["chain"].lower() not in existing_chains_lower
    ] if search else [
        c for c in KNOWN_CHAINS if c["chain"].lower() not in existing_chains_lower
    ]

    if not filtered:
        st.caption("All chains from this list are already added. Use 'Add a local or custom store' below to add more.")
    else:
        # Show in a 4-column grid
        COLS = 4
        for row_start in range(0, len(filtered), COLS):
            row = filtered[row_start:row_start + COLS]
            cols = st.columns(COLS)
            for col, chain_def in zip(cols, row):
                with col:
                    src_label = "API + PDF" if chain_def["source"] == "manual_pdf+api" else "PDF / manual"
                    badges = []
                    if chain_def["rewards"]:   badges.append("🎟 Rewards")
                    if chain_def["delivery"]:  badges.append("🚚 Delivery")
                    badge_str = " · ".join(badges)
                    st.html(f"""
                    <div style='background:white;border:1px solid #D8EDD0;border-top:3px solid #3A8C4E;
                                border-radius:8px;padding:10px;min-height:80px;margin-bottom:2px;'>
                      <div style='font-weight:700;color:#1E5C32;font-size:0.9rem;'>{chain_def['chain']}</div>
                      <div style='font-size:0.7rem;color:#9AA8A0;margin-top:4px;'>{src_label}</div>
                      <div style='font-size:0.68rem;color:#5A7A62;margin-top:2px;'>{badge_str}</div>
                    </div>""")
                    if st.button(f"Add", key=f"preset_{chain_def['chain']}", use_container_width=True):
                        new_store = {k: v for k, v in chain_def.items() if k != "flyer"}
                        new_store["location"] = ""
                        new_store["is_primary"] = len(grocers) == 0
                        grocers.append(new_store)
                        st.session_state["grocers"] = grocers
                        st.rerun()

    st.html("<hr style='border-color:#D8EDD0;margin:12px 0 8px 0;'>")
    st.html("<div style='font-size:0.78rem;font-weight:600;color:#1E5C32;margin-bottom:8px;'>Add a local or custom store</div>")

    ca, cb, cc = st.columns([2, 2, 1])
    with ca:
        custom_chain = st.text_input("Store name", placeholder="e.g. Bloom, Market 32, Your Co-op", key="custom_chain")
    with cb:
        custom_loc   = st.text_input("Location / zip (optional)", placeholder="Richmond VA 23220", key="custom_loc")
    with cc:
        custom_src = st.selectbox(
            "Data source",
            options=["manual_pdf", "manual_pdf+api"],
            format_func=lambda x: {"manual_pdf": "PDF / manual", "manual_pdf+api": "API + PDF"}[x],
            key="custom_src",
            label_visibility="visible",
        )
    cd, ce = st.columns(2)
    with cd:
        custom_rewards  = st.checkbox("Has loyalty / rewards program", key="custom_rewards")
    with ce:
        custom_delivery = st.checkbox("Offers delivery", key="custom_delivery")

    if st.button("Add custom store", type="primary", key="add_custom"):
        if custom_chain.strip():
            grocers.append({
                "chain":      custom_chain.strip(),
                "location":   custom_loc.strip(),
                "source":     custom_src,
                "rewards":    custom_rewards,
                "delivery":   custom_delivery,
                "is_primary": len(grocers) == 0,
            })
            st.session_state["grocers"] = grocers
            st.rerun()
        else:
            st.warning("Enter a store name.")

# ── Configured store list with remove buttons ─────────────────────────────────
if grocers:
    st.html("""
    <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
    color:#3A8C4E;margin:16px 0 8px 0;'>ACTIVE STORES THIS WEEK</div>
    """)
    to_remove = None
    for idx, g in enumerate(grocers):
        primary_badge = " ⭐" if g.get("is_primary") else ""
        src_icon = "🔗" if "api" in g.get("source","") else "📄"
        loc_txt  = f" · {g['location']}" if g.get("location") else ""
        rc1, rc2, rc3 = st.columns([4, 1, 0.7])
        with rc1:
            st.html(
                f"<div style='padding:6px 0;font-size:0.9rem;color:#1E5C32;font-weight:600;'>"
                f"{src_icon} {g['chain']}{primary_badge}"
                f"<span style='font-weight:400;color:#5A7A62;font-size:0.8rem;'>{loc_txt}</span>"
                f"</div>"
            )
        with rc2:
            if not g.get("is_primary") and st.button("Set primary", key=f"primary_{idx}", use_container_width=True):
                for gg in grocers:
                    gg["is_primary"] = False
                grocers[idx]["is_primary"] = True
                st.session_state["grocers"] = grocers
                st.rerun()
        with rc3:
            if st.button("✕", key=f"remove_{idx}", help=f"Remove {g['chain']}"):
                to_remove = idx
    if to_remove is not None:
        grocers.pop(to_remove)
        st.session_state["grocers"] = grocers
        st.rerun()

st.divider()

if not grocers:
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# WEEK SELECTOR + STATUS
# ══════════════════════════════════════════════════════════════════════════════
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
c1.metric("Stores loaded",  len(loaded))
c2.metric("Items loaded",   state.total_items_loaded())
c3.metric("Manual entries", len(st.session_state.get("manual_items", [])))
c4.metric("API connected",  sum(1 for g in grocers if g.get("source") in ("api", "manual_pdf+api")))

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
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
    """Convert session manual_items for a store into IngredientCandidate objects.

    POC: Reads from session_state. Allergen data is user-declared, not USDA-verified.
    PROD: Fetch from DB. Run USDA FDC enrichment async. Flag items lacking FDC ID.
    """
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


def _load_pdf_flyer(chain: str, pdf_bytes: bytes) -> tuple[int, list[IngredientCandidate]]:
    """Run the chain-specific PDF parser. Returns (item_count, candidates).

    POC: Food Lion has a dedicated parser; all others use the improved generic parser.
    PROD: Each supported chain gets a trained parser. Accuracy monitored; low-confidence
          items flagged for human review before reaching the engine.
    """
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
                # Fall back to generic parser if Food Lion parser fails
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
    """Pull live sale data from the Kroger Developer API.

    POC: Requires KROGER_CLIENT_ID + KROGER_CLIENT_SECRET env vars.
    PROD: OAuth2 client_credentials. Credentials in AWS Secrets Manager.
          Rate limit: 10,000 calls/day on free tier; production tier negotiated.
    """
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
# STORE CARDS — per-store price entry
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIES = ["produce", "protein", "dairy", "grain", "legume", "pantry", "bakery", "frozen", "beverage", "other"]
UNITS       = ["lb", "oz", "each", "pkg", "bunch", "bag", "dozen", "gal", "qt", "can", "jar", "box"]
ALLERGENS   = ["peanuts", "tree_nuts", "milk", "eggs", "wheat", "soy", "fish", "shellfish",
               "sesame", "mustard", "celery", "sulphites"]

api_stores    = [g for g in grocers if _source(g) in ("api", "manual_pdf+api")]
manual_stores = [g for g in grocers if _source(g) not in ("api",)]

# ── API-connected stores ──────────────────────────────────────────────────────
if api_stores:
    st.html("""
    <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
    color:#3A8C4E;margin-bottom:10px;'>API-connected stores</div>""")

    for g in api_stores:
        chain = _chain_name(g)
        is_ok = chain in loaded
        with st.container(border=True):
            col_icon, col_info, col_act = st.columns([0.5, 3, 2])
            with col_icon:
                st.html("🔗" if is_ok else "⚡")
            with col_info:
                st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}", unsafe_allow_html=True)
                meta = g.get("location", "")
                if g.get("rewards"):    meta += "  · 🎟 Rewards"
                if g.get("is_primary"): meta += "  · ⭐ Primary"
                st.caption(meta)
            with col_act:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Re-pull" if is_ok else "Pull from API", key=f"pull_{chain}", use_container_width=True):
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
    st.html("""
    <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
    color:#3A8C4E;margin-bottom:10px;'>Manual entry &amp; PDF upload</div>""")

for g in manual_stores:
    chain  = _chain_name(g)
    is_ok  = chain in loaded or any(m["store"] == chain for m in st.session_state.get("manual_items", []))
    dl_url = CHAIN_FLYER_URLS.get(chain.lower(), "")

    with st.container(border=True):
        col_icon, col_info, col_link = st.columns([0.5, 4, 1.5])
        with col_icon:
            st.html("✅" if is_ok else "📋")
        with col_info:
            st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}", unsafe_allow_html=True)
            loc = g.get("location", "")
            if g.get("is_primary"): loc += "  · ⭐ Primary"
            st.caption(loc)
        with col_link:
            if dl_url:
                st.html(f"<a href='{dl_url}' target='_blank' style='font-size:0.78rem;"
                        f"color:#3A8C4E;font-weight:600;text-decoration:none;'>↗ Weekly circular</a>")

        tab_manual, tab_pdf = st.tabs(["✏️ Manual entry", "📄 PDF upload"])

        # ── TAB 1: MANUAL ENTRY ───────────────────────────────────────────────
        with tab_manual:
            st.html("<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:10px;'>"
                    "Type items directly from the weekly circular or store visit.</div>")

            with st.form(key=f"manual_form_{chain}", clear_on_submit=True):
                f1, f2, f3 = st.columns([3, 1.5, 1.5])
                with f1:
                    item_name = st.text_input("Item name", placeholder="e.g. Chicken Breast, Boneless Skinless",
                                              label_visibility="collapsed")
                with f2:
                    item_cat  = st.selectbox("Category", options=CATEGORIES, label_visibility="collapsed")
                with f3:
                    item_unit = st.selectbox("Unit", options=UNITS, label_visibility="collapsed")

                f4, f5, f6 = st.columns([1.5, 1.5, 3])
                with f4:
                    sale_price = st.number_input("Sale price ($)", min_value=0.0, max_value=500.0,
                                                 step=0.01, format="%.2f")
                with f5:
                    reg_price  = st.number_input("Regular price ($)", min_value=0.0, max_value=500.0,
                                                 step=0.01, format="%.2f",
                                                 help="Optional — calculates % savings in the Ledger")
                with f6:
                    item_allergens = st.multiselect("Allergens (if any)", options=ALLERGENS)

                submitted = st.form_submit_button("＋ Add item", type="primary", use_container_width=True)
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

            store_items = [m for m in st.session_state.get("manual_items", []) if m["store"] == chain]
            if store_items:
                st.html(f"<div style='font-size:0.78rem;font-weight:700;color:#1E5C32;"
                        f"margin-bottom:6px;margin-top:8px;'>{len(store_items)} items entered</div>")
                for idx, item in enumerate(store_items):
                    ra, rb, rc, rd = st.columns([3, 1.5, 1.5, 0.8])
                    with ra:
                        st.html(f"<div style='font-size:0.88rem;color:#1A2E1D;padding:4px 0;'>"
                                f"<strong>{item['name']}</strong> "
                                f"<span style='color:#9AA8A0;font-size:0.75rem;'>· {item['category']}</span>"
                                f"</div>")
                    with rb:
                        st.html(f"<div style='font-size:0.88rem;color:#F28B30;font-weight:700;"
                                f"padding:4px 0;'>${item['sale_price']:.2f}/{item['unit']}</div>")
                    with rc:
                        if item.get("reg_price"):
                            pct = round((1 - item["sale_price"] / item["reg_price"]) * 100)
                            st.html(f"<div style='font-size:0.78rem;color:#5A7A62;padding:4px 0;'>"
                                    f"was ${item['reg_price']:.2f} "
                                    f"<span style='color:#3A8C4E;font-weight:600;'>↓{pct}%</span></div>")
                        else:
                            st.html("<div style='padding:4px 0;'>—</div>")
                    with rd:
                        full_idx = next((i for i, m in enumerate(st.session_state["manual_items"]) if m is item), None)
                        if full_idx is not None and st.button("✕", key=f"del_{chain}_{full_idx}"):
                            st.session_state["manual_items"].pop(full_idx)
                            _merge_manual_into_flyer(chain)
                            st.rerun()
            else:
                st.html("<div style='font-size:0.82rem;color:#9AA8A0;padding:8px 0;'>"
                        "No items yet — add your first item above, or upload the PDF circular.</div>")

        # ── TAB 2: PDF UPLOAD ─────────────────────────────────────────────────
        with tab_pdf:
            if dl_url:
                st.html(f"<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:8px;'>"
                        f"Download the weekly circular from "
                        f"<a href='{dl_url}' target='_blank' style='color:#3A8C4E;font-weight:600;'>"
                        f"{chain}'s website</a>, then upload it here.</div>")

            st.html("<div style='font-size:0.75rem;color:#9AA8A0;margin-bottom:8px;'>"
                    "⚠ PDF parsing is heuristic. Review what was extracted before running the engine — "
                    "add missing items via Manual Entry."
                    "</div>")

            uploaded = st.file_uploader(
                f"Upload {chain} circular (PDF)",
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
                        existing_manual = [c for c in flyer.get(chain, []) if getattr(c, "_manual", False)]
                        flyer[chain] = candidates + existing_manual
                        st.session_state["flyer_data"] = flyer
                        n = len(candidates)
                    else:
                        n, candidates = _load_pdf_flyer(chain, uploaded.read())

                if n:
                    st.success(f"✅ {n} items parsed from **{uploaded.name}**.")
                    # ── Parse review ─────────────────────────────────────────
                    st.html("<div style='font-size:0.8rem;font-weight:600;color:#1E5C32;"
                            "margin:10px 0 6px 0;'>Review parsed items — remove anything that looks wrong</div>")
                    st.html("<div style='font-size:0.75rem;color:#5A7A62;margin-bottom:8px;'>"
                            "Items marked ✕ will be removed before the engine runs. "
                            "Use Manual Entry to add anything that was missed."
                            "</div>")

                    # Use session state to track which parsed items to keep
                    review_key = f"pdf_review_{chain}"
                    if review_key not in st.session_state:
                        st.session_state[review_key] = {i: True for i in range(n)}

                    flyer_items = st.session_state.get("flyer_data", {}).get(chain, [])
                    pdf_items   = [c for c in flyer_items if not getattr(c, "_manual", False)]

                    for i, item in enumerate(pdf_items[:50]):  # cap at 50 for UI performance
                        name  = getattr(item, "name", "?") if not isinstance(item, dict) else item.get("name", "?")
                        price = getattr(item, "sale_price_per_unit", 0) if not isinstance(item, dict) else item.get("sale_price_per_unit", 0)
                        unit  = getattr(item, "unit", "each") if not isinstance(item, dict) else item.get("unit", "each")
                        cat   = getattr(item, "category", "other") if not isinstance(item, dict) else item.get("category", "other")
                        keep  = st.session_state[review_key].get(i, True)

                        ri_a, ri_b, ri_c, ri_d = st.columns([3, 1, 1, 0.5])
                        with ri_a:
                            color = "#1A2E1D" if keep else "#9AA8A0"
                            st.html(f"<div style='font-size:0.85rem;color:{color};padding:3px 0;'>"
                                    f"{'<s>' if not keep else ''}{name}{'</s>' if not keep else ''}"
                                    f" <span style='color:#9AA8A0;font-size:0.72rem;'>· {cat}</span>"
                                    f"</div>")
                        with ri_b:
                            st.html(f"<div style='font-size:0.85rem;color:#F28B30;padding:3px 0;'>"
                                    f"${price:.2f}/{unit}</div>")
                        with ri_c:
                            st.html("")
                        with ri_d:
                            if keep:
                                if st.button("✕", key=f"reject_{chain}_{i}", help="Remove this item"):
                                    st.session_state[review_key][i] = False
                                    # Remove from flyer_data
                                    flyer = st.session_state.get("flyer_data", {})
                                    kept  = [c for j, c in enumerate(
                                        [x for x in flyer.get(chain, []) if not getattr(x, "_manual", False)]
                                    ) if st.session_state[review_key].get(j, True)]
                                    manual = [c for c in flyer.get(chain, []) if getattr(c, "_manual", False)]
                                    flyer[chain] = kept + manual
                                    st.session_state["flyer_data"] = flyer
                                    st.rerun()

                    if n > 50:
                        st.caption(f"Showing first 50 of {n} items. All {n} are loaded into the engine.")
                else:
                    st.warning(
                        "Parser returned 0 items — the PDF format may not be supported yet. "
                        "Switch to Manual Entry and type in the key sale items.",
                        icon="⚠️",
                    )


# ── Item drill-down (triggered by "View items" on API stores) ─────────────────
view_store = st.session_state.pop("_view_store", None)
if view_store:
    flyer_items = st.session_state.get("flyer_data", {}).get(view_store, [])
    if flyer_items:
        st.divider()
        st.markdown(f"**{view_store} — all items loaded this week** ({len(flyer_items)} total)")
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
with st.expander("✨ Load a sample week of Charlottesville prices (for demo only)", expanded=False):
    st.caption(
        "Pre-loads realistic Kroger Barracks Road + Food Lion Pantops sale prices "
        "for the week of May 11, 2026. Use this to walk through the full flow before "
        "you have real flyer data. Do not use this week in your actual Found Money ledger."
    )
    if st.button("Load sample week", key="load_demo"):
        try:
            from app.data.sample_data import load_all_demo_data
            demo = load_all_demo_data()
            raw_grocers = demo["grocers"]
            norm_grocers = []
            for g in raw_grocers:
                src = g.get("source") or ("api" if g.get("source_type") == "api" else "manual_pdf")
                norm_grocers.append({
                    "chain":      g.get("chain") or g.get("name", "?"),
                    "location":   g.get("location", ""),
                    "source":     src,
                    "rewards":    g.get("rewards", False),
                    "delivery":   g.get("delivery", False),
                    "is_primary": g.get("is_primary", False),
                })
            raw_flyer = demo["flyer_data"]
            if "stores" in raw_flyer:
                norm_flyer = {}
                for _sid, _sdata in raw_flyer["stores"].items():
                    _display = _sdata.get("store_name", _sid)
                    norm_flyer[_display] = _sdata.get("items", [])
            else:
                norm_flyer = raw_flyer
            st.session_state["grocers"]        = norm_grocers
            st.session_state["flyer_data"]     = norm_flyer
            st.session_state["plan"]           = demo["plan"]
            st.session_state["ledger_history"] = demo["ledger_history"]
            st.session_state["active_week"]    = demo["active_week"]
            st.success("Sample prices loaded! Scroll down to run the engine.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not load demo data: {e}")


st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# RUN THE ENGINE
# POC: Runs synchronously in the Streamlit request cycle. Fine for a
#      single-household demo. Will time out with large item pools (200+).
# PROD: Engine runs as a background task (Celery worker). User sees a
#       "Plan generating…" status screen. Results pushed via WebSocket or polling.
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
    f"⚙️ Run the engine — {len(all_candidates)} items loaded",
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
        n_meals = len(raw_plan.meals)

        plan_meals = []
        plan_total = 0.0
        for meal in raw_plan.meals:
            ing_list  = []
            meal_cost = 0.0
            for scored_ing in meal.ingredients:
                ing  = scored_ing.ingredient
                cost = ing.sale_price_per_unit
                ing_list.append({
                    "item":  ing.name,
                    "qty":   f"1 {ing.unit}",
                    "store": getattr(ing, "source_store", "—"),
                    "cost":  round(cost, 2),
                })
                meal_cost += cost
            plan_meals.append({
                "day":            meal.day,
                "name":           meal.name,
                "gluten_free":    False,
                "allergen_notes": "",
                "best_store":     "—",
                "ingredients":    ing_list,
                "meal_cost":      round(meal_cost, 2),
            })
            plan_total += meal_cost

        total_servings = n_meals * household.servings_per_meal
        single_est     = round(plan_total * 1.18, 2)
        hf_equiv       = round(total_servings * 9.99, 2)

        st.session_state["plan"] = {
            "week":     st.session_state["active_week"],
            "servings": household.servings_per_meal,
            "meals":    plan_meals,
            "totals": {
                "whollyfare_plan":   round(plan_total, 2),
                "single_store_best": single_est,
                "hellofresh_equiv":  hf_equiv,
                "found_money":       round(single_est - plan_total, 2),
                "vs_hellofresh":     round(hf_equiv - plan_total, 2),
            },
        }

    n_passed   = len(result.passed)
    n_rejected = len(result.rejected)
    st.success(
        f"✅  {n_meals} dinners planned · "
        f"{n_passed} ingredients cleared · "
        f"{n_rejected} rejected by safety rules."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/3_Plan.py",          label="→ Review this week's plan", icon="🍽️")
    with c2:
        st.page_link("pages/4_Sunday_BuyOff.py", label="→ Go straight to Buy-Off",  icon="✅")
