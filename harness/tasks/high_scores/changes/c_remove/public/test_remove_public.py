"""Public checks for the c_remove change (removing scores). Shown to the
editor, never to the writer.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/public/test_remove_public.py
"""

import pytest
from scores import ScoreBoard, ScoreError


@pytest.fixture
def board():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    bd.record_score("ana", 300)
    bd.record_score("ben", 450)
    bd.record_score("ana", 120)
    return bd


def test_remove_score_takes_one_score_off_the_board(board):
    board.remove_score("ana", 300)
    assert board.get_scores("ana") == [120]
    assert board.get_total_score("ana") == 120
    assert board.get_top_scores(5) == [450, 120]


def test_undo_last_score_removes_the_most_recent_score(board):
    assert board.undo_last_score() == ("ana", 120)
    assert board.get_scores("ana") == [300]
    assert board.get_latest_score("ana") == 300
    assert board.undo_last_score() == ("ben", 450)
    assert board.get_scores("ben") == []


def test_removing_a_score_the_player_never_had_raises(board):
    with pytest.raises(ScoreError):
        board.remove_score("ana", 999)
    assert board.get_scores("ana") == [300, 120]
