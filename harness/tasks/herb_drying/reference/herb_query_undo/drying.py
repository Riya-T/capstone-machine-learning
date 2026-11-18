"""Herb drying with lookups of one herb across racks, and undo.

Correct solution for herb_drying after c_herb_query and c_undo. Never shown
to the writer or the editor; validate-tasks checks that it passes every
test it should.

Usage:
    from drying import DryingRoom
    room = DryingRoom()
    room.add_rack("north")
    room.add_rack("south")
    room.hang("north", "sage", 4)
    room.dismantle_rack("north", "south")
    room.undo()  # north is back with its sage
    room.get_racks_with("sage")  # ["north"]
"""


class DryingError(Exception):
    pass


class NotEnoughBundles(DryingError):
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
        self._undo_stack = []  # copies of the racks as they were before each call

    def add_rack(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("rack name must be a non-empty str")
        if name in self._racks:
            raise DryingError(f"rack name {name!r} is already used")
        self._save()
        self._racks[name] = {}

    def hang(self, rack, herb, count):
        self._require(rack)
        check_herb(herb)
        check_count(count)
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
        self._save()
        return self._move_everything(from_rack, to_rack)

    def dismantle_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._racks[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise DryingError("nothing to undo")
        self._racks = self._undo_stack.pop()

    def get_count(self, rack, herb):
        self._require(rack)
        return self._racks[rack].get(herb, 0)

    def get_herbs(self, rack):
        self._require(rack)
        return sorted(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

    def get_total(self, herb):
        return sum(herbs.get(herb, 0) for herbs in self._racks.values())

    def get_racks_with(self, herb):
        # Only counts above 0 are stored, so a stored herb has a bundle.
        return [name for name, herbs in self._racks.items() if herb in herbs]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: dict(herbs) for name, herbs in self._racks.items()})

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

    def _change(self, rack, herb, delta):
        herbs = self._racks[rack]
        new_count = herbs.get(herb, 0) + delta
        if new_count:
            herbs[herb] = new_count
        else:
            del herbs[herb]
