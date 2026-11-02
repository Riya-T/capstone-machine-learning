"""Public checks for hangman.py.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest public/test_hangman_public.py
"""

import pytest
from hangman import Hangman


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana")
    return hm


def test_a_right_guess_reveals_every_occurrence(games):
    assert games.guess("first", "a") is True
    assert games.get_progress("first") == "_a_a_a"
    assert games.get_wrong_count("first") == 0


def test_guesses_are_listed_alphabetically_and_misses_counted(games):
    assert games.guess("first", "z") is False
    assert games.guess("first", "b") is True
    assert games.guess("first", "x") is False
    assert games.get_progress("first") == "b_____"
    assert games.get_guesses("first") == ["b", "x", "z"]
    assert games.get_wrong_count("first") == 2


def test_the_game_is_won_when_every_letter_is_found(games):
    games.guess("first", "b")
    games.guess("first", "a")
    assert games.get_status("first") == "playing"
    assert games.guess("first", "n") is True
    assert games.get_progress("first") == "banana"
    assert games.get_status("first") == "won"


def test_a_game_is_still_won_after_wrong_guesses():
    hm = Hangman()
    hm.start_game("short", "cab")
    for letter in "defgh":
        assert hm.guess("short", letter) is False
    assert hm.get_status("short") == "playing"
    assert hm.get_wrong_count("short") == 5
    for letter in "cab":
        assert hm.guess("short", letter) is True
    assert hm.get_status("short") == "won"
    assert hm.get_wrong_count("short") == 5


def test_games_are_listed_in_the_order_started(games):
    games.start_game("second", "apple")
    assert games.get_games() == ["first", "second"]
    assert games.get_status("second") == "playing"
    with pytest.raises(KeyError):
        games.get_progress("third")


def test_letters_must_be_one_lowercase_letter(games):
    for bad in ["A", "ab", ""]:
        with pytest.raises(ValueError):
            games.guess("first", bad)
    assert games.get_guesses("first") == []
