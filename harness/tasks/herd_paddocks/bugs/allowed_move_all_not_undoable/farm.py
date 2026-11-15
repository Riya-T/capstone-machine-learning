"""Herd paddocks with undo and allowed species per paddock.

Planted bug (after c_undo and c_allowed): allowed species were added
correctly, but move_all, rewritten to check every species before moving
any, no longer records itself, so undo skips it and reverses the call
before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from farm import Farm
    farm = Farm()
    farm.add_paddock("north")
    farm.set_allowed("north", ["sheep"])
    farm.arrive("north", "sheep", 12)
    farm.undo()  # north is empty again
"""


class FarmError(Exception):
    pass


class NotEnoughAnimals(FarmError):
    pass


class NotAllowed(FarmError):
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
        # paddock name -> {species: count}, in the order the paddocks were
        # added; only counts above 0 are stored.
        self._paddocks = {}
        self._undo_stack = []  # copies of the paddocks as they were before each call
        self._allowed = {}  # paddock name -> set of allowed species; missing = any

    def add_paddock(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("paddock name must be a non-empty str")
        if name in self._paddocks:
            raise FarmError(f"paddock name {name!r} is already used")
        self._save()
        self._paddocks[name] = {}
        self._allowed.pop(name, None)  # the name may have been closed and freed

    def arrive(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        self._require_allowed(paddock, species)
        self._save()
        self._change(paddock, species, count)

    def depart(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        self._require_animals(paddock, species, count)
        self._save()
        self._change(paddock, species, -count)

    def move(self, species, from_paddock, to_paddock, count):
        self._require(from_paddock)
        self._require(to_paddock)
        check_species(species)
        check_count(count)
        check_different(from_paddock, to_paddock)
        self._require_animals(from_paddock, species, count)
        self._require_allowed(to_paddock, species)
        self._save()
        self._change(from_paddock, species, -count)
        self._change(to_paddock, species, count)

    def move_all(self, from_paddock, to_paddock):
        self._require(from_paddock)
        self._require(to_paddock)
        check_different(from_paddock, to_paddock)
        self._require_all_allowed(from_paddock, to_paddock)
        return self._move_everything(from_paddock, to_paddock)

    def close_paddock(self, name, to_paddock):
        self._require(name)
        self._require(to_paddock)
        check_different(name, to_paddock)
        self._require_all_allowed(name, to_paddock)
        self._save()
        moved = self._move_everything(name, to_paddock)
        del self._paddocks[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise FarmError("nothing to undo")
        self._paddocks = self._undo_stack.pop()

    def set_allowed(self, paddock, species):
        self._require(paddock)
        if species is None:
            self._allowed.pop(paddock, None)
            return
        if not isinstance(species, list) or not all(isinstance(s, str) and s for s in species):
            raise ValueError("allowed species must be None or a list of non-empty str")
        self._allowed[paddock] = set(species)

    def get_allowed(self, paddock):
        self._require(paddock)
        if paddock not in self._allowed:
            return None
        return sorted(self._allowed[paddock])

    def get_count(self, paddock, species):
        self._require(paddock)
        return self._paddocks[paddock].get(species, 0)

    def get_species(self, paddock):
        self._require(paddock)
        return sorted(self._paddocks[paddock])

    def get_paddocks(self):
        return list(self._paddocks)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: dict(animals) for name, animals in self._paddocks.items()})

    def _move_everything(self, from_paddock, to_paddock):
        animals = self._paddocks[from_paddock]
        moved = sum(animals.values())
        for species, count in animals.items():
            self._change(to_paddock, species, count)
        animals.clear()
        return moved

    def _require(self, paddock):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(paddock, str) or paddock not in self._paddocks:
            raise KeyError(paddock)

    def _require_animals(self, paddock, species, count):
        if self._paddocks[paddock].get(species, 0) < count:
            raise NotEnoughAnimals(f"paddock {paddock!r} has fewer than {count} {species}")

    def _require_allowed(self, paddock, species):
        allowed = self._allowed.get(paddock)
        if allowed is not None and species not in allowed:
            raise NotAllowed(f"{species} may not enter paddock {paddock!r}")

    def _require_all_allowed(self, from_paddock, to_paddock):
        # Every species that would move is checked before any animal moves.
        for species in self._paddocks[from_paddock]:
            self._require_allowed(to_paddock, species)

    def _change(self, paddock, species, delta):
        animals = self._paddocks[paddock]
        new_count = animals.get(species, 0) + delta
        if new_count:
            animals[species] = new_count
        else:
            del animals[species]
