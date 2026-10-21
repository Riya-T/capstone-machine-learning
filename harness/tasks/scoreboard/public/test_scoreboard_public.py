"""Public checks for scoreboard.py.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest public/test_scoreboard_public.py
"""

import pytest
from scoreboard import Scoreboard


@pytest.fixture
def board():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    return sb


def test_a_new_team_has_no_points(board):
    assert board.get_score("lions") == 0
    assert board.get_events("lions") == []


def test_each_kind_adds_its_points(board):
    board.score("lions", "try")
    board.score("lions", "conversion")
    board.score("lions", "drop_goal")
    assert board.get_score("lions") == 10


def test_events_are_listed_oldest_first(board):
    board.score("hawks", "drop_goal")
    board.score("hawks", "try")
    assert board.get_events("hawks") == [("drop_goal", 3), ("try", 5)]


def test_standings_put_the_highest_score_first(board):
    board.score("hawks", "conversion")
    assert board.get_standings() == ["hawks", "lions"]


def test_an_unknown_kind_raises_value_error(board):
    with pytest.raises(ValueError):
        board.score("lions", "touchdown")
    assert board.get_score("lions") == 0


def test_an_unknown_team_raises_key_error(board):
    with pytest.raises(KeyError):
        board.get_score("bears")
