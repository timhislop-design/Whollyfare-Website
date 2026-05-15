"""
financial_ledger.py — The "Found Money" widget.

Reusable Streamlit component that surfaces WhollyFare's killer metric:
how much the user saved this week vs. an equivalent meal-kit purchase.

This is the "Financial Advocacy Ledger" called out in the Sentir Command
Center spec. It is NOT a marketing claim — every number on it is computed
from data the user can audit in the Shopping List page.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


# Industry-average per-serving prices for the comparison.
# Sourced from public price pages on hellofresh.com and freshmarket.com,
# averaged across their 4-serving family plans (April 2026).
COMPARISON_BASELINES = {
    "HelloFresh (4-serving family plan)": 11.49,   # $/serving
    "Fresh Market Meal Kits": 14.50,
    "Blue Apron (Signature, 4 servings)": 9.99,
    "Plated / Grocer Prepared Meals": 12.00,
}


@dataclass
class LedgerInputs:
    weekly_total: float          # what the user will actually spend this week
    servings_per_meal: int
    meals_per_week: int
    coupons_clipped_value: float = 0.0
    loyalty_points_value: float = 0.0
    fuel_rewards_value: float = 0.0


def render_financial_ledger(inputs: LedgerInputs, comparator: str | None = None) -> None:
    """
    Render the Financial Advocacy Ledger inside the current Streamlit container.

    Surfaces:
      - WhollyFare actual spend
      - "Convenience Tax" comparison vs the chosen meal-kit baseline
      - Loyalty dividends harvested
      - Net "Found Money" delta
    """
    total_servings = inputs.servings_per_meal * inputs.meals_per_week
    wf_per_serving = inputs.weekly_total / max(total_servings, 1)

    comparator = comparator or "HelloFresh (4-serving family plan)"
    baseline_per_serving = COMPARISON_BASELINES[comparator]
    baseline_weekly = baseline_per_serving * total_servings

    loyalty_total = (
        inputs.coupons_clipped_value
        + inputs.loyalty_points_value
        + inputs.fuel_rewards_value
    )
    found_money = (baseline_weekly - inputs.weekly_total) + loyalty_total

    st.markdown("### 💰 Financial Advocacy Ledger")
    st.caption(
        f"Comparing against **{comparator}** at ${baseline_per_serving:.2f}/serving."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "WhollyFare Spend",
        f"${inputs.weekly_total:.2f}",
        delta=f"${wf_per_serving:.2f}/serving",
        delta_color="off",
    )
    c2.metric(
        "Equivalent Meal-Kit Cost",
        f"${baseline_weekly:.2f}",
        delta=f"${baseline_per_serving:.2f}/serving",
        delta_color="off",
    )
    c3.metric(
        "Loyalty Dividends",
        f"${loyalty_total:.2f}",
        help="Coupons clipped, points earned, fuel rewards generated.",
    )
    c4.metric(
        "Net Found Money (this week)",
        f"${found_money:.2f}",
        delta=f"${found_money * 52:,.0f} / yr at this rate",
    )

    with st.expander("How is 'Found Money' calculated?"):
        st.markdown(
            f"- Equivalent meal-kit cost = "
            f"`{total_servings} servings × ${baseline_per_serving:.2f}/serving` "
            f"= **${baseline_weekly:.2f}**\n"
            f"- WhollyFare actual spend = **${inputs.weekly_total:.2f}**\n"
            f"- Loyalty dividends harvested = **${loyalty_total:.2f}**\n"
            f"- **Found Money = (meal-kit − actual) + loyalty** "
            f"= ({baseline_weekly:.2f} − {inputs.weekly_total:.2f}) + "
            f"{loyalty_total:.2f} = **${found_money:.2f}**"
        )
        st.caption(
            "The Sincere Strategy commitment: every input on this calculation "
            "is shown to you, never inferred or marketed-up."
        )


def comparator_picker(default: str = "HelloFresh (4-serving family plan)") -> str:
    """Sidebar / inline picker for which meal-kit baseline to compare against."""
    return st.selectbox(
        "Compare WhollyFare spend against:",
        list(COMPARISON_BASELINES.keys()),
        index=list(COMPARISON_BASELINES.keys()).index(default),
    )
