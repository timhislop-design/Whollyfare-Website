"""
style.py — WhollyFare brand CSS. Direction A: Leaf + Fork, garden green family.
"""

import streamlit as st

# ── Brand tokens ──────────────────────────────────────────────────────────────
COLORS = {
    "garden_deep":   "#1E5C32",   # primary text, headings, logo
    "fresh_herb":    "#3A8C4E",   # buttons, CTAs, nav active
    "leaf":          "#5DAA6A",   # accents, hover states
    "sprout":        "#D8EDD0",   # card backgrounds, light fills
    "found_money":   "#F28B30",   # savings highlights
    "found_dark":    "#BF5E00",   # found money text
    "cream":         "#FAFAF7",   # page background
    "cream_border":  "#D8EDD0",   # page borders
    "surface":       "#FFFFFF",
    "muted":         "#5A7A62",   # secondary text
    "danger":        "#B91C1C",
}

# Logo data URIs — base64-encoded SVGs used as <img> src.
# Using data URIs instead of inline SVG avoids st.html() iframe height-collapse
# issues on Streamlit Cloud, where the ResizeObserver sometimes fails to detect
# the natural height of flex containers containing inline SVG elements.
LOGO_ICON_DARK  = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDQiIGhlaWdodD0iNDQiIHZpZXdCb3g9IjAgMCA1MiA1MiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48bGluZSB4MT0iMTQiIHkxPSI0NiIgeDI9IjE0IiB5Mj0iMTAiIHN0cm9rZT0iIzNBOEM0RSIgc3Ryb2tlLXdpZHRoPSIyLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSI5IiB5MT0iMTAiIHgyPSI5IiB5Mj0iMjQiIHN0cm9rZT0iIzNBOEM0RSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTQiIHkxPSIxMCIgeDI9IjE0IiB5Mj0iMjQiIHN0cm9rZT0iIzNBOEM0RSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTkiIHkxPSIxMCIgeDI9IjE5IiB5Mj0iMjQiIHN0cm9rZT0iIzNBOEM0RSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48ZWxsaXBzZSBjeD0iMzYiIGN5PSIyNiIgcng9IjEzIiByeT0iOC41IiBmaWxsPSIjNURBQTZBIiB0cmFuc2Zvcm09InJvdGF0ZSgtMjggMzYgMjYpIi8+PGxpbmUgeDE9IjI0IiB5MT0iMzUiIHgyPSI0NiIgeTI9IjE4IiBzdHJva2U9IiM5RkQ5QTgiIHN0cm9rZS13aWR0aD0iMS4zIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMjgiIHkxPSIzMiIgeDI9IjQwIiB5Mj0iMjEiIHN0cm9rZT0iIzlGRDlBOCIgc3Ryb2tlLXdpZHRoPSIwLjciIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC43Ii8+PC9zdmc+"   # green icon — for white/light backgrounds
LOGO_ICON_LIGHT = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDQiIGhlaWdodD0iNDQiIHZpZXdCb3g9IjAgMCA1MiA1MiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48bGluZSB4MT0iMTQiIHkxPSI0NiIgeDI9IjE0IiB5Mj0iMTAiIHN0cm9rZT0iIzlGRDlBOCIgc3Ryb2tlLXdpZHRoPSIyLjgiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSI5IiB5MT0iMTAiIHgyPSI5IiB5Mj0iMjQiIHN0cm9rZT0iIzlGRDlBOCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTQiIHkxPSIxMCIgeDI9IjE0IiB5Mj0iMjQiIHN0cm9rZT0iIzlGRDlBOCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTkiIHkxPSIxMCIgeDI9IjE5IiB5Mj0iMjQiIHN0cm9rZT0iIzlGRDlBOCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48ZWxsaXBzZSBjeD0iMzYiIGN5PSIyNiIgcng9IjEzIiByeT0iOC41IiBmaWxsPSIjNURBQTZBIiB0cmFuc2Zvcm09InJvdGF0ZSgtMjggMzYgMjYpIi8+PGxpbmUgeDE9IjI0IiB5MT0iMzUiIHgyPSI0NiIgeTI9IjE4IiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMS4zIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMjgiIHkxPSIzMiIgeDI9IjQwIiB5Mj0iMjEiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIwLjciIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC43Ii8+PC9zdmc+"  # light icon — for dark backgrounds (sidebar)
LOGO_ICON_HERO  = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDUyIDUyIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxsaW5lIHgxPSIxNCIgeTE9IjQ2IiB4Mj0iMTQiIHkyPSIxMCIgc3Ryb2tlPSIjOUZEOUE4IiBzdHJva2Utd2lkdGg9IjIuOCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PGxpbmUgeDE9IjkiIHkxPSIxMCIgeDI9IjkiIHkyPSIyNCIgc3Ryb2tlPSIjOUZEOUE4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSIxNCIgeTE9IjEwIiB4Mj0iMTQiIHkyPSIyNCIgc3Ryb2tlPSIjOUZEOUE4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSIxOSIgeTE9IjEwIiB4Mj0iMTkiIHkyPSIyNCIgc3Ryb2tlPSIjOUZEOUE4IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxlbGxpcHNlIGN4PSIzNiIgY3k9IjI2IiByeD0iMTMiIHJ5PSI4LjUiIGZpbGw9IiM1REFBNkEiIHRyYW5zZm9ybT0icm90YXRlKC0yOCAzNiAyNikiLz48bGluZSB4MT0iMjQiIHkxPSIzNSIgeDI9IjQ2IiB5Mj0iMTgiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIxLjMiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSIyOCIgeTE9IjMyIiB4Mj0iNDAiIHkyPSIyMSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjAuNyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBvcGFjaXR5PSIwLjUiLz48bGluZSB4MT0iMzIiIHkxPSIyOSIgeDI9IjQzIiB5Mj0iMjQiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIwLjciIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC40Ii8+PC9zdmc+"   # large light icon — for hero section overlay

