from __future__ import annotations

import pandas as pd

from radical_stats.models import DataFrames

ROLE_COLS = ["Jammer", "Pivot", "Block_1", "Block_2", "Block_3"]


def build_team_metrics(frames: DataFrames) -> pd.Series:
    jam = frames.jam_table.copy()
    lineups = frames.lineups.copy()
    if jam.empty:
        return pd.Series(dtype="float64")

    totals = {
        "total_jams": int(len(jam)),
        "total_points": float(jam["Total_points"].fillna(0).sum()),
        "avg_points_per_jam": float(jam["Total_points"].fillna(0).mean()),
        "lead_pct": _ratio_pct(jam["Lider"]),
        "call_pct": _ratio_pct(jam["Call"]),
        "no_initial_pass_pct": _ratio_pct(jam["No_initial_pass"]),
        "total_penalties": int(len(frames.penalty_tracker)),
        "total_players": _count_players(lineups),
    }
    return pd.Series(totals)


def build_player_table(frames: DataFrames) -> pd.DataFrame:
    lineups = frames.lineups.copy()
    penalties = frames.penalty_tracker.copy()
    names = frames.player_names.copy()

    if lineups.empty:
        return pd.DataFrame()

    role_counts = []
    for role_col in ROLE_COLS:
        counts = (
            lineups[role_col]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s != "0"]
            .value_counts()
            .rename_axis("Player_number")
            .reset_index(name=f"jams_as_{role_col.lower()}")
        )
        role_counts.append(counts)

    merged = role_counts[0]
    for chunk in role_counts[1:]:
        merged = merged.merge(chunk, on="Player_number", how="outer")

    merged = merged.fillna(0)
    for c in merged.columns:
        if c != "Player_number":
            merged[c] = merged[c].astype(int)

    penalty_counts = (
        penalties["Player_number"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .rename_axis("Player_number")
        .reset_index(name="penalties")
    )

    out = merged.merge(penalty_counts, on="Player_number", how="left").fillna({"penalties": 0})
    out["penalties"] = out["penalties"].astype(int)

    out["jams_played"] = out[
        ["jams_as_jammer", "jams_as_pivot", "jams_as_block_1", "jams_as_block_2", "jams_as_block_3"]
    ].sum(axis=1)
    out["penalties_per_jam"] = (out["penalties"] / out["jams_played"].replace(0, pd.NA)).fillna(0.0)

    names["Player_number"] = names["Player_number"].astype(str).str.strip()
    out = out.merge(names, on="Player_number", how="left")
    out["player_label"] = out["Name"].fillna("#" + out["Player_number"]) + " (#" + out["Player_number"] + ")"

    out = out.sort_values(["jams_played", "penalties"], ascending=[False, False]).reset_index(drop=True)
    return out


def _count_players(lineups: pd.DataFrame) -> int:
    if lineups.empty:
        return 0

    values = pd.concat([lineups[c] for c in ROLE_COLS if c in lineups.columns], ignore_index=True)
    players = values.dropna().astype(str).str.strip()
    players = players[players != "0"]
    return int(players.nunique())


def _ratio_pct(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    return float(100 * s.mean())
