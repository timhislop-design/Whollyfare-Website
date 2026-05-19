"""
2_Grocer_Hub.py — Grocer Data Hub
===================================
Weekly price data entry for all configured stores.

Supports three data paths (in order of reliability for the POC):
  1. Manual item entry  — type items in directly; always works; investor-demo safe
  2. PDF upload         — parse Food Lion / Kroger circulars automatically
  3. Kroger API         — live pull when credentials are available

POC vs. PRODUCTION
-------------------
POC:  Data lives in Streamlit session_state. Cleared on browser refresh.
      Manual entry is the primary path for Charlottesville demo weeks.
PROD: Items persist to PostgreSQL (user_id + week_id + store_id foreign keys).
      PDF parsing runs in a background worker (Celery / Lambda). Kroger API
      is the primary path; PDF/manual are fallbacks.
"""

import sys
import json
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

# ── Ensure manual_items key exists ────────────────────────────────────────────
# POC: plain list of dicts in session_state.
# PROD: fetched from DB on page load, filtered by user_id + active_week.
if "manual_items" not in st.session_state:
    st.session_state["manual_items"] = []

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Grocer Hub",
    "Load this week's prices — type items in, upload a circular PDF, or pull from Kroger.",
)


# ── Setup stepper ─────────────────────────────────────────────────────────────
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
# CHARLOTTESVILLE STORE PRESETS
# POC: One-click to pre-configure the four stores Tim shops week to week.
# PROD: User configures stores via a proper onboarding flow backed by a
#       store registry (chain + location_id from grocer API directories).
# ══════════════════════════════════════════════════════════════════════════════
CVILLE_STORES = [
    {
        "chain":      "Kroger",
        "location":   "Barracks Road, Charlottesville VA 22903",
        "source":     "manual_pdf+api",
        "rewards":    True,
        "delivery":   False,
        "is_primary": True,
        "flyer_url":  "https://www.kroger.com/weeklyad",
    },
    {
        "chain":      "Food Lion",
        "location":   "Pantops Mountain, Charlottesville VA 22911",
        "source":     "manual_pdf",
        "rewards":    True,
        "delivery":   False,
        "is_primary": False,
        "flyer_url":  "https://stores.foodlion.com",
    },
    {
        "chain":      "Aldi",
        "location":   "Rio Road, Charlottesville VA 22901",
        "source":     "manual_pdf",
        "rewards":    False,
        "delivery":   False,
        "is_primary": False,
        "flyer_url":  "https://www.aldi.us/en/weekly-specials/",
    },
    {
        "chain":      "Harris Teeter",
        "location":   "Barracks Road, Charlottesville VA 22903",
        "source":     "manual_pdf",
        "rewards":    True,
        "delivery":   True,
        "is_primary": False,
        "flyer_url":  "https://www.harristeeter.com/weeklyad",
    },
]

grocers = st.session_state.get("grocers", [])
existing_chains = {g.get("chain", "").lower() for g in grocers}
new_stores = [s for s in CVILLE_STORES if s["chain"].lower() not in existing_chains]

if new_stores:
    with st.expander("📍 Quick setup: add your Charlottesville stores", expanded=not grocers):
        st.caption(
            "These are the four stores within ten minutes of downtown Charlottesville. "
            "Add whichever ones you shop. You can add others manually below."
        )
        cols = st.columns(len(new_stores))
        for col, store in zip(cols, new_stores):
            with col:
                src_label = "API + PDF" if store["source"] == "manual_pdf+api" else "PDF upload"
                reward_str = "🎟 Rewards" if store["rewards"] else ""
                delivery_str = " · 🚚 Delivery" if store["delivery"] else ""
                primary_str = " · ⭐ Primary" if store["is_primary"] else ""
                st.html(f"""
                <div style='background:white;border:1px solid #D8EDD0;border-top:3px solid #3A8C4E;
                            border-radius:8px;padding:14px 12px;min-height:110px;'>
                  <div style='font-weight:700;color:#1E5C32;font-size:0.95rem;'>{store['chain']}</div>
                  <div style='font-size:0.75rem;color:#5A7A62;margin-top:3px;'>{store['location']}</div>
                  <div style='font-size:0.72rem;color:#9AA8A0;margin-top:6px;'>
                    {src_label}{reward_str}{delivery_str}{primary_str}
                  </div>
                </div>
                """)
                if st.button(f"Add {store['chain']}", key=f"preset_{store['chain']}", use_container_width=True):
                    grocers.append({k: v for k, v in store.items() if k != "flyer_url"})
                    st.session_state["grocers"] = grocers
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# WEEK SELECTOR + STATUS
# ══════════════════════════════════════════════════════════════════════════════
col_w, col_status, col_pull = st.columns([2, 2, 1])
with col_w:
    import datetime
    active_week = st.date_input(
        "Planning week",
        value=datetime.date.fromisoformat(st.session_state["active_week"]),
        label_visibility="collapsed",
    )
    st.session_state["active_week"] = active_week.isoformat()

