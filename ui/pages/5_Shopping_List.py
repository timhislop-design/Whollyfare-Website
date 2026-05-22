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

st.set_page_config(page_title="Shopping List - WhollyFare", page_icon="\U0001f6d2", layout="centered")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header("Shopping List", "Everything you need this week, organised by store.")

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

meals    = plan["meals"]
totals   = plan["totals"]
week     = plan["week"]
servings = plan["servings"]

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

    # 1. Sale items from plan (already assigned to a store by the meal planner)
    sale_item_keys = set()  # track to avoid double-listing in recipe extras
    for meal in plan.get("meals", []):
        for ing in meal.get("ingredients", []):
            sid       = ing.get("store", "")
            store     = STORE_NAMES.get(sid, sid) or "Unassigned"
            name      = ing.get("item", "")
            qty_str   = str(ing.get("qty", ""))
            cost      = float(ing.get("cost", 0.0))
            key       = name.lower() + "|" + store

            if key in sale_item_keys:
                # Shared ingredient (used in multiple meals) -- accumulate cost
                for item in cart.get(store, []):
                    if item["name"].lower() == name.lower() and item["source"] == "sale":
                        item["cost"] = round(item["cost"] + cost, 2)
                        if meal.get("day") and meal["day"] not in item.get("_meals", []):
                            item.setdefault("_meals", []).append(meal["day"])
                        break
                continue

            sale_item_keys.add(key)
            cart.setdefault(store, []).append({
                "name":     name,
                "qty":      qty_str,
                "cost":     cost,
                "source":   "sale",
                "category": ing.get("category", "other"),
                "moveable": False,   # sale price is store-specific -- moving loses the deal
                "_meals":   [meal.get("day", "")] if meal.get("day") else [],
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

    col_chk, col_info, col_cost, col_ctrl = st.columns([0.5, 4.5, 1.2, 1.3])

    with col_chk:
        st.checkbox(label=name, value=checked, key=check_key,
                    label_visibility="collapsed")

    with col_info:
        now        = st.session_state.get(check_key, False)
        name_style = "text-decoration:line-through;color:#9AA8A0;" if now else "color:#1A2E1D;"
        meta_style = "color:#9AA8A0;" if now else "color:#5A7A62;"
        src_badge  = (" &nbsp;<span style='font-size:0.7rem;background:#E8F5E9;"
                      "color:#3A8C4E;padding:1px 5px;border-radius:3px;'>"
                      + _source_label(source) + "</span>") if source != "sale" else ""
        st.html(
            "<div style='padding:4px 0;'>"
            "<div style='font-size:0.95rem;font-weight:600;" + name_style + "'>"
            + name + src_badge + "</div>"
            "<div style='font-size:0.75rem;" + meta_style + "'>"
            + qty + ("&nbsp;&middot;&nbsp;" + meals_str if meals_str else "") + "</div>"
            "</div>")

    with col_cost:
        now        = st.session_state.get(check_key, False)
        cost_style = "color:#9AA8A0;text-decoration:line-through;" if now else "color:#1E5C32;font-weight:700;"
        cost_str   = ("$" + "{:.2f}".format(cost)) if cost > 0 else "est."
        st.html("<div style='padding:4px 0;text-align:right;font-size:0.95rem;" + cost_style + "'>"
                + cost_str + "</div>")

    with col_ctrl:
        # Move to store (only for moveable items) or Remove (always available for manual/extras)
        ctrl_key = "ctrl_" + store + "_" + name + "_" + str(idx)
        if moveable:
            other_stores = [s for s in ALL_STORES if s != store] + (
                ["Unassigned"] if store != "Unassigned" else []
            )
            move_options = ["move..."] + other_stores + ["remove"]
            choice = st.selectbox(
                label="move", options=move_options, index=0,
                key=ctrl_key, label_visibility="collapsed"
            )
            if choice != "move...":
                # Remove from current store
                cart[store] = [i for i in cart.get(store, []) if i["name"] != name]
                if choice != "remove":
                    item_copy = dict(item)
                    item_copy["moveable"] = True
                    cart.setdefault(choice, []).append(item_copy)
                st.session_state["shopping_cart"] = cart
                st.rerun()
        elif source == "manual":
            if st.button("x", key=ctrl_key, help="Remove"):
                cart[store] = [i for i in cart.get(store, []) if i["name"] != name]
                st.session_state["shopping_cart"] = cart
                st.rerun()

    st.html("<hr style='margin:0;border:none;border-top:1px solid #EEF3EE;'>")


def _add_item_form(store: str, form_key: str):
    """Inline form to add a manual item to a specific store's cart."""
    with st.form(form_key, clear_on_submit=True):
        c1, c2, c3 = st.columns([4, 2, 1.5])
        with c1:
            new_name = st.text_input("Item name", placeholder="e.g. Greek yogurt",
                                     label_visibility="collapsed")
        with c2:
            new_qty = st.text_input("Qty", placeholder="e.g. 32 oz",
                                    label_visibility="collapsed")
        with c3:
            add_btn = st.form_submit_button("+ Add", use_container_width=True)
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

        col_chk, col_info, col_sale = st.columns([0.5, 5, 2])
        with col_chk:
            st.checkbox(label=rname, value=checked, key=check_key,
                        label_visibility="collapsed")
        with col_info:
            now = st.session_state.get(check_key, False)
            ns  = "text-decoration:line-through;color:#9AA8A0;" if now else "color:#1A2E1D;"
            ms  = "color:#9AA8A0;" if now else "color:#5A7A62;"
            st.html(
                "<div style='padding:4px 0;'>"
                "<div style='font-size:0.95rem;font-weight:600;" + ns + "'>" + rname + "</div>"
                "<div style='font-size:0.75rem;" + ms + "'>" + qty_label + "</div>"
                "</div>")
        with col_sale:
            if hints:
                parts = []
                for h in hints:
                    ps = ("$" + "{:.2f}".format(h["price"])) if h.get("price") else ""
                    parts.append(h["store"] + (" " + ps if ps else ""))
                st.html(
                    "<div style='padding:4px 0;font-size:0.76rem;color:#1E5C32;"
                    "background:#E3F4E8;border-radius:4px;padding:3px 8px;'>"
                    "On sale: " + " / ".join(parts) + "</div>")
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

# Reset + rebuild controls
btn1, btn2 = st.columns(2)
with btn1:
    if st.button("Clear all checkmarks", use_container_width=True):
        for store, items in cart.items():
            for item in items:
                st.session_state.pop("chk_" + store + "_" + item["name"], None)
        for reg in weekly_regs:
            st.session_state.pop("chk_wr_" + reg["name"], None)
        st.rerun()
with btn2:
    if st.button("Rebuild list from plan", use_container_width=True,
                 help="Discards any manual adds/moves and rebuilds from the current plan."):
        st.session_state.pop("shopping_cart", None)
        st.session_state.pop("_cart_week", None)
        st.rerun()

st.html("<br>")
st.page_link("pages/6_Ledger.py", label="-> View Found Money History")
