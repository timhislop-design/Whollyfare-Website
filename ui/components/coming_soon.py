"""
ui/components/coming_soon.py — WhollyFare "Coming Soon" stub page component

Used as the body of any page that is planned but not yet built.
Renders a consistent, on-brand placeholder with an optional ETA and description.

POC:  Static placeholder.
PROD: ETA pulled from feature_flags table; "notify me" CTA writes to a
      waitlist table and triggers an email via Supabase Edge Function.

Usage:
    from ui.components.coming_soon import coming_soon_page
    coming_soon_page(
        title="Coupon Vault",
        icon="🎟️",
        description="Auto-matched coupons from your grocery stores, applied to your plan before checkout.",
        eta="Phase 2 — Summer 2026",
    )
"""

import streamlit as st
from ui.style import page_header, COLORS


_CSS = """
<style>
.wf-coming-soon-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 24px 40px;
  text-align: center;
}
.wf-cs-icon {
  font-size: 3.5rem;
  line-height: 1;
  margin-bottom: 16px;
}
.wf-cs-badge {
  display: inline-block;
  background: #D8EDD0;
  color: #1E5C32;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 20px;
}
.wf-cs-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: #1E5C32;
  margin-bottom: 12px;
}
.wf-cs-desc {
  font-size: 0.95rem;
  color: #5A7A62;
  max-width: 460px;
  line-height: 1.6;
  margin-bottom: 20px;
}
.wf-cs-eta {
  font-size: 0.8rem;
  color: #5A7A62;
  font-style: italic;
}
</style>
"""


def coming_soon_page(
    title: str,
    icon: str = "🚧",
    description: str = "This feature is in development and will be available soon.",
    eta: str | None = None,
    subtitle: str = "",
) -> None:
    """
    Render a full Coming Soon stub page.

    Args:
        title:       Feature name, e.g. "Coupon Vault"
        icon:        Emoji icon displayed large above the title
        description: One or two sentences describing what the feature will do
        eta:         Optional timeline string, e.g. "Phase 2 — Summer 2026"
        subtitle:    Optional page header subtitle (shown in the wf-header bar)
    """
    page_header(title, subtitle)
    st.html(_CSS)

    eta_html = (
        f'<div class="wf-cs-eta">📅 {eta}</div>' if eta else ""
    )

    st.html(
        f"""<div class="wf-coming-soon-wrap">
          <div class="wf-cs-icon">{icon}</div>
          <div class="wf-cs-badge">COMING SOON</div>
          <div class="wf-cs-title">{title}</div>
          <div class="wf-cs-desc">{description}</div>
          {eta_html}
        </div>""")
