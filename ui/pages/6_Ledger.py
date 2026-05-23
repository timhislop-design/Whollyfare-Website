"""
6_Ledger.py — Found Money Ledger
==================================
The running record of real household savings, week over week.

This page serves two audiences simultaneously:
  1. Tim/pilot families — to see their actual savings accumulate
  2. Investors — to see real household data, not projections

The critical distinction: every entry carries both the WhollyFare *estimate*
(what the engine predicted you'd spend) and the *actual receipt* (what you
actually paid). That gap — the accuracy delta — is what makes this data
credible. A savings claim backed by receipts is an investor data point.
One backed by estimates alone is a marketing claim.

POC vs. PRODUCTION
-------------------
POC:  Receipts are entered manually after each shopping trip. Ledger lives
      in session_state — cleared on refresh. Export to CSV for safekeeping.
PROD: Receipt OCR via phone camera (Google ML Kit or similar). Data persists
      to Postgres. Ledger is the user's permanent account history. Shared
      (with permission) across household members.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import ui.state as state
import ui.style as style
import datetime
import io

st.set_page_config(page_title="Found Money Ledger · WhollyFare", page_icon="💰", layout="wide")
state.init()

with st.sidebar:
    style.sidebar_nav()

style.page_header(
    "Found Money Ledger",
    "Real savings. Real receipts. Every week, auditable and honest.",
)

# Load from DB if authenticated; falls back to session_state if not.
# This means the ledger survives browser refresh once the user is signed in.
ledger: list[dict] = state.load_ledger()
grocers: list[dict] = st.session_state.get("grocers", [])

# ── Store names (dynamic from session, not hardcoded) ────────────────────────
def _store_label() -> str:
    names = [g.get("chain", "?") for g in grocers]
    if not names:
        return "your stores"
    if len(names) == 1:
        return names[0]
    return " + ".join(names[:2]) + (f" + {len(names)-2} more" if len(names) > 2 else "")


# ════════════════════════════════════════════════════════════════════════════
# RECEIPT LOGGER — the most important section on this page
# Enter your actual receipt total after you shop. That's the real data.
# ════════════════════════════════════════════════════════════════════════════

# Find weeks that have been approved but don't yet have a real receipt logged
approved_without_receipt = [
    e for e in ledger
    if e.get("actual_receipt") is None and e.get("whollyfare_cost", 0) > 0
]

if approved_without_receipt:
    pending = approved_without_receipt[-1]  # most recent unentered week
    week_label = pending.get("week", "this week")
    plan_cost  = pending.get("whollyfare_cost", 0)

    st.html(f"""
    <div style='background:linear-gradient(135deg,#FFF8EC,#FFF3E0);
                border:1.5px solid #F28B30;border-radius:12px;
                padding:20px 24px;margin-bottom:20px;'>
      <div style='font-size:0.7rem;font-weight:700;letter-spacing:0.1em;
                  text-transform:uppercase;color:#BF5E00;margin-bottom:6px;'>
        Receipt needed — week of {week_label}
      </div>
      <div style='font-size:1rem;color:#1A2E1D;font-weight:600;margin-bottom:4px;'>
        Log your actual receipt to record real savings.
      </div>
      <div style='font-size:0.84rem;color:#5A6B5E;'>
        WhollyFare estimated your plan would cost <strong>${plan_cost:.2f}</strong>.
        Enter what you actually spent and we'll calculate your real Found Money.
      </div>
    </div>
    """)

    with st.form("receipt_form", clear_on_submit=False):
        rc1, rc2, rc3 = st.columns([2, 2, 3])
        with rc1:
            actual_total = st.number_input(
                "Actual receipt total ($)",
                min_value=0.0, max_value=2000.0,
                step=0.01, format="%.2f",
                value=plan_cost,
                help="Total from your grocery receipts this week — all stores combined",
            )
        with rc2:
            single_store_actual = st.number_input(
                "Single-store price check ($)",
                min_value=0.0, max_value=2000.0,
                step=0.01, format="%.2f",
                value=round(plan_cost * 1.18, 2),
                help="Optional: what the same basket would cost at one store. "
                     "Leave as the default estimate if you didn't check.",
            )
        with rc3:
            week_notes = st.text_input(
                "Notes (optional)",
                placeholder="e.g. Aldi was out of chicken, substituted at Food Lion · Kids loved the tacos",
                help="Short notes about this week — useful for the investor narrative later",
            )

        log_btn = st.form_submit_button("💰 Log this receipt", type="primary", use_container_width=True)

    if log_btn:
        # Update the ledger entry in place
        idx = next((i for i, e in enumerate(ledger) if e.get("week") == week_label), None)
        if idx is not None:
            found_actual     = round(single_store_actual - actual_total, 2)
            hf_equiv         = ledger[idx].get("vs_hellofresh", 0) + ledger[idx].get("whollyfare_cost", 0)
            vs_hf_actual     = round(hf_equiv - actual_total, 2)
            accuracy_delta   = round(actual_total - plan_cost, 2)

            ledger[idx]["actual_receipt"]     = round(actual_total, 2)
            ledger[idx]["single_store_actual"]= round(single_store_actual, 2)
            ledger[idx]["actual_found_money"] = max(found_actual, 0)
            ledger[idx]["vs_hf_actual"]       = max(vs_hf_actual, 0)
            ledger[idx]["accuracy_delta"]     = accuracy_delta
            ledger[idx]["notes"]              = week_notes.strip() if week_notes else ""

            # If stores list not yet set, capture from current session
            if not ledger[idx].get("stores_list"):
                ledger[idx]["stores_list"] = [g.get("chain", "?") for g in grocers]

            st.session_state["ledger_history"] = ledger
            # Also persist to DB (degrades gracefully if not authenticated)
            state.save_ledger_entry(ledger[idx])
            st.success(f"✅ Receipt logged — ${found_actual:.2f} in real Found Money this week.")
            st.rerun()

    st.divider()


# ════════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ════════════════════════════════════════════════════════════════════════════
real_entries = [e for e in ledger if e.get("actual_receipt") is not None]
any_entries  = len(ledger) > 0

if not any_entries:
    st.info(
        "No savings recorded yet. Complete your first week — approve Sunday Buy-Off, "
        "shop, then come back here to log your receipt.",
        icon="💰",
    )
    st.page_link("pages/4_Sunday_BuyOff.py", label="→ Sunday Buy-Off", icon="✅")
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# HEADLINE METRICS
# Uses real receipt data where available; falls back to estimates.
# ════════════════════════════════════════════════════════════════════════════
use_real = len(real_entries) > 0

total_found      = sum(e.get("actual_found_money", e.get("found_money", 0)) for e in ledger)
total_trip_costs = sum(e.get("trip_cost", 0) for e in ledger)
total_net        = sum(e.get("net_found_money", e.get("actual_found_money", e.get("found_money", 0))) for e in ledger)
total_vs_hf      = sum(e.get("vs_hf_actual", e.get("vs_hellofresh", 0)) for e in ledger)
total_meals      = sum(e.get("meals_planned", 0) for e in ledger)
weeks_planned    = len(ledger)
weeks_receipts   = len(real_entries)
has_trip_data    = total_trip_costs > 0

# Accuracy: average gap between estimate and receipt
if real_entries:
    avg_delta = sum(abs(e.get("accuracy_delta", 0)) for e in real_entries) / len(real_entries)
    accuracy_pct = max(0, round((1 - avg_delta / max(e.get("actual_receipt", 1) for e in real_entries)) * 100))
else:
    avg_delta = None
    accuracy_pct = None

data_note = "real receipts" if use_real else "plan estimates (log receipts to get real data)"

# ── Sincere Strategy banner: show net savings when trip data exists ────────────
if has_trip_data:
    st.html(
        f"""<div style='background:#F0FAF2;border:1px solid #D8EDD0;border-radius:10px;
                        padding:14px 20px;margin-bottom:16px;'>
          <div style='font-size:0.82rem;color:#5A7A62;margin-bottom:4px;'>
            Cumulative savings — what you actually kept after gas
          </div>
          <div style='display:flex;gap:40px;align-items:baseline;'>
            <div>
              <span style='font-size:2rem;font-weight:800;color:#1E5C32;'>${total_net:,.2f}</span>
              <span style='font-size:0.82rem;color:#5A7A62;margin-left:6px;'>net Found Money</span>
            </div>
            <div style='font-size:0.85rem;color:#9AA8A0;'>
              ${total_found:,.2f} gross &minus; ${total_trip_costs:,.2f} gas &equals; ${total_net:,.2f} in your pocket
            </div>
          </div>
        </div>"""
    )

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Net Found Money" if has_trip_data else "Total Found Money",
    f"${total_net:,.2f}" if has_trip_data else f"${total_found:,.2f}",
    delta=f"-${total_trip_costs:.2f} gas" if has_trip_data else None,
    help=("Gross savings minus estimated gas costs for secondary store trips. "
          "Sincere Strategy: we show the real number.") if has_trip_data
         else f"Based on {data_note}",
)
c2.metric(
    "Saved vs. HelloFresh",
    f"${total_vs_hf:,.2f}",
    help="vs. HelloFresh at $9.99/serving",
)
c3.metric(
    "Weeks tracked",
    f"{weeks_receipts} of {weeks_planned}",
    help=f"{weeks_receipts} weeks with real receipts logged",
)
c4.metric(
    "Estimate accuracy",
    f"{accuracy_pct}%" if accuracy_pct is not None else "—",
    help="How close WhollyFare's estimates were to your actual receipts",
)

if use_real:
    st.html(
        f"<div style='font-size:0.78rem;color:#3A8C4E;font-weight:600;margin-top:-8px;"
        f"margin-bottom:12px;'>✓ Figures based on real receipts — {weeks_receipts} week(s) logged</div>")
else:
    st.html(
        "<div style='font-size:0.78rem;color:#F28B30;font-weight:600;margin-top:-8px;"
        "margin-bottom:12px;'>⚠ Log your receipts above to replace estimates with real data</div>")

st.divider()


# ════════════════════════════════════════════════════════════════════════════
# CHARTS
# ════════════════════════════════════════════════════════════════════════════
try:
    import pandas as pd

    df = pd.DataFrame(ledger).sort_values("week")

    # Use actual if available, else estimate
    df["savings_to_plot"]    = df.apply(
        lambda r: r.get("actual_found_money") if r.get("actual_found_money") is not None
                  else r.get("found_money", 0),
        axis=1,
    )
    df["cumulative_savings"] = df["savings_to_plot"].cumsum()
    df["receipt_logged"]     = df["actual_receipt"].notna()

    tab_weekly, tab_cumulative, tab_accuracy = st.tabs(
        ["Weekly savings", "Cumulative savings", "Estimate vs. actual"]
    )

    with tab_weekly:
        st.bar_chart(
            df.set_index("week")[["savings_to_plot"]].rename(
                columns={"savings_to_plot": "Found Money ($)"}
            ),
            color="#3A8C4E", height=260,
        )

    with tab_cumulative:
        st.line_chart(
            df.set_index("week")[["cumulative_savings"]].rename(
                columns={"cumulative_savings": "Cumulative savings ($)"}
            ),
            color="#1E5C32", height=260,
        )

    with tab_accuracy:
        if real_entries:
            df_r = df[df["receipt_logged"]].copy()
            df_r["plan_estimate"]   = df_r["whollyfare_cost"]
            df_r["actual_receipt"]  = df_r["actual_receipt"]
            chart_data = df_r.set_index("week")[["plan_estimate", "actual_receipt"]]
            st.bar_chart(chart_data, color=["#D8EDD0", "#3A8C4E"], height=260)
            st.caption("Green = actual receipt · Light = WhollyFare estimate")
        else:
            st.info("Log your first receipt to see estimate vs. actual accuracy.", icon="📊")

except ImportError:
    st.warning("Install pandas for charts: `pip install pandas`")

st.divider()


# ════════════════════════════════════════════════════════════════════════════
# WEEK-BY-WEEK DETAIL
# ════════════════════════════════════════════════════════════════════════════
st.html(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:12px;'>Week-by-week breakdown</div>")

for entry in sorted(ledger, key=lambda e: e.get("week", ""), reverse=True):
    week       = entry.get("week", "—")
    plan_cost  = entry.get("whollyfare_cost", 0)
    actual     = entry.get("actual_receipt")
    found_est  = entry.get("found_money", 0)
    found_real = entry.get("actual_found_money")
    trip_cost  = entry.get("trip_cost", 0)
    net_fm     = entry.get("net_found_money")
    vs_hf      = entry.get("vs_hellofresh", 0)
    meals_n    = entry.get("meals_planned", 0)
    notes      = entry.get("notes", "")
    stores     = entry.get("stores_list") or [_store_label()]
    receipt_ok = actual is not None
    accuracy_d = entry.get("accuracy_delta")

    with st.container(border=True):
        col_a, col_b, col_c, col_d = st.columns([2.5, 2, 2, 2.5])

        with col_a:
            st.html(f"**Week of {week}**")
            stores_str = " + ".join(stores) if isinstance(stores, list) else str(stores)
            st.caption(f"📍 {stores_str}  ·  {meals_n} dinners")
            if notes:
                st.caption(f"📝 {notes}")

        with col_b:
            st.metric(
                "WhollyFare plan",
                f"${plan_cost:.2f}",
                help="What the engine estimated you'd spend",
            )
            if receipt_ok and accuracy_d is not None:
                sign   = "+" if accuracy_d > 0 else ""
                colour = "#B91C1C" if accuracy_d > 5 else "#3A8C4E"
                st.markdown(
                    f"<div style='font-size:0.76rem;color:{colour};margin-top:-8px;'>"
                    f"actual: ${actual:.2f} ({sign}${accuracy_d:.2f})</div>")

        with col_c:
            found_display = found_real if found_real is not None else found_est
            label_suffix  = "" if receipt_ok else " (est.)"
            # Show net if trip cost data available, otherwise gross
            if trip_cost > 0 and net_fm is not None:
                st.metric(
                    f"Net Found Money{label_suffix}",
                    f"${net_fm:.2f}",
                    delta=f"-${trip_cost:.2f} gas",
                    help=f"${found_display:.2f} grocery savings minus ${trip_cost:.2f} estimated gas. "
                         "Sincere Strategy: we show what you actually kept.",
                )
            else:
                st.metric(
                    f"Found Money{label_suffix}",
                    f"${found_display:.2f}",
                    help="Real savings vs. single-store" if receipt_ok
                         else "Estimated — log receipt for real figure",
                )
            if not receipt_ok:
                st.html(
                    "<div style='font-size:0.73rem;color:#F28B30;margin-top:-8px;'>"
                    "⚠ Receipt not logged yet</div>")

        with col_d:
            st.caption(
                f"vs. HelloFresh: **${(vs_hf + plan_cost):.2f}** would have cost  \n"
                f"WhollyFare saved you **${vs_hf:.2f}**"
            )

    # Quick receipt entry for older unentered weeks (collapsed)
    if not receipt_ok:
        with st.expander(f"↳ Log receipt for week of {week}", expanded=False):
            with st.form(f"receipt_quick_{week}"):
                qr1, qr2 = st.columns(2)
                with qr1:
                    q_actual = st.number_input(
                        "Actual total ($)", min_value=0.0, max_value=2000.0,
                        step=0.01, format="%.2f", value=plan_cost, key=f"qa_{week}",
                    )
                with qr2:
                    q_single = st.number_input(
                        "Single-store estimate ($)", min_value=0.0, max_value=2000.0,
                        step=0.01, format="%.2f", value=round(plan_cost * 1.18, 2), key=f"qs_{week}",
                    )
                q_notes = st.text_input("Notes", key=f"qn_{week}", placeholder="Optional")
                if st.form_submit_button("Log receipt", type="primary"):
                    idx = next((i for i, e in enumerate(ledger) if e.get("week") == week), None)
                    if idx is not None:
                        found_a  = round(q_single - q_actual, 2)
                        hf_equiv = ledger[idx].get("vs_hellofresh", 0) + plan_cost
                        ledger[idx]["actual_receipt"]      = round(q_actual, 2)
                        ledger[idx]["single_store_actual"] = round(q_single, 2)
                        ledger[idx]["actual_found_money"]  = max(found_a, 0)
                        ledger[idx]["vs_hf_actual"]        = max(round(hf_equiv - q_actual, 2), 0)
                        ledger[idx]["accuracy_delta"]      = round(q_actual - plan_cost, 2)
                        ledger[idx]["notes"]               = q_notes.strip()
                        st.session_state["ledger_history"] = ledger
                        state.save_ledger_entry(ledger[idx])
                        st.rerun()

st.divider()


# ════════════════════════════════════════════════════════════════════════════
# INVESTOR CALLOUT — the annualised savings projection
# Only shows after 2+ weeks of real data. Estimates are clearly marked.
# ════════════════════════════════════════════════════════════════════════════
if weeks_planned >= 2:
    base_entries = real_entries if real_entries else ledger
    avg_weekly   = sum(
        e.get("actual_found_money", e.get("found_money", 0)) for e in base_entries
    ) / len(base_entries)
    avg_annual   = avg_weekly * 52
    data_qualifier = "real receipts" if real_entries else "plan estimates — log receipts for verified figures"

    st.html(f"""
    <div style='background:linear-gradient(135deg,#F4FAF5,#E8F5EC);
                border:1px solid #A8D5B0;border-radius:12px;
                padding:20px 24px;'>
      <div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;
                  text-transform:uppercase;color:#3A8C4E;margin-bottom:8px;'>
        Annualised savings projection
      </div>
      <div style='font-size:1.6rem;font-weight:800;color:#1E5C32;line-height:1.1;'>
        ${avg_annual:,.0f}/year
      </div>
      <div style='font-size:0.84rem;color:#5A7A62;margin-top:6px;'>
        At your current average of <strong>${avg_weekly:.2f}/week</strong>,
        WhollyFare saves this household approximately
        <strong>${avg_annual:,.0f} per year</strong> vs. single-store shopping.
        Based on {data_qualifier}.
      </div>
    </div>
    """)

    st.html("<div style='height:16px;'></div>")


# ════════════════════════════════════════════════════════════════════════════
# EXPORT
# CSV is the investor-ready format. Text is the quick share format.
# PROD: Auto-generate a shareable link / PDF report on request.
# ════════════════════════════════════════════════════════════════════════════
st.html(
    "<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;"
    "color:#3A8C4E;margin-bottom:10px;'>Export your data</div>")

exp1, exp2 = st.columns(2)

with exp1:
    # CSV export — for the investor conversation
    csv_rows = ["Week,Plan estimate ($),Actual receipt ($),Found Money ($),vs HelloFresh ($),Meals,Stores,Notes"]
    for e in sorted(ledger, key=lambda x: x.get("week", "")):
        actual_str  = f"{e['actual_receipt']:.2f}" if e.get("actual_receipt") is not None else "not logged"
        found_str   = f"{e.get('actual_found_money', e.get('found_money', 0)):.2f}"
        stores_str  = "|".join(e.get("stores_list") or [_store_label()])
        csv_rows.append(
            f"{e.get('week','')},{e.get('whollyfare_cost',0):.2f},"
            f"{actual_str},{found_str},"
            f"{e.get('vs_hellofresh',0):.2f},"
            f"{e.get('meals_planned',0)},{stores_str},"
            f"\"{e.get('notes','')}\""
        )
    csv_data = "\n".join(csv_rows)
    st.download_button(
        label="📥 Export as CSV",
        data=csv_data,
        file_name=f"whollyfare_ledger_{datetime.date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Investor-ready data export — open in Excel or Google Sheets",
    )

with exp2:
    # Plain text — quick share
    lines = [
        "WhollyFare® Found Money Ledger",
        f"Exported {datetime.date.today().isoformat()}",
        "=" * 44, "",
    ]
    for e in sorted(ledger, key=lambda x: x.get("week", "")):
        actual_label = f"actual ${e['actual_receipt']:.2f}" if e.get("actual_receipt") is not None else "receipt pending"
        lines.append(
            f"Week of {e.get('week','—')}  ·  "
            f"plan ${e.get('whollyfare_cost',0):.2f}  ·  {actual_label}  ·  "
            f"Found Money ${e.get('actual_found_money', e.get('found_money',0)):.2f}"
        )
        if e.get("notes"):
            lines.append(f"  Notes: {e['notes']}")
    lines.append("")
    text_data = "\n".join(lines)
    st.download_button(
        label="📋 Export as text",
        data=text_data,
        file_name=f"whollyfare_ledger_{datetime.date.today().isoformat()}.txt",
        mime="text/plain",
        use_container_width=True,
    )
