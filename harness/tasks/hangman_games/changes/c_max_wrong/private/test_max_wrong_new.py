"""Hidden tests for the c_max_wrong change (an optional limit on wrong
guesses, so a game can be lost, and no guesses once a game is over). Never
shown to the writer or the editor.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_wrong/private/test_max_wrong_new.py
"""

import pytest
from hangman import Hangman, HangmanError

BAD_LIMITS = [0, -1, 2.5, "3"]


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana", max_wrong=3)
    hm.start_game("free", "cab", max_wrong=None)
    hm.start_game("plain", "cab")
    return hm


def state(hm):
    return {
        g: (hm.get_progress(g), hm.get_guesses(g), hm.get_wrong_count(g), hm.get_status(g))
        for g in hm.get_games()
    }


# --- limits -----------------------------------------------------------------


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


def test_a_limit_of_one_loses_on_the_first_miss():
    hm = Hangman()
    hm.start_game("sudden", "cab", max_wrong=1)
    hm.guess("sudden", "c")
    hm.guess("sudden", "z")
    assert hm.get_status("sudden") == "lost"
    assert hm.get_progress("sudden") == "c__"


def test_a_limit_above_six_outlasts_six_misses():
    hm = Hangman()
    hm.start_game("long", "cab", max_wrong=8)
    for letter in "tuvwxyz":
        hm.guess("long", letter)
    assert hm.get_status("long") == "playing"
    assert hm.get_guesses_left("long") == 1
    hm.guess("long", "s")
    assert hm.get_status("long") == "lost"


def test_a_game_can_be_won_with_misses_under_the_limit(games):
    for letter in "xyban":
        games.guess("first", letter)
    assert games.get_status("first") == "won"
    assert games.get_guesses_left("first") == 1


@pytest.mark.parametrize("game_id", ["plain", "free"])
def test_games_without_a_limit_report_none_and_never_lose(games, game_id):
    assert games.get_max_wrong(game_id) is None
    assert games.get_guesses_left(game_id) is None
    for letter in "defghijklmnopqrstuvwxyz":
        assert games.guess(game_id, letter) is False
    assert games.get_status(game_id) == "playing"
    assert games.get_wrong_count(game_id) == 23
    assert games.get_guesses_left(game_id) is None
    games.guess(game_id, "c")
    games.guess(game_id, "a")
    games.guess(game_id, "b")
    assert games.get_status(game_id) == "won"


def test_a_limit_of_six_loses_at_the_sixth_miss():
    hm = Hangman()
    hm.start_game("six", "cab", max_wrong=6)
    for letter in "uvwxy":
        hm.guess("six", letter)
    hm.guess("six", "a")
    assert hm.get_status("six") == "playing"
    assert hm.get_guesses_left("six") == 1
    hm.guess("six", "z")
    assert hm.get_status("six") == "lost"
    assert hm.get_guesses_left("six") == 0
    assert hm.get_progress("six") == "_a_"


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_and_no_game_starts(games, limit):
    before = state(games)
    with pytest.raises(ValueError):
        games.start_game("third", "apple", max_wrong=limit)
    assert games.get_games() == ["first", "free", "plain"]
    assert state(games) == before


@pytest.mark.parametrize("method", ["get_max_wrong", "get_guesses_left"])
@pytest.mark.parametrize("game_id", ["third", None, 1])
def test_limit_queries_on_unknown_games_raise_key_error(games, method, game_id):
    with pytest.raises(KeyError):
        getattr(games, method)(game_id)


def test_limits_are_per_game():
    hm = Hangman()
    hm.start_game("short", "cab", max_wrong=1)
    hm.start_game("long", "cab", max_wrong=5)
    hm.guess("short", "x")
    hm.guess("long", "x")
    assert hm.get_status("short") == "lost"
    assert hm.get_status("long") == "playing"
    assert hm.get_guesses_left("long") == 4


# --- games that are over ----------------------------------------------------


@pytest.mark.parametrize("letter", ["z", "c", "q"])
def test_a_won_game_refuses_every_guess_and_changes_nothing(games, letter):
    for right in "cab":
        games.guess("plain", right)
    games.guess("first", "x")
    before = state(games)
    with pytest.raises(HangmanError):
        games.guess("plain", letter)
    assert state(games) == before


@pytest.mark.parametrize("letter", ["a", "b", "q"])
def test_a_lost_game_refuses_every_guess_and_changes_nothing(games, letter):
    for wrong in "xyz":
        games.guess("first", wrong)
    before = state(games)
    with pytest.raises(HangmanError):
        games.guess("first", letter)
    assert state(games) == before
    assert games.get_guesses_left("first") == 0


def test_a_won_game_with_a_limit_refuses_guesses(games):
    for letter in "xban":
        games.guess("first", letter)
    assert games.get_status("first") == "won"
    with pytest.raises(HangmanError):
        games.guess("first", "q")
    assert games.get_wrong_count("first") == 1
    assert games.get_guesses_left("first") == 2


def test_a_one_letter_word_is_over_after_one_guess():
    hm = Hangman()
    hm.start_game("tiny", "q")
    hm.guess("tiny", "q")
    with pytest.raises(HangmanError):
        hm.guess("tiny", "a")
    assert hm.get_guesses("tiny") == ["q"]


def test_one_game_ending_does_not_stop_another(games):
    for right in "cab":
        games.guess("plain", right)
    for wrong in "xyz":
        games.guess("first", wrong)
    assert games.guess("free", "c") is True
    assert games.get_status("free") == "playing"
