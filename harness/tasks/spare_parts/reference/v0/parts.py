"""Spare parts: counts per part number per bin.

Correct solution for the initial spare_parts spec. Never shown to the writer
or the editor; validate-tasks checks that it passes every test it should.

Usage:
    from parts import PartsStore
    store = PartsStore()
    store.add_bin("A1")
    store.add_bin("A2")
    store.stock("A1", "bolt-m6", 40)
    store.merge_bins("A1", "A2")  # 40
"""


class StoreError(Exception):
    pass


class NotEnoughParts(StoreError):
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

    def add_bin(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("bin name must be a non-empty str")
        if name in self._bins:
            raise StoreError(f"bin {name!r} already exists")
        self._bins[name] = {}

    def stock(self, bin_name, part, count):
        self._require(bin_name)
        check_part(part)
        check_count(count)
        self._change(bin_name, part, count)

    def take(self, bin_name, part, count):
        self._require(bin_name)
        check_part(part)
        check_count(count)
        if self._bins[bin_name].get(part, 0) < count:
            raise NotEnoughParts(f"bin {bin_name!r} has fewer than {count} of {part}")
        self._change(bin_name, part, -count)

    def merge_bins(self, source, into):
        self._require(source)
        self._require(into)
        if source == into:
            raise ValueError("cannot merge a bin into itself")
        parts = self._bins.pop(source)
        for part, count in parts.items():
            self._change(into, part, count)
        return sum(parts.values())

    def scrap_bin(self, name):
        self._require(name)
        return sum(self._bins.pop(name).values())

    def get_count(self, bin_name, part):
        self._require(bin_name)
        return self._bins[bin_name].get(part, 0)

    def get_parts(self, bin_name):
        self._require(bin_name)
        return sorted(self._bins[bin_name])

    def get_bins(self):
        return list(self._bins)

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
