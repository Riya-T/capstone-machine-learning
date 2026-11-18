import copy


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

    def _apply(self, change, *args):
        """Run change(holds, *args) on a copy of the holds and keep the copy
        only if it succeeds, so a failed call has no effect."""
        holds = copy.deepcopy(self._holds)
        result = change(holds, *args)
        self._holds = holds
        return result

    def add_hold(self, name):
        self._apply(_add_hold, name)

    def load(self, hold, cargo, count):
        self._apply(_load, hold, cargo, count)

    def unload(self, hold, cargo, count):
        self._apply(_unload, hold, cargo, count)

    def shift_all(self, from_hold, to_hold):
        return self._apply(_shift_all, from_hold, to_hold)

    def seal_hold(self, name, into):
        return self._apply(_seal_hold, name, into)

    def get_count(self, hold, cargo):
        return _require(self._holds, hold).get(cargo, 0)

    def get_cargo(self, hold):
        return sorted(_require(self._holds, hold))

    def get_holds(self):
        return list(self._holds)


# Each change works on the holds it is given (a copy) and may raise.


def _add_hold(holds, name):
    if name in holds:
        raise CargoError(f"hold name {name!r} is already used")
    holds[name] = {}


def _load(holds, hold, cargo, count):
    _require(holds, hold)
    check_count(count)
    _change(holds[hold], cargo, count)


def _unload(holds, hold, cargo, count):
    crates = _require(holds, hold)
    check_count(count)
    if crates.get(cargo, 0) < count:
        raise NotEnoughCrates(f"hold {hold!r} has fewer than {count} crates of {cargo}")
    _change(crates, cargo, -count)


def _shift_all(holds, from_hold, to_hold):
    _require(holds, from_hold)
    _require(holds, to_hold)
    check_different(from_hold, to_hold)
    return _move_everything(holds, from_hold, to_hold)


def _seal_hold(holds, name, into):
    _require(holds, name)
    _require(holds, into)
    check_different(name, into)
    moved = _move_everything(holds, name, into)
    del holds[name]
    return moved


def _move_everything(holds, from_hold, to_hold):
    crates = holds[from_hold]
    moved = sum(crates.values())
    for cargo, count in crates.items():
        _change(holds[to_hold], cargo, count)
    crates.clear()
    return moved


def _require(holds, hold):
    if hold not in holds:
        raise KeyError(hold)
    return holds[hold]


def _change(crates, cargo, delta):
    new_count = crates.get(cargo, 0) + delta
    if new_count:
        crates[cargo] = new_count
    else:
        del crates[cargo]
