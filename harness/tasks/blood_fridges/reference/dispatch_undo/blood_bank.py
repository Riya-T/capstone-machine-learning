"""Blood fridges with orders that are taken as a whole, and undo.

Correct solution for blood_fridges after c_dispatch and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from blood_bank import BloodBank
    bank = BloodBank()
    bank.add_fridge("ward")
    bank.store("ward", "O-", 12)
    bank.undo()  # ward is empty again
"""


class BloodBankError(Exception):
    pass


class NotEnoughUnits(BloodBankError):
    pass


def check_blood_type(blood_type):
    if not isinstance(blood_type, str) or not blood_type:
        raise ValueError(f"blood type must be a non-empty str, got {blood_type!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_fridge, to_fridge):
    if from_fridge == to_fridge:
        raise ValueError("cannot move units into the fridge they are in")


class BloodBank:
    def __init__(self):
        # fridge name -> {blood type: units}, in the order the fridges were
        # added; only counts above 0 are stored.
        self._fridges = {}
        self._undo_stack = []  # copies of the fridges as they were before each call

    def add_fridge(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("fridge name must be a non-empty str")
        if name in self._fridges:
            raise BloodBankError(f"fridge name {name!r} is already used")
        self._save()
        self._fridges[name] = {}

    def store(self, fridge, blood_type, count):
        self._require(fridge)
        check_blood_type(blood_type)
        check_count(count)
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
        self._save()
        return self._move_everything(from_fridge, to_fridge)

    def retire_fridge(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._fridges[name]
        return moved

    def dispatch(self, order):
        # Every tuple is taken from a trial copy; the bank only changes once
        # the whole order has gone through, and then as one undoable call.
        trial = {name: dict(units) for name, units in self._fridges.items()}
        total = 0
        for fridge, blood_type, count in order:
            self._require(fridge)
            check_blood_type(blood_type)
            check_count(count)
            have = trial[fridge].get(blood_type, 0)
            if have < count:
                raise NotEnoughUnits(f"fridge {fridge!r} has fewer than {count} units of {blood_type}")
            if have == count:
                del trial[fridge][blood_type]
            else:
                trial[fridge][blood_type] = have - count
            total += count
        self._save()
        self._fridges = trial
        return total

    def undo(self):
        if not self._undo_stack:
            raise BloodBankError("nothing to undo")
        self._fridges = self._undo_stack.pop()

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
        self._undo_stack.append({name: dict(units) for name, units in self._fridges.items()})

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

    def _change(self, fridge, blood_type, delta):
        units = self._fridges[fridge]
        new_count = units.get(blood_type, 0) + delta
        if new_count:
            units[blood_type] = new_count
        else:
            del units[blood_type]
