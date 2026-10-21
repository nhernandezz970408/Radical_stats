import pandas as pd

from radical_stats.data_loader import load_data
from radical_stats.lineups import count_incomplete_jams, lineups_long
from radical_stats.metrics import build_player_table, build_team_metrics


def _row(jam=1, **players):
    row = {"Date": pd.Timestamp("2026-01-01").date(), "Rival": "X", "Period": 1, "Jam": jam,
           "Jammer": 1, "Pivot": 2, "Block_1": 3, "Block_2": 4, "Block_3": 5}
    row.update(players)
    return row


def test_synthetic_jam_has_five_rows_with_roles() -> None:
    long = lineups_long(pd.DataFrame([_row()]))
    assert len(long) == 5
    roles = dict(zip(long["Player_number"], long["Role"]))
    assert roles == {"1": "Jammer", "2": "Pivot", "3": "Bloque", "4": "Bloque", "5": "Bloque"}


def test_question_mark_and_zero_produce_no_rows() -> None:
    long = lineups_long(pd.DataFrame([_row(Pivot="?", Block_3="0")]))
    assert len(long) == 3
    assert "?" not in long["Player_number"].tolist()


def test_repeated_player_is_not_duplicated() -> None:
    long = lineups_long(pd.DataFrame([_row(Pivot=1, Block_1=1)]))
    assert long["Player_number"].tolist().count("1") == 1
    assert long.loc[long["Player_number"] == "1", "Role"].item() == "Jammer"


def test_box_columns_follow_source_position() -> None:
    row = _row(Block_2_Start_jam_Box=1, Block_2_Finish_jam_Box=0)
    long = lineups_long(pd.DataFrame([row]))
    assert long.loc[long["Player_number"] == "4", "Start_box"].item() == 1


def test_real_data() -> None:
    frames = load_data()
    long = lineups_long(frames.lineups)
    assert len(long) == 751
    assert not long.duplicated(["Date", "Period", "Jam", "Player_number"]).any()
    assert count_incomplete_jams(frames.lineups, long) == 1

    players = build_player_table(frames)
    assert "?" not in players["Player_number"].tolist()
    assert (players["jams_played"] <= len(frames.lineups)).all()
    assert (players["jams_played"] == players[["jams_as_jammer", "jams_as_pivot", "jams_as_bloque"]].sum(axis=1)).all()
    assert build_team_metrics(frames)["total_players"] == players["Player_number"].nunique()
