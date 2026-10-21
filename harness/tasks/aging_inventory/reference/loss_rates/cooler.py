"""Flower cooler whose daily freshness losses can be set for the whole cooler
and for single batches.

Correct solution for aging_inventory after c_loss_rates.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from cooler import FlowerCooler
    cooler = FlowerCooler(daily_loss=1)
    cooler.add_batch("fern", 20, 4, late_loss=3)
    cooler.end_day()
    cooler.get_losses("fern")      # -> (1, 3)
"""


class CoolerError(Exception):
    pass


MAX_FRESHNESS = 30
DEFAULT_DAILY_LOSS = 2  # freshness lost per day while a batch has days left
DEFAULT_LATE_LOSS = 5  # freshness lost per day once it has none


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


def check_optional_loss(value, what):
    if value is not None:
        check_int(value, what, 0)


class FlowerCooler:
    def __init__(self, daily_loss=DEFAULT_DAILY_LOSS, late_loss=DEFAULT_LATE_LOSS):
        check_int(daily_loss, "daily_loss", 0)
        check_int(late_loss, "late_loss", 0)
        self._losses = (daily_loss, late_loss)
        # batch id -> {"freshness", "days_left", "losses"}, in the order
        # added. "losses" holds the batch's own (daily, late) values, None
        # where it uses the cooler's.
        self._batches = {}

    def add_batch(self, batch_id, freshness, days_left, daily_loss=None, late_loss=None):
        check_name(batch_id, "batch id")
        check_int(freshness, "freshness", 0, MAX_FRESHNESS)
        check_int(days_left, "days_left", 0)
        check_optional_loss(daily_loss, "daily_loss")
        check_optional_loss(late_loss, "late_loss")
        if batch_id in self._batches:
            raise CoolerError(f"batch {batch_id!r} is already in the cooler")
        self._batches[batch_id] = {
            "freshness": freshness,
            "days_left": days_left,
            "losses": (daily_loss, late_loss),
        }

    def remove_batch(self, batch_id):
        self._require(batch_id)
        del self._batches[batch_id]

    def end_day(self):
        for batch in self._batches.values():
            daily, late = self._losses_of(batch)
            loss = daily if batch["days_left"] > 0 else late
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

    def get_losses(self, batch_id):
        self._require(batch_id)
        return self._losses_of(self._batches[batch_id])

    def set_losses(self, batch_id, daily_loss, late_loss):
        self._require(batch_id)
        check_int(daily_loss, "daily_loss", 0)
        check_int(late_loss, "late_loss", 0)
        self._batches[batch_id]["losses"] = (daily_loss, late_loss)

    # -- helpers --

    def _require(self, batch_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(batch_id, str) or batch_id not in self._batches:
            raise KeyError(batch_id)

    def _losses_of(self, batch):
        """The batch's own values, else the cooler's."""
        return tuple(
            own if own is not None else default
            for own, default in zip(batch["losses"], self._losses)
        )
