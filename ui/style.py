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

LOGO_SVG = """
<svg width="148" height="36" viewBox="0 0 148 36" xmlns="http://www.w3.org/2000/svg"
     aria-label="WhollyFare logo" role="img">
  <g transform="translate(3, 2)">
    <line x1="8"  y1="31" x2="8"  y2="6"  stroke="#3A8C4E" stroke-width="2"   stroke-linecap="round"/>
    <line x1="5"  y1="6"  x2="5"  y2="17" stroke="#3A8C4E" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="8"  y1="6"  x2="8"  y2="17" stroke="#3A8C4E" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="11" y1="6"  x2="11" y2="17" stroke="#3A8C4E" stroke-width="1.5" stroke-linecap="round"/>
    <ellipse cx="19" cy="16" rx="9" ry="6" fill="#5DAA6A" transform="rotate(-28 19 16)"/>
    <line x1="12" y1="21" x2="25" y2="12" stroke="#1E5C32" stroke-width="0.9" stroke-linecap="round"/>
    <circle cx="18" cy="15" r="1.2" fill="#1E5C32"/>
  </g>
  <text x="36" y="23" font-family="Arial, sans-serif" font-size="17" font-weight="600"
        fill="#1E5C32">WhollyFare</text>
</svg>
"""

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
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    inject()
    st.markdown(
        f"""<div class="wf-header">
          {LOGO_SVG}
          <div class="wf-page-title">{title}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f'<div class="wf-page-sub">{subtitle}</div>', unsafe_allow_html=True)


def sidebar_nav():
    """Render branded sidebar navigation.

    Call this inside a ``with st.sidebar:`` block on every page, e.g.::

        with st.sidebar:
            sidebar_nav()
    """
    # Hide Streamlit's auto-generated file-based nav
    st.markdown(
        "<style>[data-testid=\"stSidebarNav\"] { display: none !important; }</style>",
        unsafe_allow_html=True,
    )

    # ── Logo (light strokes for dark sidebar background) ─────────────────────
    SIDEBAR_LOGO = """
<svg width="52" height="52" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg"
     aria-label="WhollyFare leaf and fork icon" role="img">
  <g transform="translate(3, 2)">
    <line x1="8"  y1="31" x2="8"  y2="6"  stroke="#9FD9A8" stroke-width="2"   stroke-linecap="round"/>
    <line x1="5"  y1="6"  x2="5"  y2="17" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="8"  y1="6"  x2="8"  y2="17" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="11" y1="6"  x2="11" y2="17" stroke="#9FD9A8" stroke-width="1.5" stroke-linecap="round"/>
    <ellipse cx="19" cy="16" rx="9" ry="6" fill="#5DAA6A" transform="rotate(-28 19 16)"/>
    <line x1="12" y1="21" x2="25" y2="12" stroke="#ffffff" stroke-width="0.9" stroke-linecap="round"/>
    <circle cx="18" cy="15" r="1.2" fill="#ffffff"/>
  </g>
</svg>
"""

    st.markdown(SIDEBAR_LOGO, unsafe_allow_html=True)

    # ── Wordmark & tagline ────────────────────────────────────────────────────
    st.markdown(
        """<div style="margin-top:-4px; margin-bottom:4px;">
          <span style="font-size:1.25rem; font-weight:700; color:#ffffff;
                       font-family:Arial,sans-serif; letter-spacing:0.02em;">
            WhollyFare
          </span><br>
          <span style="font-size:0.75rem; color:#9FD9A8;
                       font-family:Arial,sans-serif; font-style:italic;">
            Eat well. Spend less.
          </span>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#3A8C4E; margin:10px 0;'>", unsafe_allow_html=True)

    # ── Home ─────────────────────────────────────────────────────────────────
    st.page_link("Home.py", label="🏠 Home")

    # ── Section: GET STARTED ──────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem; font-weight:700; color:#9FD9A8; "
        "letter-spacing:0.08em; margin-top:14px; margin-bottom:4px;'>GET STARTED</div>",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Household.py",  label="👨‍👩‍👧 Household Setup")
    st.page_link("pages/2_Grocer_Hub.py", label="🏪 Grocer Hub")

    # ── Section: WEEKLY PLAN ──────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem; font-weight:700; color:#9FD9A8; "
        "letter-spacing:0.08em; margin-top:14px; margin-bottom:4px;'>WEEKLY PLAN</div>",
        unsafe_allow_html=True,
    )
    st.page_link("pages/3_Plan.py",           label="🍽️ This Week's Plan")
    st.page_link("pages/4_Sunday_BuyOff.py",  label="✅ Sunday Buy-Off")
    st.page_link("pages/5_Shopping_List.py",  label="🛒 Shopping List")

    # ── Section: HISTORY & INFO ───────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.65rem; font-weight:700; color:#9FD9A8; "
        "letter-spacing:0.08em; margin-top:14px; margin-bottom:4px;'>HISTORY &amp; INFO</div>",
        unsafe_allow_html=True,
    )
    st.page_link("pages/6_Ledger.py",   label="💰 Found Money Ledger")
    st.page_link("pages/7_Investor.py", label="📈 Investor Brief")
