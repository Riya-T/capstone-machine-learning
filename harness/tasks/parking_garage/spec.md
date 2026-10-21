# Parking garage

Write a module `garage.py` that keeps track of the vehicles parked in a
garage with several levels, and works out how long a vehicle was parked
when it leaves.

## Interface

```python
class GarageError(Exception): ...


class GarageFull(GarageError): ...


class Garage:
    def __init__(self): ...
    def add_level(self, level_id: str, spots: int) -> None: ...
    def enter(self, plate: str, minute: int) -> str: ...
    def leave(self, plate: str, minute: int) -> int: ...
    def get_level(self, plate: str) -> str: ...
    def get_free_spots(self, level_id: str) -> int: ...
    def get_vehicles(self, level_id: str) -> list[str]: ...
    def get_levels(self) -> list[str]: ...
```

All times are minutes since the garage opened, as `int`.

## Levels

- `add_level(level_id, spots)` adds a level with that many spots, all of
  them free. `level_id` must be a non-empty `str` and `spots` an `int`
  greater than 0, or `ValueError` is raised. Adding a level id that was
  already added raises `GarageError`.
- `get_levels()` returns the ids of all levels, in the order they were added.
- `get_free_spots(level_id)` returns the number of spots on the level with no
  vehicle in them. `get_vehicles(level_id)` returns the plates of the
  vehicles parked on the level, in the order they entered.
- `get_free_spots` and `get_vehicles` raise `KeyError` for a level id that
  was not added, including values that are not strings at all, such as
  `None` or `1`.

## Entering and leaving

- `enter(plate, minute)` parks a vehicle. `plate` must be a non-empty `str`
  and `minute` an `int` of 0 or more, or `ValueError` is raised. A plate
  that is already parked raises `GarageError`. The vehicle takes a spot on
  the first level, in the order the levels were added, that has a free
  spot, and the id of that level is returned. When no level has a free
  spot, `GarageFull` is raised.
- `leave(plate, minute)` takes the vehicle out, frees its spot and returns
  the number of minutes it was parked: `minute` minus the minute it
  entered. `minute` must be an `int` that is not less than the minute the
  vehicle entered, or `ValueError` is raised. The same plate may enter again
  later.
- `get_level(plate)` returns the id of the level the vehicle is parked on.
- `leave` and `get_level` raise `KeyError` for a plate that is not parked,
  including values that are not strings.

When a call has several problems, the first of these is raised:

1. for `enter`: `ValueError` for a bad plate or minute, then `GarageError`
   for a plate that is already parked, then `GarageFull`;
2. for `leave`: `KeyError` for a plate that is not parked, then `ValueError`
   for a bad minute;
3. for `add_level`: `ValueError` for a bad id or spot count, then
   `GarageError` for an id that was already added.

A failed call has no effect: if a method raises, nothing about the levels or
the parked vehicles changes.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as minutes or spot counts, what happens if a
returned list is changed, the text of error messages, saving the garage to a
file, and use from several threads.
