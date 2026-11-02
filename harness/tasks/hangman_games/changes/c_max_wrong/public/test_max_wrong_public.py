"""Public checks for the c_max_wrong change (an optional limit on wrong
guesses, so a game can be lost, and no guesses once a game is over). Shown
to the editor, never to the writer.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_max_wrong/public/test_max_wrong_public.py
"""

import pytest
from hangman import Hangman, HangmanError


def test_reaching_the_games_own_limit_loses_it():
    hm = Hangman()
    hm.start_game("first", "banana", max_wrong=2)
    assert hm.get_max_wrong("first") == 2
    hm.guess("first", "x")
    assert hm.get_guesses_left("first") == 1
    assert hm.guess("first", "y") is False
    assert hm.get_status("first") == "lost"
    assert hm.get_guesses_left("first") == 0


def test_a_game_that_is_over_refuses_further_guesses():
    hm = Hangman()
    hm.start_game("won", "cab")
    for letter in "cab":
        hm.guess("won", letter)
    with pytest.raises(HangmanError):
        hm.guess("won", "z")
    hm.start_game("lost", "cab", max_wrong=1)
    hm.guess("lost", "z")
    with pytest.raises(HangmanError):
        hm.guess("lost", "c")
    assert hm.get_guesses("lost") == ["z"]


def test_without_a_limit_wrong_guesses_never_lose():
    hm = Hangman()
    hm.start_game("free", "banana")
    assert hm.get_max_wrong("free") is None
    assert hm.get_guesses_left("free") is None
    for letter in "cdefghijklmopqrstuvwxyz":
        hm.guess("free", letter)
    assert hm.get_status("free") == "playing"
    assert hm.get_wrong_count("free") == 23
