from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from radical_stats.models import DataFrames

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@st.cache_data(show_spinner=False)
def load_data() -> DataFrames:
    jam_table = pd.read_excel(DATA_DIR / "Jam_table.xlsx")
    rival_path = DATA_DIR / "Rival_Jam_table.xlsx"
    lineups = pd.read_excel(DATA_DIR / "Lineups.xlsx")
    penalty_tracker = pd.read_excel(DATA_DIR / "Penalty_tracker.xlsx")
    player_names = pd.read_excel(DATA_DIR / "Player_names.xlsx")
    time = pd.read_excel(DATA_DIR / "Time.xlsx")
    rival_jam_table = pd.read_excel(rival_path) if rival_path.exists() else pd.DataFrame()

    jam_table = _normalize_match_columns(jam_table)
    rival_jam_table = _normalize_match_columns(rival_jam_table)
    lineups = _normalize_match_columns(lineups)
    penalty_tracker = _normalize_match_columns(penalty_tracker)
    time = _normalize_match_columns(time)

    penalty_tracker["Player_number"] = penalty_tracker["Player_number"].astype(str).str.strip()
    player_names["Player_number"] = player_names["Player_number"].astype(str).str.strip()

    return DataFrames(
        jam_table=jam_table,
        lineups=lineups,
        penalty_tracker=penalty_tracker,
        player_names=player_names,
        time=time,
        rival_jam_table=rival_jam_table,
    )


def _normalize_match_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.date
    if "Rival" in out.columns:
        out["Rival"] = out["Rival"].astype(str).str.strip()
    if "Team" in out.columns:
        out["Team"] = out["Team"].astype(str).str.strip()
    if "Team" in out.columns and "Rival" not in out.columns:
        out["Rival"] = out["Team"]
    return out
