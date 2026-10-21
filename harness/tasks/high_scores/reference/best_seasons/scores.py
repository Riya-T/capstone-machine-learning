"""High scores with personal bests, a leaderboard and seasons.

Correct solution for high_scores after c_best and c_seasons.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from scores import ScoreBoard
    board = ScoreBoard()
    board.add_player("ana")
    board.record_score("ana", 300)
    board.start_season("spring")
    board.get_personal_best("ana", season="default")  # 300
"""

FIRST_SEASON = "default"


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
        self._seasons = [FIRST_SEASON]  # in the order started; the last is current
        self._entries = []  # (name, score, season) in the order recorded

    def add_player(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._players:
            raise ScoreError(f"player {name!r} is already on the board")
        self._players.append(name)

    def record_score(self, name, score):
        self._require(name)
        check_score(score)
        self._entries.append((name, score, self.get_current_season()))

    def start_season(self, season):
        if not isinstance(season, str) or not season:
            raise ValueError("season must be a non-empty str")
        if season in self._seasons:
            raise ScoreError(f"season {season!r} was already started")
        self._seasons.append(season)

    def get_players(self):
        return list(self._players)

    def get_seasons(self):
        return list(self._seasons)

    def get_current_season(self):
        return self._seasons[-1]

    def get_scores(self, name, season=None):
        self._require(name)
        self._require_season(season)
        return self._scores(name, season)

    def get_latest_score(self, name):
        scores = self.get_scores(name)
        if not scores:
            raise ScoreError(f"player {name!r} has no scores")
        return scores[-1]

    def get_total_score(self, name, season=None):
        return sum(self.get_scores(name, season))

    def get_top_scores(self, n, season=None):
        check_count(n)
        self._require_season(season)
        scores = [s for _, s, ssn in self._entries if season is None or ssn == season]
        return sorted(scores, reverse=True)[:n]

    def get_personal_best(self, name, season=None):
        scores = self.get_scores(name, season)
        if not scores:
            raise ScoreError(f"player {name!r} has no scores")
        return max(scores)

    def get_personal_best_count(self, name):
        count = 0
        best = None
        for score in self.get_scores(name):
            if best is None or score > best:
                best = score
                count += 1
        return count

    def get_leaderboard(self, season=None):
        self._require_season(season)
        bests = []
        for name in self._players:
            scores = self._scores(name, season)
            if scores:
                bests.append((name, max(scores)))
        return sorted(bests, key=lambda pair: -pair[1])  # stable: ties keep the added order

    def _scores(self, name, season):
        return [
            score
            for player, score, ssn in self._entries
            if player == name and (season is None or ssn == season)
        ]

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._players:
            raise KeyError(name)

    def _require_season(self, season):
        if season is not None and (not isinstance(season, str) or season not in self._seasons):
            raise KeyError(season)
