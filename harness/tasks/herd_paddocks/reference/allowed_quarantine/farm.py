"""Herd paddocks with allowed species per paddock and quarantined paddocks.

Correct solution for herd_paddocks after c_allowed and c_quarantine.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from farm import Farm
    farm = Farm()
    farm.add_paddock("north")
    farm.set_allowed("north", ["sheep"])
    farm.arrive("north", "sheep", 12)
    farm.quarantine("north")
"""


class FarmError(Exception):
    pass


class NotEnoughAnimals(FarmError):
    pass


class NotAllowed(FarmError):
    pass


class Quarantined(FarmError):
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
        self._allowed = {}  # paddock name -> set of allowed species; missing = any
        self._quarantined = set()

    def add_paddock(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("paddock name must be a non-empty str")
        if name in self._paddocks:
            raise FarmError(f"paddock name {name!r} is already used")
        self._paddocks[name] = {}
        self._allowed.pop(name, None)  # the name may have been closed and freed

    def arrive(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        self._require_not_quarantined(paddock)
        self._require_allowed(paddock, species)
        self._change(paddock, species, count)

    def depart(self, paddock, species, count):
        self._require(paddock)
        check_species(species)
        check_count(count)
        self._require_not_quarantined(paddock)
        self._require_animals(paddock, species, count)
        self._change(paddock, species, -count)

    def move(self, species, from_paddock, to_paddock, count):
        self._require(from_paddock)
        self._require(to_paddock)
        check_species(species)
        check_count(count)
        check_different(from_paddock, to_paddock)
        self._require_not_quarantined(from_paddock)
        self._require_not_quarantined(to_paddock)
        self._require_animals(from_paddock, species, count)
        self._require_allowed(to_paddock, species)
        self._change(from_paddock, species, -count)
        self._change(to_paddock, species, count)

    def move_all(self, from_paddock, to_paddock):
        self._require(from_paddock)
        self._require(to_paddock)
        check_different(from_paddock, to_paddock)
        self._require_not_quarantined(from_paddock)
        self._require_not_quarantined(to_paddock)
        animals = self._paddocks[from_paddock]
        for species in animals:  # check every species before moving any
            self._require_allowed(to_paddock, species)
        moved = sum(animals.values())
        for species, count in animals.items():
            self._change(to_paddock, species, count)
        animals.clear()
        return moved

    def close_paddock(self, name, to_paddock):
        moved = self.move_all(name, to_paddock)
        del self._paddocks[name]
        return moved

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

    def quarantine(self, paddock):
        self._require(paddock)
        self._quarantined.add(paddock)

    def release(self, paddock):
        self._require(paddock)
        self._quarantined.discard(paddock)

    def get_count(self, paddock, species):
        self._require(paddock)
        return self._paddocks[paddock].get(species, 0)

    def get_species(self, paddock):
        self._require(paddock)
        return sorted(self._paddocks[paddock])

    def get_paddocks(self):
        return list(self._paddocks)

    def _require(self, paddock):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(paddock, str) or paddock not in self._paddocks:
            raise KeyError(paddock)

    def _require_not_quarantined(self, paddock):
        if paddock in self._quarantined:
            raise Quarantined(f"paddock {paddock!r} is quarantined")

    def _require_animals(self, paddock, species, count):
        if self._paddocks[paddock].get(species, 0) < count:
            raise NotEnoughAnimals(f"paddock {paddock!r} has fewer than {count} {species}")

    def _require_allowed(self, paddock, species):
        allowed = self._allowed.get(paddock)
        if allowed is not None and species not in allowed:
            raise NotAllowed(f"{species} may not enter paddock {paddock!r}")

    def _change(self, paddock, species, delta):
        animals = self._paddocks[paddock]
        new_count = animals.get(species, 0) + delta
        if new_count:
            animals[species] = new_count
        else:
            del animals[species]
