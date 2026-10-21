"""Hangman games with a limit on wrong guesses and hints.

Planted bug (after c_max_wrong and c_hint): hints were added correctly,
but while reworking guess the check that refuses a letter already guessed
was lost, so a repeated guess is accepted and counted again.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from hangman import Hangman
    games = Hangman()
    games.start_game("first", "banana", max_wrong=6)
    games.guess("first", "a")
    games.get_hint("first")
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


def check_limit(limit):
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"max_wrong must be None or an int >= 1, got {limit!r}")


class Hangman:
    def __init__(self):
        self._words = {}  # game id -> secret word, in start order
        self._guesses = {}  # game id -> letters guessed, in order
        self._limits = {}  # game id -> max wrong guesses, or None

    def start_game(self, game_id, word, max_wrong=None):
        if not isinstance(game_id, str) or not game_id:
            raise ValueError("game_id must be a non-empty str")
        check_word(word)
        check_limit(max_wrong)
        if game_id in self._words:
            raise HangmanError(f"game {game_id!r} is already in use")
        self._words[game_id] = word
        self._guesses[game_id] = []
        self._limits[game_id] = max_wrong

    def guess(self, game_id, letter):
        self._require(game_id)
        check_letter(letter)
        if self.get_status(game_id) != "playing":
            raise HangmanError(f"game {game_id!r} is over")
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
        limit = self._limits[game_id]
        if limit is not None and self.get_wrong_count(game_id) >= limit:
            return "lost"
        return "playing"

    def get_games(self):
        return list(self._words)

    def get_max_wrong(self, game_id):
        self._require(game_id)
        return self._limits[game_id]

    def get_guesses_left(self, game_id):
        self._require(game_id)
        limit = self._limits[game_id]
        if limit is None:
            return None
        return limit - self.get_wrong_count(game_id)

    def get_hint(self, game_id):
        self._require(game_id)
        if self.get_status(game_id) != "playing":
            raise HangmanError(f"game {game_id!r} is over, nothing to hint at")
        word, guessed = self._words[game_id], set(self._guesses[game_id])
        missing = [c for c in word if c not in guessed]
        # max() keeps the first of equally common letters, i.e. the earliest in the word.
        return max(dict.fromkeys(missing), key=missing.count)

    def get_missing_count(self, game_id):
        self._require(game_id)
        return len(set(self._words[game_id]) - set(self._guesses[game_id]))

    def _require(self, game_id):
        # Non-str ids are never stored, so they count as "not in use" too.
        if not isinstance(game_id, str) or game_id not in self._words:
            raise KeyError(game_id)
