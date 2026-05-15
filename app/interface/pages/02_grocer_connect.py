"""
02_grocer_connect.py — Pull this week's flyer from the user's primary grocer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.flyer_ingestor import FlyerIngestor  # noqa: E402

st.set_page_config(page_title="Connect Grocer · WhollyFare", page_icon="🏪", layout="wide")

st.title("🏪 Connect Your Grocer")

household = st.session_state.get("household")
if not household:
    st.warning("Please complete your **Family Profile** first.")
    st.page_link("pages/01_profile_setup.py", label="→ Build Family Profile", icon="👨‍👩‍👧")
    st.stop()

primary = next(
    (g for g in household["grocers"] if g.get("is_primary")),
    household["grocers"][0],
)
st.markdown(
    f"Pulling this week's circular for **{primary['chain']}** "
    f"({primary['store_id_or_address'] or 'no location set'})."
)

st.markdown("---")

st.subheader("How would you like to connect?")
mode = st.radio(
    "Connection method",
    [
        "Use the bundled sample flyer (Food Lion Palmyra demo)",
        "Upload a flyer PDF",
        "Paste flyer URL (coming soon)",
    ],
    label_visibility="collapsed",
)

flyer_path = Path(__file__).resolve().parents[2] / "data" / "sample_data" / "sample_flyer.json"

if mode.startswith("Use the bundled"):
    if st.button("📥 Load this week's flyer", type="primary"):
        ingestor = FlyerIngestor()
        candidates = ingestor.from_json(flyer_path)
        st.session_state["candidates"] = candidates
        st.success(f"Loaded {len(candidates)} sale items.")
        with st.expander("Preview sale items"):
            for c in candidates:
                st.markdown(
                    f"- **{c.name}** — ${c.sale_price_per_unit:.2f}/{c.unit} "
                    f"({c.category})"
                )
        st.page_link("pages/03_meal_plan.py", label="→ Generate Meal Plan", icon="🍽️")

elif mode.startswith("Upload"):
    uploaded = st.file_uploader("Drop your store's weekly PDF here", type=["pdf"])
    if uploaded and st.button("📥 Parse PDF", type="primary"):
        tmp = Path("/tmp/wf_uploaded_flyer.pdf")
        tmp.write_bytes(uploaded.getbuffer())
        ingestor = FlyerIngestor()
        try:
            candidates = ingestor.from_pdf(tmp)
            st.session_state["candidates"] = candidates
            st.success(f"Parsed {len(candidates)} candidate items from the PDF.")
        except RuntimeError as e:
            st.error(str(e))
else:
    st.info("Direct URL fetching is on the v0.2 roadmap.")
