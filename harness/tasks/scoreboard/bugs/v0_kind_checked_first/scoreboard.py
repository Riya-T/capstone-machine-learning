"""Scoreboard: the score of one match, built from each team's scoring events.

Planted bug (initial version): score checks the kind before the team, so a
bad kind for an unknown team raises ValueError instead of KeyError.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from scoreboard import Scoreboard
    board = Scoreboard()
    board.add_team("lions")
    board.score("lions", "try")
"""

POINTS = {"try": 5, "conversion": 2, "drop_goal": 3}


class ScoreboardError(Exception):
    pass


class Scoreboard:
    def __init__(self):
        self._events = {}  # team name -> list of (kind, points), in adding order

    def add_team(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("team name must be a non-empty str")
        if name in self._events:
            raise ScoreboardError(f"team {name!r} was already added")
        self._events[name] = []

    def score(self, team, kind):
        if not isinstance(kind, str) or kind not in POINTS:
            raise ValueError(f"unknown kind of score: {kind!r}")
        self._require(team)
        self._events[team].append((kind, POINTS[kind]))

    def get_score(self, team):
        self._require(team)
        return sum(points for _, points in self._events[team])

    def get_events(self, team):
        self._require(team)
        return list(self._events[team])

    def get_standings(self):
        # sorted() is stable, so equal scores keep the order teams were added.
        return sorted(self._events, key=lambda team: -self.get_score(team))

    def get_teams(self):
        return list(self._events)

    def _require(self, team):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(team, str) or team not in self._events:
            raise KeyError(team)
