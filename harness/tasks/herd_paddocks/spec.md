# Herd paddocks

Write a module `farm.py` that keeps track of the animals on a farm: how many
animals of each species are in each paddock, as animals arrive, leave and
are moved from one paddock to another.

## Interface

```python
class FarmError(Exception): ...


class NotEnoughAnimals(FarmError): ...


class Farm:
    def __init__(self): ...
    def add_paddock(self, name: str) -> None: ...
    def arrive(self, paddock: str, species: str, count: int) -> None: ...
    def depart(self, paddock: str, species: str, count: int) -> None: ...
    def move(self, species: str, from_paddock: str, to_paddock: str, count: int) -> None: ...
    def move_all(self, from_paddock: str, to_paddock: str) -> int: ...
    def close_paddock(self, name: str, to_paddock: str) -> int: ...
    def get_count(self, paddock: str, species: str) -> int: ...
    def get_species(self, paddock: str) -> list[str]: ...
    def get_paddocks(self) -> list[str]: ...
```

Paddock names and species are non-empty strings, and counts are `int`.

## Paddocks

- `add_paddock(name)` adds an empty paddock. A name that is already in use
  raises `FarmError`.
- `get_paddocks()` returns the names of the paddocks in use, in the order
  they were added.
- Every other method raises `KeyError` when given a paddock name that is not
  in use: one that was never added, or one that was closed.

## Animals

- A count must be greater than 0; otherwise `ValueError` is raised.
- `arrive(paddock, species, count)` adds `count` animals of `species` to the
  paddock. `depart(paddock, species, count)` takes them away.
- `move(species, from_paddock, to_paddock, count)` moves `count` animals of
  `species` from `from_paddock` to `to_paddock`.
- `move_all(from_paddock, to_paddock)` moves every animal of every species
  from `from_paddock` to `to_paddock` and returns how many animals it moved
  in total. Afterwards `from_paddock` is empty but still in use. Moving from
  an empty paddock is not an error: nothing changes and it returns 0.
- `close_paddock(name, to_paddock)` moves every animal of every species from
  paddock `name` to `to_paddock`, then closes paddock `name`: it is removed
  from `get_paddocks()`, and every method treats it as not in use. It returns
  how many animals it moved in total (0 if the paddock was empty). The name
  is then free: `add_paddock` may add it again later, as a new empty
  paddock.
- `move`, `move_all` and `close_paddock` raise `ValueError` when both
  paddocks are the same.
- A paddock never holds fewer than 0 animals of a species: a `depart` or a
  `move` of more animals than the paddock has of that species (including a
  species it has none of) raises `NotEnoughAnimals`.
- `get_count(paddock, species)` returns how many animals of `species` are in
  the paddock: 0 for a species that has never been there, or whose animals
  have all left.
- `get_species(paddock)` returns the species that have at least one animal in
  the paddock, in alphabetical order. A species whose animals have all left
  (by `depart`, `move`, `move_all` or `close_paddock`) is no longer listed.

Python note: a `dict` must not gain or lose keys while a `for` loop runs over
it (Python raises `RuntimeError`); if a loop over a paddock's animals can add
or remove entries, loop over a copy such as `list(animals.items())`.

## Errors

`KeyError` and `ValueError` come before `NotEnoughAnimals`: a call with a
paddock that is not in use, a count of 0 or less, or the same paddock on
both sides raises `KeyError` or `ValueError`, even if it also asks for more
animals than there are. Which of `KeyError` and `ValueError` is raised when
a call has problems of both kinds is unspecified.

A failed call has no effect: if a method raises, every count and the list of
paddocks are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as `1.5`,
`"3"`, `True` or `None`), and species or paddock names that are not
non-empty strings (such as `""`, `None` or `1`), wherever they are passed.
It also includes which of `KeyError` and `ValueError` is raised when a call
has both kinds of problem, what happens if a returned list is changed, the
text of error messages, saving the farm to a file, and use from several
threads.
