from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats.data_loader import load_data
from radical_stats.metrics import build_player_table
from radical_stats.ui import apply_global_filters, show_empty_state

st.title("Player Statistics")

frames = load_data()
filtered = apply_global_filters(frames, key_prefix="player")

player_table = build_player_table(filtered)
if player_table.empty:
    show_empty_state()
    st.stop()

player_options = player_table["player_label"].tolist()
selected_player = st.selectbox("Select player", player_options)
player_row = player_table[player_table["player_label"] == selected_player].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Jams Played", int(player_row["jams_played"]))
c2.metric("Jams as Jammer", int(player_row["jams_as_jammer"]))
c3.metric("Penalties", int(player_row["penalties"]))
c4.metric("Penalty Rate", f"{player_row['penalties_per_jam']:.2f}")

st.subheader("Role Distribution")
role_cols = [
    "jams_as_jammer",
    "jams_as_pivot",
    "jams_as_block_1",
    "jams_as_block_2",
    "jams_as_block_3",
]
role_frame = pd.DataFrame(
    {
        "Role": ["Jammer", "Pivot", "Block 1", "Block 2", "Block 3"],
        "Count": [int(player_row[c]) for c in role_cols],
    }
)
st.bar_chart(role_frame.set_index("Role"))

st.subheader("All Players Table")
st.dataframe(
    player_table[
        [
            "player_label",
            "jams_played",
            "jams_as_jammer",
            "penalties",
            "penalties_per_jam",
        ]
    ].rename(
        columns={
            "player_label": "Player",
            "jams_played": "Jams",
            "jams_as_jammer": "Jammer Jams",
            "penalties": "Penalties",
            "penalties_per_jam": "Pen/Jam",
        }
    ),
    use_container_width=True,
)
