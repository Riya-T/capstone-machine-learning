"""Hidden tests for the c_remove change (removing scores). Never shown to
the writer or the editor.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/private/test_remove_new.py
"""

import pytest
from scores import ScoreBoard, ScoreError

BAD_SCORES = [-1, 1.5, "10", None]


@pytest.fixture
def board():
    """ana: 300, 120, 300 (in that order); ben: 450."""
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    bd.record_score("ana", 300)
    bd.record_score("ben", 450)
    bd.record_score("ana", 120)
    bd.record_score("ana", 300)
    return bd


def state(bd):
    return {p: bd.get_scores(p) for p in bd.get_players()}


def test_remove_score_takes_the_most_recent_occurrence(board):
    board.remove_score("ana", 300)
    assert board.get_scores("ana") == [300, 120]
    assert board.get_latest_score("ana") == 120
    board.remove_score("ana", 300)
    assert board.get_scores("ana") == [120]
    assert board.get_scores("ben") == [450]
    assert board.get_players() == ["ana", "ben"]


def test_removal_updates_total_and_top_scores(board):
    board.remove_score("ana", 300)
    board.remove_score("ben", 450)
    assert board.get_total_score("ana") == 420
    assert board.get_total_score("ben") == 0
    assert board.get_top_scores(5) == [300, 120]


def test_removing_the_only_score_leaves_the_player_empty(board):
    board.remove_score("ben", 450)
    assert board.get_scores("ben") == []
    assert board.get_total_score("ben") == 0
    with pytest.raises(ScoreError):
        board.get_latest_score("ben")


def test_a_score_of_zero_can_be_recorded_and_removed(board):
    board.record_score("ben", 0)
    assert board.get_scores("ben") == [450, 0]
    board.remove_score("ben", 0)
    assert board.get_scores("ben") == [450]


def test_removing_a_missing_score_raises_and_changes_nothing(board):
    before = state(board)
    with pytest.raises(ScoreError):
        board.remove_score("ben", 300)  # ana's score, not ben's
    with pytest.raises(ScoreError):
        board.remove_score("ana", 7)
    assert state(board) == before


@pytest.mark.parametrize("score", BAD_SCORES)
def test_invalid_scores_are_rejected_by_remove(board, score):
    before = state(board)
    with pytest.raises(ValueError):
        board.remove_score("ana", score)
    assert state(board) == before


@pytest.mark.parametrize("name", ["dan", None, 1])
def test_unknown_players_raise_key_error(board, name):
    before = state(board)
    with pytest.raises(KeyError):
        board.remove_score(name, 300)
    assert state(board) == before


def test_errors_are_reported_in_order(board):
    with pytest.raises(KeyError):
        board.remove_score("dan", -1)
    with pytest.raises(ValueError):
        board.remove_score("ben", -1)  # ben has no -1 either, but the value is bad first


def test_undo_last_score_works_across_players(board):
    assert board.undo_last_score() == ("ana", 300)
    assert board.undo_last_score() == ("ana", 120)
    assert board.undo_last_score() == ("ben", 450)
    assert board.undo_last_score() == ("ana", 300)
    assert state(board) == {"ana": [], "ben": []}
    assert board.get_top_scores(3) == []


def test_undo_on_an_empty_board_raises(board):
    for _ in range(4):
        board.undo_last_score()
    with pytest.raises(ScoreError):
        board.undo_last_score()
    assert ScoreBoard().get_players() == []
    with pytest.raises(ScoreError):
        ScoreBoard().undo_last_score()


def test_undo_after_remove_takes_the_latest_remaining_score(board):
    board.remove_score("ana", 300)  # the most recent score
    assert board.undo_last_score() == ("ana", 120)
    assert board.get_scores("ana") == [300]
    assert board.undo_last_score() == ("ben", 450)


def test_scores_can_be_recorded_again_after_removal(board):
    board.undo_last_score()
    board.record_score("ana", 5)
    assert board.get_scores("ana") == [300, 120, 5]
    assert board.get_latest_score("ana") == 5
    assert board.undo_last_score() == ("ana", 5)
