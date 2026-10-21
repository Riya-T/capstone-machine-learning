"""Scoreboard with an adjustable points table, corrections and periods.

Correct solution for scoreboard after c_points, c_corrections and c_periods.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from scoreboard import Scoreboard
    board = Scoreboard()
    board.add_team("lions")
    board.score("lions", "try")
    board.next_period()
    board.get_period_scores("lions")  # -> [5, 0]
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
        self._period = 1
        self._events = {}  # team name -> list of (kind, points, period), in adding order
        self._undone = {}  # team name -> list of (kind, points), in undo order

    def add_team(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("team name must be a non-empty str")
        if name in self._events:
            raise ScoreboardError(f"team {name!r} was already added")
        self._events[name] = []
        self._undone[name] = []

    def score(self, team, kind):
        self._require(team)
        points = self.get_points(kind)
        self._events[team].append((kind, points, self._period))

    def undo_last(self, team):
        self._require(team)
        if not self._events[team]:
            raise ScoreboardError(f"team {team!r} has no events to undo")
        kind, points, _ = self._events[team].pop()
        self._undone[team].append((kind, points))
        return (kind, points)

    def get_score(self, team):
        self._require(team)
        return sum(points for _, points, _ in self._events[team])

    def get_events(self, team, period=None):
        self._require(team)
        if period is not None:
            self._check_period(period)
        return [
            (kind, points)
            for kind, points, scored_in in self._events[team]
            if period is None or scored_in == period
        ]

    def get_undone(self, team):
        self._require(team)
        return list(self._undone[team])

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

    def next_period(self):
        self._period += 1
        return self._period

    def get_period(self):
        return self._period

    def get_period_scores(self, team):
        self._require(team)
        totals = [0] * self._period
        for _, points, scored_in in self._events[team]:
            totals[scored_in - 1] += points
        return totals

    def get_period_standings(self, period):
        self._check_period(period)
        return sorted(self._events, key=lambda team: -self._period_points(team, period))

    def _period_points(self, team, period):
        return sum(points for _, points, scored_in in self._events[team] if scored_in == period)

    def _check_period(self, period):
        if (
            isinstance(period, bool)
            or not isinstance(period, int)
            or not 1 <= period <= self._period
        ):
            raise ValueError(f"period must be an int from 1 to {self._period}, got {period!r}")

    def _require(self, team):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(team, str) or team not in self._events:
            raise KeyError(team)
