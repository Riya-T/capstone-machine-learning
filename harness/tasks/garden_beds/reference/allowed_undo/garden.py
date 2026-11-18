"""Garden beds with undo and allowed species per bed.

Correct solution for garden_beds after c_undo and c_allowed.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from garden import Garden
    garden = Garden()
    garden.add_bed("shade", allowed=["fern", "mint"])
    garden.plant("shade", "fern", 6)
    garden.undo()  # shade is empty again
"""


class GardenError(Exception):
    pass


class NotEnoughPlants(GardenError):
    pass


class NotAllowed(GardenError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_bed, to_bed):
    if from_bed == to_bed:
        raise ValueError("cannot move plants into the bed they are in")


class Garden:
    def __init__(self):
        # bed name -> {species: count}, in the order the beds were added;
        # only counts above 0 are stored.
        self._beds = {}
        self._allowed = {}  # bed name -> set of allowed species, or None for any
        self._undo_stack = []  # (beds, allowed) as they were before each call

    def add_bed(self, name, allowed=None):
        if name in self._beds:
            raise GardenError(f"bed name {name!r} is already used")
        self._save()
        self._beds[name] = {}
        self._allowed[name] = None if allowed is None else set(allowed)

    def plant(self, bed, species, count):
        self._require(bed)
        check_count(count)
        self._require_allowed(bed, species)
        self._save()
        self._change(bed, species, count)

    def pull(self, bed, species, count):
        self._require(bed)
        check_count(count)
        self._require_plants(bed, species, count)
        self._save()
        self._change(bed, species, -count)

    def transplant_all(self, from_bed, to_bed):
        self._require(from_bed)
        self._require(to_bed)
        check_different(from_bed, to_bed)
        self._require_all_allowed(from_bed, to_bed)
        self._save()
        return self._move_everything(from_bed, to_bed)

    def clear_bed(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_all_allowed(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._beds[name]
        del self._allowed[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise GardenError("nothing to undo")
        self._beds, self._allowed = self._undo_stack.pop()

    def get_allowed(self, bed):
        self._require(bed)
        allowed = self._allowed[bed]
        return None if allowed is None else sorted(allowed)

    def get_count(self, bed, species):
        self._require(bed)
        return self._beds[bed].get(species, 0)

    def get_species(self, bed):
        self._require(bed)
        return sorted(self._beds[bed])

    def get_beds(self):
        return list(self._beds)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        beds = {name: dict(plants) for name, plants in self._beds.items()}
        self._undo_stack.append((beds, dict(self._allowed)))

    def _move_everything(self, from_bed, to_bed):
        plants = self._beds[from_bed]
        moved = sum(plants.values())
        for species, count in plants.items():
            self._change(to_bed, species, count)
        plants.clear()
        return moved

    def _require(self, bed):
        if bed not in self._beds:
            raise KeyError(bed)

    def _require_plants(self, bed, species, count):
        if self._beds[bed].get(species, 0) < count:
            raise NotEnoughPlants(f"bed {bed!r} has fewer than {count} {species}")

    def _require_allowed(self, bed, species):
        allowed = self._allowed[bed]
        if allowed is not None and species not in allowed:
            raise NotAllowed(f"{species} may not grow in bed {bed!r}")

    def _require_all_allowed(self, from_bed, to_bed):
        # Every species that would move is checked before any plant moves.
        for species in self._beds[from_bed]:
            self._require_allowed(to_bed, species)

    def _change(self, bed, species, delta):
        plants = self._beds[bed]
        new_count = plants.get(species, 0) + delta
        if new_count:
            plants[species] = new_count
        else:
            del plants[species]
