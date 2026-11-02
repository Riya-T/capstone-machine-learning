"""Hidden tests for the c_hint change (hints and missing letters). Never shown
to the writer or the editor.

Games without a limit never get 6 or more wrong guesses here, so the s1
regression bug hint_no_limit_lost_at_six passes these tests and only the
c_max_wrong tests catch it.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hint/private/test_hint_new.py
"""

import pytest
from hangman import Hangman, HangmanError


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana")
    hm.start_game("second", "cab")
    return hm


def state(hm):
    return {
        g: (hm.get_progress(g), hm.get_guesses(g), hm.get_wrong_count(g), hm.get_status(g))
        for g in hm.get_games()
    }


def test_ties_go_to_the_letter_that_appears_first(games):
    assert games.get_hint("second") == "c"
    games.guess("second", "c")
    assert games.get_hint("second") == "a"
    games.guess("second", "a")
    assert games.get_hint("second") == "b"


def test_a_later_frequent_letter_beats_an_earlier_rare_one():
    hm = Hangman()
    hm.start_game("word", "xaabbb")
    assert hm.get_hint("word") == "b"
    hm.guess("word", "b")
    assert hm.get_hint("word") == "a"
    hm.guess("word", "a")
    assert hm.get_hint("word") == "x"


def test_wrong_guesses_do_not_change_the_hint(games):
    for letter in "xyz":
        games.guess("first", letter)
    assert games.get_hint("first") == "a"
    assert games.get_missing_count("first") == 3


def test_the_hint_skips_letters_already_guessed(games):
    games.guess("first", "n")
    assert games.get_hint("first") == "a"
    games.guess("first", "a")
    assert games.get_hint("first") == "b"


def test_hint_queries_change_nothing(games):
    games.guess("first", "x")
    before = state(games)
    for _ in range(3):
        assert games.get_hint("first") == "a"
        assert games.get_missing_count("first") == 3
    assert state(games) == before


def test_a_won_game_has_no_hint_and_nothing_missing(games):
    for letter in "cab":
        games.guess("second", letter)
    assert games.get_missing_count("second") == 0
    before = state(games)
    with pytest.raises(HangmanError):
        games.get_hint("second")
    assert state(games) == before


def test_a_lost_game_has_no_hint_but_letters_still_missing(games):
    games.start_game("doomed", "banana", max_wrong=2)
    games.guess("doomed", "a")
    games.guess("doomed", "y")
    games.guess("doomed", "z")
    assert games.get_status("doomed") == "lost"
    assert games.get_missing_count("doomed") == 2
    before = state(games)
    with pytest.raises(HangmanError):
        games.get_hint("doomed")
    assert state(games) == before


def test_a_game_one_miss_from_losing_still_gets_a_hint(games):
    games.start_game("close", "banana", max_wrong=2)
    games.guess("close", "z")
    assert games.get_status("close") == "playing"
    assert games.get_hint("close") == "a"


def test_a_game_without_a_limit_gets_hints_after_many_misses(games):
    for letter in "vwxyz":
        games.guess("first", letter)
    assert games.get_status("first") == "playing"
    assert games.get_hint("first") == "a"
    assert games.get_missing_count("first") == 3


def test_missing_count_counts_different_letters_once():
    hm = Hangman()
    hm.start_game("repeat", "aaaa")
    assert hm.get_missing_count("repeat") == 1
    hm.start_game("mixed", "abcabc")
    assert hm.get_missing_count("mixed") == 3


@pytest.mark.parametrize("method", ["get_hint", "get_missing_count"])
@pytest.mark.parametrize("game_id", ["third", None, 1])
def test_hint_queries_on_unknown_games_raise_key_error(games, method, game_id):
    with pytest.raises(KeyError):
        getattr(games, method)(game_id)


def test_hints_are_per_game(games):
    games.guess("first", "a")
    assert games.get_hint("first") == "n"
    assert games.get_hint("second") == "c"
    assert games.get_missing_count("second") == 3
