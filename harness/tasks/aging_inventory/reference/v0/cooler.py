"""Flower cooler: batches of cut flowers whose freshness drops a little at the
end of every day, faster once they are past their sell-by day.

Correct solution for aging_inventory before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cooler import FlowerCooler
    cooler = FlowerCooler()
    cooler.add_batch("tulips", 12, 1)
    cooler.end_day()
    cooler.get_freshness("tulips")    # -> 10
"""


class CoolerError(Exception):
    pass


MAX_FRESHNESS = 30
DAILY_LOSS = 2  # freshness lost per day while a batch has days left
LATE_LOSS = 5  # freshness lost per day once it has none


def check_id(value):
    if not isinstance(value, str) or not value:
        raise ValueError(f"batch id must be a non-empty str, got {value!r}")


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

    def add_batch(self, batch_id, freshness, days_left):
        check_id(batch_id)
        check_int(freshness, "freshness", 0, MAX_FRESHNESS)
        check_int(days_left, "days_left", 0)
        if batch_id in self._batches:
            raise CoolerError(f"batch {batch_id!r} is already in the cooler")
        self._batches[batch_id] = {"freshness": freshness, "days_left": days_left}

    def remove_batch(self, batch_id):
        self._require(batch_id)
        del self._batches[batch_id]

    def end_day(self):
        for batch in self._batches.values():
            loss = DAILY_LOSS if batch["days_left"] > 0 else LATE_LOSS
            batch["freshness"] = max(0, batch["freshness"] - loss)
            batch["days_left"] -= 1

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

    def _require(self, batch_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(batch_id, str) or batch_id not in self._batches:
            raise KeyError(batch_id)
