# Aquarium tanks

Write a module `aquarium.py` that keeps track of the fish in a public
aquarium: how many fish of each species are in each tank, as fish are put
in, taken out, and moved from one tank to another.

## Interface

```python
class AquariumError(Exception): ...


class NotEnoughFish(AquariumError): ...


class Aquarium:
    def __init__(self): ...
    def add_tank(self, name: str) -> None: ...
    def add_fish(self, tank: str, species: str, count: int) -> None: ...
    def remove_fish(self, tank: str, species: str, count: int) -> None: ...
    def move_all(self, from_tank: str, to_tank: str) -> int: ...
    def drain_tank(self, from_tank: str, to_tank: str) -> int: ...
    def get_count(self, tank: str, species: str) -> int: ...
    def get_species(self, tank: str) -> list[str]: ...
    def get_tanks(self) -> list[str]: ...
```

Tank names and species are non-empty strings, and counts are `int`.

## Tanks

- `add_tank(name)` adds an empty tank. A name that is already in use raises
  `AquariumError`.
- `get_tanks()` returns the names of the tanks in use, in the order they
  were added.
- Every other method raises `KeyError` when given a tank name that is not
  in use: one that was never added, or one that was drained.

## Fish

- `add_fish(tank, species, count)` puts `count` fish of `species` into the
  tank, adding to any fish of that species already there. A count of 0 or
  less raises `ValueError`.
- `remove_fish(tank, species, count)` takes `count` fish of `species` out
  of the tank. Taking out more fish than the tank has of that species
  (including a species it has none of) raises `NotEnoughFish`.
- `move_all(from_tank, to_tank)` moves every fish of every species from
  `from_tank` into `to_tank`, and returns how many fish it moved in total.
  Afterwards `from_tank` is empty but still in use. A tank with no fish
  moves nothing, and the call returns 0.
- `drain_tank(from_tank, to_tank)` moves every fish of every species from
  `from_tank` into `to_tank`, then removes `from_tank`: it is no longer
  listed by `get_tanks()`, and every method treats it as not in use. It
  returns how many fish it moved in total. The name is then free:
  `add_tank` may add it again later, as a new empty tank listed last.
- `move_all` and `drain_tank` raise `ValueError` when both tanks are the
  same.
- `get_count(tank, species)` returns how many fish of `species` are in the
  tank: 0 for a species that is not there.
- `get_species(tank)` returns the species that have at least one fish in
  the tank, in alphabetical order. A species whose fish have all been taken
  out or moved away is no longer listed.

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`). If a loop over a tank's fish calls
something that can add or remove entries (such as `remove_fish`), loop over
a copy such as `list(fish.items())`.

## Errors

A failed call has no effect: if a method raises, every count and the list
of tanks are unchanged.

When a call has more than one problem (for example a tank that is not in
use and a count of 0), which of the errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as `1.5`,
`"3"`, `True` or `None`), and species or tank names that are not non-empty
strings (such as `""`, `None` or `1`), wherever they are passed. It also
includes `remove_fish` with a count of 0 or less, the counts after
`move_all` or `drain_tank` moves fish into a tank that already has fish of
the same species, which error is raised when a call has more than one
problem, what happens if a returned list is changed, the text of error
messages, saving the aquarium to a file, and use from several threads.