loaded  = state.stores_loaded_this_week()
grocers = st.session_state.get("grocers", [])

with col_status:
    total_items = state.total_items_loaded()
    manual_count = len(st.session_state.get("manual_items", []))
    if len(loaded) == 0 and manual_count == 0:
        st.html('<span class="pill pill-miss">⚠ No prices loaded yet</span>')
    elif len(loaded) < len(grocers):
        st.html(
            f'<span class="pill pill-warn">⚠ {len(loaded)} of {len(grocers)} stores loaded</span>')
    else:
        st.html(
            f'<span class="pill pill-ok">✓ {total_items} items across {len(loaded)} stores</span>')

with col_pull:
    _pull_all_api = st.button("Pull API stores", use_container_width=True)

# Summary metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stores loaded",    len(loaded))
c2.metric("Items loaded",     state.total_items_loaded())
c3.metric("Manual entries",   len(st.session_state.get("manual_items", [])))
c4.metric("API connected",    sum(1 for g in grocers if g.get("source") in ("api", "manual_pdf+api")))

st.divider()


# ── Add store (sidebar) ───────────────────────────────────────────────────────
with st.sidebar:
    st.html("### Configured stores")
    for g in grocers:
        src  = g.get("source", "manual_pdf")
        icon = "🔗" if "api" in src else "📄"
        st.caption(f"{icon} {g.get('chain','?')}")
    st.divider()
    with st.expander("＋ Add a store"):
        new_chain  = st.text_input("Store name", placeholder="e.g. Wegmans", key="new_chain")
        new_loc    = st.text_input("Location / zip", placeholder="Charlottesville VA", key="new_loc")
        new_source = st.selectbox(
            "Data source",
            options=["manual_pdf", "api", "manual_pdf+api"],
            format_func=lambda x: {
                "manual_pdf":     "PDF upload (manual)",
                "api":            "API (auto-pull)",
                "manual_pdf+api": "PDF + partial API",
            }[x],
            key="new_source",
        )
        new_rewards  = st.checkbox("Loyalty/rewards enrolled", key="new_rewards")
        new_delivery = st.checkbox("Prefer delivery", key="new_delivery")
        new_primary  = st.checkbox("Set as primary store", key="new_primary")
        if st.button("Add store", type="primary"):
            if new_chain.strip():
                if new_primary:
                    for g in grocers:
                        g["is_primary"] = False
                grocers.append({
                    "chain":      new_chain.strip(),
                    "location":   new_loc.strip(),
                    "source":     new_source,
                    "rewards":    new_rewards,
                    "delivery":   new_delivery,
                    "is_primary": new_primary,
                })
                st.session_state["grocers"] = grocers
                st.rerun()


if not grocers:
    st.info("No stores configured yet. Use the presets above or the sidebar to add your first store.", icon="🏪")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _chain_name(g: dict) -> str:
    return g.get("chain") or g.get("name", "?")

def _source(g: dict) -> str:
    return g.get("source") or g.get("source_type", "manual_pdf")

