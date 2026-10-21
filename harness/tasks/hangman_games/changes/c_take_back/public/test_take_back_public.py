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


def test_taking_back_a_right_guess_hides_the_letter_again():
    hm = Hangman()
    hm.start_game("first", "banana")
    hm.guess("first", "b")
    hm.guess("first", "a")
    assert hm.take_back("first") == "a"
    assert hm.get_progress("first") == "b_____"
    assert hm.get_guesses("first") == ["b"]


def test_nothing_to_take_back_raises():
    hm = Hangman()
    hm.start_game("first", "banana")
    with pytest.raises(HangmanError):
        hm.take_back("first")
