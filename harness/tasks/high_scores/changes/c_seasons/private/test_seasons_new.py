"""Hidden tests for the c_seasons change (seasons). Never shown to the writer
or the editor.

Usage (with scores.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seasons/private/test_seasons_new.py
"""

import pytest
from scores import ScoreBoard, ScoreError

BAD_SEASON_NAMES = ["", None, 3]


@pytest.fixture
def board():
    """ana: 100 in default, 250 in spring. ben: 400 in default only."""
    bd = ScoreBoard()
    bd.add_player("ana")
    bd.add_player("ben")
    bd.record_score("ana", 100)
    bd.record_score("ben", 400)
    bd.start_season("spring")
    bd.record_score("ana", 250)
    return bd


def test_a_new_board_is_in_the_default_season():
    bd = ScoreBoard()
    assert bd.get_seasons() == ["default"]
    assert bd.get_current_season() == "default"
    bd.add_player("ana")
    bd.record_score("ana", 5)
    assert bd.get_scores("ana", season="default") == [5]


def test_seasons_are_listed_in_the_order_started(board):
    board.start_season("summer")
    board.start_season("autumn")
    assert board.get_seasons() == ["default", "spring", "summer", "autumn"]
    assert board.get_current_season() == "autumn"


@pytest.mark.parametrize("season", BAD_SEASON_NAMES)
def test_invalid_season_names_are_rejected(board, season):
    with pytest.raises(ValueError):
        board.start_season(season)
    assert board.get_seasons() == ["default", "spring"]


@pytest.mark.parametrize("season", ["default", "spring"])
def test_a_season_cannot_be_started_twice(board, season):
    with pytest.raises(ScoreError):
        board.start_season(season)
    assert board.get_seasons() == ["default", "spring"]
    assert board.get_current_season() == "spring"


def test_starting_a_season_changes_no_players_or_scores(board):
    board.start_season("summer")
    assert board.get_players() == ["ana", "ben"]
    assert board.get_scores("ana") == [100, 250]
    assert board.get_scores("ana", season="summer") == []
    assert board.get_total_score("ben", season="summer") == 0


def test_without_a_season_every_season_counts(board):
    assert board.get_scores("ana") == [100, 250]
    assert board.get_scores("ana", season=None) == [100, 250]
    assert board.get_total_score("ana") == 350
    assert board.get_top_scores(3) == [400, 250, 100]
    assert board.get_personal_best("ana") == 250
    assert board.get_leaderboard() == [("ben", 400), ("ana", 250)]
    assert board.get_latest_score("ana") == 250
    assert board.get_latest_score("ben") == 400


def test_scores_and_totals_are_filtered_by_season(board):
    assert board.get_scores("ana", season="default") == [100]
    assert board.get_scores("ben", season="spring") == []
    assert board.get_total_score("ana", season="default") == 100
    assert board.get_total_score("ben", season="spring") == 0


def test_top_scores_are_filtered_by_season(board):
    board.record_score("ben", 50)
    assert board.get_top_scores(5, season="default") == [400, 100]
    assert board.get_top_scores(5, season="spring") == [250, 50]
    assert board.get_top_scores(1, season="spring") == [250]


def test_personal_best_is_filtered_by_season(board):
    assert board.get_personal_best("ana", season="default") == 100
    assert board.get_personal_best("ana", season="spring") == 250
    with pytest.raises(ScoreError):
        board.get_personal_best("ben", season="spring")


def test_leaderboard_is_filtered_by_season(board):
    assert board.get_leaderboard(season="default") == [("ben", 400), ("ana", 100)]
    assert board.get_leaderboard(season="spring") == [("ana", 250)]


@pytest.mark.parametrize(
    "call",
    [
        lambda bd: bd.get_scores("ana", season="winter"),
        lambda bd: bd.get_total_score("ana", season="winter"),
        lambda bd: bd.get_top_scores(3, season="winter"),
        lambda bd: bd.get_personal_best("ana", season="winter"),
        lambda bd: bd.get_leaderboard(season="winter"),
        lambda bd: bd.get_scores("ana", season=1),
    ],
)
def test_a_season_never_started_raises_key_error(board, call):
    with pytest.raises(KeyError):
        call(board)


def test_errors_are_reported_in_order(board):
    with pytest.raises(ValueError):
        board.get_top_scores(0, season="winter")
    with pytest.raises(KeyError):
        board.get_scores("dan", season="winter")