# Legacy: keep LOGO_SVG as a fallback for any code that references it directly
LOGO_SVG = f'''<img src="{LOGO_ICON_DARK}" width="40" height="40"
     alt="WhollyFare fork and leaf logo" style="vertical-align:middle;">'''

CSS = """
<style>
/* ── Brand palette ──────────────────────────────────────────────────────── */
:root {
  --garden-deep:  #1E5C32;
  --fresh-herb:   #3A8C4E;
  --leaf:         #5DAA6A;
  --sprout:       #D8EDD0;
  --found-money:  #F28B30;
  --found-dark:   #BF5E00;
  --cream:        #FAFAF7;
  --cream-border: #D8EDD0;
  --surface:      #FFFFFF;
  --muted:        #5A7A62;
  --danger:       #B91C1C;
}

/* ── Global ─────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: Arial, sans-serif !important;
}
.main .block-container {
  padding-top: 1.5rem;
  max-width: 980px;
  background-color: var(--cream);
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: var(--garden-deep) !important;
}
[data-testid="stSidebar"] * {
  color: #e8f5ec !important;
}
[data-testid="stSidebarNav"] a {
  color: #b8dbc2 !important;
  border-radius: 6px;
}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a[aria-selected="true"] {
  color: #ffffff !important;
  background: rgba(90,170,106,0.25) !important;
  border-radius: 6px;
}

/* ── Page heading ────────────────────────────────────────────────────────── */
.wf-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0.2rem;
}
.wf-page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--garden-deep);
  margin: 0;
}
.wf-page-sub {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 1.2rem;
  margin-left: 2px;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
div[data-testid="stButton"] > button[kind="primary"] {
  background-color: var(--fresh-herb) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background-color: var(--garden-deep) !important;
}

/* ── Status pills ────────────────────────────────────────────────────────── */
.pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.pill-ok   { background: #E3F4E8; color: var(--garden-deep); }
.pill-warn { background: #FFF3E0; color: #8C4A00; }
.pill-miss { background: #FFEBEE; color: var(--danger); }
.pill-api  { background: var(--sprout); color: var(--fresh-herb); }
.pill-muted{ background: var(--cream); color: var(--muted); border: 1px solid var(--cream-border); }

/* ── Store card ──────────────────────────────────────────────────────────── */
.store-card {
  background: var(--surface);
  border: 1px solid var(--cream-border);
  border-left: 4px solid var(--cream-border);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.store-card.ok   { border-left-color: var(--fresh-herb); }
.store-card.api  { border-left-color: var(--leaf); }
.store-card.warn { border-left-color: var(--found-money); }
.store-name { font-weight: 700; color: var(--garden-deep); font-size: 14px; }
.store-meta { font-size: 12px; color: var(--muted); margin-top: 3px; }

/* ── Found Money big number ──────────────────────────────────────────────── */
.found-money-box {
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border: 1px solid #FFCC80;
  border-radius: 12px;
  padding: 20px 24px;
  text-align: center;
}
.found-money-amount {
  font-size: 3rem;
  font-weight: 800;
  color: var(--found-dark);
  line-height: 1;
}
.found-money-label {
  font-size: 0.85rem;
  color: var(--found-money);
  margin-top: 4px;
  font-weight: 600;
}

/* ── Metric tweaks ───────────────────────────────────────────────────────── */
[data-testid="stMetric"] label {
  font-size: 12px !important;
  color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.6rem !important;
  font-weight: 700 !important;
  color: var(--garden-deep) !important;
}

/* ── Ingredient hero card ────────────────────────────────────────────────── */
.hero-card {
  background: var(--surface);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-left: 3px solid var(--fresh-herb);
  border: 0.5px solid var(--cream-border);
}

/* ── Constraint audit table ──────────────────────────────────────────────── */
.audit-row {
  padding: 6px 0;
  border-bottom: 1px solid #EEF3EE;
  font-size: 12px;
}
.audit-reason { color: var(--danger); font-weight: 600; }
.audit-member { color: var(--fresh-herb); }

/* ── Expander overrides ───────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  border: 0.5px solid var(--cream-border) !important;
  border-radius: 8px !important;
  background: var(--surface) !important;
}

/* ── Dataframe / table ───────────────────────────────────────────────────── */
[data-testid="stDataFrame"] thead th {
  background-color: var(--sprout) !important;
  color: var(--garden-deep) !important;
  font-weight: 600 !important;
  font-size: 12px !important;
}

/* ── Download button ─────────────────────────────────────────────────────── */
div[data-testid="stDownloadButton"] > button {
  border-color: var(--fresh-herb) !important;
  color: var(--fresh-herb) !important;
}
div[data-testid="stDownloadButton"] > button:hover {
  background-color: var(--sprout) !important;
}
</style>
"""


