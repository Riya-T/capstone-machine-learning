"""Canal locks with undo and channel limits.

Correct solution for canal_locks after c_undo and c_limits.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from canals import CanalNetwork
    network = CanalNetwork()
    network.add_lock("upper")
    network.set_max_channels("upper", 2)
    network.undo()  # upper has no limit again
"""


class CanalError(Exception):
    pass


class TooManyChannels(CanalError):
    pass


def check_limit(limit):
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"limit must be None or an int of 1 or more, got {limit!r}")


class CanalNetwork:
    def __init__(self):
        # lock name -> names of the locks joined to it, in the order the
        # channels were added; the locks are kept in the order they were added.
        self._channels = {}
        self._limits = {}  # lock name -> most channels allowed; missing = no limit
        self._history = []  # snapshots of the state just before each recorded call

    def add_lock(self, name):
        if name in self._channels:
            raise CanalError(f"lock name {name!r} is already used")
        self._save()
        self._channels[name] = []

    def connect(self, first, second):
        self._require_pair(first, second)
        if second in self._channels[first]:
            raise CanalError(f"{first!r} and {second!r} are already joined")
        for lock in (first, second):
            self._require_room(lock, len(self._channels[lock]) + 1)
        self._save()
        self._join(first, second)

    def disconnect(self, first, second):
        self._require_pair(first, second)
        if second not in self._channels[first]:
            raise CanalError(f"{first!r} and {second!r} are not joined")
        self._save()
        self._split(first, second)

    def close_lock(self, name):
        self._require(name)
        self._save()
        joined = self._channels.pop(name)
        self._limits.pop(name, None)
        for other in joined:
            self._channels[other].remove(name)
        return len(joined)

    def merge_locks(self, source, into):
        self._require_pair(source, into)
        moving = self._channels[source]
        new = [other for other in moving if other != into and other not in self._channels[into]]
        dropped = 1 if into in moving else 0
        self._require_room(into, len(self._channels[into]) - dropped + len(new))
        self._save()
        for other in list(moving):
            self._split(source, other)
            if other in new:
                self._join(into, other)
        del self._channels[source]
        self._limits.pop(source, None)
        return len(new)

    def set_max_channels(self, name, limit):
        self._require(name)
        check_limit(limit)
        if limit is not None and limit < len(self._channels[name]):
            raise ValueError(f"lock {name!r} already has more than {limit} channels")
        self._save()
        if limit is None:
            self._limits.pop(name, None)
        else:
            self._limits[name] = limit

    def get_max_channels(self, name):
        self._require(name)
        return self._limits.get(name)

    def undo(self):
        if not self._history:
            raise CanalError("nothing to undo")
        self._channels, self._limits = self._history.pop()

    def get_locks(self):
        return list(self._channels)

    def get_channels(self, name):
        self._require(name)
        return list(self._channels[name])

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        channels = {name: list(joined) for name, joined in self._channels.items()}
        self._history.append((channels, dict(self._limits)))

    def _require_room(self, name, count):
        limit = self._limits.get(name)
        if limit is not None and count > limit:
            raise TooManyChannels(f"lock {name!r} may have at most {limit} channels")

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
