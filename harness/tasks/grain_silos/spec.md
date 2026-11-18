# Grain silos

Write a module `silos.py` that keeps track of the grain stored in a farm
cooperative's silos: how many tonnes of each grain each silo holds, as
grain is loaded, unloaded and moved from one silo to another.

## Interface

```python
class SiloError(Exception): ...


class NotEnoughGrain(SiloError): ...


class Silos:
    def __init__(self): ...
    def add_silo(self, name: str) -> None: ...
    def load(self, silo: str, grain: str, tonnes: int) -> None: ...
    def unload(self, silo: str, grain: str, tonnes: int) -> None: ...
    def blend_into(self, from_silo: str, to_silo: str) -> int: ...
    def demolish_silo(self, name: str, into: str) -> int: ...
    def get_tonnes(self, silo: str, grain: str) -> int: ...
    def get_grains(self, silo: str) -> list[str]: ...
    def get_silos(self) -> list[str]: ...
```

Silo names and grains (such as `"wheat"`) are non-empty strings, and
tonnes are `int`.

## Silos

- `add_silo(name)` adds an empty silo. A name that is already in use
  raises `SiloError`.
- `get_silos()` returns the names of the silos in use, in the order they
  were added.
- Every other method raises `KeyError` when given a silo name that is not
  in use: one that was never added, or one that was demolished.

## Grain

- Tonnes must be greater than 0; otherwise `load` and `unload` raise
  `ValueError`.
- `load(silo, grain, tonnes)` adds `tonnes` of that grain to the silo.
  `unload(silo, grain, tonnes)` takes them out. Unloading more of a grain
  than the silo holds (including a grain it holds none of) raises
  `NotEnoughGrain`.
- `get_tonnes(silo, grain)` returns how many tonnes of that grain the silo
  holds: 0 for a grain it has never held, or whose tonnes have all left.
- `get_grains(silo)` returns the grains the silo holds at least 1 tonne of,
  in alphabetical order. A grain whose tonnes have all left the silo (by
  `unload`, `blend_into` or `demolish_silo`) is no longer listed.

## Moving all the grain

- `blend_into(from_silo, to_silo)` moves all the grain of every kind from
  `from_silo` into `to_silo` and returns how many tonnes it moved in total.
  Afterwards `from_silo` is empty but still in use. Blending an empty silo
  is not an error: nothing changes and it returns 0.
- `demolish_silo(name, into)` moves all the grain of every kind from silo
  `name` into silo `into`, then demolishes silo `name`: it is no longer
  listed by `get_silos()`, and every method treats it as not in use. It
  returns how many tonnes it moved in total (0 if the silo was empty). The
  other silos keep their order.
- `blend_into` and `demolish_silo` raise `ValueError` when both names are
  the same.

```python
s = Silos()
s.add_silo("north")
s.add_silo("south")
s.load("north", "wheat", 40)
s.load("north", "barley", 15)
s.load("south", "wheat", 5)
s.blend_into("north", "south")    # returns 55
s.get_tonnes("south", "wheat")    # 45
s.get_grains("south")             # ["barley", "wheat"]
s.get_grains("north")             # []
s.demolish_silo("north", "south") # returns 0
s.get_silos()                     # ["south"]
```

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`); if a loop over a silo's grain can
add or remove entries, loop over a copy such as `list(grain.items())`.

## Errors

Which error is raised when a call has more than one problem (for example a
silo that is not in use and tonnes of 0) is unspecified.

A failed call has no effect: if a method raises, every amount and the list
of silos are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes values of the wrong type (tonnes that are not `int`, such as
`1.5`, `"3"`, `True` or `None`, and names or grains that are not non-empty
strings), which error is raised when a call has more than one problem,
adding a silo under the name of a demolished silo, what happens if a
returned list is changed, the text of error messages, saving the silos to
a file, and use from several threads.
