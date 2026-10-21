"""Hidden tests for the initial high_scores spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest private/test_scores_initial.py
"""

import pytest
from scores import ScoreBoard, ScoreError

BAD_SCORES = [-1, -100, 1.5, "10", None]
BAD_COUNTS = [0, -1, 1.5, "3", None]


@pytest.fixture
def board():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    return bd


def state(bd):
    """Every player's scores, to check that a failed call changed nothing."""
    return {p: bd.get_scores(p) for p in bd.get_players()}


# --- players ----------------------------------------------------------------


def test_a_new_player_has_no_scores(board):
    assert board.get_scores("ana") == []
    assert board.get_total_score("ana") == 0
    with pytest.raises(ScoreError):
        board.get_latest_score("ana")


def test_players_are_listed_in_the_order_added():
    bd = ScoreBoard()
    for name in ["cleo", "ana", "ben"]:
        bd.add_player(name)
    assert bd.get_players() == ["cleo", "ana", "ben"]


def test_an_empty_name_is_rejected():
    bd = ScoreBoard()
    with pytest.raises(ValueError):
        bd.add_player("")
    assert bd.get_players() == []


def test_a_name_already_on_the_board_is_rejected(board):
    board.record_score("ana", 50)
    with pytest.raises(ScoreError):
        board.add_player("ana")
    assert board.get_players() == ["ana", "ben"]
    assert board.get_scores("ana") == [50]


@pytest.mark.parametrize(
    "call",
    [
        lambda bd: bd.record_score("cleo", 10),
        lambda bd: bd.get_scores("cleo"),
        lambda bd: bd.get_latest_score("cleo"),
        lambda bd: bd.get_total_score("cleo"),
        lambda bd: bd.get_scores(None),
        lambda bd: bd.get_scores(1),
        lambda bd: bd.record_score(None, 10),
    ],
)
def test_players_not_on_the_board_raise_key_error(board, call):
    board.record_score("ana", 50)
    before = state(board)
    with pytest.raises(KeyError):
        call(board)
    assert state(board) == before


# --- scores -----------------------------------------------------------------


def test_scores_are_listed_in_the_order_recorded_with_repeats(board):
    for score in [300, 120, 300, 7]:
        board.record_score("ana", score)
    assert board.get_scores("ana") == [300, 120, 300, 7]
    assert board.get_scores("ben") == []


def test_a_score_of_zero_is_allowed(board):
    board.record_score("ana", 0)
    assert board.get_scores("ana") == [0]
    assert board.get_latest_score("ana") == 0
    assert board.get_top_scores(1) == [0]


@pytest.mark.parametrize("score", BAD_SCORES)
def test_invalid_scores_are_rejected(board, score):
    board.record_score("ana", 50)
    before = state(board)
    with pytest.raises(ValueError):
        board.record_score("ana", score)
    assert state(board) == before


def test_an_unknown_player_is_reported_before_a_bad_score(board):
    with pytest.raises(KeyError):
        board.record_score("cleo", -1)


def test_latest_score_is_the_most_recent_one(board):
    board.record_score("ana", 300)
    assert board.get_latest_score("ana") == 300
    board.record_score("ana", 20)
    assert board.get_latest_score("ana") == 20
    board.record_score("ben", 999)
    assert board.get_latest_score("ana") == 20


def test_total_score_sums_every_score(board):
    for score in [300, 120, 0, 80]:
        board.record_score("ana", score)
    board.record_score("ben", 5)
    assert board.get_total_score("ana") == 500
    assert board.get_total_score("ben") == 5


# --- top scores -------------------------------------------------------------


def test_top_scores_are_highest_first_over_all_players(board):
    board.record_score("ana", 300)
    board.record_score("ben", 450)
    board.record_score("ana", 120)
    board.record_score("ben", 90)
    assert board.get_top_scores(3) == [450, 300, 120]


def test_top_scores_returns_fewer_when_the_board_has_fewer(board):
    board.record_score("ana", 10)
    board.record_score("ben", 20)
    assert board.get_top_scores(5) == [20, 10]
    assert board.get_top_scores(1) == [20]


def test_repeated_scores_appear_repeatedly_in_the_top(board):
    board.record_score("ana", 100)
    board.record_score("ben", 100)
    board.record_score("ana", 40)
    assert board.get_top_scores(3) == [100, 100, 40]


def test_top_scores_of_an_empty_board_is_empty(board):
    assert board.get_top_scores(3) == []
    assert ScoreBoard().get_top_scores(1) == []


@pytest.mark.parametrize("n", BAD_COUNTS)
def test_invalid_counts_are_rejected(board, n):
    board.record_score("ana", 10)
    with pytest.raises(ValueError):
        board.get_top_scores(n)
    assert board.get_scores("ana") == [10]


def test_reading_the_top_does_not_reorder_the_scores(board):
    for score in [5, 50, 20]:
        board.record_score("ana", score)
    board.get_top_scores(3)
    assert board.get_scores("ana") == [5, 50, 20]
    assert board.get_latest_score("ana") == 20


def test_boards_do_not_share_players():
    first, second = ScoreBoard(), ScoreBoard()
    first.add_player("ana")
    first.record_score("ana", 5)
    assert second.get_players() == []
    second.add_player("ana")
    assert second.get_scores("ana") == []
    assert second.get_top_scores(1) == []
