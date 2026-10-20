"""Hidden tests for the c_remove change (removing games). Never shown to the
writer or the editor.

Usage (with season.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/private/test_remove_new.py
"""

import pytest
from season import Season

KEYS = ["wins", "losses", "ties", "points_for", "points_against"]
TEAMS = ["Bears", "Lions", "Packers"]
GAMES = [
    ("Bears", "Lions", 24, 17),
    ("Lions", "Packers", 13, 13),
    ("Packers", "Bears", 31, 7),
]


def season_with(games):
    s = Season()
    for team in TEAMS:
        s.add_team(team)
    ids = [s.record_game(*game) for game in games]
    return s, ids


def summary(s):
    records = {team: tuple(s.get_record(team)[key] for key in KEYS) for team in TEAMS}
    return records, s.get_standings()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_everything_is_as_if_the_game_never_happened(index):
    s, ids = season_with(GAMES)
    s.remove_game(ids[index])
    expected, _ = season_with(GAMES[:index] + GAMES[index + 1 :])
    assert summary(s) == summary(expected)


def test_removing_every_game_empties_the_records():
    s, ids = season_with(GAMES)
    for game_id in ids:
        s.remove_game(game_id)
    expected, _ = season_with([])
    assert summary(s) == summary(expected)


def test_ids_are_never_reused():
    s, ids = season_with(GAMES)
    s.remove_game(ids[2])
    assert s.record_game("Bears", "Packers", 3, 0) == 4
    assert s.get_game(4)["home"] == "Bears"


@pytest.mark.parametrize("bad_id", [99, 0, "1", None])
def test_ids_that_are_not_recorded_games_raise_key_error(bad_id):
    s, _ = season_with(GAMES)
    before = summary(s)
    with pytest.raises(KeyError):
        s.remove_game(bad_id)
    with pytest.raises(KeyError):
        s.get_game(bad_id)
    assert summary(s) == before


def test_a_removed_game_is_gone():
    s, ids = season_with(GAMES)
    s.remove_game(ids[1])
    with pytest.raises(KeyError):
        s.get_game(ids[1])
    with pytest.raises(KeyError):
        s.remove_game(ids[1])
    assert s.get_game(ids[0])["home"] == "Bears"


def test_get_game_returns_the_recorded_result():
    s, ids = season_with(GAMES)
    game = s.get_game(ids[2])
    assert {key: game[key] for key in ["home", "away", "home_score", "away_score"]} == {
        "home": "Packers",
        "away": "Bears",
        "home_score": 31,
        "away_score": 7,
    }
