"""Scoreboard with an adjustable points table.

Correct solution for scoreboard after c_points.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from scoreboard import Scoreboard
    board = Scoreboard(points={"goal": 6, "behind": 1})
    board.add_team("lions")
    board.score("lions", "goal")
    board.set_points("goal", 7)
"""

STANDARD_POINTS = {"try": 5, "conversion": 2, "drop_goal": 3}


class ScoreboardError(Exception):
    pass


def check_kind(kind):
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"kind must be a non-empty str, got {kind!r}")


def check_value(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"points must be an int >= 1, got {value!r}")


class Scoreboard:
    def __init__(self, points=None):
        if points is None:
            points = STANDARD_POINTS
        if not isinstance(points, dict) or not points:
            raise ValueError("points must be a non-empty dict")
        for kind, value in points.items():
            check_kind(kind)
            check_value(value)
        self._points = dict(points)  # kind -> points, in table order
        self._events = {}  # team name -> list of (kind, points), in adding order

    def add_team(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("team name must be a non-empty str")
        if name in self._events:
            raise ScoreboardError(f"team {name!r} was already added")
        self._events[name] = []

    def score(self, team, kind):
        self._require(team)
        points = self.get_points(kind)
        self._events[team].append((kind, points))

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

    def get_points(self, kind):
        if not isinstance(kind, str) or kind not in self._points:
            raise ValueError(f"unknown kind of score: {kind!r}")
        return self._points[kind]

    def get_kinds(self):
        return list(self._points)

    def set_points(self, kind, value):
        check_kind(kind)
        check_value(value)
        self._points[kind] = value

    def _require(self, team):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(team, str) or team not in self._events:
            raise KeyError(team)
