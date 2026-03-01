from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from radical_stats.data_loader import load_data
from radical_stats.metrics import build_team_metrics
from radical_stats.models import DataFrames
from radical_stats.ui import apply_global_filters, show_empty_state

frames = load_data()
filtered = apply_global_filters(frames, key_prefix="team")
selected_matches = st.session_state.get("team_matches", [])


def _period_phrase(selected: list[str]) -> str:
    period_map = {
        "1": "the first period",
        "2": "the second period",
        "3": "the third period",
        "4": "the fourth period",
    }
    if len(selected) == 1:
        return period_map.get(selected[0], f"period {selected[0]}")
    return "the selected periods"


def _extract_players_from_lineups(lineups: pd.DataFrame) -> pd.Series:
    role_cols = ["Jammer", "Pivot", "Block_1", "Block_2", "Block_3"]
    values = pd.concat([lineups[c] for c in role_cols if c in lineups.columns], ignore_index=True)
    players = values.dropna().astype(str).str.strip()
    return players[players != "0"].drop_duplicates()


def _normalize_period_column(df: pd.DataFrame, col: str = "Period") -> pd.DataFrame:
    out = df.copy()
    if col not in out.columns:
        return out

    period_num = pd.to_numeric(out[col], errors="coerce")
    clean = period_num.dropna()
    # Some lineup files encode periods as 0/1 instead of 1/2.
    if not clean.empty and set(clean.unique().tolist()).issubset({0, 1}):
        period_num = period_num + 1

    out[col] = period_num.astype("Int64").astype(str)
    out.loc[out[col] == "<NA>", col] = pd.NA
    return out


def _filter_by_period(df: pd.DataFrame, selected_periods: list[str]) -> pd.DataFrame:
    if "Period" not in df.columns:
        return df
    return df[df["Period"].isin(selected_periods)].copy()


rivals = []
if "Rival" in filtered.jam_table.columns:
    rivals = sorted(filtered.jam_table["Rival"].dropna().astype(str).unique().tolist())

is_general_mode = len(selected_matches) == 0
rival_label = rivals[0] if (not is_general_mode and len(rivals) == 1) else None
title = "Team Statistics - General" if is_general_mode else (f"Team Statistics vs {rival_label}" if rival_label else "Team Statistics")
st.title(title)

