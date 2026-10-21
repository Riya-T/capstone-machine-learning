"""Public checks for the c_max_wrong change (a limit on wrong guesses).
Shown to the editor, never to the writer.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_wrong/public/test_max_wrong_public.py
"""

import pytest
from hangman import Hangman, HangmanError


def test_reaching_the_limit_loses_the_game():
    hm = Hangman()
    hm.start_game("first", "banana", max_wrong=2)
    assert hm.get_max_wrong("first") == 2
    hm.guess("first", "x")
    assert hm.get_guesses_left("first") == 1
    assert hm.guess("first", "y") is False
    assert hm.get_status("first") == "lost"
    assert hm.get_guesses_left("first") == 0


def test_a_lost_game_refuses_further_guesses():
    hm = Hangman()
    hm.start_game("first", "banana", max_wrong=1)
    hm.guess("first", "x")
    with pytest.raises(HangmanError):
        hm.guess("first", "a")
    assert hm.get_guesses("first") == ["x"]


def test_without_a_limit_nothing_changes():
    hm = Hangman()
    hm.start_game("first", "banana")
    assert hm.get_max_wrong("first") is None
    assert hm.get_guesses_left("first") is None
    for letter in "cdefghijklmopqrstuvwxyz":
        hm.guess("first", letter)
    assert hm.get_status("first") == "playing"
