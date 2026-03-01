from radical_stats.data_loader import load_data
from radical_stats.metrics import build_player_table, build_team_metrics


def test_metrics_smoke() -> None:
    frames = load_data()
    team = build_team_metrics(frames)
    players = build_player_table(frames)

    assert not team.empty
    assert "total_points" in team.index
    assert not players.empty
    assert "player_label" in players.columns
