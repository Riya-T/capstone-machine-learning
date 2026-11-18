"""Aquarium tanks with undo and a capacity per tank.

Planted regression bug (sequence s1, step 2): while adding the capacity
check to move_all, the call that saved the state for undo was dropped, so
move_all is no longer recorded. The capacity tests never undo a move_all;
the undo tests from step 1 do.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from aquarium import Aquarium
    aquarium = Aquarium()
    aquarium.add_tank("reef", capacity=10)
    aquarium.add_fish("reef", "clownfish", 6)
    aquarium.undo()  # reef is empty again
"""


class AquariumError(Exception):
    pass


class NotEnoughFish(AquariumError):
    pass


class TankFull(AquariumError):
    pass


def check_species(species):
    if not isinstance(species, str) or not species:
        raise ValueError(f"species must be a non-empty str, got {species!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_capacity(capacity):
    if capacity is None:
        return
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError(f"capacity must be None or a positive int, got {capacity!r}")


def check_different(from_tank, to_tank):
    if from_tank == to_tank:
        raise ValueError("cannot move fish into the tank they are in")


class Aquarium:
    def __init__(self):
        # tank name -> {species: count}, in the order the tanks were added;
        # only counts above 0 are stored.
        self._tanks = {}
        self._capacity = {}  # tank name -> capacity, or None for no limit
        self._undo_stack = []  # copies of the state as it was before each call

    def add_tank(self, name, capacity=None):
        if not isinstance(name, str) or not name:
            raise ValueError("tank name must be a non-empty str")
        check_capacity(capacity)
        if name in self._tanks:
            raise AquariumError(f"tank name {name!r} is already used")
        self._save()
        self._tanks[name] = {}
        self._capacity[name] = capacity

    def add_fish(self, tank, species, count):
        self._require(tank)
        check_species(species)
        check_count(count)
        self._require_room(tank, count)
        self._save()
        self._change(tank, species, count)

    def remove_fish(self, tank, species, count):
        self._require(tank)
        check_species(species)
        check_count(count)
        self._require_fish(tank, species, count)
        self._save()
        self._change(tank, species, -count)

    def move_all(self, from_tank, to_tank):
        self._require(from_tank)
        self._require(to_tank)
        check_different(from_tank, to_tank)
        self._require_room(to_tank, self._total(from_tank))
        return self._move_everything(from_tank, to_tank)

    def drain_tank(self, from_tank, to_tank):
        self._require(from_tank)
        self._require(to_tank)
        check_different(from_tank, to_tank)
        self._require_room(to_tank, self._total(from_tank))
        self._save()
        moved = self._move_everything(from_tank, to_tank)
        del self._tanks[from_tank]
        del self._capacity[from_tank]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise AquariumError("nothing to undo")
        self._tanks, self._capacity = self._undo_stack.pop()

    def get_capacity(self, tank):
        self._require(tank)
        return self._capacity[tank]

    def get_count(self, tank, species):
        self._require(tank)
        return self._tanks[tank].get(species, 0)

    def get_species(self, tank):
        self._require(tank)
        return sorted(self._tanks[tank])

    def get_tanks(self):
        return list(self._tanks)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        tanks = {name: dict(fish) for name, fish in self._tanks.items()}
        self._undo_stack.append((tanks, dict(self._capacity)))

    def _total(self, tank):
        return sum(self._tanks[tank].values())

    def _move_everything(self, from_tank, to_tank):
        fish = self._tanks[from_tank]
        moved = sum(fish.values())
        for species, count in list(fish.items()):
            self._change(to_tank, species, count)
        fish.clear()
        return moved

    def _require(self, tank):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(tank, str) or tank not in self._tanks:
            raise KeyError(tank)

    def _require_fish(self, tank, species, count):
        if self._tanks[tank].get(species, 0) < count:
            raise NotEnoughFish(f"tank {tank!r} has fewer than {count} {species}")

    def _require_room(self, tank, count):
        capacity = self._capacity[tank]
        if capacity is not None and self._total(tank) + count > capacity:
            raise TankFull(f"tank {tank!r} has no room for {count} more fish")

    def _change(self, tank, species, delta):
        fish = self._tanks[tank]
        new_count = fish.get(species, 0) + delta
        if new_count:
            fish[species] = new_count
        else:
            del fish[species]
