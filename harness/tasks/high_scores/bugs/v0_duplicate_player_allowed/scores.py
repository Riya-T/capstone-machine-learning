"""High scores: players and the scores they recorded, with a top-N list.

Planted bug (initial version): add_player never checks whether the name is
already on the board, so adding a player twice lists them twice instead of
raising ScoreError. The public checks never add a name twice, so only the
hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from scores import ScoreBoard
    board = ScoreBoard()
    board.add_player("ana")
    board.record_score("ana", 300)
"""


class ScoreError(Exception):
    pass


def check_score(score):
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError(f"score must be an int >= 0, got {score!r}")


def check_count(n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be an int >= 1, got {n!r}")


class ScoreBoard:
    def __init__(self):
        self._players = []  # names in the order added
        self._entries = []  # (name, score) in the order recorded

    def add_player(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        self._players.append(name)

    def record_score(self, name, score):
        self._require(name)
        check_score(score)
        self._entries.append((name, score))

    def get_players(self):
        return list(self._players)

    def get_scores(self, name):
        self._require(name)
        return [score for player, score in self._entries if player == name]

    def get_latest_score(self, name):
        scores = self.get_scores(name)
        if not scores:
            raise ScoreError(f"player {name!r} has no scores")
        return scores[-1]

    def get_total_score(self, name):
        return sum(self.get_scores(name))

    def get_top_scores(self, n):
        check_count(n)
        return sorted((score for _, score in self._entries), reverse=True)[:n]

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._players:
            raise KeyError(name)
