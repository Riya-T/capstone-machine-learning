# Flower cooler

Write a module `cooler.py` that tracks the batches of cut flowers in a
florist's cold room. Each batch has a freshness score and a number of days
left before it should be sold. At closing time the florist ends the day,
and every batch gets a little less fresh.

## Interface

```python
class CoolerError(Exception): ...


class FlowerCooler:
    def __init__(self): ...
    def add_batch(self, batch_id: str, freshness: int, days_left: int) -> None: ...
    def remove_batch(self, batch_id: str) -> None: ...
    def end_day(self) -> None: ...
    def get_freshness(self, batch_id: str) -> int: ...
    def get_days_left(self, batch_id: str) -> int: ...
    def get_batches(self) -> list[str]: ...
    def get_wilted(self) -> list[str]: ...
```

## Batches

- `add_batch(batch_id, freshness, days_left)` puts a new batch in the
  cooler. An empty id raises `ValueError`. `freshness` must be an `int`
  from 0 to 30 and `days_left` an `int` of 0 or more; anything else raises
  `ValueError`. Adding an id that is already in the cooler raises
  `CoolerError`. Every `ValueError` comes before the `CoolerError`.
- `remove_batch(batch_id)` takes a batch out of the cooler (it was sold or
  thrown away). Its id may be added again later as a new batch.
- `get_batches()` returns the ids of the batches in the cooler, in the
  order they were added.
- `get_freshness(batch_id)` and `get_days_left(batch_id)` return the
  batch's current values.
- Every method except `add_batch` raises `KeyError` when given an id that
  is not in the cooler, including values that are not strings, such as
  `None` or `1`.

## Ending a day

`end_day()` updates every batch in the cooler, each on its own:

1. A batch that still has days left (`days_left` greater than 0) loses 2
   freshness. A batch with no days left (`days_left` 0 or less) loses 5
   freshness instead. The check uses `days_left` as it was before this
   day.
2. Freshness never goes below 0.
3. `days_left` goes down by 1. It keeps going down after 0, so `-3` means
   the batch is three days past its sell-by day.

For example, a batch added with freshness 12 and 1 day left has
freshness 10 and 0 days left after one day, then 5 and -1, then 0 and -2,
then 0 and -3.

`get_wilted()` returns the same ids as `get_batches()`, in the same order,
but keeps only the batches whose freshness is 0 right now. The order in
which batches wilted does not matter. A list of wilted ids built up in
`end_day` gets this wrong (a batch can be added already wilted, and a
removed batch must disappear), so work it out from the batches. So a batch added with freshness 0 is
wilted right away, each wilted batch is listed once, and a removed batch is
no longer listed. Wilted batches stay in the cooler until removed: they are
still in `get_batches()` and still change each day.

A failed call has no effect: if a method raises, every batch is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_batch`, `bool` values for
freshness or days left, what happens if a returned list is changed, the
text of error messages, saving the cooler to a file, and use from several
threads.
