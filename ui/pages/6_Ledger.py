"""
6_Ledger.py — Found Money Ledger
Running record of savings, week over week.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style

st.set_page_config(page_title="Found Money Ledger · WhollyFare", page_icon="💰", layout="wide")
state.init()
style.page_header("Found Money Ledger", "Your running savings record — every week, auditable and honest.")

ledger = st.session_state.get("ledger_history", [])

if not ledger:
    st.info(
        "No savings recorded yet. Approve your first week's plan on the Sunday Buy-Off screen "
        "and the savings will appear here automatically.",
        icon="💰",
    )
    st.page_link("pages/4_Sunday_BuyOff.py", label="→ Sunday Buy-Off", icon="✅")
    st.stop()

# ── Headline metrics ──────────────────────────────────────────────────────────
total_found      = sum(e.get("found_money", 0) for e in ledger)
total_vs_hf      = sum(e.get("vs_hellofresh", 0) for e in ledger)
total_meals      = sum(e.get("meals", 0) for e in ledger)
weeks_planned    = len(ledger)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Found Money",       f"${total_found:,.2f}",  help="vs. single-store shopping")
c2.metric("Saved vs. HelloFresh",    f"${total_vs_hf:,.2f}",  help="vs. HelloFresh at $9.99/serving")
c3.metric("Weeks planned",           weeks_planned)
c4.metric("Dinners cooked",          total_meals)

st.divider()

# ── Bar chart — weekly found money ────────────────────────────────────────────
st.subheader("Found Money by week")

try:
    import pandas as pd

    df = pd.DataFrame(ledger)
    df = df.sort_values("week")
    df["cumulative"] = df["found_money"].cumsum()

    tab_weekly, tab_cumulative = st.tabs(["Weekly savings", "Cumulative savings"])

    with tab_weekly:
        st.bar_chart(
            df.set_index("week")[["found_money"]],
            color="#007A87",
            height=260,
        )

    with tab_cumulative:
        st.line_chart(
            df.set_index("week")[["cumulative"]],
            color="#2E7D32",
            height=260,
        )

except ImportError:
    # Pandas not available — fall back to plain table
    st.warning("Install pandas for charts: `pip install pandas`")

st.divider()

# ── Detailed ledger table ──────────────────────────────────────────────────────
st.subheader("Week-by-week breakdown")

for entry in sorted(ledger, key=lambda e: e.get("week", ""), reverse=True):
    week        = entry.get("week", "—")
    found       = entry.get("found_money", 0)
    plan_cost   = entry.get("plan_cost", 0)
    single_est  = plan_cost * 1.20
    hf_est      = entry.get("vs_hellofresh", 0) + plan_cost
    meals_n     = entry.get("meals", 0)
    servings_n  = entry.get("servings_per_meal", 0)
    grocer      = entry.get("primary_grocer", "—")

    with st.container(border=True):
        col_week, col_cost, col_found, col_meta = st.columns([2, 2, 2, 3])

        with col_week:
            st.markdown(f"**Week of {week}**")
            st.caption(f"📍 {grocer}")

        with col_cost:
            st.metric("Plan cost", f"${plan_cost:.2f}", help="What you actually spent")

        with col_found:
            st.metric(
                "Found Money",
                f"${found:.2f}",
                delta=f"vs. single-store ${single_est:.2f}",
                delta_color="normal",
            )

        with col_meta:
            st.caption(
                f"**{meals_n}** dinners · **{servings_n}** servings each · "
                f"vs. HelloFresh ${hf_est:.2f}"
            )

st.divider()

# ── Savings rate callout ───────────────────────────────────────────────────────
if weeks_planned >= 2:
    avg_weekly = total_found / weeks_planned
    avg_annual = avg_weekly * 52
    st.success(
        f"At your current average of **${avg_weekly:.2f}/week**, "
        f"WhollyFare is on pace to save your household "
        f"**${avg_annual:,.0f} this year** vs. single-store shopping.",
        icon="🌱",
    )

# ── Export ─────────────────────────────────────────────────────────────────────
lines = ["WhollyFare Found Money Ledger", "=" * 40, ""]
for entry in sorted(ledger, key=lambda e: e.get("week", "")):
    lines.append(
        f"Week of {entry.get('week','—')}  |  "
        f"Plan cost: ${entry.get('plan_cost',0):.2f}  |  "
        f"Found Money: ${entry.get('found_money',0):.2f}  |  "
        f"Grocer: {entry.get('primary_grocer','—')}"
    )
lines += ["", f"TOTAL FOUND MONEY: ${total_found:,.2f}"]

st.download_button(
    label="📥 Export ledger (text)",
    data="\n".join(lines),
    file_name="whollyfare_ledger.txt",
    mime="text/plain",
)
