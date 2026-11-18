# Garden beds

Write a module `garden.py` that keeps track of the plants in a garden: how
many plants of each species grow in each bed, as plants are planted, pulled
up and moved from one bed to another.

## Interface

```python
class GardenError(Exception): ...


class NotEnoughPlants(GardenError): ...


class Garden:
    def __init__(self): ...
    def add_bed(self, name: str) -> None: ...
    def plant(self, bed: str, species: str, count: int) -> None: ...
    def pull(self, bed: str, species: str, count: int) -> None: ...
    def transplant_all(self, from_bed: str, to_bed: str) -> int: ...
    def clear_bed(self, name: str, into: str) -> int: ...
    def get_count(self, bed: str, species: str) -> int: ...
    def get_species(self, bed: str) -> list[str]: ...
    def get_beds(self) -> list[str]: ...
```

Bed names and species are non-empty strings, and counts are `int`.

## Beds

- `add_bed(name)` adds an empty bed. A name that is already in use raises
  `GardenError`.
- `get_beds()` returns the names of the beds in use, in the order they were
  added.
- Every other method raises `KeyError` when given a bed name that is not in
  use: one that was never added, or one that was cleared.

## Plants

- `plant(bed, species, count)` adds `count` plants of `species` to the bed.
  The count must be greater than 0; otherwise `ValueError` is raised.
- `pull(bed, species, count)` takes `count` plants of `species` out of the
  bed. Pulling more plants of a species than the bed has (including a
  species it has none of) raises `NotEnoughPlants`.
- `transplant_all(from_bed, to_bed)` moves every plant of every species from
  `from_bed` to `to_bed`, where they are added to any plants of the same
  species already there, and returns how many plants it moved in total.
  Afterwards `from_bed` is empty but still in use. If `from_bed` is already
  empty, nothing changes and it returns 0.
- `clear_bed(name, into)` moves every plant of every species from bed
  `name` into bed `into` (added to any plants of the same species already
  there), then removes bed `name`: it is no longer listed by `get_beds()`,
  and every method treats it as not in use. It returns how many plants it
  moved in total. The other beds keep their order.
- `transplant_all` and `clear_bed` raise `ValueError` when both beds are the
  same.
- `get_count(bed, species)` returns how many plants of `species` are in the
  bed: 0 for a species the bed has none of.
- `get_species(bed)` returns the species that have at least one plant in
  the bed, in alphabetical order. A species whose plants have all gone (by
  `pull`, `transplant_all` or `clear_bed`) is no longer listed.

Python note: a `dict` must not gain or lose keys while a `for` loop runs over
it (Python raises `RuntimeError: dictionary changed size during
iteration`). In `transplant_all` and `clear_bed`, a loop over a bed's plants
that deletes entries from that bed (directly or by calling `pull`) must loop
over a copy such as `list(plants.items())`.

## Errors

When a call has more than one problem (for example a bed that is not in use
and a count of 0), which of the errors it raises is unspecified.

A failed call has no effect: if a method raises, every count and the list of
beds are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as `1.5`,
`"3"`, `True` or `None`), and species or bed names that are not non-empty
strings (such as `""`, `None` or `1`), wherever they are passed. It also
includes which error is raised when a call has several problems, pulling a
count of 0 or less, clearing a bed that is empty, adding a bed under the
name of a bed that was cleared, what happens if a returned
list is changed, the text of error messages, saving the garden to a file,
and use from several threads.
