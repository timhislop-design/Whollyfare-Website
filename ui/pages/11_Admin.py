"""11_Admin.py -- Admin Console (four tabs)

Tim's weekly tool and platform management hub.

Tabs
----
1. Circulars  -- Upload PDF circulars, extract with Claude Vision, save to app + DB.
2. Users      -- Manage platform users: admin flags, test accounts, password resets.
3. Dashboard  -- Activity feed and key metrics for the pilot.
4. Feedback   -- View and triage feedback submitted by signed-in users.

IMPORTANT: Keep this page admin-only. It bypasses the normal constraint engine and
           exposes user management functions. Admin gate enforced via state.is_admin().
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style
from datetime import date, timedelta, datetime, timezone

st.set_page_config(
    page_title="Admin Console - WhollyFare",
    page_icon="\U0001f5c2\ufe0f",
    layout="wide",
)
state.init()

with st.sidebar:
    style.sidebar_nav()

# \u2500\u2500 Admin gate \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
if not state.is_authenticated():
    style.page_header("Admin Console", "")
    st.warning("You must be signed in to access this page.", icon="\U0001f512")
    if st.button("Sign in", key="admin_signin_btn"):
        st.switch_page("pages/9_Account.py")
    st.stop()

if not state.is_admin():
    style.page_header("Admin Console", "")
    st.error(
        "Access denied. This page is restricted to WhollyFare platform admins.\n\n"
        "If you believe you should have access, contact tim.hislop@gmail.com.",
        icon="\U0001f512",
    )
    st.stop()
# \u2500\u2500 End admin gate \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

style.page_header(
    "Admin Console",
    "Circulars \u00b7 Users \u00b7 Dashboard \u00b7 Feedback",
)

tab_circ, tab_users, tab_dash, tab_fb = st.tabs([
    "\U0001f4c4 Circulars", "\U0001f465 Users", "\U0001f4ca Dashboard", "\U0001f4ac Feedback"
])


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TAB 1 \u2014 CIRCULARS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_circ:

    # Lazy imports (heavy)
    from app.data.store_directory import CHARLOTTESVILLE_STORES, PDF_STORES
    try:
        from app.core_logic.claude_extractor import extract_uploaded_pdf, merge_into_flyer_data
        _extractor_available = True
    except ImportError as _ei:
        _extractor_available = False
        _extractor_error = str(_ei)

    # Week selector
    today = date.today()
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
            "Import error: " + _extractor_error
        )

    # Session state for staged extraction results
    if "admin_staged" not in st.session_state:
        st.session_state["admin_staged"] = {}
    staged: dict = st.session_state["admin_staged"]

    # API key
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
            "Add it to .streamlit/secrets.toml as ANTHROPIC_API_KEY = \"sk-ant-...\""
        )

    # Preview + save function
    def _render_extraction_preview(chain: str, result, week_iso: str) -> None:
        """Show extracted items and a Save button for a staged extraction result."""
        parts = []
        for p in result.page_log:
            note = " (error)" if p.get("error") else ""
            parts.append("p." + str(p["page"]) + ": " + str(p["item_count"]) + " items" + note)
        page_summary = "  \u00b7  ".join(parts)

        st.html(
            "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:8px;'>"
            "<strong>Extraction log:</strong> " + page_summary + "</div>"
        )

        if result.errors:
            for err in result.errors:
                st.warning("Parser note: " + err)

        if result.raw_items:
            display_items = result.raw_items[:100]
            more = max(0, len(result.raw_items) - 100)

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
                price_str = "$" + "{:.2f}".format(price)

                rows_html += (
                    "<tr>"
                    "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.85rem;'>" + name + "</td>"
                    "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.85rem;"
                    "text-align:right;font-weight:600;color:#1E5C32;'>" + price_str + "</td>"
                    "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.82rem;"
                    "color:#5A7A62;'>" + unit + "</td>"
                    "<td style='padding:5px 8px;border-bottom:1px solid #EEE;'>"
                    "<span style='background:" + cat_bg + ";font-size:0.75rem;"
                    "padding:1px 6px;border-radius:8px;'>" + cat + "</span></td>"
                    "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.78rem;"
                    "color:#9AA8A0;'>" + raw_text + "</td>"
                    "</tr>"
                )

            more_row = ""
            if more > 0:
                more_row = (
                    "<div style='padding:8px 12px;font-size:0.78rem;color:#9AA8A0;'>"
                    "+ " + str(more) + " more items (all saved to database)</div>"
                )

            st.html(
                "<div style='overflow-x:auto;max-height:380px;overflow-y:auto;"
                "border:1px solid #E0E0E0;border-radius:8px;'>"
                "<table style='width:100%;border-collapse:collapse;'>"
                "<thead><tr style='background:#F0F7F1;'>"
                "<th style='padding:6px 8px;text-align:left;font-size:0.78rem;color:#5A7A62;"
                "border-bottom:2px solid #C8E6C9;'>Item</th>"
                "<th style='padding:6px 8px;text-align:right;font-size:0.78rem;color:#5A7A62;"
                "border-bottom:2px solid #C8E6C9;'>Price/unit</th>"
                "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;"
                "border-bottom:2px solid #C8E6C9;'>Unit</th>"
                "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;"
                "border-bottom:2px solid #C8E6C9;'>Category</th>"
                "<th style='padding:6px 8px;font-size:0.78rem;color:#5A7A62;"
                "border-bottom:2px solid #C8E6C9;'>Raw text</th>"
                "</tr></thead>"
                "<tbody>" + rows_html + "</tbody>"
                "</table>"
                + more_row
                + "</div>"
            )

        col_save, col_discard = st.columns([2, 1])
        with col_save:
            if st.button(
                "Save " + str(result.item_count) + " items to app + database",
                key="save_" + chain.replace(" ", "_"),
                type="primary",
                use_container_width=True,
            ):
                fd = st.session_state.get("flyer_data", {})
                fd = merge_into_flyer_data(result, chain, fd)
                st.session_state["flyer_data"] = fd
                st.session_state.pop("shopping_cart", None)
                st.session_state.pop("_cart_week", None)

                db_msg = ""
                if state.is_authenticated():
                    ok, msg = state.save_flyer_items(
                        chain=chain,
                        candidates=result.candidates,
                        week=week_iso,
                        method="pdf",
                    )
                    db_msg = " \u00b7 " + msg
                else:
                    db_msg = " \u00b7 Not saved to DB (not signed in)"

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

    # Store grid
    TIER_LABELS = {
        "full_service":   ("\U0001f3ea", "Full-Service"),
        "value_discount": ("\U0001f4b0", "Value & Discount"),
        "specialty":      ("\U0001f33f", "Specialty"),
        "local":          ("\U0001f4cd", "Local"),
    }

    METHOD_BADGE = {
        "kroger_api": ("\U0001f7e2", "Live API"),
        "pdf":        ("\U0001f4c4", "PDF upload"),
        "manual":     ("\u270f\ufe0f",  "Manual entry"),
    }

    _tier_order = ["full_service", "value_discount", "specialty", "local"]
    _by_tier: dict = {t: [] for t in _tier_order}
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
            chain     = store["chain"]
            location  = store["location"]
            method    = store["method"]
            flyer_url = store.get("flyer_url")
            notes     = store.get("notes", "")
            flyer_day = store.get("flyer_day")

            method_icon, method_label = METHOD_BADGE.get(method, ("", method))

            flyer_data    = st.session_state.get("flyer_data", {})
            existing_key  = chain.lower().replace(" ", "_")
            existing_items = flyer_data.get(chain) or flyer_data.get(existing_key) or []
            has_items     = len(existing_items) > 0
            has_staged    = chain in staged and staged[chain].item_count > 0

            if has_staged:
                status_html = (
                    "<span style='background:#FFF3CD;color:#856404;font-size:0.78rem;"
                    "padding:2px 8px;border-radius:12px;font-weight:600;'>"
                    + str(staged[chain].item_count) + " items staged \u2014 not yet saved</span>"
                )
            elif has_items:
                status_html = (
                    "<span style='background:#D4EDDA;color:#155724;font-size:0.78rem;"
                    "padding:2px 8px;border-radius:12px;font-weight:600;'>"
                    + str(len(existing_items)) + " items loaded</span>"
                )
            else:
                status_html = (
                    "<span style='background:#F8F9FA;color:#6C757D;font-size:0.78rem;"
                    "padding:2px 8px;border-radius:12px;'>Not loaded</span>"
                )

            with st.expander(
                chain + " \u2014 " + location + "  " + method_icon + " " + method_label,
                expanded=(has_staged or (method == "pdf" and not has_items)),
            ):
                col_info, col_action = st.columns([3, 2])
                with col_info:
                    flyer_day_str = ""
                    if flyer_day:
                        flyer_day_str = (
                            "<br><span style='color:#9AA8A0;'>Circular posts: "
                            "<strong style='color:#5A7A62;'>" + flyer_day + "s</strong></span>"
                        )
                    st.html(
                        "<div style='font-size:0.85rem;color:#5A7A62;line-height:1.6;'>"
                        + status_html +
                        "<br><span style='color:#9AA8A0;'>" + notes + "</span>"
                        + flyer_day_str
                        + "</div>"
                    )

                with col_action:
                    if method == "pdf":
                        if flyer_url:
                            st.html(
                                "<div style='font-size:0.8rem;margin-bottom:6px;'>"
                                "<a href='" + flyer_url + "' target='_blank' "
                                "style='color:#1E5C32;text-decoration:underline;'>"
                                "Download circular</a></div>"
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
                                with st.spinner("Reading " + chain + " circular with Claude Vision..."):
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
                                        "Extracted " + str(result.item_count) + " items from "
                                        + str(len(result.page_log)) + " pages."
                                    )
                                    st.rerun()
                                elif not result.errors:
                                    st.warning(
                                        "No items found. The PDF may be password-protected "
                                        "or have no readable sale prices."
                                    )

                    elif method == "kroger_api":
                        kroger_items = (
                            flyer_data.get("kroger_palmyra") or
                            flyer_data.get("Kroger") or []
                        )
                        if kroger_items:
                            st.html(
                                "<div style='font-size:0.85rem;color:#1E5C32;'>"
                                + str(len(kroger_items)) + " items loaded from Kroger API. "
                                "Go to <strong>Grocer Hub</strong> to refresh.</div>"
                            )
                        else:
                            st.html(
                                "<div style='font-size:0.85rem;color:#9AA8A0;'>"
                                "Pull Kroger data from the <strong>Grocer Hub</strong> page.</div>"
                            )

                    elif method == "manual":
                        st.html(
                            "<div style='font-size:0.85rem;color:#9AA8A0;'>"
                            "Manual entry only. Use the <strong>Grocer Hub</strong> "
                            "to type in items from this store's circular.</div>"
                        )

                if chain in staged:
                    result = staged[chain]
                    st.divider()
                    _render_extraction_preview(chain, result, week_start.isoformat())

    # Weekly circular checklist
    st.divider()
    st.html(
        "<div style='font-size:1.0rem;font-weight:700;color:#1E5C32;margin-bottom:4px;'>"
        "This Week's Circular Checklist</div>"
        "<div style='font-size:0.78rem;color:#5A7A62;margin-bottom:14px;'>"
        "All managed stores \u00b7 upload by their refresh day each week</div>"
    )

    flyer_data = st.session_state.get("flyer_data", {})
    today      = date.today()
    day_name   = today.strftime("%A")

    _day_colors = {
        "Wednesday": ("#1E5C32", "#D4EDDA"),
        "Friday":    ("#7A4A00", "#FFF3CD"),
        "Sunday":    ("#5D4037", "#FBF8F5"),
    }
    _method_icons = {
        "kroger_api": "API",
        "pdf":        "PDF",
        "manual":     "Manual",
    }

    rows_html = ""
    total_items = 0
    missing = []

    for s in CHARLOTTESVILLE_STORES:
        chain   = s["chain"]
        method  = s.get("method", "pdf")
        ref_day = s.get("flyer_day") or "\u2014"
        key1    = chain
        key2    = chain.lower().replace(" ", "_")
        items   = flyer_data.get(key1) or flyer_data.get(key2) or []
        count   = len(items)
        total_items += count

        if count > 0:
            status_html = (
                "<span style='background:#D4EDDA;color:#155724;font-size:0.73rem;"
                "padding:2px 8px;border-radius:10px;font-weight:600;'>" + str(count) + " items</span>"
            )
        else:
            missing.append(chain)
            status_html = (
                "<span style='background:#F8D7DA;color:#721C24;font-size:0.73rem;"
                "padding:2px 8px;border-radius:10px;font-weight:600;'>Not uploaded</span>"
            )

        fg, bg = _day_colors.get(ref_day, ("#555", "#F5F5F5"))
        today_marker = " (today)" if ref_day == day_name else ""
        day_html = (
            "<span style='background:" + bg + ";color:" + fg + ";font-size:0.70rem;"
            "padding:1px 7px;border-radius:8px;'>" + ref_day + today_marker + "</span>"
        )
        method_label = _method_icons.get(method, "PDF")

        rows_html += (
            "<tr>"
            "<td style='padding:6px 10px;border-bottom:1px solid #EEF0EE;"
            "font-size:0.86rem;font-weight:600;color:#1A2E1D;'>" + chain + "</td>"
            "<td style='padding:6px 10px;border-bottom:1px solid #EEF0EE;"
            "font-size:0.78rem;color:#5A7A62;'>" + method_label + "</td>"
            "<td style='padding:6px 10px;border-bottom:1px solid #EEF0EE;'>" + day_html + "</td>"
            "<td style='padding:6px 10px;border-bottom:1px solid #EEF0EE;'>" + status_html + "</td>"
            "</tr>"
        )

    n_loaded  = len(CHARLOTTESVILLE_STORES) - len(missing)
    n_total   = len(CHARLOTTESVILLE_STORES)
    summary_color = "#1E5C32" if not missing else "#7A4A00"
    summary_bg    = "#D4EDDA" if not missing else "#FFF3CD"
    summary_text  = (
        "All " + str(n_total) + " stores loaded \u2014 " + str(total_items) + " items ready"
        if not missing else
        str(n_loaded) + " of " + str(n_total) + " stores loaded \u00b7 still needed: " + ", ".join(missing)
    )

    st.html(
        "<table style='width:100%;border-collapse:collapse;"
        "border:1px solid #E0E0E0;border-radius:8px;overflow:hidden;margin-bottom:10px;'>"
        "<thead><tr style='background:#F0F7F1;'>"
        "<th style='padding:6px 10px;text-align:left;font-size:0.75rem;color:#5A7A62;'>Store</th>"
        "<th style='padding:6px 10px;text-align:left;font-size:0.75rem;color:#5A7A62;'>Method</th>"
        "<th style='padding:6px 10px;text-align:left;font-size:0.75rem;color:#5A7A62;'>Refresh day</th>"
        "<th style='padding:6px 10px;text-align:left;font-size:0.75rem;color:#5A7A62;'>Status</th>"
        "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table>"
        "<div style='background:" + summary_bg + ";color:" + summary_color + ";"
        "font-size:0.82rem;font-weight:600;padding:8px 12px;border-radius:6px;'>"
        + summary_text + "</div>"
    )

    with st.expander("How the circular pipeline works", expanded=False):
        st.html(
            "<div style='font-size:0.88rem;color:#3A3A3A;line-height:1.7;'>"
            "<strong>Every Wednesday morning:</strong><br>"
            "1. Visit each store's website (links above) and download the weekly circular PDF.<br>"
            "2. Upload each PDF here. Claude Vision reads the images and extracts every sale item.<br>"
            "3. Review the preview table \u2014 check that item names, prices, and categories look right.<br>"
            "4. Click Save. Items go into the app immediately and are stored in Supabase.<br>"
            "5. Run This Week's Plan \u2014 the meal planner now sees all store prices.<br><br>"
            "<strong>Data flow:</strong><br>"
            "PDF upload \u2192 PyMuPDF renders pages \u2192 Claude Vision API extracts items \u2192 "
            "IngredientCandidates \u2192 flyer_data (session) + flyer_items (Supabase)<br><br>"
            "<strong>What Claude extracts:</strong><br>"
            "Item name, sale price per unit, unit (lb/oz/each), category, and the raw price "
            "text exactly as printed (e.g. '2/$5'). Multi-buy deals are normalized to "
            "per-unit price. BOGO is set to half price when the regular price is shown.<br><br>"
            "<strong>Pilot vs. Production:</strong><br>"
            "Pilot: Tim uploads PDFs manually. One API call per page via claude-haiku-4-5. "
            "Production: Scheduled job downloads PDFs, diffs against prior week, "
            "confidence-scores each item, and queues low-confidence items for review."
            "</div>"
        )


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TAB 2 \u2014 USERS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_users:
    st.html(
        "<div style='font-size:0.85rem;color:#5A7A62;margin-bottom:16px;'>"
        "Manage platform users: grant/revoke admin access, mark test accounts, "
        "send password resets, and create test users.</div>"
    )

    if st.button("Load / Refresh user list", key="load_users_btn"):
        with st.spinner("Loading users from Supabase Auth..."):
            users = state.admin_list_users()
            st.session_state["admin_users_cache"] = users

    users = st.session_state.get("admin_users_cache", [])

    if users:
        total      = len(users)
        real_users = sum(1 for u in users if not u.get("is_test_account"))
        test_accts = sum(1 for u in users if u.get("is_test_account"))
        admins     = sum(1 for u in users if u.get("is_platform_admin"))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total users", total)
        c2.metric("Real users", real_users)
        c3.metric("Test accounts", test_accts)
        c4.metric("Admins", admins)

        st.divider()

        for u in users:
            uid       = u.get("id", "")
            email     = u.get("email", "(no email)")
            joined    = (u.get("created_at") or "")[:10] or "\u2014"
            last_in   = (u.get("last_sign_in_at") or "")[:10] or "never"
            confirmed = "yes" if u.get("email_confirmed_at") else "no"
            tier      = str(u.get("tier") or "\u2014")
            is_admin_flag = u.get("is_platform_admin", False)
            is_test_flag  = u.get("is_test_account", False)

            badge = ""
            if is_admin_flag:
                badge += " [admin]"
            if is_test_flag:
                badge += " [test]"

            with st.expander(email + badge, expanded=False):
                info_col, action_col = st.columns([2, 3])
                with info_col:
                    st.html(
                        "<div style='font-size:0.82rem;color:#5A7A62;line-height:1.8;'>"
                        "<strong>Joined:</strong> " + joined + "<br>"
                        "<strong>Last sign-in:</strong> " + last_in + "<br>"
                        "<strong>Email confirmed:</strong> " + confirmed + "<br>"
                        "<strong>Tier:</strong> " + tier + "<br>"
                        "<strong>Admin:</strong> " + ("Yes" if is_admin_flag else "No") + "<br>"
                        "<strong>Test account:</strong> " + ("Yes" if is_test_flag else "No") +
                        "</div>"
                    )
                with action_col:
                    safe_key = uid[:8] if uid else email[:8]
                    btn_cols = st.columns(2)

                    with btn_cols[0]:
                        admin_label = "Remove admin" if is_admin_flag else "Make admin"
                        if st.button(admin_label, key="adm_" + safe_key, use_container_width=True):
                            ok, msg = state.admin_set_platform_admin(uid, not is_admin_flag)
                            if ok:
                                st.session_state.pop("admin_users_cache", None)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    with btn_cols[1]:
                        test_label = "Un-mark test" if is_test_flag else "Mark as test"
                        if st.button(test_label, key="tst_" + safe_key, use_container_width=True):
                            ok, msg = state.admin_set_test_account(uid, not is_test_flag)
                            if ok:
                                st.session_state.pop("admin_users_cache", None)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                    if st.button("Send password reset", key="pw_" + safe_key, use_container_width=True):
                        ok, msg = state.admin_send_password_reset(email)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

                    confirm_key = "confirm_delete_" + safe_key
                    if st.session_state.get(confirm_key):
                        st.warning("Are you sure? This cannot be undone.")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Yes, delete", key="yes_del_" + safe_key,
                                         type="primary", use_container_width=True):
                                ok, msg = state.admin_delete_user(uid)
                                if ok:
                                    st.session_state.pop("admin_users_cache", None)
                                    st.session_state.pop(confirm_key, None)
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with cc2:
                            if st.button("Cancel", key="cancel_del_" + safe_key,
                                         use_container_width=True):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                    else:
                        if st.button("Delete user", key="del_" + safe_key, use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()

    elif "admin_users_cache" in st.session_state:
        st.info("No users found.")

    st.divider()
    st.html(
        "<div style='font-size:0.9rem;font-weight:700;color:#1E5C32;margin-bottom:8px;'>"
        "Create test account</div>"
    )
    with st.form("create_test_user_form"):
        test_email = st.text_input("Email", placeholder="test@example.com")
        test_pw    = st.text_input("Password", type="password", placeholder="minimum 6 characters")
        if st.form_submit_button("Create test account", type="primary"):
            if test_email and test_pw:
                ok, msg = state.admin_create_test_user(test_email, test_pw)
                if ok:
                    st.session_state.pop("admin_users_cache", None)
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("Email and password are required.")


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TAB 3 \u2014 DASHBOARD
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_dash:
    st.html(
        "<div style='font-size:0.85rem;color:#5A7A62;margin-bottom:16px;'>"
        "Activity feed for the pilot. Shows the last 200 events across all users.</div>"
    )

    if st.button("Load / Refresh activity", key="load_activity_btn"):
        with st.spinner("Loading activity log..."):
            activity = state.admin_get_activity(200)
            st.session_state["admin_activity_cache"] = activity

    activity = st.session_state.get("admin_activity_cache", [])

    if activity:
        now_utc = datetime.now(timezone.utc)
        seven_days_ago = now_utc - timedelta(days=7)

        def _parse_ts(ts_str):
            if not ts_str:
                return None
            try:
                return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                return None

        total_events    = len(activity)
        unique_users    = len({e.get("user_id") for e in activity if e.get("user_id")})
        recent_signins  = sum(
            1 for e in activity
            if e.get("event_type") == "sign_in"
            and (_parse_ts(e.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)) > seven_days_ago
        )
        plans_generated = sum(1 for e in activity if e.get("event_type") == "plan_generated")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total events", total_events)
        c2.metric("Unique users", unique_users)
        c3.metric("Sign-ins (7d)", recent_signins)
        c4.metric("Plans generated", plans_generated)

        st.divider()
        st.html(
            "<div style='font-size:0.88rem;font-weight:700;color:#1E5C32;margin-bottom:8px;'>"
            "Recent activity (last 50 events)</div>"
        )

        recent = activity[:50]
        rows_html = ""
        for e in recent:
            ts    = (e.get("created_at") or "")[:16].replace("T", " ")
            email = e.get("email") or (e.get("user_id") or "")[:8] or "\u2014"
            etype = e.get("event_type") or "\u2014"
            page  = e.get("page") or "\u2014"
            rows_html += (
                "<tr>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.78rem;"
                "color:#5A7A62;white-space:nowrap;'>" + ts + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.82rem;'>" + email + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.82rem;"
                "font-weight:600;color:#1E5C32;'>" + etype + "</td>"
                "<td style='padding:5px 8px;border-bottom:1px solid #EEE;font-size:0.78rem;"
                "color:#9AA8A0;'>" + page + "</td>"
                "</tr>"
            )

        st.html(
            "<div style='overflow-x:auto;max-height:480px;overflow-y:auto;"
            "border:1px solid #E0E0E0;border-radius:8px;'>"
            "<table style='width:100%;border-collapse:collapse;'>"
            "<thead><tr style='background:#F0F7F1;'>"
            "<th style='padding:6px 8px;text-align:left;font-size:0.75rem;color:#5A7A62;"
            "border-bottom:2px solid #C8E6C9;'>Time (UTC)</th>"
            "<th style='padding:6px 8px;text-align:left;font-size:0.75rem;color:#5A7A62;"
            "border-bottom:2px solid #C8E6C9;'>User</th>"
            "<th style='padding:6px 8px;text-align:left;font-size:0.75rem;color:#5A7A62;"
            "border-bottom:2px solid #C8E6C9;'>Event</th>"
            "<th style='padding:6px 8px;text-align:left;font-size:0.75rem;color:#5A7A62;"
            "border-bottom:2px solid #C8E6C9;'>Page</th>"
            "</tr></thead>"
            "<tbody>" + rows_html + "</tbody>"
            "</table></div>"
        )

    elif "admin_activity_cache" in st.session_state:
        st.info("No activity recorded yet.")


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# TAB 4 \u2014 FEEDBACK
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
with tab_fb:
    st.html(
        "<div style='font-size:0.85rem;color:#5A7A62;margin-bottom:16px;'>"
        "Feedback submitted by signed-in users via the sidebar. "
        "Mark items read or archive them once actioned.</div>"
    )

    fb_filter = st.radio(
        "Show",
        ["All", "New", "Read", "Archived"],
        horizontal=True,
        key="fb_filter",
        label_visibility="collapsed",
    )

    if st.button("Load / Refresh feedback", key="load_fb_btn"):
        status_arg = fb_filter.lower() if fb_filter != "All" else "all"
        with st.spinner("Loading feedback..."):
            feedback_rows = state.admin_get_feedback(status_arg)
            st.session_state["admin_feedback_cache"] = feedback_rows
            st.session_state["admin_feedback_filter"] = fb_filter

    feedback_rows = st.session_state.get("admin_feedback_cache", [])
    cached_filter = st.session_state.get("admin_feedback_filter", "All")
    if feedback_rows and fb_filter != "All" and fb_filter != cached_filter:
        feedback_rows = [r for r in feedback_rows if r.get("status") == fb_filter.lower()]

    if feedback_rows:
        st.html(
            "<div style='font-size:0.82rem;color:#5A7A62;margin-bottom:8px;'>"
            + str(len(feedback_rows)) + " item(s) shown</div>"
        )

        for row in feedback_rows:
            row_id  = row.get("id", "")
            ts      = (row.get("created_at") or "")[:16].replace("T", " ")
            email   = row.get("email") or "\u2014"
            page    = row.get("page") or "\u2014"
            rating  = row.get("rating")
            message = row.get("message") or "(no message)"
            status  = row.get("status") or "new"

            stars = ""
            if rating:
                stars = ("\u2605" * int(rating)) + ("\u2606" * (5 - int(rating)))
            else:
                stars = "\u2014"

            status_color = {"new": "#856404", "read": "#155724", "archived": "#6C757D"}.get(status, "#555")
            status_bg    = {"new": "#FFF3CD", "read": "#D4EDDA", "archived": "#F8F9FA"}.get(status, "#F5F5F5")

            header = ts + " \u00b7 " + email + " \u00b7 " + page
            with st.expander(header, expanded=(status == "new")):
                st.html(
                    "<div style='font-size:0.85rem;line-height:1.7;'>"
                    "<strong>Rating:</strong> " + stars + "<br>"
                    "<strong>Status:</strong> "
                    "<span style='background:" + status_bg + ";color:" + status_color + ";"
                    "font-size:0.75rem;padding:1px 8px;border-radius:10px;'>" + status + "</span><br>"
                    "<strong>Message:</strong><br>"
                    "<div style='background:#F8F9FA;padding:8px 12px;border-radius:6px;"
                    "margin-top:4px;font-size:0.83rem;color:#3A3A3A;'>" + message + "</div>"
                    "</div>"
                )

                safe_id = str(row_id)[:8] if row_id else "unk"
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    if status != "read" and st.button(
                        "Mark read", key="fb_read_" + safe_id, use_container_width=True
                    ):
                        state._sb_update("feedback", {"status": "read"}, "id", row_id)
                        st.session_state.pop("admin_feedback_cache", None)
                        st.rerun()
                with ac2:
                    if status != "archived" and st.button(
                        "Archive", key="fb_arch_" + safe_id, use_container_width=True
                    ):
                        state._sb_update("feedback", {"status": "archived"}, "id", row_id)
                        st.session_state.pop("admin_feedback_cache", None)
                        st.rerun()
                with ac3:
                    if status == "archived" and st.button(
                        "Restore to new", key="fb_restore_" + safe_id, use_container_width=True
                    ):
                        state._sb_update("feedback", {"status": "new"}, "id", row_id)
                        st.session_state.pop("admin_feedback_cache", None)
                        st.rerun()

    elif "admin_feedback_cache" in st.session_state:
        st.info("No feedback items match the current filter.")
    else:
        st.info("Click \"Load / Refresh feedback\" to see submitted feedback.")
