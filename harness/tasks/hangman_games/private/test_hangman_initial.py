"""Hidden tests for the initial hangman_games spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

The initial spec says nothing about losing, so no test here makes 6 or more
wrong guesses in one game: programs with and without the classic hangman
loss at 6 both pass. No test guesses in a game that is already won either:
that is unspecified too (c_max_wrong later adds losing and makes guessing
in a finished game an error).

Usage (with hangman.py importable, e.g. in the sandbox):
    python -m pytest private/test_hangman_initial.py
"""

import pytest
from hangman import Hangman, HangmanError

BAD_LETTERS = ["", "A", "ab", "1", "-", " ", None]
BAD_WORDS = ["", "Banana", "ban ana", "ban-ana", "abc1", None]


@pytest.fixture
def games():
    hm = Hangman()
    hm.start_game("first", "banana")
    hm.start_game("second", "cab")
    return hm


def state(hm):
    """Everything readable about every game, to check that a failed call changed nothing."""
    return {
        g: (hm.get_progress(g), hm.get_guesses(g), hm.get_wrong_count(g), hm.get_status(g))
        for g in hm.get_games()
    }


# --- games ------------------------------------------------------------------


def test_a_new_game_is_fully_hidden(games):
    assert games.get_progress("first") == "______"
    assert games.get_guesses("first") == []
    assert games.get_wrong_count("first") == 0
    assert games.get_status("first") == "playing"


def test_games_are_listed_in_the_order_started():
    hm = Hangman()
    for name in ["zeta", "alpha", "mid"]:
        hm.start_game(name, "word")
    assert hm.get_games() == ["zeta", "alpha", "mid"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_game_ids_are_rejected(bad_id):
    hm = Hangman()
    with pytest.raises(ValueError):
        hm.start_game(bad_id, "word")
    assert hm.get_games() == []


@pytest.mark.parametrize("word", BAD_WORDS)
def test_invalid_words_are_rejected(games, word):
    before = state(games)
    with pytest.raises(ValueError):
        games.start_game("third", word)
    assert games.get_games() == ["first", "second"]
    assert state(games) == before


def test_reusing_a_game_id_is_rejected(games):
    games.guess("first", "a")
    before = state(games)
    with pytest.raises(HangmanError):
        games.start_game("first", "apple")
    assert state(games) == before
    assert games.get_games() == ["first", "second"]


@pytest.mark.parametrize(
    "call",
    [
        lambda hm: hm.guess("third", "a"),
        lambda hm: hm.get_progress("third"),
        lambda hm: hm.get_guesses("third"),
        lambda hm: hm.get_wrong_count("third"),
        lambda hm: hm.get_status("third"),
        lambda hm: hm.get_progress(None),
        lambda hm: hm.get_progress(1),
        lambda hm: hm.guess(None, "a"),
    ],
)
def test_game_ids_not_in_use_raise_key_error(games, call):
    games.guess("first", "a")
    before = state(games)
    with pytest.raises(KeyError):
        call(games)
    assert state(games) == before


# --- guessing ---------------------------------------------------------------


def test_guess_reports_whether_the_letter_is_in_the_word(games):
    assert games.guess("first", "b") is True
    assert games.guess("first", "x") is False
    assert games.guess("first", "n") is True


def test_progress_shows_every_occurrence_of_a_guessed_letter(games):
    games.guess("first", "n")
    assert games.get_progress("first") == "__n_n_"
    games.guess("first", "b")
    assert games.get_progress("first") == "b_n_n_"


def test_guesses_are_listed_in_alphabetical_order(games):
    for letter in "zban":
        games.guess("first", letter)
    assert games.get_guesses("first") == ["a", "b", "n", "z"]


def test_wrong_count_counts_only_misses(games):
    for letter in "xbyz":
        games.guess("first", letter)
    assert games.get_wrong_count("first") == 3
    assert games.get_progress("first") == "b_____"


@pytest.mark.parametrize("letter", BAD_LETTERS)
def test_invalid_letters_are_rejected(games, letter):
    games.guess("first", "a")
    before = state(games)
    with pytest.raises(ValueError):
        games.guess("first", letter)
    assert state(games) == before


@pytest.mark.parametrize("letter", ["a", "z"])
def test_repeating_a_guess_is_rejected(games, letter):
    games.guess("first", letter)
    before = state(games)
    with pytest.raises(HangmanError):
        games.guess("first", letter)
    assert state(games) == before


# --- winning ----------------------------------------------------------------


def test_the_game_is_won_once_every_letter_is_guessed(games):
    for letter in "bza":
        games.guess("first", letter)
    assert games.get_status("first") == "playing"
    assert games.guess("first", "n") is True
    assert games.get_status("first") == "won"
    assert games.get_progress("first") == "banana"
    assert games.get_wrong_count("first") == 1
    assert games.get_guesses("first") == ["a", "b", "n", "z"]


def test_a_one_letter_word_is_won_in_one_guess():
    hm = Hangman()
    hm.start_game("tiny", "q")
    assert hm.get_progress("tiny") == "_"
    assert hm.guess("tiny", "q") is True
    assert hm.get_status("tiny") == "won"


def test_five_wrong_guesses_leave_the_game_playing(games):
    for letter in "vwxyz":
        assert games.guess("second", letter) is False
    assert games.get_status("second") == "playing"
    assert games.get_wrong_count("second") == 5
    assert games.get_guesses("second") == ["v", "w", "x", "y", "z"]
    assert games.get_progress("second") == "___"


def test_a_game_can_be_won_after_five_wrong_guesses(games):
    for letter in "vwxyz":
        games.guess("second", letter)
    games.guess("second", "c")
    games.guess("second", "a")
    assert games.get_status("second") == "playing"
    games.guess("second", "b")
    assert games.get_status("second") == "won"
    assert games.get_wrong_count("second") == 5
    assert games.get_progress("second") == "cab"


def test_wrong_guesses_in_one_game_do_not_affect_another(games):
    for letter in "vwxyz":
        games.guess("second", letter)
    for letter in "uvwxy":
        games.guess("first", letter)
    assert games.get_wrong_count("first") == 5
    assert games.get_status("first") == "playing"
    for letter in "ban":
        games.guess("first", letter)
    assert games.get_status("first") == "won"


def test_winning_one_game_does_not_end_another(games):
    for letter in "cab":
        games.guess("second", letter)
    assert games.get_status("second") == "won"
    assert games.get_status("first") == "playing"
    assert games.guess("first", "b") is True


# --- separate games ---------------------------------------------------------


def test_games_do_not_share_guesses(games):
    games.guess("first", "a")
    games.guess("second", "z")
    assert games.get_guesses("second") == ["z"]
    assert games.get_progress("second") == "___"
    assert games.get_wrong_count("first") == 0
    assert games.guess("second", "a") is True


def test_instances_do_not_share_games():
    first, second = Hangman(), Hangman()
    first.start_game("only", "word")
    assert second.get_games() == []
    second.start_game("only", "other")
    assert second.get_progress("only") == "_____"
