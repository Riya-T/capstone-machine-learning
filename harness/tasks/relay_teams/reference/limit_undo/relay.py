"""Relay teams with undo and a limit on lineup size.

Correct solution for relay_teams after c_undo and c_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from relay import RelayMeet
    meet = RelayMeet(max_runners=4)
    meet.add_team("hawks")
    meet.add_runner("hawks", "ana")
    meet.undo()  # the hawks' lineup is empty again
"""


class RelayError(Exception):
    pass


class TeamFull(RelayError):
    pass


class RelayMeet:
    def __init__(self, max_runners=None):
        if max_runners is not None and (
            isinstance(max_runners, bool) or not isinstance(max_runners, int) or max_runners <= 0
        ):
            raise ValueError(f"max_runners must be None or a positive int, got {max_runners!r}")
        self._max_runners = max_runners
        # team name -> its lineup in running order, in the order the teams were added.
        self._teams = {}
        self._undo_stack = []  # copies of the teams as they were before each call

    def add_team(self, name):
        if name in self._teams:
            raise RelayError(f"team name {name!r} is already used")
        self._save()
        self._teams[name] = []

    def add_runner(self, team, runner):
        self._require(team)
        if self._team_of(runner) is not None:
            raise RelayError(f"{runner!r} is already in a team")
        self._require_room(team, 1)
        self._save()
        self._teams[team].append(runner)

    def remove_runner(self, runner):
        team = self._find(runner)
        self._save()
        self._teams[team].remove(runner)

    def move_runner(self, runner, team):
        current = self._find(runner)
        self._require(team)
        if current == team:
            raise ValueError(f"{runner!r} is already in team {team!r}")
        self._require_room(team, 1)
        self._save()
        self._teams[current].remove(runner)
        self._teams[team].append(runner)

    def merge_teams(self, source, into):
        self._require(source)
        self._require(into)
        if source == into:
            raise ValueError("cannot merge a team into itself")
        self._require_room(into, len(self._teams[source]))
        self._save()
        runners = self._teams.pop(source)
        self._teams[into].extend(runners)
        return len(runners)

    def withdraw_team(self, name):
        self._require(name)
        self._save()
        return len(self._teams.pop(name))

    def undo(self):
        if not self._undo_stack:
            raise RelayError("nothing to undo")
        self._teams = self._undo_stack.pop()

    def get_max_runners(self):
        return self._max_runners

    def get_lineup(self, team):
        self._require(team)
        return list(self._teams[team])

    def get_teams(self):
        return list(self._teams)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(lineup) for name, lineup in self._teams.items()})

    def _require(self, team):
        if team not in self._teams:
            raise KeyError(team)

    def _require_room(self, team, count):
        if self._max_runners is not None and len(self._teams[team]) + count > self._max_runners:
            raise TeamFull(f"team {team!r} has no room for {count} more runners")

    def _team_of(self, runner):
        for name, lineup in self._teams.items():
            if runner in lineup:
                return name
        return None

    def _find(self, runner):
        team = self._team_of(runner)
        if team is None:
            raise KeyError(runner)
        return team
