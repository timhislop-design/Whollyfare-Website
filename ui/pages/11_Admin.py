"""11_Admin.py -- Admin Circular Manager

Tim's weekly tool for uploading grocer circulars and getting them into the app.

What this page does
-------------------
1. Shows every Charlottesville-area store Tim tracks.
2. For PDF stores: accepts a PDF upload, calls the Claude Vision extractor,
   and shows the extracted items in a preview table.
3. For Kroger/API stores: shows the live Kroger pull status.
4. For manual stores (TJ's, EW Thomas): shows a note + link to the Grocer Hub
   manual entry form.
5. Once Tim confirms the preview, one click saves items to:
   a. session_state["flyer_data"] -- used immediately by Plan, Buy-Off, Shopping List
   b. Supabase flyer_items table -- persists across sessions

Pilot vs. Production
--------------------
Pilot:  Tim runs this every Wednesday morning. Manual download + upload.
        Claude extracts. Tim reviews. One click saves.
PROD:   Scheduled job downloads PDFs automatically. Admin page becomes a
        review/override queue. Claude confidence scores flag uncertain items
        for human review.

IMPORTANT: Keep this page admin-only in production. It bypasses the normal
           constraint engine -- it loads raw sale data, not filtered data.
           In Phase 2, add a simple admin_token check.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style
from datetime import date, timedelta

st.set_page_config(
    page_title="Admin: Circular Manager - WhollyFare",
    page_icon="🗂️",
    layout="wide",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Admin: Circular Manager",
    "Upload weekly circulars, extract sale items with Claude, save to the app and database.",
)

# ── Imports (lazy -- these are heavy) ─────────────────────────────────────────
from app.data.store_directory import CHARLOTTESVILLE_STORES, PDF_STORES
try:
    from app.core_logic.claude_extractor import extract_uploaded_pdf, merge_into_flyer_data
    _extractor_available = True
except ImportError as _ei:
    _extractor_available = False
    _extractor_error = str(_ei)

# ── Week selector ──────────────────────────────────────────────────────────────
today = date.today()
# Weeks start Monday -- find this week's Monday
week_start = today - timedelta(days=today.weekday())
week_label = week_start.strftime("Week of %B %-d, %Y")

st.html(
    "<div style='background:#E3F4E8;border:1px solid #5DAA6A;border-radius:10px;"
    "padding:10px 18px;margin-bottom:24px;font-size:0.9rem;color:#1E5C32;'>"
    "<strong>Active week:</strong> " + week_label +
    " &nbsp;&middot;&nbsp; "
    "Items saved here appear in This Week's Plan, Sunday Buy-Off, and the Shopping List."
    "</div>"
)

if not _extractor_available:
    st.warning(
        "Claude extractor unavailable. "
        "Make sure `anthropic>=0.25.0` is installed and ANTHROPIC_API_KEY is set. "
        f"Import error: {_extractor_error}"
    )

# ── Session state for extraction results ──────────────────────────────────────
# Keyed by store chain name so multiple stores can be staged at once.
# Format: {chain: ExtractionResult}
if "admin_staged" not in st.session_state:
    st.session_state["admin_staged"] = {}

staged: dict = st.session_state["admin_staged"]

# ── API key ────────────────────────────────────────────────────────────────────
api_key = None
try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except Exception:
    pass
if not api_key:
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error(
        "ANTHROPIC_API_KEY is not set. "
        "Add it to `.streamlit/secrets.toml` as ANTHROPIC_API_KEY = \"sk-ant-...\""
    )

# ── Preview + save function ────────────────────────────────────────────────────
def _render_extraction_preview(chain: str, result, week_iso: str) -> None:
    """Show extracted items and a Save button for a staged extraction result."""

    page_summary = "  ·  ".join(
        f"p.{p['page']}: {p['item_count']} items"
        + (" ⚠" if p.get("error") else "")
        for p in result.page_log
    )
    st.html(
        "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:8px;'>"
        "<strong>Extraction log:</strong> " + page_summary + "</div>"
    )

    if result.errors:
        for err in result.errors:
            st.warning("Parser note: " + err)

    # Preview table
    if result.raw_items:
        # Limit display to 100 rows -- full list goes to DB
        display_items = result.raw_items[:100]
        more = max(0, len(result.raw_items) - 100)

        # Build HTML table
        rows_html = ""
        for item in display_items:
            name     = str(item.get("name",     ""))[:60]
            price    = item.get("price", 0.0) or 0.0
            unit     = str(item.get("unit",     "each"))
            cat      = str(item.get("category", "other"))
            raw_text = str(item.get("raw_text", ""))

            _cat_colors = {
                "produce": "#E8F5E9", "protein": "#FFF3E0", "dairy": "#E3F2FD",
                "grain": "#FFF9C4", "frozen": "#E8EAF6", "snack": "#FCE4EC",
                "beverage": "#E0F7FA", "deli": "#FFF3E0",
                "household": "#F5F5F5", "personal_care": "#F3E5F5", "other": "#FAFAFA",
            }
            cat_bg = _cat_colors.get(cat, "#FAFAFA")

            rows_html += (
                "<tr>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.85rem;'>" + name + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.85rem;"
                "text-align:right;font-weight:600;color:#1E5C32;'>$" + f"{price:.2f}" + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.82rem;"
                "color:#5A7A62;'>" + unit + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;'>"
                "<span style='background:" + cat_bg + ";font-size:0.75rem;"
                "padding:1px 6px;border-radius:8px;'>" + cat + "</span></td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.78rem;"
                "color:#9AA8A0;'>" + raw_text + "</td>"
                "</tr>"
            )

        st.html(
            "<div style='overflow-x:auto;max-height:380px;overflow-y:auto;"
            "border:1px solid #E0E0E0;border-radius:8px;'>"
            "<table style='width:100%;border-collapse:collapse;'>"
            "<thead><tr style='background:#F0F7F1;'>"
            "<th style='padding:6px 8px;text-align:left;font-size:0.78rem;color:#5A7A62;border-bottom:2px solid #C8E6C9;'>Item</th>"
            "<th style='padding:6px 8px;text-align:right;font-size:0.78rem;color:#5A7A62;border-bottom:2px solid #C8E6C9;'>Price/unit</th>"
            "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;border-bottom:2px solid #C8E6C9;'>Unit</th>"
            "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;border-bottom:2px solid #C8E6C9;'>Category</th>"
            "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;border-bottom:2px solid #C8E6C9;'>Raw text</th>"
            "</tr></thead>"
            "<tbody>" + rows_html + "</tbody>"
            "</table>"
            + (
                "<div style='padding:8px 12px;font-size:0.78rem;color:#9AA8A0;'>"
                "+ " + str(more) + " more items (all saved to database)</div>"
                if more > 0 else ""
            )
            + "</div>"
        )

    # Save row
    col_save, col_discard = st.columns([2, 1])
    with col_save:
        store_key = chain.lower().replace(" ", "_")
        if st.button(
            "Save " + str(result.item_count) + " items to app + database",
            key="save_" + chain.replace(" ", "_"),
            type="primary",
            use_container_width=True,
        ):
            # 1. Merge into session_state flyer_data (immediate effect)
            fd = st.session_state.get("flyer_data", {})
            fd = merge_into_flyer_data(result, chain, fd)
            st.session_state["flyer_data"] = fd

            # 2. Invalidate the shopping cart so it rebuilds with new prices
            st.session_state.pop("shopping_cart", None)
            st.session_state.pop("_cart_week", None)

            # 3. Persist to Supabase if authenticated
            db_msg = ""
            if state.is_authenticated():
                ok, msg = state.save_flyer_items(
                    chain=chain,
                    candidates=result.candidates,
                    week=week_iso,
                    method="pdf",
                )
                db_msg = " · " + msg
            else:
                db_msg = " · Not saved to DB (not signed in)"

            # 4. Clear staged result
            staged_now = st.session_state.get("admin_staged", {})
            staged_now.pop(chain, None)
            st.session_state["admin_staged"] = staged_now

            st.success(
                chain + ": " + str(result.item_count) +
                " items loaded into the app." + db_msg
            )
            st.rerun()

    with col_discard:
        if st.button(
            "Discard",
            key="discard_" + chain.replace(" ", "_"),
            use_container_width=True,
        ):
            staged_now = st.session_state.get("admin_staged", {})
            staged_now.pop(chain, None)
            st.session_state["admin_staged"] = staged_now
            st.rerun()



# ── Store grid ─────────────────────────────────────────────────────────────────

TIER_LABELS = {
    "full_service":   ("🏪", "Full-Service"),
    "value_discount": ("💰", "Value & Discount"),
    "specialty":      ("🌿", "Specialty"),
    "local":          ("📍", "Local"),
}

METHOD_BADGE = {
    "kroger_api": ("🟢", "Live API"),
    "pdf":        ("📄", "PDF upload"),
    "manual":     ("✏️",  "Manual entry"),
}

# Group stores by tier for display
_tier_order = ["full_service", "value_discount", "specialty", "local"]
_by_tier: dict[str, list] = {t: [] for t in _tier_order}
for s in CHARLOTTESVILLE_STORES:
    _by_tier.setdefault(s["tier"], []).append(s)

for tier_key in _tier_order:
    stores_in_tier = _by_tier[tier_key]
    if not stores_in_tier:
        continue

    tier_icon, tier_name = TIER_LABELS.get(tier_key, ("", tier_key))
    st.html(
        "<div style='font-size:1.05rem;font-weight:700;color:#1E5C32;"
        "margin:24px 0 8px 0;border-bottom:2px solid #C8E6C9;padding-bottom:4px;'>"
        + tier_icon + " " + tier_name + " Grocers</div>"
    )

    for store in stores_in_tier:
        chain    = store["chain"]
        location = store["location"]
        method   = store["method"]
        flyer_url = store.get("flyer_url")
        notes    = store.get("notes", "")
        flyer_day = store.get("flyer_day")

        method_icon, method_label = METHOD_BADGE.get(method, ("", method))

        # Check if items are already in flyer_data for this store
        flyer_data    = st.session_state.get("flyer_data", {})
        existing_key  = chain.lower().replace(" ", "_")
        existing_items = flyer_data.get(chain) or flyer_data.get(existing_key) or []
        has_items     = len(existing_items) > 0

        # Is there a staged (extracted but not yet saved) result?
        has_staged = chain in staged and staged[chain].item_count > 0

        # Status indicator
        if has_staged:
            status_html = (
                "<span style='background:#FFF3CD;color:#856404;font-size:0.78rem;"
                "padding:2px 8px;border-radius:12px;font-weight:600;'>"
                "⏳ " + str(staged[chain].item_count) + " items staged — not yet saved</span>"
            )
        elif has_items:
            status_html = (
                "<span style='background:#D4EDDA;color:#155724;font-size:0.78rem;"
                "padding:2px 8px;border-radius:12px;font-weight:600;'>"
                "✅ " + str(len(existing_items)) + " items loaded</span>"
            )
        else:
            status_html = (
                "<span style='background:#F8F9FA;color:#6C757D;font-size:0.78rem;"
                "padding:2px 8px;border-radius:12px;'>"
                "○ Not loaded</span>"
            )

        with st.expander(
            chain + " — " + location + "  " + method_icon + " " + method_label,
            expanded=(has_staged or method == "pdf" and not has_items),
        ):
            # Store header row
            col_info, col_action = st.columns([3, 2])
            with col_info:
                st.html(
                    "<div style='font-size:0.85rem;color:#5A7A62;line-height:1.6;'>"
                    + status_html +
                    "<br><span style='color:#9AA8A0;'>" + notes + "</span>"
                    + (
                        "<br><span style='color:#9AA8A0;'>Circular posts: <strong style='color:#5A7A62;'>"
                        + flyer_day + "s</strong></span>"
                        if flyer_day else ""
                    )
                    + "</div>"
                )

            with col_action:
                # ── PDF upload path ────────────────────────────────────────
                if method == "pdf":
                    if flyer_url:
                        st.html(
                            "<div style='font-size:0.8rem;margin-bottom:6px;'>"
                            "<a href='" + flyer_url + "' target='_blank' "
                            "style='color:#1E5C32;text-decoration:underline;'>"
                            "↗ Download circular</a></div>"
                        )
                    uploaded = st.file_uploader(
                        "Upload PDF circular",
                        type=["pdf"],
                        key="pdf_upload_" + chain.replace(" ", "_"),
                        label_visibility="collapsed",
                        help="Download the weekly circular PDF from the store's website and upload here.",
                    )

                    if uploaded and _extractor_available and api_key:
                        if st.button(
                            "Extract items with Claude",
                            key="extract_" + chain.replace(" ", "_"),
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner(
                                "Reading " + chain + " circular with Claude Vision..."
                            ):
                                result = extract_uploaded_pdf(
                                    file_bytes=uploaded.read(),
                                    store_chain=chain,
                                    api_key=api_key,
                                    max_pages=20,
                                )
                            if result.errors:
                                for err in result.errors:
                                    st.error(err)
                            if result.item_count > 0:
                                staged[chain] = result
                                st.session_state["admin_staged"] = staged
                                st.success(
                                    f"Extracted {result.item_count} items from "
                                    f"{len(result.page_log)} pages."
                                )
                                st.rerun()
                            elif not result.errors:
                                st.warning(
                                    "No items found. The PDF may be password-protected "
                                    "or have no readable sale prices."
                                )

                # ── Kroger API path ────────────────────────────────────────
                elif method == "kroger_api":
                    kroger_items = (
                        flyer_data.get("kroger_palmyra") or
                        flyer_data.get("Kroger") or []
                    )
                    if kroger_items:
                        st.html(
                            "<div style='font-size:0.85rem;color:#1E5C32;'>"
                            "✅ " + str(len(kroger_items)) + " items loaded from Kroger API. "
                            "Go to <strong>Grocer Hub</strong> to refresh.</div>"
                        )
                    else:
                        st.html(
                            "<div style='font-size:0.85rem;color:#9AA8A0;'>"
                            "Pull Kroger data from the <strong>Grocer Hub</strong> page.</div>"
                        )

                # ── Manual entry path ──────────────────────────────────────
                elif method == "manual":
                    st.html(
                        "<div style='font-size:0.85rem;color:#9AA8A0;'>"
                        "Manual entry only. Use the <strong>Grocer Hub</strong> "
                        "to type in items from this store's circular.</div>"
                    )

            # ── Staged results preview ─────────────────────────────────────
            if chain in staged:
                result = staged[chain]
                st.divider()
                _render_extraction_preview(chain, result, week_start.isoformat())


# ── Summary: what's loaded this week ──────────────────────────────────────────
st.divider()
st.html(
    "<div style='font-size:1.0rem;font-weight:700;color:#1E5C32;margin-bottom:12px;'>"
    "This Week's Data Status</div>"
)

flyer_data = st.session_state.get("flyer_data", {})
loaded_stores = []
for s in CHARLOTTESVILLE_STORES:
    chain = s["chain"]
    key1  = chain
    key2  = chain.lower().replace(" ", "_")
    items = flyer_data.get(key1) or flyer_data.get(key2) or []
    if items:
        loaded_stores.append((chain, len(items)))

if loaded_stores:
    rows = "".join(
        "<tr>"
        "<td style='padding:5px 10px;border-bottom:1px solid #EEE;font-size:0.88rem;'>" + ch + "</td>"
        "<td style='padding:5px 10px;border-bottom:1px solid #EEE;font-size:0.88rem;"
        "text-align:right;font-weight:600;color:#1E5C32;'>" + str(ct) + " items</td>"
        "<td style='padding:5px 10px;border-bottom:1px solid #EEE;'>"
        "<span style='background:#D4EDDA;color:#155724;font-size:0.75rem;"
        "padding:2px 7px;border-radius:10px;'>✅ Ready</span></td>"
        "</tr>"
        for ch, ct in loaded_stores
    )
    total = sum(ct for _, ct in loaded_stores)
    st.html(
        "<table style='width:100%;border-collapse:collapse;"
        "border:1px solid #E0E0E0;border-radius:8px;overflow:hidden;'>"
        "<thead><tr style='background:#F0F7F1;'>"
        "<th style='padding:6px 10px;text-align:left;font-size:0.78rem;color:#5A7A62;'>Store</th>"
        "<th style='padding:6px 10px;text-align:right;font-size:0.78rem;color:#5A7A62;'>Items</th>"
        "<th style='padding:6px 10px;font-size:0.78rem;color:#5A7A62;'>Status</th>"
        "</tr></thead>"
        "<tbody>" + rows + "</tbody>"
        "<tfoot><tr style='background:#F8FDF9;'>"
        "<td style='padding:6px 10px;font-size:0.82rem;font-weight:700;color:#1E5C32;'>Total</td>"
        "<td style='padding:6px 10px;text-align:right;font-size:0.82rem;"
        "font-weight:700;color:#1E5C32;'>" + str(total) + "</td>"
        "<td></td>"
        "</tr></tfoot>"
        "</table>"
    )
else:
    st.html(
        "<div style='font-size:0.88rem;color:#9AA8A0;font-style:italic;'>"
        "No store circulars loaded yet this week. Upload PDFs above to get started.</div>"
    )

# ── How it works explainer ─────────────────────────────────────────────────────
with st.expander("How the circular pipeline works", expanded=False):
    st.html(
        "<div style='font-size:0.88rem;color:#3A3A3A;line-height:1.7;'>"
        "<strong>Every Wednesday morning:</strong><br>"
        "1. Visit each store's website (links above) and download the weekly circular PDF.<br>"
        "2. Upload each PDF here. Claude Vision reads the images and extracts every sale item.<br>"
        "3. Review the preview table — check that item names, prices, and categories look right.<br>"
        "4. Click Save. Items go into the app immediately and are stored in Supabase.<br>"
        "5. Run This Week's Plan — the meal planner now sees all store prices.<br><br>"
        "<strong>Data flow:</strong><br>"
        "PDF upload → PyMuPDF renders pages (pure Python) → Claude Vision API extracts items → "
        "IngredientCandidates → flyer_data (session) + flyer_items (Supabase)<br><br>"
        "<strong>What Claude extracts:</strong><br>"
        "Item name, sale price per unit, unit (lb/oz/each), category, and the raw price "
        "Item name, sale price per unit, unit (lb/oz/each), category, and the raw price "
        "text exactly as printed (e.g. '2/$5'). Multi-buy deals are normalized to "
        "per-unit price. BOGO is set to half price when the regular price is shown."
        "<br><br>"
        "<strong>Pilot vs. Production:</strong><br>"
        "Pilot: Tim uploads PDFs manually. One API call per page via claude-3-haiku. "
        "Production: Scheduled job downloads PDFs, diffs against prior week, "
        "confidence-scores each item, and queues low-confidence items for review."
        "</div>"
    )
