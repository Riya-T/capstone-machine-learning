# Wine cellar

Write a module `cellar.py` that keeps track of the bottles in a wine
cellar: how many bottles of each vintage are in each rack, as bottles are
stored, taken out, and moved from rack to rack.

## Interface

```python
class CellarError(Exception): ...


class NotEnoughBottles(CellarError): ...


class Cellar:
    def __init__(self): ...
    def add_rack(self, name: str) -> None: ...
    def store(self, rack: str, vintage: int, count: int) -> None: ...
    def take(self, rack: str, vintage: int, count: int) -> None: ...
    def relocate_all(self, from_rack: str, to_rack: str) -> int: ...
    def decommission_rack(self, name: str, into: str) -> int: ...
    def get_count(self, rack: str, vintage: int) -> int: ...
    def get_vintages(self, rack: str) -> list[int]: ...
    def get_racks(self) -> list[str]: ...
```

Rack names are non-empty strings. A vintage is a year, such as `2015`, and
counts are `int`.

## Racks

- `add_rack(name)` adds an empty rack. A name that is already in use raises
  `CellarError`.
- `get_racks()` returns the names of the racks in use, in the order they
  were added.
- Every other method raises `KeyError` when given a rack name that is not
  in use: one that was never added, or one that was decommissioned.

## Bottles

- The count given to `store` must be greater than 0; otherwise `store`
  raises `ValueError`.
- `store(rack, vintage, count)` puts `count` bottles of `vintage` into the
  rack. `take(rack, vintage, count)` takes them out of the rack. Taking more
  bottles of a vintage than the rack has (including a vintage it has none
  of) raises `NotEnoughBottles`.
- `relocate_all(from_rack, to_rack)` moves every bottle of every vintage
  from `from_rack` to `to_rack`, and returns how many bottles it moved in
  total. Afterwards `from_rack` is empty but still in use. If `from_rack`
  is empty, nothing changes and it returns 0.
- `decommission_rack(name, into)` moves every bottle of every vintage from
  rack `name` to rack `into`, then takes rack `name` out of use: it is
  removed from `get_racks()`, and every method treats it as not in use. It
  returns how many bottles it moved in total (0 if the rack was empty). The
  name is then free: `add_rack` may add it again later, as a new empty rack
  at the end of `get_racks()`.
- `relocate_all` and `decommission_rack` raise `ValueError` when both racks
  are the same.
- `get_count(rack, vintage)` returns how many bottles of `vintage` are in
  the rack: 0 for a vintage that has never been there, or whose bottles
  have all been taken or moved out.
- `get_vintages(rack)` returns the vintages that have bottles in the rack,
  oldest first. Whether it still lists a vintage whose bottles have all
  been taken or moved out is unspecified.

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError: dictionary changed size during
iteration`). That includes a loop over a rack's bottles that calls `take`
or `store`, or anything else that adds or deletes a vintage of that rack;
in such a loop, loop over a copy such as `list(bottles.items())`.

## Errors

A failed call has no effect: if a method raises, every count and the list
of racks are unchanged.

When a call has more than one problem, which error it raises is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts or vintages that are not `int`
(such as `1.5`, `"3"`, `True` or `None`), and rack names that are not
non-empty strings (such as `""`, `None` or `1`), wherever they are passed.
It also includes a count of 0 or less passed to `take`, whether
`get_vintages` lists vintages that have no bottles left, which error a
call with several problems raises, what happens if a returned list is
changed, the text of error messages, saving
the cellar to a file, and use from several threads.
