"""Hidden tests for the c_periods change (scores per period). Never shown to
the writer or the editor.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_periods/private/test_periods_new.py
"""

import pytest
from scoreboard import Scoreboard

BAD_PERIODS = [0, -1, 3, True, 1.0, "1"]


@pytest.fixture
def board():
    """Two periods played, the board now in period 2."""
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    sb.score("lions", "try")
    sb.score("hawks", "drop_goal")
    sb.score("lions", "conversion")
    sb.next_period()
    sb.score("hawks", "try")
    sb.score("hawks", "conversion")
    return sb


def state(sb):
    teams = {
        t: (sb.get_score(t), sb.get_events(t), sb.get_period_scores(t)) for t in sb.get_teams()
    }
    return teams, sb.get_standings(), sb.get_period()


def test_periods_a_new_board_is_in_period_one():
    sb = Scoreboard()
    sb.add_team("lions")
    assert sb.get_period() == 1
    assert sb.get_period_scores("lions") == [0]


def test_periods_next_period_counts_up():
    sb = Scoreboard()
    assert [sb.next_period() for _ in range(3)] == [2, 3, 4]
    assert sb.get_period() == 4


def test_periods_scores_per_period(board):
    assert board.get_period_scores("lions") == [7, 0]
    assert board.get_period_scores("hawks") == [3, 7]
    assert (board.get_score("lions"), board.get_score("hawks")) == (7, 10)
    board.next_period()
    assert board.get_period_scores("lions") == [7, 0, 0]


def test_periods_events_can_be_filtered_by_period(board):
    assert board.get_events("hawks", period=1) == [("drop_goal", 3)]
    assert board.get_events("hawks", period=2) == [("try", 5), ("conversion", 2)]
    assert board.get_events("lions", period=2) == []
    assert board.get_events("hawks") == [("drop_goal", 3), ("try", 5), ("conversion", 2)]
    assert board.get_events("hawks", period=None) == board.get_events("hawks")


@pytest.mark.parametrize("period", BAD_PERIODS)
def test_periods_bad_periods_are_rejected(board, period):
    before = state(board)
    with pytest.raises(ValueError):
        board.get_events("lions", period=period)
    with pytest.raises(ValueError):
        board.get_period_standings(period)
    assert state(board) == before


def test_periods_an_unknown_team_is_reported_before_a_bad_period(board):
    with pytest.raises(KeyError):
        board.get_events("bears", period=0)
    with pytest.raises(KeyError):
        board.get_period_scores("bears")


def test_periods_standings_per_period(board):
    board.add_team("owls")
    assert board.get_period_standings(1) == ["lions", "hawks", "owls"]
    assert board.get_period_standings(2) == ["hawks", "lions", "owls"]
    assert board.get_standings() == ["hawks", "lions", "owls"]


def test_periods_equal_points_in_a_period_keep_the_adding_order(board):
    board.next_period()
    board.score("hawks", "drop_goal")
    board.score("lions", "drop_goal")
    assert board.get_period_standings(3) == ["lions", "hawks"]


def test_periods_undo_reaches_back_into_an_earlier_period(board):
    board.next_period()
    assert board.undo_last("lions") == ("conversion", 2)
    assert board.get_period_scores("lions") == [5, 0, 0]
    assert board.get_events("lions", period=1) == [("try", 5)]
    assert board.get_period() == 3


def test_periods_set_points_and_periods_work_together():
    sb = Scoreboard(points={"goal": 6, "behind": 1})
    sb.add_team("lions")
    sb.score("lions", "goal")
    sb.next_period()
    sb.set_points("goal", 4)
    sb.score("lions", "goal")
    sb.score("lions", "behind")
    assert sb.get_period_scores("lions") == [6, 5]
    assert sb.get_events("lions", period=2) == [("goal", 4), ("behind", 1)]
