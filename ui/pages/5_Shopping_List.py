"""5_Shopping_List.py -- Shopping list by store with delivery-ready export.

Design bar: usable on a phone in a grocery store aisle AND ready for Phase 3
delivery app API integration (Kroger, Instacart, Shipt).

Architecture
------------
The canonical shopping_cart is a dict stored in session_state:
  {store_name: [CartItem, ...], "Unassigned": [CartItem, ...]}

A CartItem is a plain dict:
  {
    name     : str    -- display name
    qty      : str    -- "2 lb", "1 bunch", "8 oz"
    cost     : float  -- 0.0 for unpriced items
    source   : str    -- "sale" | "recipe_extra" | "pantry_restock" | "manual"
    category : str    -- produce | protein | dairy | grain | pantry | other
    moveable : bool   -- user can reassign this item to another store
  }

The cart is built once from the plan and persists in session_state until the
active_week changes or the user triggers a rebuild. User overrides (add / move /
remove) mutate the session_state cart directly.

Phase 3 delivery hooks (see _to_delivery_payload below):
  Kroger:    PUT /cart/add  with product UPCs (matched via Kroger API search)
  Instacart: POST /fulfillment/v2/fulfillment_orders  (Instacart Platform API)
  Shipt:     POST /lists/{list_id}/items  (Shipt API)

Pilot vs. Production
---------------------
Pilot:  Cart rebuilt from plan on each new week. User overrides held in
        session_state -- cleared on browser refresh.
        Export: formatted text block + per-store CSV (copy-paste into any app).
PROD:   Cart persisted to DB per household + week. Overrides synced across devices.
        Phase 3: direct API integration to push cart to delivery services.
        PWA manifest so the list lives on the home screen.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Shopping List - WhollyFare", page_icon="\U0001f6cd", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("Shopping List", "Everything you need this week, organised by store.")

# ── Subscription tier gate ────────────────────────────────────────────────────
# Free users who have completed their 7-day trial see this upsell card instead
# of the page content. Trial users and paid users pass through silently.
# POC: tier checked from session state (cached at sign-in). No DB hit.
# PROD: same — tier is immutable within a session; changes take effect on next sign-in.
if not state.has_access("meal_planner"):
    style.page_header("Shopping List", "")
    st.html("""
    <div style='max-width:520px;margin:32px auto 0;background:white;border-radius:18px;
                border-top:5px solid #1E5C32;box-shadow:0 4px 32px rgba(30,92,50,0.10);
                padding:36px 36px 28px;text-align:center;'>
      <div style='font-size:2.2rem;margin-bottom:12px;'>🔒</div>
      <div style='font-size:1.3rem;font-weight:800;color:#1A2E1D;margin-bottom:8px;'>
        Shopping List — Meal Planner feature
      </div>
      <div style='font-size:0.93rem;color:#5A7A62;line-height:1.65;margin-bottom:24px;'>
        Your approved plan becomes a phone-ready shopping list, organised by store and category. Upgrade to Meal Planner to unlock your weekly shopping list.
      </div>
      <div style='background:#F4FAF5;border:1px solid #D0EDD8;border-radius:12px;
                  padding:16px 20px;margin-bottom:24px;text-align:left;'>
        <div style='font-size:0.75rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.09em;color:#3A8C4E;margin-bottom:8px;'>
          Meal Planner — $7/month
        </div>
        <div style='font-size:0.85rem;color:#4A5568;line-height:1.6;'>
          ✓ &nbsp;Weekly 5-dinner plan built from this week's sale prices<br>
          ✓ &nbsp;Sunday Buy-Off — one tap to approve and lock in savings<br>
          ✓ &nbsp;Shopping list organised by store, ready on your phone<br>
          ✓ &nbsp;Found Money tracked every week
        </div>
      </div>
    </div>
    """)
    _u1, _u2, _u3 = st.columns([1, 2, 1])
    with _u2:
        if st.button("See plans & pricing →", type="primary", use_container_width=True,
                     key="upsell_cta_shopping_list"):
            st.switch_page("Home.py")
    st.stop()


state.log_activity("shopping_list_viewed", page="Shopping List")

# -- Setup check --
plan = st.session_state.get("plan")
if not plan:
    st.warning("No plan yet. Generate a plan first.", icon="⚠️")
    st.page_link("pages/2_Grocer_Hub.py", label="-> Go to Grocer Hub", icon="\U0001f3ea")
    st.stop()

STORE_NAMES = {
    "kroger_palmyra":           "Kroger",
    "food_lion_palmyra":        "Food Lion",
    "aldi_rio":                 "Aldi",
    "harris_teeter_barracks":   "Harris Teeter",
    "Kroger":                   "Kroger",
    "Food Lion":                "Food Lion",
    "Aldi":                     "Aldi",
    "Harris Teeter":            "Harris Teeter",
}

ALL_STORES = list(dict.fromkeys(STORE_NAMES.values()))  # ordered, unique

# Honor skipped meals from the Buy-Off. Only include approved / pending meals
# in the shopping list — skipped meals are excluded entirely.
# POC: skipped_indices set at lock-in time. PROD: meal_plan_meals table has status column.
_skipped_indices = set(plan.get("_skipped_indices", []))
meals    = [m for i, m in enumerate(plan["meals"]) if i not in _skipped_indices]
totals   = plan["totals"]
week     = plan["week"]
servings = plan["servings"]

if _skipped_indices:
    _n_skipped = len(_skipped_indices)
    st.html(
        f"<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:6px;"
        f"padding:8px 14px;margin-bottom:12px;font-size:0.82rem;color:#5A3A00;'>"
        f"⏭ {_n_skipped} meal{'s' if _n_skipped != 1 else ''} skipped in Buy-Off — "
        f"their ingredients are excluded from this list.</div>"
    )

pantry       = state.pantry_items()
out_of_stock = st.session_state.get("pantry_out_of_stock", set())
weekly_regs  = st.session_state.get("weekly_regulars") or state.WEEKLY_REGULARS_DEFAULTS


# ==============================================================================
# CART BUILDER
# Builds the canonical shopping_cart from the plan. Only runs once per week
# (keyed on active_week). User overrides mutate the cart in session_state.
#
# Pilot: rebuilt on browser refresh (session_state is ephemeral).
# PROD:  persist cart to DB so overrides survive refresh and cross-device sync.
# ==============================================================================

def _combine_qty(base: str, add: str) -> str:
    """
    Numerically combine two qty strings when units match.
    "2 lb" + "2 lb" -> "4 lb".  Falls back to base if units differ or unparseable.
    Pilot: integer + simple fraction support. Phase 2: unit conversion (oz -> lb).
    """
    import re
    base = (base or "").strip()
    add  = (add  or "").strip()
    if not add or add == base:
        return base
    m1 = re.match(r'^([0-9]+\.?[0-9]*)\s*(.*)$', base)
    m2 = re.match(r'^([0-9]+\.?[0-9]*)\s*(.*)$', add)
    if m1 and m2 and m1.group(2).strip().lower() == m2.group(2).strip().lower():
        total = float(m1.group(1)) + float(m2.group(1))
        unit  = m1.group(2).strip()
        # Show as int if whole number
        total_str = str(int(total)) if total == int(total) else f"{total:g}"
        return (total_str + " " + unit).strip()
    return base  # can't combine cleanly — keep original


def _build_cart(plan, pantry, out_of_stock):
    """
    Build the canonical shopping cart from the current plan.

    Returns a dict: {store_name: [CartItem, ...], "Unassigned": [CartItem, ...]}.

    Sources ingested:
      1. Sale items (ingredients sourced from sale flyers via meal planner)
      2. Recipe extras (non-pantry ingredients not covered by sale items)
      3. Out-of-stock pantry restocks

    Weekly Regulars are NOT in the cart -- they are shown separately per the
    Sincere Strategy (separate cost line, not mixed into Found Money math).

    Phase 3: add a `store_product_id` field when matched via Kroger/Instacart
    search API so the delivery payload can reference items by SKU.
    """
    cart = {}  # {store: [CartItem]}

    # 1. Sale items — use the pre-deduplicated weekly_shopping basket built by
    # the plan page.  That basket allocates each ingredient once with its full
    # purchase price and total qty, regardless of how many meals share it.
    # Falling back to per-meal iteration (the old approach) caused chicken breast
    # to appear once per meal even when the same sale item was shared across all
    # chicken dishes.
    #
    # Pilot: category field not stored in weekly_shopping yet — defaults to "other".
    # Phase 2: add category to basket items so store sections sort correctly.
    sale_item_keys = set()
    for ws in plan.get("weekly_shopping", []):
        store_sid = ws.get("store", "")
        store     = STORE_NAMES.get(store_sid, store_sid) or "Unassigned"
        name      = ws.get("item", "")
        qty_str   = str(ws.get("qty_total", ""))
        cost      = float(ws.get("total_cost", 0.0))
        meals_ct  = ws.get("meals", 1)

        key = name.lower() + "|" + store
        sale_item_keys.add(key)
        cart.setdefault(store, []).append({
            "name":     name,
            "qty":      qty_str,
            "cost":     cost,
            "source":   "sale",
            "category": ws.get("category", "other"),
            "moveable": False,   # sale price is store-specific — moving loses the deal
            "_meals":   [f"{meals_ct} meals"] if meals_ct > 1 else [],
        })

    # 2. Recipe extras -- non-pantry ingredients not in the sale list
    sale_names_lower = {n.lower() for n in (
        item["name"] for items in cart.values() for item in items
    )}
    for meal in plan.get("meals", []):
        for ri in meal.get("recipe_ingredients", []):
            name      = ri.get("name", "")
            name_low  = name.lower().strip()
            is_pantry = ri.get("pantry_stable", False)

            # Skip pantry-stable unless out of stock
            if name_low in out_of_stock:
                pass  # needs buying this week
            elif is_pantry or name_low in pantry:
                continue

            # Skip if already in the sale list
            if any(name_low in sn or sn in name_low for sn in sale_names_lower):
                continue

            qty_str = (str(ri.get("qty", "")) + " " + str(ri.get("unit", ""))).strip()

            # Check if already added (multiple meals may need same extra)
            found = False
            for item in cart.get("Unassigned", []):
                if item["name"].lower() == name_low:
                    item["qty"] = _combine_qty(item["qty"], qty_str)
                    if meal.get("day") and meal["day"] not in item.get("_meals", []):
                        item.setdefault("_meals", []).append(meal["day"])
                    found = True
                    break
            if not found:
                cart.setdefault("Unassigned", []).append({
                    "name":     name,
                    "qty":      qty_str,
                    "cost":     0.0,
                    "source":   "recipe_extra",
                    "category": ri.get("category", "other"),
                    "moveable": True,   # user can assign to any store
                    "_meals":   [meal.get("day", "")] if meal.get("day") else [],
                })

    # 3. Out-of-stock pantry restocks not already captured above
    for oos in sorted(out_of_stock):
        already = any(
            item["name"].lower() == oos
            for items in cart.values()
            for item in items
        )
        if not already:
            cart.setdefault("Unassigned", []).append({
                "name":     oos.title(),
                "qty":      "restock",
                "cost":     0.0,
                "source":   "pantry_restock",
                "category": "pantry",
                "moveable": True,
                "_meals":   ["pantry restock"],
            })

    return cart


# -- Build or retrieve canonical cart ------------------------------------------
# Rebuild when week changes; otherwise use whatever is in session_state so
# user overrides (add/move/remove) persist across page interactions.
if "household_staples" not in st.session_state:
    st.session_state["household_staples"] = []

cart_week = st.session_state.get("_cart_week")
if cart_week != week or "shopping_cart" not in st.session_state:
    st.session_state["shopping_cart"] = _build_cart(plan, pantry, out_of_stock)
    st.session_state["_cart_week"] = week

cart = st.session_state["shopping_cart"]


# ==============================================================================
# DELIVERY PAYLOAD BUILDER
# Phase 3: transform cart into a format suitable for delivery API calls.
# For now this builds a structured dict -- wire to real API in Phase 3.
#
# PROD: match items to store product IDs via Kroger API search or Instacart
#       catalog lookup. Add UPCs so the delivery service can find exact products.
# ==============================================================================

def _to_delivery_payload(store: str) -> list[dict]:
    """
    Build a delivery-API-ready payload for one store's cart items.

    Phase 3 shape (Kroger cart API example):
      [{"upc": "...", "quantity": 2, "modality": "PICKUP"}, ...]

    Pilot: returns a structured list without UPCs (name-only).
    PROD:  resolve UPCs via Kroger API product search:
           GET /products?filter.term={name}&filter.locationId={store_location_id}
    """
    items = cart.get(store, [])
    return [
        {
            "name":     item["name"],
            "qty":      item["qty"],
            "category": item["category"],
            "cost_est": item["cost"],
            # PROD: add upc, store_product_id, modality (PICKUP | DELIVERY)
        }
        for item in items
    ]


# -- Progress ------------------------------------------------------------------
all_items  = [(store, item) for store, items in cart.items() for item in items]
total_items = len(all_items)

total_checked = sum(
    1 for store, item in all_items
    if st.session_state.get("chk_" + store + "_" + item["name"], False)
)

# -- Week header + progress bar ------------------------------------------------
st.html(
    "<div style='font-size:0.95rem;color:#3A8C4E;margin-bottom:4px;'>"
    "<strong>Week of " + week + "</strong> &nbsp;·&nbsp; "
    + str(total_items) + " items &nbsp;·&nbsp; "
    + str(len(meals)) + " dinners &nbsp;·&nbsp; "
    + str(servings) + " servings each"
    "</div>")

if total_items > 0:
    pct = int(total_checked / total_items * 100)
    st.progress(pct / 100, text=str(total_checked) + " of " + str(total_items) + " checked off")

st.divider()


# ==============================================================================
# HELPERS
# ==============================================================================

def _source_label(source: str) -> str:
    return {
        "sale":           "on sale",
        "recipe_extra":   "recipe",
        "pantry_restock": "restock",
        "manual":         "added by you",
    }.get(source, source)


def _render_item_row(store: str, item: dict, idx: int):
    """Render one cart item with checkbox, info, cost, and move/remove controls."""
    check_key = "chk_" + store + "_" + item["name"]
    checked   = st.session_state.get(check_key, False)
    name      = item["name"]
    qty       = item["qty"]
    cost      = item["cost"]
    source    = item["source"]
    moveable  = item.get("moveable", True)
    meals_str = ", ".join(m for m in item.get("_meals", []) if m)

    # Mobile-first: 2-column layout — large checkbox + all item info in one block
    col_chk, col_info = st.columns([1, 9])

    with col_chk:
        st.checkbox(label=name, value=checked, key=check_key,
                    label_visibility="collapsed")

    with col_info:
        now        = st.session_state.get(check_key, False)
        name_style = "text-decoration:line-through;color:#9AA8A0;" if now else "color:#1A2E1D;"
        meta_style = "color:#9AA8A0;" if now else "color:#5A7A62;"
        cost_style = "color:#9AA8A0;" if now else "color:#1E5C32;font-weight:700;"
        src_badge  = (" &nbsp;<span style='font-size:0.72rem;background:#E8F5E9;"
                      "color:#3A8C4E;padding:1px 6px;border-radius:3px;'>"
                      + _source_label(source) + "</span>") if source != "sale" else ""
        cost_str   = ("$" + "{:.2f}".format(cost)) if cost > 0 else ""
        meta_parts = []
        if qty:
            meta_parts.append(qty)
        if meals_str:
            meta_parts.append(meals_str)
        if cost_str:
            meta_parts.append("<span style='" + cost_style + "'>" + cost_str + "</span>")
        meta_line = "&nbsp;&middot;&nbsp;".join(meta_parts)
        st.html(
            "<div style='padding:6px 0;'>"
            "<div style='font-size:1rem;font-weight:600;" + name_style + "'>"
            + name + src_badge + "</div>"
            + ("<div style='font-size:0.82rem;" + meta_style + "'>" + meta_line + "</div>"
               if meta_line else "")
            + "</div>")

    # Move/remove controls — full width below the row for easy thumb access
    ctrl_key = "ctrl_" + store + "_" + name + "_" + str(idx)
    if moveable:
        other_stores = [s for s in ALL_STORES if s != store] + (
            ["Unassigned"] if store != "Unassigned" else []
        )
        move_options = ["move to a different store..."] + other_stores + ["remove"]
        choice = st.selectbox(
            label="move", options=move_options, index=0,
            key=ctrl_key, label_visibility="collapsed"
        )
        if choice != "move to a different store...":
            cart[store] = [i for i in cart.get(store, []) if i["name"] != name]
            if choice != "remove":
                item_copy = dict(item)
                item_copy["moveable"] = True
                cart.setdefault(choice, []).append(item_copy)
            st.session_state["shopping_cart"] = cart
            st.rerun()
    elif source == "manual":
        if st.button("Remove", key=ctrl_key, help="Remove this item",
                     use_container_width=True):
            cart[store] = [i for i in cart.get(store, []) if i["name"] != name]
            st.session_state["shopping_cart"] = cart
            st.rerun()

    st.html("<hr style='margin:0;border:none;border-top:1px solid #EEF3EE;'>")


def _add_item_form(store: str, form_key: str):
    """Inline form to add a manual item to a specific store's cart."""
    with st.form(form_key, clear_on_submit=True):
        c1, c2 = st.columns([6, 3])
        with c1:
            new_name = st.text_input("Item name", placeholder="e.g. Greek yogurt",
                                     label_visibility="collapsed")
        with c2:
            new_qty = st.text_input("Qty", placeholder="e.g. 32 oz",
                                    label_visibility="collapsed")
        add_btn = st.form_submit_button("+ Add item", use_container_width=True)
        if add_btn and new_name.strip():
            cart.setdefault(store, []).append({
                "name":     new_name.strip(),
                "qty":      new_qty.strip() or "1",
                "cost":     0.0,
                "source":   "manual",
                "category": "other",
                "moveable": True,
                "_meals":   [],
            })
            st.session_state["shopping_cart"] = cart
            st.rerun()


