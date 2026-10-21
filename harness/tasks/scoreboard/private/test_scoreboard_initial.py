"""Hidden tests for the initial scoreboard spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with scoreboard.py importable, e.g. in the sandbox):
    python -m pytest private/test_scoreboard_initial.py
"""

import pytest
from scoreboard import Scoreboard, ScoreboardError

BAD_KINDS = ["Try", "", "touchdown", "drop goal", None, 5]


@pytest.fixture
def board():
    sb = Scoreboard()
    sb.add_team("lions")
    sb.add_team("hawks")
    return sb


def state(sb):
    """Every score, event list and the standings, to check that a failed call
    changed nothing."""
    teams = {t: (sb.get_score(t), sb.get_events(t)) for t in sb.get_teams()}
    return teams, sb.get_standings()


# --- teams ------------------------------------------------------------------


def test_new_teams_start_with_nothing(board):
    assert board.get_score("hawks") == 0
    assert board.get_events("hawks") == []
    assert board.get_teams() == ["lions", "hawks"]


def test_teams_are_listed_in_the_order_they_were_added():
    sb = Scoreboard()
    for name in ["wolves", "bears", "owls"]:
        sb.add_team(name)
    assert sb.get_teams() == ["wolves", "bears", "owls"]


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_team_names_are_rejected(bad_name):
    sb = Scoreboard()
    with pytest.raises(ValueError):
        sb.add_team(bad_name)
    assert sb.get_teams() == []


def test_adding_a_team_twice_is_rejected(board):
    board.score("lions", "try")
    before = state(board)
    with pytest.raises(ScoreboardError):
        board.add_team("lions")
    assert state(board) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda sb: sb.score("bears", "try"),
        lambda sb: sb.get_score("bears"),
        lambda sb: sb.get_events("bears"),
        lambda sb: sb.get_score(None),
        lambda sb: sb.get_events(1),
        lambda sb: sb.score(None, "try"),
    ],
)
def test_teams_that_were_not_added_raise_key_error(board, call):
    board.score("lions", "try")
    before = state(board)
    with pytest.raises(KeyError):
        call(board)
    assert state(board) == before


# --- scoring ----------------------------------------------------------------


@pytest.mark.parametrize("kind, points", [("try", 5), ("conversion", 2), ("drop_goal", 3)])
def test_each_kind_is_worth_its_points(board, kind, points):
    board.score("lions", kind)
    assert board.get_score("lions") == points
    assert board.get_events("lions") == [(kind, points)]


def test_points_add_up_over_many_events(board):
    for kind in ["try", "conversion", "try", "drop_goal", "try"]:
        board.score("lions", kind)
    assert board.get_score("lions") == 20


def test_events_keep_their_order_and_points(board):
    board.score("hawks", "conversion")
    board.score("hawks", "try")
    board.score("hawks", "conversion")
    board.score("hawks", "drop_goal")
    assert board.get_events("hawks") == [
        ("conversion", 2),
        ("try", 5),
        ("conversion", 2),
        ("drop_goal", 3),
    ]


def test_scoring_for_one_team_leaves_the_others_alone(board):
    board.score("lions", "try")
    board.score("lions", "drop_goal")
    assert board.get_score("hawks") == 0
    assert board.get_events("hawks") == []


@pytest.mark.parametrize("kind", BAD_KINDS)
def test_unknown_kinds_are_rejected_and_change_nothing(board, kind):
    board.score("lions", "conversion")
    before = state(board)
    with pytest.raises(ValueError):
        board.score("lions", kind)
    assert state(board) == before


def test_a_team_that_was_not_added_is_reported_before_a_bad_kind(board):
    with pytest.raises(KeyError):
        board.score("bears", "touchdown")
    with pytest.raises(KeyError):
        board.score(None, None)


def test_failed_calls_record_no_events(board):
    board.score("lions", "try")
    for call in (
        lambda: board.score("lions", "Try"),
        lambda: board.score("hawks", ""),
        lambda: board.score("bears", "try"),
        lambda: board.add_team("hawks"),
    ):
        with pytest.raises((ValueError, KeyError, ScoreboardError)):
            call()
    assert board.get_events("lions") == [("try", 5)]
    assert board.get_events("hawks") == []


# --- standings --------------------------------------------------------------


def test_standings_order_teams_by_score():
    sb = Scoreboard()
    for name in ["owls", "bears", "wolves"]:
        sb.add_team(name)
    sb.score("wolves", "try")
    sb.score("owls", "conversion")
    sb.score("bears", "drop_goal")
    assert sb.get_standings() == ["wolves", "bears", "owls"]


def test_equal_scores_keep_the_order_teams_were_added():
    sb = Scoreboard()
    for name in ["wolves", "bears", "owls", "ants"]:
        sb.add_team(name)
    sb.score("owls", "try")
    sb.score("ants", "drop_goal")
    sb.score("ants", "conversion")
    # owls and ants both have 5; wolves and bears both have 0.
    assert sb.get_standings() == ["owls", "ants", "wolves", "bears"]


def test_teams_without_events_are_in_the_standings(board):
    assert board.get_standings() == ["lions", "hawks"]


def test_standings_follow_the_lead_changing(board):
    board.score("hawks", "drop_goal")
    assert board.get_standings() == ["hawks", "lions"]
    board.score("lions", "try")
    assert board.get_standings() == ["lions", "hawks"]
    board.score("hawks", "conversion")
    assert board.get_standings() == ["lions", "hawks"]


def test_an_empty_scoreboard_has_empty_standings():
    sb = Scoreboard()
    assert sb.get_standings() == []
    assert sb.get_teams() == []


def test_scoreboard_error_is_not_a_key_or_value_error():
    assert issubclass(ScoreboardError, Exception)
    assert not issubclass(ScoreboardError, (KeyError, ValueError))


def test_scoreboards_do_not_share_teams():
    first, second = Scoreboard(), Scoreboard()
    first.add_team("lions")
    first.score("lions", "try")
    assert second.get_teams() == []
    second.add_team("lions")
    assert second.get_score("lions") == 0
