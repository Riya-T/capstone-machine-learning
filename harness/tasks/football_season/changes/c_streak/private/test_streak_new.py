"""Hidden tests for the c_streak change (current streaks). Never shown to the
writer or the editor.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_streak/private/test_streak_new.py
"""

import pytest
from season import Season


@pytest.fixture
def season():
    s = Season()
    for team in ["Bears", "Lions", "Packers"]:
        s.add_team(team)
    return s


def streak(s, team):
    return s.get_record(team)["streak"]


def test_one_game(season):
    season.record_game("Bears", "Lions", 10, 3)
    assert (streak(season, "Bears"), streak(season, "Lions")) == ("W1", "L1")
    assert streak(season, "Packers") == ""


def test_the_streak_restarts_when_the_result_changes(season):
    season.record_game("Bears", "Lions", 10, 3)
    season.record_game("Bears", "Packers", 10, 3)
    season.record_game("Lions", "Bears", 20, 3)
    assert streak(season, "Bears") == "L1"
    season.record_game("Bears", "Packers", 7, 0)
    assert streak(season, "Bears") == "W1"


def test_ties_have_their_own_streak(season):
    season.record_game("Bears", "Lions", 7, 7)
    season.record_game("Lions", "Bears", 3, 3)
    assert (streak(season, "Bears"), streak(season, "Lions")) == ("T2", "T2")
    season.record_game("Bears", "Packers", 0, 6)
    assert streak(season, "Bears") == "L1"


def test_home_and_away_games_both_count(season):
    season.record_game("Bears", "Lions", 10, 3)
    season.record_game("Packers", "Bears", 3, 10)
    assert streak(season, "Bears") == "W2"


def test_the_latest_recorded_games_decide(season):
    season.record_game("Bears", "Lions", 0, 3)
    season.record_game("Bears", "Lions", 10, 3)
    season.record_game("Bears", "Packers", 10, 3)
    assert streak(season, "Bears") == "W2"
    assert streak(season, "Lions") == "L1"


def test_long_streaks_count_past_nine(season):
    for _ in range(11):
        season.record_game("Bears", "Lions", 14, 0)
    assert streak(season, "Bears") == "W11"


def test_records_keep_their_other_keys(season):
    season.record_game("Bears", "Lions", 21, 14)
    record = season.get_record("Bears")
    assert (record["wins"], record["points_for"], record["points_against"]) == (1, 21, 14)
