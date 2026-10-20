"""Hidden tests for the initial football_season spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest private/test_season_initial.py
"""

import pytest
from season import Season

KEYS = ["wins", "losses", "ties", "points_for", "points_against"]


def season_with(*teams):
    s = Season()
    for team in teams:
        s.add_team(team)
    return s


def record(s, team):
    """The listed keys of a record, as a tuple (records may have more keys)."""
    return tuple(s.get_record(team)[key] for key in KEYS)


def all_records(s, teams):
    return {team: record(s, team) for team in teams}


# --- teams ------------------------------------------------------------------


def test_a_new_team_has_an_empty_record():
    s = season_with("Bears")
    assert record(s, "Bears") == (0, 0, 0, 0, 0)


def test_teams_that_have_not_played_keep_the_order_added():
    s = season_with("Lions", "Bears", "Packers")
    assert s.get_standings() == ["Lions", "Bears", "Packers"]


@pytest.mark.parametrize("name", [""])
def test_invalid_team_names_are_rejected(name):
    s = Season()
    with pytest.raises(ValueError):
        s.add_team(name)
    assert s.get_standings() == []


def test_a_team_cannot_be_added_twice():
    s = season_with("Bears")
    with pytest.raises(ValueError):
        s.add_team("Bears")
    assert s.get_standings() == ["Bears"]


@pytest.mark.parametrize("team", ["Vikings", None, 1])
def test_get_record_of_a_team_not_added_raises_key_error(team):
    with pytest.raises(KeyError):
        season_with("Bears").get_record(team)


# --- games ------------------------------------------------------------------


def test_every_result_is_counted_for_both_teams():
    s = season_with("Bears", "Lions", "Packers")
    s.record_game("Bears", "Lions", 24, 17)
    s.record_game("Lions", "Packers", 13, 13)
    s.record_game("Packers", "Bears", 31, 7)
    assert all_records(s, ["Bears", "Lions", "Packers"]) == {
        "Bears": (1, 1, 0, 31, 48),
        "Lions": (0, 1, 1, 30, 37),
        "Packers": (1, 0, 1, 44, 20),
    }


def test_teams_can_meet_more_than_once():
    s = season_with("Bears", "Lions")
    s.record_game("Bears", "Lions", 10, 3)
    s.record_game("Lions", "Bears", 27, 24)
    s.record_game("Bears", "Lions", 17, 17)
    assert record(s, "Bears") == (1, 1, 1, 51, 47)
    assert record(s, "Lions") == (1, 1, 1, 47, 51)


@pytest.mark.parametrize(
    ("home", "away"),
    [("Vikings", "Bears"), ("Bears", "Vikings"), (None, "Bears"), ("Bears", 7)],
)
def test_teams_not_added_raise_key_error(home, away):
    s = season_with("Bears", "Lions")
    with pytest.raises(KeyError):
        s.record_game(home, away, 10, 3)
    assert all_records(s, ["Bears", "Lions"]) == {"Bears": (0,) * 5, "Lions": (0,) * 5}


def test_a_team_cannot_play_itself():
    s = season_with("Bears")
    with pytest.raises(ValueError):
        s.record_game("Bears", "Bears", 10, 3)
    assert record(s, "Bears") == (0,) * 5


@pytest.mark.parametrize("score", [-1, 1.5, "7", None])
def test_invalid_scores_are_rejected(score):
    s = season_with("Bears", "Lions")
    with pytest.raises(ValueError):
        s.record_game("Bears", "Lions", score, 3)
    with pytest.raises(ValueError):
        s.record_game("Bears", "Lions", 3, score)
    assert record(s, "Bears") == (0,) * 5


def test_key_error_comes_before_value_error():
    s = season_with("Bears")
    with pytest.raises(KeyError):
        s.record_game("Vikings", "Vikings", -1, 0)


def test_a_failed_call_uses_up_no_id():
    s = season_with("Bears", "Lions")
    assert s.record_game("Bears", "Lions", 10, 3) == 1
    with pytest.raises(ValueError):
        s.record_game("Bears", "Lions", -1, 3)
    with pytest.raises(KeyError):
        s.record_game("Bears", "Vikings", 10, 3)
    assert s.record_game("Lions", "Bears", 10, 3) == 2


# --- standings --------------------------------------------------------------


def test_a_tie_counts_as_half_a_win():
    s = season_with("Alpha", "Beta", "X", "Y")
    s.record_game("Alpha", "X", 10, 7)
    s.record_game("Alpha", "Y", 3, 3)  # Alpha 1-0-1: 3 points, differential +3
    s.record_game("Beta", "X", 40, 0)
    s.record_game("Y", "Beta", 1, 0)  # Beta 1-1: 2 points, differential +39
    # Y (a tie and a win: 3 points, +1) ties Alpha on points but not on differential.
    assert s.get_standings() == ["Alpha", "Y", "Beta", "X"]


def test_a_team_that_has_not_played_has_zero_points():
    s = season_with("Bears", "Lions", "Packers")
    s.record_game("Lions", "Packers", 10, 3)
    # Bears and Packers are both at 0; Bears' differential (0) beats -7.
    assert s.get_standings() == ["Lions", "Bears", "Packers"]


def test_point_differential_breaks_a_tie_on_points():
    s = season_with("Alpha", "Zeta", "C", "D")
    s.record_game("Zeta", "C", 30, 10)
    s.record_game("Alpha", "D", 14, 13)
    assert s.get_standings()[:2] == ["Zeta", "Alpha"]


def test_the_order_added_breaks_a_complete_tie():
    s = season_with("Zeta", "Alpha", "Mid")
    s.record_game("Alpha", "Zeta", 7, 7)
    assert s.get_standings() == ["Zeta", "Alpha", "Mid"]


def test_seasons_do_not_share_teams_or_games():
    first, second = season_with("Bears", "Lions"), Season()
    first.record_game("Bears", "Lions", 10, 3)
    assert second.get_standings() == []
    second.add_team("Bears")
    second.add_team("Lions")
    assert second.record_game("Bears", "Lions", 0, 0) == 1
    assert record(second, "Bears") == (0, 0, 1, 0, 0)
