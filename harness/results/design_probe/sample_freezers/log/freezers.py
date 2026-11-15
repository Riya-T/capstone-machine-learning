"""Lab freezers: which freezer holds each named sample, in arrival order.

Every successful change is recorded as an operation in self._ops; the
current state (which freezers exist, what each one holds) is what replaying
those operations from the start gives.
"""


class FreezerError(Exception):
    pass


class Freezers:
    def __init__(self):
        self._ops = []  # every successful change, oldest first: (name, *args)
        self._rebuild()

    # --- freezers ---------------------------------------------------------

    def add_freezer(self, freezer_id):
        if freezer_id in self._contents:
            raise FreezerError(f"freezer {freezer_id!r} is already in use")
        return self._record("add_freezer", freezer_id)

    def remove_freezer(self, freezer_id, to_freezer):
        self._require_pair(freezer_id, to_freezer)
        return self._record("remove_freezer", freezer_id, to_freezer)

    def get_freezers(self):
        return list(self._contents)

    def get_samples(self, freezer_id):
        self._require_freezer(freezer_id)
        return list(self._contents[freezer_id])

    # --- samples ----------------------------------------------------------

    def store(self, freezer_id, sample_id):
        self._require_freezer(freezer_id)
        if sample_id in self._location:
            raise FreezerError(f"sample {sample_id!r} is already stored")
        return self._record("store", freezer_id, sample_id)

    def discard(self, sample_id):
        self.find(sample_id)
        return self._record("discard", sample_id)

    def move(self, sample_id, to_freezer):
        from_freezer = self.find(sample_id)
        self._require_freezer(to_freezer)
        if from_freezer == to_freezer:
            raise ValueError(f"sample {sample_id!r} is already in {to_freezer!r}")
        return self._record("move", sample_id, to_freezer)

    def move_all(self, from_freezer, to_freezer):
        self._require_pair(from_freezer, to_freezer)
        return self._record("move_all", from_freezer, to_freezer)

    def find(self, sample_id):
        if not isinstance(sample_id, str) or sample_id not in self._location:
            raise KeyError(sample_id)
        return self._location[sample_id]

    # --- operations -------------------------------------------------------

    def _record(self, *op):
        """Apply a validated operation and add it to the history."""
        result = self._apply(op)
        self._ops.append(op)
        return result

    def _rebuild(self):
        """Recompute the state by replaying every recorded operation."""
        self._contents = {}  # freezer id -> sample ids in arrival order
        self._location = {}  # sample id -> freezer id
        for op in self._ops:
            self._apply(op)

    def _apply(self, op):
        name, *args = op
        if name == "add_freezer":
            (freezer_id,) = args
            self._contents[freezer_id] = []
        elif name == "store":
            freezer_id, sample_id = args
            self._contents[freezer_id].append(sample_id)
            self._location[sample_id] = freezer_id
        elif name == "discard":
            (sample_id,) = args
            self._contents[self._location.pop(sample_id)].remove(sample_id)
        elif name == "move":
            sample_id, to_freezer = args
            self._contents[self._location[sample_id]].remove(sample_id)
            self._contents[to_freezer].append(sample_id)
            self._location[sample_id] = to_freezer
        elif name == "move_all":
            return self._move_contents(*args)
        elif name == "remove_freezer":
            freezer_id, to_freezer = args
            moved = self._move_contents(freezer_id, to_freezer)
            del self._contents[freezer_id]
            return moved
        return None

    # --- helpers ----------------------------------------------------------

    def _require_freezer(self, freezer_id):
        if not isinstance(freezer_id, str) or freezer_id not in self._contents:
            raise KeyError(freezer_id)

    def _require_pair(self, from_freezer, to_freezer):
        self._require_freezer(from_freezer)
        self._require_freezer(to_freezer)
        if from_freezer == to_freezer:
            raise ValueError("the two freezers must be different")

    def _move_contents(self, from_freezer, to_freezer):
        """Move every sample, keeping their order, after those in to_freezer."""
        samples = self._contents[from_freezer]
        self._contents[from_freezer] = []
        self._contents[to_freezer].extend(samples)
        for sample_id in samples:
            self._location[sample_id] = to_freezer
        return len(samples)