# ==============================================================================
# SECTION 1 -- SALE ITEMS BY STORE
# ==============================================================================
store_order = [s for s in ALL_STORES if s in cart and s != "Unassigned"]
other_stores_in_cart = [s for s in cart if s not in store_order and s != "Unassigned"]
store_order += other_stores_in_cart

for store in store_order:
    items       = cart.get(store, [])
    store_total = sum(i["cost"] for i in items)
    item_count  = len(items)
    store_chkd  = sum(1 for i in items
                      if st.session_state.get("chk_" + store + "_" + i["name"], False))
    all_done    = store_chkd == item_count and item_count > 0
    done_badge  = " done!" if all_done else (" " + str(store_chkd) + "/" + str(item_count))
    hdr_bg      = "#3A8C4E" if all_done else "#1E5C32"

    st.html(
        "<div style='background:" + hdr_bg + ";color:#FFFFFF;border-radius:8px 8px 0 0;"
        "padding:12px 18px;margin-top:20px;'>"
        "<span style='font-size:1.05rem;font-weight:700;'>" + store + "</span>"
        "<span style='font-size:0.82rem;color:#9FD9A8;margin-left:10px;'>"
        + str(item_count) + " items &nbsp;" + done_badge + "</span>"
        "<span style='float:right;font-size:0.9rem;font-weight:600;color:#D8EDD0;'>"
        "$" + "{:.2f}".format(store_total) + "</span></div>")

    for idx, item in enumerate(items):
        _render_item_row(store, item, idx)

    _add_item_form(store, "add_" + store.replace(" ", "_"))

    footer_label = ("All done at " + store) if all_done else (store + " subtotal")
    st.html(
        "<div style='background:#E3F4E8;border-radius:0 0 8px 8px;padding:10px 18px;"
        "display:flex;justify-content:space-between;align-items:center;"
        "border-top:2px solid #5DAA6A;margin-bottom:4px;'>"
        "<span style='font-size:0.85rem;color:#3A8C4E;'>"
        + ("done " if all_done else "") + footer_label + "</span>"
        "<span style='font-size:1rem;font-weight:700;color:#1E5C32;'>"
        "$" + "{:.2f}".format(store_total) + "</span></div>")