st.markdown(
    """
<style>
div.block-container {
    max-width: 95%;
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

jam_normalized = _normalize_period_column(filtered.jam_table)
rival_jam_normalized = _normalize_period_column(filtered.rival_jam_table)
lineups_normalized = _normalize_period_column(filtered.lineups)
penalties_normalized = _normalize_period_column(filtered.penalty_tracker)
time_normalized = _normalize_period_column(filtered.time)

period_options = []
if "Period" in jam_normalized.columns:
    period_options = sorted(jam_normalized["Period"].dropna().astype(str).unique().tolist())

st.subheader("General Information")

selected_periods = st.multiselect(
    "Period Filter",
    options=period_options,
    default=period_options,
    help="Filter summary metrics and charts by period.",
)

period_filtered = DataFrames(
    jam_table=_filter_by_period(jam_normalized, selected_periods),
    lineups=_filter_by_period(lineups_normalized, selected_periods),
    penalty_tracker=_filter_by_period(penalties_normalized, selected_periods),
    player_names=filtered.player_names,
    time=_filter_by_period(time_normalized, selected_periods),
    rival_jam_table=_filter_by_period(rival_jam_normalized, selected_periods),
)
team_metrics = build_team_metrics(period_filtered)

if team_metrics.empty:
    show_empty_state()
    st.stop()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Jams", int(team_metrics["total_jams"]))
kpi2.metric("Total Points", int(team_metrics["total_points"]))
kpi3.metric("Avg Points / Jam", f"{team_metrics['avg_points_per_jam']:.2f}")
kpi4.metric("Lead %", f"{team_metrics['lead_pct']:.1f}%")

kpi5, kpi6, kpi7, kpi8 = st.columns(4)
kpi5.metric("Call-Off %", f"{team_metrics['call_pct']:.1f}%")
kpi6.metric("No Initial Pass %", f"{team_metrics['no_initial_pass_pct']:.1f}%")
kpi7.metric("Total Penalties", int(team_metrics["total_penalties"]))
kpi8.metric("Number of Players", int(team_metrics["total_players"]))

chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    points_title = "Points by Jam - General"
    if rival_label and selected_periods:
        points_title = f"Points by Jam vs {rival_label} in {_period_phrase(selected_periods)}"
    elif rival_label:
        points_title = f"Points by Jam vs {rival_label}"
    st.subheader(points_title)
    jam_points = period_filtered.jam_table.copy()

    if jam_points.empty:
        st.info("No jam points data for the selected period filter.")
    else:
        jam_points["Jam"] = pd.to_numeric(jam_points["Jam"], errors="coerce")
        jam_points["Total_points"] = pd.to_numeric(jam_points["Total_points"], errors="coerce").fillna(0)
        jam_points = jam_points.dropna(subset=["Jam"]).copy()

        jam_points["period_label"] = "Period " + jam_points["Period"].astype(str)
        jam_lines = (
            jam_points.groupby(["Jam", "period_label"], as_index=False)["Total_points"].sum()
            .pivot(index="Jam", columns="period_label", values="Total_points")
            .sort_index()
        )
        st.bar_chart(jam_lines)

with chart_col_2:
    penalties_title = "Penalties by Player - General"
    if rival_label and selected_periods:
        penalties_title = f"Penalties by Player vs {rival_label} in {_period_phrase(selected_periods)}"
    elif rival_label:
        penalties_title = f"Penalties by Player vs {rival_label}"
    st.subheader(penalties_title)

    pen = period_filtered.penalty_tracker.copy()
    lineups = period_filtered.lineups.copy()

    players_in_scope = _extract_players_from_lineups(lineups)
    if players_in_scope.empty:
        st.info("No penalty data for the selected period filter.")
    else:
        by_player = pd.DataFrame({"Player_number": players_in_scope})
        by_player["Player_number"] = by_player["Player_number"].astype(str).str.strip()

        pen["Player_number"] = pen["Player_number"].astype(str).str.strip()
        penalty_counts = (
            pen.groupby("Player_number", as_index=False)
            .size()
            .rename(columns={"size": "Penalties"})
        )
        by_player = by_player.merge(penalty_counts, on="Player_number", how="left").fillna({"Penalties": 0})
        by_player["Penalties"] = by_player["Penalties"].astype(int)

        names = filtered.player_names.copy()
        names["Player_number"] = names["Player_number"].astype(str).str.strip()
        by_player = by_player.merge(names, on="Player_number", how="left")
        by_player["Player"] = by_player["Name"].fillna("#" + by_player["Player_number"])

        by_player = by_player.sort_values(["Penalties", "Player"], ascending=[False, True])
        st.bar_chart(by_player.set_index("Player")[["Penalties"]])

effective_col_1, effective_col_2 = st.columns(2)

effective_title = "Effective Points by Jam - General"
if rival_label and selected_periods:
    effective_title = f"Effective Points by Jam vs {rival_label} in {_period_phrase(selected_periods)}"
elif rival_label:
    effective_title = f"Effective Points by Jam vs {rival_label}"

effective_time_title = "Effective Points by Time - General"
if rival_label and selected_periods:
    effective_time_title = f"Effective Points by Time vs {rival_label} in {_period_phrase(selected_periods)}"
elif rival_label:
    effective_time_title = f"Effective Points by Time vs {rival_label}"

our_jams = period_filtered.jam_table.copy()
opp_jams = period_filtered.rival_jam_table.copy()
jam_keys = ["Date", "Period", "Jam"]

for frame in (our_jams, opp_jams):
    if not frame.empty:
        frame["Jam"] = pd.to_numeric(frame["Jam"], errors="coerce")
        frame["Total_points"] = pd.to_numeric(frame["Total_points"], errors="coerce").fillna(0)

if opp_jams.empty:
    with effective_col_1:
        st.subheader(effective_title)
        st.info("Rival jam data is missing. Add data in `Rival_Jam_table.xlsx`.")
    with effective_col_2:
        st.subheader(effective_time_title)
        st.info("Rival jam data is missing. Add data in `Rival_Jam_table.xlsx`.")
else:
    effective = our_jams[jam_keys + ["Total_points"]].merge(
        opp_jams[jam_keys + ["Total_points"]],
        on=jam_keys,
        how="inner",
        suffixes=("_our", "_rival"),
    )
    effective["effective_points"] = effective["Total_points_our"] - effective["Total_points_rival"]
    effective = effective.dropna(subset=["Jam"]).copy()
    effective["Jam"] = effective["Jam"].astype(int)
    effective["period_num"] = pd.to_numeric(effective["Period"], errors="coerce")
    effective = effective.dropna(subset=["period_num"]).copy()
    effective["period_num"] = effective["period_num"].astype(int)
    effective["jam_key"] = "J" + effective["Jam"].astype(str) + "-P" + effective["period_num"].astype(str)
    effective = effective.sort_values(["Jam", "period_num", "Date"]).reset_index(drop=True)
    effective["jam_period_order"] = range(len(effective))

    with effective_col_1:
        st.subheader(effective_title)
        if effective.empty:
            st.info("No effective points data for the selected filters.")
        else:
            bar_chart = (
                alt.Chart(effective)
                .mark_bar()
                .encode(
                    x=alt.X("jam_key:N", title="Jam", sort=alt.SortField(field="jam_period_order", order="ascending")),
                    y=alt.Y("effective_points:Q", title="Effective Points"),
                    color=alt.condition(
                        "datum.effective_points >= 0",
                        alt.value("#1A9850"),
                        alt.value("#D73027"),
                    ),
                    tooltip=[
                        alt.Tooltip("Date:N"),
                        alt.Tooltip("Period:N"),
                        alt.Tooltip("Jam:Q"),
                        alt.Tooltip("Total_points_our:Q", title="Our points"),
                        alt.Tooltip("Total_points_rival:Q", title="Rival points"),
                        alt.Tooltip("effective_points:Q", title="Effective points"),
                    ],
                )
            )
            st.altair_chart(bar_chart, use_container_width=True)

    with effective_col_2:
        st.subheader(effective_time_title)
        time_df = period_filtered.time.copy()
        if time_df.empty:
            st.info("No time data available for the selected filters.")
        else:
            time_df["Jam"] = pd.to_numeric(time_df["Jam"], errors="coerce")
            time_df["Time"] = pd.to_numeric(time_df["Time"], errors="coerce")
            time_df = time_df.dropna(subset=["Jam", "Time"]).copy()
            time_df["Jam"] = time_df["Jam"].astype(int)
            time_df["Time"] = time_df["Time"].astype(float)

            effective_time = effective.merge(time_df[jam_keys + ["Time"]], on=jam_keys, how="inner")
            effective_time = effective_time.sort_values(["Date", "Period", "Jam"]).reset_index(drop=True)
            effective_time["elapsed_minutes"] = effective_time["Time"].cumsum() / 60.0

            if effective_time.empty:
                st.info("No effective points by time data for the selected filters.")
            else:
                line = (
                    alt.Chart(effective_time)
                    .mark_line(color="#1F2933")
                    .encode(
                        x=alt.X("elapsed_minutes:Q", title="Elapsed Time (minutes)"),
                        y=alt.Y("effective_points:Q", title="Effective Points"),
                        tooltip=[
                            alt.Tooltip("elapsed_minutes:Q", format=".2f", title="Elapsed min"),
                            alt.Tooltip("Period:N"),
                            alt.Tooltip("Jam:Q"),
                            alt.Tooltip("effective_points:Q", title="Effective points"),
                        ],
                    )
                )
                points = (
                    alt.Chart(effective_time)
                    .mark_circle(size=80)
                    .encode(
                        x="elapsed_minutes:Q",
                        y="effective_points:Q",
                        color=alt.condition(
                            "datum.effective_points >= 0",
                            alt.value("#1A9850"),
                            alt.value("#D73027"),
                        ),
                        tooltip=[
                            alt.Tooltip("elapsed_minutes:Q", format=".2f", title="Elapsed min"),
                            alt.Tooltip("Period:N"),
                            alt.Tooltip("Jam:Q"),
                            alt.Tooltip("effective_points:Q", title="Effective points"),
                        ],
                    )
                )
                st.altair_chart(line + points, use_container_width=True)

    player_effective_title = "Cumulative Effective Points by Player - General"
    if rival_label and selected_periods:
        player_effective_title = f"Cumulative Effective Points by Player vs {rival_label} in {_period_phrase(selected_periods)}"
    elif rival_label:
        player_effective_title = f"Cumulative Effective Points by Player vs {rival_label}"

    st.subheader(player_effective_title)
    lineups_for_player = period_filtered.lineups.copy()
    if lineups_for_player.empty:
        st.info("No lineup data available for the selected filters.")
    else:
        role_cols = ["Jammer", "Pivot", "Block_1", "Block_2", "Block_3"]
        lineup_long = lineups_for_player[jam_keys + role_cols].melt(
            id_vars=jam_keys,
            value_vars=role_cols,
            value_name="Player_number",
        )
        lineup_long["Player_number"] = lineup_long["Player_number"].astype(str).str.strip()
        lineup_long = lineup_long[(lineup_long["Player_number"].notna()) & (lineup_long["Player_number"] != "0")].copy()

        # Count a player's impact once per jam even if data has duplicated role assignments.
        lineup_long = lineup_long.drop_duplicates(subset=jam_keys + ["Player_number"])
        player_effective = lineup_long.merge(
            effective[jam_keys + ["effective_points"]],
            on=jam_keys,
            how="inner",
        )

        if player_effective.empty:
            st.info("No player effective points data for the selected filters.")
        else:
            player_effective = (
                player_effective.groupby("Player_number", as_index=False)["effective_points"]
                .sum()
                .rename(columns={"effective_points": "cumulative_effective_points"})
            )

            names = filtered.player_names.copy()
            names["Player_number"] = names["Player_number"].astype(str).str.strip()
            player_effective = player_effective.merge(names, on="Player_number", how="left")
            player_effective["Player"] = player_effective["Name"].fillna("#" + player_effective["Player_number"])
            player_effective = player_effective.sort_values(
                ["cumulative_effective_points", "Player"], ascending=[False, True]
            ).reset_index(drop=True)

            player_effective_chart = (
                alt.Chart(player_effective)
                .mark_bar()
                .encode(
                    x=alt.X("Player:N", sort="-y", title="Player"),
                    y=alt.Y("cumulative_effective_points:Q", title="Cumulative Effective Points"),
                    color=alt.condition(
                        "datum.cumulative_effective_points >= 0",
                        alt.value("#1A9850"),
                        alt.value("#D73027"),
                    ),
                    tooltip=[
                        alt.Tooltip("Player:N"),
                        alt.Tooltip("cumulative_effective_points:Q", title="Cumulative effective points"),
                    ],
                )
            )
            st.altair_chart(player_effective_chart, use_container_width=True)

with st.expander("Show filtered team data"):
    st.dataframe(period_filtered.jam_table, use_container_width=True)
