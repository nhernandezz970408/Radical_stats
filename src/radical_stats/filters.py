from __future__ import annotations

from radical_stats.models import DataFrames


def filter_by_match(frames: DataFrames, selected_matches: list[str]) -> DataFrames:
    if not selected_matches:
        return frames

    def _apply(df):
        if df.empty or "match_id" not in df.columns:
            return df
        return df[df["match_id"].isin(selected_matches)].copy()

    return DataFrames(
        jam_table=_apply(frames.jam_table),
        lineups=_apply(frames.lineups),
        penalty_tracker=_apply(frames.penalty_tracker),
        player_names=frames.player_names,
        time=_apply(frames.time),
        rival_jam_table=_apply(frames.rival_jam_table),
    )
