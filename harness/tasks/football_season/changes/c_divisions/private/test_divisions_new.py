"""Hidden tests for the c_divisions change (divisions). Never shown to the
writer or the editor.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_divisions/private/test_divisions_new.py
"""

import pytest
from season import Season

DIVISION_KEYS = ["division_wins", "division_losses", "division_ties"]


@pytest.fixture
def season():
    s = Season()
    for team in ["Bears", "Lions", "Packers"]:
        s.add_team(team, division="North")
    for team in ["Saints", "Falcons"]:
        s.add_team(team, division="South")
    s.add_team("Jets")
    s.add_team("Giants")
    return s


def division_record(s, team):
    return tuple(s.get_record(team)[key] for key in DIVISION_KEYS)


def test_without_a_division_every_team_is_ranked_together(season):
    season.record_game("Saints", "Jets", 21, 3)
    assert season.get_standings() == [
        "Saints",
        "Bears",
        "Lions",
        "Packers",
        "Falcons",
        "Giants",
        "Jets",
    ]


def test_division_standings_use_the_same_ranking(season):
    season.record_game("Packers", "Lions", 10, 3)
    season.record_game("Bears", "Saints", 3, 30)
    assert season.get_standings("North") == ["Packers", "Lions", "Bears"]
    assert season.get_standings("South") == ["Saints", "Falcons"]


def test_a_division_no_team_belongs_to_raises_key_error(season):
    with pytest.raises(KeyError):
        season.get_standings("West")


@pytest.mark.parametrize("division", ["", 5])
def test_invalid_divisions_are_rejected(division):
    s = Season()
    with pytest.raises(ValueError):
        s.add_team("Bears", division=division)
    assert s.get_standings() == []


def test_only_games_within_the_division_count(season):
    season.record_game("Bears", "Lions", 21, 14)
    season.record_game("Bears", "Saints", 10, 17)
    season.record_game("Packers", "Bears", 7, 7)
    record = season.get_record("Bears")
    assert (record["wins"], record["losses"], record["ties"]) == (1, 1, 1)
    assert division_record(season, "Bears") == (1, 0, 1)
    assert division_record(season, "Saints") == (0, 0, 0)


def test_teams_without_a_division_have_no_division_games(season):
    season.record_game("Jets", "Giants", 20, 3)
    assert season.get_record("Jets")["wins"] == 1
    assert division_record(season, "Jets") == (0, 0, 0)
    assert division_record(season, "Giants") == (0, 0, 0)


def test_removing_a_division_game_takes_back_its_division_result(season):
    game_id = season.record_game("Bears", "Lions", 21, 14)
    season.record_game("Lions", "Packers", 3, 0)
    season.remove_game(game_id)
    assert division_record(season, "Bears") == (0, 0, 0)
    assert division_record(season, "Lions") == (1, 0, 0)


def test_records_keep_their_other_keys(season):
    season.record_game("Bears", "Lions", 21, 14)
    record = season.get_record("Bears")
    assert (record["wins"], record["points_for"], record["points_against"]) == (1, 21, 14)
