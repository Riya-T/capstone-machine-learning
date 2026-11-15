"""Fuel depot that can undo its calls.

Correct solution for fuel_depot after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from depot import Depot
    depot = Depot()
    depot.add_tank("north")
    depot.fill("north", 500)
    depot.undo()
"""


class DepotError(Exception):
    pass


class NotEnoughFuel(DepotError):
    pass


def check_litres(litres):
    if isinstance(litres, bool) or not isinstance(litres, int) or litres <= 0:
        raise ValueError(f"litres must be a positive int, got {litres!r}")


def check_keep(keep):
    if isinstance(keep, bool) or not isinstance(keep, int) or keep < 0:
        raise ValueError(f"keep must be an int >= 0, got {keep!r}")


class Depot:
    def __init__(self):
        self._levels = {}  # tank id -> litres, for tanks in use, in the order added
        self._logs = {}  # tank id -> list of (kind, litres), for tanks in use
        self._saved = []  # the state before each call undo can still reverse

    def add_tank(self, tank_id):
        if not isinstance(tank_id, str) or not tank_id:
            raise ValueError("tank_id must be a non-empty str")
        if tank_id in self._levels:
            raise DepotError(f"tank id {tank_id!r} is already in use")
        self._save()
        self._levels[tank_id] = 0
        self._logs[tank_id] = []

    def fill(self, tank_id, litres):
        self._require(tank_id)
        check_litres(litres)
        self._save()
        self._levels[tank_id] += litres
        self._logs[tank_id].append(("fill", litres))

    def drain(self, tank_id, litres):
        self._require(tank_id)
        check_litres(litres)
        self._require_fuel(tank_id, litres)
        self._save()
        self._levels[tank_id] -= litres
        self._logs[tank_id].append(("drain", litres))

    def pump(self, from_id, to_id, litres):
        self._require(from_id)
        self._require(to_id)
        check_litres(litres)
        self._require_different(from_id, to_id)
        self._require_fuel(from_id, litres)
        self._save()
        self._move(from_id, to_id, litres)

    def pump_down(self, from_id, to_id, keep):
        self._require(from_id)
        self._require(to_id)
        check_keep(keep)
        self._require_different(from_id, to_id)
        litres = max(self._levels[from_id] - keep, 0)
        self._save()
        self._move(from_id, to_id, litres)
        return litres

    def retire_tank(self, from_id, to_id):
        self._require(from_id)
        self._require(to_id)
        self._require_different(from_id, to_id)
        litres = self._levels[from_id]
        self._save()
        self._move(from_id, to_id, litres)
        del self._levels[from_id]
        del self._logs[from_id]
        return litres

    def undo(self):
        if not self._saved:
            raise DepotError("nothing to undo")
        self._levels, self._logs = self._saved.pop()

    def get_level(self, tank_id):
        self._require(tank_id)
        return self._levels[tank_id]

    def get_log(self, tank_id):
        self._require(tank_id)
        return list(self._logs[tank_id])

    def get_tanks(self):
        return list(self._levels)

    def _save(self):
        # Called once a call has passed every check, just before it changes anything.
        logs = {tank_id: list(log) for tank_id, log in self._logs.items()}
        self._saved.append((dict(self._levels), logs))

    def _require(self, tank_id):
        # Non-str ids are never stored, so they count as "not in use" too.
        if not isinstance(tank_id, str) or tank_id not in self._levels:
            raise KeyError(tank_id)

    def _require_different(self, from_id, to_id):
        if from_id == to_id:
            raise ValueError(f"cannot move fuel from tank {from_id!r} to itself")

    def _require_fuel(self, tank_id, litres):
        if self._levels[tank_id] < litres:
            raise NotEnoughFuel(f"tank {tank_id!r} holds less than {litres}")

    def _move(self, from_id, to_id, litres):
        # Shared by pump, pump_down and retire_tank; a move of 0 logs nothing.
        if litres == 0:
            return
        self._levels[from_id] -= litres
        self._levels[to_id] += litres
        self._logs[from_id].append(("out", litres))
        self._logs[to_id].append(("in", litres))
