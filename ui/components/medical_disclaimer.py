"""
ui/components/medical_disclaimer.py — WhollyFare medical authority disclaimer

Used on any page that surfaces health-related constraints, dietary guidance,
or condition-based ingredient filtering.

POC:  Static citations rendered inline.
PROD: Citations pulled from constraint_evidence_sources table, linked to the
      specific constraint engine rule that triggered the rejection.

Usage:
    from ui.components.medical_disclaimer import medical_disclaimer, source_pill
    medical_disclaimer()                   # full disclaimer block
    source_pill("AHA", "https://...")     # inline citation badge
"""

import streamlit as st


# ── Authority sources referenced by the constraint engine ─────────────────────
# POC: hard-coded here. PROD: read from constraint_evidence_sources table.
EVIDENCE_SOURCES = {
    "AHA":    ("American Heart Association",   "https://www.heart.org"),
    "NKF":    ("National Kidney Foundation",   "https://www.kidney.org"),
    "ADA":    ("American Diabetes Association","https://www.diabetes.org"),
    "CDF":    ("Celiac Disease Foundation",    "https://celiac.org"),
    "FARE":   ("Food Allergy Research & Education", "https://www.foodallergy.org"),
    "Monash": ("Monash University FODMAP",     "https://www.monash.edu/medicine/ccs/gastroenterology"),
    "NIH":    ("National Institutes of Health","https://www.nih.gov"),
    "ACAAI":  ("American College of Allergy, Asthma & Immunology", "https://acaai.org"),
}

_DISCLAIMER_CSS = """
<style>
.wf-disclaimer {
  background: #F0F7F0;
  border: 1px solid #C5DFC9;
  border-left: 4px solid #3A8C4E;
  border-radius: 8px;
  padding: 14px 16px;
  margin: 12px 0;
  font-size: 12px;
  color: #3A5C40;
}
.wf-disclaimer strong { color: #1E5C32; }
.wf-disclaimer a { color: #3A8C4E; text-decoration: underline; }
.wf-src-pill {
  display: inline-block;
  background: #D8EDD0;
  color: #1E5C32;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  margin: 0 2px;
  text-decoration: none;
  vertical-align: middle;
}
.wf-src-pill:hover { background: #C5DFC9; }
</style>
"""


def medical_disclaimer(
    condition: str | None = None,
    sources: list[str] | None = None,
    show_step_back: bool = True,
) -> None:
    """
    Render a medical disclaimer block.

    Args:
        condition:     If provided, names the specific condition (e.g. "CKD Stage 3").
                       If None, renders a generic health-constraint disclaimer.
        sources:       List of source keys from EVIDENCE_SOURCES to cite.
                       E.g. ["NKF", "ADA"]. If None, no citations shown.
        show_step_back: If True, adds the "step back" advisory to consult a
                        healthcare provider before acting on these filters.
    """
    st.html(_DISCLAIMER_CSS)

    condition_line = (
        f"<strong>Health filters active for: {condition}</strong><br>"
        if condition
        else "<strong>Health constraints active</strong><br>"
    )

    source_line = ""
    if sources:
        pills = []
        for key in sources:
            if key in EVIDENCE_SOURCES:
                name, url = EVIDENCE_SOURCES[key]
                pills.append(f'<a class="wf-src-pill" href="{url}" target="_blank">{key}</a>')
        if pills:
            source_line = f"<div style='margin-top:6px;'>Sources: {''.join(pills)}</div>"

    step_back = ""
    if show_step_back:
        step_back = (
            "<div style='margin-top:6px; font-style:italic;'>"
            "WhollyFare applies dietary guidelines conservatively. "
            "Always consult your healthcare provider before making changes to a "
            "medically supervised diet."
            "</div>"
        )

    st.html(
        f"""<div class="wf-disclaimer">
          {condition_line}
          Ingredients flagged below are excluded based on published clinical guidelines.
          {source_line}
          {step_back}
        </div>""")


def source_pill(key: str, url: str | None = None) -> str:
    """
    Return an HTML citation badge string for inline use.

    Args:
        key:  Short source key, e.g. "AHA". Looked up in EVIDENCE_SOURCES.
              If not found, the key itself is used as the label.
        url:  Override URL. If None, falls back to EVIDENCE_SOURCES lookup.

    Returns:
        HTML string — safe to embed via st.html(...).

    Example:
        st.html(
            f"Potassium restriction per {source_pill('NKF')} guideline.")
    """
    st.html(_DISCLAIMER_CSS)

    if key in EVIDENCE_SOURCES:
        label, default_url = EVIDENCE_SOURCES[key]
        href = url or default_url
        title = label
    else:
        label = key
        href = url or "#"
        title = key

    return f'<a class="wf-src-pill" href="{href}" target="_blank" title="{title}">{label}</a>'
