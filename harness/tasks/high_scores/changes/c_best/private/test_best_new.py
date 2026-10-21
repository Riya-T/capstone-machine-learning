"""Hidden tests for the c_best change (personal bests). Never shown to the
writer or the editor.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_best/private/test_best_new.py
"""

import pytest
from scores import ScoreBoard, ScoreError


@pytest.fixture
def board():
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    bd.add_player("cleo")
    return bd


def test_a_player_without_scores_has_no_best_and_a_count_of_zero(board):
    with pytest.raises(ScoreError):
        board.get_personal_best("ana")
    assert board.get_personal_best_count("ana") == 0
    assert board.get_leaderboard() == []


def test_personal_best_ignores_the_order_of_scores(board):
    for score in [300, 120, 50]:
        board.record_score("ana", score)
    assert board.get_personal_best("ana") == 300
    board.record_score("ana", 301)
    assert board.get_personal_best("ana") == 301


def test_the_first_score_is_always_a_personal_best(board):
    board.record_score("ana", 5)
    assert board.get_personal_best_count("ana") == 1
    assert board.get_personal_best("ana") == 5


def test_only_strictly_higher_scores_count_as_new_bests(board):
    for score in [100, 100, 90, 101, 101, 150]:
        board.record_score("ana", score)
    assert board.get_personal_best_count("ana") == 3


def test_a_single_high_score_followed_by_lower_ones_counts_once(board):
    for score in [500, 10, 20, 30]:
        board.record_score("ana", score)
    assert board.get_personal_best_count("ana") == 1
    assert board.get_personal_best("ana") == 500


def test_leaderboard_uses_each_players_best_not_latest_or_total(board):
    for score in [400, 10]:
        board.record_score("ana", score)
    for score in [200, 200, 200]:
        board.record_score("ben", score)
    board.record_score("cleo", 350)
    assert board.get_leaderboard() == [("ana", 400), ("cleo", 350), ("ben", 200)]


def test_leaderboard_ties_keep_the_order_players_were_added(board):
    board.record_score("cleo", 100)
    board.record_score("ana", 100)
    board.record_score("ben", 100)
    assert board.get_leaderboard() == [("ana", 100), ("ben", 100), ("cleo", 100)]


def test_leaderboard_leaves_out_players_without_scores(board):
    board.record_score("cleo", 70)
    assert board.get_leaderboard() == [("cleo", 70)]


def test_leaderboard_follows_later_scores(board):
    board.record_score("ana", 100)
    board.record_score("ben", 200)
    assert board.get_leaderboard() == [("ben", 200), ("ana", 100)]
    board.record_score("ana", 250)
    assert board.get_leaderboard() == [("ana", 250), ("ben", 200)]


@pytest.mark.parametrize("method", ["get_personal_best", "get_personal_best_count"])
@pytest.mark.parametrize("name", ["dan", None, 1])
def test_unknown_players_raise_key_error(board, method, name):
    with pytest.raises(KeyError):
        getattr(board, method)(name)


def test_reading_bests_changes_nothing(board):
    for score in [30, 10, 20]:
        board.record_score("ana", score)
    board.get_personal_best("ana")
    board.get_personal_best_count("ana")
    board.get_leaderboard()
    assert board.get_scores("ana") == [30, 10, 20]
    assert board.get_latest_score("ana") == 20
