from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

st.set_page_config(
    page_title="Radical Stats",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("Radical Stats Dashboard")
st.caption("Analyze team and player performance. Use the page selector in the sidebar.")

st.markdown(
    """
### Available Views
- **Team Statistics**: match-level and aggregate team metrics.
- **Player Statistics**: detailed stats by selected player.

Data source: Excel summaries under `data/`.
"""
)
