"""Hidden tests for the c_max_wrong change (a limit on wrong guesses). Never
shown to the writer or the editor.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_wrong/private/test_max_wrong_new.py
"""

import pytest
from hangman import Hangman, HangmanError

BAD_LIMITS = [0, -1, 1.5, "3", True]


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana", max_wrong=3)
    hm.start_game("free", "cab")
    return hm


def state(hm):
    return {
        g: (hm.get_progress(g), hm.get_guesses(g), hm.get_wrong_count(g), hm.get_status(g))
        for g in hm.get_games()
    }


def test_the_limit_and_the_guesses_left_are_reported(games):
    assert games.get_max_wrong("first") == 3
    assert games.get_guesses_left("first") == 3
    games.guess("first", "x")
    assert games.get_guesses_left("first") == 2
    assert games.get_max_wrong("first") == 3


def test_right_guesses_do_not_use_up_the_limit(games):
    for letter in "ban":
        games.guess("first", letter)
    assert games.get_guesses_left("first") == 3
    assert games.get_status("first") == "won"


def test_the_losing_guess_still_counts_as_a_guess(games):
    games.guess("first", "x")
    games.guess("first", "y")
    assert games.get_status("first") == "playing"
    assert games.guess("first", "z") is False
    assert games.get_status("first") == "lost"
    assert games.get_guesses("first") == ["x", "y", "z"]
    assert games.get_wrong_count("first") == 3
    assert games.get_guesses_left("first") == 0


def test_a_lost_game_refuses_guesses_and_changes_nothing(games):
    for letter in "xyz":
        games.guess("first", letter)
    before = state(games)
    with pytest.raises(HangmanError):
        games.guess("first", "a")
    assert state(games) == before
    assert games.get_guesses_left("first") == 0


def test_a_limit_of_one_loses_on_the_first_miss():
    hm = Hangman()
    hm.start_game("sudden", "cab", max_wrong=1)
    hm.guess("sudden", "c")
    hm.guess("sudden", "z")
    assert hm.get_status("sudden") == "lost"
    assert hm.get_progress("sudden") == "c__"


def test_a_game_can_be_won_with_misses_under_the_limit(games):
    for letter in "xyban":
        games.guess("first", letter)
    assert games.get_status("first") == "won"
    assert games.get_guesses_left("first") == 1


def test_games_without_a_limit_report_none_and_never_lose(games):
    assert games.get_max_wrong("free") is None
    assert games.get_guesses_left("free") is None
    for letter in "defghijklmnopqrstuvwxyz":
        games.guess("free", letter)
    assert games.get_status("free") == "playing"
    assert games.get_guesses_left("free") is None


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_and_no_game_starts(games, limit):
    before = state(games)
    with pytest.raises(ValueError):
        games.start_game("third", "apple", max_wrong=limit)
    assert games.get_games() == ["first", "free"]
    assert state(games) == before


def test_a_bad_limit_is_reported_before_a_reused_id(games):
    with pytest.raises(ValueError):
        games.start_game("first", "apple", max_wrong=0)


@pytest.mark.parametrize("method", ["get_max_wrong", "get_guesses_left"])
@pytest.mark.parametrize("game_id", ["third", None, 1])
def test_limit_queries_on_unknown_games_raise_key_error(games, method, game_id):
    with pytest.raises(KeyError):
        getattr(games, method)(game_id)


def test_a_bad_letter_is_reported_before_a_lost_game(games):
    for letter in "xyz":
        games.guess("first", letter)
    with pytest.raises(ValueError):
        games.guess("first", "1")
    with pytest.raises(KeyError):
        games.guess("third", "1")


def test_limits_are_per_game():
    hm = Hangman()
    hm.start_game("short", "cab", max_wrong=1)
    hm.start_game("long", "cab", max_wrong=5)
    hm.guess("short", "x")
    hm.guess("long", "x")
    assert hm.get_status("short") == "lost"
    assert hm.get_status("long") == "playing"
    assert hm.get_guesses_left("long") == 4
