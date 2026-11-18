"""Spare parts with undo and frozen bins.

Correct solution for spare_parts after c_undo and c_frozen. Never shown to
the writer or the editor; validate-tasks checks that it passes every test it
should.

Usage:
    from parts import PartsStore
    store = PartsStore()
    store.add_bin("A1")
    store.set_frozen("A1", True)
    store.undo()  # A1 is unfrozen again
"""

import copy


class StoreError(Exception):
    pass


class NotEnoughParts(StoreError):
    pass


class BinFrozen(StoreError):
    pass


def check_part(part):
    if not isinstance(part, str) or not part:
        raise ValueError(f"part number must be a non-empty str, got {part!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


class PartsStore:
    def __init__(self):
        # bin name -> {part: count}, in the order the bins were added; only
        # counts above 0 are stored.
        self._bins = {}
        self._frozen = {}  # bin name -> frozen?
        self._history = []  # copies of the state from before each recorded call

    def add_bin(self, name):
        with _Recorded(self):
            if not isinstance(name, str) or not name:
                raise ValueError("bin name must be a non-empty str")
            if name in self._bins:
                raise StoreError(f"bin {name!r} already exists")
            self._bins[name] = {}
            self._frozen[name] = False

    def stock(self, bin_name, part, count):
        with _Recorded(self):
            self._require(bin_name)
            check_part(part)
            check_count(count)
            self._require_unfrozen(bin_name)
            self._change(bin_name, part, count)

    def take(self, bin_name, part, count):
        with _Recorded(self):
            self._take(bin_name, part, count)

    def merge_bins(self, source, into):
        with _Recorded(self):
            self._require(source)
            self._require(into)
            if source == into:
                raise ValueError("cannot merge a bin into itself")
            self._require_unfrozen(source)
            self._require_unfrozen(into)
            parts = self._remove_bin(source)
            for part, count in parts.items():
                self._change(into, part, count)
        return sum(parts.values())

    def scrap_bin(self, name):
        with _Recorded(self):
            self._require(name)
            self._require_unfrozen(name)
            parts = self._remove_bin(name)
        return sum(parts.values())

    def set_frozen(self, bin_name, frozen):
        with _Recorded(self):
            self._require(bin_name)
            if not isinstance(frozen, bool):
                raise ValueError("frozen must be True or False")
            self._frozen[bin_name] = frozen

    def get_frozen(self, bin_name):
        self._require(bin_name)
        return self._frozen[bin_name]

    def undo(self):
        if not self._history:
            raise StoreError("nothing to undo")
        self._set_state(self._history.pop())

    def get_count(self, bin_name, part):
        self._require(bin_name)
        return self._bins[bin_name].get(part, 0)

    def get_parts(self, bin_name):
        self._require(bin_name)
        return sorted(self._bins[bin_name])

    def get_bins(self):
        return list(self._bins)

    def _get_state(self):
        return copy.deepcopy((self._bins, self._frozen))

    def _set_state(self, state):
        self._bins, self._frozen = state

    def _take(self, bin_name, part, count):
        self._require(bin_name)
        check_part(part)
        check_count(count)
        if self._bins[bin_name].get(part, 0) < count:
            raise NotEnoughParts(f"bin {bin_name!r} has fewer than {count} of {part}")
        self._require_unfrozen(bin_name)
        self._change(bin_name, part, -count)

    def _remove_bin(self, name):
        del self._frozen[name]
        return self._bins.pop(name)

    def _require_unfrozen(self, bin_name):
        if self._frozen[bin_name]:
            raise BinFrozen(f"bin {bin_name!r} is frozen")

    def _change(self, bin_name, part, delta):
        parts = self._bins[bin_name]
        new_count = parts.get(part, 0) + delta
        if new_count:
            parts[part] = new_count
        else:
            del parts[part]

    def _require(self, bin_name):
        if not isinstance(bin_name, str) or bin_name not in self._bins:
            raise KeyError(bin_name)


class _Recorded:
    """One recorded call: on success the state from before it goes on the
    history; on an error the state is put back and nothing is recorded."""

    def __init__(self, store):
        self.store = store

    def __enter__(self):
        self.before = self.store._get_state()

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.store._history.append(self.before)
        else:
            self.store._set_state(self.before)
        return False
