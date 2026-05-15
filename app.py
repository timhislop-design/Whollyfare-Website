"""
app.py — WhollyFare entry point.

Run locally:
    streamlit run app.py

This file simply launches ui/Home.py as the Streamlit app,
keeping the project root clean while the full UI lives in ui/.
"""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "ui" / "Home.py"), run_name="__main__")
