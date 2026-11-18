"""Trail huts with routes and undo.

Planted regression bug (sequence s2, step 2): when add_route was rewritten
to save the map for undo, it lost the check against trails planned
earlier in the same route, so a route that repeats one of its own trails
adds it twice. The undo tests never call add_route; the route tests from
step 1 do.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from trails import TrailMap
    trails = TrailMap()
    trails.add_hut("Alpe")
    trails.add_hut("Berg")
    trails.add_trail("Alpe", "Berg")
    trails.undo()  # no trail again
"""


class TrailError(Exception):
    pass


class TrailMap:
    def __init__(self):
        # hut name -> the huts joined to it, in the order those trails were
        # added; the huts themselves are kept in the order they were added.
        self._neighbors = {}
        self._undo_stack = []  # copies of the map as it was before each call

    def add_hut(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("hut name must be a non-empty str")
        if name in self._neighbors:
            raise TrailError(f"hut name {name!r} is already used")
        self._save()
        self._neighbors[name] = []

    def add_trail(self, hut_a, hut_b):
        self._require(hut_a)
        self._require(hut_b)
        if hut_a == hut_b:
            raise ValueError("a trail joins two different huts")
        if hut_b in self._neighbors[hut_a]:
            raise TrailError(f"{hut_a!r} and {hut_b!r} are already joined")
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
        return removed

    def merge_huts(self, hut, into_hut):
        self._require(hut)
        self._require(into_hut)
        if hut == into_hut:
            raise ValueError("cannot merge a hut into itself")
        self._save()
        for other in list(self._neighbors[hut]):
            self._unlink(hut, other)
            if other != into_hut and other not in self._neighbors[into_hut]:
                self._link(into_hut, other)
        del self._neighbors[hut]

    def add_route(self, huts):
        # Check every trail first, then add them all as one recorded call.
        pairs = list(zip(huts, huts[1:]))
        for hut_a, hut_b in pairs:
            self._require(hut_a)
            self._require(hut_b)
            if hut_a == hut_b:
                raise ValueError("a trail joins two different huts")
            if hut_b in self._neighbors[hut_a]:
                raise TrailError(f"{hut_a!r} and {hut_b!r} are already joined")
        self._save()
        for hut_a, hut_b in pairs:
            self._link(hut_a, hut_b)

    def undo(self):
        if not self._undo_stack:
            raise TrailError("nothing to undo")
        self._neighbors = self._undo_stack.pop()

    def get_huts(self):
        return list(self._neighbors)

    def get_neighbors(self, hut):
        self._require(hut)
        return list(self._neighbors[hut])

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({hut: list(others) for hut, others in self._neighbors.items()})

    def _require(self, hut):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(hut, str) or hut not in self._neighbors:
            raise KeyError(hut)

    def _link(self, hut_a, hut_b):
        self._neighbors[hut_a].append(hut_b)
        self._neighbors[hut_b].append(hut_a)

    def _unlink(self, hut_a, hut_b):
        self._neighbors[hut_a].remove(hut_b)
        self._neighbors[hut_b].remove(hut_a)
