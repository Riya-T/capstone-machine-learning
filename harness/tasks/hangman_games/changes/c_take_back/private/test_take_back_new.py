"""Hidden tests for the c_take_back change (taking back a guess). Never shown
to the writer or the editor.

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest changes/c_take_back/private/test_take_back_new.py
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


def test_take_back_returns_the_newest_letter(games):
    games.guess("first", "b")
    games.guess("first", "x")
    assert games.take_back("first") == "x"
    assert games.take_back("first") == "b"


def test_guesses_are_taken_back_newest_first(games):
    for letter in "bxa":
        games.guess("first", letter)
    games.take_back("first")
    assert games.get_guesses("first") == ["b", "x"]
    assert games.get_progress("first") == "b_____"
    assert games.get_wrong_count("first") == 1
    games.take_back("first")
    assert games.get_guesses("first") == ["b"]
    assert games.get_wrong_count("first") == 0


def test_taking_back_every_guess_restores_the_start(games):
    before = state(games)
    for letter in "zan":
        games.guess("first", letter)
    for _ in range(3):
        games.take_back("first")
    assert state(games) == before


def test_taking_back_the_winning_guess_reopens_the_game(games):
    for letter in "cab":
        games.guess("second", letter)
    assert games.get_status("second") == "won"
    assert games.take_back("second") == "b"
    assert games.get_status("second") == "playing"
    assert games.get_progress("second") == "ca_"


def test_a_reopened_game_accepts_guesses_again(games):
    for letter in "cab":
        games.guess("second", letter)
    games.take_back("second")
    assert games.guess("second", "z") is False
    assert games.guess("second", "b") is True
    assert games.get_status("second") == "won"
    assert games.get_guesses("second") == ["c", "a", "z", "b"]


def test_a_taken_back_letter_may_be_guessed_again(games):
    games.guess("first", "a")
    games.take_back("first")
    assert games.guess("first", "a") is True
    assert games.get_guesses("first") == ["a"]
    assert games.get_progress("first") == "_a_a_a"


def test_taking_back_a_repeated_letter_hides_every_occurrence(games):
    games.guess("first", "n")
    games.guess("first", "a")
    games.take_back("first")
    assert games.get_progress("first") == "__n_n_"


@pytest.mark.parametrize("game_id", ["third", None, 1])
def test_take_back_on_an_unknown_game_raises_key_error(games, game_id):
    games.guess("first", "a")
    before = state(games)
    with pytest.raises(KeyError):
        games.take_back(game_id)
    assert state(games) == before


def test_take_back_with_no_guesses_changes_nothing(games):
    games.guess("first", "a")
    before = state(games)
    with pytest.raises(HangmanError):
        games.take_back("second")
    assert state(games) == before
    games.take_back("first")
    with pytest.raises(HangmanError):
        games.take_back("first")


def test_take_back_only_touches_the_named_game(games):
    games.guess("first", "a")
    games.guess("second", "z")
    games.take_back("second")
    assert games.get_guesses("first") == ["a"]
    assert games.get_guesses("second") == []
    assert games.get_wrong_count("second") == 0
