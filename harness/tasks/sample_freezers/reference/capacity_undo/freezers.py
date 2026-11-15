"""Lab freezers with undo and a capacity per freezer.

Correct solution for sample_freezers after c_undo and c_capacity.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from freezers import Freezers
    lab = Freezers()
    lab.add_freezer("F1")
    lab.set_capacity("F1", 100)
    lab.store("F1", "blood-001")
    lab.undo()  # blood-001 is no longer stored
"""


class FreezerError(Exception):
    pass


class Full(FreezerError):
    pass


def check_capacity(samples):
    if samples is None:
        return
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 0:
        raise ValueError(f"capacity must be an int >= 0 or None, got {samples!r}")


class Freezers:
    def __init__(self):
        # freezer id -> sample ids in the order they arrived; the dict keeps
        # the freezers in the order they were added
        self._contents = {}
        self._location = {}  # sample id -> id of the freezer holding it
        self._snapshots = []  # state before each recorded call, newest last
        # freezer id -> most samples it may hold, or None. Not part of the
        # snapshots: set_capacity is not undone, and a freezer brought back
        # by undo keeps its capacity.
        self._capacity = {}

    # --- freezers ---------------------------------------------------------

    def add_freezer(self, freezer_id):
        if freezer_id in self._contents:
            raise FreezerError(f"freezer {freezer_id!r} is already in use")
        self._save()
        self._contents[freezer_id] = []
        self._capacity[freezer_id] = None

    def remove_freezer(self, freezer_id, to_freezer):
        self._require_pair(freezer_id, to_freezer)
        self._require_room(to_freezer, len(self._contents[freezer_id]))
        self._save()
        moved = self._move_contents(freezer_id, to_freezer)
        del self._contents[freezer_id]
        return moved

    def set_capacity(self, freezer_id, samples):
        self._require_freezer(freezer_id)
        check_capacity(samples)
        self._capacity[freezer_id] = samples

    def get_capacity(self, freezer_id):
        self._require_freezer(freezer_id)
        return self._capacity[freezer_id]

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
        self._require_room(freezer_id, 1)
        self._save()
        self._contents[freezer_id].append(sample_id)
        self._location[sample_id] = freezer_id

    def discard(self, sample_id):
        freezer_id = self.find(sample_id)
        self._save()
        self._contents[freezer_id].remove(sample_id)
        del self._location[sample_id]

    def move(self, sample_id, to_freezer):
        from_freezer = self.find(sample_id)
        self._require_freezer(to_freezer)
        if from_freezer == to_freezer:
            raise ValueError(f"sample {sample_id!r} is already in {to_freezer!r}")
        self._require_room(to_freezer, 1)
        self._save()
        self._contents[from_freezer].remove(sample_id)
        self._contents[to_freezer].append(sample_id)
        self._location[sample_id] = to_freezer

    def move_all(self, from_freezer, to_freezer):
        self._require_pair(from_freezer, to_freezer)
        self._require_room(to_freezer, len(self._contents[from_freezer]))
        self._save()
        return self._move_contents(from_freezer, to_freezer)

    def find(self, sample_id):
        # Non-str ids are never stored, so they count as "not stored" too.
        if not isinstance(sample_id, str) or sample_id not in self._location:
            raise KeyError(sample_id)
        return self._location[sample_id]

    # --- undo -------------------------------------------------------------

    def undo(self):
        if not self._snapshots:
            raise FreezerError("nothing to undo")
        self._contents, self._location = self._snapshots.pop()

    def _save(self):
        """Remember the state before a call that is about to succeed."""
        contents = {f: list(samples) for f, samples in self._contents.items()}
        self._snapshots.append((contents, dict(self._location)))

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

    def _require_room(self, freezer_id, count):
        capacity = self._capacity[freezer_id]
        if count == 0 or capacity is None:
            return
        if len(self._contents[freezer_id]) + count > capacity:
            raise Full(f"freezer {freezer_id!r} has no room for {count} more")

    def _move_contents(self, from_freezer, to_freezer):
        """Move every sample, keeping their order, after those in to_freezer."""
        samples = self._contents[from_freezer]
        self._contents[from_freezer] = []
        self._contents[to_freezer].extend(samples)
        for sample_id in samples:
            self._location[sample_id] = to_freezer
        return len(samples)
