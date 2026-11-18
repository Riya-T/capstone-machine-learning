"""Cargo holds.

Correct solution for cargo_holds before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ship import Ship
    ship = Ship()
    ship.add_hold("fore")
    ship.load("fore", "grain", 12)
"""


class CargoError(Exception):
    pass


class NotEnoughCrates(CargoError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_hold, to_hold):
    if from_hold == to_hold:
        raise ValueError("cannot move crates into the hold they are in")


class Ship:
    def __init__(self):
        # hold name -> {cargo: count}, in the order the holds were added;
        # only counts above 0 are stored.
        self._holds = {}

    def add_hold(self, name):
        if name in self._holds:
            raise CargoError(f"hold name {name!r} is already used")
        self._holds[name] = {}

    def load(self, hold, cargo, count):
        self._require(hold)
        check_count(count)
        self._change(hold, cargo, count)

    def unload(self, hold, cargo, count):
        self._require(hold)
        check_count(count)
        self._require_crates(hold, cargo, count)
        self._change(hold, cargo, -count)

    def shift_all(self, from_hold, to_hold):
        self._require(from_hold)
        self._require(to_hold)
        check_different(from_hold, to_hold)
        return self._move_everything(from_hold, to_hold)

    def seal_hold(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        moved = self._move_everything(name, into)
        del self._holds[name]
        return moved

    def get_count(self, hold, cargo):
        self._require(hold)
        return self._holds[hold].get(cargo, 0)

    def get_cargo(self, hold):
        self._require(hold)
        return sorted(self._holds[hold])

    def get_holds(self):
        return list(self._holds)

    def _move_everything(self, from_hold, to_hold):
        crates = self._holds[from_hold]
        moved = sum(crates.values())
        for cargo, count in crates.items():
            self._change(to_hold, cargo, count)
        crates.clear()
        return moved

    def _require(self, hold):
        if hold not in self._holds:
            raise KeyError(hold)

    def _require_crates(self, hold, cargo, count):
        if self._holds[hold].get(cargo, 0) < count:
            raise NotEnoughCrates(f"hold {hold!r} has fewer than {count} crates of {cargo}")

    def _change(self, hold, cargo, delta):
        crates = self._holds[hold]
        new_count = crates.get(cargo, 0) + delta
        if new_count:
            crates[cargo] = new_count
        else:
            del crates[cargo]
