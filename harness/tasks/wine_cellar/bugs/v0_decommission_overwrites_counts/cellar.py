"""Wine cellar: bottles per vintage per rack.

Planted bug (initial version): decommission_rack copies the rack's bottles
into the receiving rack with dict.update, which replaces the count of a
vintage the receiving rack already has instead of adding to it. The public
checks only decommission into an empty rack, so only the hidden initial
tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.
"""


class CellarError(Exception):
    pass


class NotEnoughBottles(CellarError):
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

    def add_rack(self, name):
        if name in self._racks:
            raise CellarError(f"rack name {name!r} is already used")
        self._racks[name] = {}

    def store(self, rack, vintage, count):
        self._require(rack)
        check_count(count)
        self._change(rack, vintage, count)

    def take(self, rack, vintage, count):
        self._require(rack)
        check_count(count)
        self._require_bottles(rack, vintage, count)
        self._change(rack, vintage, -count)

    def relocate_all(self, from_rack, to_rack):
        self._require(from_rack)
        self._require(to_rack)
        check_different(from_rack, to_rack)
        return self._move_everything(from_rack, to_rack)

    def decommission_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        bottles = self._racks.pop(name)
        self._racks[into].update(bottles)
        return sum(bottles.values())

    def get_count(self, rack, vintage):
        self._require(rack)
        return self._racks[rack].get(vintage, 0)

    def get_vintages(self, rack):
        self._require(rack)
        return sorted(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

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

    def _change(self, rack, vintage, delta):
        bottles = self._racks[rack]
        new_count = bottles.get(vintage, 0) + delta
        if new_count:
            bottles[vintage] = new_count
        else:
            del bottles[vintage]
