"""Hidden tests for the c_take_back change (taking back a guess). Never shown
to the writer or the editor.

c_take_back comes before c_max_wrong in s2, when losing is still
unspecified, so no game here gets 6 or more wrong guesses. No test guesses
in a won game unless take_back has reopened it first: c_max_wrong (step 2
of s2) makes that an error.

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


# --- what is taken back -----------------------------------------------------


def test_take_back_returns_the_newest_letter_not_the_last_alphabetically(games):
    games.guess("first", "z")
    games.guess("first", "b")
    assert games.take_back("first") == "b"
    assert games.take_back("first") == "z"


def test_guesses_are_taken_back_newest_first(games):
    for letter in "bxa":
        games.guess("first", letter)
    assert games.take_back("first") == "a"
    assert games.get_guesses("first") == ["b", "x"]
    assert games.get_progress("first") == "b_____"
    assert games.get_wrong_count("first") == 1
    assert games.take_back("first") == "x"
    assert games.get_guesses("first") == ["b"]
    assert games.get_wrong_count("first") == 0


def test_guesses_made_after_a_take_back_are_newer(games):
    games.guess("first", "n")
    games.guess("first", "z")
    games.take_back("first")
    games.guess("first", "b")
    games.guess("first", "y")
    assert games.take_back("first") == "y"
    assert games.take_back("first") == "b"
    assert games.take_back("first") == "n"
    assert games.get_guesses("first") == []


def test_taking_back_a_right_guess_keeps_the_wrong_count(games):
    games.guess("first", "z")
    games.guess("first", "a")
    assert games.take_back("first") == "a"
    assert games.get_wrong_count("first") == 1
    assert games.get_progress("first") == "______"


def test_taking_back_every_guess_restores_the_start(games):
    before = state(games)
    for letter in "zan":
        games.guess("first", letter)
    for _ in range(3):
        games.take_back("first")
    assert state(games) == before


def test_taking_back_a_repeated_letter_hides_every_occurrence(games):
    games.guess("first", "n")
    games.guess("first", "a")
    games.take_back("first")
    assert games.get_progress("first") == "__n_n_"


def test_a_taken_back_letter_may_be_guessed_again(games):
    games.guess("first", "a")
    games.take_back("first")
    assert games.guess("first", "a") is True
    assert games.get_guesses("first") == ["a"]
    assert games.get_progress("first") == "_a_a_a"


# --- games that were won ----------------------------------------------------


def test_taking_back_the_winning_guess_reopens_the_game(games):
    for letter in "cab":
        games.guess("second", letter)
    assert games.get_status("second") == "won"
    assert games.take_back("second") == "b"
    assert games.get_status("second") == "playing"
    assert games.get_progress("second") == "ca_"


def test_a_game_reopened_after_a_win_accepts_guesses_again(games):
    for letter in "cab":
        games.guess("second", letter)
    games.take_back("second")
    assert games.guess("second", "z") is False
    assert games.guess("second", "b") is True
    assert games.get_status("second") == "won"
    assert games.get_guesses("second") == ["a", "b", "c", "z"]


def test_a_win_after_misses_is_undone_newest_first(games):
    for letter in "xycab":
        games.guess("second", letter)
    assert games.get_status("second") == "won"
    assert games.take_back("second") == "b"
    assert games.get_status("second") == "playing"
    assert games.get_wrong_count("second") == 2
    assert games.take_back("second") == "a"
    assert games.get_progress("second") == "c__"
    assert games.get_guesses("second") == ["c", "x", "y"]


def test_a_one_letter_word_can_be_won_again_after_a_take_back():
    hm = Hangman()
    hm.start_game("tiny", "q")
    hm.guess("tiny", "q")
    assert hm.take_back("tiny") == "q"
    assert hm.get_status("tiny") == "playing"
    assert hm.get_progress("tiny") == "_"
    assert hm.guess("tiny", "q") is True
    assert hm.get_status("tiny") == "won"


# --- errors -----------------------------------------------------------------


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
