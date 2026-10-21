from radical_stats.data_loader import load_data
from radical_stats.validation import jammer_mismatches, penalties_off_track


def test_period_is_1_or_2_everywhere() -> None:
    frames = load_data()
    for df in (frames.jam_table, frames.rival_jam_table, frames.lineups, frames.penalty_tracker, frames.time):
        assert set(df["Period"].unique()) <= {1, 2}


def test_lineups_jammer_matches_jam_table() -> None:
    frames = load_data()
    assert len(frames.lineups) == 151
    assert len(jammer_mismatches(frames)) == 0


def test_penalties_fall_on_players_on_track() -> None:
    frames = load_data()
    total = len(frames.penalty_tracker)
    off = len(penalties_off_track(frames))
    assert total == 131
    assert total - off >= 130
