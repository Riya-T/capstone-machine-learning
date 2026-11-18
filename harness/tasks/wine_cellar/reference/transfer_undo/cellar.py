"""Wine cellar with transfers of several moves in one call, and undo.

Correct solution for wine_cellar after c_transfer and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cellar import Cellar
    cellar = Cellar()
    cellar.add_rack("north")
    cellar.store("north", 2015, 6)
    cellar.undo()  # north is empty again
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
        self._undo_stack = []  # copies of the racks as they were before each call

    def add_rack(self, name):
        if name in self._racks:
            raise CellarError(f"rack name {name!r} is already used")
        self._save()
        self._racks[name] = {}

    def store(self, rack, vintage, count):
        self._require(rack)
        check_count(count)
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
        self._save()
        return self._move_everything(from_rack, to_rack)

    def decommission_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._racks[name]
        return moved

    def transfer(self, moves):
        # Make the moves on a copy, and keep it only if every move succeeds;
        # the untouched original is what undo goes back to.
        original = self._racks
        self._racks = {name: dict(bottles) for name, bottles in original.items()}
        try:
            total = 0
            for from_rack, to_rack, vintage, count in moves:
                self._move(from_rack, to_rack, vintage, count)
                total += count
        except Exception:
            self._racks = original
            raise
        self._undo_stack.append(original)
        return total

    def undo(self):
        if not self._undo_stack:
            raise CellarError("nothing to undo")
        self._racks = self._undo_stack.pop()

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
        self._undo_stack.append({name: dict(bottles) for name, bottles in self._racks.items()})

    def _move(self, from_rack, to_rack, vintage, count):
        self._require(from_rack)
        self._require(to_rack)
        check_count(count)
        check_different(from_rack, to_rack)
        self._require_bottles(from_rack, vintage, count)
        self._change(from_rack, vintage, -count)
        self._change(to_rack, vintage, count)

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