def inject():
    st.html(CSS)


def scroll_to_top():
    """
    Flag that the next page render should scroll to the top of the viewport.
    Call this before st.rerun() on any save/generate action.
    """
    import streamlit as _st
    _st.session_state["_scroll_to_top"] = True


def maybe_scroll_to_top():
    """
    Call near the top of each page render (after state.init()).
    If scroll_to_top() was called before the last rerun, scrolls viewport to 0.
    Uses window.parent to reach the Streamlit host frame from the component iframe.
    """
    import streamlit as _st
    if not _st.session_state.pop("_scroll_to_top", False):
        return
    import streamlit.components.v1 as _comps
    _js = (
        "<script>"
        "(function(){"
        "var s=['[data-testid=\'stMain\']','section.main','.main'];"
        "for(var i=0;i<s.length;i++){"
        "var e=window.parent.document.querySelector(s[i]);"
        "if(e){e.scrollTop=0;break;}"
        "}"
        "window.parent.scrollTo(0,0);"
        "})();"
        "</script>"
    )
    _comps.html(_js, height=0)


def page_header(title: str, subtitle: str = ""):
    """Render the standard page header with fork+leaf logo and page title.

    Uses a base64 data URI <img> tag — this avoids the Streamlit Cloud iframe
    height-collapse bug where st.html() with inline SVG sometimes renders to 0px.
    All styles are inline so there is no dependency on inject() CSS being applied
    in a separate iframe.
    """
    inject()  # still called for sidebar + button styles on the main page
    st.html(
        f'''<div style="display:flex;align-items:center;gap:12px;
                        margin-bottom:0.2rem;min-height:56px;padding:4px 0;">
          <img src="{LOGO_ICON_DARK}" width="44" height="44"
               alt="WhollyFare logo" style="flex-shrink:0;">
          <div style="font-size:1.5rem;font-weight:700;color:#1E5C32;
                      margin:0;font-family:Arial,sans-serif;">''' + title + '''</div>
        </div>'''
    )
    if subtitle:
        st.html(
            '<div style="font-size:0.85rem;color:#5A7A62;'
            'margin-bottom:1.2rem;margin-left:2px;'
            f'font-family:Arial,sans-serif;">' + subtitle + '</div>'
        )


