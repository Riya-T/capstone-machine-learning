"""Aquarium tanks: how many fish of each species are in each tank.

Planted bug (initial version): get_species lists the species in the order
they first came into the tank instead of alphabetically. The public checks
only add species in alphabetical order, so only the hidden initial tests
catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from aquarium import Aquarium
    aquarium = Aquarium()
    aquarium.add_tank("reef")
    aquarium.add_fish("reef", "clownfish", 6)
"""


class AquariumError(Exception):
    pass


class NotEnoughFish(AquariumError):
    pass


def check_species(species):
    if not isinstance(species, str) or not species:
        raise ValueError(f"species must be a non-empty str, got {species!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_tank, to_tank):
    if from_tank == to_tank:
        raise ValueError("cannot move fish into the tank they are in")


class Aquarium:
    def __init__(self):
        # tank name -> {species: count}, in the order the tanks were added;
        # only counts above 0 are stored.
        self._tanks = {}

    def add_tank(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("tank name must be a non-empty str")
        if name in self._tanks:
            raise AquariumError(f"tank name {name!r} is already used")
        self._tanks[name] = {}

    def add_fish(self, tank, species, count):
        self._require(tank)
        check_species(species)
        check_count(count)
        self._change(tank, species, count)

    def remove_fish(self, tank, species, count):
        self._require(tank)
        check_species(species)
        check_count(count)
        self._require_fish(tank, species, count)
        self._change(tank, species, -count)

    def move_all(self, from_tank, to_tank):
        self._require(from_tank)
        self._require(to_tank)
        check_different(from_tank, to_tank)
        fish = self._tanks[from_tank]
        moved = sum(fish.values())
        for species, count in list(fish.items()):
            self._change(to_tank, species, count)
        fish.clear()
        return moved

    def drain_tank(self, from_tank, to_tank):
        moved = self.move_all(from_tank, to_tank)
        del self._tanks[from_tank]
        return moved

    def get_count(self, tank, species):
        self._require(tank)
        return self._tanks[tank].get(species, 0)

    def get_species(self, tank):
        self._require(tank)
        return list(self._tanks[tank])

    def get_tanks(self):
        return list(self._tanks)

    def _require(self, tank):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(tank, str) or tank not in self._tanks:
            raise KeyError(tank)

    def _require_fish(self, tank, species, count):
        if self._tanks[tank].get(species, 0) < count:
            raise NotEnoughFish(f"tank {tank!r} has fewer than {count} {species}")

    def _change(self, tank, species, delta):
        fish = self._tanks[tank]
        new_count = fish.get(species, 0) + delta
        if new_count:
            fish[species] = new_count
        else:
            del fish[species]
