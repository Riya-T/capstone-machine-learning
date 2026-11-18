# Mail bins

Write a module `sorting.py` for a parcel sorting room. Parcels are dropped
into named sorting bins and wait there in the order they arrived: the
parcel that arrived first is at the front of its bin and is picked first.

## Interface

```python
class SortingError(Exception): ...


class SortingRoom:
    def __init__(self): ...
    def add_bin(self, name: str) -> None: ...
    def drop(self, bin_name: str, parcel: str) -> None: ...
    def pick(self, bin_name: str) -> str: ...
    def recall(self, parcel: str) -> str: ...
    def empty_bin_into(self, from_bin: str, to_bin: str) -> int: ...
    def close_bin(self, name: str, into: str) -> int: ...
    def get_parcels(self, bin_name: str) -> list[str]: ...
    def get_bins(self) -> list[str]: ...
```

Bin names and parcel names are non-empty strings.

## Bins

- `add_bin(name)` adds an empty bin. A name that is already in use raises
  `SortingError`.
- `get_bins()` returns the names of the bins in use, in the order they were
  added.
- Every other method that takes a bin name raises `KeyError` when that bin
  is not in use: one that was never added, or one that was closed.

## Parcels

- A parcel is in at most one bin at a time. `drop(bin_name, parcel)` puts
  the parcel at the back of the bin. Dropping a parcel that is already in
  a bin (this one or any other) raises `SortingError`.
- `get_parcels(bin_name)` returns the parcels in the bin from front to
  back, that is, in the order they arrived in the bin.
- `pick(bin_name)` removes the parcel at the front of the bin and returns
  its name. Picking from an empty bin raises `SortingError`.
- `recall(parcel)` removes the parcel from the bin that holds it, wherever
  it is in that bin, and returns the name of that bin. The other parcels
  keep their order. A parcel that is in no bin raises `SortingError`.
- A parcel that was picked or recalled has left the room: it may be
  dropped again later, as a new arrival at the back of a bin.
- `empty_bin_into(from_bin, to_bin)` moves every parcel from `from_bin` to
  the back of `to_bin`, keeping their order, behind the parcels already in
  `to_bin`. It returns how many parcels it moved. Afterwards `from_bin` is
  empty but still in use. If `from_bin` is empty, nothing changes and it
  returns 0.
- `close_bin(name, into)` moves every parcel from bin `name` to the back of
  bin `into` in the same way, then closes bin `name`: it is removed from
  `get_bins()`, and every method treats it as not in use. It returns how
  many parcels it moved. An empty bin is closed too (nothing moves and it
  returns 0). The name is then free:
  `add_bin` may add it again later, as a new empty bin at the end of
  `get_bins()`.
- `empty_bin_into` and `close_bin` raise `ValueError` when both bins are
  the same.

## Errors

A failed call has no effect: if a method raises, the list of bins and the
parcels in every bin, in their order, are unchanged.

When a call has more than one problem, which error it raises is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes bin or parcel names that are not non-empty strings (such as `""`,
`None` or `1`), which error a call with several problems raises, what
happens if a returned list is changed, the text of error messages, saving
the room to a file, and use from several threads.
