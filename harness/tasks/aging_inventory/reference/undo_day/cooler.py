"""Flower cooler where ended days can be taken back.

Correct solution for aging_inventory after c_undo_day.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cooler import FlowerCooler
    cooler = FlowerCooler()
    cooler.add_batch("fern", 20, 4)
    cooler.end_day()
    cooler.undo_day()
"""


class CoolerError(Exception):
    pass


MAX_FRESHNESS = 30
DAILY_LOSS = 2  # freshness lost per day while a batch has days left
LATE_LOSS = 5  # freshness lost per day once it has none


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_int(value, what, low, high=None):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < low
        or (high is not None and value > high)
    ):
        raise ValueError(f"{what} out of range: {value!r}")


class FlowerCooler:
    def __init__(self):
        # batch id -> {"freshness", "days_left"}, in the order added
        self._batches = {}
        # One entry per ended day not taken back, oldest first: a list of
        # (batch id, batch record, freshness before, days left before).
        self._days = []

    def add_batch(self, batch_id, freshness, days_left):
        check_name(batch_id, "batch id")
        check_int(freshness, "freshness", 0, MAX_FRESHNESS)
        check_int(days_left, "days_left", 0)
        if batch_id in self._batches:
            raise CoolerError(f"batch {batch_id!r} is already in the cooler")
        self._batches[batch_id] = {"freshness": freshness, "days_left": days_left}

    def remove_batch(self, batch_id):
        self._require(batch_id)
        del self._batches[batch_id]

    def end_day(self):
        before = []
        for batch_id, batch in self._batches.items():
            before.append((batch_id, batch, batch["freshness"], batch["days_left"]))
            loss = DAILY_LOSS if batch["days_left"] > 0 else LATE_LOSS
            batch["freshness"] = max(0, batch["freshness"] - loss)
            batch["days_left"] -= 1
        self._days.append(before)

    def undo_day(self):
        if not self._days:
            raise CoolerError("there is no ended day to take back")
        for batch_id, batch, freshness, days_left in self._days.pop():
            # Only the very record that day changed: not a removed batch, and
            # not a newer batch that reuses its id.
            if self._batches.get(batch_id) is batch:
                batch["freshness"] = freshness
                batch["days_left"] = days_left

    def get_day(self):
        return len(self._days)

    def get_freshness(self, batch_id):
        self._require(batch_id)
        return self._batches[batch_id]["freshness"]

    def get_days_left(self, batch_id):
        self._require(batch_id)
        return self._batches[batch_id]["days_left"]

    def get_batches(self):
        return list(self._batches)

    def get_wilted(self):
        return [b for b, batch in self._batches.items() if batch["freshness"] == 0]

    # -- helpers --

    def _require(self, batch_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(batch_id, str) or batch_id not in self._batches:
            raise KeyError(batch_id)
