"""Wine cellar with undo and rack capacities.

Planted bug (after c_undo and c_capacity): capacities were added
correctly, but decommission_rack, rewritten to check the receiving rack's
room first, no longer records itself, so undo skips it and reverses the
call before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from cellar import Cellar
    cellar = Cellar()
    cellar.add_rack("north")
    cellar.set_capacity("north", 12)
    cellar.store("north", 2015, 6)
    cellar.undo()  # north is empty again
"""


class CellarError(Exception):
    pass


class NotEnoughBottles(CellarError):
    pass


class RackFull(CellarError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_rack, to_rack):
    if from_rack == to_rack:
        raise ValueError("cannot move bottles into the rack they are in")


class Cellar:
    def __init__(self):
        # rack name -> {vintage: count}, in the order the racks were added;
        # only counts above 0 are stored.
        self._racks = {}
        self._capacity = {}  # rack name -> most bottles; missing = no limit
        self._undo_stack = []  # (racks, capacities) as they were before each call

    def add_rack(self, name):
        if name in self._racks:
            raise CellarError(f"rack name {name!r} is already used")
        self._save()
        self._racks[name] = {}
        self._capacity.pop(name, None)

    def store(self, rack, vintage, count):
        self._require(rack)
        check_count(count)
        self._require_room(rack, count)
        self._save()
        self._change(rack, vintage, count)

    def take(self, rack, vintage, count):
        self._require(rack)
        check_count(count)
        self._require_bottles(rack, vintage, count)
        self._save()
        self._change(rack, vintage, -count)

    def relocate_all(self, from_rack, to_rack):
        self._require(from_rack)
        self._require(to_rack)
        check_different(from_rack, to_rack)
        self._require_room(to_rack, self._total(from_rack))
        self._save()
        return self._move_everything(from_rack, to_rack)

    def decommission_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(into, self._total(name))
        moved = self._move_everything(name, into)
        del self._racks[name]
        self._capacity.pop(name, None)
        return moved

    def set_capacity(self, rack, capacity):
        self._require(rack)
        if capacity is not None:
            if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
                raise ValueError(f"capacity must be None or a positive int, got {capacity!r}")
            if capacity < self._total(rack):
                raise ValueError(f"rack {rack!r} already holds more than {capacity} bottles")
        self._save()
        if capacity is None:
            self._capacity.pop(rack, None)
        else:
            self._capacity[rack] = capacity

    def get_capacity(self, rack):
        self._require(rack)
        return self._capacity.get(rack)

    def undo(self):
        if not self._undo_stack:
            raise CellarError("nothing to undo")
        self._racks, self._capacity = self._undo_stack.pop()

    def get_count(self, rack, vintage):
        self._require(rack)
        return self._racks[rack].get(vintage, 0)

    def get_vintages(self, rack):
        self._require(rack)
        return sorted(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        racks = {name: dict(bottles) for name, bottles in self._racks.items()}
        self._undo_stack.append((racks, dict(self._capacity)))

    def _total(self, rack):
        return sum(self._racks[rack].values())

    def _move_everything(self, from_rack, to_rack):
        bottles = self._racks[from_rack]
        moved = sum(bottles.values())
        for vintage, count in bottles.items():
            self._change(to_rack, vintage, count)
        bottles.clear()
        return moved

    def _require(self, rack):
        if rack not in self._racks:
            raise KeyError(rack)

    def _require_bottles(self, rack, vintage, count):
        if self._racks[rack].get(vintage, 0) < count:
            raise NotEnoughBottles(f"rack {rack!r} has fewer than {count} bottles of {vintage}")

    def _require_room(self, rack, count):
        capacity = self._capacity.get(rack)
        if capacity is not None and self._total(rack) + count > capacity:
            raise RackFull(f"rack {rack!r} has no room for {count} more bottles")

    def _change(self, rack, vintage, delta):
        bottles = self._racks[rack]
        new_count = bottles.get(vintage, 0) + delta
        if new_count:
            bottles[vintage] = new_count
        else:
            del bottles[vintage]
