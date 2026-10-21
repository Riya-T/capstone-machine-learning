"""Public checks for scores.py.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest public/test_scores_public.py
"""

import pytest
from scores import ScoreBoard


@pytest.fixture
def board():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    return bd


def test_scores_are_kept_in_the_order_recorded(board):
    board.record_score("ana", 300)
    board.record_score("ana", 120)
    board.record_score("ana", 300)
    assert board.get_scores("ana") == [300, 120, 300]
    assert board.get_players() == ["ana", "ben"]


def test_latest_and_total_follow_the_scores(board):
    board.record_score("ana", 300)
    board.record_score("ana", 120)
    assert board.get_latest_score("ana") == 120
    assert board.get_total_score("ana") == 420
    assert board.get_total_score("ben") == 0


def test_top_scores_come_from_every_player_highest_first(board):
    board.record_score("ana", 300)
    board.record_score("ben", 450)
    board.record_score("ana", 120)
    assert board.get_top_scores(2) == [450, 300]
    assert board.get_top_scores(10) == [450, 300, 120]


def test_unknown_player_raises_key_error(board):
    with pytest.raises(KeyError):
        board.record_score("cleo", 10)
    with pytest.raises(KeyError):
        board.get_scores("cleo")


def test_scores_must_be_non_negative_ints(board):
    with pytest.raises(ValueError):
        board.record_score("ana", -1)
    with pytest.raises(ValueError):
        board.record_score("ana", 2.5)
    assert board.get_scores("ana") == []
