"""Hidden tests for the c_corrections change (taking back events). Never
shown to the writer or the editor.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_corrections/private/test_corrections_new.py
"""

import pytest
from scoreboard import Scoreboard, ScoreboardError


@pytest.fixture
def board():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    sb.score("lions", "try")
    sb.score("lions", "conversion")
    sb.score("hawks", "drop_goal")
    return sb


def state(sb):
    teams = {t: (sb.get_score(t), sb.get_events(t), sb.get_undone(t)) for t in sb.get_teams()}
    return teams, sb.get_standings()


def test_corrections_undo_walks_back_one_event_at_a_time(board):
    board.score("lions", "drop_goal")
    assert board.undo_last("lions") == ("drop_goal", 3)
    assert board.undo_last("lions") == ("conversion", 2)
    assert board.undo_last("lions") == ("try", 5)
    assert board.get_score("lions") == 0
    assert board.get_events("lions") == []
    assert board.get_undone("lions") == [("drop_goal", 3), ("conversion", 2), ("try", 5)]


def test_corrections_an_empty_team_raises_and_changes_nothing(board):
    board.undo_last("hawks")
    before = state(board)
    with pytest.raises(ScoreboardError):
        board.undo_last("hawks")
    assert state(board) == before


@pytest.mark.parametrize("method", ["undo_last", "get_undone"])
@pytest.mark.parametrize("team", ["bears", None, 1])
def test_corrections_teams_that_were_not_added_raise_key_error(board, method, team):
    before = state(board)
    with pytest.raises(KeyError):
        getattr(board, method)(team)
    assert state(board) == before


def test_corrections_only_the_given_team_is_affected(board):
    board.undo_last("lions")
    assert board.get_score("hawks") == 3
    assert board.get_events("hawks") == [("drop_goal", 3)]
    assert board.get_undone("hawks") == []


def test_corrections_undo_removes_the_points_the_event_was_worth(board):
    board.set_points("conversion", 9)
    board.set_points("try", 1)
    assert board.undo_last("lions") == ("conversion", 2)
    assert board.get_score("lions") == 5
    assert board.undo_last("lions") == ("try", 5)
    assert board.get_score("lions") == 0


def test_corrections_standings_follow_an_undo(board):
    assert board.get_standings() == ["lions", "hawks"]
    board.undo_last("lions")  # lions 5, hawks 3
    assert board.get_standings() == ["lions", "hawks"]
    board.undo_last("lions")  # lions 0, hawks 3
    assert board.get_standings() == ["hawks", "lions"]
    board.undo_last("hawks")  # both 0: back to the order they were added
    assert board.get_standings() == ["lions", "hawks"]


def test_corrections_scoring_after_an_undo_works_as_usual(board):
    board.undo_last("lions")
    board.score("lions", "drop_goal")
    assert board.get_events("lions") == [("try", 5), ("drop_goal", 3)]
    assert board.get_score("lions") == 8
    assert board.undo_last("lions") == ("drop_goal", 3)
    assert board.get_events("lions") == [("try", 5)]
    assert board.get_undone("lions") == [("conversion", 2), ("drop_goal", 3)]


def test_corrections_undone_events_never_come_back(board):
    board.undo_last("lions")
    board.undo_last("lions")
    with pytest.raises(ScoreboardError):
        board.undo_last("lions")
    board.score("lions", "try")
    board.undo_last("lions")
    assert board.get_events("lions") == []
    assert board.get_score("lions") == 0


def test_corrections_a_custom_table_is_undone_with_its_values():
    sb = Scoreboard(points={"goal": 6, "behind": 1})
    sb.add_team("lions")
    sb.score("lions", "goal")
    sb.score("lions", "behind")
    assert sb.undo_last("lions") == ("behind", 1)
    assert sb.get_score("lions") == 6
