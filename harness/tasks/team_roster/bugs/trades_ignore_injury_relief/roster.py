"""Team roster under a salary cap, with an injured list and trades.

Planted bug (after c_injuries and c_trades): trades work, but add_player
judges the cap by the whole payroll again, so an injured player's salary
no longer frees cap room for a new player.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from roster import Roster
    roster = Roster(salary_cap=100_000)
    roster.add_player("Ada", "PG", 30_000)
    roster.place_on_injured_list("Ada")
    roster.trade(["Ada"], [("Bo", "C", 35_000)])
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


def cap_hit_of(players, injured):
    return sum(salary for name, (_, salary) in players.items() if name not in injured)


class Roster:
    def __init__(self, salary_cap):
        check_positive_int(salary_cap, "salary_cap")
        self._cap = salary_cap
        self._players = {}  # name -> (position, salary), in the order added
        self._injured = set()

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
        self._injured.discard(name)

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
        # then adopt it, so a failed trade changes nothing. Incoming players
        # are never injured; outgoing ones leave the injured list.
        after = {name: entry for name, entry in self._players.items() if name not in outgoing}
        for name, position, salary in incoming:
            if name in after:
                raise RosterError(f"{name!r} would be on the roster twice")
            after[name] = (position, salary)
        injured_after = self._injured - set(outgoing)
        if cap_hit_of(after, injured_after) > self._cap:
            raise CapExceeded("the trade would go over the cap")
        self._players = after
        self._injured = injured_after

    def place_on_injured_list(self, name):
        self._require(name)
        self._injured.add(name)

    def activate(self, name):
        self._require(name)
        if name not in self._injured:
            return
        if self.get_cap_hit() + self._players[name][1] > self._cap:
            raise CapExceeded(f"activating {name!r} would go over the cap")
        self._injured.discard(name)

    def is_injured(self, name):
        self._require(name)
        return name in self._injured

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
        return sum(salary for _, salary in self._players.values())

    def get_cap_hit(self):
        return cap_hit_of(self._players, self._injured)

    def get_cap_space(self):
        return self._cap - self.get_cap_hit()

    def _require(self, name):
        if not isinstance(name, str) or name not in self._players:
            raise KeyError(name)
