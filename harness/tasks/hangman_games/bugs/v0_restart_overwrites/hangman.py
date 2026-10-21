"""Hangman games: several named games, each with a secret word and the
letters guessed so far.

Planted bug (initial version): start_game with an id that is already in
use silently replaces the old game instead of raising HangmanError. The
public checks never reuse an id, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from hangman import Hangman
    games = Hangman()
    games.start_game("first", "banana")
    games.guess("first", "a")
"""

LETTERS = "abcdefghijklmnopqrstuvwxyz"


class HangmanError(Exception):
    pass


def check_word(word):
    if not isinstance(word, str) or not word or any(c not in LETTERS for c in word):
        raise ValueError(f"word must be a non-empty str of lowercase letters, got {word!r}")


def check_letter(letter):
    if not isinstance(letter, str) or len(letter) != 1 or letter not in LETTERS:
        raise ValueError(f"letter must be a single lowercase letter, got {letter!r}")


class Hangman:
    def __init__(self):
        self._words = {}  # game id -> secret word, in start order
        self._guesses = {}  # game id -> letters guessed, in order

    def start_game(self, game_id, word):
        if not isinstance(game_id, str) or not game_id:
            raise ValueError("game_id must be a non-empty str")
        check_word(word)
        self._words[game_id] = word
        self._guesses[game_id] = []

    def guess(self, game_id, letter):
        self._require(game_id)
        check_letter(letter)
        if self.get_status(game_id) != "playing":
            raise HangmanError(f"game {game_id!r} is over")
        if letter in self._guesses[game_id]:
            raise HangmanError(f"{letter!r} was already guessed in game {game_id!r}")
        self._guesses[game_id].append(letter)
        return letter in self._words[game_id]

    def get_progress(self, game_id):
        self._require(game_id)
        guessed = set(self._guesses[game_id])
        return "".join(c if c in guessed else "_" for c in self._words[game_id])

    def get_guesses(self, game_id):
        self._require(game_id)
        return list(self._guesses[game_id])

    def get_wrong_count(self, game_id):
        self._require(game_id)
        word = self._words[game_id]
        return sum(1 for letter in self._guesses[game_id] if letter not in word)

    def get_status(self, game_id):
        self._require(game_id)
        if set(self._words[game_id]) <= set(self._guesses[game_id]):
            return "won"
        return "playing"

    def get_games(self):
        return list(self._words)

    def _require(self, game_id):
        # Non-str ids are never stored, so they count as "not in use" too.
        if not isinstance(game_id, str) or game_id not in self._words:
            raise KeyError(game_id)
