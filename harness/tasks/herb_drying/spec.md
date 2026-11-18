# Herb drying

Write a module `drying.py` that keeps track of the herbs hung up to dry in a
drying room: how many bundles of each herb hang on each rack, as bundles
are hung, taken down and shifted from one rack to another.

## Interface

```python
class DryingError(Exception): ...


class NotEnoughBundles(DryingError): ...


class DryingRoom:
    def __init__(self): ...
    def add_rack(self, name: str) -> None: ...
    def hang(self, rack: str, herb: str, count: int) -> None: ...
    def take_down(self, rack: str, herb: str, count: int) -> None: ...
    def shift_all(self, from_rack: str, to_rack: str) -> int: ...
    def dismantle_rack(self, name: str, into: str) -> int: ...
    def get_count(self, rack: str, herb: str) -> int: ...
    def get_herbs(self, rack: str) -> list[str]: ...
    def get_racks(self) -> list[str]: ...
```

Rack names and herbs are non-empty strings, and counts are `int`.

## Racks

- `add_rack(name)` adds an empty rack. A name that is already in use raises
  `DryingError`.
- `get_racks()` returns the names of the racks in use, in the order they
  were added.
- Every other method raises `KeyError` when given a rack name that is not
  in use: one that was never added, or one that was dismantled.

## Bundles

- `hang(rack, herb, count)` adds `count` bundles of `herb` to the rack. The
  count must be greater than 0; otherwise `hang` raises `ValueError`.
- `take_down(rack, herb, count)` takes `count` bundles of `herb` away.
- A rack never holds fewer than 0 bundles of a herb: a `take_down` of more
  bundles than the rack has of that herb (including a herb it has none of)
  raises `NotEnoughBundles`.
- `get_count(rack, herb)` returns how many bundles of `herb` hang on the
  rack: 0 for a herb that has never been there, or whose bundles have all
  been taken down or moved away.
- `get_herbs(rack)` returns the herbs that have at least one bundle on the
  rack, in alphabetical order.

## Moving every bundle

- `shift_all(from_rack, to_rack)` moves every bundle of every herb from
  `from_rack` to `to_rack` and returns how many bundles it moved in total.
  Afterwards `from_rack` is empty but still in use.
- `dismantle_rack(name, into)` moves every bundle of every herb from rack
  `name` to rack `into`, then removes rack `name`: it is no longer listed by
  `get_racks()`, and every method treats it as not in use. It returns how
  many bundles it moved in total (0 if the rack was empty). The name is
  then free: `add_rack` may add it again later, as a new empty rack.
- `shift_all` raises `ValueError` when both racks are the same.

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`). For example, if `shift_all` calls
`take_down` (which may delete a herb whose bundles are all gone) inside
`for herb, count in herbs.items():`, loop over a copy instead:
`for herb, count in list(herbs.items()):`.

## Errors

A failed call has no effect: if a method raises, every count and the list
of racks are unchanged.

When a call has more than one problem, which of the errors is raised is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as
`1.5`, `"3"`, `True` or `None`), and herbs or rack names that are not
non-empty strings (such as `""`, `None` or `1`), wherever they are passed.
It also includes what `take_down` does with a count of 0 or less, what
`shift_all` does when `from_rack` holds no bundles, what `dismantle_rack`
does when both racks are the same, which error is raised when a call has
more than one problem, what happens
if a returned list is changed, the text of error messages, saving the room
to a file, and use from several threads.
