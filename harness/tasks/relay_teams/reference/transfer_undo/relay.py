"""Relay teams with moving several runners at once, and undo.

Correct solution for relay_teams after c_transfer and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from relay import RelayMeet
    meet = RelayMeet()
    meet.add_team("hawks")
    meet.add_team("owls")
    meet.add_runner("hawks", "ana")
    meet.move_runners(["ana"], "owls")
    meet.undo()  # ana is back with the hawks
"""


class RelayError(Exception):
    pass


class RelayMeet:
    def __init__(self):
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
        self._save()
        self._teams[current].remove(runner)
        self._teams[team].append(runner)

    def move_runners(self, runners, team):
        # Every runner is checked before any of them moves. Moving one runner
        # never changes whether another may move, so checking them all
        # against the current lineups is the same as checking each in turn.
        self._require(team)
        teams = [self._find(runner) for runner in runners]
        for runner, current in zip(runners, teams):
            if current == team:
                raise ValueError(f"{runner!r} is already in team {team!r}")
        self._save()
        for runner, current in zip(runners, teams):
            self._teams[current].remove(runner)
            self._teams[team].append(runner)
        return len(runners)

    def merge_teams(self, source, into):
        self._require(source)
        self._require(into)
        if source == into:
            raise ValueError("cannot merge a team into itself")
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
