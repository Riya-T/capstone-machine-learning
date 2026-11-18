"""Blood fridges with undo and a capacity per fridge.

Correct solution for blood_fridges after c_undo and c_capacity.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from blood_bank import BloodBank
    bank = BloodBank()
    bank.add_fridge("ward", capacity=20)
    bank.store("ward", "O-", 12)
    bank.undo()  # ward is empty again
"""


class BloodBankError(Exception):
    pass


class NotEnoughUnits(BloodBankError):
    pass


class FridgeFull(BloodBankError):
    pass


def check_blood_type(blood_type):
    if not isinstance(blood_type, str) or not blood_type:
        raise ValueError(f"blood type must be a non-empty str, got {blood_type!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_capacity(capacity):
    if capacity is not None and (
        isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0
    ):
        raise ValueError(f"capacity must be None or a positive int, got {capacity!r}")


def check_different(from_fridge, to_fridge):
    if from_fridge == to_fridge:
        raise ValueError("cannot move units into the fridge they are in")


class BloodBank:
    def __init__(self):
        # fridge name -> {blood type: units}, in the order the fridges were
        # added; only counts above 0 are stored.
        self._fridges = {}
        self._capacity = {}  # fridge name -> capacity or None
        self._undo_stack = []  # copies of the state as it was before each call

    def add_fridge(self, name, capacity=None):
        if not isinstance(name, str) or not name:
            raise ValueError("fridge name must be a non-empty str")
        if name in self._fridges:
            raise BloodBankError(f"fridge name {name!r} is already used")
        check_capacity(capacity)
        self._save()
        self._fridges[name] = {}
        self._capacity[name] = capacity

    def store(self, fridge, blood_type, count):
        self._require(fridge)
        check_blood_type(blood_type)
        check_count(count)
        self._require_room(fridge, count)
        self._save()
        self._change(fridge, blood_type, count)

    def take(self, fridge, blood_type, count):
        self._require(fridge)
        check_blood_type(blood_type)
        check_count(count)
        self._require_units(fridge, blood_type, count)
        self._save()
        self._change(fridge, blood_type, -count)

    def transfer_all(self, from_fridge, to_fridge):
        self._require(from_fridge)
        self._require(to_fridge)
        check_different(from_fridge, to_fridge)
        self._require_room(to_fridge, self._total(from_fridge))
        self._save()
        return self._move_everything(from_fridge, to_fridge)

    def retire_fridge(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(into, self._total(name))
        self._save()
        moved = self._move_everything(name, into)
        del self._fridges[name]
        del self._capacity[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise BloodBankError("nothing to undo")
        self._fridges, self._capacity = self._undo_stack.pop()

    def get_capacity(self, fridge):
        self._require(fridge)
        return self._capacity[fridge]

    def get_units(self, fridge, blood_type):
        self._require(fridge)
        return self._fridges[fridge].get(blood_type, 0)

    def get_blood_types(self, fridge):
        self._require(fridge)
        return sorted(self._fridges[fridge])

    def get_fridges(self):
        return list(self._fridges)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        fridges = {name: dict(units) for name, units in self._fridges.items()}
        self._undo_stack.append((fridges, dict(self._capacity)))

    def _total(self, fridge):
        return sum(self._fridges[fridge].values())

    def _move_everything(self, from_fridge, to_fridge):
        units = self._fridges[from_fridge]
        moved = sum(units.values())
        for blood_type, count in units.items():
            self._change(to_fridge, blood_type, count)
        units.clear()
        return moved

    def _require(self, fridge):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(fridge, str) or fridge not in self._fridges:
            raise KeyError(fridge)

    def _require_units(self, fridge, blood_type, count):
        if self._fridges[fridge].get(blood_type, 0) < count:
            raise NotEnoughUnits(f"fridge {fridge!r} has fewer than {count} units of {blood_type}")

    def _require_room(self, fridge, count):
        capacity = self._capacity[fridge]
        if capacity is not None and self._total(fridge) + count > capacity:
            raise FridgeFull(f"fridge {fridge!r} has no room for {count} more units")

    def _change(self, fridge, blood_type, delta):
        units = self._fridges[fridge]
        new_count = units.get(blood_type, 0) + delta
        if new_count:
            units[blood_type] = new_count
        else:
            del units[blood_type]
