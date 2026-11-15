"""Herd paddocks: how many animals of each species are in each paddock.

Every successful change is recorded as an operation in self._ops; the
current counts and paddocks are what replaying those operations from the
start gives.
"""


class FarmError(Exception):
    pass


class NotEnoughAnimals(FarmError):
    pass


def check_species(species):
    if not isinstance(species, str) or not species:
        raise ValueError(f"species must be a non-empty str, got {species!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_paddock, to_paddock):
    if from_paddock == to_paddock:
        raise ValueError("cannot move animals into the paddock they are in")


class Farm:
    def __init__(self):
        self._ops = []  # every successful change, oldest first: (name, *args)
        self._rebuild()

    def add_paddock(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("paddock name must be a non-empty str")
        if name in self._paddocks:
            raise FarmError(f"paddock name {name!r} is already used")
        return self._record("add_paddock", name)

    def arrive(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        return self._record("arrive", paddock, species, count)

    def depart(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        self._require_animals(paddock, species, count)
        return self._record("depart", paddock, species, count)

    def move(self, species, from_paddock, to_paddock, count):
        self._require(from_paddock)
        self._require(to_paddock)
        check_species(species)
        check_count(count)
        check_different(from_paddock, to_paddock)
        self._require_animals(from_paddock, species, count)
        return self._record("move", species, from_paddock, to_paddock, count)

    def move_all(self, from_paddock, to_paddock):
        self._require(from_paddock)
        self._require(to_paddock)
        check_different(from_paddock, to_paddock)
        return self._record("move_all", from_paddock, to_paddock)

    def close_paddock(self, name, to_paddock):
        self._require(name)
        self._require(to_paddock)
        check_different(name, to_paddock)
        return self._record("close_paddock", name, to_paddock)

    def get_count(self, paddock, species):
        self._require(paddock)
        return self._paddocks[paddock].get(species, 0)

    def get_species(self, paddock):
        self._require(paddock)
        return sorted(self._paddocks[paddock])

    def get_paddocks(self):
        return list(self._paddocks)

    # --- operations -------------------------------------------------------

    def _record(self, *op):
        """Apply a validated operation and add it to the history."""
        result = self._apply(op)
        self._ops.append(op)
        return result

    def _rebuild(self):
        """Recompute the state by replaying every recorded operation."""
        # paddock name -> {species: count}, in the order the paddocks were
        # added; only counts above 0 are stored.
        self._paddocks = {}
        for op in self._ops:
            self._apply(op)

    def _apply(self, op):
        name, *args = op
        if name == "add_paddock":
            self._paddocks[args[0]] = {}
        elif name == "arrive":
            paddock, species, count = args
            self._change(paddock, species, count)
        elif name == "depart":
            paddock, species, count = args
            self._change(paddock, species, -count)
        elif name == "move":
            species, from_paddock, to_paddock, count = args
            self._change(from_paddock, species, -count)
            self._change(to_paddock, species, count)
        elif name == "move_all":
            return self._move_animals(*args)
        elif name == "close_paddock":
            paddock, to_paddock = args
            moved = self._move_animals(paddock, to_paddock)
            del self._paddocks[paddock]
            return moved
        return None

    # --- helpers ----------------------------------------------------------

    def _require(self, paddock):
        if not isinstance(paddock, str) or paddock not in self._paddocks:
            raise KeyError(paddock)

    def _require_animals(self, paddock, species, count):
        if self._paddocks[paddock].get(species, 0) < count:
            raise NotEnoughAnimals(f"paddock {paddock!r} has fewer than {count} {species}")

    def _move_animals(self, from_paddock, to_paddock):
        animals = self._paddocks[from_paddock]
        moved = sum(animals.values())
        for species, count in animals.items():
            self._change(to_paddock, species, count)
        animals.clear()
        return moved

    def _change(self, paddock, species, delta):
        animals = self._paddocks[paddock]
        new_count = animals.get(species, 0) + delta
        if new_count:
            animals[species] = new_count
        else:
            del animals[species]