st.divider()


# ==============================================================================
# SECTION 2 -- UNASSIGNED (recipe extras + restocks)
# Items not tied to a sale flyer. User can assign to any store for delivery.
# Pilot: no store assigned. Phase 3: auto-match to nearest store via price API.
# ==============================================================================
unassigned = cart.get("Unassigned", [])
if unassigned:
    ua_chkd   = sum(1 for i in unassigned
                    if st.session_state.get("chk_Unassigned_" + i["name"], False))
    all_ua    = ua_chkd == len(unassigned)
    hdr_ua    = "#3A8C4E" if all_ua else "#5A7A62"
    st.html(
        "<div style='background:" + hdr_ua + ";color:#FFFFFF;border-radius:8px 8px 0 0;"
        "padding:12px 18px;margin-top:20px;'>"
        "<span style='font-size:1.05rem;font-weight:700;'>Also needed this week</span>"
        "<span style='font-size:0.82rem;color:#C8E6C9;margin-left:10px;'>"
        "Recipe ingredients &nbsp;|&nbsp; assign to a store for delivery ordering &nbsp;"
        + str(ua_chkd) + "/" + str(len(unassigned)) + "</span></div>")

    for idx, item in enumerate(unassigned):
        _render_item_row("Unassigned", item, idx)

    _add_item_form("Unassigned", "add_unassigned")

    footer_ua = ("All grabbed") if all_ua else "Assign to a store using the dropdown, or grab anywhere."
    st.html(
        "<div style='background:#E8F5E9;border-radius:0 0 8px 8px;padding:10px 18px;"
        "border-top:2px solid #5DAA6A;margin-bottom:4px;font-size:0.82rem;color:#3A8C4E;'>"
        + ("done  " if all_ua else "") + footer_ua + "</div>")

    st.divider()


