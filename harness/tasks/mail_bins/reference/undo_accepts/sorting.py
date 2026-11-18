"""Mail bins with undo and the destinations each bin accepts.

Correct solution for mail_bins after c_undo and c_accepts.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from sorting import SortingRoom
    room = SortingRoom()
    room.add_bin("east")
    room.set_accepts("east", ["NY-"])
    room.drop("east", "NY-1")
    room.undo()  # east is empty again
"""


class SortingError(Exception):
    pass


class NotAccepted(SortingError):
    pass


class SortingRoom:
    def __init__(self):
        # bin name -> list of parcels, front first, in the order bins were added
        self._bins = {}
        self._accepts = {}  # bin name -> set of prefixes; missing = every parcel
        self._undo_stack = []  # (bins, accepts) as they were before each call

    def add_bin(self, name):
        if name in self._bins:
            raise SortingError(f"bin name {name!r} is already used")
        self._save()
        self._bins[name] = []
        self._accepts.pop(name, None)

    def drop(self, bin_name, parcel):
        parcels = self._parcels(bin_name)
        if self._bin_of(parcel) is not None:
            raise SortingError(f"parcel {parcel!r} is already in a bin")
        self._require_accepted(bin_name, [parcel])
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
        self._require_accepted(to_bin, self._bins[from_bin])
        self._save()
        return self._move_everything(from_bin, to_bin)

    def close_bin(self, name, into):
        self._check_pair(name, into)
        self._require_accepted(into, self._bins[name])
        self._save()
        moved = self._move_everything(name, into)
        del self._bins[name]
        self._accepts.pop(name, None)
        return moved

    def set_accepts(self, bin_name, prefixes):
        self._parcels(bin_name)
        if prefixes is not None and (
            not isinstance(prefixes, list)
            or not all(isinstance(p, str) and p for p in prefixes)
        ):
            raise ValueError("prefixes must be None or a list of non-empty str")
        self._save()
        if prefixes is None:
            self._accepts.pop(bin_name, None)
        else:
            self._accepts[bin_name] = set(prefixes)

    def get_accepts(self, bin_name):
        self._parcels(bin_name)
        if bin_name not in self._accepts:
            return None
        return sorted(self._accepts[bin_name])

    def undo(self):
        if not self._undo_stack:
            raise SortingError("nothing to undo")
        self._bins, self._accepts = self._undo_stack.pop()

    def get_parcels(self, bin_name):
        return list(self._parcels(bin_name))

    def get_bins(self):
        return list(self._bins)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        bins = {name: list(parcels) for name, parcels in self._bins.items()}
        accepts = {name: set(prefixes) for name, prefixes in self._accepts.items()}
        self._undo_stack.append((bins, accepts))

    def _check_pair(self, from_bin, to_bin):
        self._parcels(from_bin)
        self._parcels(to_bin)
        if from_bin == to_bin:
            raise ValueError("cannot move parcels into the bin they are in")

    def _require_accepted(self, bin_name, parcels):
        # Every parcel is checked before any moves.
        prefixes = self._accepts.get(bin_name)
        if prefixes is None:
            return
        for parcel in parcels:
            if not any(parcel.startswith(p) for p in prefixes):
                raise NotAccepted(f"bin {bin_name!r} does not accept parcel {parcel!r}")

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
