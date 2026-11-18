"""Canal locks: a network of locks joined by channels.

Correct solution for canal_locks before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from canals import CanalNetwork
    network = CanalNetwork()
    network.add_lock("upper")
    network.add_lock("lower")
    network.connect("upper", "lower")
"""


class CanalError(Exception):
    pass


class CanalNetwork:
    def __init__(self):
        # lock name -> names of the locks joined to it, in the order the
        # channels were added; the locks are kept in the order they were added.
        self._channels = {}

    def add_lock(self, name):
        if name in self._channels:
            raise CanalError(f"lock name {name!r} is already used")
        self._channels[name] = []

    def connect(self, first, second):
        self._require_pair(first, second)
        if second in self._channels[first]:
            raise CanalError(f"{first!r} and {second!r} are already joined")
        self._join(first, second)

    def disconnect(self, first, second):
        self._require_pair(first, second)
        if second not in self._channels[first]:
            raise CanalError(f"{first!r} and {second!r} are not joined")
        self._split(first, second)

    def close_lock(self, name):
        self._require(name)
        joined = self._channels.pop(name)
        for other in joined:
            self._channels[other].remove(name)
        return len(joined)

    def merge_locks(self, source, into):
        self._require_pair(source, into)
        added = 0
        for other in list(self._channels[source]):
            self._split(source, other)
            if other != into and other not in self._channels[into]:
                self._join(into, other)
                added += 1
        del self._channels[source]
        return added

    def get_locks(self):
        return list(self._channels)

    def get_channels(self, name):
        self._require(name)
        return list(self._channels[name])

    def _require(self, name):
        if not isinstance(name, str) or name not in self._channels:
            raise KeyError(name)

    def _require_pair(self, first, second):
        self._require(first)
        self._require(second)
        if first == second:
            raise ValueError("a channel joins two different locks")

    def _join(self, first, second):
        self._channels[first].append(second)
        self._channels[second].append(first)

    def _split(self, first, second):
        self._channels[first].remove(second)
        self._channels[second].remove(first)
