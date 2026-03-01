from __future__ import annotations

import streamlit as st

from radical_stats.filters import filter_by_match
from radical_stats.models import DataFrames


def apply_global_filters(frames: DataFrames, key_prefix: str = "") -> DataFrames:
    match_options = _build_match_options(frames)

    with st.sidebar:
        st.header("Filters")
        selected_matches = st.multiselect(
            "Match",
            options=match_options,
            default=match_options,
            key=f"{key_prefix}_matches",
            help="Filter statistics by one or more matches.",
        )

    filtered = _attach_match_id(frames)
    return filter_by_match(filtered, selected_matches)


def show_empty_state() -> None:
    st.warning("No data available for the selected filters.")


def _attach_match_id(frames: DataFrames) -> DataFrames:
    def _tag(df):
        if df.empty or "Date" not in df.columns or "Rival" not in df.columns:
            return df
        out = df.copy()
        out["match_id"] = out["Date"].astype(str) + " | " + out["Rival"].astype(str)
        return out

    return DataFrames(
        jam_table=_tag(frames.jam_table),
        lineups=_tag(frames.lineups),
        penalty_tracker=_tag(frames.penalty_tracker),
        player_names=frames.player_names,
        time=_tag(frames.time),
        rival_jam_table=_tag(frames.rival_jam_table),
    )


def _build_match_options(frames: DataFrames) -> list[str]:
    jam = frames.jam_table
    if jam.empty or "Date" not in jam.columns or "Rival" not in jam.columns:
        return []

    tmp = jam[["Date", "Rival"]].dropna().drop_duplicates().copy()
    tmp["match_id"] = tmp["Date"].astype(str) + " | " + tmp["Rival"].astype(str)
    return sorted(tmp["match_id"].tolist())
