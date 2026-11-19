"""Mail bins: parcels waiting in sorting bins in arrival order.

Planted bug (initial version): drop only checks the bin it drops into, so a
parcel already waiting in another bin can be dropped a second time and end
up in two bins. The public checks only drop a parcel twice into the same
bin, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from sorting import SortingRoom
    room = SortingRoom()
    room.add_bin("east")
    room.drop("east", "NY-1")
    room.drop("east", "LA-2")
    room.pick("east")  # "NY-1"
"""


class SortingError(Exception):
    pass


class SortingRoom:
    def __init__(self):
        # bin name -> list of parcels, front first, in the order bins were added
        self._bins = {}

    def add_bin(self, name):
        if name in self._bins:
            raise SortingError(f"bin name {name!r} is already used")
        self._bins[name] = []

    def drop(self, bin_name, parcel):
        parcels = self._parcels(bin_name)
        if parcel in parcels:
            raise SortingError(f"parcel {parcel!r} is already in a bin")
        parcels.append(parcel)

    def pick(self, bin_name):
        parcels = self._parcels(bin_name)
        if not parcels:
            raise SortingError(f"bin {bin_name!r} is empty")
        return parcels.pop(0)

    def recall(self, parcel):
        bin_name = self._bin_of(parcel)
        if bin_name is None:
            raise SortingError(f"parcel {parcel!r} is in no bin")
        self._bins[bin_name].remove(parcel)
        return bin_name

    def empty_bin_into(self, from_bin, to_bin):
        self._check_pair(from_bin, to_bin)
        return self._move_everything(from_bin, to_bin)

    def close_bin(self, name, into):
        self._check_pair(name, into)
        moved = self._move_everything(name, into)
        del self._bins[name]
        return moved

    def get_parcels(self, bin_name):
        return list(self._parcels(bin_name))

    def get_bins(self):
        return list(self._bins)

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
