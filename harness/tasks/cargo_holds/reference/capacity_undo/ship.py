"""Cargo holds with undo and hold capacities.

Correct solution for cargo_holds after c_undo and c_capacity.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from ship import Ship
    ship = Ship()
    ship.add_hold("fore", capacity=20)
    ship.load("fore", "grain", 12)
    ship.undo()  # fore is empty again
"""


class CargoError(Exception):
    pass


class NotEnoughCrates(CargoError):
    pass


class HoldFull(CargoError):
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
        self._capacity = {}  # hold name -> capacity, or None for no limit
        self._undo_stack = []  # (holds, capacities) as they were before each call

    def add_hold(self, name, capacity=None):
        if name in self._holds:
            raise CargoError(f"hold name {name!r} is already used")
        if capacity is not None:
            check_count(capacity)
        self._save()
        self._holds[name] = {}
        self._capacity[name] = capacity

    def load(self, hold, cargo, count):
        self._require(hold)
        check_count(count)
        self._require_room(hold, count)
        self._save()
        self._change(hold, cargo, count)

    def unload(self, hold, cargo, count):
        self._require(hold)
        check_count(count)
        self._require_crates(hold, cargo, count)
        self._save()
        self._change(hold, cargo, -count)

    def shift_all(self, from_hold, to_hold):
        self._require(from_hold)
        self._require(to_hold)
        check_different(from_hold, to_hold)
        self._require_room(to_hold, self._total(from_hold))
        self._save()
        return self._move_everything(from_hold, to_hold)

    def seal_hold(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(into, self._total(name))
        self._save()
        moved = self._move_everything(name, into)
        del self._holds[name]
        del self._capacity[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise CargoError("nothing to undo")
        self._holds, self._capacity = self._undo_stack.pop()

    def get_capacity(self, hold):
        self._require(hold)
        return self._capacity[hold]

    def get_count(self, hold, cargo):
        self._require(hold)
        return self._holds[hold].get(cargo, 0)

    def get_cargo(self, hold):
        self._require(hold)
        return sorted(self._holds[hold])

    def get_holds(self):
        return list(self._holds)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        holds = {name: dict(crates) for name, crates in self._holds.items()}
        self._undo_stack.append((holds, dict(self._capacity)))

    def _total(self, hold):
        return sum(self._holds[hold].values())

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

    def _require_room(self, hold, count):
        capacity = self._capacity[hold]
        if capacity is not None and self._total(hold) + count > capacity:
            raise HoldFull(f"hold {hold!r} has no room for {count} more crates")

    def _change(self, hold, cargo, delta):
        crates = self._holds[hold]
        new_count = crates.get(cargo, 0) + delta
        if new_count:
            crates[cargo] = new_count
        else:
            del crates[cargo]
