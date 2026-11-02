"""Public checks for the c_take_back change (taking back a guess). Shown to
the editor, never to the writer.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_back/public/test_take_back_public.py
"""

import pytest
from hangman import Hangman, HangmanError


def test_taking_back_a_wrong_guess_forgets_it():
    hm = Hangman()
    hm.start_game("first", "banana")
    hm.guess("first", "z")
    assert hm.take_back("first") == "z"
    assert hm.get_guesses("first") == []
    assert hm.get_wrong_count("first") == 0


def test_the_newest_guess_is_taken_back_first():
    hm = Hangman()
    hm.start_game("first", "banana")
    hm.guess("first", "n")
    hm.guess("first", "z")
    hm.guess("first", "b")
    assert hm.take_back("first") == "b"
    assert hm.get_progress("first") == "__n_n_"
    assert hm.get_guesses("first") == ["n", "z"]
    assert hm.take_back("first") == "z"
    assert hm.take_back("first") == "n"


def test_taking_back_the_winning_guess_reopens_the_game():
    hm = Hangman()
    hm.start_game("first", "cab")
    for letter in "cab":
        hm.guess("first", letter)
    assert hm.take_back("first") == "b"
    assert hm.get_status("first") == "playing"
    assert hm.get_progress("first") == "ca_"


def test_nothing_to_take_back_raises():
    hm = Hangman()
    hm.start_game("first", "banana")
    with pytest.raises(HangmanError):
        hm.take_back("first")
