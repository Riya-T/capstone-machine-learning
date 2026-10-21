"""Hidden tests for the c_versions change (version numbers per team). Never
shown to the writer or the editor.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from scoreboard import Scoreboard, ScoreboardError, VersionConflict


@pytest.fixture
def board():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    sb.score("lions", "try")
    sb.score("lions", "conversion")
    return sb


def state(sb):
    teams = {
        t: (sb.get_score(t), sb.get_events(t), sb.get_version(t)) for t in sb.get_teams()
    }
    return teams, sb.get_standings()


def test_versions_new_teams_start_at_one(board):
    board.add_team("owls")
    assert board.get_version("owls") == 1
    assert board.get_version("hawks") == 1


def test_versions_go_up_by_one_per_score(board):
    assert board.get_version("lions") == 3
    board.score("lions", "drop_goal")
    assert board.get_version("lions") == 4


def test_versions_scoring_leaves_other_teams_alone(board):
    board.score("hawks", "try")
    assert board.get_version("hawks") == 2
    assert board.get_version("lions") == 3


def test_versions_the_current_version_is_accepted(board):
    board.score("lions", "try", expected_version=3)
    board.score("hawks", "try", expected_version=1)
    assert board.get_events("lions") == [("try", 5), ("conversion", 2), ("try", 5)]
    assert (board.get_version("lions"), board.get_version("hawks")) == (4, 2)


@pytest.mark.parametrize("expected", [1, 2, 4, 100])
def test_versions_any_other_version_conflicts_and_changes_nothing(board, expected):
    before = state(board)
    with pytest.raises(VersionConflict):
        board.score("lions", "drop_goal", expected_version=expected)
    assert state(board) == before


def test_versions_none_means_no_check(board):
    board.score("lions", "try", expected_version=None)
    assert board.get_version("lions") == 4


def test_versions_failed_calls_do_not_change_the_version(board):
    for call in (
        lambda: board.score("lions", "touchdown"),
        lambda: board.score("lions", "try", expected_version=1),
        lambda: board.add_team("lions"),
    ):
        with pytest.raises((ValueError, ScoreboardError)):
            call()
    assert board.get_version("lions") == 3


@pytest.mark.parametrize("team", ["bears", None, 1])
def test_versions_teams_that_were_not_added_raise_key_error(board, team):
    with pytest.raises(KeyError):
        board.get_version(team)


def test_versions_error_order(board):
    with pytest.raises(KeyError):
        board.score("bears", "touchdown", expected_version=99)
    with pytest.raises(ValueError):
        board.score("lions", "touchdown", expected_version=99)


def test_versions_conflict_is_a_scoreboard_error():
    assert issubclass(VersionConflict, ScoreboardError)


def test_versions_two_devices_one_wins(board):
    seen = board.get_version("hawks")
    board.score("hawks", "try", expected_version=seen)  # first device
    with pytest.raises(VersionConflict):
        board.score("hawks", "try", expected_version=seen)  # second device, stale
    assert board.get_events("hawks") == [("try", 5)]
    board.score("hawks", "conversion", expected_version=board.get_version("hawks"))
    assert board.get_score("hawks") == 7