def _status_badge(chain: str) -> str:
    if chain in loaded:
        count = len(st.session_state["flyer_data"].get(chain, []))
        manual = sum(1 for m in st.session_state.get("manual_items", []) if m["store"] == chain)
        parts = []
        if count:   parts.append(f"{count} from circular")
        if manual:  parts.append(f"{manual} manual")
        label = " · ".join(parts) if parts else f"{count} items"
        return f'<span class="pill pill-ok">✓ {label}</span>'
    manual = sum(1 for m in st.session_state.get("manual_items", []) if m["store"] == chain)
    if manual:
        return f'<span class="pill pill-warn">⚠ {manual} manual only — no circular</span>'
    return '<span class="pill pill-miss">⚠ No data</span>'


def _manual_items_as_candidates(store: str) -> list[IngredientCandidate]:
    """Convert session manual_items for a store into IngredientCandidate objects.

    POC: Reads from session_state list. Allergen data is user-declared — not USDA verified.
    PROD: Fetch from DB. Run USDA FoodData Central enrichment async after entry.
          Flag items that lack USDA FDC ID with a 'needs-enrichment' tag.
    """
    out = []
    for item in st.session_state.get("manual_items", []):
        if item["store"] != store:
            continue
        out.append(IngredientCandidate(
            name=item["name"],
            usda_fdc_id=None,               # PROD: lookup via USDA FDC API
            allergens=item.get("allergens", []),
            nutrition={},                    # PROD: populated by USDA enricher
            sale_price_per_unit=item["sale_price"],
            unit=item["unit"],
            standard_unit_weight_g=100.0,    # PROD: from USDA FDC portion data
            category=item["category"],
            tags=item.get("tags", []),
        ))
    return out


def _merge_manual_into_flyer(store: str):
    """Push manual entries for `store` into flyer_data so the engine sees them.

    Call after any manual add/delete to keep flyer_data current.
    """
    flyer = st.session_state.get("flyer_data", {})
    pdf_items = [c for c in flyer.get(store, [])
                 if not getattr(c, "_manual", False)]  # keep PDF-parsed items
    manual = _manual_items_as_candidates(store)
    # tag each manual candidate so we can strip them on re-merge
    for c in manual:
        c._manual = True  # type: ignore[attr-defined]
    flyer[store] = pdf_items + manual
    st.session_state["flyer_data"] = flyer


def _load_pdf_flyer(chain: str, pdf_bytes: bytes) -> int:
    """Run the chain-specific PDF parser.

    POC: pdfplumber heuristic regex for Food Lion; generic for others.
    PROD: Each chain has a trained parser (pdfplumber + regex rules per chain layout).
          Food Lion, Kroger, Aldi, Harris Teeter all have distinct PDF formats.
          Parser accuracy is monitored; low-confidence items are flagged for human review.
          Long-term: switch to grocer APIs entirely and retire PDF parsing.
    """
    ingestor = FlyerIngestor()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)
    try:
        if "food lion" in chain.lower():
            from integrations.food_lion.parser import FoodLionParser
            parser = FoodLionParser(flyer_week=st.session_state["active_week"])
            result = parser.parse_pdf(tmp_path)
            import os
            usda_key = os.environ.get("USDA_API_KEY", "")
            if usda_key:
                from integrations.food_lion.usda_enricher import USDAEnricher
                USDAEnricher(api_key=usda_key).enrich(result)
            out = Path("app/data/flyers") / f"food_lion_{st.session_state['active_week']}.json"
            parser.save(result, out)
            candidates = ingestor.from_json(out)
        else:
            candidates = ingestor.from_pdf(tmp_path)
        flyer = st.session_state.get("flyer_data", {})
        # Preserve manual items already entered for this store
        existing_manual = [c for c in flyer.get(chain, [])
                           if getattr(c, "_manual", False)]
        flyer[chain] = candidates + existing_manual
        st.session_state["flyer_data"] = flyer
        return len(candidates)
    except Exception as e:
        st.error(f"PDF parse failed for {chain}: {e}")
        return 0
    finally:
        tmp_path.unlink(missing_ok=True)


