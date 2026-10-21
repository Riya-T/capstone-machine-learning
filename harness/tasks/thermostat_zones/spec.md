# Thermostat zones

Write a module `thermostat.py` that controls the heating zones of a
building: each zone has a target temperature, a mode, and the temperature
readings its sensor has reported.

## Interface

```python
class ThermostatError(Exception): ...


class Thermostat:
    def __init__(self): ...
    def add_zone(self, zone: str) -> None: ...
    def set_target(self, zone: str, temp: int) -> None: ...
    def set_mode(self, zone: str, mode: str) -> None: ...
    def record_reading(self, zone: str, temp: int) -> None: ...
    def get_setting(self, zone: str) -> tuple[str, int]: ...
    def get_reading(self, zone: str) -> int: ...
    def get_zones(self) -> list[str]: ...
```

All temperatures are whole degrees, as `int`. They may be negative.

## Zones

- `add_zone(zone)` adds a zone. Its mode starts as `"off"`, its target as
  `20`, and it has no reading yet. An empty name raises `ValueError`, and
  a name that was already added raises `ThermostatError` and changes
  nothing.
- `get_zones()` returns the zones in the order they were added.
- Every other method raises `KeyError` when given a zone that was not
  added, including values that are not strings at all, such as `None` or
  `1`.

## Settings

- `set_target(zone, temp)` replaces the zone's target temperature. The
  temperature must be an `int`, or `ValueError` is raised.
- `set_mode(zone, mode)` replaces the zone's mode, which must be one of
  `"heat"`, `"cool"` or `"off"`; anything else raises `ValueError`.
- `get_setting(zone)` returns `(mode, target)` for the zone.

## Readings

- `record_reading(zone, temp)` records a temperature reported by the zone's
  sensor. The temperature must be an `int`, or `ValueError` is raised.
  Readings are never limited by the target or the mode.
- `get_reading(zone)` returns the most recent reading of the zone. A zone
  that has no reading yet raises `ThermostatError`.

When a call has several problems, the first of these is raised:

1. `KeyError` for a zone that was not added;
2. `ValueError` for an invalid temperature or mode;
3. `ThermostatError`.

A failed call has no effect: if a method raises, every zone's mode, target
and readings are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_zone`, `bool`
temperatures, what happens if a returned list is changed, the text of error
messages, saving the thermostat to a file, and use from several threads.