def sidebar_nav():
    """Render branded sidebar navigation.

    Call this inside a ``with st.sidebar:`` block on every page, e.g.::

        with st.sidebar:
            sidebar_nav()
    """
    # Hide Streamlit's auto-generated file-based nav
    st.html("<style>[data-testid=\"stSidebarNav\"] { display: none !important; }</style>")

    # ── Logo + wordmark in one block so they appear side-by-side ─────────────
    # IMPORTANT: one single st.html() call keeps SVG + text in the same iframe.
    # Splitting across two st.html() calls causes the bare SVG iframe to collapse
    # to 0 height in Streamlit 1.31+ because it has no wrapper div to anchor it.
    st.html(
        f'''<div style="display:flex;align-items:center;gap:10px;
                       padding:6px 0;margin-bottom:2px;min-height:60px;">
          <img src="{LOGO_ICON_LIGHT}" width="44" height="44"
               alt="WhollyFare logo" style="flex-shrink:0;">
          <div>
            <div style="font-size:1.2rem;font-weight:700;color:#ffffff;
                        font-family:Arial,sans-serif;letter-spacing:0.02em;
                        line-height:1.2;">WhollyFare</div>
            <div style="font-size:0.72rem;color:#9FD9A8;
                        font-family:Arial,sans-serif;font-style:italic;">
              The meal plan that pays you back.
            </div>
          </div>
        </div>'''
    )

    st.html("<hr style='border-color:#3A8C4E; margin:10px 0;'>")

    def _section(label: str):
        st.html(
            f"<div style='font-size:0.65rem; font-weight:700; color:#9FD9A8; "
            f"letter-spacing:0.08em; margin-top:14px; margin-bottom:4px;'>{label}</div>"
        )

    def _coming_soon(label: str):
        st.html(
            f"<div style='font-size:0.85rem; color:#6aaa7a; padding:4px 8px; "
            f"opacity:0.6; cursor:default;'>{label} "
            f"<span style='font-size:0.6rem; background:#2e7d4f; color:#9FD9A8; "
            f"padding:1px 5px; border-radius:8px; vertical-align:middle;'>SOON</span></div>"
        )

    # ── Home ─────────────────────────────────────────────────────────────────
    st.page_link("Home.py", label="🏠 Home")

    # ── GET STARTED ───────────────────────────────────────────────────────────
    _section("GET STARTED")
    st.page_link("pages/1_Household.py",  label="👨‍👩‍👧 Household Setup")
    st.page_link("pages/2_Grocer_Hub.py", label="🏪 Grocer Hub")

    # ── WEEKLY PLAN ───────────────────────────────────────────────────────────
    _section("WEEKLY PLAN")
    st.page_link("pages/0_This_Week.py",      label="📅 This Week")
    st.page_link("pages/3_Plan.py",           label="🍽️ Meal Plan")
    st.page_link("pages/4_Sunday_BuyOff.py",  label="✅ Sunday Buy-Off")
    st.page_link("pages/5_Shopping_List.py",  label="🛍️ Shopping List")
    st.page_link("pages/10_Pantry.py",         label="🧂 My Pantry")
    st.page_link("pages/12_Recipes.py",        label="📖 Recipe Library")

    # ── SAVINGS INTELLIGENCE ──────────────────────────────────────────────────
    _section("SAVINGS INTELLIGENCE")
    st.page_link("pages/6_Ledger.py", label="💰 Found Money Ledger")
    _coming_soon("🎟️ Coupon Vault")
    _coming_soon("📊 Price Intelligence")

    # ── HEALTH GUARD ──────────────────────────────────────────────────────────
    _section("HEALTH GUARD")
    _coming_soon("🛡️ Health Guard Dashboard")

    # ── DELIVERY ──────────────────────────────────────────────────────────────
    _section("DELIVERY")
    _coming_soon("🚚 Delivery Hub")

    # ── PLATFORM ──────────────────────────────────────────────────────────────
    _section("PLATFORM")
    st.page_link("pages/7_Investor.py", label="📈 Investor Brief")
    st.page_link("pages/8_Roadmap.py",  label="🗺️ Product Roadmap")
    _coming_soon("❓ Help & FAQ")
    st.page_link("pages/9_Account.py", label="⚙️ Account")

    # Admin link — only visible to signed-in platform admins.
    # Import inline to avoid circular dependency at module load.
    try:
        import ui.state as _state
        if _state.is_admin():
            st.page_link("pages/11_Admin.py", label="🗂️ Admin Console")
    except Exception:
        pass

    # ── Feedback footer ───────────────────────────────────────────────────────
    # Shown to all signed-in users. Feedback goes to the admin dashboard.
    try:
        import ui.state as _state_fb
        if _state_fb.is_authenticated():
            st.html(
                "<div style='margin-top:18px;padding-top:10px;"
                "border-top:1px solid #2e7d4f;'>"
                "<a href='?feedback=1' style='font-size:0.72rem;color:#9FD9A8;"
                "text-decoration:none;opacity:0.8;'>💬 Share feedback</a>"
                "</div>"
            )
    except Exception:
        pass

    # ── Feedback form handler (sidebar inline form when ?feedback=1) ──────────
    # Shown to all signed-in users. Detects the ?feedback=1 query param set by
    # the "Share feedback" link in the sidebar footer.
    try:
        import ui.state as _state_fb2
        if _state_fb2.is_authenticated():
            _qp = st.query_params
            if _qp.get("feedback") == "1":
                with st.expander("Share feedback", expanded=True):
                    with st.form("sidebar_feedback_form", clear_on_submit=True):
                        _fb_msg = st.text_area(
                            "What\'s on your mind?",
                            placeholder="Bug, suggestion, question \u2014 anything helps.",
                            height=100,
                            label_visibility="collapsed",
                        )
                        _fb_rating = st.select_slider(
                            "How is your experience?",
                            options=[1, 2, 3, 4, 5],
                            value=4,
                            label_visibility="visible",
                        )
                        if st.form_submit_button("Send feedback", type="primary", use_container_width=True):
                            if _fb_msg.strip():
                                _ok, _msg = _state_fb2.submit_feedback(
                                    message=_fb_msg.strip(),
                                    page="sidebar",
                                    rating=_fb_rating,
                                )
                                if _ok:
                                    st.success("Thanks! Feedback sent.")
                                    st.query_params.clear()
                                    st.rerun()
                                else:
                                    st.error(_msg)
                            else:
                                st.warning("Please enter a message before sending.")
    except Exception:
        pass

    # ── Auth widget ─────────────────────────────────────────────────────────────
    # POC: sign-in / sign-up / sign-out panel at the bottom of the sidebar.
    # Import here (not at module level) to avoid circular import with state.py.
    try:
        from ui.components.auth import auth_sidebar
        auth_sidebar()
    except Exception:
        pass  # Silently skip if auth component is unavailable