# ==============================================================================
# SECTION 3 -- WEEKLY REGULARS (separate cost line -- Sincere Strategy)
# Not in cart. Shown as a separate block. Checkboxes for in-store use.
# ==============================================================================
if weekly_regs:
    # Check for sale matches in flyer_data
    flyer_data = st.session_state.get("flyer_data", {})
    reg_hints  = {}
    for reg in weekly_regs:
        kws = [w for w in reg["name"].lower().split() if len(w) > 3]
        for sk, cands in flyer_data.items():
            slabel = STORE_NAMES.get(sk, sk)
            for c in cands:
                cname = (getattr(c, "name", "") if hasattr(c, "name")
                         else c.get("name", "") if isinstance(c, dict) else "")
                if any(kw in cname.lower() for kw in kws):
                    price = (getattr(c, "sale_price_per_unit", 0.0)
                             if hasattr(c, "sale_price_per_unit")
                             else c.get("sale_price", 0.0)
                             if isinstance(c, dict) else 0.0)
                    reg_hints.setdefault(reg["name"], []).append(
                        {"store": slabel, "price": price}
                    )
                    break

    wr_chkd  = sum(1 for r in weekly_regs
                   if st.session_state.get("chk_wr_" + r["name"], False))
    all_wr   = wr_chkd == len(weekly_regs)
    hdr_wr   = "#3A8C4E" if all_wr else "#4A6E8A"
    st.html(
        "<div style='background:" + hdr_wr + ";color:#FFFFFF;border-radius:8px 8px 0 0;"
        "padding:12px 18px;margin-top:20px;'>"
        "<span style='font-size:1.05rem;font-weight:700;'>Weekly Regulars</span>"
        "<span style='font-size:0.82rem;color:#C8DFF4;margin-left:10px;'>"
        "Every week &nbsp;|&nbsp; tracked separately from meal savings &nbsp;"
        + str(wr_chkd) + "/" + str(len(weekly_regs)) + "</span></div>")

    for reg in weekly_regs:
        rname     = reg["name"]
        check_key = "chk_wr_" + rname
        checked   = st.session_state.get(check_key, False)
        qty_label = (str(reg.get("qty", "")) + " " + str(reg.get("unit", ""))).strip()
        hints     = reg_hints.get(rname, [])

        # Mobile-first: 2-column layout, sale hint inline in item name row
        col_chk, col_info = st.columns([1, 9])
        with col_chk:
            st.checkbox(label=rname, value=checked, key=check_key,
                        label_visibility="collapsed")
        with col_info:
            now = st.session_state.get(check_key, False)
            ns  = "text-decoration:line-through;color:#9AA8A0;" if now else "color:#1A2E1D;"
            ms  = "color:#9AA8A0;" if now else "color:#5A7A62;"
            sale_badge = ""
            if hints:
                parts = []
                for h in hints:
                    ps = ("$" + "{:.2f}".format(h["price"])) if h.get("price") else ""
                    parts.append(h["store"] + (" " + ps if ps else ""))
                sale_badge = (" &nbsp;<span style='font-size:0.72rem;background:#E3F4E8;"
                              "color:#1E5C32;padding:1px 6px;border-radius:3px;'>"
                              "sale: " + " / ".join(parts) + "</span>")
            st.html(
                "<div style='padding:6px 0;'>"
                "<div style='font-size:1rem;font-weight:600;" + ns + "'>"
                + rname + sale_badge + "</div>"
                "<div style='font-size:0.82rem;" + ms + "'>" + qty_label + "</div>"
                "</div>")
        st.html("<hr style='margin:0;border:none;border-top:1px solid #EEF3EE;'>")

    footer_wr = "All in the cart" if all_wr else "Add these to your regular run -- cost tracked separately."
    st.html(
        "<div style='background:#E8F0F8;border-radius:0 0 8px 8px;padding:10px 18px;"
        "border-top:2px solid #4A6E8A;margin-bottom:4px;font-size:0.82rem;color:#2A5070;'>"
        + ("done  " if all_wr else "") + footer_wr + "</div>")

    st.divider()


