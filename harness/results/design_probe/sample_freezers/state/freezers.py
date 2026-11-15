"""Lab freezers: which freezer holds each named sample, in arrival order."""


class FreezerError(Exception):
    pass


class Freezers:
    def __init__(self):
        # freezer id -> sample ids in the order they arrived; the dict keeps
        # the freezers in the order they were added
        self._contents = {}
        self._location = {}  # sample id -> id of the freezer holding it

    # --- freezers ---------------------------------------------------------

    def add_freezer(self, freezer_id):
        if freezer_id in self._contents:
            raise FreezerError(f"freezer {freezer_id!r} is already in use")
        self._contents[freezer_id] = []

    def remove_freezer(self, freezer_id, to_freezer):
        self._require_pair(freezer_id, to_freezer)
        moved = self._move_contents(freezer_id, to_freezer)
        del self._contents[freezer_id]
        return moved

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
        self._contents[freezer_id].append(sample_id)
        self._location[sample_id] = freezer_id

    def discard(self, sample_id):
        freezer_id = self.find(sample_id)
        self._contents[freezer_id].remove(sample_id)
        del self._location[sample_id]

    def move(self, sample_id, to_freezer):
        from_freezer = self.find(sample_id)
        self._require_freezer(to_freezer)
        if from_freezer == to_freezer:
            raise ValueError(f"sample {sample_id!r} is already in {to_freezer!r}")
        self._contents[from_freezer].remove(sample_id)
        self._contents[to_freezer].append(sample_id)
        self._location[sample_id] = to_freezer

    def move_all(self, from_freezer, to_freezer):
        self._require_pair(from_freezer, to_freezer)
        return self._move_contents(from_freezer, to_freezer)

    def find(self, sample_id):
        # Non-str ids are never stored, so they count as "not stored" too.
        if not isinstance(sample_id, str) or sample_id not in self._location:
            raise KeyError(sample_id)
        return self._location[sample_id]

    # --- helpers ----------------------------------------------------------

    def _require_freezer(self, freezer_id):
        # Non-str ids are never added, so they count as "not in use" too.
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
