"""Public checks for season.py.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest public/test_season_public.py
"""

import pytest
from season import Season


@pytest.fixture
def season():
    s = Season()
    for team in ["Bears", "Lions", "Packers"]:
        s.add_team(team)
    return s


def test_a_win_and_a_loss_are_counted(season):
    season.record_game("Bears", "Lions", 24, 17)
    assert season.get_record("Bears")["wins"] == 1
    assert season.get_record("Lions")["losses"] == 1


def test_points_are_counted_for_both_teams(season):
    season.record_game("Bears", "Lions", 24, 17)
    record = season.get_record("Lions")
    assert (record["points_for"], record["points_against"]) == (17, 24)


def test_a_tie_is_counted(season):
    season.record_game("Bears", "Lions", 10, 10)
    assert season.get_record("Bears")["ties"] == 1
    assert season.get_record("Lions")["ties"] == 1


def test_standings_rank_by_points(season):
    season.record_game("Packers", "Bears", 21, 14)
    season.record_game("Packers", "Lions", 28, 3)
    season.record_game("Lions", "Bears", 20, 10)
    assert season.get_standings() == ["Packers", "Lions", "Bears"]


def test_a_team_that_has_not_played_has_zero_points(season):
    season.record_game("Lions", "Packers", 10, 3)
    assert season.get_standings() == ["Lions", "Bears", "Packers"]


def test_teams_still_tied_keep_the_order_they_were_added():
    s = Season()
    s.add_team("Packers")
    s.add_team("Bears")
    s.record_game("Bears", "Packers", 7, 7)
    assert s.get_standings() == ["Packers", "Bears"]


def test_game_ids_count_up_from_one(season):
    assert season.record_game("Bears", "Lions", 3, 0) == 1
    assert season.record_game("Lions", "Packers", 7, 6) == 2


def test_unknown_teams_and_negative_scores_are_rejected(season):
    with pytest.raises(KeyError):
        season.record_game("Bears", "Vikings", 10, 3)
    with pytest.raises(ValueError):
        season.record_game("Bears", "Lions", -3, 0)