# ==============================================================================
# SECTION 4 -- PANTRY CHECK (collapsed)
# ==============================================================================
pantry_check = {}
for meal in meals:
    for ri in meal.get("recipe_ingredients", []):
        if not ri.get("pantry_stable", False):
            continue
        name = ri.get("name", "")
        if name:
            pantry_check.setdefault(name, [])
            day = meal.get("day", "")
            if day and day not in pantry_check[name]:
                pantry_check[name].append(day)

if pantry_check:
    with st.expander("Pantry check -- " + str(len(pantry_check)) + " items to verify", expanded=False):
        st.html(
            "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:10px;'>"
            "WhollyFare assumed you have these. Quick check before you shop.</div>")
        for name, days in pantry_check.items():
            st.html(
                "<div style='font-size:0.9rem;padding:4px 0;border-bottom:1px solid #EEF3EE;'>"
                "<span style='color:#1A2E1D;'>v " + name + "</span>"
                "<span style='color:#9AA8A0;font-size:0.78rem;float:right;'>"
                + ", ".join(days) + "</span></div>")
    st.divider()


# ==============================================================================
# PANTRY RESTOCK INTELLIGENCE (Layer 3)
# Show "good time to stock up" when a running-low pantry item is on sale
# in this week's flyer. No paid placements — purely usage math + circular price.
# Sincere Strategy: we say why. Usage count shown, sale price shown, no fluff.
# ==============================================================================
_running_low   = set(state.get_running_low())
_flyer_data    = st.session_state.get("flyer_data", {})
_restock_hits  = []  # [{name, store, price, uses}]

