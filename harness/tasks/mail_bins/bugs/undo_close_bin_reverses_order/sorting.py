"""Mail bins with parcel lookups and undo.

Planted bug (after c_lookup and c_undo): undo was added correctly, but
close_bin was rewritten to pop the closed bin's parcels one at a time into
the receiving bin, which reverses their order.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from sorting import SortingRoom
    room = SortingRoom()
    room.add_bin("east")
    room.drop("east", "NY-1")
    room.pick("east")  # "NY-1"
    room.undo()  # NY-1 is back at the front of east
"""


class SortingError(Exception):
    pass


class SortingRoom:
    def __init__(self):
        # bin name -> list of parcels, front first, in the order bins were added
        self._bins = {}
        self._undo_stack = []  # copies of the bins as they were before each call

    def add_bin(self, name):
        if name in self._bins:
            raise SortingError(f"bin name {name!r} is already used")
        self._save()
        self._bins[name] = []

    def drop(self, bin_name, parcel):
        parcels = self._parcels(bin_name)
        if self._bin_of(parcel) is not None:
            raise SortingError(f"parcel {parcel!r} is already in a bin")
        self._save()
        parcels.append(parcel)

    def pick(self, bin_name):
        parcels = self._parcels(bin_name)
        if not parcels:
            raise SortingError(f"bin {bin_name!r} is empty")
        self._save()
        return parcels.pop(0)

    def recall(self, parcel):
        bin_name = self._bin_of(parcel)
        if bin_name is None:
            raise SortingError(f"parcel {parcel!r} is in no bin")
        self._save()
        self._bins[bin_name].remove(parcel)
        return bin_name

    def empty_bin_into(self, from_bin, to_bin):
        self._check_pair(from_bin, to_bin)
        self._save()
        return self._move_everything(from_bin, to_bin)

    def close_bin(self, name, into):
        self._check_pair(name, into)
        self._save()
        source = self._bins.pop(name)
        moved = len(source)
        while source:  # takes the parcels off the back, so they arrive reversed
            self._bins[into].append(source.pop())
        return moved

    def undo(self):
        if not self._undo_stack:
            raise SortingError("nothing to undo")
        self._bins = self._undo_stack.pop()

    def get_parcels(self, bin_name):
        return list(self._parcels(bin_name))

    def get_bins(self):
        return list(self._bins)

    def get_bin_of(self, parcel):
        return self._bin_of(parcel)

    def find_parcels(self, prefix, bin_name=None):
        names = list(self._bins) if bin_name is None else [bin_name]
        found = []
        for name in names:
            found += [p for p in self._parcels(name) if p.startswith(prefix)]
        return found

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(parcels) for name, parcels in self._bins.items()})

    def _check_pair(self, from_bin, to_bin):
        self._parcels(from_bin)
        self._parcels(to_bin)
        if from_bin == to_bin:
            raise ValueError("cannot move parcels into the bin they are in")

    def _move_everything(self, from_bin, to_bin):
        source = self._bins[from_bin]
        moved = len(source)
        self._bins[to_bin].extend(source)
        source.clear()
        return moved

    def _parcels(self, bin_name):
        if bin_name not in self._bins:
            raise KeyError(bin_name)
        return self._bins[bin_name]

    def _bin_of(self, parcel):
        for bin_name, parcels in self._bins.items():
            if parcel in parcels:
                return bin_name
        return None
