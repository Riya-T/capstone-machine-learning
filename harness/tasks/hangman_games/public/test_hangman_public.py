"""Public checks for hangman.py.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest public/test_hangman_public.py
"""

import pytest
from hangman import Hangman, HangmanError


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana")
    return hm


def test_a_right_guess_reveals_every_occurrence(games):
    assert games.guess("first", "a") is True
    assert games.get_progress("first") == "_a_a_a"
    assert games.get_wrong_count("first") == 0


def test_a_wrong_guess_is_counted(games):
    assert games.guess("first", "z") is False
    assert games.get_progress("first") == "______"
    assert games.get_guesses("first") == ["z"]
    assert games.get_wrong_count("first") == 1


def test_the_game_is_won_when_every_letter_is_found(games):
    for letter in "ban":
        games.guess("first", letter)
    assert games.get_progress("first") == "banana"
    assert games.get_status("first") == "won"
    with pytest.raises(HangmanError):
        games.guess("first", "z")


def test_games_are_listed_in_the_order_started(games):
    games.start_game("second", "apple")
    assert games.get_games() == ["first", "second"]
    assert games.get_status("second") == "playing"


def test_letters_must_be_one_lowercase_letter(games):
    for bad in ["A", "ab", ""]:
        with pytest.raises(ValueError):
            games.guess("first", bad)
    assert games.get_guesses("first") == []


def test_unknown_game_raises_key_error(games):
    with pytest.raises(KeyError):
        games.get_progress("third")