if _running_low and _flyer_data:
    _usage = st.session_state.get("pantry_usage") or {}
    for store_key, candidates in _flyer_data.items():
        store_label = store_key.replace("_", " ").title()
        for c in candidates:
            item_name = (
                getattr(c, "name", "") if hasattr(c, "name")
                else c.get("name", "") if isinstance(c, dict) else ""
            ).lower().strip()
            price = (
                getattr(c, "sale_price_per_unit", 0.0) if hasattr(c, "sale_price_per_unit")
                else c.get("sale_price", 0.0) if isinstance(c, dict) else 0.0
            )
            if not item_name or not price:
                continue
            for low_item in _running_low:
                keywords = [w for w in low_item.split() if len(w) > 3]
                if any(kw in item_name for kw in keywords):
                    uses = _usage.get(low_item, 0)
                    _restock_hits.append({
                        "name":  low_item,
                        "store": store_label,
                        "price": price,
                        "uses":  uses,
                    })
                    break

if _restock_hits:
    st.html(
        "<div style='font-size:1rem;font-weight:700;color:#7A4500;margin-bottom:4px;'>"
        "🔶 Good time to restock</div>"
        "<div style='font-size:0.82rem;color:#9A6A30;margin-bottom:12px;'>"
        "These pantry items are running low based on your cooking history — "
        "and on sale at a store you shop this week. "
        "No sponsored recommendations. Usage math + this week's circular, nothing else.</div>")
    for hit in _restock_hits:
        _threshold = state.PANTRY_DEPLETION_THRESHOLDS.get(
            hit["name"], state.PANTRY_DEPLETION_DEFAULT)
        _pct = min(int((hit["uses"] / max(_threshold, 1)) * 100), 100)
        _price_str = "${:.2f}".format(hit["price"])
        st.html(
            "<div style='background:#FFF8F0;border:1px solid #FFCC80;border-radius:8px;"
            "padding:12px 16px;margin-bottom:8px;'>"
            "<div style='font-weight:600;color:#7A4500;font-size:0.95rem;'>"
            + hit["name"].title() +
            " &nbsp;<span style='font-weight:400;font-size:0.85rem;color:#1E5C32;'>"
            "on sale at " + hit["store"] + " — " + _price_str + "</span></div>"
            "<div style='font-size:0.8rem;color:#9A6A30;margin-top:4px;'>"
            "Used in " + str(hit["uses"]) + " meals since last restock "
            "(" + str(_pct) + "% of typical container used up)"
            "</div></div>")
    st.divider()

