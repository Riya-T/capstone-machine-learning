"""Herd paddocks with undo of every change to the paddocks and their animals.

Correct solution for herd_paddocks after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from farm import Farm
    farm = Farm()
    farm.add_paddock("north")
    farm.arrive("north", "sheep", 12)
    farm.undo()  # north is empty again
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
        # paddock name -> {species: count}, in the order the paddocks were
        # added; only counts above 0 are stored.
        self._paddocks = {}
        self._undo_stack = []  # copies of the paddocks as they were before each call

    def add_paddock(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("paddock name must be a non-empty str")
        if name in self._paddocks:
            raise FarmError(f"paddock name {name!r} is already used")
        self._save()
        self._paddocks[name] = {}

    def arrive(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
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
        self._save()
        self._change(from_paddock, species, -count)
        self._change(to_paddock, species, count)

    def move_all(self, from_paddock, to_paddock):
        self._require(from_paddock)
        self._require(to_paddock)
        check_different(from_paddock, to_paddock)
        self._save()
        return self._move_everything(from_paddock, to_paddock)

    def close_paddock(self, name, to_paddock):
        self._require(name)
        self._require(to_paddock)
        check_different(name, to_paddock)
        self._save()
        moved = self._move_everything(name, to_paddock)
        del self._paddocks[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise FarmError("nothing to undo")
        self._paddocks = self._undo_stack.pop()

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

    def _change(self, paddock, species, delta):
        animals = self._paddocks[paddock]
        new_count = animals.get(species, 0) + delta
        if new_count:
            animals[species] = new_count
        else:
            del animals[species]
