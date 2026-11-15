"""Lab freezers with a capacity per freezer, which can also be locked.

Planted bug (after c_capacity and c_lock): locks were added correctly, but
remove_freezer was rewritten to move the samples one at a time with move(),
so when they don't all fit it raises Full after moving the ones that did,
instead of moving none.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from freezers import Freezers
    lab = Freezers()
    lab.add_freezer("F1")
    lab.set_capacity("F1", 100)
    lab.store("F1", "blood-001")
    lab.lock("F1")
"""


class FreezerError(Exception):
    pass


class Full(FreezerError):
    pass


class Locked(FreezerError):
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
        self._capacity = {}  # freezer id -> most samples it may hold, or None
        self._locked = set()  # ids of locked freezers

    # --- freezers ---------------------------------------------------------

    def add_freezer(self, freezer_id):
        if freezer_id in self._contents:
            raise FreezerError(f"freezer {freezer_id!r} is already in use")
        self._contents[freezer_id] = []
        self._capacity[freezer_id] = None

    def remove_freezer(self, freezer_id, to_freezer):
        self._require_pair(freezer_id, to_freezer)
        self._require_unlocked(freezer_id, to_freezer)
        moved = 0
        for sample_id in list(self._contents[freezer_id]):
            self.move(sample_id, to_freezer)
            moved += 1
        del self._contents[freezer_id]
        return moved

    def set_capacity(self, freezer_id, samples):
        self._require_freezer(freezer_id)
        check_capacity(samples)
        self._capacity[freezer_id] = samples

    def get_capacity(self, freezer_id):
        self._require_freezer(freezer_id)
        return self._capacity[freezer_id]

    def lock(self, freezer_id):
        self._require_freezer(freezer_id)
        self._locked.add(freezer_id)

    def unlock(self, freezer_id):
        self._require_freezer(freezer_id)
        self._locked.discard(freezer_id)

    def get_freezers(self):
        return list(self._contents)

    def get_samples(self, freezer_id):
        self._require_freezer(freezer_id)
        return list(self._contents[freezer_id])

    # --- samples ----------------------------------------------------------

    def store(self, freezer_id, sample_id):
        self._require_freezer(freezer_id)
        self._require_unlocked(freezer_id)
        if sample_id in self._location:
            raise FreezerError(f"sample {sample_id!r} is already stored")
        self._require_room(freezer_id, 1)
        self._contents[freezer_id].append(sample_id)
        self._location[sample_id] = freezer_id

    def discard(self, sample_id):
        freezer_id = self.find(sample_id)
        self._require_unlocked(freezer_id)
        self._contents[freezer_id].remove(sample_id)
        del self._location[sample_id]

    def move(self, sample_id, to_freezer):
        from_freezer = self.find(sample_id)
        self._require_freezer(to_freezer)
        if from_freezer == to_freezer:
            raise ValueError(f"sample {sample_id!r} is already in {to_freezer!r}")
        self._require_unlocked(from_freezer, to_freezer)
        self._require_room(to_freezer, 1)
        self._contents[from_freezer].remove(sample_id)
        self._contents[to_freezer].append(sample_id)
        self._location[sample_id] = to_freezer

    def move_all(self, from_freezer, to_freezer):
        self._require_pair(from_freezer, to_freezer)
        self._require_unlocked(from_freezer, to_freezer)
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

    def _require_unlocked(self, *freezer_ids):
        for freezer_id in freezer_ids:
            if freezer_id in self._locked:
                raise Locked(f"freezer {freezer_id!r} is locked")

    def _require_room(self, freezer_id, count):
        capacity = self._capacity[freezer_id]
        if count == 0 or capacity is None:
            return
        if len(self._contents[freezer_id]) + count > capacity:
            raise Full(f"freezer {freezer_id!r} has no room for {count} more")

    def _move_contents(self, from_freezer, to_freezer):
        """Move every sample, keeping their order, after those in to_freezer;
        all of them or, if they don't all fit, none."""
        samples = self._contents[from_freezer]
        self._require_room(to_freezer, len(samples))
        self._contents[from_freezer] = []
        self._contents[to_freezer].extend(samples)
        for sample_id in samples:
            self._location[sample_id] = to_freezer
        return len(samples)