# ==============================================================================
# SUMMARY FOOTER
# Meal plan cost and Found Money -- weekly regulars shown as a separate estimate.
# Sincere Strategy: never fold regulars into Found Money.
# ==============================================================================
meal_plan_cost = sum(
    i["cost"] for items in cart.values() for i in items if i["cost"] > 0
)

sf1, sf2 = st.columns(2)
with sf1:
    st.metric("Meal plan cost est.", "$" + "{:.2f}".format(totals.get("whollyfare_plan", meal_plan_cost)))
with sf2:
    st.metric("Found Money", "$" + "{:.2f}".format(totals.get("found_money", 0.0)),
              delta="vs. one store")

st.html(
    "<div style='font-size:0.8rem;color:#9AA8A0;margin-top:-10px;margin-bottom:12px;'>"
    "Weekly regulars tracked separately and not included in Found Money.</div>")


# ==============================================================================
# EXPORT SECTION
# Per-store formatted text (copy-paste into any delivery app) + CSV per store.
#
# Phase 3: replace "copy text" with live API calls:
#   Kroger:    push cart via PUT /cart/add  (credentials already in secrets.toml)
#   Instacart: POST /fulfillment/v2/fulfillment_orders  (partner API)
#   Shipt:     POST /lists/{list_id}/items
# ==============================================================================
st.divider()
st.html(
    "<div style='font-size:1rem;font-weight:700;color:#1E5C32;margin-bottom:8px;'>"
    "Export your list</div>")

# Per-store text blocks
for store in store_order:
    items = cart.get(store, [])
    if not items:
        continue

    # Build the text payload -- this is the shape that delivery app APIs want
    lines_txt = [store.upper() + " -- WhollyFare list -- Week of " + week,
                 "=" * 48]
    for item in items:
        qty   = item["qty"].ljust(10) if item["qty"] else "".ljust(10)
        price = ("$" + "{:.2f}".format(item["cost"])) if item["cost"] > 0 else "est."
        lines_txt.append("[ ] " + item["name"].ljust(30) + qty + price)
    lines_txt += ["", "Subtotal: $" + "{:.2f}".format(sum(i["cost"] for i in items))]

    st.download_button(
        label="Download " + store + " list (.txt)",
        data="\n".join(lines_txt),
        file_name="whollyfare_" + store.lower().replace(" ", "_") + "_" + week + ".txt",
        mime="text/plain",
        use_container_width=True,
        key="dl_txt_" + store.replace(" ", "_"),
    )

    # CSV -- the shape most delivery app APIs accept for bulk import
    lines_csv = ["name,qty,unit,estimated_price,category,source"]
    for item in items:
        qty_parts = item["qty"].split(" ", 1)
        qty_val   = qty_parts[0] if qty_parts else ""
        qty_unit  = qty_parts[1] if len(qty_parts) > 1 else "each"
        price_str = "{:.2f}".format(item["cost"]) if item["cost"] > 0 else ""
        lines_csv.append(",".join([
            '"' + item["name"].replace('"', "'") + '"',
            qty_val,
            qty_unit,
            price_str,
            item.get("category", "other"),
            item.get("source", ""),
        ]))

    st.download_button(
        label="Download " + store + " list (.csv)",
        data="\n".join(lines_csv),
        file_name="whollyfare_" + store.lower().replace(" ", "_") + "_" + week + ".csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_csv_" + store.replace(" ", "_"),
    )

