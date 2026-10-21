"""Public checks for the c_best change (personal bests). Shown to the editor,
never to the writer.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_best/public/test_best_public.py
"""

import pytest
from scores import ScoreBoard, ScoreError


@pytest.fixture
def board():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    return bd


def test_personal_best_is_the_highest_score(board):
    for score in [120, 300, 50]:
        board.record_score("ana", score)
    assert board.get_personal_best("ana") == 300
    with pytest.raises(ScoreError):
        board.get_personal_best("ben")


def test_personal_best_count_counts_improvements(board):
    for score in [120, 300, 50, 300, 310]:
        board.record_score("ana", score)
    assert board.get_personal_best_count("ana") == 3
    assert board.get_personal_best_count("ben") == 0


def test_leaderboard_ranks_players_by_personal_best(board):
    board.record_score("ana", 120)
    board.record_score("ben", 450)
    board.record_score("ana", 300)
    assert board.get_leaderboard() == [("ben", 450), ("ana", 300)]