def _pull_kroger(chain: str, location_id: str) -> int:
    """Pull live sale data from the Kroger Developer API.

    POC: Requires KROGER_CLIENT_ID + KROGER_CLIENT_SECRET env vars.
         Not expected to work in a demo without credentials.
    PROD: OAuth2 client_credentials flow. Credentials stored in AWS Secrets Manager.
          Rate limit: 10,000 calls/day on Kroger's free tier; production tier negotiated.
          Location ID resolved from user's zip code via Kroger Locations API.
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
        ingestor = FlyerIngestor()
        candidates = ingestor.from_json(out)
        flyer = st.session_state.get("flyer_data", {})
        flyer[chain] = candidates
        st.session_state["flyer_data"] = flyer
        return len(candidates)
    except Exception as e:
        st.error(f"Kroger pull failed: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# STORE CARDS
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIES = ["produce", "protein", "dairy", "grain", "legume", "pantry", "bakery", "frozen", "beverage", "other"]
UNITS       = ["lb", "oz", "each", "pkg", "bunch", "bag", "dozen", "gal", "qt", "can", "jar", "box"]
ALLERGENS   = ["peanuts", "tree_nuts", "milk", "eggs", "wheat", "soy", "fish", "shellfish",
               "sesame", "mustard", "celery", "sulphites"]

FLYER_HINTS = {
    "kroger":        "https://www.kroger.com/weeklyad",
    "food lion":     "https://stores.foodlion.com",
    "aldi":          "https://www.aldi.us/en/weekly-specials/",
    "harris teeter": "https://www.harristeeter.com/weeklyad",
    "walmart":       "https://www.walmart.com/store/finder",
    "giant":         "https://stores.giantfood.com",
    "wegmans":       "https://www.wegmans.com/weeklyad",
}

api_stores    = [g for g in grocers if _source(g) in ("api", "manual_pdf+api")]
manual_stores = [g for g in grocers if _source(g) not in ("api",)]

# ── API-connected stores ──────────────────────────────────────────────────────
if api_stores:
    st.markdown(
        "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
        "color:#3A8C4E;margin-bottom:10px;'>API-connected stores</div>")
    for g in api_stores:
        chain  = _chain_name(g)
        is_ok  = chain in loaded
        with st.container(border=True):
            col_icon, col_info, col_act = st.columns([0.5, 3, 2])
            with col_icon:
                st.html("🔗" if is_ok else "⚡")
            with col_info:
                st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}")
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

        # Manual entry inline for API stores too (fallback when API is down)
        _render_manual_entry = True

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
    st.html(
        "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
        "color:#3A8C4E;margin-bottom:10px;'>Stores — manual entry &amp; PDF upload</div>")

for g in manual_stores:
    chain  = _chain_name(g)
    is_ok  = chain in loaded or any(m["store"] == chain for m in st.session_state.get("manual_items", []))
    dl_url = FLYER_HINTS.get(chain.lower(), "")

    with st.container(border=True):
        # ── Store header row ─────────────────────────────────────────────────
        col_icon, col_info, col_link = st.columns([0.5, 4, 1.5])
        with col_icon:
            st.html("✅" if is_ok else "📋")
        with col_info:
            st.markdown(f"**{chain}** &nbsp; {_status_badge(chain)}")
            loc = g.get("location", "")
            if g.get("is_primary"): loc += "  · ⭐ Primary"
            st.caption(loc)
        with col_link:
            if dl_url:
                st.html(
                    f"<a href='{dl_url}' target='_blank' style='font-size:0.78rem;"
                    f"color:#3A8C4E;font-weight:600;text-decoration:none;'>↗ Weekly circular</a>")

        # ── Two-tab interface: Manual Entry | PDF Upload ──────────────────────
        tab_manual, tab_pdf = st.tabs(["✏️ Manual entry", "📄 PDF upload"])

        # ── TAB 1: MANUAL ENTRY ───────────────────────────────────────────────
        with tab_manual:
            st.html(
                "<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:10px;'>"
                "Type items directly from the weekly circular or store visit. "
                "These merge with any PDF-parsed items when the engine runs."
                "</div>")

            # Entry form
            with st.form(key=f"manual_form_{chain}", clear_on_submit=True):
                f1, f2, f3 = st.columns([3, 1.5, 1.5])
                with f1:
                    item_name = st.text_input(
                        "Item name",
                        placeholder="e.g. Chicken Breast, Boneless Skinless",
                        label_visibility="collapsed",
                    )
                with f2:
                    item_cat = st.selectbox(
                        "Category",
                        options=CATEGORIES,
                        label_visibility="collapsed",
                    )
                with f3:
                    item_unit = st.selectbox(
                        "Unit",
                        options=UNITS,
                        label_visibility="collapsed",
                    )

                f4, f5, f6 = st.columns([1.5, 1.5, 3])
                with f4:
                    sale_price = st.number_input(
                        "Sale price ($)",
                        min_value=0.0, max_value=500.0,
                        step=0.01, format="%.2f",
                    )
                with f5:
                    reg_price = st.number_input(
                        "Regular price ($)",
                        min_value=0.0, max_value=500.0,
                        step=0.01, format="%.2f",
                        help="Optional — used to calculate % savings in the Ledger",
                    )
                with f6:
                    item_allergens = st.multiselect(
                        "Allergens (if any)",
                        options=ALLERGENS,
                        label_visibility="visible",
                    )

                submitted = st.form_submit_button("＋ Add item", type="primary", use_container_width=True)
                if submitted and item_name.strip():
                    new_item = {
                        "store":        chain,
                        "name":         item_name.strip(),
                        "category":     item_cat,
                        "unit":         item_unit,
                        "sale_price":   round(sale_price, 2),
                        "reg_price":    round(reg_price, 2) if reg_price > 0 else None,
                        "allergens":    item_allergens,
                        "tags":         [],
                        "week":         st.session_state["active_week"],
                    }
                    st.session_state["manual_items"].append(new_item)
                    _merge_manual_into_flyer(chain)
                    st.success(f"Added: {item_name.strip()} @ ${sale_price:.2f}/{item_unit}")
                    st.rerun()
                elif submitted:
                    st.warning("Item name is required.")

            # Items table for this store
            store_items = [m for m in st.session_state.get("manual_items", [])
                           if m["store"] == chain]
            if store_items:
                st.html(
                    f"<div style='font-size:0.78rem;font-weight:700;color:#1E5C32;"
                    f"margin-bottom:6px;margin-top:8px;'>{len(store_items)} items entered</div>")
                for idx, item in enumerate(store_items):
                    row_a, row_b, row_c, row_d = st.columns([3, 1.5, 1.5, 0.8])
                    with row_a:
                        st.html(
                            f"<div style='font-size:0.88rem;color:#1A2E1D;padding:4px 0;'>"
                            f"<strong>{item['name']}</strong> "
                            f"<span style='color:#9AA8A0;font-size:0.75rem;'>· {item['category']}</span>"
                            f"</div>")
                    with row_b:
                        st.html(
                            f"<div style='font-size:0.88rem;color:#F28B30;font-weight:700;"
                            f"padding:4px 0;'>${item['sale_price']:.2f}/{item['unit']}</div>")
                    with row_c:
                        if item.get("reg_price"):
                            savings_pct = round((1 - item["sale_price"] / item["reg_price"]) * 100)
                            st.html(
                                f"<div style='font-size:0.78rem;color:#5A7A62;padding:4px 0;'>"
                                f"was ${item['reg_price']:.2f} "
                                f"<span style='color:#3A8C4E;font-weight:600;'>↓{savings_pct}%</span>"
                                f"</div>")
                        else:
                            st.html("<div style='padding:4px 0;'>—</div>")
                    with row_d:
                        # Find the actual index in the full manual_items list
                        full_idx = next(
                            (i for i, m in enumerate(st.session_state["manual_items"])
                             if m is item), None
                        )
                        if full_idx is not None:
                            if st.button("✕", key=f"del_{chain}_{full_idx}", help="Remove this item"):
                                st.session_state["manual_items"].pop(full_idx)
                                _merge_manual_into_flyer(chain)
                                st.rerun()
            else:
                st.html(
                    "<div style='font-size:0.82rem;color:#9AA8A0;padding:8px 0;'>"
                    "No items yet — add your first item above, or upload the PDF circular."
                    "</div>")

        # ── TAB 2: PDF UPLOAD ─────────────────────────────────────────────────
        with tab_pdf:
            if dl_url:
                st.html(
                    f"<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:8px;'>"
                    f"Download the weekly circular from "
                    f"<a href='{dl_url}' target='_blank' style='color:#3A8C4E;font-weight:600;'>"
                    f"{chain}'s website</a>, then upload the PDF here."
                    f"</div>")

            st.html(
                "<div style='font-size:0.75rem;color:#9AA8A0;margin-bottom:8px;'>"
                "⚠ PDF parsing is heuristic and may miss items. Use Manual Entry as a fallback "
                "or to add items the parser skipped."
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
                            n = len(ingestor.from_json(Path(tmp.name)))
                            flyer = st.session_state.get("flyer_data", {})
                            existing_manual = [c for c in flyer.get(chain, [])
                                               if getattr(c, "_manual", False)]
                            flyer[chain] = ingestor.from_json(Path(tmp.name)) + existing_manual
                            st.session_state["flyer_data"] = flyer
                    else:
                        n = _load_pdf_flyer(chain, uploaded.read())
                if n:
                    st.success(f"✅ {n} items parsed from {uploaded.name}. Review in Manual Entry tab.")
                    st.rerun()
                else:
                    st.warning(
                        "Parser returned 0 items — the PDF format may not be supported. "
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
                rows.append({
                    "Source":    "✏️ manual" if is_manual else "📄 circular",
                    "Name":      c.get("name", "?"),
                    "Category":  c.get("category", "—"),
                    "Sale price": f"${price:.2f}/{c.get('unit','?')}",
                    "Allergens": ", ".join(c.get("allergens", [])) or "—",
                })
            else:
                rows.append({
                    "Source":    "✏️ manual" if is_manual else "📄 circular",
                    "Name":      c.name,
                    "Category":  c.category,
                    "Sale price": f"${c.sale_price_per_unit:.2f}/{c.unit}",
                    "Allergens": ", ".join(c.allergens) or "—",
                })
        st.dataframe(rows, use_container_width=True, height=320)


# ── Demo load (tucked away — for investor demo if no real data yet) ───────────
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
# POC: Runs synchronously in the Streamlit request/response cycle. Fine for a
#      single-household demo. Will time out with large item pools (200+).
# PROD: Engine runs as a background task (Celery worker). User sees a "Plan
#      generating…" status screen. Results pushed via WebSocket or polling.
# ══════════════════════════════════════════════════════════════════════════════
all_candidates = [c for v in st.session_state.get("flyer_data", {}).values() for c in v]
can_run = len(all_candidates) > 0 and st.session_state.get("household") is not None

if not can_run:
    reasons = []
    if not st.session_state.get("household"):
        reasons.append("set up your household profile first")
    if not all_candidates:
        reasons.append("add at least one item (Manual Entry or PDF upload)")
    st.info(f"Almost ready — {' and '.join(reasons)}.", icon="💡")
    if not st.session_state.get("household"):
        if st.button("→ Go to Household Setup", type="primary"):
            st.switch_page("pages/1_Household.py")

run_btn = st.button(
    f"⚙️ Run the engine → ({len(all_candidates)} items to process)",
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
        n_meals  = len(raw_plan.meals)

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

        plan_dict = {
            "week":     st.session_state["active_week"],
            "servings": household.servings_per_meal,
            "meals":    plan_meals,
            "totals": {
                "whollyfare_plan":    round(plan_total, 2),
                "single_store_best":  single_est,
                "hellofresh_equiv":   hf_equiv,
                "found_money":        round(single_est - plan_total, 2),
                "vs_hellofresh":      round(hf_equiv - plan_total, 2),
            },
        }
        st.session_state["plan"] = plan_dict

    n_passed   = len(result.passed)
    n_rejected = len(result.rejected)
    st.success(
        f"✅  {n_meals} dinners planned · "
        f"{n_passed} ingredients cleared · "
        f"{n_rejected} rejected by safety rules.",
    )
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("pages/3_Plan.py",          label="→ Review this week's plan", icon="🍽️")
    with c2:
        st.page_link("pages/4_Sunday_BuyOff.py", label="→ Go straight to Buy-Off",  icon="✅")