# Unassigned export
if unassigned:
    lines_ua = ["ALSO NEEDED -- not store-specific -- Week of " + week, "-" * 48]
    for item in unassigned:
        lines_ua.append("[ ] " + item["name"].ljust(30) + item["qty"])
    st.download_button(
        label="Download 'Also needed' list (.txt)",
        data="\n".join(lines_ua),
        file_name="whollyfare_unassigned_" + week + ".txt",
        mime="text/plain",
        use_container_width=True,
        key="dl_txt_unassigned",
    )

# Phase 3 coming-soon hooks
st.divider()
st.html(
    "<div style='font-size:0.82rem;color:#9AA8A0;'>"
    "<strong>Phase 3 (coming soon):</strong> &nbsp;"
    "Direct ordering via Kroger, Instacart, and Shipt. "
    "Your list, one tap, delivered. &nbsp;"
    "<span style='font-size:0.75rem;'>No sponsored placements. No affiliate fees. "
    "WhollyFare charges a flat subscription -- that's it.</span>"
    "</div>")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# HOUSEHOLD STAPLES
# Food items always needed that aren't from the meal plan or weekly regulars.
# Water, coffee, snacks, kids' lunch items, specialty ingredients, etc.
# Non-food items (detergent, paper goods) belong in WhollyWare.
# ─────────────────────────────────────────────────────────────────────────────
st.html("<div style='font-size:1rem;font-weight:700;color:#1E5C32;margin-bottom:4px;'>"
        "🧺 Household Staples</div>"
        "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:12px;'>"
        "Food items you always grab — not from the meal plan. "
        "Water, coffee, snacks, lunch items, anything else.</div>")

hs_items = st.session_state["household_staples"]

if hs_items:
    hs_to_keep = []
    for hs in hs_items:
        hs_key = "chk_hs_" + hs["name"].replace(" ", "_")
        c1, c2 = st.columns([8, 1])
        with c1:
            cost_disp = f" · ${hs['cost']:.2f}" if hs.get("cost") else ""
            label = hs["name"] + (f" — {hs['qty']}" if hs.get("qty") else "") + cost_disp
            st.checkbox(label, value=st.session_state.get(hs_key, False), key=hs_key)
        with c2:
            if not st.button("×", key="hs_rm_" + hs["name"].replace(" ", "_"),
                              help="Remove"):
                hs_to_keep.append(hs)
    if len(hs_to_keep) != len(hs_items):
        st.session_state["household_staples"] = hs_to_keep
        st.rerun()
    # Show subtotal for items with cost entered
    hs_total = sum(float(h.get("cost") or 0) for h in hs_items)
    if hs_total > 0:
        st.html(f"<div style='text-align:right;font-size:0.88rem;font-weight:600;"
                f"color:#1E5C32;padding:4px 0;'>"
                f"Staples estimated total: ${hs_total:.2f}</div>")
else:
    st.html("<div style='font-size:0.85rem;color:#9AA8A0;font-style:italic;"
            "padding:4px 0 12px 0;'>No staples added yet — add water, coffee, snacks, anything.</div>")

with st.form("add_hs_form", clear_on_submit=True):
    hs_c1, hs_c2 = st.columns([6, 3])
    with hs_c1:
        hs_name = st.text_input("Item", placeholder="e.g. Spring water, Coffee",
                                label_visibility="collapsed")
    with hs_c2:
        hs_qty = st.text_input("Qty", placeholder="e.g. 2 cases",
                               label_visibility="collapsed")
    hs_c3, hs_c4 = st.columns([6, 3])
    with hs_c3:
        hs_cost = st.text_input("Cost $", placeholder="e.g. 4.99",
                                label_visibility="collapsed")
    with hs_c4:
        hs_add = st.form_submit_button("+ Add", use_container_width=True)
    if hs_add and hs_name.strip():
        existing = {i["name"].lower() for i in hs_items}
        if hs_name.strip().lower() not in existing:
            try:
                cost_val = float(hs_cost.strip()) if hs_cost.strip() else 0.0
            except ValueError:
                cost_val = 0.0
            hs_items.append({"name": hs_name.strip(), "qty": hs_qty.strip(),
                              "cost": cost_val})
            st.session_state["household_staples"] = hs_items
            st.rerun()

st.divider()

# Reset + rebuild controls
btn1, btn2 = st.columns(2)
with btn1:
    if st.button("Check all items", use_container_width=True):
        for store, items in cart.items():
            for item in items:
                st.session_state["chk_" + store + "_" + item["name"]] = True
        for reg in weekly_regs:
            st.session_state["chk_wr_" + reg["name"]] = True
        st.rerun()
    if st.button("Clear all items", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("chk_"):
                st.session_state[k] = False
        st.rerun()
with btn2:
    if st.button("🔄 Rebuild from this week's plan", use_container_width=True):
        # Re-derive cart by clearing shopping_cart — plan page will repopulate on next visit
        st.session_state.pop("shopping_cart", None)
        st.rerun()
