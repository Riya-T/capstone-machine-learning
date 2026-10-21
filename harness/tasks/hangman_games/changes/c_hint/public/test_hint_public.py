"""Public checks for the c_hint change (hints and missing letters). Shown to
the editor, never to the writer.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hint/public/test_hint_public.py
"""

import pytest
from hangman import Hangman, HangmanError


def test_the_hint_is_the_most_common_missing_letter():
    hm = Hangman()
    hm.start_game("first", "banana")
    assert hm.get_hint("first") == "a"
    hm.guess("first", "a")
    assert hm.get_hint("first") == "n"
    hm.guess("first", "n")
    assert hm.get_hint("first") == "b"


def test_the_missing_count_falls_with_each_right_guess():
    hm = Hangman()
    hm.start_game("first", "banana")
    assert hm.get_missing_count("first") == 3
    hm.guess("first", "a")
    assert hm.get_missing_count("first") == 2
    hm.guess("first", "z")
    assert hm.get_missing_count("first") == 2


def test_a_won_game_has_no_hint():
    hm = Hangman()
    hm.start_game("first", "cab")
    for letter in "cab":
        hm.guess("first", letter)
    assert hm.get_missing_count("first") == 0
    with pytest.raises(HangmanError):
        hm.get_hint("first")
