# Spare parts

Write a module `parts.py` that keeps track of a spare-parts store: how many
parts of each part number are in each bin, as parts are stocked and taken,
and as bins are merged or scrapped.

## Interface

```python
class StoreError(Exception): ...


class NotEnoughParts(StoreError): ...


class PartsStore:
    def __init__(self): ...
    def add_bin(self, name: str) -> None: ...
    def stock(self, bin_name: str, part: str, count: int) -> None: ...
    def take(self, bin_name: str, part: str, count: int) -> None: ...
    def merge_bins(self, source: str, into: str) -> int: ...
    def scrap_bin(self, name: str) -> int: ...
    def get_count(self, bin_name: str, part: str) -> int: ...
    def get_parts(self, bin_name: str) -> list[str]: ...
    def get_bins(self) -> list[str]: ...
```

Bin names and part numbers are non-empty strings, and counts are `int`.

## Bins

- `add_bin(name)` adds an empty bin. A name that is already in use raises
  `StoreError`.
- `get_bins()` returns the names of the bins in use, in the order they were
  added.
- Every other method raises `KeyError` when given a bin name that is not in
  use: one that was never added, or one that was removed by `merge_bins` or
  `scrap_bin`.

## Parts

- A count given to `stock` must be greater than 0; otherwise `ValueError`
  is raised. What `take` does with a count of 0 or less is unspecified.
- `stock(bin_name, part, count)` adds `count` parts of that part number to
  the bin. `take(bin_name, part, count)` takes them out.
- A bin never holds fewer than 0 parts of a part number: a `take` of more
  parts than the bin has of that part number (including a part number it
  has none of) raises `NotEnoughParts`.
- `get_count(bin_name, part)` returns how many parts of that part number
  are in the bin: 0 for a part number that has never been there, or whose
  parts have all been taken.
- `get_parts(bin_name)` returns the part numbers that have at least one
  part in the bin, in alphabetical order.

## Merging and scrapping bins

- `merge_bins(source, into)` moves every part of every part number from bin
  `source` to bin `into` (adding to the counts `into` already has), then
  removes bin `source`: it is no longer in `get_bins()`, and every method
  treats it as not in use. It returns how many parts it moved in total (0
  if `source` was empty). Merging a bin into itself raises `ValueError`.
- `scrap_bin(name)` removes bin `name` together with all its parts. It
  returns how many parts were thrown away in total (0 if the bin was
  empty).

## Errors

A failed call has no effect: if a method raises, every count and the list
of bins are unchanged. When a call has more than one problem, which of its
errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type (counts that are not `int`, such as `1.5`
or `True`; names or part numbers that are not non-empty strings), which
error is raised when a call has several problems, whether the name of a
removed bin may be added again, what happens if a returned list is changed,
the text of error messages, saving the store to a file, and use from
several threads.
