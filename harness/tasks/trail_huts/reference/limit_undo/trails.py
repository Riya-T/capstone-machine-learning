"""Trail huts with undo and a trail limit per hut.

Correct solution for trail_huts after c_undo and c_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from trails import TrailMap
    trails = TrailMap()
    trails.add_hut("Alpe", max_trails=1)
    trails.add_hut("Berg")
    trails.add_trail("Alpe", "Berg")
    trails.undo()  # no trail again
"""


class TrailError(Exception):
    pass


class TooManyTrails(TrailError):
    pass


def check_limit(max_trails):
    if max_trails is None:
        return
    if isinstance(max_trails, bool) or not isinstance(max_trails, int) or max_trails <= 0:
        raise ValueError(f"max_trails must be None or a positive int, got {max_trails!r}")


class TrailMap:
    def __init__(self):
        # hut name -> the huts joined to it, in the order those trails were
        # added; the huts themselves are kept in the order they were added.
        self._neighbors = {}
        self._limit = {}  # hut name -> most trails allowed, or None
        self._undo_stack = []  # copies of the map as it was before each call

    def add_hut(self, name, max_trails=None):
        if not isinstance(name, str) or not name:
            raise ValueError("hut name must be a non-empty str")
        check_limit(max_trails)
        if name in self._neighbors:
            raise TrailError(f"hut name {name!r} is already used")
        self._save()
        self._neighbors[name] = []
        self._limit[name] = max_trails

    def add_trail(self, hut_a, hut_b):
        self._require(hut_a)
        self._require(hut_b)
        if hut_a == hut_b:
            raise ValueError("a trail joins two different huts")
        if hut_b in self._neighbors[hut_a]:
            raise TrailError(f"{hut_a!r} and {hut_b!r} are already joined")
        self._require_room(hut_a, len(self._neighbors[hut_a]) + 1)
        self._require_room(hut_b, len(self._neighbors[hut_b]) + 1)
        self._save()
        self._link(hut_a, hut_b)

    def remove_trail(self, hut_a, hut_b):
        self._require(hut_a)
        self._require(hut_b)
        if hut_b not in self._neighbors[hut_a]:
            raise TrailError(f"{hut_a!r} and {hut_b!r} are not joined")
        self._save()
        self._unlink(hut_a, hut_b)

    def close_hut(self, hut):
        self._require(hut)
        self._save()
        removed = len(self._neighbors[hut])
        for other in list(self._neighbors[hut]):
            self._unlink(hut, other)
        del self._neighbors[hut]
        del self._limit[hut]
        return removed

    def merge_huts(self, hut, into_hut):
        self._require(hut)
        self._require(into_hut)
        if hut == into_hut:
            raise ValueError("cannot merge a hut into itself")
        into = self._neighbors[into_hut]
        kept = [other for other in into if other != hut]
        gained = [o for o in self._neighbors[hut] if o != into_hut and o not in into]
        self._require_room(into_hut, len(kept) + len(gained))
        self._save()
        for other in list(self._neighbors[hut]):
            self._unlink(hut, other)
            if other != into_hut and other not in self._neighbors[into_hut]:
                self._link(into_hut, other)
        del self._neighbors[hut]
        del self._limit[hut]

    def undo(self):
        if not self._undo_stack:
            raise TrailError("nothing to undo")
        self._neighbors, self._limit = self._undo_stack.pop()

    def get_max_trails(self, hut):
        self._require(hut)
        return self._limit[hut]

    def get_huts(self):
        return list(self._neighbors)

    def get_neighbors(self, hut):
        self._require(hut)
        return list(self._neighbors[hut])

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        neighbors = {hut: list(others) for hut, others in self._neighbors.items()}
        self._undo_stack.append((neighbors, dict(self._limit)))

    def _require(self, hut):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(hut, str) or hut not in self._neighbors:
            raise KeyError(hut)

    def _require_room(self, hut, trails_after):
        limit = self._limit[hut]
        if limit is not None and trails_after > limit:
            raise TooManyTrails(f"hut {hut!r} may have at most {limit} trails")

    def _link(self, hut_a, hut_b):
        self._neighbors[hut_a].append(hut_b)
        self._neighbors[hut_b].append(hut_a)

    def _unlink(self, hut_a, hut_b):
        self._neighbors[hut_a].remove(hut_b)
        self._neighbors[hut_b].remove(hut_a)
