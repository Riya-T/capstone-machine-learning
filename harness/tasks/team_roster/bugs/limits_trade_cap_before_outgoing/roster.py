"""Team roster under a salary cap, with trades and position limits.

Planted bug (after c_trades and c_position_limits): position limits work,
but a trade's salary cap check now counts the outgoing players' salaries,
as if they had not left yet.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from roster import Roster
    roster = Roster(salary_cap=100_000, position_limits={"C": 2})
    roster.add_player("Ada", "C", 30_000)
    roster.trade(["Ada"], [("Bo", "C", 35_000)])
"""

from collections import Counter

POSITIONS = ("PG", "SG", "SF", "PF", "C")


class RosterError(Exception):
    pass


class CapExceeded(RosterError):
    pass


def check_positive_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be an int > 0, got {value!r}")


def check_player(name, position, salary):
    if not isinstance(name, str) or not name:
        raise ValueError("a player name must be a non-empty str")
    if position not in POSITIONS:
        raise ValueError(f"position must be one of {POSITIONS}, got {position!r}")
    check_positive_int(salary, "salary")


def check_limits(limits):
    if limits is None:
        return {}
    if not isinstance(limits, dict):
        raise ValueError("position_limits must be a dict or None")
    for position, most in limits.items():
        if position not in POSITIONS:
            raise ValueError(f"position must be one of {POSITIONS}, got {position!r}")
        if isinstance(most, bool) or not isinstance(most, int) or most < 0:
            raise ValueError(f"a position limit must be an int >= 0, got {most!r}")
    return dict(limits)


def total_salary(players):
    return sum(salary for _, salary in players.values())


class Roster:
    def __init__(self, salary_cap, position_limits=None):
        check_positive_int(salary_cap, "salary_cap")
        self._cap = salary_cap
        self._limits = check_limits(position_limits)  # position -> most players
        self._players = {}  # name -> (position, salary), in the order added

    def add_player(self, name, position, salary):
        check_player(name, position, salary)
        if name in self._players:
            raise RosterError(f"{name!r} is already on the roster")
        self._check_limits({**self._players, name: (position, salary)})
        if self.get_payroll() + salary > self._cap:
            raise CapExceeded(f"adding {name!r} would go over the cap")
        self._players[name] = (position, salary)

    def remove_player(self, name):
        self._require(name)
        del self._players[name]

    def trade(self, outgoing, incoming):
        outgoing = list(outgoing)
        incoming = [tuple(entry) for entry in incoming]
        for name in outgoing:
            self._require(name)
        if len(set(outgoing)) != len(outgoing):
            raise ValueError("a player is listed twice in outgoing")
        for name, position, salary in incoming:
            check_player(name, position, salary)
        # Build the roster as it would be after the trade, check it, and only
        # then adopt it, so a failed trade changes nothing.
        after = {name: entry for name, entry in self._players.items() if name not in outgoing}
        for name, position, salary in incoming:
            if name in after:
                raise RosterError(f"{name!r} would be on the roster twice")
            after[name] = (position, salary)
        self._check_limits(after)
        if self.get_payroll() + sum(salary for _, _, salary in incoming) > self._cap:
            raise CapExceeded("the trade would go over the cap")
        self._players = after

    def get_players(self, position=None):
        if position is not None and position not in POSITIONS:
            raise ValueError(f"position must be one of {POSITIONS}, got {position!r}")
        return [
            name for name, (pos, _) in self._players.items() if position is None or pos == position
        ]

    def get_player(self, name):
        self._require(name)
        position, salary = self._players[name]
        return {"name": name, "position": position, "salary": salary}

    def get_payroll(self):
        return total_salary(self._players)

    def get_cap_space(self):
        return self._cap - self.get_payroll()

    def _check_limits(self, players):
        counts = Counter(position for position, _ in players.values())
        for position, most in self._limits.items():
            if counts[position] > most:
                raise RosterError(f"more than {most} players at {position}")

    def _require(self, name):
        if not isinstance(name, str) or name not in self._players:
            raise KeyError(name)
