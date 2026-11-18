"""Herb drying with undo and rack capacities.

Correct solution for herb_drying after c_undo and c_capacity. Never shown
to the writer or the editor; validate-tasks checks that it passes every
test it should.

Usage:
    from drying import DryingRoom
    room = DryingRoom()
    room.add_rack("north")
    room.set_capacity("north", 10)
    room.hang("north", "sage", 4)
    room.undo()  # north is empty again, still with capacity 10
"""


class DryingError(Exception):
    pass


class NotEnoughBundles(DryingError):
    pass


class RackFull(DryingError):
    pass


def check_herb(herb):
    if not isinstance(herb, str) or not herb:
        raise ValueError(f"herb must be a non-empty str, got {herb!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_rack, to_rack):
    if from_rack == to_rack:
        raise ValueError("cannot move bundles onto the rack they are on")


class DryingRoom:
    def __init__(self):
        # rack name -> {herb: bundles}, in the order the racks were added;
        # only counts above 0 are stored.
        self._racks = {}
        self._capacity = {}  # rack name -> capacity; missing = no limit
        self._undo_stack = []  # copies of the state as it was before each call

    def add_rack(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("rack name must be a non-empty str")
        if name in self._racks:
            raise DryingError(f"rack name {name!r} is already used")
        self._save()
        self._racks[name] = {}
        self._capacity.pop(name, None)  # the name may have been dismantled

    def hang(self, rack, herb, count):
        self._require(rack)
        check_herb(herb)
        check_count(count)
        self._require_room(rack, count)
        self._save()
        self._change(rack, herb, count)

    def take_down(self, rack, herb, count):
        self._require(rack)
        check_herb(herb)
        check_count(count)
        if self._racks[rack].get(herb, 0) < count:
            raise NotEnoughBundles(f"rack {rack!r} has fewer than {count} bundles of {herb}")
        self._save()
        self._change(rack, herb, -count)

    def shift_all(self, from_rack, to_rack):
        self._require(from_rack)
        self._require(to_rack)
        check_different(from_rack, to_rack)
        self._require_room(to_rack, sum(self._racks[from_rack].values()))
        self._save()
        return self._move_everything(from_rack, to_rack)

    def dismantle_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(into, sum(self._racks[name].values()))
        self._save()
        moved = self._move_everything(name, into)
        del self._racks[name]
        self._capacity.pop(name, None)
        return moved

    def set_capacity(self, rack, capacity):
        self._require(rack)
        if capacity is not None and (
            isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0
        ):
            raise ValueError(f"capacity must be None or a positive int, got {capacity!r}")
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
            raise DryingError("nothing to undo")
        self._racks, self._capacity = self._undo_stack.pop()

    def get_count(self, rack, herb):
        self._require(rack)
        return self._racks[rack].get(herb, 0)

    def get_herbs(self, rack):
        self._require(rack)
        return sorted(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        racks = {name: dict(herbs) for name, herbs in self._racks.items()}
        self._undo_stack.append((racks, dict(self._capacity)))

    def _move_everything(self, from_rack, to_rack):
        herbs = self._racks[from_rack]
        moved = sum(herbs.values())
        for herb, count in herbs.items():
            self._change(to_rack, herb, count)
        herbs.clear()
        return moved

    def _require(self, rack):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(rack, str) or rack not in self._racks:
            raise KeyError(rack)

    def _require_room(self, rack, adding):
        capacity = self._capacity.get(rack)
        if capacity is not None and sum(self._racks[rack].values()) + adding > capacity:
            raise RackFull(f"rack {rack!r} has room for fewer than {adding} more bundles")

    def _change(self, rack, herb, delta):
        herbs = self._racks[rack]
        new_count = herbs.get(herb, 0) + delta
        if new_count:
            herbs[herb] = new_count
        else:
            del herbs[herb]
