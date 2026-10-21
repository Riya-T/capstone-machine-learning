"""Scoreboard where each team has a version number, to detect conflicts.

Correct solution for scoreboard after c_versions.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from scoreboard import Scoreboard
    board = Scoreboard()
    board.add_team("lions")
    board.score("lions", "try", expected_version=1)
    board.get_version("lions")  # -> 2
"""

POINTS = {"try": 5, "conversion": 2, "drop_goal": 3}


class ScoreboardError(Exception):
    pass


class VersionConflict(ScoreboardError):
    pass


class Scoreboard:
    def __init__(self):
        self._events = {}  # team name -> list of (kind, points), in adding order
        self._versions = {}  # team name -> version number

    def add_team(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("team name must be a non-empty str")
        if name in self._events:
            raise ScoreboardError(f"team {name!r} was already added")
        self._events[name] = []
        self._versions[name] = 1

    def score(self, team, kind, expected_version=None):
        self._require(team)
        if not isinstance(kind, str) or kind not in POINTS:
            raise ValueError(f"unknown kind of score: {kind!r}")
        self._check_version(team, expected_version)
        self._events[team].append((kind, POINTS[kind]))
        self._versions[team] += 1

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

    def get_version(self, team):
        self._require(team)
        return self._versions[team]

    def _check_version(self, team, expected_version):
        if expected_version is not None and expected_version != self._versions[team]:
            raise VersionConflict(
                f"team {team!r} is at version {self._versions[team]}, not {expected_version}"
            )

    def _require(self, team):
        # Non-str names are never stored, so they count as "not added" too.
        if not isinstance(team, str) or team not in self._events:
            raise KeyError(team)
