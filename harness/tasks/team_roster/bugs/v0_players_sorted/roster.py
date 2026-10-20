"""Team roster: a basketball roster under a salary cap.

Planted bug (initial version): players() lists names alphabetically
instead of in the order they were added. The public checks never look at
the order, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from roster import Roster
    roster = Roster(salary_cap=100_000)
    roster.add_player("Ada", "PG", 30_000)
    roster.get_cap_space()
"""

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


class Roster:
    def __init__(self, salary_cap):
        check_positive_int(salary_cap, "salary_cap")
        self._cap = salary_cap
        self._players = {}  # name -> (position, salary), in the order added

    def add_player(self, name, position, salary):
        check_player(name, position, salary)
        if name in self._players:
            raise RosterError(f"{name!r} is already on the roster")
        if self.get_payroll() + salary > self._cap:
            raise CapExceeded(f"adding {name!r} would go over the cap")
        self._players[name] = (position, salary)

    def remove_player(self, name):
        self._require(name)
        del self._players[name]

    def get_players(self, position=None):
        if position is not None and position not in POSITIONS:
            raise ValueError(f"position must be one of {POSITIONS}, got {position!r}")
        return sorted(
            name for name, (pos, _) in self._players.items() if position is None or pos == position
        )

    def get_player(self, name):
        self._require(name)
        position, salary = self._players[name]
        return {"name": name, "position": position, "salary": salary}

    def get_payroll(self):
        return sum(salary for _, salary in self._players.values())

    def get_cap_space(self):
        return self._cap - self.get_payroll()

    def _require(self, name):
        if not isinstance(name, str) or name not in self._players:
            raise KeyError(name)
